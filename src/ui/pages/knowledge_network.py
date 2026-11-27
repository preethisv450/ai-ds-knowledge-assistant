"""D14: the concept graph, laid out so a student can read it.

Nodes are concepts from data/concepts/concepts.csv, edges the relations in
relations.csv. The page shows one subject at a time, lays prerequisites out
top to bottom so the learning order is visible, and colours each concept by
the module it belongs to. Betweenness is computed once and kept in session
state for the bridge-concepts panel (D15).
"""
import json
from pathlib import Path

import networkx as nx
import streamlit as st
import streamlit.components.v1 as components
from pyvis.network import Network

from src.data.concepts import load_concepts, load_relations

ROOT = Path(__file__).resolve().parents[3]
CONCEPTS_PATH = ROOT / "data" / "concepts" / "concepts.csv"
RELATIONS_PATH = ROOT / "data" / "concepts" / "relations.csv"

MODULE_COLORS = ["#2E5BBA", "#22A447", "#F59E0B", "#8B5CD6", "#EF4444", "#06B6D4"]
EVERYTHING = "All subjects"
ALL_MODULES = "All modules"

# Zoom controls. pyvis puts the vis.js instance in a global called `network`,
# so the buttons can drive it directly.
ZOOM_BAR = """
<style>
  body{position:relative;}
  #knzoom{position:absolute; top:12px; right:12px; display:flex; gap:6px; z-index:5;}
  #knzoom button{height:34px; min-width:34px; padding:0 10px; border-radius:8px;
    border:1px solid #DCE3EF; background:#fff; color:#0F2A62; font-size:17px;
    font-weight:700; line-height:1; cursor:pointer; box-shadow:0 1px 3px rgba(15,42,98,.12);}
  #knzoom button:hover{background:#E2EBF9; border-color:#0F2A62;}
  #knzoom button.wide{font-size:13px;}
</style>
<div id="knzoom">
  <button onclick="knZoom(1.3)" title="Zoom in">+</button>
  <button onclick="knZoom(0.77)" title="Zoom out">&minus;</button>
  <button class="wide" onclick="knFit()" title="Fit everything on screen">Fit</button>
</div>
<script>
  function knZoom(f){ if(!window.network) return;
    network.moveTo({scale: network.getScale()*f, animation:{duration:200}}); }
  function knFit(){ if(!window.network) return; network.fit({animation:{duration:250}}); }
  // Start at a size the labels are readable at; Fit is one click away.
  setTimeout(function(){
    if(window.network && network.getScale() < 0.72){ network.moveTo({scale:0.72}); }
  }, 400);
</script>
"""


@st.cache_data(show_spinner=False)
def load_graph():
    """Return (bundle, problems). bundle is None when there is no concept data yet."""
    concepts, c_problems = load_concepts(CONCEPTS_PATH)
    relations, r_problems = load_relations(RELATIONS_PATH)
    if not concepts:
        return None, c_problems + r_problems

    graph = nx.DiGraph()
    ids = {c["concept_id"] for c in concepts}
    for c in concepts:
        graph.add_node(
            c["concept_id"],
            label=c["name"],
            module_id=c["module_id"] or "",
            subject_code=c["subject_code"] or "",
        )
    for r in relations:
        if r["source"] in ids and r["target"] in ids:
            graph.add_edge(r["source"], r["target"], relation=r["relation"], weight=r["weight"])

    betweenness = nx.betweenness_centrality(graph) if graph.number_of_edges() else {n: 0.0 for n in graph}
    return {"graph": graph, "betweenness": betweenness}, c_problems + r_problems


@st.cache_data(show_spinner=False)
def curriculum_names():
    """{'AI201': 'Artificial Intelligence'}, {'AI201-M1': 'Introduction to AI'}."""
    subjects, modules = {}, {}
    path = ROOT / "data" / "processed" / "curriculum.json"
    try:
        curriculum = json.loads(path.read_text())
    except Exception:
        return subjects, modules
    for year in curriculum.get("years", []):
        for sem in year.get("semesters", []):
            for subject in sem.get("subjects", []):
                subjects[subject.get("code")] = subject.get("name")
                for module in subject.get("modules", []):
                    modules[module.get("id")] = module.get("title")
    return subjects, modules


def build_html(graph, colour_of):
    """A top-to-bottom layered graph: a concept sits below everything it needs first."""
    net = Network(height="520px", width="100%", directed=True, bgcolor="#ffffff",
                  font_color="#18233A", cdn_resources="in_line")

    for node, data in graph.nodes(data=True):
        needs = [graph.nodes[s]["label"] for s, _, d in graph.in_edges(node, data=True)
                 if d.get("relation") == "prerequisite"]
        tooltip = data["label"] + ("<br>Learn first: " + ", ".join(needs) if needs else "<br>No prerequisites")
        net.add_node(
            node,
            label=data["label"],
            title=tooltip,
            shape="box",
            color={"background": colour_of.get(data["module_id"], "#2E5BBA"),
                   "border": colour_of.get(data["module_id"], "#2E5BBA")},
            font={"color": "#FFFFFF", "size": 16, "face": "Inter, Segoe UI, sans-serif"},
            margin=10,
        )

    for source, target, data in graph.edges(data=True):
        related = data.get("relation") == "related-to"
        net.add_edge(
            source, target,
            dashes=related,
            arrows="" if related else "to",
            color="#C2D0EA" if related else "#8AA6D6",
            width=1 if related else 2,
            title="taught alongside" if related else "learn this first",
        )

    net.set_options(json.dumps({
        "layout": {"hierarchical": {"enabled": True, "direction": "UD", "sortMethod": "directed",
                                    "levelSeparation": 110, "nodeSpacing": 210, "treeSpacing": 240}},
        "physics": {"enabled": False},
        "interaction": {"hover": True, "dragNodes": True, "zoomView": True, "dragView": True},
    }))
    return net.generate_html(notebook=False).replace("</body>", ZOOM_BAR + "</body>")


def show_knowledge_network():
    bundle, problems = load_graph()

    if not bundle:
        st.info(
            "The knowledge graph needs data/concepts/concepts.csv and relations.csv. "
            "Run `python scripts/extract_concepts.py` for candidate concepts, curate them, "
            "then `python scripts/check_concepts.py` to validate."
        )
        if problems:
            with st.expander("Details"):
                for p in problems:
                    st.caption(p)
        return

    st.session_state["network_bundle"] = bundle
    graph = bundle["graph"]
    subject_names, module_names = curriculum_names()

    codes = sorted({d["subject_code"] for _, d in graph.nodes(data=True) if d["subject_code"]})
    options = codes + [EVERYTHING]
    picked_elsewhere = (st.session_state.get("selection") or {}).get("subject_code")
    default = options.index(picked_elsewhere) if picked_elsewhere in options else 0

    left, right = st.columns(2)
    with left:
        chosen = st.selectbox(
            "Subject",
            options,
            index=default,
            format_func=lambda c: EVERYTHING if c == EVERYTHING else f"{subject_names.get(c, c)} ({c})",
            key="network_subject",
        )

    if chosen != EVERYTHING:
        keep = [n for n, d in graph.nodes(data=True) if d["subject_code"] == chosen]
        graph = graph.subgraph(keep).copy()

        in_subject = sorted({d["module_id"] for _, d in graph.nodes(data=True) if d["module_id"]})
        module_options = [ALL_MODULES] + in_subject
        wanted = (st.session_state.get("selection") or {}).get("module_id")
        with right:
            module_choice = st.selectbox(
                "Module",
                module_options,
                index=module_options.index(wanted) if wanted in module_options else 0,
                format_func=lambda m: ALL_MODULES if m == ALL_MODULES else module_names.get(m, m),
                key=f"network_module|{chosen}",
            )
        if module_choice != ALL_MODULES:
            keep = [n for n, d in graph.nodes(data=True) if d["module_id"] == module_choice]
            graph = graph.subgraph(keep).copy()

    module_ids = sorted({d["module_id"] for _, d in graph.nodes(data=True) if d["module_id"]})
    colour_of = {mid: MODULE_COLORS[i % len(MODULE_COLORS)] for i, mid in enumerate(module_ids)}
    st.session_state["network_legend"] = [
        (module_names.get(mid, mid), colour_of[mid]) for mid in module_ids
    ]

    if graph.number_of_nodes() == 0:
        st.info("No concepts recorded for this subject yet.")
        st.session_state["network_table"] = []
        st.session_state["network_bridges"] = []
        return

    # D15: what the side panels show. The table ranks what is on screen by how
    # many links each concept has; bridges use betweenness over the whole
    # curriculum, so a concept scores for what it unlocks in other modules too.
    ranked = sorted(graph.degree, key=lambda kv: (-kv[1], graph.nodes[kv[0]]["label"]))
    st.session_state["network_table"] = [
        (graph.nodes[n]["label"], d) for n, d in ranked[:8]
    ]

    whole, scores = bundle["graph"], bundle["betweenness"]
    on_screen = [(n, scores.get(n, 0.0)) for n in graph.nodes if scores.get(n, 0.0) > 0]
    on_screen.sort(key=lambda kv: -kv[1])
    top = on_screen[:5]
    highest = top[0][1] if top else 0
    st.session_state["network_bridges"] = [
        (whole.nodes[n]["label"],
         module_names.get(whole.nodes[n]["module_id"], whole.nodes[n]["module_id"]),
         round(100 * score / highest) if highest else 0)
        for n, score in top
    ]

    components.html(build_html(graph, colour_of), height=540, scrolling=False)
    st.caption(
        f"{graph.number_of_nodes()} concepts · arrows point from what to learn first "
        "to what it leads to · hover a concept to see what it needs"
    )
