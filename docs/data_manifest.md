# How documents are labelled for search

Put every PDF in `data/pdfs/`, then run `python scripts/build_index.py`. The index labels each page as a
**syllabus** document, a **regulation** document or **other**. Syllabus mode only searches syllabus documents
for the subject (and module) chosen in the sidebar. Regulation mode only searches regulation documents.

## Option 1: just name the files (no extra file needed)

- `AI201_syllabus.pdf`, `DS202_notes.pdf`: a subject code (2-4 letters + 3 digits) at the start of the name,
  followed by `_`, `-` or a space. Labelled syllabus for that subject. The code must match the `code` in `curriculum.json`.
- `Academic_Regulations.pdf`, `Exam_Policy.pdf`: the name contains regulation, ordinance, policy, policies, rules, bylaw or statute.
  Labelled regulation.
- Anything else is labelled `other` and is NOT searched.

## Option 2: `data/processed/documents.json` (needed when one PDF covers several subjects or modules)

See `data/processed/documents.example.json`. For each file give `doc_type` (`syllabus`, `regulation` or `other`),
the `subject_code` for syllabus files, and optionally `modules`: the first and last PDF page of each module,
using the module ids from `curriculum.json`. A syllabus document with no `modules` matches every module of its subject.
The manifest wins over the file-name rules.

If the manifest has a mistake, `build_index.py` stops and says exactly what to fix.

Until at least one document is labelled syllabus or regulation, scoping is switched off so the app still works while
the real data is being collected.
