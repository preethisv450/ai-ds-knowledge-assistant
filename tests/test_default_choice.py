"""The app should open on a subject that has documents, not on the first subject in the list."""
from src.ui.sidebar import first_indexed_choice

CUR = {
    "Year 1": {"Sem 1": {"Maths": ["M1"], "C": ["M1"]}},
    "Year 2": {"Sem 3": {"AI": ["M1"], "DB": ["M1"]}, "Sem 4": {"ML": ["M1"]}},
}
CODES = {"Maths": "MA101", "C": "CS101", "AI": "AI201", "DB": "CS201", "ML": "DS202"}


def _code(y, s, n):
    return CODES[n]


def test_picks_first_subject_that_has_documents():
    assert first_indexed_choice(CUR, {"AI201", "DS202"}, _code) == ("Year 2", "Sem 3", "AI")


def test_none_when_nothing_is_indexed():
    assert first_indexed_choice(CUR, set(), _code) is None


def test_first_subject_wins_when_it_is_indexed():
    assert first_indexed_choice(CUR, {"MA101"}, _code) == ("Year 1", "Sem 1", "Maths")


def test_works_with_the_real_curriculum_and_manifest():
    """Regression: the lookup must match data_loader's real structure (a mock-only test missed a bug here)."""
    from src.ui import data_loader
    from src.ui.sidebar import _indexed_subject_codes

    tree, index = data_loader.load_curriculum.__wrapped__()
    codes = _indexed_subject_codes()
    choice = first_indexed_choice(tree, codes, lambda y, s, n: index[(y, s, n)]["code"])
    assert choice is None or index[choice]["code"] in codes
