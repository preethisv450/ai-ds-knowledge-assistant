from src.data.concepts import (CONCEPTS_HEADER, RELATIONS_HEADER, check, load_concepts, load_relations,
                               slug, stats, suggest_concepts, write_csv)
from tests.data_helpers import CURRICULUM


def write(tmp_path, name, header, lines):
    p = tmp_path / name
    p.write_text(",".join(header) + "\n" + "\n".join(lines) + "\n")
    return p


def test_slug_and_default_ids(tmp_path):
    assert slug("Gradient Descent!") == "gradient-descent"
    p = write(tmp_path, "c.csv", CONCEPTS_HEADER, [",Rational Agent,AI201,AI201-M1,agent|agents"])
    concepts, problems = load_concepts(p)
    assert problems == []
    assert concepts[0]["concept_id"] == "rational-agent"
    assert concepts[0]["aliases"] == ["agent", "agents"]


def test_duplicate_concept_id_is_reported(tmp_path):
    p = write(tmp_path, "c.csv", CONCEPTS_HEADER,
              ["peas,PEAS,AI201,AI201-M1,", "peas,PEAS again,AI201,AI201-M1,"])
    concepts, problems = load_concepts(p)
    assert len(concepts) == 1 and any("used twice" in x for x in problems)


def test_missing_file_and_missing_column(tmp_path):
    _, problems = load_concepts(tmp_path / "nope.csv")
    assert any("not found" in x for x in problems)
    p = tmp_path / "c.csv"
    p.write_text("concept_id,module_id\nx,AI201-M1\n")
    _, problems = load_concepts(p)
    assert any("missing column" in x for x in problems)


def test_relations_validate_type_weight_and_self_loops(tmp_path):
    p = write(tmp_path, "r.csv", RELATIONS_HEADER, [
        "a,b,prerequisite,2,fine",
        "a,a,related-to,1,points at itself",
        "a,b,sibling-of,1,bad type",
        "b,c,related-to,zero,bad weight",
        "c,d,related-to,0,non positive",
        "a,,related-to,1,no target",
    ])
    relations, problems = load_relations(p)
    assert [r["source"] for r in relations] == ["a"]
    assert relations[0]["weight"] == 2.0
    joined = " ".join(problems)
    assert "points at itself" in joined and "must be one of" in joined
    assert "not a number" in joined and "greater than 0" in joined and "both source and target" in joined


def test_an_undirected_edge_listed_both_ways_is_a_duplicate(tmp_path):
    p = write(tmp_path, "r.csv", RELATIONS_HEADER, ["a,b,related-to,1,", "b,a,related-to,1,"])
    relations, problems = load_relations(p)
    assert len(relations) == 1 and any("listed twice" in x for x in problems)


def test_a_prerequisite_in_both_directions_is_kept(tmp_path):
    """A -> B and B -> A as prerequisites is a cycle to notice, not a duplicate row."""
    p = write(tmp_path, "r.csv", RELATIONS_HEADER, ["a,b,prerequisite,1,", "b,a,prerequisite,1,"])
    relations, problems = load_relations(p)
    assert len(relations) == 2 and problems == []


def test_check_against_the_curriculum(tmp_path):
    c = write(tmp_path, "c.csv", CONCEPTS_HEADER, [
        "peas,PEAS,AI201,AI201-M1,",
        "ghost,Ghost,ZZ999,ZZ999-M1,",
        "wrongmod,Wrong Module,AI201,CS101-M1,",
    ])
    r = write(tmp_path, "r.csv", RELATIONS_HEADER, ["peas,missing-one,related-to,1,"])
    concepts, _ = load_concepts(c)
    relations, _ = load_relations(r)
    problems = " ".join(check(concepts, relations, CURRICULUM))
    assert "subject ZZ999 is not in curriculum.json" in problems
    assert "does not belong to subject AI201" in problems
    assert "missing-one is not in concepts.csv" in problems


def test_duplicate_name_inside_one_module(tmp_path):
    c = write(tmp_path, "c.csv", CONCEPTS_HEADER, ["a,Search,AI201,AI201-M2,", "b,search,AI201,AI201-M2,"])
    concepts, _ = load_concepts(c)
    assert any("already appears" in x for x in check(concepts, [], CURRICULUM))


def test_stats_counts_and_finds_isolated_concepts(tmp_path):
    c = write(tmp_path, "c.csv", CONCEPTS_HEADER,
              ["a,A,AI201,AI201-M1,", "b,B,AI201,AI201-M1,", "lonely,Lonely,AI201,AI201-M2,"])
    r = write(tmp_path, "r.csv", RELATIONS_HEADER, ["a,b,prerequisite,1,"])
    s = stats(*(load_concepts(c)[0], load_relations(r)[0]))
    assert s["concepts"] == 3 and s["prerequisite"] == 1 and s["related_to"] == 0
    assert s["isolated"] == ["lonely"] and s["per_module"]["AI201-M1"] == 2


def test_suggest_concepts_ranks_repeated_terms_per_module():
    chunks = [
        {"module_id": "AI201-M2", "subject_code": "AI201",
         "text": "heuristic search expands nodes. heuristic search is admissible. the student will study"},
        {"module_id": "AI201-M2", "subject_code": "AI201",
         "text": "admissible heuristic never overestimates. admissible heuristic keeps A star optimal"},
    ]
    rows = suggest_concepts(chunks, per_module=5)
    names = [r["name"].lower() for r in rows]
    assert "heuristic search" in names or "admissible heuristic" in names
    assert all(r["module_id"] == "AI201-M2" for r in rows)
    assert not any("student" in n or "study" in n for n in names)   # stopwords are dropped


def test_write_csv_round_trips_aliases(tmp_path):
    rows = [{"concept_id": "x", "name": "X", "subject_code": "AI201", "module_id": "AI201-M1",
             "aliases": ["ex", "eks"], "_count": 9}]
    p = write_csv(rows, tmp_path / "out.csv", CONCEPTS_HEADER)
    back, problems = load_concepts(p)
    assert problems == [] and back[0]["aliases"] == ["ex", "eks"]
    assert "_count" not in p.read_text().splitlines()[0]
