"""D13: try quiz generation on your real index.  python scripts/try_quiz.py AI201 "Neural Networks" 3"""
import sys

sys.path.insert(0, ".")
from src.backend.study import generate_quiz

code = sys.argv[1] if len(sys.argv) > 1 else ""
module = sys.argv[2] if len(sys.argv) > 2 else "Introduction"
n = int(sys.argv[3]) if len(sys.argv) > 3 else 3
r = generate_quiz({"subject": code, "subject_code": code or None, "module": module, "module_id": None}, n)
print(r["message"] or "")
for i, q in enumerate(r["quiz"], 1):
    print(f"\nQ{i}. {q['question']}")
    for j, o in enumerate(q["options"]):
        print(f"   {'*' if j == q['correct_index'] else ' '} {'ABCD'[j]}. {o}")
    print("   Why:", q["explanation"])
print("\nSources:", ", ".join(f"{s['document']} p.{s['page']}" for s in r["sources"]))
