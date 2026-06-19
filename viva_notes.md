# ADBMS Query Optimizer Simulator: Viva Preparation Notes

This document provides a summary of the Query Optimizer Simulator project to assist students in preparing for oral defense (viva voce) examinations.

---

## 🏛️ Project Objective & Architecture

### 1. Objective
To design and build an educational simulator of a Relational Database Management System (RDBMS) Query Optimizer. It demonstrates how SQL queries are parsed, parsed into logical Relational Algebra trees, optimized through heuristic rewriting rules, planned into alternative physical execution pathways, and evaluated using cost-based models.

### 2. Architecture Overview
The simulator consists of a modular query compiling pipelining flow:
1. **SQL Parsing & Validation**: Reads raw SQL, tokenizes it, and constructs an Abstract Syntax Tree (AST) representing SELECT, FROM, JOIN, and WHERE components.
2. **Schema Verification**: Cross-checks the AST against actual database schemas to reject queries referencing unknown tables or columns.
3. **Logical Tree Construction**: Transforms the verified AST into a logical Relational Algebra plan containing `Projection`, `Selection`, `Join`, and `Relation` nodes.
4. **Logical Optimization Rule Engine**: Applies heuristic rules (Join Reordering, Selection Pushdown, and Projection Pushdown) to generate an optimized logical tree.
5. **Physical Plan Generator**: Translates the logical nodes into concrete physical candidates (Plan A: Nested Loop Join, Plan B: Hash Join, Plan C: Sort Merge Join).
6. **Cost Estimation Engine**: Recursively calculates I/O and CPU costs for each node using database statistics (row counts) dynamically read from SQLite.
7. ** Chepest Plan Selector**: Chooses the physical plan with the lowest cost and generates human-readable explanations.
8. **Execution**: Executes the query against the SQLite database to fetch actual row counts and execution times.

---

## ⚡ Core Concepts & Algorithms

### 1. Access Paths: Sequential Scan vs. Index Scan
* **Sequential Scan (Seq Scan)**: Iterates through every row in the table. Its cost grows linearly $O(N)$ with the table size. Excellent for small tables but highly inefficient for large tables.
* **Index Scan**: Uses a pre-existing index (like a primary key B-Tree index) to jump directly to specific records. Its cost is logarithmic $O(\log N)$ in height, making it extremely fast for point lookups.

### 2. Join Algorithms: NLJ vs. Hash Join vs. Sort Merge
* **Nested Loop Join (NLJ)**: Scans the outer table, and for each row, scans the inner table. Cost is $O(M \times N)$ or $O(M \times \log N)$ if the inner table has an index. Highly inefficient for large, unindexed datasets.
* **Hash Join**: Builds an in-memory hash table of the smaller table's join keys, then scans the larger table to probe the hash table. Its cost is linear $O(M + N)$. It is the preferred choice for large, unsorted sets.
* **Sort Merge Join**: Sorts both tables by join keys, then merges them in a single pass. Cost is $O(M \log M + N \log N)$ for sorting, plus $O(M + N)$ for merging. Ideal when inputs are already sorted or indexed.

### 3. Logical Optimization Rules
* **Selection Pushdown**: Moves `Selection` ($\sigma$) nodes down the tree, applying filters before joins. This reduces the number of rows that must be processed during expensive join operations.
* **Projection Pushdown**: Moves `Projection` ($\pi$) nodes down, instructing scans to only fetch columns referenced in the query. This saves memory and decreases CPU cache misses.
* **Join Reordering**: Alters the sequence of join operations (e.g., joining smaller tables first) to reduce the size of intermediate relations.

---

## ❓ Expected Viva Questions & Answers

### Q1: What is the main difference between Logical and Physical query plans?
**A**: A **Logical Plan** represents the query in terms of relational algebra operators (e.g., Projection, Selection, Join) and defines *what* data to retrieve without specifying the algorithm. A **Physical Plan** translates these operators into executable algorithms (e.g., Seq Scan vs. Index Scan, Nested Loop vs. Hash Join) describing *how* the data will be retrieved.

### Q2: What is Cost-Based Optimization (CBO) and how does it work?
**A**: CBO is an optimization strategy where the optimizer generates multiple candidate physical plans and estimates the cost of each using mathematical cost formulas and database statistics (e.g., row counts, index availability). The plan with the lowest estimated total cost is selected for execution.

### Q3: Why is Selection Pushdown considered a critical heuristic?
**A**: It reduces intermediate relation sizes as early as possible. If a table of 5,000 rows is joined with a table of 100 rows, joining first yields an intermediate space. Filtering the 5,000-row table down to 50 rows *before* joining means the join operator only processes $50 \times 100$ combinations, saving significant CPU and memory.

### Q4: Explain the cost formula for a Nested Loop Join.
**A**: $\text{Cost} = \text{Left Cost} + (\text{Left Rows} \times \text{Right Cost})$. For every row emitted by the outer (left) child, we must perform a complete scan of the inner (right) child. If the inner relation is large and lacks an index, the cost escalates rapidly.

### Q5: How does Projection Pushdown improve query performance?
**A**: In row-store databases, fetching whole rows puts unused columns into memory buffers. Projection Pushdown prunes columns early, minimizing I/O byte transfers and reducing memory consumption during sorting or hashing.

### Q6: How does your simulator handle SQL syntax errors?
**A**: It uses a custom lexical analyzer and recursive descent parser that validates keywords, parenthesis, operator positions, and raises descriptive syntax errors (e.g., `"SQL Syntax Error: Trailing comma in SELECT column list"`). Additionally, it cross-checks parsed identifiers against the active database schema to report unknown tables or columns.
