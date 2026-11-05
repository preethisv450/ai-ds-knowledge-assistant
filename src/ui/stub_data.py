"""Temporary curriculum data for Day 2.

Day 4: replace the body of get_curriculum() with a cached loader that
reads Nishant's JSON. Keep the function name and return shape identical
so nothing else in the app has to change.
"""

_CURRICULUM = {
    "Year 1": {
        "Semester 1": {
            "Engineering Mathematics I": [
                "M1: Calculus",
                "M2: Linear Algebra",
                "M3: Differential Equations",
            ],
            "Programming in C": [
                "M1: Basics and Control Flow",
                "M2: Arrays and Strings",
                "M3: Pointers",
            ],
        },
        "Semester 2": {
            "Data Structures": [
                "M1: Arrays and Linked Lists",
                "M2: Stacks and Queues",
                "M3: Trees and Graphs",
            ],
        },
    },
    "Year 2": {
        "Semester 3": {
            "Artificial Intelligence": [
                "M1: Introduction to AI",
                "M2: Problem Solving and Search",
                "M3: Knowledge Representation",
            ],
            "Database Systems": [
                "M1: ER Modelling",
                "M2: SQL",
                "M3: Normalization",
            ],
        },
        "Semester 4": {
            "Machine Learning": [
                "M1: Supervised Learning",
                "M2: Unsupervised Learning",
                "M3: Model Evaluation",
            ],
        },
    },
}


def get_curriculum():
    """Return the full curriculum tree: year -> semester -> subject -> [modules]."""
    return _CURRICULUM
