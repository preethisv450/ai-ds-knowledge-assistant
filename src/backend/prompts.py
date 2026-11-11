"""D5: the four prompt templates (answer, summary, questions, quiz).

Built with string concatenation, not str.format, so braces in PDF text (formulas, code)
can never break a template. Each builder returns (system_instruction, prompt).
"""

NOT_FOUND = "I could not find this in the documents."


def format_context(chunks):
    """Number the chunks and label each with its file and page so the model can cite them."""
    parts = []
    for i, c in enumerate(chunks, 1):
        parts.append(f"[S{i}] (Source: {c['document']}, page {c['page']})\n{c['text']}")
    return "\n\n".join(parts)


def answer_prompt(question, chunks, mode="Syllabus", scope=None):
    what = "the academic regulations" if mode == "Regulation" else "the syllabus"
    system = (
        f"You are a study assistant answering questions about {what} for university students. "
        "Answer ONLY from the numbered context. Do not use outside knowledge and do not guess. "
        "After each fact, cite the context passage it came from by its marker, like [S2] "
        "(or [S1][S3] when several passages support it). Use only markers that appear in the context. "
        "Never write file names or page numbers yourself: the system adds them from the markers. "
        "If the context answers only part of the question, answer that part and say what is missing. "
        f"If the context does not contain the answer at all, reply with exactly: {NOT_FOUND} "
        "Be concise and clear."
    )
    if scope and mode != "Regulation":
        system += f" The student is currently studying: {scope}."
    prompt = f"Context:\n{format_context(chunks)}\n\nQuestion: {question}\n\nAnswer:"
    return system, prompt


def summary_prompt(subject, module, chunks):
    system = (
        "You are a study assistant. Write a structured revision summary using ONLY the context. "
        "Use these markdown sections: Key points, Definitions, Formulas (omit if none), "
        "Things to remember. Be accurate and brief. Do not invent content. "
        "End each bullet with the marker of the context passage it came from, like [S2]. "
        "Use only markers that appear in the context; never write file names or page numbers yourself. "
        "If the context has nothing useful about the module, reply with exactly: " + NOT_FOUND
    )
    prompt = f"Subject: {subject}\nModule: {module}\n\nContext:\n{format_context(chunks)}\n\nSummary:"
    return system, prompt


def questions_prompt(subject, module, chunks, qtype="short", n=5, difficulty="medium"):
    marks = "2 to 3 marks (a few sentences)" if qtype == "short" else "8 to 10 marks (a detailed paragraph answer)"
    system = (
        "You are an exam-question writer for university courses. Use ONLY the context. "
        "Return ONLY a JSON array, no other text. Each item: "
        '{"question": string, "model_answer": string}.'
    )
    prompt = (
        f"Subject: {subject}\nModule: {module}\n"
        f"Write {n} {qtype}-answer questions of {difficulty} difficulty, each worth {marks}, "
        f"with a model answer.\n\nContext:\n{format_context(chunks)}"
    )
    return system, prompt


def quiz_prompt(subject, module, chunks, n=5):
    system = (
        "You are a quiz writer for university courses. Use ONLY the context. "
        "Return ONLY a JSON array, no other text. Each item: "
        '{"question": string, "options": [4 strings], "correct_index": 0-3, "explanation": string}. '
        "Exactly one option is correct; distractors must be plausible."
    )
    prompt = f"Subject: {subject}\nModule: {module}\nWrite {n} multiple-choice questions.\n\nContext:\n{format_context(chunks)}"
    return system, prompt


def validate_quiz(data):
    """Raise ValueError unless data is a list of well-formed MCQs."""
    if not isinstance(data, list) or not data:
        raise ValueError("quiz must be a non-empty list")
    for q in data:
        if not isinstance(q, dict) or not q.get("question") or not q.get("explanation"):
            raise ValueError("each item needs question and explanation")
        opts = q.get("options")
        if not isinstance(opts, list) or len(opts) != 4 or not all(isinstance(o, str) and o for o in opts):
            raise ValueError("each item needs exactly 4 options")
        ci = q.get("correct_index")
        if not isinstance(ci, int) or isinstance(ci, bool) or not 0 <= ci <= 3:
            raise ValueError("correct_index must be 0-3")


def validate_questions(data):
    if not isinstance(data, list) or not data:
        raise ValueError("questions must be a non-empty list")
    for q in data:
        if not isinstance(q, dict) or not q.get("question") or not q.get("model_answer"):
            raise ValueError("each item needs question and model_answer")
