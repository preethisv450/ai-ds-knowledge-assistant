from src.backend import rag, study
from src.backend.cache import Cache
from src.backend.evaluation import is_service_error
from src.backend.gemini_client import GeminiError, _MESSAGES

SEL = {"subject": "AI", "subject_code": "AI201", "module": "NN", "module_id": "AI201-M1"}
R = [{"document": "AI.pdf", "page": p, "snippet": f"snippet {p}", "score": 0.5, "chunk_id": str(p), "text": f"text {p}"}
     for p in (4, 6, 9)]
ret = lambda q, k=5, where=None: R


def boom(p, system=None, **kw):
    raise GeminiError("rate_limit", _MESSAGES["rate_limit"])


def boom_json(p, system=None, validate=None, **kw):
    raise GeminiError("rate_limit", _MESSAGES["rate_limit"])


def test_answer_falls_back_to_best_passages_when_gemini_fails():
    r = rag.answer("What is x?", retrieve_fn=ret, generate_fn=boom)
    assert r["answer"].startswith(_MESSAGES["rate_limit"])
    assert "AI.pdf, page 4" in r["answer"] and "snippet 4" in r["answer"] and "page 9" not in r["answer"]
    assert [s["page"] for s in r["sources"]] == [4, 6]
    assert is_service_error(r["answer"])  # the evaluation harness still treats it as a Gemini problem


def test_fallback_can_be_switched_off_for_measuring():
    r = rag.answer("What is x?", retrieve_fn=ret, generate_fn=boom, fallback=False)
    assert r == {"answer": _MESSAGES["rate_limit"], "sources": []}


def test_expired_cached_answer_is_used_when_gemini_fails(tmp_path):
    t = [0.0]
    c = Cache(tmp_path, ttl_s=10, now=lambda: t[0])
    good = rag.answer("What is x?", retrieve_fn=ret, generate_fn=lambda p, system=None: "It is y [S1].", cache=c)
    t[0] = 100.0  # entry expired
    again = rag.answer("What is x?", retrieve_fn=ret, generate_fn=boom, cache=c)
    assert again == good and "busy" not in again["answer"]


def test_summary_shows_passages_or_stale_summary_when_gemini_fails(tmp_path):
    r = study.generate_summary(SEL, retrieve_fn=ret, generate_fn=boom)
    assert r["summary"].startswith(_MESSAGES["rate_limit"]) and "snippet 9" in r["summary"] and len(r["sources"]) == 3

    t = [0.0]
    c = Cache(tmp_path, ttl_s=10, now=lambda: t[0])
    good = study.generate_summary(SEL, retrieve_fn=ret, generate_fn=lambda p, system=None: "- fact [S1]", cache=c)
    t[0] = 100.0
    assert study.generate_summary(SEL, retrieve_fn=ret, generate_fn=boom, cache=c) == good


def test_questions_and_quiz_use_stale_entry_but_do_not_invent_one(tmp_path):
    t = [0.0]
    c = Cache(tmp_path, ttl_s=10, now=lambda: t[0])
    qs = [{"question": "Q?", "model_answer": "A"}]
    zs = [{"question": "Q", "options": list("abcd"), "correct_index": 0, "explanation": "e"}]
    q1 = study.generate_questions(SEL, "short", 1, retrieve_fn=ret, generate_json_fn=lambda p, system=None, validate=None, **k: qs, cache=c)
    z1 = study.generate_quiz(SEL, 1, retrieve_fn=ret, generate_json_fn=lambda p, system=None, validate=None, **k: [dict(zs[0])], cache=c)
    t[0] = 100.0
    assert study.generate_questions(SEL, "short", 1, retrieve_fn=ret, generate_json_fn=boom_json, cache=c) == q1
    assert study.generate_quiz(SEL, 1, retrieve_fn=ret, generate_json_fn=boom_json, cache=c) == z1
    nothing = study.generate_questions(SEL, "long", 1, retrieve_fn=ret, generate_json_fn=boom_json, cache=c)
    assert nothing == {"questions": [], "message": _MESSAGES["rate_limit"], "sources": []}
    assert study.generate_questions(SEL, "short", 1, retrieve_fn=ret, generate_json_fn=boom_json, cache=c, fallback=False, refresh=True)["questions"] == []


def test_stale_entries_are_only_returned_on_request(tmp_path):
    t = [0.0]
    c = Cache(tmp_path, ttl_s=10, now=lambda: t[0])
    c.put("k", "x", 1)
    t[0] = 50.0
    assert c.get("k", "x") is None and c.get("k", "x", allow_stale=True) == 1


def test_warm_up_never_raises_without_an_index(tmp_path, monkeypatch):
    from src.backend import vector_store
    from src.backend.warmup import warm_up
    monkeypatch.setattr(vector_store, "embed_texts", lambda texts, embed_fn=None: None)  # do not load the real model
    r = warm_up(tmp_path)  # no index in this folder
    assert r["ok"] is False and "no index" in r["error"] and set(r) == {"ok", "model_s", "index_s", "error"}


def test_warm_up_loads_model_then_index(tmp_path, monkeypatch):
    from src.backend import retrieval, vector_store
    from src.backend.warmup import warm_up
    seen = []
    monkeypatch.setattr(vector_store, "embed_texts", lambda texts, embed_fn=None: seen.append("model"))
    monkeypatch.setattr(retrieval, "_load", lambda d: seen.append("index"))
    r = warm_up(tmp_path)
    assert r["ok"] is True and seen == ["model", "index"]
