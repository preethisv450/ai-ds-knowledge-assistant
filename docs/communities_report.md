# Concept communities — D13

Method: Louvain (Blondel et al. 2008), run with `networkx.community.louvain_communities` on the undirected form of the concept graph, weighted by relation strength, seed 42, resolution 1.0.

- Communities found: **21**
- Modularity: **0.924**
- Concepts: 151 across 141 relations

Modularity above about 0.3 means the clustering found real structure rather than splitting an evenly connected graph at random.

## Communities

### 1. Artificial Intelligence — core

15 concepts · 67% from its dominant module or subject · subjects: AI201, CS102

State Space Search, A Star Search, Breadth First Search, Graph Traversal, Admissibility, Binary Tree, Depth First Search, Heuristic Function, and 7 more

### 2. Programming in C — core

15 concepts · 67% from its dominant module or subject · subjects: CS101, CS102

Pointer, Singly Linked List, Array, Static Array, Array Indexing, Pointer Arithmetic, String, Abstract Data Type, and 7 more

### 3. Across subjects: Machine Learning, AI Ethics and Governance

12 concepts · 58% from its dominant module or subject · subjects: DS202, DS402

Fairness Metric, Overfitting, Supervised Learning, Train Test Split, Training Data Bias, Bias Variance Tradeoff, Cross Validation, Linear Regression, and 4 more

### 4. Across subjects: Engineering Mathematics I, Deep Learning

10 concepts · 50% from its dominant module or subject · subjects: DS301, MA101

Derivative, Backpropagation, Activation Function, Feedforward Network, Loss Function, Perceptron, Chain Rule, Definite Integral, and 2 more

### 5. Natural Language Processing — core

10 concepts · 100% from its dominant module or subject · subjects: DS302

Bag of Words, Machine Translation, Named Entity Recognition, Question Answering, Stemming, Stopword Removal, Text Classification, Tokenization, and 2 more

### 6. Across subjects: Natural Language Processing, Deep Learning

10 concepts · 50% from its dominant module or subject · subjects: DS301, DS302

Attention Mechanism, Contextual Embedding, LSTM, Pretrained Language Model, Recurrent Network, Transformer, Word Embedding, Word2Vec, and 2 more

### 7. Across subjects: Big Data Analytics, Database Systems

10 concepts · 50% from its dominant module or subject · subjects: CS201, DS401

Select Query, Partitioning, Data Replication, HDFS, Relational Model, Aggregate Function, CAP Theorem, Distributed File System, and 2 more

### 8. Knowledge Representation

7 concepts · 100% from its dominant module or subject · subjects: AI201

Forward Chaining, Inference, Backward Chaining, First Order Logic, Horn Clause, Propositional Logic, Resolution

### 9. Linear Algebra

6 concepts · 83% from its dominant module or subject · subjects: DS202, MA101

Determinant, Eigenvalue, Matrix Operations, Principal Component Analysis, Matrix Inverse, Vector Space

### 10. Differential Equations

5 concepts · 100% from its dominant module or subject · subjects: MA101

Linear First Order Equation, Second Order Linear Equation, Separable Equation, Differential Equation, Laplace Transform

### 11. Basics and Control Flow

5 concepts · 100% from its dominant module or subject · subjects: CS101

Conditional Statement, Data Type, Operator, Loop, Variable

### 12. Stacks and Queues

5 concepts · 100% from its dominant module or subject · subjects: CS102

Queue, Stack, Circular Queue, Priority Queue, Stack Application

### 13. ER Modelling

5 concepts · 100% from its dominant module or subject · subjects: CS201

Cardinality, Entity, Relationship, Attribute, ER Diagram

### 14. Normalization

5 concepts · 100% from its dominant module or subject · subjects: CS201

First Normal Form, Second Normal Form, Third Normal Form, Boyce Codd Normal Form, Functional Dependency

### 15. Convolutional Networks

5 concepts · 100% from its dominant module or subject · subjects: DS301

CNN Architecture, Convolution, Filter Kernel, Pooling, Transfer Learning

### 16. MapReduce and Spark

5 concepts · 100% from its dominant module or subject · subjects: DS401

MapReduce, Mapper and Reducer, Spark RDD, Shuffle and Sort, Spark DataFrame

### 17. Streaming Analytics

5 concepts · 100% from its dominant module or subject · subjects: DS401

Event Time, Message Queue, Streaming Data, Stream Processing, Windowing

### 18. Privacy and Data Protection

5 concepts · 100% from its dominant module or subject · subjects: DS402

Anonymisation, Consent, Personal Data, Data Minimisation, Differential Privacy

### 19. Regulation and Accountability

5 concepts · 100% from its dominant module or subject · subjects: DS402

AI Regulation, Auditability, Model Documentation, Accountability, Risk Assessment

### 20. Unsupervised Learning

3 concepts · 100% from its dominant module or subject · subjects: DS202

Centroid, Clustering, K Means

### 21. Model Evaluation

3 concepts · 100% from its dominant module or subject · subjects: DS202

Confusion Matrix, Precision and Recall, ROC Curve

## Do the clusters make sense?

- **Alignment with the syllabus.** 17 of 21 communities are at least 60% one module or subject, which is what you would expect if the hand-written relations follow the teaching order.
- **Communities spanning subjects:** 7. These are the interesting ones: they show where the curriculum genuinely connects across subject boundaries.
- **Single-concept communities:** 0. None, so every concept belongs to a group.

Re-run with `--resolution=0.8` for fewer, larger communities or `--resolution=1.4` for more, smaller ones, and `--seed=` to confirm the grouping is stable.

Full assignment for all 151 concepts: `data/processed/communities.csv`.
