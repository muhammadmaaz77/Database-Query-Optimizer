import unittest
import json
import time
from app import app
from database import get_schema
from parser import SQLParser, validate_schema
from algebra_tree import build_initial_tree
from optimizer import QueryOptimizer
from cost_estimator import CostEstimator

class QueryOptimizerIntegrationTests(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        cls.client = app.test_client()
        cls.schema = get_schema()
        
    def test_01_schema_retrieval(self):
        """Test database statistics & schema loading."""
        print("\n--- TEST: Schema Retrieval ---")
        response = self.client.get('/api/statistics')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode('utf-8'))
        
        self.assertTrue(data.get("success"))
        self.assertEqual(data.get("num_tables"), 4)
        self.assertIn("Student", data.get("table_counts"))
        self.assertIn("Department", data.get("table_counts"))
        self.assertIn("Teacher", data.get("table_counts"))
        self.assertIn("Course", data.get("table_counts"))
        print("Total Seeded Records:", data.get("total_records"))
        print("Table Row Counts:", data.get("table_counts"))
        
    def test_02_components_unit_workflow(self):
        """Test modular workflow: Parser -> Tree -> Optimizer -> Estimator."""
        print("\n--- TEST: Unit Modules Workflow ---")
        query = "SELECT Student.name, Department.name FROM Student JOIN Department ON Student.dept_id = Department.id WHERE Student.cgpa > 3.7"
        
        # 1. Parse
        parser = SQLParser()
        parsed_q = parser.parse(query)
        self.assertEqual(parsed_q["base_table"], "Student")
        self.assertEqual(len(parsed_q["joins"]), 1)
        
        # 2. Schema Validation
        validate_schema(parsed_q, self.schema)
        
        # 3. Algebra Tree
        tree = build_initial_tree(parsed_q)
        self.assertEqual(tree.node_type, "Projection")
        
        # 4. Optimize
        optimizer = QueryOptimizer()
        opt_tree, summary = optimizer.optimize(tree, parsed_q)
        self.assertIsNotNone(opt_tree)
        self.assertTrue(summary["cost_reduction_pct"] > 0)
        
        # 5. Cost Estimator
        estimator = CostEstimator()
        cost, rows = estimator.estimate_cost(opt_tree)
        self.assertTrue(cost > 0)
        self.assertTrue(rows > 0)
        print("Integration components verified successfully.")

    def test_03_twenty_demonstration_queries(self):
        """Test Phase 3: Execute 20 diverse query patterns and check optimization."""
        print("\n--- TEST: 20 Demonstration SQL Queries ---")
        queries = [
            # 1. Simple SELECT
            "SELECT name FROM Student;",
            # 2. WHERE filter (non-indexed)
            "SELECT name, cgpa FROM Student WHERE cgpa > 3.5;",
            # 3. JOIN with indexed lookup
            "SELECT Student.name, Department.name FROM Student JOIN Department ON Student.dept_id = Department.id;",
            # 4. JOIN + WHERE filter (Selection Pushdown demonstration)
            "SELECT Student.name, Department.name FROM Student JOIN Department ON Student.dept_id = Department.id WHERE Student.cgpa > 3.8;",
            # 5. Multiple JOIN (Join Reordering demonstration)
            "SELECT Student.name, Department.name, Teacher.name FROM Student JOIN Department ON Student.dept_id = Department.id JOIN Teacher ON Teacher.dept_id = Department.id;",
            # 6. Multiple JOIN with complex filters
            "SELECT Student.name, Department.name, Teacher.name FROM Student JOIN Department ON Student.dept_id = Department.id JOIN Teacher ON Teacher.dept_id = Department.id WHERE Student.cgpa > 3.9 AND Department.id > 5;",
            # 7. Indexed lookup on primary key
            "SELECT Student.name FROM Student WHERE Student.id = 50;",
            # 8. Range filter on indexed column
            "SELECT Department.name FROM Department WHERE Department.id > 3;",
            # 9. JOIN between Course and Teacher
            "SELECT Course.name, Teacher.name FROM Course JOIN Teacher ON Course.teacher_id = Teacher.id;",
            # 10. Projection wildcard *
            "SELECT * FROM Student;",
            # 11. WHERE filter with OR condition
            "SELECT name, cgpa FROM Student WHERE cgpa < 2.5 OR cgpa > 3.8;",
            # 12. WHERE clause with qualified columns and AND
            "SELECT Student.name, Department.name FROM Student JOIN Department ON Student.dept_id = Department.id WHERE Student.cgpa > 3.5 AND Student.dept_id > 2;",
            # 13. String literal filter
            "SELECT Student.name, Department.name FROM Student JOIN Department ON Student.dept_id = Department.id WHERE Student.name = 'Alice';",
            # 14. Indexed lookup on Teacher
            "SELECT Teacher.name FROM Teacher WHERE Teacher.id = 10;",
            # 15. Indexed lookup on Course
            "SELECT Course.name FROM Course WHERE Course.id = 5;",
            # 16. Double indexed join
            "SELECT Student.name, Department.name FROM Student JOIN Department ON Student.dept_id = Department.id WHERE Student.id = 100 AND Department.id = 5;",
            # 17. Non-indexed filter on Teacher, indexed on Department
            "SELECT Teacher.name, Department.name FROM Teacher JOIN Department ON Teacher.dept_id = Department.id WHERE Teacher.dept_id = 1;",
            # 18. Complex OR filter
            "SELECT Student.name, Department.name FROM Student JOIN Department ON Student.dept_id = Department.id WHERE Student.cgpa > 3.0 OR Department.id = 2;",
            # 19. Four table join
            "SELECT Student.name, Department.name, Teacher.name, Course.name FROM Student JOIN Department ON Student.dept_id = Department.id JOIN Teacher ON Teacher.dept_id = Department.id JOIN Course ON Course.teacher_id = Teacher.id WHERE Student.cgpa > 3.5;",
            # 20. Projection Pushdown demonstration (Requesting single column with indexed filter)
            "SELECT Student.cgpa FROM Student WHERE Student.id = 250;"
        ]
        
        for idx, q in enumerate(queries, 1):
            start = time.perf_counter()
            response = self.client.post('/api/execute', 
                                        data=json.dumps({"query": q}),
                                        content_type='application/json')
            elapsed = (time.perf_counter() - start) * 1000
            
            self.assertEqual(response.status_code, 200, f"Query {idx} failed: {q}")
            data = json.loads(response.data.decode('utf-8'))
            self.assertTrue(data.get("success"), f"Query {idx} execution flag was false: {data.get('error')}")
            
            # Verify cost-based planner and explanation outcomes
            best_plan = data.get("best_plan", {})
            self.assertIn("name", best_plan)
            self.assertIn("total_cost", best_plan)
            self.assertIn("cost_reduction_pct", data)
            self.assertTrue(len(data.get("optimization_explanations", [])) > 0)
            
            print(f"Query {idx:02d} verified in {elapsed:6.2f} ms | Best Plan: {best_plan['name']:12s} | Cost: {best_plan['total_cost']:8.2f} | Reduction: {data['cost_reduction_pct']}%")

    def test_04_robust_error_handling(self):
        """Test Phase 4: Invalid queries yield meaningful educational errors."""
        print("\n--- TEST: Robust Error Handling ---")
        invalid_cases = [
            # 1. Empty query
            ("", "Query cannot be empty."),
            # 2. Missing FROM
            ("SELECT Student.name", "SQL Syntax Error: Missing FROM clause."),
            # 3. Invalid JOIN
            ("SELECT Student.name FROM Student JOIN Department", "SQL Syntax Error: Expected ON keyword after table"),
            # 4. Invalid WHERE
            ("SELECT Student.name FROM Student WHERE", "SQL Syntax Error: Expected condition in WHERE clause"),
            # 5. Unknown table
            ("SELECT Student.name FROM NonexistentTable WHERE id = 1", "SQL Schema Error: Unknown table 'NonexistentTable'"),
            # 6. Unknown column
            ("SELECT Student.nonexistent_column FROM Student", "SQL Schema Error: Column 'nonexistent_column' does not exist in table 'Student'"),
            # 7. Malformed SQL
            ("SELECT Student.name FROM Student WHERE Student.cgpa > ;", "SQL Syntax Error: Expected number, string, or column name")
        ]
        
        for idx, (q, expected_err) in enumerate(invalid_cases, 1):
            response = self.client.post('/api/execute',
                                        data=json.dumps({"query": q}),
                                        content_type='application/json')
            
            data = json.loads(response.data.decode('utf-8'))
            self.assertFalse(data.get("success"), f"Invalid query {idx} was incorrectly marked successful: {q}")
            
            err_msg = data.get("error", "") or data.get("errors", "")
            self.assertIn(expected_err.lower(), err_msg.lower(), f"Unexpected error message: '{err_msg}' (Expected: '{expected_err}')")
            print(f"Error Case {idx}: Detected expected error -> \"{err_msg}\"")

if __name__ == "__main__":
    unittest.main()
