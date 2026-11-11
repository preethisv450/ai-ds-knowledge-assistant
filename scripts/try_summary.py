"""D11: try the summary on your real index.  python scripts/try_summary.py "AI201" "Neural Networks"
Arguments: subject code (optional filter, or "" for any), then the module/topic words."""
import sys

sys.path.insert(0, ".")
from src.backend.study import generate_summary

code = sys.argv[1] if len(sys.argv) > 1 else ""
module = " ".join(sys.argv[2:]) or "Introduction"
sel = {"subject": code, "subject_code": code or None, "module": module, "module_id": None}
r = generate_summary(sel)
print(r["summary"])
print("\nSources:")
for s in r["sources"]:
    print(f"  {s['document']}, p.{s['page']}")
