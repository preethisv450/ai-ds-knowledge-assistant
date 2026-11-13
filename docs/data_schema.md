# Data schema (D1)

Everything the assistant answers from lives in four files. This is the agreed shape of
each one. Preethi's UI and Pragna's backend both read these, so a change here has to be
agreed by all three of us before it is made.

## 1. `data/processed/curriculum.json` — the navigation tree

```
Year -> Semester -> Subject -> Module -> Topics
```

```json
{
  "schema_version": 2,
  "programme": "AI & DS",
  "years": [
    { "year": "Year 2",
      "semesters": [
        { "semester": "Semester 3",
          "subjects": [
            { "code": "AI201",
              "name": "Artificial Intelligence",
              "credits": 4,
              "source_file": "AI201_syllabus.pdf",
              "modules": [
                { "id": "AI201-M1",
                  "title": "Introduction to AI",
                  "topics": ["rational agent", "PEAS", "task environments"] }
              ] }
          ] }
      ] }
  ]
}
```

| Field | Required | Rule |
|---|---|---|
| `code` | yes | two to four letters then three digits: `AI201`, `DS402A`. Unique across the file |
| `name` | yes | as printed in the syllabus, no trailing spaces |
| `credits` | no | a number from 1 to 10 |
| `source_file` | no | the PDF this subject came from |
| `id` (module) | yes | `<subject code>-M<n>`, numbered from 1 with no gaps |
| `title` (module) | yes | as printed in the syllabus |
| `topics` (module) | no but wanted | short phrases; these seed the concept list in D5 |

`schema_version` 1 had no `credits` or `topics`. Both are optional, so version 1 files
still load.

## 2. `data/processed/documents.json` — what each PDF is

```json
[
  { "file": "AI201_syllabus.pdf", "doc_type": "syllabus", "subject_code": "AI201",
    "modules": { "AI201-M1": [1, 4], "AI201-M2": [5, 8] } },
  { "file": "Academic_Regulations.pdf", "doc_type": "regulation" }
]
```

`doc_type` is `syllabus`, `regulation` or `other`. Documents marked `other` are never
searched. `modules` maps a module id to `[first_page, last_page]`, and the ranges must
not overlap. This file is what makes module-scoped search work: without it, a question
asked under one module can be answered from another subject's pages.

## 3. `data/processed/regulations.json` — the regulation document, split up

Written by `scripts/split_regulations.py`. One entry per section with its title, the
topic it covers, its page range and its text. The page numbers here are what the
evaluation set cites as `expected_page` for regulation questions.

## 4. `data/concepts/concepts.csv` and `relations.csv` — the network inputs

`concepts.csv`: `concept_id, name, subject_code, module_id, aliases` (aliases separated
by `|`). `relations.csv`: `source, target, relation, weight, note`, where `relation` is
`prerequisite` (directed: source must be understood first) or `related-to` (undirected).

See `data/concepts/concepts.example.csv` and `relations.example.csv` for a filled-in set.

## What has to be collected (D1 checklist)

- [ ] Syllabus PDF for every subject in the programme, with selectable text (not a scan)
- [ ] The current academic regulations document
- [ ] Confirmation of which regulation version applies to this batch
- [ ] File names that start with the subject code: `AI201_syllabus.pdf`
- [ ] A regulation file name containing the word "regulation"

A scanned PDF has no text layer and cannot be indexed. `python scripts/validate_data.py`
reports those, and they have to be OCRed or replaced before anything else works.
