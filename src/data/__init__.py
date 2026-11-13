"""Nishant's data layer: collecting, structuring and validating the documents the
assistant answers from, plus the concept graph inputs and the evaluation workflow.

Nothing here calls Gemini or touches the vector index. These modules produce and check
the files that the backend consumes:
    data/processed/curriculum.json     the Year -> Semester -> Subject -> Module tree
    data/processed/documents.json      which PDF is what, and which pages hold which module
    data/processed/regulations.json    the regulation document split into sections
    data/concepts/concepts.csv         concept nodes
    data/concepts/relations.csv        concept edges
    data/eval/test_questions.csv       the evaluation set
"""
