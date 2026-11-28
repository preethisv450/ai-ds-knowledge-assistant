"""D12: rank concepts by centrality and name the bridge concepts.

Reads data/processed/concept_graph.graphml (written by build_concept_graph.py)
and computes, for every concept:

  prerequisites   in-degree, how many concepts must come first
  leads_to        out-degree, how many concepts build on it
  degree          Freeman degree centrality, normalised
  betweenness     Freeman betweenness centrality, normalised

Betweenness is the bridge measure: a concept scores highly when the shortest
paths between other concepts run through it, which in a curriculum means
skipping it blocks the most downstream topics.

Writes data/processed/centrality.csv (every concept, for D14) and
docs/centrality_report.md (the ranked tables for the report).

    python scripts/centrality_report.py
    python scripts/centrality_report.py --top=25
"""
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import networkx as nx

ROOT = Path(__file__).resolve().parents[1]
GRAPH = ROOT / "data" / "processed" / "concept_graph.graphml"
CSV_OUT = ROOT / "data" / "processed" / "centrality.csv"
MD_OUT = ROOT / "docs" / "centrality_report.md"


def measure(graph):
    degree = nx.degree_centrality(graph)
    betweenness = nx.betweenness_centrality(graph, normalized=True)
    rows = []
    for node, data in graph.nodes(data=True):
        rows.append({
            "concept_id": node,
            "name": data.get("name", node),
            "subject_code": data.get("subject_code", ""),
            "module_id": data.get("module_id", ""),
            "prerequisites": graph.in_degree(node),
            "leads_to": graph.out_degree(node),
            "degree_centrality": round(degree.get(node, 0.0), 5),
            "betweenness": round(betweenness.get(node, 0.0), 5),
        })
    rows.sort(key=lambda r: (-r["betweenness"], -r["degree_centrality"], r["name"]))
    for i, r in enumerate(rows, start=1):
        r["rank"] = i
    return rows


def table(rows, columns):
    head = "| " + " | ".join(h for h, _ in columns) + " |"
    rule = "|" + "|".join("---" for _ in columns) + "|"
    body = ["| " + " | ".join(str(f(r)) for _, f in columns) + " |" for r in rows]
    return "\n".join([head, rule] + body)


def main():
    top = int(next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--top=")), 20))
    if not GRAPH.exists():
        print(f"{GRAPH} not found. Run scripts/build_concept_graph.py first.")
        return 1

    graph = nx.read_graphml(GRAPH)
    rows = measure(graph)

    fields = ["rank", "concept_id", "name", "subject_code", "module_id",
              "prerequisites", "leads_to", "degree_centrality", "betweenness"]
    with open(CSV_OUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for r in rows:
            writer.writerow({k: r[k] for k in fields})

    bridges = [r for r in rows if r["betweenness"] > 0][:10]
    by_degree = sorted(rows, key=lambda r: (-r["degree_centrality"], r["name"]))[:top]
    foundations = sorted((r for r in rows if r["prerequisites"] == 0),
                         key=lambda r: (-r["leads_to"], r["name"]))[:10]

    cross = []
    for src, tgt in graph.edges():
        a, b = graph.nodes[src], graph.nodes[tgt]
        if a.get("subject_code") and b.get("subject_code") and a["subject_code"] != b["subject_code"]:
            cross.append((a.get("name", src), a["subject_code"], b.get("name", tgt), b["subject_code"]))

    md = [
        "# Concept centrality — D12",
        "",
        f"Graph: {graph.number_of_nodes()} concepts, {graph.number_of_edges()} relations, "
        f"built by `scripts/build_concept_graph.py`.",
        "Measures are Freeman's degree and betweenness centrality, both normalised, "
        "computed with NetworkX on the directed graph.",
        "",
        "- **prerequisites** — concepts that must come first (in-degree)",
        "- **leads_to** — concepts that build on it (out-degree)",
        "- **betweenness** — how often it sits on the shortest path between two other "
        "concepts; the bridge measure",
        "",
        "## Bridge concepts",
        "",
        "These carry the most traffic between topics. Skipping one blocks the largest "
        "number of later concepts, so they are the ones to teach and revise first.",
        "",
        table(bridges, [
            ("Rank", lambda r: r["rank"]),
            ("Concept", lambda r: r["name"]),
            ("Subject", lambda r: r["subject_code"]),
            ("Module", lambda r: r["module_id"]),
            ("Betweenness", lambda r: f"{r['betweenness']:.4f}"),
            ("Leads to", lambda r: r["leads_to"]),
        ]),
        "",
        f"## Top {top} by degree centrality",
        "",
        "Degree centrality counts direct connections, so this is a measure of how "
        "densely a concept sits in the syllabus rather than how much depends on it.",
        "",
        table(by_degree, [
            ("Concept", lambda r: r["name"]),
            ("Subject", lambda r: r["subject_code"]),
            ("Prerequisites", lambda r: r["prerequisites"]),
            ("Leads to", lambda r: r["leads_to"]),
            ("Degree", lambda r: f"{r['degree_centrality']:.4f}"),
        ]),
        "",
        "## Starting points",
        "",
        "Concepts with no prerequisites, ranked by how much follows from them. These "
        "are where a student with no background should begin.",
        "",
        table(foundations, [
            ("Concept", lambda r: r["name"]),
            ("Subject", lambda r: r["subject_code"]),
            ("Module", lambda r: r["module_id"]),
            ("Leads to", lambda r: r["leads_to"]),
        ]),
        "",
        "## Links that cross subjects",
        "",
        f"{len(cross)} relations connect one subject to another. These are why the "
        "bridge scores above are not simply the busiest concept inside each module.",
        "",
        table(cross, [
            ("From", lambda c: f"{c[0]} ({c[1]})"),
            ("To", lambda c: f"{c[2]} ({c[3]})"),
        ]) if cross else "_None._",
        "",
        f"Full table for all {len(rows)} concepts: `data/processed/centrality.csv`.",
        "",
    ]
    MD_OUT.write_text("\n".join(md), encoding="utf-8")

    print(f"Concepts   : {len(rows)}")
    print(f"With bridge score > 0: {sum(1 for r in rows if r['betweenness'] > 0)}")
    print("\nTop bridge concepts:")
    for r in bridges[:5]:
        print(f"  {r['rank']:>2}. {r['name']:<32} {r['betweenness']:.4f}  ({r['subject_code']})")
    print(f"\nSaved {CSV_OUT}")
    print(f"Saved {MD_OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
