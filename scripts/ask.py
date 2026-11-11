"""Ask the RAG backend from the terminal and see the retrieval scores behind the answer.
  python scripts/ask.py "your question"       (add --regulation for Regulation mode)
Use it to tune RAG_MIN_SCORE: relevant questions should score above it, unrelated ones below."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.backend import config
from src.backend.rag import answer
from src.backend.retrieval import retrieve

args = [a for a in sys.argv[1:] if not a.startswith("--")]
mode = "Regulation" if "--regulation" in sys.argv else "Syllabus"
if not args:
    sys.exit('Usage: python scripts/ask.py "your question" [--regulation]')
q = " ".join(args)

print(f"Top retrieval scores (threshold {config.RAG_MIN_SCORE}):")
for r in retrieve(q, k=config.TOP_K):
    flag = "kept   " if r["score"] >= config.RAG_MIN_SCORE else "dropped"
    print(f"  {r['score']:.3f} {flag} {r['document']} p.{r['page']}")
res = answer(q, mode)
print(f"\nANSWER:\n{res['answer']}\n\nSOURCES: " + (", ".join(f"{s['document']} p.{s['page']}" for s in res["sources"]) or "(none)"))
