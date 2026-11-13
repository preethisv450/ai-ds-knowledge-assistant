"""D8: create the blank 30-question evaluation set, or check a filled-in one.

  python scripts/make_question_set.py --new      write a blank template to fill in
  python scripts/make_question_set.py            check data/eval/test_questions.csv

Fill the template in Sheets, export it back to the same path as CSV, then run the
check. Every problem it reports would otherwise show up later as a false failure.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.backend.config import PDF_DIR
from src.backend.evaluation import load_questions
from src.data.questions import balance, check, write_template

path = Path(next((a for a in sys.argv[1:] if not a.startswith("--")), "data/eval/test_questions.csv"))

if "--new" in sys.argv:
    if path.exists():
        sys.exit(f"{path} already exists. Delete or rename it first, so a filled-in set is never overwritten.")
    write_template(path)
    print(f"Blank set written to {path}")
    print("Fill in one row per question: the question as a student would type it, the keywords the answer")
    print("must contain, and the document and page the answer is on. Keep the unanswerable rows empty.")
    sys.exit(0)

if not path.exists():
    sys.exit(f"{path} not found. Create it with: python scripts/make_question_set.py --new")

rows = load_questions(path)
curriculum = json.loads(Path("data/processed/curriculum.json").read_text()) \
    if Path("data/processed/curriculum.json").exists() else None
b = balance(rows)

print(f"{b['total']} questions: " + ", ".join(f"{n} {m}" for m, n in sorted(b["by_mode"].items())))
print(f"{b['unanswerable']} of them unanswerable (refusal is tested)")
if b["modules_covered"]:
    print(f"Modules covered: {', '.join(b['modules_covered'])}")
for n in b["notes"]:
    print(f"  - {n}")

problems = check(rows, PDF_DIR, curriculum)
if problems:
    print(f"\nPROBLEMS ({len(problems)})")
    for p in problems:
        print("  -", p)
    sys.exit(1)
print("\nThe set is usable. Next: python scripts/accuracy_report.py")
