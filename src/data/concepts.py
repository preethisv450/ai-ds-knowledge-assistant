"""D5: the concept nodes and edges that the network analysis (D11-D13) is built from.

Two small CSV files, kept by hand in Sheets and checked by this module:

  data/concepts/concepts.csv   concept_id, name, subject_code, module_id, aliases
  data/concepts/relations.csv  source, target, relation, weight, note

`relation` is 'prerequisite' (source must be understood before target) or 'related-to'
(the two are taught together). Prerequisite edges are directed; related-to edges are not.

suggest_concepts() reads the syllabus and proposes candidate terms per module. They are
candidates only - a person keeps the real ones and deletes the rest.
"""
import csv
import re
from collections import Counter
from pathlib import Path

from src.data.schema import RELATION_TYPES, SUBJECT_CODE, subject_of_module

CONCEPTS_HEADER = ["concept_id", "name", "subject_code", "module_id", "aliases"]
RELATIONS_HEADER = ["source", "target", "relation", "weight", "note"]

STOPWORDS = set("""
a an the and or of to in for on with without by from as at into over under is are was were be been being
this that these those it its their there here which who whom whose what when where why how
can could should would may might must will shall do does did done has have had
not no nor only own same so than too very just also such both each few more most other some any all
student students course courses subject subjects module modules unit units syllabus semester year
introduction overview basics basic concept concepts topics topic following above below example examples
using used use uses study studies understand understanding learn learning
""".split())
_WORD = re.compile(r"[A-Za-z][A-Za-z\-]+")


def slug(name):
    """'Gradient Descent' -> 'gradient-descent'. Used as concept_id when none is given."""
    return re.sub(r"[^a-z0-9]+", "-", (name or "").strip().lower()).strip("-")


# ---------------------------------------------------------------- reading
def _rows(path, header, required):
    path = Path(path)
    if not path.exists():
        return [], [f"{path} not found"]
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        missing = [c for c in required if c not in (reader.fieldnames or [])]
        if missing:
            return [], [f"{path.name}: missing column(s) {', '.join(missing)}"]
        return list(reader), []


def load_concepts(path):
    """Return ([concept dicts], [problems])."""
    rows, problems = _rows(path, CONCEPTS_HEADER, ["name"])
    concepts, seen = [], {}
    for n, r in enumerate(rows, start=2):
        name = (r.get("name") or "").strip()
        if not name:
            continue
        cid = (r.get("concept_id") or "").strip() or slug(name)
        if cid in seen:
            problems.append(f"line {n}: concept_id {cid!r} is used twice (also line {seen[cid]})")
            continue
        seen[cid] = n
        concepts.append({
            "concept_id": cid,
            "name": name,
            "subject_code": (r.get("subject_code") or "").strip().upper() or None,
            "module_id": (r.get("module_id") or "").strip().upper() or None,
            "aliases": [a.strip() for a in (r.get("aliases") or "").split("|") if a.strip()],
        })
    return concepts, problems


def load_relations(path):
    """Return ([relation dicts], [problems])."""
    rows, problems = _rows(path, RELATIONS_HEADER, ["source", "target"])
    relations, seen = [], set()
    for n, r in enumerate(rows, start=2):
        src, tgt = (r.get("source") or "").strip(), (r.get("target") or "").strip()
        if not src and not tgt:
            continue
        if not src or not tgt:
            problems.append(f"line {n}: a relation needs both source and target")
            continue
        rel = (r.get("relation") or "related-to").strip().lower()
        if rel not in RELATION_TYPES:
            problems.append(f"line {n}: relation {rel!r} must be one of {', '.join(RELATION_TYPES)}")
            continue
        if src == tgt:
            problems.append(f"line {n}: {src} points at itself")
            continue
        weight_raw = (r.get("weight") or "1").strip() or "1"
        try:
            weight = float(weight_raw)
        except ValueError:
            problems.append(f"line {n}: weight {weight_raw!r} is not a number")
            continue
        if weight <= 0:
            problems.append(f"line {n}: weight must be greater than 0")
            continue
        key = (src, tgt, rel) if rel == "prerequisite" else tuple(sorted((src, tgt))) + (rel,)
        if key in seen:
            problems.append(f"line {n}: {src} -> {target_label(tgt)} ({rel}) is listed twice")
            continue
        seen.add(key)
        relations.append({"source": src, "target": tgt, "relation": rel, "weight": weight,
                          "note": (r.get("note") or "").strip()})
    return relations, problems


def target_label(t):
    return t


# ---------------------------------------------------------------- checking
def check(concepts, relations, curriculum=None):
    """Cross-check the two files against each other and against the curriculum."""
    problems = []
    ids = {c["concept_id"] for c in concepts}
    by_module = {}
    known_modules, known_codes = set(), set()
    if curriculum:
        from src.data.schema import iter_modules, iter_subjects
        known_modules = {(m.get("id") or "").upper() for _, _, _, m in iter_modules(curriculum)}
        known_codes = {(s.get("code") or "").upper() for _, _, s in iter_subjects(curriculum)}

    for c in concepts:
        code, mid = c["subject_code"], c["module_id"]
        if code and not SUBJECT_CODE.match(code):
            problems.append(f"{c['concept_id']}: subject_code {code!r} does not look like a subject code")
        if curriculum and code and code not in known_codes:
            problems.append(f"{c['concept_id']}: subject {code} is not in curriculum.json")
        if curriculum and mid and mid not in known_modules:
            problems.append(f"{c['concept_id']}: module {mid} is not in curriculum.json")
        if mid and code and subject_of_module(mid) not in (None, code):
            problems.append(f"{c['concept_id']}: module {mid} does not belong to subject {code}")
        key = (mid or code or "", c["name"].lower())
        if key in by_module:
            problems.append(f"{c['concept_id']}: {c['name']!r} already appears in {mid or code or 'the same scope'}")
        by_module[key] = c["concept_id"]

    for r in relations:
        for end in ("source", "target"):
            if r[end] not in ids:
                problems.append(f"relation {r['source']} -> {r['target']}: {r[end]} is not in concepts.csv")
    return problems


def stats(concepts, relations):
    per_module = Counter(c["module_id"] or c["subject_code"] or "(unassigned)" for c in concepts)
    return {
        "concepts": len(concepts),
        "relations": len(relations),
        "prerequisite": sum(r["relation"] == "prerequisite" for r in relations),
        "related_to": sum(r["relation"] == "related-to" for r in relations),
        "unassigned": sum(1 for c in concepts if not c["module_id"]),
        "per_module": dict(per_module),
        "isolated": sorted({c["concept_id"] for c in concepts}
                           - {r["source"] for r in relations} - {r["target"] for r in relations}),
    }


# ---------------------------------------------------------------- suggesting
def suggest_concepts(chunks, per_module=12, min_count=2):
    """Propose candidate concept names per module from indexed chunks.

    Candidates are the most frequent one- and two-word terms that are not stopwords.
    This is a first draft to curate, not an extraction of real concepts: a person keeps
    the terms that are genuinely concepts and deletes the rest."""
    buckets = {}
    for c in chunks:
        key = (c.get("module_id"), c.get("subject_code"))
        buckets.setdefault(key, []).append(c.get("text", ""))

    out = []
    for (module_id, code), texts in sorted(buckets.items(), key=lambda kv: str(kv[0])):
        words = []
        for t in texts:
            words += [w.lower() for w in _WORD.findall(t)]
        singles = Counter(w for w in words if w not in STOPWORDS and len(w) > 3)
        pairs = Counter()
        for a, b in zip(words, words[1:]):
            if a not in STOPWORDS and b not in STOPWORDS and len(a) > 2 and len(b) > 2:
                pairs[f"{a} {b}"] += 1
        ranked = [(t, n) for t, n in pairs.most_common(per_module * 2) if n >= min_count]
        in_pairs = {w for t, _ in ranked for w in t.split()}
        ranked += [(t, n) for t, n in singles.most_common(per_module * 3)
                   if n >= min_count and t not in in_pairs]
        ranked.sort(key=lambda x: (-x[1], x[0]))
        for term, n in ranked[:per_module]:
            out.append({"concept_id": slug(term), "name": term.title(), "subject_code": code,
                        "module_id": module_id, "aliases": "", "_count": n})
    return out


def write_csv(rows, path, header):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=header, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: ("|".join(v) if isinstance(v, list) else v) for k, v in r.items() if k in header})
    return path
