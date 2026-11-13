"""D1: the agreed data schema, in one place.

Year -> Semester -> Subject -> Module -> Topics. Every other script reads these
constants rather than hard-coding field names, so a schema change happens here once.
"""
import re

SCHEMA_VERSION = 2  # v1 had no credits/topics; v2 adds them, both optional

# --- field names -------------------------------------------------------------
CURRICULUM_FIELDS = {
    "root": ("schema_version", "programme", "years"),
    "year": ("year", "semesters"),
    "semester": ("semester", "subjects"),
    "subject": ("code", "name", "modules"),            # optional: credits, hours, prerequisites
    "module": ("id", "title"),                          # optional: topics, hours
}
SUBJECT_OPTIONAL = ("credits", "hours", "prerequisites", "source_file")
MODULE_OPTIONAL = ("topics", "hours")

# --- value rules -------------------------------------------------------------
SUBJECT_CODE = re.compile(r"^[A-Z]{2,4}\d{3}[A-Z]?$")   # CS101, AI201, DS402A
MODULE_ID = re.compile(r"^([A-Z]{2,4}\d{3}[A-Z]?)-M(\d{1,2})$")  # AI201-M1
MAX_CREDITS = 10
DOC_TYPES = ("syllabus", "regulation", "other")
RELATION_TYPES = ("prerequisite", "related-to")

# --- regulation sections we expect to find -----------------------------------
# Each entry: canonical section key -> words that identify it in a heading.
REGULATION_TOPICS = {
    "attendance": ("attendance", "condonation"),
    "examination": ("examination", "exam", "cie", "see", "semester end"),
    "evaluation": ("evaluation", "assessment", "marks", "internal"),
    "grading": ("grading", "grade", "cgpa", "sgpa"),
    "credits": ("credit", "credits"),
    "reexamination": ("re-examination", "reexamination", "supplementary", "makeup", "repeat"),
    "promotion": ("promotion", "eligibility", "detention"),
    "malpractice": ("malpractice", "misconduct", "unfair means"),
    "award": ("degree", "award", "convocation"),
}


def module_id_for(subject_code, n):
    """The one place module ids are built: AI201 + 1 -> 'AI201-M1'."""
    return f"{subject_code.upper()}-M{int(n)}"


def subject_of_module(module_id):
    """'AI201-M2' -> 'AI201'. None when the id does not follow the convention."""
    m = MODULE_ID.match((module_id or "").upper())
    return m.group(1) if m else None


def iter_subjects(curriculum):
    """Yield (year, semester, subject) for every subject in the tree."""
    for year in curriculum.get("years", []):
        for sem in year.get("semesters", []):
            for subject in sem.get("subjects", []):
                yield year.get("year"), sem.get("semester"), subject


def iter_modules(curriculum):
    """Yield (year, semester, subject, module) for every module in the tree."""
    for y, s, subject in iter_subjects(curriculum):
        for module in subject.get("modules", []):
            yield y, s, subject, module


def find_module(curriculum, module_id):
    """Return (subject, module) for a module id, or (None, None)."""
    for _, _, subject, module in iter_modules(curriculum):
        if (module.get("id") or "").upper() == (module_id or "").upper():
            return subject, module
    return None, None
