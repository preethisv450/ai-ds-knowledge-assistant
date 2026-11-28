"""D11: build the concept graph and save it for the analysis that follows.

Reads data/concepts/concepts.csv and relations.csv, builds a NetworkX directed
graph, drops duplicate and self-referencing edges, and writes the graph as both
GraphML and node-link JSON so D12 (centrality), D13 (communities) and D14
(export for the UI) all start from the same file.

    python scripts/build_concept_graph.py
    python scripts/build_concept_graph.py --out=data/processed/concept_graph
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import networkx as nx

from src.data.concepts import load_concepts, load_relations

ROOT = Path(__file__).resolve().parents[1]
CONCEPTS = ROOT / "data" / "concepts" / "concepts.csv"
RELATIONS = ROOT / "data" / "concepts" / "relations.csv"


def build(concepts, relations):
    """Return (graph, notes). Notes lists everything that was dropped or merged."""
    notes = []
    graph = nx.DiGraph()

    seen = set()
    for c in concepts:
        cid = c["concept_id"]
        if cid in seen:
            notes.append(f"duplicate concept_id dropped: {cid}")
            continue
        seen.add(cid)
        graph.add_node(
            cid,
            name=c["name"],
            subject_code=c["subject_code"] or "",
            module_id=c["module_id"] or "",
            aliases="|".join(c.get("aliases") or []),
        )

    best = {}
    for r in relations:
        src, tgt = r["source"], r["target"]
        if src not in graph or tgt not in graph:
            notes.append(f"edge skipped, unknown concept: {src} -> {tgt}")
            continue
        if src == tgt:
            notes.append(f"self-loop dropped: {src}")
            continue
        key = (src, tgt)
        if key in best:
            notes.append(f"duplicate edge merged, highest weight kept: {src} -> {tgt}")
            if r["weight"] <= best[key]["weight"]:
                continue
        best[key] = {"relation": r["relation"], "weight": r["weight"], "note": r.get("note", "")}

    for (src, tgt), data in best.items():
        graph.add_edge(src, tgt, **data)

    for src, tgt in list(graph.edges()):
        if graph.has_edge(tgt, src) and graph[src][tgt]["relation"] == "prerequisite" \
                and graph[tgt][src]["relation"] == "prerequisite":
            notes.append(f"both directions marked prerequisite, check by hand: {src} <-> {tgt}")

    return graph, notes


def main():
    out = next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--out=")),
               "data/processed/concept_graph")
    out_path = ROOT / out if not Path(out).is_absolute() else Path(out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    concepts, c_problems = load_concepts(CONCEPTS)
    relations, r_problems = load_relations(RELATIONS)
    for p in c_problems + r_problems:
        print(f"  data problem: {p}")
    if not concepts:
        print("No concepts found. Run scripts/check_concepts.py first.")
        return 1

    graph, notes = build(concepts, relations)

    nx.write_graphml(graph, out_path.with_suffix(".graphml"))
    try:
        payload = nx.node_link_data(graph, edges="links")
    except TypeError:  # networkx < 3.4 has no edges= argument
        payload = nx.node_link_data(graph)
    out_path.with_suffix(".json").write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8"
    )

    kinds = {}
    for _, _, d in graph.edges(data=True):
        kinds[d["relation"]] = kinds.get(d["relation"], 0) + 1
    isolated = [n for n in graph if graph.degree(n) == 0]

    print(f"Concepts : {graph.number_of_nodes()}")
    print(f"Relations: {graph.number_of_edges()} " +
          ", ".join(f"{k} {v}" for k, v in sorted(kinds.items())))
    print(f"Subjects : {len({d['subject_code'] for _, d in graph.nodes(data=True) if d['subject_code']})}")
    print(f"Modules  : {len({d['module_id'] for _, d in graph.nodes(data=True) if d['module_id']})}")
    if isolated:
        print(f"Isolated : {len(isolated)} ({', '.join(sorted(isolated)[:6])})")
    if notes:
        print("\nCleaning notes:")
        for n in notes:
            print(f"  {n}")
    print(f"\nSaved {out_path.with_suffix('.graphml')}")
    print(f"Saved {out_path.with_suffix('.json')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
