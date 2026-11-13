"""D15: end-to-end checks of the Module Assistant features for one module.

check_module() takes the three study functions as plain callables, so the logic is tested offline with
fakes (tests/test_e2e.py) and run for real by scripts/e2e_check.py. Each check is PASS, FAIL or SKIP
(SKIP = Gemini itself failed, which says nothing about our code).
"""
import time

from src.backend.evaluation import is_service_error

CACHE_FAST_S = 0.5


class Quota(Exception):
    """The daily Gemini quota is used up: stop the whole run, nothing more can be learned."""


def _row(module, check, status, detail=""):
    return {"module": module, "check": check, "status": status, "detail": detail}


def _service_problem(text):
    return is_service_error(text)


def check_module(sel, doc, pages, summary_fn, questions_fn, quiz_fn, pause=lambda: None, quota_message=None):
    """sel: {subject, subject_code, module, module_id}; doc: expected file name; pages: (first, last).
    summary_fn(sel, refresh) / questions_fn(sel, qtype, n, refresh) / quiz_fn(sel, n, refresh)."""
    mid = sel["module_id"]
    rows = []

    def skip(check, text):
        if quota_message and (text or "").startswith(quota_message):
            raise Quota()
        rows.append(_row(mid, check, "SKIP", "Gemini problem: " + text))

    # --- summary ---
    s = summary_fn(sel, True)
    pause()
    if _service_problem(s["summary"]):
        skip("summary", s["summary"])
    else:
        text = s["summary"]
        rows.append(_row(mid, "summary text", "PASS" if len(text.split()) >= 30 and "[S" not in text else "FAIL",
                         f"{len(text.split())} words" + ("; raw [S#] marker left in text" if "[S" in text else "")))
        rows.append(_row(mid, "summary structure", "PASS" if "key points" in text.lower() else "FAIL",
                         "" if "key points" in text.lower() else "no 'Key points' section"))
        bad = [x for x in s["sources"] if x["document"].lower() != doc.lower() or not pages[0] <= x["page"] <= pages[1]]
        rows.append(_row(mid, "summary scoped to module",
                         "PASS" if s["sources"] and not bad else "FAIL",
                         "no sources" if not s["sources"] else (f"outside the module: {[(x['document'], x['page']) for x in bad]}" if bad else
                                                                  f"{doc} p.{pages[0]}-{pages[1]}")))
        # cache: asking again must be instant and identical
        t = time.time()
        again = summary_fn(sel, False)
        dt = time.time() - t
        rows.append(_row(mid, "summary cached", "PASS" if again == s and dt < CACHE_FAST_S else "FAIL",
                         f"second call {dt:.2f}s" + ("" if again == s else ", result differs")))

    # --- questions (short and long) ---
    for qtype, n in (("short", 3), ("long", 2)):
        q = questions_fn(sel, qtype, n, True)
        pause()
        if not q["questions"] and _service_problem(q["message"]):
            skip(f"{qtype} questions", q["message"])
            continue
        ok = len(q["questions"]) == n and all(i["question"].strip() and i["model_answer"].strip() for i in q["questions"])
        rows.append(_row(mid, f"{qtype} questions", "PASS" if ok else "FAIL",
                         f"{len(q['questions'])} of {n}" + ("" if ok else f" {q['message']}")))

    # --- quiz ---
    z = quiz_fn(sel, 3, True)
    pause()
    if not z["quiz"] and _service_problem(z["message"]):
        skip("quiz", z["message"])
    else:
        items = z["quiz"]
        ok = len(items) == 3 and all(len(i["options"]) == 4 and 0 <= i["correct_index"] <= 3 and i["explanation"] for i in items)
        rows.append(_row(mid, "quiz", "PASS" if ok else "FAIL", f"{len(items)} of 3" + ("" if ok else f" {z['message']}")))
    return rows


def module_targets(curriculum, manifest):
    """Yield (selection, doc, (first, last)) for every module that has a page range in the manifest."""
    for y in curriculum["years"]:
        for sem in y["semesters"]:
            for sub in sem["subjects"]:
                for m in sub["modules"]:
                    for entry in manifest.values():
                        rng = (entry.get("modules") or {}).get(m["id"])
                        if rng and (entry.get("subject_code") or "").upper() == sub["code"].upper():
                            yield ({"year": y["year"], "semester": sem["semester"], "subject": sub["name"],
                                    "subject_code": sub["code"], "module": m["title"], "module_id": m["id"]},
                                   entry["file"], tuple(rng))
