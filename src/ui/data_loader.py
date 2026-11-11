"""Curriculum loading.

Day 4: reads data/processed/curriculum.json and reshapes it for the UI.
When Nishant's real file arrives it drops into the same path in the same
schema, and nothing here changes.
"""

import json
from pathlib import Path

import streamlit as st

CURRICULUM_PATH = Path("data/processed/curriculum.json")


@st.cache_data
def load_curriculum(path: str = str(CURRICULUM_PATH)):
    """Read the curriculum JSON once and reshape it.

    Returns (tree, index):
      tree  -> {year: {semester: {subject_name: [module_title, ...]}}}
      index -> {(year, semester, subject_name): {"code": str,
                                                 "modules": {title: id}}}
    """
    file = Path(path)
    if not file.exists():
        raise FileNotFoundError(
            f"Curriculum file not found at {file}. "
            "Run the app from the repo root (where app.py lives)."
        )

    raw = json.loads(file.read_text())

    tree = {}
    index = {}

    for year in raw["years"]:
        y = year["year"]
        tree[y] = {}
        for sem in year["semesters"]:
            s = sem["semester"]
            tree[y][s] = {}
            for subject in sem["subjects"]:
                name = subject["name"]
                modules = subject["modules"]
                tree[y][s][name] = [m["title"] for m in modules]
                index[(y, s, name)] = {
                    "code": subject["code"],
                    "modules": {m["title"]: m["id"] for m in modules},
                }

    return tree, index


def get_curriculum():
    """Year -> semester -> subject -> [module titles], for the dropdowns."""
    tree, _ = load_curriculum()
    return tree


def get_module_meta(year, semester, subject, module_title):
    """Return (subject_code, module_id) for a selection, or (None, None)."""
    _, index = load_curriculum()
    entry = index.get((year, semester, subject))
    if not entry:
        return None, None
    return entry["code"], entry["modules"].get(module_title)
