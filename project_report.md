# Academic Project Report: Educational ADBMS Query Optimizer Simulator

## Abstract
Query optimization is a core component of modern relational database management systems (RDBMS) that translates high-level SQL queries into efficient low-level physical execution plans. Because this process is highly abstract and internal, students studying Advanced Database Management Systems (ADBMS) often struggle to grasp it. This report presents an **Educational Query Optimizer Simulator** built using Python, Flask, and SQLite. The simulator parses SQL, builds Relational Algebra trees, applies logical optimization heuristics (Selection Pushdown, Projection Pushdown, Join Reordering), generates alternative physical plans, and uses cost-based models to select the cheapest plan. The interactive dashboard allows students to visualize these concepts in real time.

---

## 1. Introduction
Modern database systems decouple query expression (SQL) from query execution. The user specifies *what* data they want, and the DBMS optimizer decides *how* to retrieve it. This project provides an educational platform that visually exposes these hidden optimization steps. By exposing intermediate ASTs, logical relational algebra structures, physical candidates, and step-by-step optimization logs, it acts as an effective pedagogical tool.

---

## 2. Problem Statement
Many database curriculum materials present query optimization solely through mathematical formulas. Students lack interactive tools to:
1. See how SQL translates into Relational Algebra trees.
2. Observe selection and projection pushdowns dynamically.
3. Understand cost estimation differences between Nested Loop, Hash, and Sort Merge joins.
4. Visualize why indexes change the optimizer's access path choices.

This simulator bridges this gap by providing a hands-on sandbox seeded with real data.

---

## 3. Objectives
The core objectives of this query optimizer simulator are:
* **Lexical & Syntactic Parsing**: Parse select queries, joins, and where filters into a structured AST with detailed syntax and schema auditing.
* **Heuristic Logical Optimization**: Implement Selection Pushdown, Column Pruning (Projection Pushdown), and Join Reordering.
* **Cost-Based Physical Optimization**: Estimate physical plan costs based on dynamic database statistics.
* **Comparison Dashboard**: Display unoptimized vs. optimized logical trees and plan cost comparison bar charts side-by-side.
* **Session Query History & Help Guide**: Build tools for session tracking and conceptual support.

---

## 4. Methodology & System Design
The system is built on a clean pipeline architecture:
1. **Parser & Lexer**: Breaks SQL into tokens, validates syntax, and matches tables and columns against the SQLite schema.
2. **Logical Planner**: Generates a tree of Relational Algebra operators.
3. **Logical Optimizer**: Iteratively rewrites the logical tree using heuristic rules.
4. **Physical Planner**: Creates three physical plans representing baseline, hash-optimized, and sort-merge joins.
5. **Cost Estimator**: Uses table cardinialities and selectivity values to estimate page reads (I/O) and CPU operations.
6. **Best Plan Selector**: Chooses the plan with the lowest estimated total cost and compiles explanations.
7. **Frontend Web UI**: Interactive glassmorphism single-page application built with HTML5, CSS3, and ES6 JavaScript.

---

## 5. Database Schema & Design
The simulated database represents a university management system with four tables:

```sql
CREATE TABLE Department (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE Teacher (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    dept_id INTEGER,
    FOREIGN KEY (dept_id) REFERENCES Department (id)
);

CREATE TABLE Course (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    teacher_id INTEGER,
    FOREIGN KEY (teacher_id) REFERENCES Teacher (id)
);

CREATE TABLE Student (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    dept_id INTEGER,
    cgpa REAL CHECK (cgpa >= 0.0 AND cgpa <= 4.0),
    FOREIGN KEY (dept_id) REFERENCES Department (id)
);
```

The database is pre-seeded with **10 departments, 100 teachers, 200 courses, and 5,000 students** to ensure realistic statistic profiles.

---

## 6. Optimization Algorithms & Cost Equations

### 6.1 Cost Formulas
* **Sequential Scan Cost**:
  $$\text{Cost}_{seq} = \text{Table Rows} \times 1.0 \text{ (I/O)} + \text{Table Rows} \times 0.01 \text{ (CPU)}$$
* **Index Scan Cost**:
  $$\text{Cost}_{idx} = \log_2(\text{Table Rows}) \times 1.0 \text{ (I/O)} + \log_2(\text{Table Rows}) \times 0.1 \text{ (CPU)}$$
* **Nested Loop Join**:
  $$\text{Cost}_{nlj} = \text{Left IO} + \text{Left Rows} \times \text{Right IO} + \text{Left Rows} \times \text{Right Rows} \times 0.05 \text{ (CPU)}$$
* **Hash Join**:
  $$\text{Cost}_{hash} = \text{Left IO} + \text{Right IO} + (\text{Left Rows} + \text{Right Rows}) \times 1.5 \text{ (CPU)}$$
* **Sort Merge Join**:
  $$\text{Cost}_{smj} = \text{Left IO} + \text{Right IO} + \text{Left Rows}\log_2(\text{Left Rows})\times 0.2 + \text{Right Rows}\log_2(\text{Right Rows})\times 0.2 + (\text{Left Rows} + \text{Right Rows})\times 0.1 \text{ (CPU)}$$

---

## 7. Results & Analysis
Testing demonstrates that the logical rules successfully minimize the cost of queries. For instance, executing a join query with a filter:

```sql
SELECT Student.name, Department.name 
FROM Student 
JOIN Department ON Student.dept_id = Department.id 
WHERE Student.cgpa > 3.7
```

* **Without Optimization**: The entire Student table (5,000 rows) is joined with Department, resulting in a large intermediate space.
* **With Optimization**: Selection pushdown filters Student rows down to ~1,500 *before* the join. Projection pushdown limits attributes to name and dept_id.
* **Outcome**: The plan cost drops from 13,105.15 to 7,105.15, achieving a **45.78% total cost reduction**.

---

## 8. Conclusion & Future Work
This simulator successfully demonstrates query compilation, rewriting, and physical planning. Future enhancements will include:
1. **Dynamic Schema Editor**: Let users add or drop columns and custom indexes, observing cost metrics adapt instantly.
2. **Visual Join Histograms**: Implement attribute value frequency distribution bars to show selectivity estimations visually.
3. **Advanced Rewrite Rules**: Support subquery flattening and join elimination heuristics.
