# Data and evaluation runbook (D1–D10)

Every command runs from the repo root with the virtual environment active. The order
matters: each step consumes what the one before it produced.

## D1 — Collect and agree the schema

Put the syllabus PDFs and the regulation document in `data/pdfs/`. Name each syllabus
after its subject code (`AI201_syllabus.pdf`) and keep the word "regulation" in the
regulation file name. The schema is written up in `docs/data_schema.md` — read it with
Preethi and Pragna before any data is typed, because changing it later means redoing
work in all three parts.

## D2 — Syllabus PDFs into structured JSON

```
python scripts/parse_syllabus.py data/pdfs/AI201_syllabus.pdf data/pdfs/DS202_syllabus.pdf
```

Writes a draft to `data/processed/syllabus_draft.json` and prints a `CHECK:` line for
everything it guessed. It is a first pass, not a finished file: read every line, fix the
subject names, add the credits and topics it could not find, then paste the subjects into
`data/processed/curriculum.json`.

## D3 — Regulation PDF into sections

```
python scripts/split_regulations.py data/pdfs/Academic_Regulations.pdf
```

Writes `data/processed/regulations.json` and prints each section with its page range and
the topic it was tagged with. Check the list against the document: if a rule you know is
in there has no section, the heading style was not recognised and that part will need to
be added by hand.

## D4 — Validate before handing over

```
python scripts/validate_data.py
```

Errors must be fixed; warnings are worth reading. Run this before every hand-off to
Preethi or Pragna. It checks subject codes, module ids, duplicate entries, page ranges
that run past the end of a file, modules that overlap, subjects with no document, and a
missing regulation document.

## D5 — First concept nodes and edges

```
python scripts/extract_concepts.py          # needs the index: python scripts/build_index.py
python scripts/check_concepts.py
```

The first command proposes frequent terms per module into
`data/concepts/concepts.candidates.csv`. They are candidates, not concepts: open the file,
delete the noise, fix the names, and save the keepers as `data/concepts/concepts.csv`.
Then write the edges in `data/concepts/relations.csv` and run the check. Use
`concepts.example.csv` and `relations.example.csv` as the model.

## D6 — Documents ready for indexing

```
python scripts/clean_documents.py
```

Running headers, footers and page numbers are stripped automatically during indexing.
This command shows exactly what is being removed from each PDF. If a real heading
appears in that list, tell Pragna before the next rebuild.

## D7 — Per-module metadata

```
python scripts/build_manifest.py            # preview
python scripts/build_manifest.py --write    # save it
```

Finds the module headings in each syllabus PDF and writes the page ranges into
`data/processed/documents.json`. Entries already in the file are kept, so hand
corrections are never overwritten. Re-run `scripts/validate_data.py` afterwards, then ask
Pragna to rebuild the index.

## D8 — The 30-question evaluation set

```
python scripts/make_question_set.py --new   # blank template
python scripts/make_question_set.py         # check a filled-in one
```

Fifteen regulation questions and fifteen syllabus questions, written the way a student
would actually type them. For each one, record the keywords the answer must contain and
the document and page the answer is on. Keep a few questions the documents genuinely
cannot answer, marked `answerable=no`: refusing those correctly is as important as
answering the rest. The check catches a page number past the end of a file, a module id
that does not exist, and an unanswerable question that was given an expected answer.

## D9 — First run, with reasons

```
python scripts/accuracy_report.py --retrieval-only     # free, no Gemini
python scripts/accuracy_report.py --delay=8            # the real run
```

Every answer is graded correct, partial or wrong, each with a reason. Read the reasons
rather than the headline number: `the expected page was not retrieved at all` is a
retrieval problem for Pragna, while `said not found, but the documents do contain the
answer` usually means the similarity threshold is too high. Gemini failures are reported
separately and are not counted as wrong answers. Each run is saved to
`results/accuracy_<timestamp>.csv`.

## D10 — Re-run and compare

```
python scripts/accuracy_report.py --delay=8 --compare=results/accuracy_<first run>.csv
```

Shows what the fixes changed: which questions were fixed, which regressed, and which are
still failing. The exit code is 0 when accuracy is at or above the 80 percent milestone.

Report the number honestly, including the sample size. An accuracy figure means nothing
without saying which documents and how many questions it was measured on.
