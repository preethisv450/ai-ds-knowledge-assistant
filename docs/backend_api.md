# Backend API notes (frozen at D10)

The UI talks to the backend through one function. Its signature and return shape do not change.

```python
from src.ui.answer_service import get_answer
get_answer(question: str, mode: str, selection: dict | None) -> {"answer": str, "sources": [{"document": str, "page": int, "snippet": str}]}
```

- `mode` is `"Syllabus"` or `"Regulation"`.
- `selection` is the sidebar dict (keys used: `subject`, `module`, `subject_code`, `module_id`). `None` is fine.
- `answer` is markdown. `sources` can be empty and lists only pages the answer cites (one entry per page, best first).
- It never raises for expected problems. It returns a friendly sentence in `answer` and `sources == []` when: the question is empty,
  the index has not been built, nothing relevant was found ("I could not find this in the documents..."), the chosen subject/module
  has no documents yet, or Gemini failed (rate limit, timeout, outage).

## Other backend functions (same package, `src/backend/`)

| Function | Module | Returns |
|---|---|---|
| `retrieve(query, k, where=None)` | `retrieval` | top-k chunks: document, page, snippet, score, chunk_id, text |
| `generate(prompt, system=None, json_mode=False)` | `gemini_client` | text, or raises `GeminiError` (`.user_message` is safe to show) |
| `generate_json(prompt, system, validate)` | `gemini_client` | parsed JSON, re-asked if invalid |
| `answer_prompt / summary_prompt / questions_prompt / quiz_prompt` | `prompts` | `(system, prompt)` |

## Settings (`src/backend/config.py`, overridable in `.env`)

`GEMINI_MODEL`, `GEMINI_FALLBACK_MODEL` (optional backup), `RAG_MIN_SCORE` (below this similarity a chunk is ignored; default 0.12),
`TOP_K` (5), `CHUNK_WORDS` (180) / `CHUNK_OVERLAP` (30). Changing chunk settings or the embedding model needs `python scripts/build_index.py`.

## Commands

- `python scripts/build_index.py`: build/rebuild the index from `data/pdfs/` (see `docs/data_manifest.md` for labelling documents)
- `python scripts/ask.py "question"`: ask from the terminal and see retrieval scores
- `python scripts/evaluate.py data/eval/test_questions.csv [--retrieval-only]`: accuracy report and threshold advice
- `python scripts/try_gemini.py`: one live call per prompt template
- `pytest`: all tests (no network, no API key needed)

## Gemini free-tier quotas (important)

Free-tier daily limits are per model and per project (extra API keys in one project do not help) and reset at midnight Pacific time.
`gemini-3.6-flash` and `gemini-3.8-flash` allow only about 20 requests per day; the flash-lite models allow about 500 per day
(figures from a third-party summary and matched by the 429 error we saw; Google shows the real numbers in the AI Studio rate-limit page).
So the default model is `gemini-3.5-flash-lite`, with `gemini-3.6-flash` as the automatic fallback. When a model's daily quota is
used up, `generate()` does not retry it; it moves to the fallback model straight away, and if every model is used up the user sees
"Today's free AI usage limit has been reached. Please try again tomorrow."

Save requests: `scripts/evaluate.py --retrieval-only` costs nothing, tests never call Gemini, and D14 adds a cache so repeated
questions and summaries do not use a request.


## Summary (D11)

`src.backend.study.generate_summary(selection)` returns `{"summary": str (markdown), "sources": [{document, page, snippet}]}`. `selection` is the sidebar dict (needs `module`; `subject`, `subject_code`, `module_id` scope the search). Never raises for expected problems: a friendly message goes in `summary` and `sources` is `[]`. Wired into the Summary tab of `src/ui/pages/module_assistant.py`; the result is kept in `st.session_state` per module so rerenders do not call Gemini again.

## Practice questions (D12)

`src.backend.study.generate_questions(selection, qtype="short", n=5, difficulty="medium")` returns `{"questions": [{"question", "model_answer"}], "message": str, "sources": [{document, page, snippet}]}`. `qtype` accepts "short"/"long" or the UI labels "Short answer"/"Long answer"; `n` is clamped to 1-20. Gemini is called in JSON mode and the reply is validated (re-asked up to 3 times). On any expected problem (no module chosen, no index, no documents, nothing relevant, Gemini error) `questions` is `[]` and `message` holds a friendly sentence for `st.warning`. `sources` are the pages the questions were written from (questions are not cited one by one).

## Quiz (D13)

`src.backend.study.generate_quiz(selection, n=5)` returns `{"quiz": [{"question", "options": [4 strings], "correct_index": 0-3, "explanation"}], "message": str, "sources": [{document, page, snippet}]}`. `n` is clamped to 1-15. Gemini replies in JSON mode and is validated (4 distinct options, correct_index 0-3, explanation present; re-asked up to 3 times). The options are shuffled in code so the right answer is not always in the same slot, and `correct_index` is remapped. On any expected problem `quiz` is `[]` and `message` is a friendly sentence. The Quiz tab keeps the quiz and the student's answers in `st.session_state`, so scoring does not call Gemini again.

## Caching and rate limits (D14)

`src/backend/cache.py` keeps successful results on disk in `.cache/generated/` (gitignored): chat answers (same question, mode, subject and module, ignoring case and spacing), summaries, questions (per type, count and difficulty) and quizzes (per count). Entries expire after 7 days (`CACHE_TTL_S`) and are tied to a fingerprint of the index, so rebuilding the index makes old entries unreachable. Errors and "not found" messages are never saved. A corrupt or unwritable cache is treated as a miss, never as an error.

`generate_summary`, `generate_questions` and `generate_quiz` take `refresh=True` to skip the saved result and replace it (the UI "make a new set" checkbox). `answer` and the study functions accept `cache=None` to switch caching off; `scripts/evaluate.py` does this so accuracy is always measured on fresh answers. When functions are injected (tests) no cache is used unless one is passed. `python scripts/clear_cache.py` removes everything.

Rate limits: transient errors are retried with backoff and then the fallback model is tried (D5). New in D14: when a model reports its daily quota is used up, it is skipped for `QUOTA_COOLDOWN_S` (15 minutes), so later requests fail fast with the "daily limit reached" message instead of waiting on a call that cannot succeed. Cached results keep working while the quota is exhausted.
