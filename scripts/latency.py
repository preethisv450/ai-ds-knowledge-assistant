"""D16: measure what the student waits for.  python scripts/latency.py
Prints model load, index load, retrieval time per question, and (if --gemini) one real answer."""
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.backend.warmup import warm_up

print("Warm-up (model + index):", warm_up())
from src.backend.catalog import make_filter
from src.backend.retrieval import retrieve

qs = ["What is an admissible heuristic?", "What does PEAS stand for?", "What is the minimum attendance?",
      "How is precision calculated?", "What is k-means?", "Explain modus ponens", "What is a dendrogram?",
      "When is re-evaluation allowed?", "What is overfitting?", "Define a rational agent"]
times = []
for q in qs:
    t = time.time()
    retrieve(q, k=5, where=make_filter("Syllabus", None))
    times.append(time.time() - t)
print(f"Retrieval after warm-up: median {statistics.median(times) * 1000:.0f} ms, slowest {max(times) * 1000:.0f} ms ({len(qs)} questions)")

if "--gemini" in sys.argv:
    from src.backend.rag import answer
    for label in ("first ask (Gemini call)", "same question again (cache)"):
        t = time.time()
        answer("What is an admissible heuristic?", "Syllabus", {"subject_code": "AI201", "module_id": "AI201-M2"})
        print(f"{label}: {time.time() - t:.2f}s")
