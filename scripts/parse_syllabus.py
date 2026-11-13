"""D2: turn syllabus PDFs into a draft curriculum entry you then correct by hand.

  python scripts/parse_syllabus.py data/pdfs/AI201_syllabus.pdf
  python scripts/parse_syllabus.py data/pdfs/*.pdf --out data/processed/syllabus_draft.json

Writes a draft JSON and prints what needs checking. It is a starting point, never the
final file: read every line it produces before pasting it into curriculum.json.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.data.syllabus_parser import module_pages, parse_syllabus, to_curriculum_entry

args = [a for a in sys.argv[1:] if not a.startswith("--")]
out_path = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--out=")),
                "data/processed/syllabus_draft.json")
if not args:
    sys.exit(__doc__)

drafts, manifest_hint = [], {}
for p in args:
    draft = parse_syllabus(p)
    drafts.append(to_curriculum_entry(draft))
    manifest_hint[Path(p).name] = {"subject_code": draft["code"], "modules": module_pages(draft)}
    print(f"\n{Path(p).name}")
    print(f"  code    : {draft['code']}")
    print(f"  name    : {draft['name'] or '(not found)'}")
    print(f"  credits : {draft['credits'] if draft['credits'] is not None else '(not found)'}")
    for m in draft["modules"]:
        print(f"  {m['id']}  p{m['pages'][0]}-{m['pages'][1]}  {m['title']}  ({len(m['topics'])} topics)")
    for r in draft["_review"]:
        print(f"  CHECK: {r}")

Path(out_path).parent.mkdir(parents=True, exist_ok=True)
Path(out_path).write_text(json.dumps({"subjects": drafts, "manifest_hint": manifest_hint}, indent=2) + "\n")
print(f"\nDraft written to {out_path}")
print("Next: correct it by hand, paste the subjects into data/processed/curriculum.json,")
print("      then run  python scripts/validate_data.py")
