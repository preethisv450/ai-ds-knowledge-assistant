# D15 end-to-end report (backend)

Command: `python scripts/e2e_check.py --delay=3` (real Gemini, documents in `data/pdfs`, 2026-11-28).

Result: **63 passed, 0 failed, 0 skipped.**

| Check | Result |
|---|---|
| Retrieval stays inside each module's pages (6 modules) | PASS |
| Summary: text, structure, scoped to the module's pages (6 modules) | PASS |
| Summary cached: second call 0.00s (6 modules) | PASS |
| Short questions: 3 of 3 per module | PASS |
| Long questions: 2 of 2 per module | PASS |
| Quiz: 3 of 3 MCQs per module | PASS |
| Chat: 14 questions with page references | PASS |
| Chat accuracy at least 80% (plan target) | PASS (100%) |

Modules covered: AI201-M1, M2, M3 and DS202-M1, M2, M3.

Not covered: a real Gemini rate limit was not triggered (quota-cooldown handling is covered by a unit test only).
Caveat: the sample PDFs are one page per module, so re-run the check once the real documents are added.
