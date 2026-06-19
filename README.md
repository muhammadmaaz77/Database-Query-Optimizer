# 🗃️ Database Query Optimizer Simulator

> A full-stack, educational web application that visually demonstrates how a relational database engine parses, rewrites, optimizes, and executes SQL queries — step by step.

---

## 📌 Overview

The **Database Query Optimizer Simulator** is a Python/Flask web application that simulates the internal query processing pipeline of a relational database management system (RDBMS). It is designed to make abstract database theory tangible and interactive.

Given a SQL `SELECT` query, the simulator:

1. **Parses** the SQL into a structured AST representation
2. **Builds** a Logical Relational Algebra Tree
3. **Optimizes** the logical tree using rule-based rewriting
4. **Generates** three alternative Physical Execution Plans
5. **Estimates** CPU and I/O costs for each plan
6. **Selects** the best plan using cost-based comparison
7. **Executes** the query against a real SQLite database
8. **Visualizes** every step in a rich, interactive dashboard

---

## ✨ Features

| Feature | Description |
|---|---|
| **Custom SQL Parser** | Handwritten tokenizer and parser — no external SQL libraries |
| **Schema Validation** | Validates all tables and columns against the live database schema |
| **Relational Algebra Tree** | Builds a logical plan tree (Projection → Selection → Join → Relation) |
| **Rule-Based Optimization** | Applies Join Reordering, Selection Pushdown, and Projection Pushdown |
| **Physical Plan Generation** | Generates 3 alternative physical plans (A, B, C) with different operators |
| **Cost Estimation** | Models CPU + I/O cost formulas for Seq Scan, Index Scan, NLJ, Hash Join, SMJ |
| **Before vs After Comparison** | Side-by-side comparison of unoptimized vs optimized plan trees and costs |
| **Real Query Execution** | Executes the query on SQLite and returns actual result rows |
| **Auto Data Generation** | Populates a university database (5,000 students, 100 teachers, 200 courses) |
| **REST API** | Full JSON API for schema, execution, and statistics |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                    Flask Web Server                 │
│                       app.py                        │
└────────────────────────┬────────────────────────────┘
                         │
         ┌───────────────┼───────────────────┐
         ▼               ▼                   ▼
   ┌──────────┐   ┌─────────────┐    ┌─────────────┐
   │  parser  │   │ algebra_tree│    │  database   │
   │  .py     │   │ .py         │    │  .py        │
   └──────────┘   └─────────────┘    └─────────────┘
         │               │
         ▼               ▼
   ┌──────────┐   ┌──────────────┐
   │optimizer │──▶│execution_    │
   │  .py     │   │plans.py      │
   └──────────┘   └──────────────┘
         │
         ▼
   ┌──────────────────┐    ┌───────────────────┐
   │ cost_estimator   │◀───│ statistics_manager│
   │ .py              │    │ .py               │
   └──────────────────┘    └───────────────────┘
```

### Module Responsibilities

| Module | Role |
|---|---|
| [`app.py`](app.py) | Flask application, routes, startup initialization |
| [`parser.py`](parser.py) | Custom SQL tokenizer, recursive-descent parser, schema validator |
| [`algebra_tree.py`](algebra_tree.py) | `AlgebraNode` class, logical tree builder |
| [`optimizer.py`](optimizer.py) | `QueryOptimizer` — Join Reordering, Selection Pushdown, Projection Pushdown |
| [`execution_plans.py`](execution_plans.py) | `PhysicalPlanNode`, 3 physical plan generators (NLJ, Hash Join, SMJ) |
| [`cost_estimator.py`](cost_estimator.py) | `CostEstimator` — CPU/I/O formula engine for all physical operators |
| [`statistics_manager.py`](statistics_manager.py) | `DBStatistics` — live table row counts, selectivity & cardinality estimates |
| [`database.py`](database.py) | SQLite connection, schema creation, query execution |
| [`config.py`](config.py) | Configuration (DB path, secret key, debug flag) |
| [`fake_data.py`](fake_data.py) | Faker-based seed data generator for the university database |

---

## 🗄️ Database Schema

The application uses a simulated **university database** with 4 tables:

```sql
Department (id, name)
Teacher    (id, name, dept_id → Department.id)
Course     (id, name, teacher_id → Teacher.id)
Student    (id, name, dept_id → Department.id, cgpa)
```

**Seeded data:**
- 10 Departments
- 100 Teachers
- 200 Courses
- 5,000 Students

The database is auto-created and populated on the first server startup. No manual setup is required.

---

## ⚙️ Query Processing Pipeline

For every submitted SQL query, the following pipeline executes:

```
SQL String
    │
    ▼
[1] Tokenize + Parse  ──── SQLParser.parse()
    │  → Structured AST dict (tables, joins, WHERE, SELECT)
    │
    ▼
[2] Schema Validation ──── validate_schema()
    │  → Verifies all table & column names against live schema
    │
    ▼
[3] Logical Plan      ──── build_initial_tree()
    │  → AlgebraNode tree: Projection → Selection → Join(s) → Relation(s)
    │
    ▼
[4] Optimization      ──── QueryOptimizer.optimize()
    │  → Rule 1: Join Reordering (cost-based swap)
    │  → Rule 2: Selection Pushdown (filter → base relations)
    │  → Rule 3: Projection Pushdown (prune column sets)
    │
    ▼
[5] Physical Planning ──── generate_alternative_plans()
    │  → Plan A: Seq Scan + Nested Loop Join
    │  → Plan B: Index Scan + Hash Join
    │  → Plan C: Index Scan + Sort Merge Join
    │
    ▼
[6] Cost Estimation   ──── CostEstimator.calculate_and_populate_tree()
    │  → CPU + I/O costs per node, ranked by total cost
    │
    ▼
[7] Best Plan Selection
    │  → Lowest total cost plan selected; why_selected rationale generated
    │
    ▼
[8] SQL Execution     ──── execute_query()
    │  → Real SQLite execution, up to 100 result rows returned
    │
    ▼
JSON Response → Frontend Dashboard
```

---

## 💡 Optimization Rules

### Rule 1 — Join Reordering
Evaluates two join orderings and selects the one with the lower estimated cost:
- `BaseTable ⋈ Table1 ⋈ Table2`  vs  `BaseTable ⋈ Table2 ⋈ Table1`

### Rule 2 — Selection Pushdown (σ-pushdown)
Moves `WHERE` filter conditions as close to the base relation as possible, reducing the number of rows that travel up through join operators.

### Rule 3 — Projection Pushdown (π-pushdown)
Prunes unnecessary columns from each table's scanned column set, reducing I/O and intermediate data width.

---

## 📐 Cost Model

Each physical operator has a defined cost formula:

| Operator | I/O Cost | CPU Cost |
|---|---|---|
| **Sequential Scan** | `N` (rows) | `N × 0.01` |
| **Index Scan** | `log₂(N)` | `log₂(N) × 0.1` |
| **Filter** | inherited | `child_rows × 0.1` |
| **Nested Loop Join** | `I/O_left + (rows_left × I/O_right)` | `rows_left × rows_right × 0.05` |
| **Hash Join** | `I/O_left + I/O_right` | `(rows_left + rows_right) × 1.5` |
| **Sort Merge Join** | `I/O_left + I/O_right` | sort cost + `(rows_left + rows_right) × 0.1` |
| **Projection** | inherited | `child_rows × 0.05` |

---

## 🌐 REST API

### `GET /`
Renders the main dashboard with the database schema loaded.

### `GET /api/schema`
Returns the full database schema as JSON.

```json
{
  "Student": [{"name": "id", "type": "INTEGER", ...}, ...],
  "Department": [...],
  ...
}
```

### `POST /api/execute`
Main query processing endpoint. Accepts a SQL string and returns the full pipeline result.

**Request:**
```json
{ "query": "SELECT Student.name, Department.name FROM Student JOIN Department ON Student.dept_id = Department.id WHERE Student.cgpa > 3.5" }
```

**Response fields:**

| Field | Description |
|---|---|
| `parsed_query` | Structured AST from the SQL parser |
| `algebra_tree` | Logical relational algebra tree (JSON) |
| `physical_plans` | All 3 physical plan trees with costs |
| `cost_analysis` | Per-plan cost breakdown (CPU, I/O, total, rank) |
| `best_plan` | Selected plan with rationale |
| `before_optimization` | Unoptimized logical tree and plans |
| `after_optimization` | Optimized logical tree and plans |
| `cost_reduction_pct` | Percentage cost improvement from optimization |
| `optimization_explanations` | Step-by-step explanation of each rewrite |
| `execution_result` | Actual query result rows (up to 100) |
| `execution_time_ms` | Real SQLite execution time in milliseconds |

### `GET /api/statistics`
Returns live database statistics.

```json
{
  "num_tables": 4,
  "total_records": 5310,
  "table_counts": {"Student": 5000, "Department": 10, ...},
  "indexed_columns": {"Student": ["id"], ...}
}
```

---

## 🧪 Supported SQL Syntax

The custom parser supports:

```sql
-- Simple SELECT
SELECT * FROM Student

-- Column list
SELECT Student.name, Department.name FROM Student

-- INNER JOIN
SELECT * FROM Student INNER JOIN Department ON Student.dept_id = Department.id

-- LEFT / RIGHT JOIN
SELECT * FROM Student LEFT JOIN Department ON Student.dept_id = Department.id

-- WHERE with single condition
SELECT * FROM Student WHERE Student.cgpa > 3.5

-- WHERE with AND / OR
SELECT Student.name FROM Student
  JOIN Department ON Student.dept_id = Department.id
  WHERE Student.cgpa >= 3.0 AND Department.id > 2

-- Multiple JOINs
SELECT Student.name, Department.name, Teacher.name
  FROM Student
  JOIN Department ON Student.dept_id = Department.id
  JOIN Teacher ON Teacher.dept_id = Department.id
  WHERE Student.cgpa > 3.5

-- With semicolon
SELECT * FROM Student WHERE cgpa = 4.0;
```

**Operators supported in WHERE:** `=`, `<`, `>`, `<=`, `>=`, `!=`, `<>`

---

## 🚀 Local Setup

### Prerequisites
- Python 3.10+
- pip

### Install & Run

```bash
# 1. Clone the repository
git clone https://github.com/muhammadmaaz77/Database-Query-Optimizer.git
cd Database-Query-Optimizer

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the development server
python app.py
```

The app will be available at **http://127.0.0.1:5000**

> The database is created and seeded automatically on first startup. No additional configuration is needed.

---

## ☁️ Deployment on Render

This project is configured for one-click deployment on [Render](https://render.com).

### Configuration Files

| File | Contents |
|---|---|
| [`Procfile`](Procfile) | `web: gunicorn app:app` |
| [`requirements.txt`](requirements.txt) | Minimal 9-package dependency list |

### Deploy Steps

1. Push the repository to GitHub
2. Create a new **Web Service** on Render
3. Connect your GitHub repository
4. Render auto-detects `Procfile` and runs `gunicorn app:app`

### Environment Variables (Optional)

| Variable | Default | Description |
|---|---|---|
| `SECRET_KEY` | `query-optimizer-simulator-secret-key` | Flask session secret |
| `FLASK_DEBUG` | `False` | Set to `true` for debug mode |

> **Note:** Render uses an ephemeral filesystem. The SQLite database is re-created and re-seeded automatically on every deploy — this is by design for a simulator application.

---

## 📁 Project Structure

```
Query Optimizer/
├── app.py                  # Flask app, routes, startup
├── parser.py               # Custom SQL tokenizer & parser
├── algebra_tree.py         # Logical plan tree (AlgebraNode)
├── optimizer.py            # Rule-based + cost-based optimizer
├── execution_plans.py      # Physical plan generator & nodes
├── cost_estimator.py       # CPU/I/O cost formulas
├── statistics_manager.py   # Table statistics & cardinality
├── database.py             # SQLite connection & schema
├── config.py               # App configuration
├── fake_data.py            # Faker-based data seeder
├── test_integration.py     # Integration test suite
├── templates/
│   └── index.html          # Main dashboard (single-page app)
├── static/
│   ├── style.css           # Dashboard styles
│   └── script.js           # Frontend logic & visualizations
├── data/
│   └── university.db       # SQLite database (auto-created)
├── Procfile                # Render deployment config
├── requirements.txt        # Python dependencies
└── README.md               # This file
```

---

## 🧰 Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Python 3, Flask 3 |
| **Database** | SQLite 3 (via Python stdlib) |
| **WSGI Server** | Gunicorn |
| **Test Data** | Faker |
| **Frontend** | HTML, Vanilla CSS, Vanilla JavaScript |
| **Deployment** | Render |

---

## 🧪 Running Tests

```bash
python -m pytest test_integration.py -v
```

---

## 📄 License

This project is developed for educational purposes as a Database Systems course project.

---

*Built with 🔬 for learning how database query optimizers work under the hood.*
