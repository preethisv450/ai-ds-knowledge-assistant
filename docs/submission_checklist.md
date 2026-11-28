# Submission checklist — D20

Covers the report and the data and analysis artifacts. For the demo rehearsal
and the second-device test see `docs/release_checklist.md`.

## A. Clear the TODOs

`docs/report_part2.md` carries ten placeholders. None may survive into the
submitted document.

    Select-String -Path docs/report_part2.md -Pattern "TODO"

| TODO | Comes from | Done |
|---|---|---|
| Run 3 accuracy (38 questions) | `scripts/evaluate.py` output, recorded in `docs/tuning_log.md` | |
| Run 4 accuracy (50 questions) | same, on the final set | |
| Summary rubric scores | `docs/quality_rubric.md`, D17 | |
| Quiz rubric scores | `docs/quality_rubric.md`, D17 | |
| Number of students and feedback summary | `docs/student_feedback.md`, D17 | |
| Reviewer name, role, date and verdict | `docs/graph_validation.md`, D15 | |

If a review did not happen, say so in the report rather than leaving a blank or
inventing a figure. "The faculty review is scheduled for ..." is an acceptable
sentence; a made-up name is not.

## B. Assemble the report

- [ ] Merge `report_part1.md` and `report_part2.md` into one document
- [ ] Delete the reference list at the end of Part 1; keep the one at the end
- [ ] Renumber sections if your template differs from 1 to 8
- [ ] Replace the three Mermaid blocks with rendered images — view the file on
      GitHub and screenshot, or redraw in Word
- [ ] Caption every figure (Figure 1, 2, 3) and refer to each by number in the text
- [ ] Caption every table and refer to each by number in the text
- [ ] Add title page, abstract, table of contents, list of figures
- [ ] Check the citation style matches what your department requires
- [ ] Export to PDF and check nothing reflowed or split badly

## C. Proofread against the data

Every number in the report must match the files. Check each against its source
rather than trusting the draft.

| Claim in the report | Source file | Expected |
|---|---|---|
| Concepts in the graph | `data/processed/centrality.csv` | 151 |
| Relations | `concept_graph.json` | 141 (130 prerequisite, 11 related-to) |
| Subjects and modules | `curriculum.json` | 10 and 30 |
| Communities and modularity | `docs/communities_report.md` | 21 and 0.924 |
| Concepts with betweenness above zero | `docs/centrality_report.md` | 71 |
| Communities at least 60% one subject | `docs/communities_report.md` | 17 of 21 |
| Cross-subject relations | `docs/study_order.md` | 10 |
| Test set size and split | `data/eval/test_questions.csv` | 50: 35 syllabus, 15 regulation |
| Answerable and unanswerable | same | 47 and 3 |
| Regulation sections extracted | `data/processed/regulations.json` | 5 |
| Top concept by degree | `docs/centrality_report.md` | Derivative |
| Top concept by betweenness | `docs/centrality_report.md` | Backpropagation |

Then read for these:

- [ ] No claim that the system was tested on real course documents; the PDFs
      are sample data and section 6.5 says so
- [ ] No claim of accuracy across ten subjects; only two have documents
- [ ] The eight hand-written subjects are described as provisional wherever
      their centrality or communities are discussed
- [ ] One term per concept throughout: "bridge concept" or "betweenness", not
      both for the same thing
- [ ] Every reference [1] to [6] is cited at least once in the text
- [ ] No "we will" or "this project aims to" left in the results or conclusion;
      by submission it is past tense

## D. Verify it reproduces

From a clean clone, with the environment installed, these six commands must run
without error and produce the numbers in section C. Run them in order.

    python scripts/check_concepts.py
    python scripts/build_concept_graph.py
    python scripts/centrality_report.py
    python scripts/communities_report.py
    python scripts/export_graph.py
    python scripts/validate_data.py

- [ ] All six complete
- [ ] The regenerated reports match the figures quoted in the report
- [ ] `pytest` passes

A result an examiner can regenerate is worth more than one they have to take on
trust.

## E. Package contents

- [ ] Report PDF
- [ ] Source code — the repository, or a zip of it with `.venv` and
      `data/vector_store` excluded
- [ ] `docs/user_guide.md`
- [ ] `docs/demo_script.md`
- [ ] Screenshots of each page, if your department requires them
- [ ] The slides
- [ ] Data files: `concepts.csv`, `relations.csv`, `test_questions.csv`,
      `centrality.csv`, `communities.csv`, `graph_export.json`
- [ ] Review records: `graph_validation.md`, `quality_rubric.md`,
      `student_feedback.md`, `usability_findings.md`

## F. Final repository state

- [ ] Every feature branch merged into `main`
- [ ] `git status` clean
- [ ] README accurate
- [ ] Tag the submitted commit

    git checkout main
    git pull origin main
    git tag -a v1.0 -m "Final submission"
    git push origin v1.0
