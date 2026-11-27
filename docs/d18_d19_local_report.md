# D18 and D19 report (backend): localhost only

Decision: the project is **not deployed**. It runs on the local machine only
(`streamlit run app.py`, http://localhost:8501). D18 "deploy" is replaced by a local run check.

## D18: local run check (2026-11-28)
- Python 3.10.22 venv, `pip install -r requirements.txt` clean, `python scripts/build_index.py` OK (20 chunks, 5/5 self-retrieval).
- `streamlit run app.py` serves http://localhost:8501 (HTTP 200); Gemini key read from `.env`.
- Live UI check in the browser: Regulation Chatbot asked "minimum attendance to appear in the end-semester exam" ->
  "at least 75 percent ... (Academic_Regulations.pdf, p.1)" with a source panel.
- Note: Syllabus mode starts on the first curriculum subject (MA101), which has no PDF in the sample data, so it answers
  "No documents have been added yet". Pick AI201 or DS202 (the indexed subjects) or add the real syllabi.

## D19: final regression (2026-11-28)
| Check | Result |
|---|---|
| `python -m pytest -q` | 240 passed |
| `python scripts/e2e_check.py` (summaries, questions, quizzes for 6 modules + chat) | 63 passed, 0 failed, 0 skipped |
| `scripts/evaluate.py data/eval/test_questions.csv` (30 questions) | 100%, 100% cite the expected page |
| `scripts/evaluate.py data/eval/unseen_questions.csv` (10 unseen questions, from `feature/d16-d17-backend`) | 100%, 100% cite the expected page |

## Freeze and tag
After every branch is merged into `main` and `git status` is clean, tag the release:
`git tag -a v1.0 -m "AI & DS Knowledge Assistant v1.0 (local)"` then `git push origin v1.0`.

## Caveat
The PDFs are sample documents (one page per module), so these numbers are easier than real course material would be.
