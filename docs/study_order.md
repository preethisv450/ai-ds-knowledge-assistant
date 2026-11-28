# What to study first — D14

Written from the concept graph, not from opinion. Every claim below comes from `data/processed/graph_export.json`: how many concepts depend on each one, and where it sits on the paths between topics.

## Start with these

They need nothing before them, and the most other concepts follow from them. If you are starting a subject cold, start here.

- **Pointer** (Programming in C) — 4 concepts build on it
- **Supervised Learning** (Machine Learning) — 4 concepts build on it
- **Array** (Programming in C) — 3 concepts build on it
- **Inference** (Artificial Intelligence) — 3 concepts build on it
- **AI Regulation** (AI Ethics and Governance) — 2 concepts build on it
- **Binary Tree** (Data Structures) — 2 concepts build on it
- **Clustering** (Machine Learning) — 2 concepts build on it
- **Confusion Matrix** (Machine Learning) — 2 concepts build on it

## Do not skip these

These sit on the paths between topics. Miss one and the concepts beyond it stop making sense, even if the syllabus treats it as a small item.

- **Backpropagation** (Deep Learning) — bridge score 0.0016, 1 concepts beyond it
- **Convolution** (Deep Learning) — bridge score 0.0014, 1 concepts beyond it
- **Filter Kernel** (Deep Learning) — bridge score 0.0012, 1 concepts beyond it
- **Loss Function** (Deep Learning) — bridge score 0.0011, 1 concepts beyond it
- **Feedforward Network** (Deep Learning) — bridge score 0.0009, 1 concepts beyond it
- **Pooling** (Deep Learning) — bridge score 0.0009, 1 concepts beyond it
- **State Space Search** (Artificial Intelligence) — bridge score 0.0009, 2 concepts beyond it
- **Activation Function** (Deep Learning) — bridge score 0.0007, 1 concepts beyond it

## Where one subject depends on another

These are easy to miss because they cross a timetable boundary: the concept you need was taught in a different subject.

- Learn **Supervised Learning** (Machine Learning) before **Perceptron** (Deep Learning)
- Learn **Overfitting** (Machine Learning) alongside **Training Data Bias** (AI Ethics and Governance)
- Learn **Train Test Split** (Machine Learning) alongside **Fairness Metric** (AI Ethics and Governance)
- Learn **Derivative** (Engineering Mathematics I) before **Backpropagation** (Deep Learning)
- Learn **Eigenvalue** (Engineering Mathematics I) before **Principal Component Analysis** (Machine Learning)
- Learn **Array** (Programming in C) before **Static Array** (Data Structures)
- Learn **Pointer** (Programming in C) before **Singly Linked List** (Data Structures)
- Learn **Graph Traversal** (Data Structures) before **State Space Search** (Artificial Intelligence)
- Learn **Relational Model** (Database Systems) alongside **Partitioning** (Big Data Analytics)
- Learn **Transformer** (Deep Learning) before **Pretrained Language Model** (Natural Language Processing)

## Order within each subject

Each step only needs the steps above it. Concepts on the same line can be learnt in any order.

### Artificial Intelligence (AI201)

1. Heuristic Function, Inference, PEAS Description, Propositional Logic, Rational Agent
2. Admissibility, Backward Chaining, First Order Logic, Horn Clause, State Space Search, Task Environment
3. Breadth First Search, Depth First Search, Forward Chaining, Optimality, Resolution
4. A Star Search

### Programming in C (CS101)

1. Array, Pointer, Variable
2. Array Indexing, Data Type, Dynamic Memory, Function Pointer, Pointer Arithmetic, String
3. Multidimensional Array, Operator, Pointer to Array, String Function
4. Conditional Statement
5. Loop

### Data Structures (CS102)

1. Abstract Data Type, Binary Tree, Graph Representation, Stack
2. Binary Search Tree, Queue, Stack Application, Static Array, Tree Traversal
3. Circular Queue, Graph Traversal, Priority Queue, Singly Linked List
4. Circular Linked List, Doubly Linked List

### Database Systems (CS201)

1. Entity, Functional Dependency, Relational Model
2. Attribute, First Normal Form, Relationship, Select Query
3. Aggregate Function, Cardinality, Join, Second Normal Form, Subquery
4. ER Diagram, Third Normal Form
5. Boyce Codd Normal Form

### Machine Learning (DS202)

1. Clustering, Confusion Matrix, Overfitting, Principal Component Analysis, Supervised Learning
2. Bias Variance Tradeoff, Centroid, Linear Regression, Precision and Recall, ROC Curve, Regularisation, Train Test Split
3. Cross Validation, K Means

### Deep Learning (DS301)

1. Perceptron, Sequence Data
2. Activation Function, Recurrent Network
3. Feedforward Network, LSTM
4. Attention Mechanism, Loss Function
5. Backpropagation, Transformer
6. Convolution
7. Filter Kernel
8. Pooling
9. CNN Architecture
10. Transfer Learning

### Natural Language Processing (DS302)

1. N Gram Model, Tokenization
2. Bag of Words, Stopword Removal, Word Embedding
3. Stemming, Text Classification, Word2Vec
4. Contextual Embedding, Lemmatization, Named Entity Recognition
5. Machine Translation, Pretrained Language Model
6. Question Answering
7. Text Summarisation

### Big Data Analytics (DS401)

1. Distributed File System, MapReduce, Streaming Data
2. Event Time, HDFS, Mapper and Reducer, Message Queue, Spark RDD
3. Data Replication, Shuffle and Sort, Spark DataFrame, Stream Processing, Windowing
4. Partitioning
5. CAP Theorem

### AI Ethics and Governance (DS402)

1. AI Regulation, Algorithmic Bias, Personal Data
2. Anonymisation, Consent, Model Documentation, Risk Assessment, Training Data Bias
3. Auditability, Data Minimisation, Differential Privacy, Fairness Metric
4. Accountability, Bias Mitigation, Disparate Impact

### Engineering Mathematics I (MA101)

1. Differential Equation, Limit, Vector Space
2. Derivative, Matrix Operations, Separable Equation
3. Chain Rule, Definite Integral, Determinant, Linear First Order Equation, Taylor Series
4. Eigenvalue, Matrix Inverse, Second Order Linear Equation
5. Laplace Transform

## How to read this

**Bridge score** is betweenness centrality: how often a concept lies on the shortest path between two others. A high score means it carries traffic between topics rather than just having many neighbours.

**A caution.** Only Artificial Intelligence and Machine Learning have concepts drawn from the syllabus PDFs. The relations for the other eight subjects were written by hand from standard course content, so the ordering there is a reasonable default rather than a finding. Check it against the real syllabus before quoting it.
