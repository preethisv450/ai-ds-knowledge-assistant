import pytest

from src.backend import prompts as p

CHUNKS = [
    {"document": "AI.pdf", "page": 4, "text": "A perceptron computes y = f(w.x + b) where {w} are weights."},
    {"document": "AI.pdf", "page": 5, "text": "Backpropagation uses the chain rule."},
]


def test_answer_prompt_has_question_context_citations_and_fallback():
    system, prompt = p.answer_prompt("What is a perceptron?", CHUNKS)
    assert "What is a perceptron?" in prompt
    assert "AI.pdf, page 4" in prompt and "AI.pdf, page 5" in prompt
    assert "ONLY from" in system and p.NOT_FOUND in system and "cite" in system


def test_answer_prompt_mode_changes_scope():
    assert "regulations" in p.answer_prompt("q", CHUNKS, "Regulation")[0]
    assert "syllabus" in p.answer_prompt("q", CHUNKS, "Syllabus")[0]


def test_braces_in_pdf_text_do_not_break_templates():
    for system, prompt in (p.answer_prompt("q", CHUNKS), p.summary_prompt("S", "M", CHUNKS),
                           p.questions_prompt("S", "M", CHUNKS), p.quiz_prompt("S", "M", CHUNKS)):
        assert "{w}" in prompt


def test_summary_prompt_asks_for_structure():
    system, prompt = p.summary_prompt("AI", "Neural Nets", CHUNKS)
    assert "Key points" in system and "Definitions" in system and "Formulas" in system
    assert "Neural Nets" in prompt


@pytest.mark.parametrize("qtype,marks", [("short", "2 to 3"), ("long", "8 to 10")])
def test_questions_prompt_short_vs_long(qtype, marks):
    system, prompt = p.questions_prompt("AI", "NN", CHUNKS, qtype=qtype, n=4, difficulty="hard")
    assert marks in prompt and "4" in prompt and "hard" in prompt and "JSON" in system


def test_quiz_prompt_demands_four_options_and_json():
    system, prompt = p.quiz_prompt("AI", "NN", CHUNKS, n=3)
    assert "4 strings" in system and "correct_index" in system and "3 multiple-choice" in prompt


def test_validators():
    good = [{"question": "Q", "options": list("abcd"), "correct_index": 0, "explanation": "e"}]
    p.validate_quiz(good)
    for bad in ([], "x", [{**good[0], "options": ["a"]}], [{**good[0], "correct_index": 4}],
                [{**good[0], "correct_index": True}], [{**good[0], "explanation": ""}]):
        with pytest.raises(ValueError):
            p.validate_quiz(bad)
    p.validate_questions([{"question": "Q", "model_answer": "A"}])
    with pytest.raises(ValueError):
        p.validate_questions([{"question": "Q"}])
