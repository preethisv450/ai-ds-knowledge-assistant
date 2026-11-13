"""Helpers for the data-layer tests: build small PDFs on the fly."""
import pymupdf


def make_pdf(path, pages, footer=None, header=None):
    """pages: list of page bodies (str). Optional repeated header/footer line per page."""
    doc = pymupdf.open()
    for i, body in enumerate(pages, 1):
        page = doc.new_page(width=595, height=842)
        text = body if header is None else f"{header}\n{body}"
        page.insert_textbox(pymupdf.Rect(50, 50, 545, 780), text, fontsize=11, fontname="helv")
        if footer:
            page.insert_text((50, 800), footer.format(n=i), fontsize=9, fontname="helv")
    doc.save(str(path))
    doc.close()
    return path


CURRICULUM = {
    "schema_version": 2, "programme": "AI & DS",
    "years": [{"year": "Year 2", "semesters": [{"semester": "Semester 3", "subjects": [
        {"code": "AI201", "name": "Artificial Intelligence", "credits": 4, "modules": [
            {"id": "AI201-M1", "title": "Introduction to AI", "topics": ["rational agent", "PEAS"]},
            {"id": "AI201-M2", "title": "Search", "topics": ["A star"]}]}]}]}],
}
