import importlib.util
import json
from pathlib import Path

import pytest

from src.backend import e2e
from src.backend.e2e import Quota, check_module, module_targets
from src.backend.gemini_client import _MESSAGES

SEL = {"subject": "AI", "subject_code": "AI201", "module": "Intro", "module_id": "AI201-M1"}
SUMMARY = {"summary": "## Key points\n" + "word " * 40, "sources": [{"document": "AI.pdf", "page": 1, "snippet": "s"}]}
QS = lambda n: {"questions": [{"question": "q?", "model_answer": "a"}] * n, "message": "", "sources": []}
QUIZ = {"quiz": [{"question": "q", "options": list("abcd"), "correct_index": 1, "explanation": "e"}] * 3, "message": "", "sources": []}


def run(summary=lambda s, r: SUMMARY, questions=lambda s, t, n, r: QS(n), quiz=lambda s, n, r: QUIZ, **kw):
    return check_module(SEL, "AI.pdf", (1, 1), summary, questions, quiz, **kw)


def status(rows):
    return {r["check"]: r["status"] for r in rows}


def test_everything_ok_passes_every_check():
    s = status(run())
    assert set(s.values()) == {"PASS"} and len(s) == 7


def test_summary_from_the_wrong_page_or_file_fails_the_scoping_check():
    bad = dict(SUMMARY, sources=[{"document": "AI.pdf", "page": 2, "snippet": "s"}])
    assert status(run(summary=lambda s, r: bad))["summary scoped to module"] == "FAIL"
    bad = dict(SUMMARY, sources=[{"document": "Other.pdf", "page": 1, "snippet": "s"}])
    assert status(run(summary=lambda s, r: bad))["summary scoped to module"] == "FAIL"
    assert status(run(summary=lambda s, r: dict(SUMMARY, sources=[])))["summary scoped to module"] == "FAIL"


def test_missing_structure_raw_markers_and_short_text_fail():
    assert status(run(summary=lambda s, r: dict(SUMMARY, summary="word " * 40)))["summary structure"] == "FAIL"
    assert status(run(summary=lambda s, r: dict(SUMMARY, summary="Key points " + "w " * 40 + "[S1]")))["summary text"] == "FAIL"


def test_cache_check_fails_when_second_call_differs():
    calls = []

    def summary(s, refresh):
        calls.append(refresh)
        return SUMMARY if refresh else dict(SUMMARY, summary="different Key points " + "w " * 40)
    assert status(run(summary=summary))["summary cached"] == "FAIL" and calls == [True, False]


def test_wrong_counts_fail_and_gemini_errors_are_skipped_not_failed():
    assert status(run(questions=lambda s, t, n, r: QS(n - 1)))["short questions"] == "FAIL"
    busy = {"summary": _MESSAGES["rate_limit"], "sources": []}
    s = status(run(summary=lambda sel, r: busy))
    assert s["summary"] == "SKIP" and "summary cached" not in s
    q = {"questions": [], "message": _MESSAGES["timeout"], "sources": []}
    assert status(run(questions=lambda sel, t, n, r: q))["long questions"] == "SKIP"
    z = {"quiz": [], "message": _MESSAGES["server"], "sources": []}
    assert status(run(quiz=lambda sel, n, r: z))["quiz"] == "SKIP"


def test_quota_stops_the_run():
    quota = _MESSAGES["quota"]
    with pytest.raises(Quota):
        run(summary=lambda s, r: {"summary": quota, "sources": []}, quota_message=quota)


def test_pause_is_called_between_gemini_calls():
    n = []
    run(pause=lambda: n.append(1))
    assert len(n) == 4  # summary, short, long, quiz


# ---- sample data + the whole pipeline with a fake embedder ----
@pytest.fixture
def sample(tmp_path, monkeypatch):
    path = Path(__file__).resolve().parents[1] / "scripts" / "make_sample_data.py"
    spec = importlib.util.spec_from_file_location("make_sample_data", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    monkeypatch.setattr(mod, "PDF_DIR", tmp_path / "pdfs")
    monkeypatch.setattr(mod, "MANIFEST", tmp_path / "processed" / "documents.json")
    monkeypatch.setattr(mod, "QUESTIONS", tmp_path / "eval" / "e2e_questions.csv")
    monkeypatch.setattr(mod, "ROOT", tmp_path)
    mod.build()
    return mod, tmp_path


def test_sample_pdfs_have_one_complete_chunk_per_module_page(sample):
    from src.backend.ingest import chunk_pdf
    mod, root = sample
    for fname, (code, name, modules) in mod.SYLLABI.items():
        chunks = chunk_pdf(root / "pdfs" / fname)
        assert sorted({c["page"] for c in chunks}) == [1, 2, 3]
        for page, (_, _, text) in enumerate(modules, 1):
            joined = " ".join(c["text"] for c in chunks if c["page"] == page)
            tail = " ".join(text.split()[-5:])
            assert tail in " ".join(joined.split()), f"{fname} page {page} lost its last words"


def test_manifest_labels_every_module_and_scoping_keeps_chunks_inside_it(sample):
    import numpy as np
    from src.backend.catalog import load_manifest, make_filter
    from src.backend.vector_store import build_from_pdfs, load_index
    mod, root = sample
    index_dir = root / "index"

    def embed(texts):  # word-overlap-ish fake embedding: hashes words into 64 buckets
        out = np.zeros((len(texts), 64))
        for i, t in enumerate(texts):
            for w in t.lower().split():
                out[i, hash(w) % 64] += 1
        return out
    manifest = load_manifest(mod.MANIFEST)
    build_from_pdfs(root / "pdfs", index_dir, embed, manifest)
    _, chunks = load_index(index_dir)
    curriculum = {"years": [{"year": "Y2", "semesters": [{"semester": "S3", "subjects": [
        {"code": c, "name": c, "modules": [{"id": f"{c}-M{i}", "title": f"T{i}"} for i in (1, 2, 3)]}
        for c in ("AI201", "DS202", "CS999")]}]}]}
    assert {c["doc_type"] for c in chunks} == {"syllabus", "regulation"}
    reg = [c for c in chunks if c["doc_type"] == "regulation"]
    assert reg and all(c["document"] == "Academic_Regulations.pdf" for c in reg)
    ok = make_filter("Syllabus", {"subject_code": "DS202", "module_id": "DS202-M2"})
    chosen = [c for c in chunks if ok(c)]
    assert chosen and {(c["document"], c["page"]) for c in chosen} == {("DS202_syllabus.pdf", 2)}
    targets = list(module_targets(curriculum, manifest))  # CS999 has no document, so it is not a target
    assert {t[0]["module_id"] for t in targets} == {f"{c}-M{i}" for c in ("AI201", "DS202") for i in (1, 2, 3)}
    assert all(t[2] == (int(t[0]["module_id"][-1]),) * 2 for t in targets)


def test_sample_questions_load_and_scoping_question_is_unanswerable(sample):
    from src.backend.evaluation import load_questions
    _, root = sample
    rows = load_questions(root / "eval" / "e2e_questions.csv")
    assert len(rows) == 14 and [r["answerable"] for r in rows].count(False) == 3
    assert rows[-1]["selection"]["module_id"] == "AI201-M1" and "elbow" in rows[-1]["question"].lower()
    assert any(r["mode"] == "Regulation" for r in rows)


def test_manifest_is_not_overwritten_when_different(sample, capsys):
    mod, root = sample
    mod.MANIFEST.write_text("[]")
    mod.build()
    assert mod.MANIFEST.read_text() == "[]" and "left it alone" in capsys.readouterr().out
    mod.clean()
    assert not (root / "pdfs" / "AI201_syllabus.pdf").exists() and not mod.MANIFEST.exists()
