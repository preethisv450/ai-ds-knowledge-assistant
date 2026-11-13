from src.data.clean_text import find_boilerplate, strip_boilerplate

HEADER = "BMS College of Engineering - Academic Regulations"


BODY = ("A student must keep the required attendance in every subject.\n"
        "Condonation may be granted on medical grounds with a certificate.\n"
        "The head of the department decides each case on its merits.")


def pages(n=5, body=BODY):
    return [(i, f"{HEADER}\n{body}\nPage {i} of {n}") for i in range(1, n + 1)]


def test_repeated_header_and_numbered_footer_are_removed():
    cleaned, report = strip_boilerplate(pages())
    assert len(cleaned) == 5
    for _, text in cleaned:
        assert HEADER not in text and "of 5" not in text
        assert "A student must keep the required attendance" in text
    assert any(HEADER.lower() in p for p in report["patterns"])


def test_a_short_document_keeps_its_header():
    """Under three pages there is not enough evidence to call a line a running header.
    A bare page number is always noise, so that still goes."""
    cleaned, report = strip_boilerplate(pages(2))
    assert all(HEADER in t for _, t in cleaned)
    assert all("of 2" not in t for _, t in cleaned)
    assert set(report["patterns"]) == set()


def test_a_heading_in_the_body_survives():
    p = [(i, f"{HEADER}\nATTENDANCE\n{BODY}\nPage {i} of 4") for i in range(1, 5)]
    cleaned, _ = strip_boilerplate(p)
    assert all("ATTENDANCE" in t for _, t in cleaned)
    assert all(HEADER not in t for _, t in cleaned)


def test_a_line_that_appears_once_is_kept():
    p = pages(4)
    p[2] = (3, f"{HEADER}\n{BODY}\nSpecial note only on this page\nPage 3 of 4")
    cleaned, _ = strip_boilerplate(p)
    assert "Special note only on this page" in dict(cleaned)[3]


def test_find_boilerplate_needs_enough_pages():
    assert find_boilerplate(pages(2)) == set()
    assert find_boilerplate(pages(6)) != set()


def test_a_long_line_differing_only_by_a_number_is_not_treated_as_a_footer():
    long_body = "The maximum duration allowed to complete the programme is {n} years in total."
    p = [(i, f"{HEADER}\n{long_body.format(n=i)}\n{BODY}\nPage {i} of 4") for i in range(1, 5)]
    cleaned, _ = strip_boilerplate(p)
    assert all("maximum duration allowed" in t for _, t in cleaned)


def test_pages_that_become_empty_are_dropped():
    p = [(i, HEADER) for i in range(1, 4)]
    cleaned, _ = strip_boilerplate(p)
    assert cleaned == []
