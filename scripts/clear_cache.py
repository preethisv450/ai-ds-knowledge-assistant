"""D14: delete saved summaries, questions, quizzes and answers.  python scripts/clear_cache.py
Run it after changing prompts or models if you want everything regenerated."""
import sys

sys.path.insert(0, ".")
from src.backend.cache import get_cache

c = get_cache()
print(f"Removed {c.clear()} saved results from {c.dir}")
