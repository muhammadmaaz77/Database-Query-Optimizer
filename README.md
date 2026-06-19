# Educational ADBMS Query Optimizer Simulator

A production-ready Advanced Database Management Systems (ADBMS) query optimization simulator. This educational simulator demonstrates logical query optimization rewrites, physical execution plan generation, cost-based planning, schema statistics, and query execution analytics using a real SQLite backend.

Designed for university coursework, laboratory demonstrations, and ADBMS viva examinations.

---

## 🚀 Key Educational Features

### 1. Logical Query Optimization Rules
The optimizer implements three major logical optimization rules to rewrite the parsed query's Relational Algebra representation before physical planning:
* **Selection Pushdown**: Pushes `WHERE` predicates down past relational `Join` operators close to the base `Relation` scans, reducing intermediate tuple counts early.
* **Projection Pushdown**: Removes unused table attributes as early as possible. Prunes scanned columns to match only the projected, filter, and join columns, saving memory and I/O bus overhead.
* **Join Reordering**: Evaluates permutations of multi-join sequences (e.g. `A JOIN B JOIN C`), estimates logical tree costs, and reorders joins (placing smaller/cheaper joins first) to minimize intermediate cartesian or matching spaces.

### 2. Physical Plan Generator & Cost-Based Optimizer (CBO)
Translates the logical Relational Algebra nodes into concrete physical operators. It generates **three alternative execution plans** for comparison:
* **Plan A (Baseline)**: Sequential Scan + Nested Loop Join (classical cross-product-based fallback).
* **Plan B (Hash Join Optimized)**: Index Scan (simulated) + Hash Join (highly efficient for large, unsorted datasets).
* **Plan C (Sort Merge Join)**: Index Scan (simulated) + Sort Merge Join (ideal when inputs are pre-sorted or indexed).

It calculates physical costs using database statistics:
* **Sequential Scan Cost** = `row_count` (I/O) + `row_count * 0.01` (CPU)
* **Index Scan Cost** = `log2(row_count)` (I/O) + `log2(row_count) * 0.1` (CPU)
* **Nested Loop Join Cost** = `outer_io` + `outer_rows * inner_io` + CPU evaluation
* **Hash Join Cost** = `left_io` + `right_io` + `(left_rows + right_rows) * 1.5` (CPU)
* **Sort Merge Join Cost** = `left_io` + `right_io` + `sort_cost` + `merge_cost`

### 3. Optimization Explanation Engine
Generates human-readable, educational explanation logs explaining the optimizer's decisions step-by-step (e.g. why selections were pushed, which join reordering was preferred, cost metrics before vs. after, and why the best physical plan was selected).

### 4. Side-by-Side Comparison Dashboard
Includes an optimization analytics panel showcasing the unoptimized logical tree vs. the optimized logical tree side-by-side, cost reduction percentages, and the exact physical plan cost matrix comparison with CSS bar charts.

### 5. Session Query History
Stores executed queries in local session storage, displaying the query string, timestamp, selected best plan, and total estimated cost. Clicking "Load Query" restores the query in the editor and re-runs it instantly.

### 6. Database Statistics Explorer
Provides a statistics dashboard showing the active database metrics (table row counts, number of tables, simulated indexed attributes, and total seeded records) dynamically read from the database.

### 7. Educational Guide
A complete built-in help guide explaining sequential scans, index scans, join types (Nested Loop, Hash, Sort Merge), rewrite rules, and cost-based optimization formulas in student-friendly summaries.

---

## 🏛️ Database Schema

The database `university.db` consists of 4 main tables:
1. **`Department`** (`id` INTEGER PRIMARY KEY, `name` TEXT UNIQUE)
2. **`Teacher`** (`id` INTEGER PRIMARY KEY, `name` TEXT, `dept_id` REFERENCES Department)
3. **`Course`** (`id` INTEGER PRIMARY KEY, `name` TEXT, `teacher_id` REFERENCES Teacher)
4. **`Student`** (`id` INTEGER PRIMARY KEY, `name` TEXT, `dept_id` REFERENCES Department, `cgpa` REAL)

The database is pre-seeded with **10 departments, 100 teachers, 200 courses, and 5,000 students** using `fake_data.py` (which runs automatically on app startup).

---

## 📂 Folder Structure

```text
Query Optimizer/
│
├── app.py                  # Flask backend & REST API endpoints (/api/execute, /api/statistics)
├── config.py               # Database paths and environment configuration
├── database.py             # SQLite helper and schema fetcher
├── parser.py               # SQL parsing engine mapping query into abstract components AST
├── algebra_tree.py         # Relational Algebra logical tree structures
├── optimizer.py            # Rule-Based & Cost-Based logical optimizer (Join Reorder, Pushdowns)
├── cost_estimator.py       # CPU/IO cost models for physical and logical plans
├── execution_plans.py      # Translates logical trees into physical Plan A, B, and C
├── fake_data.py            # SQLite data generator creating 5000+ records via Faker
├── requirements.txt        # Python dependency lists
│
├── templates/
│      └── index.html       # Web dashboard with tabular controls
│
├── static/
│      ├── style.css        # Theme, layout styling, node visualizer, CSS bar charts
│      └── script.js        # Ajax requests, history storage, tabs, and plan rendering
│
└── README.md               # Project documentation
```

---

## 🏁 Installation & Running Instructions

### 1. Prerequisites
Install Python 3.8 or higher.

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Start the Application
```bash
python app.py
```
*(Launching `app.py` will automatically initialize `university.db` and generate 5,000+ fake records if they don't exist yet).*

### 4. View in Browser
Open your browser and navigate to:
**`http://127.0.0.1:5000`**

---

## 🧪 Sample SQL Queries to Try

1. **Selection Pushdown Demonstration**:
   ```sql
   SELECT Student.name, Department.name
   FROM Student
   JOIN Department ON Student.dept_id = Department.id
   WHERE Student.cgpa > 3.8
   ```
   *Observe how the Selection is pushed down directly to the `Student` scan in the optimized tree.*

2. **Join Reordering & Multi-Join**:
   ```sql
   SELECT Student.name, Department.name, Teacher.name
   FROM Student
   JOIN Department ON Student.dept_id = Department.id
   JOIN Teacher ON Teacher.dept_id = Department.id
   WHERE Student.cgpa > 3.9
   ```
   *Observe how the optimizer evaluates different join orders to minimize the cost of intermediate relations.*

3. **Projection Pruning**:
   ```sql
   SELECT Student.cgpa
   FROM Student
   WHERE Student.id > 100
   ```
   *Observe how projection pushdown prunes the scanned attributes to only `cgpa` and `id` instead of fetching all columns.*

---

## 📷 Screenshots Section Placeholder
![Dashboard Interface](file:///C:/Users/Soul/.gemini/antigravity-cli/brain/c1e9869c-b4a9-4f1a-8192-d037e83dee3b/scratch/dashboard_mockup.png)
*(Place dashboard screenshots here during viva preparation)*

---

## 🔮 Future Improvements
* **Dynamic Indexing**: Allow users to click to add or drop indexes on tables and see the access path costs change in real-time.
* **Join Selectivity Enhancements**: Integrate histogram-based statistical summaries instead of basic selectivities.
* **Query Editor Autocomplete**: Add SQL keywords and column suggestions in the code input area.
