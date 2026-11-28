# Graph validation — D15

A faculty member or senior reviews whether the concept graph matches how the
subjects are actually taught. Take `docs/study_order.md`,
`docs/centrality_report.md` and `docs/communities_report.md` to the meeting, or
show the Knowledge Network page itself.

Reviewer: ________________  Role: ________________  Date: ____________

## 1. Are the concepts right?

Pick two subjects the reviewer teaches. For each, show the concept list from
`data/concepts/concepts.csv` and ask:

| Question | Subject 1: ______ | Subject 2: ______ |
|---|---|---|
| Are these the concepts you would list for these modules? | | |
| Anything important missing? | | |
| Anything here that does not belong, or is too fine-grained? | | |
| Are the names the ones students would recognise? | | |

## 2. Are the prerequisites right?

Show the per-subject order in `docs/study_order.md`.

| Question | Answer |
|---|---|
| Does the teaching order match how you teach it? | |
| Any arrow pointing the wrong way? | |
| Any prerequisite that is really just "related", or the reverse? | |
| Any missing dependency a student would trip over? | |

## 3. Do the cross-subject links hold?

These ten claims are the ones most worth checking, because they cross a
timetable boundary and nobody owns them.

| Claim | Agree? | Comment |
|---|---|---|
| Supervised Learning before Perceptron | | |
| Overfitting alongside Training Data Bias | | |
| Train Test Split alongside Fairness Metric | | |
| Derivative before Backpropagation | | |
| Eigenvalue before Principal Component Analysis | | |
| Array before Static Array | | |
| Pointer before Singly Linked List | | |
| Graph Traversal before State Space Search | | |
| Relational Model alongside Partitioning | | |
| Transformer before Pretrained Language Model | | |

## 4. Do the communities make sense?

Show the labelled groups in `docs/communities_report.md` (21 communities,
modularity 0.924).

| Question | Answer |
|---|---|
| Do the groupings look like real topic areas? | |
| Any group that should be split, or two that should be merged? | |
| Are the labels the names you would use? | |

## 5. Are the recommendations sound?

Show the "Start with these" and "Do not skip these" lists in
`docs/study_order.md`.

| Question | Answer |
|---|---|
| Would you tell a student to start with these? | |
| Is Backpropagation a fair top bridge concept, or an artefact? | |
| Anything you would add to "do not skip"? | |

## Verdict

- [ ] Accepted as is
- [ ] Accepted with the changes listed below
- [ ] Needs rework before it can be used

Changes required:

| # | What to change | Where | Done |
|---|---|---|---|
| 1 | | | |
| 2 | | | |
| 3 | | | |

Reviewer signature: ________________

## After the review

Apply the agreed changes to `data/concepts/concepts.csv` and `relations.csv`,
then regenerate everything downstream so the reports match the data:

    python scripts/check_concepts.py
    python scripts/build_concept_graph.py
    python scripts/centrality_report.py
    python scripts/communities_report.py
    python scripts/export_graph.py
