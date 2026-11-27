# D16 and D17 report (backend)

## D16: latency and graceful fallback
Measured with `python scripts/latency.py --gemini` (2026-11-28, CPU, sample PDFs):

| Step | Time |
|---|---|
| Embedding model load (once, in a background thread at startup, `warmup.py`) | 6.5 s |
| Index load (once, then cached in memory) | 0.0 s |
| Retrieval after warm-up | median 8 ms, slowest 15 ms (10 questions) |
| First answer (retrieve + Gemini call) | 1.41 s |
| Same question again (answer cache) | 0.00 s |

Already in place: index and model loaded once (`warmup.py`, `retrieval._load`), embeddings batched (`batch_size=32` in `vector_store.py`), answers/summaries/questions/quizzes cached (`cache.py`).

Fallback when Gemini fails: simulated a rate-limit error; the app returned the friendly message plus the best matching passage with file and page, instead of an error (`rag.fallback_text`; tests in `tests/test_fallback.py`). An expired cached answer is used first if one exists.

## D17: quality on 10 unseen questions
`data/eval/unseen_questions.csv`: 10 questions not in the 30-question tuning set (9 answerable, 1 unanswerable), written after the threshold was tuned so they were not used to tune it.

Result (`python scripts/evaluate.py data/eval/unseen_questions.csv`): **accuracy 100% (10/10)**, expected page in top 5 for 100%, answers cite the expected page for 100%, the unanswerable question was refused.

## Backend bugs from the student usability test
None to fix: `docs/usability_findings.md` is still the empty template (no sessions recorded yet), so there are no reported bugs. Fill it in after the 3 to 5 student sessions; backend issues found there get fixed under D17.

## Caveat
The sample PDFs are three short pages each. Re-run `latency.py` and the evaluation once real documents are indexed.
