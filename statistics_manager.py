from database import get_db_connection

class DBStatistics:
    """Statistics collector for the university database.
    
    Collects total rows per table dynamically from SQLite, keeps track of indexed
    columns, and provides estimates for selectivity and join cardinality.
    """
    
    def __init__(self):
        self.table_counts = {}
        self.indexed_columns = {
            "Student": ["id"],
            "Department": ["id"],
            "Teacher": ["id"],
            "Course": ["id"]
        }
        self.refresh()
        
    def refresh(self):
        """Fetches total rows from SQLite tables dynamically."""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            tables = ["Student", "Department", "Teacher", "Course"]
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                self.table_counts[table] = cursor.fetchone()[0]
            conn.close()
        except Exception as e:
            # Fallback mock statistics if database doesn't exist yet
            self.table_counts = {
                "Student": 5000,
                "Department": 10,
                "Teacher": 100,
                "Course": 200
            }
            
    def get_table_rows(self, table_name: str) -> int:
        """Returns the total number of rows in a table."""
        return self.table_counts.get(table_name, 1000)
        
    def is_column_indexed(self, table_name: str, column_name: str) -> bool:
        """Checks if a column has a simulated index."""
        return column_name in self.indexed_columns.get(table_name, [])
        
    def estimate_selectivity(self, condition: str, parent_rows: int) -> float:
        """Estimates selectivity of a WHERE clause condition."""
        if not condition:
            return 1.0
            
        cond_upper = condition.upper()
        if " AND " in cond_upper:
            parts = condition.split(" AND ")
            sel = 1.0
            for part in parts:
                sel *= self.estimate_selectivity(part.strip(), parent_rows)
            return sel
        elif " OR " in cond_upper:
            parts = condition.split(" OR ")
            sel1 = self.estimate_selectivity(parts[0].strip(), parent_rows)
            sel2 = self.estimate_selectivity(parts[1].strip(), parent_rows)
            return sel1 + sel2 - (sel1 * sel2)
            
        # Comparison logic
        if "=" in condition:
            if "id" in condition.lower():
                return 1.0 / parent_rows if parent_rows > 0 else 0.01
            return 0.05  # 5% for other equality columns
        elif ">" in condition or "<" in condition:
            return 0.20  # 20% for inequalities
            
        return 0.20

    def estimate_join_cardinality(self, left_rows: int, right_rows: int, on_clause: str) -> int:
        """Estimates output rows of a join based on key/foreign-key relationships."""
        # Standard primary key-foreign key join assumes output cardinality matches referencing table (larger)
        return max(left_rows, right_rows)
