import json

from src.backend import cache as cachemod, config, gemini_client as gc, rag, study
from src.backend.cache import Cache, index_fingerprint, make_key
from tests.test_gemini_client import FakeAPIError, FakeClient, NOSLEEP, QUOTA_MSG

SEL = {"subject": "AI", "subject_code": "AI201", "module": "NN", "module_id": "AI201-M1"}
R = [{"document": "AI.pdf", "page": 4, "snippet": "s", "score": 0.5, "chunk_id": "a", "text": "A perceptron computes y."}]
ret = lambda q, k=5, where=None: R


def counting(text):
    calls = []

    def gen(prompt, system=None):
        calls.append(prompt)
        return text
    gen.calls = calls
    return gen


# ---- Cache ----
def test_put_get_roundtrip_and_miss(tmp_path):
    c = Cache(tmp_path)
    assert c.get("k", "x") is None
    c.put("k", "x", {"a": [1, 2]})
    assert c.get("k", "x") == {"a": [1, 2]} and c.get("other", "x") is None


def test_expiry_corruption_and_unwritable_dir_are_misses_not_errors(tmp_path):
    t = [1000.0]
    c = Cache(tmp_path, ttl_s=10, now=lambda: t[0])
    c.put("k", "x", 1)
    t[0] = 1011.0
    assert c.get("k", "x") is None
    (tmp_path / "k-bad.json").write_text("{not json")
    assert c.get("k", "bad") is None
    blocker = tmp_path / "file"
    blocker.write_text("x")
    Cache(blocker / "sub").put("k", "x", 1)  # directory cannot be created: silently ignored


def test_clear_counts_removed_entries(tmp_path):
    c = Cache(tmp_path)
    c.put("a", "1", 1)
    c.put("a", "2", 2)
    assert c.clear() == 2 and c.get("a", "1") is None


def test_make_key_depends_on_every_part():
    assert make_key("a", 1) == make_key("a", 1)
    assert make_key("a", 1) != make_key("a", 2) and make_key("a", 1) != make_key("b", 1)


def test_index_fingerprint_changes_when_index_is_rebuilt(tmp_path):
    assert index_fingerprint(tmp_path) == "none"
    for n in ("chunks.json", "faiss.index", "meta.json"):
        (tmp_path / n).write_text("1")
    a = index_fingerprint(tmp_path)
    (tmp_path / "chunks.json").write_text("12345")
    assert a != index_fingerprint(tmp_path) != "none"


def test_resolve_uses_real_cache_only_when_nothing_is_injected(tmp_path, monkeypatch):
    mine = Cache(tmp_path)
    monkeypatch.setattr(cachemod, "_default", mine)
    assert cachemod.resolve(cachemod.AUTO) is mine
    assert cachemod.resolve(cachemod.AUTO, None, lambda: 1) is None
    assert cachemod.resolve(None) is None and cachemod.resolve(mine) is mine


# ---- study: second call is free, refresh and parameters bypass ----
def test_summary_cached_second_call_makes_no_gemini_call(tmp_path):
    c, gen = Cache(tmp_path), counting("- fact [S1]")
    a = study.generate_summary(SEL, retrieve_fn=ret, generate_fn=gen, cache=c)
    b = study.generate_summary(SEL, retrieve_fn=ret, generate_fn=gen, cache=c)
    assert a == b and len(gen.calls) == 1
    study.generate_summary(SEL, retrieve_fn=ret, generate_fn=gen, cache=c, refresh=True)
    assert len(gen.calls) == 2
    study.generate_summary(dict(SEL, module_id="AI201-M2", module="Other"), retrieve_fn=ret, generate_fn=gen, cache=c)
    assert len(gen.calls) == 3


def test_errors_and_not_found_are_never_cached(tmp_path):
    from src.backend.gemini_client import GeminiError
    c = Cache(tmp_path)

    def bad(p, system=None):
        raise GeminiError("busy", "busy")
    study.generate_summary(SEL, retrieve_fn=ret, generate_fn=bad, cache=c)
    study.generate_summary(SEL, retrieve_fn=ret, generate_fn=counting("I could not find this in the documents."), cache=c)
    assert list(tmp_path.glob("*.json")) == []
    gen = counting("- ok [S1]")
    study.generate_summary(SEL, retrieve_fn=ret, generate_fn=gen, cache=c)
    assert len(gen.calls) == 1


def test_questions_and_quiz_cache_by_type_and_count(tmp_path):
    c, n = Cache(tmp_path), {"q": 0, "z": 0}
    good_q = [{"question": "Q?", "model_answer": "A"}]
    good_z = [{"question": "Q?", "options": ["a", "b", "c", "d"], "correct_index": 0, "explanation": "e"}]

    def gq(p, system=None, validate=None, **kw):
        n["q"] += 1
        return good_q

    def gz(p, system=None, validate=None, **kw):
        n["z"] += 1
        return [dict(good_z[0])]

    for _ in range(2):
        study.generate_questions(SEL, "short", 3, retrieve_fn=ret, generate_json_fn=gq, cache=c)
        study.generate_quiz(SEL, 3, retrieve_fn=ret, generate_json_fn=gz, cache=c)
    assert n == {"q": 1, "z": 1}
    study.generate_questions(SEL, "long", 3, retrieve_fn=ret, generate_json_fn=gq, cache=c)
    study.generate_questions(SEL, "short", 4, retrieve_fn=ret, generate_json_fn=gq, cache=c)
    study.generate_quiz(SEL, 4, retrieve_fn=ret, generate_json_fn=gz, cache=c)
    study.generate_questions(SEL, "short", 3, retrieve_fn=ret, generate_json_fn=gq, cache=c, refresh=True)
    assert n == {"q": 4, "z": 2}


def test_cache_miss_after_index_rebuild(tmp_path, monkeypatch):
    c, gen = Cache(tmp_path), counting("- x [S1]")
    monkeypatch.setattr(study, "index_fingerprint", lambda: "v1")
    study.generate_summary(SEL, retrieve_fn=ret, generate_fn=gen, cache=c)
    monkeypatch.setattr(study, "index_fingerprint", lambda: "v2")
    study.generate_summary(SEL, retrieve_fn=ret, generate_fn=gen, cache=c)
    assert len(gen.calls) == 2


# ---- rag: repeated question is answered from the cache ----
def test_same_question_answered_from_cache_ignoring_case_and_spacing(tmp_path):
    c, gen = Cache(tmp_path), counting("It computes y [S1].")
    a = rag.answer("What is a perceptron?", retrieve_fn=ret, generate_fn=gen, cache=c)
    b = rag.answer("  what is   a PERCEPTRON? ", retrieve_fn=ret, generate_fn=gen, cache=c)
    assert a == b and len(gen.calls) == 1
    rag.answer("What is a perceptron?", "Regulation", retrieve_fn=ret, generate_fn=gen, cache=c)
    assert len(gen.calls) == 2  # other mode = different question
    assert rag.answer("q", retrieve_fn=ret, generate_fn=gen) is not None  # injected fns and no cache: still works


def test_injected_functions_never_touch_the_shared_cache(tmp_path, monkeypatch):
    mine = Cache(tmp_path)
    monkeypatch.setattr(cachemod, "_default", mine)
    rag.answer("x?", retrieve_fn=ret, generate_fn=counting("ok [S1]"))
    study.generate_summary(SEL, retrieve_fn=ret, generate_fn=counting("- ok [S1]"))
    assert list(tmp_path.glob("*.json")) == []


# ---- quota cooldown ----
def test_quota_cooldown_skips_exhausted_model_without_calling_it(monkeypatch):
    monkeypatch.setattr(config, "GEMINI_FALLBACK_MODEL", "")
    t = [100.0]
    monkeypatch.setattr(gc, "_now", lambda: t[0])
    c = FakeClient([FakeAPIError(429, QUOTA_MSG)])
    try:
        gc.generate("p", client=c, sleep=NOSLEEP)
    except gc.GeminiError as e:
        assert e.kind == "quota"
    assert len(c.calls) == 1
    try:
        gc.generate("p", client=c, sleep=NOSLEEP)  # within cooldown: no new call
    except gc.GeminiError as e:
        assert e.kind == "quota" and "tomorrow" in e.user_message
    assert len(c.calls) == 1
    t[0] += config.QUOTA_COOLDOWN_S + 1  # cooldown over: tries again
    c.script = ["hello"]
    assert gc.generate("p", client=c, sleep=NOSLEEP) == "hello" and len(c.calls) == 2


def test_quota_on_primary_still_uses_fallback_and_remembers_primary(monkeypatch):
    monkeypatch.setattr(config, "GEMINI_MODEL", "m1")
    monkeypatch.setattr(config, "GEMINI_FALLBACK_MODEL", "m2")
    c = FakeClient([FakeAPIError(429, QUOTA_MSG), "from m2", "again m2"])
    assert gc.generate("p", client=c, sleep=NOSLEEP) == "from m2"
    assert gc.generate("p", client=c, sleep=NOSLEEP) == "again m2"
    assert c.calls == ["m1", "m2", "m2"]
