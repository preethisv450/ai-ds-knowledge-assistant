"""D5: check the concept nodes and edges before the graph is built.

  python scripts/check_concepts.py

Reads data/concepts/concepts.csv and relations.csv, checks them against curriculum.json,
and prints what needs fixing. Exit code 1 if anything is wrong.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.data.concepts import check, load_concepts, load_relations, stats

cpath, rpath = Path("data/concepts/concepts.csv"), Path("data/concepts/relations.csv")
curriculum = json.loads(Path("data/processed/curriculum.json").read_text()) \
    if Path("data/processed/curriculum.json").exists() else None

concepts, p1 = load_concepts(cpath)
relations, p2 = load_relations(rpath)
problems = p1 + p2 + (check(concepts, relations, curriculum) if concepts else [])

s = stats(concepts, relations)
print(f"{s['concepts']} concepts, {s['relations']} relations "
      f"({s['prerequisite']} prerequisite, {s['related_to']} related-to)")
if s["per_module"]:
    print("\nConcepts per module")
    for mid, n in sorted(s["per_module"].items()):
        print(f"  {mid:<14} {n}")
if s["unassigned"]:
    print(f"\n{s['unassigned']} concept(s) have no module_id")
if s["isolated"]:
    print(f"\n{len(s['isolated'])} concept(s) have no edges and will sit alone in the graph:")
    print("  " + ", ".join(s["isolated"][:15]) + (" ..." if len(s["isolated"]) > 15 else ""))

if problems:
    print(f"\nPROBLEMS ({len(problems)})")
    for p in problems:
        print("  -", p)
    sys.exit(1)
print("\nNo problems found.")
