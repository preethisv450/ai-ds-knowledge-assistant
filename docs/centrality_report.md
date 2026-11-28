# Concept centrality — D12

Graph: 151 concepts, 141 relations, built by `scripts/build_concept_graph.py`.
Measures are Freeman's degree and betweenness centrality, both normalised, computed with NetworkX on the directed graph.

- **prerequisites** — concepts that must come first (in-degree)
- **leads_to** — concepts that build on it (out-degree)
- **betweenness** — how often it sits on the shortest path between two other concepts; the bridge measure

## Bridge concepts

These carry the most traffic between topics. Skipping one blocks the largest number of later concepts, so they are the ones to teach and revise first.

| Rank | Concept | Subject | Module | Betweenness | Leads to |
|---|---|---|---|---|---|
| 1 | Backpropagation | DS301 | DS301-M1 | 0.0016 | 1 |
| 2 | Convolution | DS301 | DS301-M2 | 0.0014 | 1 |
| 3 | Filter Kernel | DS301 | DS301-M2 | 0.0012 | 1 |
| 4 | Loss Function | DS301 | DS301-M1 | 0.0011 | 1 |
| 5 | Feedforward Network | DS301 | DS301-M1 | 0.0009 | 1 |
| 6 | State Space Search | AI201 | AI201-M2 | 0.0009 | 2 |
| 7 | Pooling | DS301 | DS301-M2 | 0.0009 | 1 |
| 8 | Activation Function | DS301 | DS301-M1 | 0.0007 | 1 |
| 9 | Graph Traversal | CS102 | CS102-M3 | 0.0007 | 1 |
| 10 | Breadth First Search | AI201 | AI201-M2 | 0.0005 | 2 |

## Top 20 by degree centrality

Degree centrality counts direct connections, so this is a measure of how densely a concept sits in the syllabus rather than how much depends on it.

| Concept | Subject | Prerequisites | Leads to | Degree |
|---|---|---|---|---|
| Derivative | MA101 | 1 | 4 | 0.0333 |
| Fairness Metric | DS402 | 2 | 2 | 0.0267 |
| Overfitting | DS202 | 1 | 3 | 0.0267 |
| Pointer | CS101 | 0 | 4 | 0.0267 |
| Select Query | CS201 | 1 | 3 | 0.0267 |
| Singly Linked List | CS102 | 2 | 2 | 0.0267 |
| State Space Search | AI201 | 2 | 2 | 0.0267 |
| Supervised Learning | DS202 | 0 | 4 | 0.0267 |
| A Star Search | AI201 | 2 | 1 | 0.0200 |
| Array | CS101 | 0 | 3 | 0.0200 |
| Backpropagation | DS301 | 2 | 1 | 0.0200 |
| Breadth First Search | AI201 | 1 | 2 | 0.0200 |
| Determinant | MA101 | 1 | 2 | 0.0200 |
| Forward Chaining | AI201 | 2 | 1 | 0.0200 |
| Graph Traversal | CS102 | 2 | 1 | 0.0200 |
| Inference | AI201 | 0 | 3 | 0.0200 |
| Partitioning | DS401 | 2 | 1 | 0.0200 |
| Queue | CS102 | 1 | 2 | 0.0200 |
| Static Array | CS102 | 2 | 1 | 0.0200 |
| Train Test Split | DS202 | 1 | 2 | 0.0200 |

## Starting points

Concepts with no prerequisites, ranked by how much follows from them. These are where a student with no background should begin.

| Concept | Subject | Module | Leads to |
|---|---|---|---|
| Pointer | CS101 | CS101-M3 | 4 |
| Supervised Learning | DS202 | DS202-M1 | 4 |
| Array | CS101 | CS101-M2 | 3 |
| Inference | AI201 | AI201-M3 | 3 |
| AI Regulation | DS402 | DS402-M3 | 2 |
| Binary Tree | CS102 | CS102-M3 | 2 |
| Clustering | DS202 | DS202-M2 | 2 |
| Confusion Matrix | DS202 | DS202-M3 | 2 |
| Entity | CS201 | CS201-M1 | 2 |
| Heuristic Function | AI201 | AI201-M2 | 2 |

## Links that cross subjects

10 relations connect one subject to another. These are why the bridge scores above are not simply the busiest concept inside each module.

| From | To |
|---|---|
| Supervised Learning (DS202) | Perceptron (DS301) |
| Overfitting (DS202) | Training Data Bias (DS402) |
| Train Test Split (DS202) | Fairness Metric (DS402) |
| Derivative (MA101) | Backpropagation (DS301) |
| Eigenvalue (MA101) | Principal Component Analysis (DS202) |
| Array (CS101) | Static Array (CS102) |
| Pointer (CS101) | Singly Linked List (CS102) |
| Graph Traversal (CS102) | State Space Search (AI201) |
| Relational Model (CS201) | Partitioning (DS401) |
| Transformer (DS301) | Pretrained Language Model (DS302) |

Full table for all 151 concepts: `data/processed/centrality.csv`.
