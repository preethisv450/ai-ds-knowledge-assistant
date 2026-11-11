"""Live D5 check: one real Gemini call per template, using chunks from your index.
Run from the repo root: python scripts/try_gemini.py   (about 10-40 seconds)"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.backend import config, prompts
from src.backend.gemini_client import GeminiError, generate, generate_json
from src.backend.retrieval import retrieve

print(f"Model: {config.GEMINI_MODEL} | fallback: {config.GEMINI_FALLBACK_MODEL or '(none set)'}")
chunks = retrieve("Gemini wrapper retries timeout prompt templates", k=3)
print(f"Using {len(chunks)} chunks: " + ", ".join(f"{c['document']} p.{c['page']}" for c in chunks))
failed = False


def run(name, fn):
    global failed
    t = time.time()
    try:
        out = fn()
        print(f"\nOK   {name} ({time.time()-t:.1f}s)\n{str(out)[:350]}")
    except GeminiError as e:
        failed = True
        print(f"\nFAIL {name}: [{e.kind}] {e.user_message}\n     detail: {e.detail}")


q = "What does the Gemini wrapper need to handle?"
run("answer (with citations)", lambda: generate(*reversed(prompts.answer_prompt(q, chunks))))
run("answer (question NOT in documents)", lambda: generate(
    *reversed(prompts.answer_prompt("What is the capital of Peru?", chunks))))
run("summary", lambda: generate(*reversed(prompts.summary_prompt("AI & DS", "Project plan", chunks))))
s, p = prompts.questions_prompt("AI & DS", "Project plan", chunks, "short", 2)
run("questions (JSON, validated)", lambda: generate_json(p, system=s, validate=prompts.validate_questions))
s, p = prompts.quiz_prompt("AI & DS", "Project plan", chunks, 2)
run("quiz (JSON, validated)", lambda: generate_json(p, system=s, validate=prompts.validate_quiz))
print("\nAll four templates work." if not failed else "\nSome calls failed - paste this output to Claude.")
sys.exit(1 if failed else 0)
