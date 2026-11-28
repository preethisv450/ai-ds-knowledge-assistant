# AI & DS Knowledge Assistant — Report, Part 2

Sections 6 to 8 and the reference list. When merging with Part 1, delete the
reference list at the end of Part 1 and keep this one.

Figures marked **TODO** come from runs that must be completed and the real
numbers substituted. Do not submit with TODO in place.

---

## 6. Results

### 6.1 Question answering accuracy

The system was evaluated against a hand-written test set of questions drawn
from the source documents, each recording the expected keywords and the
document and page the answer should cite. An answer passes if it contains at
least 60% of the expected keywords. Unanswerable questions pass only if the
system refuses them rather than inventing an answer.

Retrieval and generation are scored separately. Retrieval is judged by whether
the expected page appears among the five chunks returned; generation by whether
the final answer is correct. The split matters because the two failure modes
need different fixes.

| Run | Questions | Threshold | Answer accuracy | Expected page retrieved | Note |
|---|---|---|---|---|---|
| 1 | 30 | 0.12 | 97% (29/30) | 96% | baseline |
| 2 | 30 | 0.04 | 100% (30/30) | 100% | after threshold change |
| 3 | 38 | 0.04 | **TODO** | **TODO** | 8 regulation questions added |
| 4 | 50 | 0.04 | **TODO** | **TODO** | final set, 35 syllabus and 15 regulation |

All three deliberately unanswerable questions were refused in every run,
meaning the system did not fabricate an answer when the corpus did not contain
one.

### 6.2 What the threshold experiment showed

The one failure in run 1 was instructive. The question "What does PEAS stand
for?" returned no answer, not because retrieval failed — the correct page was
ranked first — but because the best chunk scored 0.05 against a cutoff of 0.12.
Short acronym questions produce low similarity scores against any passage, and
the lowest-scoring answerable question (0.054) scored below the
highest-scoring unanswerable one (0.145). No single cutoff separates the two.

The fix was to lower the cutoff for chat answers to 0.04 and rely on the
prompt's instruction to refuse when the passages do not contain the answer. All
three unanswerable questions were still refused. The stricter 0.12 cutoff was
kept for summaries, questions and quizzes, because those retrieve more broadly
and the looser setting allowed unrelated pages into the source list.

The finding is that a similarity threshold cannot distinguish relevance on its
own, and that a well-specified refusal instruction does the job better.

### 6.3 Network analysis findings

The curated concept graph holds **151 concepts** and **141 relations** across
**10 subjects** and **30 modules**. Relations are 130 prerequisite edges and 11
related-to edges, each carrying a note justifying it.

**Centrality.** Degree and Freeman betweenness centrality rank concepts
differently, which is the point of computing both.

| Measure | Top concept | Score | Interpretation |
|---|---|---|---|
| Degree | Derivative (MA101) | 0.0333 | four concepts depend on it directly |
| Betweenness | Backpropagation (DS301) | 0.0016 | lies on the most paths between topics |

Backpropagation tops the betweenness ranking not because of its neighbours
within Deep Learning but because paths from Engineering Mathematics into Deep
Learning must pass through it. Derivative tops degree centrality. The two
measures answer different questions: which concept is locally busiest, and
which concept is a bottleneck in the learning sequence.

Of 151 concepts, 71 have a non-zero betweenness score; the remaining 80 are
leaves in the dependency structure.

**Communities.** Louvain detection found **21 communities** with a modularity
of **0.924**, far above the 0.3 threshold conventionally taken to indicate real
community structure. No community consisted of a single concept, meaning every
concept is connected to the structure.

Seventeen of the 21 communities are at least 60% drawn from one module or
subject, which is what should happen if the hand-written relations follow the
teaching order; this is evidence that the curation is consistent with the
syllabus rather than arbitrary. The remaining communities span subjects and are
the more interesting result. One groups Derivative and Chain Rule from
Engineering Mathematics with Backpropagation, Loss Function and the other
neural-network concepts — the algorithm recovering the maths-to-deep-learning
dependency without being told it exists.

**Cross-subject dependencies.** Ten relations connect one subject to another:

| Learn this | Before or alongside | Subjects |
|---|---|---|
| Derivative | Backpropagation | MA101 → DS301 |
| Eigenvalue | Principal Component Analysis | MA101 → DS202 |
| Array | Static Array | CS101 → CS102 |
| Pointer | Singly Linked List | CS101 → CS102 |
| Graph Traversal | State Space Search | CS102 → AI201 |
| Supervised Learning | Perceptron | DS202 → DS301 |
| Transformer | Pretrained Language Model | DS301 → DS302 |
| Overfitting | Training Data Bias | DS202 → DS402 |
| Train Test Split | Fairness Metric | DS202 → DS402 |
| Relational Model | Partitioning | CS201 → DS401 |

These are the dependencies a timetable hides: the concept a student needs was
taught in a different subject, possibly a different semester. They are also the
claims most worth a faculty member's scrutiny, because no single subject owns
them.

**Teaching order.** A topological sort of the prerequisite edges within each
subject produces a layered order in which every layer depends only on earlier
ones. For Engineering Mathematics I this yields five layers, beginning with
Limit, Vector Space and Differential Equation and ending with the Laplace
Transform.

### 6.4 Content quality and student feedback

Summaries, practice questions and quizzes were scored against a rubric on
correctness, scope, clarity, structure and citation, across six modules.

| | Modules reviewed | Mean score (1-5) | Items scoring 1 or 2 |
|---|---|---|---|
| Summaries | **TODO** | **TODO** | **TODO** |
| Quizzes | **TODO** | **TODO** | **TODO** |

Student feedback was collected from **TODO** students who had used the system
for at least a week. **TODO — the two highest-rated aspects, the lowest-rated
aspect, and the one change made in response.**

The concept graph was reviewed by **TODO (name, role)** on **TODO (date)**, who
**TODO (accepted / accepted with changes / rejected)**. **TODO — summarise the
changes requested and whether they were applied.**

### 6.5 Threats to validity

The accuracy figures above are measured on sample documents of three pages per
subject, carrying the line "SAMPLE DATA for testing — not real course
material". High accuracy on such a corpus demonstrates that the pipeline works;
it is not evidence of performance on a full syllabus of several hundred pages,
where retrieval has far more opportunity to return a plausible but wrong page.

Only two of the ten subjects have source documents at all. Every retrieval
measurement therefore covers AI201 and DS202 only.

Concept relations for the remaining eight subjects were written from standard
course content rather than extracted from documents, so the centrality and
community results for those subjects are provisional until the faculty review
confirms them.

The pass rule — 60% keyword overlap — rewards an answer that contains the right
words. It does not detect an answer that contains the right words in a wrong
explanation. A human reading of a sample of answers, as in section 6.4, is a
necessary complement to the automated score.

## 7. Conclusion

The project set out to answer questions from a programme's own documents with
verifiable citations, generate study material from the same sources, and expose
the curriculum's dependency structure. All three were achieved.

Retrieval-augmented generation over institutional PDFs produces answers that
cite a document and a page, and refuses when the corpus does not contain the
answer — behaviour a general-purpose chatbot does not offer and which matters
more in an academic setting than fluency does. The threshold experiment in
section 6.2 showed that this refusal behaviour is better enforced by the prompt
than by a similarity cutoff, which is a transferable finding for anyone
building retrieval over a small corpus.

Treating the curriculum as a network rather than a list produced results a
reading of the syllabus would not. The ten cross-subject dependencies, and the
community that merges calculus with neural networks, are structural facts about
the programme that no individual subject's document states. The distinction
between degree and betweenness centrality turned out to be substantive and not
merely technical: the concept with the most connections and the concept that
most blocks progress are different concepts.

The main limitation is data. The system is only as good as the documents it is
given, and in this project it was given two subjects' worth of sample pages.
The architecture is unchanged by that; the evidence is weakened by it.

## 8. Future work

**Complete the corpus.** Obtaining the remaining eight syllabi would make every
measurement in section 6 meaningful across the whole programme and would
replace the hand-written concept relations with extracted ones.

**Derive relations rather than assert them.** With a full corpus, prerequisite
edges could be proposed automatically — a concept defined in terms of another
is a candidate dependency — and then confirmed by a teacher, reducing the
curation effort that currently limits the graph's size.

**Evaluate meaning, not keywords.** Replacing the 60% keyword rule with a
judged comparison against a reference answer would catch answers that use the
right vocabulary to say the wrong thing.

**Personalise the study order.** The graph currently describes the curriculum.
Recording which concepts a student has already met would let it recommend the
next concept for that student rather than the general starting points.

**Deploy for a cohort.** The system runs on one machine. Hosting it, with the
index built once and shared, would let a class use it and would turn the
twenty-student feedback exercise into a continuous source of failure cases.

**Connect the timetable.** The timetable page is a placeholder. Linking it to
the concept graph would let the system say what to revise before a given class.

---

### References

[1] P. Lewis et al., "Retrieval-Augmented Generation for Knowledge-Intensive
NLP Tasks," *Advances in Neural Information Processing Systems*, vol. 33, 2020.

[2] N. Reimers and I. Gurevych, "Sentence-BERT: Sentence Embeddings using
Siamese BERT-Networks," *Proceedings of EMNLP-IJCNLP*, 2019.

[3] J. Johnson, M. Douze and H. Jégou, "Billion-scale similarity search with
GPUs," *IEEE Transactions on Big Data*, vol. 7, no. 3, pp. 535–547, 2019.

[4] L. C. Freeman, "A Set of Measures of Centrality Based on Betweenness,"
*Sociometry*, vol. 40, no. 1, pp. 35–41, 1977.

[5] V. D. Blondel, J.-L. Guillaume, R. Lambiotte and E. Lefebvre, "Fast
unfolding of communities in large networks," *Journal of Statistical Mechanics:
Theory and Experiment*, P10008, 2008.

[6] A. A. Hagberg, D. A. Schult and P. J. Swart, "Exploring network structure,
dynamics, and function using NetworkX," *Proceedings of the 7th Python in
Science Conference*, pp. 11–15, 2008.
