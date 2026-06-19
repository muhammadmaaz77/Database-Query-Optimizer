# 🎓 ADBMS Query Optimizer Simulator - Comprehensive User Guide

Welcome to the **Query Optimizer Simulator** educational manual. This guide is designed to help students, database administrators, and software engineers understand the internal mechanisms of modern relational database management system (RDBMS) query compilers and optimizers.

---

## 📖 1. What is this Project?

The **Query Optimizer Simulator** is an interactive, university-level educational tool built to simulate the multi-phase query compilation, logical rewriting, cost estimation, and physical planning processes executed inside relational database engines (such as PostgreSQL, SQLite, or MySQL).

It connects a live **SQLite database** (containing 5,000+ seeded university records) with an educational compiler pipeline, allowing users to write custom SQL queries and visualize how the system optimizes and executes them in real time.

---

## 🧩 2. Core Concepts & Terminology

### 🔍 SQL Parser & AST (Abstract Syntax Tree)
Before a database can execute a SQL query, it must parse the text to understand its structure.
* **Parsing**: The lexical analyzer breaks the SQL text into tokens (keywords, identifiers, literals), and the parser builds a syntax tree.
* **AST (Abstract Syntax Tree)**: A nested structural object that breaks down the query components:
  * **Selected Columns**: The attributes requested in the `SELECT` clause.
  * **Base Table**: The source relation in the `FROM` clause.
  * **Joins**: The list of target tables and their matching conditions (`JOIN ... ON ...`).
  * **Filters**: Conditional predicates in the `WHERE` clause (grouped by `AND` / `OR` logic).

```json
/* Example Parsed AST representation */
{
  "select": ["Student.name", "Department.name"],
  "from": "Student",
  "joins": [
    {
      "table": "Department",
      "on": ["Student.dept_id", "Department.id"],
      "type": "INNER"
    }
  ],
  "where": {
    "op": "AND",
    "conditions": [
      ["Student.cgpa", ">", 3.7]
    ]
  }
}
```

---

### 🌿 Relational Algebra & Logical Trees
Once the AST is verified against the database schema, it is translated into a **Logical Query Plan** modeled as a tree of relational algebra operators.
* **Projection ($\pi$)**: Retains only specified columns, discarding the rest to minimize tuple width in memory.
* **Selection ($\sigma$)**: Filters out rows that do not satisfy a predicate, reducing tuple cardinality.
* **Join ($\bowtie$)**: Pairs matching records from two relations based on join conditions.
* **Scan / Relation ($R$)**: Reads the data records directly from base database tables.

```
Logical Plan Tree:
     [Projection] (Student.name, Department.name)
          |
      [Selection] (Student.cgpa > 3.7)
          |
        [Join] (Student.dept_id = Department.id)
       /      \
  [Scan]      [Scan] (Department)
 (Student)
```

---

### ⚙️ Heuristic Heuristic (Logical Rules)
A logical optimizer rewrites the tree structure to minimize intermediate data volumes before any physical execution begins. The simulator showcases two critical logical rewrites:

1. **Selection Pushdown ($\sigma$-Pushdown)**:
   * *Concept*: Moves filters down the tree, closer to the physical table scans.
   * *Rationale*: Applying filters before joins reduces the number of records fed into the join operator, preventing expensive Cartesian products.
2. **Projection Pushdown ($\pi$-Pushdown)**:
   * *Concept*: Restricts the columns retrieved from base tables to only those referenced in joins, selections, or final projections.
   * *Rationale*: Pruning unused fields early reduces disk I/O and memory buffer footprint.

---

### 🚀 Physical Execution Plans
A logical tree defines *what* data to fetch, but a **Physical Plan** defines *how* to execute it. The simulator generates three alternative physical execution plan archetypes:

#### 📊 Plan A: Sequential Scan + Nested Loop Join
* **Access Path**: **Sequential Scan (Seq Scan)** reads the entire table from beginning to end ($O(N)$ complexity).
* **Join Algorithm**: **Nested Loop Join** compares every outer table row against every inner table row.
* *Characteristics*: High time complexity $O(M \times N)$; highly inefficient for large tables.

#### 🧮 Plan B: Index Scan + Hash Join
* **Access Path**: **Index Scan** uses a B-Tree or Hash index on primary keys to jump directly to target rows ($O(\log N)$ complexity).
* **Join Algorithm**: **Hash Join** builds an in-memory hash table on the smaller table and probes it with rows from the larger table.
* *Characteristics*: High memory overhead but very fast linear time complexity $O(M + N)$.

#### 🔀 Plan C: Index Scan + Sort Merge Join
* **Access Path**: **Index Scan** (simulated index lookup).
* **Join Algorithm**: **Sort Merge Join** sorts both relations by their join keys, then merges the matches in a single parallel pass.
* *Characteristics*: High CPU cost to sort, but highly efficient $O(M \log M + N \log N)$ complexity, particularly if inputs are already sorted by indexes.

---

### 🧮 3. Cost Estimation Engine Formulas
The **Cost-Based Optimizer (CBO)** calculates estimated execution costs for each candidate plan using the following simplified mathematical models:

* **Sequential Scan Cost**:
  $$\text{Cost} = N_{\text{rows}} + (N_{\text{rows}} \times 0.01)$$
* **Index Scan Cost**:
  $$\text{Cost} = \log_2(N_{\text{rows}}) + (\log_2(N_{\text{rows}}) \times 0.1)$$
  *(Falls back to Sequential Scan if no index exists on the filter attribute)*.
* **Nested Loop Join Cost**:
  $$\text{Cost} = L_{\text{io}} + (L_{\text{rows}} \times R_{\text{io}})$$
* **Hash Join Cost**:
  $$\text{Cost} = (L_{\text{io}} + R_{\text{io}}) \times 1.2 + (L_{\text{rows}} + R_{\text{rows}}) \times 1.5$$
* **Sort Merge Join Cost**:
  $$\text{Cost} = L_{\text{io}} + R_{\text{io}} + (L_{\text{rows}} \log_2 L_{\text{rows}} + R_{\text{rows}} \log_2 R_{\text{rows}}) \times 2.0$$

---

## 🕹️ 4. How to Use the Simulator

### Step 1: Browse the Schema Explorer (Left Sidebar)
* The left panel displays all the tables in the database (`Student`, `Department`, `Teacher`, `Course`) and their attributes (types and primary key markers).
* **Clicking** any column name automatically inserts it into the SQL Query Editor at your cursor position.

### Step 2: Write your SQL Query
* Input your query in the **SQL Query Editor**.
* You can write standard `SELECT` queries with filters (`WHERE`), logical operators (`AND` / `OR`), and table joins (`JOIN ... ON`).
* Or click any of the **Quick Templates** to load a pre-configured educational query.

### Step 3: Run the Optimizer
* Click **Execute & Optimize** (or press `Ctrl` + `Enter`).
* The simulation engine parses and optimizes the query, executes it on the live SQLite database, and populates the dashboard tabs.

### Step 4: Analyze the Results Tabs
1. **Results Grid**: View the actual records returned from the database (capped at 100 rows for performance).
2. **Optimizer Comparison**: Compare the unoptimized logical plan against the optimized logical plan. Displays the percentage of estimated database I/O cost saved.
3. **Physical Plans**: Inspect the visual diagram of the three physical plan alternatives. Green connectors show marching animations representing data flow from table scans upwards.
4. **Algebra Tree**: View the ASCII formatting of the initial and optimized logical query plans.
5. **Parsed AST**: View the raw JSON parsing details of the query structure.
6. **Session History**: Easily re-load previously run queries.
7. **DB Stats**: View active record counts and statistics for each table.

---

## 🎓 5. Walkthrough Example

### Input SQL:
```sql
SELECT Student.name, Department.name
FROM Student
JOIN Department ON Student.dept_id = Department.id
WHERE Student.cgpa > 3.8;
```

### 1. Parsing (AST Generation)
The system parses the query and discovers that it targets `Student` as the base table, joins with `Department`, and applies a filter predicate (`Student.cgpa > 3.8`).

### 2. Heuristic Optimization
The optimizer rewrites the logical tree using **Selection Pushdown**:
* **Initial Plan**: Scan both tables $\rightarrow$ Join them $\rightarrow$ Filter the results where `cgpa > 3.8`.
* **Optimized Plan**: Filter `Student` table immediately to keep only students with `cgpa > 3.8` $\rightarrow$ Join only those matching students with the `Department` table.
* **Benefit**: The optimizer saves **~69%** of execution cost by discarding non-matching student records *before* executing the join.

### 3. Physical Plan Costing
The Cost Estimation Engine calculates costs:
* **Plan A (Nested Loop)**: Cost = $5,300$
* **Plan B (Hash Join)**: Cost = $8,856$
* **Plan C (Sort Merge)**: Cost = $13,105$
* The simulator picks **Plan A** or **Plan B** depending on card estimates, highlights the selection rationale, and renders glowing data-flow laser lines in the **Physical Plans** tab.
