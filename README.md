# AI & DS Knowledge Assistant

A Streamlit app for exploring AI & Data Science course materials. It combines syllabus and academic-regulation documents with retrieval-augmented generation (RAG) to answer questions with source references, and offers study tools for module summaries, practice questions, and quizzes.

## Features

- **Module Assistant:** Generate module summaries, practice questions, and multiple-choice quizzes from the indexed course materials.
- **Chat:** Ask questions in syllabus or regulation mode and inspect cited source passages. Syllabus answers can be scoped to the selected module.
- **Knowledge Network:** An interactive prerequisite map of every module. Concepts are laid out top to bottom so the learning order is visible, coloured by module, with a centrality table and the bridge concepts that the most other topics depend on.
- **Timetable:** The app section is present; the schedule is not yet connected to real data.

## Requirements

- Python 3.10 or newer
- A Gemini API key for generated answers and study materials

## Setup

From the repository root, create and activate a virtual environment, then install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

On Windows PowerShell, activate the environment with:

```powershell
.venv\Scripts\Activate.ps1
```

Create a local environment file from the example:

```bash
cp .env.example .env
```

Edit `.env` and set `GEMINI_API_KEY` to a valid key. Keep the key private: `.env` is ignored by Git. Never paste a real key into source files, documentation, or commits. If a key has been exposed, revoke it with Google Cloud and create a replacement.

Optional model settings are also listed in `.env.example`:

- `GEMINI_MODEL` selects the primary Gemini model.
- `GEMINI_FALLBACK_MODEL` selects the fallback model.

## Build the document index

Place syllabus and regulation PDFs in `data/pdfs/`. The repository includes sample documents. Build the local FAISS index before starting the app:

```bash
python scripts/build_index.py
```

The index is generated under `data/vector_store/` and is intentionally ignored by Git. Re-run the command when source PDFs change.

## Build the concept graph

The Knowledge Network reads `data/concepts/concepts.csv` and `data/concepts/relations.csv`, which are committed. To propose new candidate concepts from the indexed syllabus and check any edits:

```bash
python scripts/extract_concepts.py     # writes data/concepts/concepts.candidates.csv
python scripts/check_concepts.py       # validates concepts.csv and relations.csv
```

## Run the app

```bash
streamlit run app.py
```

Open the local URL printed by Streamlit in your browser. Navigate with the five-item bar fixed at the bottom of the window. Select a year, semester, subject, and module in the **Select Curriculum** panel on the Module Assistant page; the chatbot and the Knowledge Network follow that choice.

## Validate data and run tests

Validate the structured course data:

```bash
python scripts/validate_data.py
```

Run the test suite:

```bash
pytest
```

For evaluation workflows, question-set guidance, and the data preparation sequence, see [`docs/nishant_runbook.md`](docs/nishant_runbook.md). The expected structure of curriculum, document, regulation, and concept data is described in [`docs/data_schema.md`](docs/data_schema.md).

## Documentation

- [`docs/user_guide.md`](docs/user_guide.md) — how to use the app, one page.
- [`docs/demo_script.md`](docs/demo_script.md) — the five-minute demonstration.
- [`docs/ui_test_checklist.md`](docs/ui_test_checklist.md) — manual test pass before a release.
- [`docs/usability_test_script.md`](docs/usability_test_script.md) — the usability session protocol.

## Project layout

```text
app.py                  Streamlit application entry point
src/backend/            Retrieval, indexing, Gemini, and study-generation logic
src/data/               Data parsing, validation, and reporting utilities
src/ui/                 Streamlit components and pages
data/pdfs/              Source syllabus and regulation PDFs
data/processed/         Structured curriculum and document metadata
scripts/                Indexing, validation, and evaluation commands
tests/                  Automated tests
docs/                   API, data-schema, and workflow documentation
```