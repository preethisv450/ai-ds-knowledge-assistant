# AI & DS Knowledge Assistant

A Streamlit app for exploring AI & Data Science course materials. It combines syllabus and academic-regulation documents with retrieval-augmented generation (RAG) to answer questions with source references, and offers study tools for module summaries, practice questions, and quizzes.

## Features

- **Module Assistant:** Generate module summaries, practice questions, and multiple-choice quizzes from the indexed course materials.
- **Chat:** Ask questions in syllabus or regulation mode and inspect cited source passages. Syllabus answers can be scoped to the selected module.
- **Knowledge Network and Timetable:** App sections are present; their interactive graph and schedule features are not yet implemented.

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

## Run the app

```bash
streamlit run app.py
```

Open the local URL printed by Streamlit in your browser. Use the sidebar to select a year, semester, subject, and module where applicable.

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