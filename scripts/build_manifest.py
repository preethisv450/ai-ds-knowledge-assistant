"""D7: build or update data/processed/documents.json from the PDFs in data/pdfs.

  python scripts/build_manifest.py                 show what it would write
  python scripts/build_manifest.py --write         write the file (keeps existing entries)
  python scripts/build_manifest.py --write --fresh replace the file completely

Entries already in the file are never overwritten, so hand corrections survive.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.backend.config import PDF_DIR
from src.data.manifest import MANIFEST_PATH, build, merge, save

write, fresh = "--write" in sys.argv, "--fresh" in sys.argv
curriculum = json.loads(Path("data/processed/curriculum.json").read_text()) \
    if Path("data/processed/curriculum.json").exists() else None
if curriculum is None:
    print("Note: curriculum.json not found, so module titles cannot be cross-checked.\n")

entries, notes = build(PDF_DIR, curriculum)
if not entries:
    sys.exit(f"No PDFs found in {PDF_DIR}")

existing = []
if MANIFEST_PATH.exists() and not fresh:
    existing = json.loads(MANIFEST_PATH.read_text())
    existing = existing.get("documents", existing) if isinstance(existing, dict) else existing
final = merge(existing, entries) if existing else entries

for e in final:
    mods = e.get("modules") or {}
    ranges = "  ".join(f"{m} p{v[0]}-{v[1]}" for m, v in sorted(mods.items())) or "-"
    kept = " (kept from the existing file)" if any(x["file"] == e["file"] for x in existing) else ""
    print(f"{e['file']:<32} {e['doc_type']:<11} {e.get('subject_code') or '-':<8} {ranges}{kept}")

if notes:
    print("\nCheck these:")
    for n in notes:
        print(" -", n)

if write:
    print(f"\nWritten to {save(final)}")
    print("Next: python scripts/validate_data.py   then rebuild the index")
else:
    print("\nNothing written. Re-run with --write to save this.")
