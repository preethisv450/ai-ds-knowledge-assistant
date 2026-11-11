"""D15: create SAMPLE documents so every feature can be tested end to end before the real PDFs arrive.

  python scripts/make_sample_data.py          write the sample PDFs, manifest and test questions
  python scripts/make_sample_data.py --clean  remove exactly what this script wrote

Writes (all clearly marked SAMPLE; the content is invented for testing, not real course material):
  data/pdfs/AI201_syllabus.pdf, DS202_syllabus.pdf, Academic_Regulations.pdf
  data/processed/documents.json        (module -> page ranges; refuses to overwrite a different file)
  data/eval/e2e_questions.csv          (questions with known answers for scripts/e2e_check.py)
Real documents replace these later: delete them with --clean, then follow docs/data_manifest.md.
"""
import csv
import sys
from pathlib import Path

try:
    import pymupdf as fitz
except ImportError:  # older PyMuPDF
    import fitz

ROOT = Path(__file__).resolve().parents[1]
PDF_DIR = ROOT / "data" / "pdfs"
MANIFEST = ROOT / "data" / "processed" / "documents.json"
QUESTIONS = ROOT / "data" / "eval" / "e2e_questions.csv"
MARK = "SAMPLE DATA for testing - not real course material"

SYLLABI = {
    "AI201_syllabus.pdf": ("AI201", "Artificial Intelligence", [
        ("AI201-M1", "Module 1: Introduction to AI",
         "Artificial intelligence is the study of agents that perceive their environment and take actions to achieve goals. "
         "The term artificial intelligence was coined by John McCarthy at the Dartmouth workshop in 1956. "
         "Alan Turing proposed the Turing test in 1950: a machine passes if a human judge cannot tell its answers from a person's. "
         "A rational agent chooses the action expected to maximise its performance measure. "
         "Agent types are simple reflex, model-based reflex, goal-based, utility-based and learning agents. "
         "A task environment is described using PEAS: Performance measure, Environment, Actuators and Sensors. "
         "Environments are classified as fully or partially observable, deterministic or stochastic, episodic or sequential, "
         "static or dynamic, discrete or continuous, and single-agent or multi-agent. "
         "Reference text: Russell and Norvig, Artificial Intelligence: A Modern Approach."),
        ("AI201-M2", "Module 2: Problem Solving and Search",
         "Problem solving is modelled as search through a state space from an initial state to a goal state. "
         "Breadth-first search expands the shallowest node first; it is complete and optimal when every step costs the same, "
         "but its time and memory grow as O(b^d). Depth-first search uses memory O(bm) but can get stuck in infinite paths. "
         "Uniform-cost search expands the node with the lowest path cost g(n). Iterative deepening combines the memory use of "
         "depth-first search with the completeness of breadth-first search. "
         "A* search ranks nodes by the evaluation function f(n) = g(n) + h(n), where h(n) estimates the remaining cost. "
         "A heuristic is admissible if it never overestimates the true cost to reach the goal; with an admissible heuristic A* is optimal. "
         "Greedy best-first search uses only h(n). Hill climbing can stop at a local maximum; simulated annealing escapes by "
         "sometimes accepting worse moves. Minimax search with alpha-beta pruning is used for two-player games."),
        ("AI201-M3", "Module 3: Knowledge Representation",
         "A knowledge base is a set of sentences in a formal language that an agent can reason over. "
         "Propositional logic uses symbols and connectives such as AND, OR, NOT and implies. First-order logic adds objects, "
         "predicates and the quantifiers for all and there exists. "
         "Modus ponens is an inference rule: from P and the sentence P implies Q, infer Q. "
         "Resolution is a complete inference method for clauses in conjunctive normal form. "
         "Forward chaining starts from known facts and derives new ones; backward chaining starts from a goal and works back to the facts. "
         "A Horn clause has at most one positive literal, and Prolog programs are built from Horn clauses. "
         "Semantic networks and frames organise knowledge as nodes and slots. An ontology defines the concepts of a domain and the "
         "relations between them, and is used by the semantic web."),
    ]),
    "DS202_syllabus.pdf": ("DS202", "Machine Learning", [
        ("DS202-M1", "Module 1: Supervised Learning",
         "In supervised learning the training data is labelled: each example has an input and the correct output. "
         "Regression predicts a number and classification predicts a category. "
         "Linear regression fits a line by least squares, which minimises the sum of squared errors. "
         "Logistic regression passes a linear score through the sigmoid function to give a class probability. "
         "Decision trees split the data using information gain or Gini impurity. k-nearest neighbours classifies a point by the "
         "majority label among its k closest training points. A support vector machine finds the maximum-margin separating boundary. "
         "Overfitting happens when a model memorises the training data and performs poorly on new data. Regularisation fights it: "
         "L1 regularisation (lasso) penalises the absolute size of weights and can set some to zero, while L2 regularisation (ridge) "
         "penalises the squared size of weights."),
        ("DS202-M2", "Module 2: Unsupervised Learning",
         "Unsupervised learning finds structure in unlabelled data. "
         "The k-means algorithm picks k initial centroids, assigns each point to its nearest centroid, recomputes each centroid as the "
         "mean of its points, and repeats until assignments stop changing. The number of clusters k is often chosen with the elbow method, "
         "which plots the within-cluster sum of squares against k and looks for the bend. "
         "Hierarchical agglomerative clustering repeatedly merges the two closest clusters and is drawn as a dendrogram. "
         "DBSCAN groups points that are density-connected using two parameters, eps and minPts, and marks isolated points as noise. "
         "Principal component analysis reduces dimensions by projecting data onto the eigenvectors of the covariance matrix with the "
         "largest eigenvalues. The Apriori algorithm mines association rules using the measures support and confidence."),
        ("DS202-M3", "Module 3: Model Evaluation",
         "Data is split into training, validation and test sets; the test set is used only once at the end. "
         "In k-fold cross-validation the data is divided into k parts and each part is used once for validation; k = 10 is common. "
         "A confusion matrix counts true positives (TP), false positives (FP), true negatives (TN) and false negatives (FN). "
         "Precision = TP / (TP + FP). Recall = TP / (TP + FN). The F1 score is the harmonic mean of precision and recall. "
         "The ROC curve plots the true positive rate against the false positive rate, and the area under it (AUC) summarises the classifier. "
         "The bias-variance trade-off says that very simple models underfit (high bias) and very flexible models overfit (high variance). "
         "For regression, the mean squared error (MSE), its square root (RMSE) and R-squared are used. Data leakage, where test "
         "information reaches training, makes results look better than they are."),
    ]),
}

REGULATIONS = [
    ("Academic Regulations (sample)\n\nAttendance. A student must have at least 75 percent attendance in each subject to appear in the "
     "end-semester examination. A student with attendance between 65 and 75 percent may apply for condonation on medical grounds "
     "and must pay a condonation fee of Rs. 500 per subject. A student with attendance below 65 percent is detained and must repeat "
     "the semester.\n\nAssessment. Every subject has 40 marks of internal assessment and 60 marks of end-semester examination. To pass "
     "a subject a student must score at least 40 percent in the end-semester examination and at least 50 percent in total."),
    ("Grading. Marks are converted to letter grades: O for 90 and above, A+ for 80 to 89, A for 70 to 79, B+ for 60 to 69, B for 50 to 59 "
     "and F below 50. The CGPA is the sum of credits times grade points divided by the sum of credits.\n\nRe-evaluation. A student may "
     "apply for re-evaluation within 7 days of the result being published, with a fee of Rs. 1000 per paper. The better of the two "
     "scores is kept.\n\nBacklogs. A student who fails a subject may appear in the supplementary examination. The maximum duration "
     "to complete the 8-semester programme is 6 years."),
]

# id, question, mode, subject_code, module_id, expected_keywords, expected_doc, expected_page, answerable
QROWS = [
    ("1", "What does PEAS stand for?", "Syllabus", "AI201", "AI201-M1", "Performance|Environment|Actuators|Sensors", "AI201_syllabus.pdf", 1, "yes"),
    ("2", "Who proposed the Turing test and in which year?", "Syllabus", "AI201", "AI201-M1", "Turing|1950", "AI201_syllabus.pdf", 1, "yes"),
    ("3", "What is an admissible heuristic?", "Syllabus", "AI201", "AI201-M2", "overestimate", "AI201_syllabus.pdf", 2, "yes"),
    ("4", "Which evaluation function does A* search use?", "Syllabus", "AI201", "AI201-M2", "g(n)|h(n)", "AI201_syllabus.pdf", 2, "yes"),
    ("5", "State the modus ponens rule.", "Syllabus", "AI201", "AI201-M3", "P|infer", "AI201_syllabus.pdf", 3, "yes"),
    ("6", "How is the number of clusters chosen in k-means?", "Syllabus", "DS202", "DS202-M2", "elbow", "DS202_syllabus.pdf", 2, "yes"),
    ("7", "What is the formula for precision?", "Syllabus", "DS202", "DS202-M3", "TP|FP", "DS202_syllabus.pdf", 3, "yes"),
    ("8", "What does L2 regularisation penalise?", "Syllabus", "DS202", "DS202-M1", "squared", "DS202_syllabus.pdf", 1, "yes"),
    ("9", "What is the minimum attendance required to appear in the end-semester exam?", "Regulation", "", "", "75", "Academic_Regulations.pdf", 1, "yes"),
    ("10", "What is the fee for re-evaluation?", "Regulation", "", "", "1000", "Academic_Regulations.pdf", 2, "yes"),
    ("11", "Which grade is given for 85 marks?", "Regulation", "", "", "A+", "Academic_Regulations.pdf", 2, "yes"),
    ("12", "Who is the vice chancellor of the university?", "Regulation", "", "", "", "", "", "no"),
    ("13", "What is the capital of Peru?", "Syllabus", "AI201", "AI201-M1", "", "", "", "no"),
    ("14", "What is the elbow method?", "Syllabus", "AI201", "AI201-M1", "", "", "", "no"),  # exists, but only in DS202: scoping must hide it
]


def write_pdf(path, pages):
    doc = fitz.open()
    for i, text in enumerate(pages, 1):
        page = doc.new_page(width=595, height=842)
        page.insert_textbox(fitz.Rect(56, 56, 539, 780), text, fontsize=11, fontname="helv")
        page.insert_text((56, 810), f"{MARK}  |  page {i}", fontsize=8, fontname="helv")
    doc.save(str(path))
    doc.close()


def build():
    import json
    PDF_DIR.mkdir(parents=True, exist_ok=True)
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    QUESTIONS.parent.mkdir(parents=True, exist_ok=True)
    manifest = []
    for fname, (code, name, modules) in SYLLABI.items():
        write_pdf(PDF_DIR / fname, [f"{code} {name} - Syllabus\n\n{title}\n\n{text}" for _, title, text in modules])
        manifest.append({"file": fname, "doc_type": "syllabus", "subject_code": code,
                         "modules": {mid: [i, i] for i, (mid, _, _) in enumerate(modules, 1)}})
    write_pdf(PDF_DIR / "Academic_Regulations.pdf", REGULATIONS)
    manifest.append({"file": "Academic_Regulations.pdf", "doc_type": "regulation"})
    new = json.dumps(manifest, indent=2) + "\n"
    if MANIFEST.exists() and MANIFEST.read_text() != new:
        print(f"NOTE: {MANIFEST} already exists with different content, so I left it alone.\n"
              f"      If it is not yours to keep, delete it and run this again.")
    else:
        MANIFEST.write_text(new)
    with open(QUESTIONS, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "question", "mode", "subject_code", "module_id", "expected_keywords",
                    "expected_doc", "expected_page", "answerable"])
        w.writerows(QROWS)
    print("Sample data written:")
    for p in (*(PDF_DIR / n for n in (*SYLLABI, "Academic_Regulations.pdf")), MANIFEST, QUESTIONS):
        print("  ", p.relative_to(ROOT))
    print("\nNext: python scripts/build_index.py   then   python scripts/e2e_check.py")


def clean():
    removed = [PDF_DIR / n for n in (*SYLLABI, "Academic_Regulations.pdf")] + [MANIFEST, QUESTIONS]
    for p in removed:
        if p.exists():
            p.unlink()
            print("removed", p.relative_to(ROOT))
    print("Now run python scripts/build_index.py again so the index matches your files.")


if __name__ == "__main__":
    clean() if "--clean" in sys.argv else build()
