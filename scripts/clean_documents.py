"""D6: show the running headers and footers that are stripped before indexing.

  python scripts/clean_documents.py

Reads every PDF in data/pdfs and reports which repeated lines are removed. Removal is
automatic during indexing; this script is how you check it is removing the right thing
and nothing more. If a real heading is listed here, tell Pragna before the next rebuild.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.backend.config import PDF_DIR
from src.backend.ingest import extract_pages
from src.data.clean_text import strip_boilerplate

pdfs = sorted(Path(PDF_DIR).glob("*.pdf"))
if not pdfs:
    sys.exit(f"No PDFs in {PDF_DIR}")

for pdf in pdfs:
    raw = extract_pages(pdf, strip_headers=False)
    if not raw:
        print(f"\n{pdf.name}: no selectable text (a scan needs OCR first)")
        continue
    cleaned, report = strip_boilerplate(raw)
    before = sum(len(t.split()) for _, t in raw)
    after = sum(len(t.split()) for _, t in cleaned)
    print(f"\n{pdf.name}  ({len(raw)} pages, {before} words -> {after} words)")
    if not report["removed_lines"]:
        print("   nothing repeated often enough to remove")
    for line, n in sorted(report["removed_lines"].items(), key=lambda kv: -kv[1]):
        print(f"   removed {n:>3}x  {line[:80]}")
