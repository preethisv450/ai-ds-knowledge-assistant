"""D13: Louvain community detection over the concept graph.

Runs the Louvain method (Blondel et al. 2008) on the undirected form of
data/processed/concept_graph.graphml, gives every community a theme label
drawn from the modules and subjects its concepts belong to, and reports the
checks that say whether the clustering is sensible: modularity, community
sizes, and how cleanly each community maps onto one module or subject.

Uses networkx.community.louvain_communities, which implements the same
algorithm as the python-louvain package. If python-louvain is installed it is
used instead, so results can be compared.

    python scripts/communities_report.py
    python scripts/communities_report.py --seed=7 --resolution=1.0
"""
import csv
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import networkx as nx

ROOT = Path(__file__).resolve().parents[1]
GRAPH = ROOT / "data" / "processed" / "concept_graph.graphml"
CENTRALITY = ROOT / "data" / "processed" / "centrality.csv"
CURRICULUM = ROOT / "data" / "processed" / "curriculum.json"
CSV_OUT = ROOT / "data" / "processed" / "communities.csv"
MD_OUT = ROOT / "docs" / "communities_report.md"


def names():
    subjects, modules = {}, {}
    try:
        data = json.loads(CURRICULUM.read_text(encoding="utf-8"))
    except Exception:
        return subjects, modules
    for year in data.get("years", []):
        for sem in year.get("semesters", []):
            for subject in sem.get("subjects", []):
                subjects[subject.get("code")] = subject.get("name")
                for module in subject.get("modules", []):
                    modules[module.get("id")] = module.get("title")
    return subjects, modules


def detect(graph, seed, resolution):
    undirected = nx.Graph()
    undirected.add_nodes_from(graph.nodes(data=True))
    for src, tgt, data in graph.edges(data=True):
        weight = float(data.get("weight", 1) or 1)
        if undirected.has_edge(src, tgt):
            undirected[src][tgt]["weight"] += weight
        else:
            undirected.add_edge(src, tgt, weight=weight)

    try:
        import community as community_louvain  # python-louvain
        partition = community_louvain.best_partition(
            undirected, weight="weight", random_state=seed, resolution=resolution)
        groups = {}
        for node, cid in partition.items():
            groups.setdefault(cid, set()).add(node)
        communities = [groups[k] for k in sorted(groups)]
        library = "python-louvain"
    except ImportError:
        communities = nx.community.louvain_communities(
            undirected, weight="weight", seed=seed, resolution=resolution)
        library = "networkx.community.louvain_communities"

    communities = sorted(communities, key=len, reverse=True)
    return undirected, communities, library


def label_for(members, graph, subjects, modules):
    """A theme label: the module if the community is mostly one, else the subject."""
    mods = Counter(graph.nodes[n].get("module_id", "") for n in members if graph.nodes[n].get("module_id"))
    subs = Counter(graph.nodes[n].get("subject_code", "") for n in members if graph.nodes[n].get("subject_code"))
    total = len(members)

    if mods:
        mod, count = mods.most_common(1)[0]
        if count / total >= 0.6:
            return modules.get(mod, mod), mod, round(100 * count / total)
    if subs:
        sub, count = subs.most_common(1)[0]
        if count / total >= 0.6:
            return f"{subjects.get(sub, sub)} — core", sub, round(100 * count / total)
    top = ", ".join(subjects.get(s, s) for s, _ in subs.most_common(2))
    best = subs.most_common(1)[0][1] if subs else 0
    return f"Across subjects: {top}", "", round(100 * best / total) if total else 0


def centrality_lookup():
    scores = {}
    if CENTRALITY.exists():
        with open(CENTRALITY, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                scores[row["concept_id"]] = float(row["degree_centrality"])
    return scores


def main():
    seed = int(next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--seed=")), 42))
    resolution = float(next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--resolution=")), 1.0))
    if not GRAPH.exists():
        print(f"{GRAPH} not found. Run scripts/build_concept_graph.py first.")
        return 1

    graph = nx.read_graphml(GRAPH)
    subjects, modules = names()
    undirected, communities, library = detect(graph, seed, resolution)
    modularity = nx.community.modularity(undirected, communities, weight="weight")
    scores = centrality_lookup()

    rows, blocks = [], []
    for i, members in enumerate(communities, start=1):
        label, anchor, purity = label_for(members, graph, subjects, modules)
        ordered = sorted(members, key=lambda n: (-scores.get(n, 0.0), graph.nodes[n].get("name", n)))
        for node in members:
            rows.append({
                "concept_id": node,
                "name": graph.nodes[node].get("name", node),
                "subject_code": graph.nodes[node].get("subject_code", ""),
                "module_id": graph.nodes[node].get("module_id", ""),
                "community_id": i,
                "community_label": label,
            })
        subs = sorted({graph.nodes[n].get("subject_code", "") for n in members if graph.nodes[n].get("subject_code")})
        blocks.append({
            "id": i, "label": label, "size": len(members), "purity": purity,
            "subjects": subs,
            "concepts": [graph.nodes[n].get("name", n) for n in ordered],
        })

    rows.sort(key=lambda r: (r["community_id"], r["name"]))
    with open(CSV_OUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "community_id", "community_label", "concept_id", "name", "subject_code", "module_id"])
        writer.writeheader()
        for r in rows:
            writer.writerow({k: r[k] for k in writer.fieldnames})

    singletons = [b for b in blocks if b["size"] == 1]
    mixed = [b for b in blocks if len(b["subjects"]) > 1]

    md = [
        "# Concept communities — D13",
        "",
        f"Method: Louvain (Blondel et al. 2008), run with `{library}` on the undirected "
        f"form of the concept graph, weighted by relation strength, seed {seed}, "
        f"resolution {resolution}.",
        "",
        f"- Communities found: **{len(communities)}**",
        f"- Modularity: **{modularity:.3f}**",
        f"- Concepts: {graph.number_of_nodes()} across {graph.number_of_edges()} relations",
        "",
        "Modularity above about 0.3 means the clustering found real structure rather "
        "than splitting an evenly connected graph at random.",
        "",
        "## Communities",
        "",
    ]
    for b in blocks:
        shown = ", ".join(b["concepts"][:8])
        if len(b["concepts"]) > 8:
            shown += f", and {len(b['concepts']) - 8} more"
        md += [
            f"### {b['id']}. {b['label']}",
            "",
            f"{b['size']} concepts · {b['purity']}% from its dominant module or subject · "
            f"subjects: {', '.join(b['subjects']) or 'none recorded'}",
            "",
            shown,
            "",
        ]

    md += [
        "## Do the clusters make sense?",
        "",
        f"- **Alignment with the syllabus.** {sum(1 for b in blocks if b['purity'] >= 60)} of "
        f"{len(blocks)} communities are at least 60% one module or subject, which is what "
        "you would expect if the hand-written relations follow the teaching order.",
        f"- **Communities spanning subjects:** {len(mixed)}. "
        + ("These are the interesting ones: they show where the curriculum genuinely "
           "connects across subject boundaries." if mixed else "None, so every cluster sits inside one subject."),
        f"- **Single-concept communities:** {len(singletons)}. "
        + ("Each is a concept with no relations recorded yet; add edges or remove it."
           if singletons else "None, so every concept belongs to a group."),
        "",
        "Re-run with `--resolution=0.8` for fewer, larger communities or `--resolution=1.4` "
        "for more, smaller ones, and `--seed=` to confirm the grouping is stable.",
        "",
        f"Full assignment for all {len(rows)} concepts: `data/processed/communities.csv`.",
        "",
    ]
    MD_OUT.write_text("\n".join(md), encoding="utf-8")

    print(f"Library    : {library}")
    print(f"Communities: {len(communities)}")
    print(f"Modularity : {modularity:.3f}")
    print(f"Singletons : {len(singletons)}   Cross-subject: {len(mixed)}")
    print()
    for b in blocks[:8]:
        print(f"  {b['id']:>2}. {b['label'][:44]:<44} {b['size']:>3} concepts  {b['purity']:>3}% pure")
    if len(blocks) > 8:
        print(f"      ... and {len(blocks) - 8} more")
    print(f"\nSaved {CSV_OUT}")
    print(f"Saved {MD_OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
