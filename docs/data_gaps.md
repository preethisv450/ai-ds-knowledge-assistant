# Data gaps — D16

What the evaluation and the D15 review exposed, what was fixed, and what is
still open. Written so the report states the limits rather than hiding them.

## Fixed in D16

| Gap | Was | Now |
|---|---|---|
| Test set too small | 38 questions | 50 questions: 35 syllabus, 15 regulation, 47 answerable and 3 deliberately unanswerable |
| Regulation questions under-represented | 7 of 38 | 15 of 50, covering attendance, condonation, assessment split, pass marks, grading bands, CGPA, re-evaluation and backlogs |
| Syllabus topics never tested | 23 questions clustered on a few topics | every module has at least 5 questions; added uniform-cost search, iterative deepening, first-order logic, resolution, logistic regression, decision trees, hierarchical clustering, PCA, recall and the ROC curve |
| Regulation sections not extracted | `split_regulations.py` had never been run | `data/processed/regulations.json` generated, 5 sections with page numbers |

## Still open

**Only two subjects have source documents.** `data/pdfs/` holds syllabi for
AI201 and DS202 only. The other eight subjects in `curriculum.json` — MA101,
CS101, CS102, CS201, DS301, DS302, DS401, DS402 — have no PDF, so nothing can
be indexed for them, no syllabus question can be asked about them, and their
concepts in `concepts.csv` were written from standard course content rather
than extracted from a document. Every accuracy figure in this project is
therefore measured on two subjects, not ten. Fixing this means obtaining the
remaining syllabi; no amount of code substitutes for it.

**The regulation document is partial.** `split_regulations.py` finds
attendance, assessment, grading, re-evaluation and backlogs. It reports no
section for award of degree, credits, malpractice, promotion or
re-examination, so questions on those cannot be answered and are not in the
test set.

**The PDFs are sample data.** Each is three pages and carries the line "SAMPLE
DATA for testing - not real course material". The 100% accuracy recorded in
`docs/tuning_log.md` is a signal that the pipeline works, not evidence of how
it performs on a real multi-hundred-page syllabus. Re-run the evaluation when
the real documents arrive, and expect the figure to drop.

**Concept relations for eight subjects are unverified.** They follow standard
teaching order rather than this college's syllabus. The D15 faculty review is
what turns them from plausible into checked; until that is signed off, the
centrality and community findings for those subjects should be reported as
provisional.

## How to re-check after filling a gap

    python scripts/build_index.py
    python scripts/evaluate.py data/eval/test_questions.csv --delay=4
    python scripts/check_concepts.py
    python scripts/build_concept_graph.py
    python scripts/centrality_report.py
    python scripts/communities_report.py
    python scripts/export_graph.py
