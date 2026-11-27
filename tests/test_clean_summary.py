from src.backend.study import clean_summary


def test_placeholder_formulas_section_is_removed():
    text = "## Key points\n- a\n\n## Formulas\n\n(Omit if none)\n\n## Things to remember\n- b"
    out = clean_summary(text)
    assert "Formulas" not in out and "Omit" not in out
    assert "Key points" in out and "Things to remember" in out and "- b" in out


def test_placeholder_variants_are_removed():
    for ph in ("None", "N/A", "(none)", "*Omit if none*", "-"):
        assert "Formulas" not in clean_summary(f"## Definitions\n- x\n**Formulas**\n{ph}\n**Things to remember**\n- y")


def test_real_formulas_are_kept():
    text = "## Formulas\nPrecision = TP / (TP + FP)\n\n## Things to remember\n- y"
    assert clean_summary(text) == text


def test_formulas_as_last_section_with_placeholder():
    assert clean_summary("## Key points\n- a\n## Formulas\n(Omit if none)") == "## Key points\n- a"


def test_text_without_formulas_is_unchanged():
    assert clean_summary("## Key points\n- a") == "## Key points\n- a"
