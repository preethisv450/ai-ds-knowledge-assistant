"""D12: try question generation on your real index.
python scripts/try_questions.py AI201 "Neural Networks" short 3     (type: short|long, count)"""
import sys

sys.path.insert(0, ".")
from src.backend.study import generate_questions

code = sys.argv[1] if len(sys.argv) > 1 else ""
module = sys.argv[2] if len(sys.argv) > 2 else "Introduction"
qtype = sys.argv[3] if len(sys.argv) > 3 else "short"
n = int(sys.argv[4]) if len(sys.argv) > 4 else 3
r = generate_questions({"subject": code, "subject_code": code or None, "module": module, "module_id": None}, qtype, n)
print(r["message"] or "")
for i, q in enumerate(r["questions"], 1):
    print(f"\nQ{i}. {q['question']}\nAnswer: {q['model_answer']}")
print("\nSources:", ", ".join(f"{s['document']} p.{s['page']}" for s in r["sources"]))
