"""D5: propose candidate concepts per module, for you to curate into concepts.csv.

  python scripts/extract_concepts.py                    needs the index to be built
  python scripts/extract_concepts.py --per-module=15

Writes data/concepts/concepts.candidates.csv. These are frequent terms, not verified
concepts: open the file, delete the noise, fix the names, then save the keepers into
data/concepts/concepts.csv and write the edges in data/concepts/relations.csv.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.backend.config import INDEX_DIR
from src.data.concepts import CONCEPTS_HEADER, suggest_concepts, write_csv

per_module = next((int(a.split("=", 1)[1]) for a in sys.argv if a.startswith("--per-module=")), 12)
out = Path("data/concepts/concepts.candidates.csv")

try:
    from src.backend.vector_store import load_index
    _, chunks = load_index(INDEX_DIR)
except FileNotFoundError:
    sys.exit("No index found. Run: python scripts/build_index.py")

labelled = [c for c in chunks if c.get("doc_type") == "syllabus"]
if not labelled:
    sys.exit("No syllabus chunks in the index. Check data/processed/documents.json, then rebuild the index.")

rows = suggest_concepts(labelled, per_module=per_module)
write_csv(rows, out, CONCEPTS_HEADER)

current = None
for r in rows:
    if r["module_id"] != current:
        current = r["module_id"]
        print(f"\n{current or '(no module)'}")
    print(f"   {r['_count']:>3}x  {r['name']}")

print(f"\n{len(rows)} candidates written to {out}")
print("These are frequent terms, not verified concepts. Curate them into data/concepts/concepts.csv,")
print("then write the edges in data/concepts/relations.csv and run python scripts/check_concepts.py")
