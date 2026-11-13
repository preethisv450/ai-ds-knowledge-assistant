"""D3: split the regulation PDF into sections with page numbers.

  python scripts/split_regulations.py data/pdfs/Academic_Regulations.pdf

Writes data/processed/regulations.json and prints the sections it found, so you can
see at a glance which rules the document covers and on which page each one sits.
Those page numbers are what the D8 test set cites as expected_page.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.data.regulation_sections import coverage, save, split_regulation

args = [a for a in sys.argv[1:] if not a.startswith("--")]
if not args:
    sys.exit(__doc__)
pdf = Path(args[0])
out = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--out=")), "data/processed/regulations.json")

sections = split_regulation(pdf)
if not sections:
    sys.exit(f"No text found in {pdf}. If it is a scan, it needs OCR first.")

print(f"{len(sections)} sections in {pdf.name}\n")
print(f"{'pages':<9} {'topic':<14} title")
for s in sections:
    pages = f"{s['first_page']}-{s['last_page']}" if s["last_page"] != s["first_page"] else str(s["first_page"])
    print(f"{pages:<9} {str(s['topic'] or '-'):<14} {s['title']}  ({s['word_count']} words)")

c = coverage(sections)
print(f"\nTopics found  : {', '.join(c['found']) or 'none'}")
if c["missing"]:
    print(f"Not found     : {', '.join(c['missing'])}")
    print("               (either this document does not cover them, or the heading style was not recognised)")
print(f"\nSaved to {save(sections, out, source_file=pdf.name)}")
