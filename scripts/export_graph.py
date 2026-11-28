"""D14: one export of the graph for the UI, plus plain-language study notes.

Merges what the three previous days produced:

  concept_graph.graphml   nodes, edges, subjects and modules   (D11)
  centrality.csv          degree, betweenness, in/out degree   (D12)
  communities.csv         Louvain community and its label      (D13)

into data/processed/graph_export.json, a single file the Knowledge Network page
can read without recomputing anything, and docs/study_order.md, which says in
plain words where to start and which concepts not to skip.

    python scripts/export_graph.py
"""
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import networkx as nx

ROOT = Path(__file__).resolve().parents[1]
GRAPH = ROOT / "data" / "processed" / "concept_graph.graphml"
CENTRALITY = ROOT / "data" / "processed" / "centrality.csv"
COMMUNITIES = ROOT / "data" / "processed" / "communities.csv"
CURRICULUM = ROOT / "data" / "processed" / "curriculum.json"
JSON_OUT = ROOT / "data" / "processed" / "graph_export.json"
MD_OUT = ROOT / "docs" / "study_order.md"


def read_csv(path, key="concept_id"):
    if not path.exists():
        return {}
    with open(path, newline="", encoding="utf-8") as f:
        return {row[key]: row for row in csv.DictReader(f)}


def subject_names():
    names = {}
    try:
        data = json.loads(CURRICULUM.read_text(encoding="utf-8"))
    except Exception:
        return names
    for year in data.get("years", []):
        for sem in year.get("semesters", []):
            for subject in sem.get("subjects", []):
                names[subject.get("code")] = subject.get("name")
    return names


def layers(graph, members):
    """Teaching order inside one subject: each layer needs only earlier layers."""
    sub = graph.subgraph(members).copy()
    sub.remove_edges_from([(u, v) for u, v, d in sub.edges(data=True)
                           if d.get("relation") != "prerequisite"])
    try:
        return [sorted(layer, key=lambda n: graph.nodes[n].get("name", n))
                for layer in nx.topological_generations(sub)]
    except nx.NetworkXUnfeasible:
        return None


def main():
    missing = [p.name for p in (GRAPH, CENTRALITY, COMMUNITIES) if not p.exists()]
    if missing:
        print("Missing: " + ", ".join(missing))
        print("Run build_concept_graph.py, centrality_report.py and communities_report.py first.")
        return 1

    graph = nx.read_graphml(GRAPH)
    central = read_csv(CENTRALITY)
    community = read_csv(COMMUNITIES)
    subjects = subject_names()

    nodes = []
    for node, data in graph.nodes(data=True):
        c = central.get(node, {})
        g = community.get(node, {})
        nodes.append({
            "id": node,
            "name": data.get("name", node),
            "subject_code": data.get("subject_code", ""),
            "module_id": data.get("module_id", ""),
            "aliases": [a for a in (data.get("aliases") or "").split("|") if a],
            "prerequisites": int(c.get("prerequisites", graph.in_degree(node))),
            "leads_to": int(c.get("leads_to", graph.out_degree(node))),
            "degree_centrality": float(c.get("degree_centrality", 0) or 0),
            "betweenness": float(c.get("betweenness", 0) or 0),
            "community_id": int(g["community_id"]) if g.get("community_id") else None,
            "community_label": g.get("community_label", ""),
        })
    nodes.sort(key=lambda n: (-n["betweenness"], n["name"]))

    edges = [{
        "source": s, "target": t,
        "relation": d.get("relation", "related-to"),
        "weight": float(d.get("weight", 1) or 1),
        "note": d.get("note", ""),
    } for s, t, d in graph.edges(data=True)]

    export = {
        "generated_from": {
            "graph": str(GRAPH.relative_to(ROOT)),
            "centrality": str(CENTRALITY.relative_to(ROOT)),
            "communities": str(COMMUNITIES.relative_to(ROOT)),
        },
        "counts": {
            "concepts": len(nodes),
            "relations": len(edges),
            "subjects": len({n["subject_code"] for n in nodes if n["subject_code"]}),
            "modules": len({n["module_id"] for n in nodes if n["module_id"]}),
            "communities": len({n["community_id"] for n in nodes if n["community_id"]}),
        },
        "nodes": nodes,
        "edges": edges,
    }
    JSON_OUT.write_text(json.dumps(export, indent=2) + "\n", encoding="utf-8")

    by_subject = defaultdict(list)
    for node, data in graph.nodes(data=True):
        if data.get("subject_code"):
            by_subject[data["subject_code"]].append(node)

    bridges = [n for n in nodes if n["betweenness"] > 0][:8]
    starts = sorted((n for n in nodes if n["prerequisites"] == 0),
                    key=lambda n: (-n["leads_to"], n["name"]))[:8]
    crossing = []
    for s, t, d in graph.edges(data=True):
        a, b = graph.nodes[s], graph.nodes[t]
        if a.get("subject_code") and b.get("subject_code") and a["subject_code"] != b["subject_code"]:
            crossing.append((a.get("name", s), a["subject_code"], b.get("name", t), b["subject_code"],
                             d.get("relation", "")))

    md = [
        "# What to study first — D14",
        "",
        "Written from the concept graph, not from opinion. Every claim below comes "
        "from `data/processed/graph_export.json`: how many concepts depend on each "
        "one, and where it sits on the paths between topics.",
        "",
        "## Start with these",
        "",
        "They need nothing before them, and the most other concepts follow from them. "
        "If you are starting a subject cold, start here.",
        "",
    ]
    for n in starts:
        md.append(f"- **{n['name']}** ({subjects.get(n['subject_code'], n['subject_code'])}) "
                  f"— {n['leads_to']} concepts build on it")

    md += [
        "",
        "## Do not skip these",
        "",
        "These sit on the paths between topics. Miss one and the concepts beyond it "
        "stop making sense, even if the syllabus treats it as a small item.",
        "",
    ]
    for n in bridges:
        md.append(f"- **{n['name']}** ({subjects.get(n['subject_code'], n['subject_code'])}) "
                  f"— bridge score {n['betweenness']:.4f}, {n['leads_to']} concepts beyond it")

    md += [
        "",
        "## Where one subject depends on another",
        "",
        "These are easy to miss because they cross a timetable boundary: the concept "
        "you need was taught in a different subject.",
        "",
    ]
    for a, ac, b, bc, rel in crossing:
        word = "before" if rel == "prerequisite" else "alongside"
        md.append(f"- Learn **{a}** ({subjects.get(ac, ac)}) {word} "
                  f"**{b}** ({subjects.get(bc, bc)})")

    md += ["", "## Order within each subject", "",
           "Each step only needs the steps above it. Concepts on the same line can be "
           "learnt in any order.", ""]
    for code in sorted(by_subject):
        md += [f"### {subjects.get(code, code)} ({code})", ""]
        ordered = layers(graph, by_subject[code])
        if ordered is None:
            md += ["_The prerequisites for this subject contain a loop; fix them in "
                   "relations.csv before relying on this order._", ""]
            continue
        for i, layer in enumerate(ordered, start=1):
            names = ", ".join(graph.nodes[n].get("name", n) for n in layer)
            md.append(f"{i}. {names}")
        md.append("")

    md += [
        "## How to read this",
        "",
        "**Bridge score** is betweenness centrality: how often a concept lies on the "
        "shortest path between two others. A high score means it carries traffic "
        "between topics rather than just having many neighbours.",
        "",
        "**A caution.** Only Artificial Intelligence and Machine Learning have concepts "
        "drawn from the syllabus PDFs. The relations for the other eight subjects were "
        "written by hand from standard course content, so the ordering there is a "
        "reasonable default rather than a finding. Check it against the real syllabus "
        "before quoting it.",
        "",
    ]
    MD_OUT.write_text("\n".join(md), encoding="utf-8")

    print(f"Concepts   : {export['counts']['concepts']}")
    print(f"Relations  : {export['counts']['relations']}")
    print(f"Communities: {export['counts']['communities']}")
    print(f"Cross-subject dependencies: {len(crossing)}")
    print("\nStart with:")
    for n in starts[:5]:
        print(f"  {n['name']:<28} {n['leads_to']} follow")
    print(f"\nSaved {JSON_OUT}")
    print(f"Saved {MD_OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
