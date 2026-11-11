"""Try retrieval by hand. Judge each result yourself: is the top chunk actually relevant?
  python scripts/try_queries.py                 -> runs the 10 sample queries
  python scripts/try_queries.py "your question" -> runs just that one"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.backend.retrieval import retrieve

SAMPLE_QUERIES = [
    "Which embedding model and vector store are used?",
    "What is Nishant responsible for?",
    "What does the Gemini wrapper need to handle?",
    "How is retrieval accuracy measured?",
    "What happens on Day 10?",
    "How is the app deployed?",
    "What does the Quiz tab do?",
    "How are chunks created from PDFs?",
    "What is community detection used for?",
    "What is the not found fallback?",
]

queries = sys.argv[1:] or SAMPLE_QUERIES
for q in queries:
    print(f"\n=== {q}")
    for r in retrieve(q, k=3):
        print(f"  {r['score']:.3f}  {r['document']} p.{r['page']}  {r['snippet'][:110]}")
