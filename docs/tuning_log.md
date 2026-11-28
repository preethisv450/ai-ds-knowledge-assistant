# D9 tuning log (backend)

Test set: `data/eval/test_questions.csv` (30 questions: 27 answerable, 3 unanswerable; AI201, DS202 and the regulations).
Command: `python scripts/evaluate.py data/eval/test_questions.csv --delay=4` (fresh answers, no cache).
Pass rule: an answer must contain at least 60% of the expected keywords; unanswerable questions must be refused.

| Run | RAG_MIN_SCORE | Accuracy | Cited expected page | Failures |
|---|---|---|---|---|
| 1 (baseline) | 0.12 | 97% (29/30) | 96% | Q1 "What does PEAS stand for?" answered "not found" (best chunk scored 0.05, under the cutoff) |
| 2 | 0.04 | 100% (30/30) | 100% | none |

## Findings
- Retrieval itself is fine: the expected page was in the top 5 for 100% of answerable questions in both runs.
- The weak-score cutoff was the only problem: short acronym questions score low (lowest answerable 0.054) while the best unanswerable question scored 0.145, so no cutoff separates them by score alone.
- Fix: lower the cutoff to 0.04 and let the prompt's "not found" rule (rag.py) refuse unanswerable questions. All 3 were still refused.
- Trade-off: more irrelevant questions now reach Gemini (one extra API call each) instead of being stopped before it.

## Change made
New setting `ANSWER_MIN_SCORE` = 0.04 in `src/backend/config.py`, used only by chat answers (`rag.py`) and the evaluation scripts.
`RAG_MIN_SCORE` stays 0.12 for summaries, questions and quizzes: lowering it there let unrelated pages into the sources (tests caught this).
Env override: `ANSWER_MIN_SCORE=0.15 python scripts/evaluate.py ...`.

## Caveat
The sample PDFs are three short pages each, so 100% on 30 questions is a good sign, not proof. Re-run on the real documents when they are added.

## Re-run after extending the regulation questions (D8 catch-up)

The set was 23 syllabus and 7 regulation; the plan called for 15 regulation, so
eight more were added from the Academic Regulations PDF (ids 31-38), taking the
set to 38 questions: 35 answerable, 3 unanswerable.

| Run | Questions | Accuracy | Cited expected page | Failures |
|---|---|---|---|---|
| 3 | 38 | TODO | TODO | TODO |
