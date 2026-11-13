"""D4: check the curriculum and the document manifest before handing them over.

  python scripts/validate_data.py

Exit code 0 when there are no errors (warnings are fine), 1 when something must be fixed.
Run this before every hand-off to Preethi or Pragna.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.data.validate import counts, validate_all

findings = validate_all()
if not findings:
    print("All checks passed: curriculum.json and documents.json are consistent.")
    sys.exit(0)

for level in ("error", "warning"):
    rows = [f for f in findings if f["level"] == level]
    if not rows:
        continue
    print(f"\n{level.upper()}S ({len(rows)})")
    width = max(len(r["where"]) for r in rows)
    for r in rows:
        print(f"  {r['where']:<{width}}  {r['message']}")

c = counts(findings)
print(f"\n{c['errors']} errors, {c['warnings']} warnings")
if c["errors"]:
    print("Fix the errors before handing the data over.")
sys.exit(1 if c["errors"] else 0)
