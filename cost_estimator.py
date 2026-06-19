from database import get_db_connection
from algebra_tree import AlgebraNode
from execution_plans import PhysicalPlanNode
from statistics_manager import DBStatistics
from typing import Dict, Tuple, List, Any
import math

class CostEstimator:
    """Estimates the processing cost and output size of query plans.
    
    Implements CPU & I/O breakdown formulas for Sequential Scan, Index Scan,
    Nested Loop Join, Hash Join, and Sort Merge Join.
    """
    
    def __init__(self):
        self.stats = DBStatistics()
        
    def refresh_stats(self):
        """Refreshes table counts from the database."""
        self.stats.refresh()

    def estimate_cost(self, node: AlgebraNode) -> Tuple[float, int]:
        """Backward compatible cost estimator for Logical Relational Algebra nodes.
        
        Returns:
            Tuple[float, int]: (Total Estimated Cost, Output Row Count)
        """
        node_type = node.node_type
        
        if node_type in ("Scan", "Relation"):
            table_name = node.attributes.get("table")
            row_count = self.stats.get_table_rows(table_name)
            cost = float(row_count)
            return cost, row_count
            
        elif node_type == "Selection":
            if not node.children:
                return 0.0, 0
            child_cost, child_rows = self.estimate_cost(node.children[0])
            selectivity = 0.2
            cpu_cost = child_rows * 0.1
            total_cost = child_cost + cpu_cost
            output_rows = max(1, int(child_rows * selectivity))
            return total_cost, output_rows
            
        elif node_type == "Join":
            if len(node.children) < 2:
                return 0.0, 0
            left_cost, left_rows = self.estimate_cost(node.children[0])
            right_cost, right_rows = self.estimate_cost(node.children[1])
            join_cost = left_rows * right_rows * 0.5
            total_cost = left_cost + right_cost + join_cost
            output_rows = max(left_rows, right_rows)
            return total_cost, output_rows
            
        elif node_type == "Projection":
            if not node.children:
                return 0.0, 0
            child_cost, child_rows = self.estimate_cost(node.children[0])
            projection_cost = child_rows * 0.05
            return child_cost + projection_cost, child_rows
            
        return 0.0, 0

    def calculate_and_populate_tree(self, node: PhysicalPlanNode) -> Tuple[float, float, float, int]:
        """Recursively estimates CPU, I/O, total cost, and row count for every physical node,
        populating attributes directly on the tree nodes (bottom-up).
        
        Returns:
            Tuple[float, float, float, int]: (CPU Cost, I/O Cost, Total Cost, Output Rows)
        """
        op = node.operator_name
        children = node.children
        
        # 1. Process children recursively (bottom-up traversal)
        child_stats = [self.calculate_and_populate_tree(child) for child in children]
        
        # 2. Compute cost based on the physical operator
        cpu_cost = 0.0
        io_cost = 0.0
        total_cost = 0.0
        output_rows = 0
        
        if op == "Seq Scan":
            table_name = node.details.get("table")
            row_count = self.stats.get_table_rows(table_name)
            
            # Cost = Number of rows in table
            io_cost = float(row_count)
            cpu_cost = row_count * 0.01  # very small CPU cost
            total_cost = io_cost + cpu_cost
            output_rows = row_count
            
        elif op == "Index Scan":
            table_name = node.details.get("table")
            row_count = self.stats.get_table_rows(table_name)
            
            # Cost = log2(Number of rows)
            log_rows = math.log2(row_count) if row_count > 1 else 1.0
            
            io_cost = log_rows
            cpu_cost = log_rows * 0.1
            total_cost = io_cost + cpu_cost
            output_rows = 1  # Simulated single-record lookup (indexed lookup)
            
        elif op == "Filter":
            if child_stats:
                child_cpu, child_io, child_total, child_rows = child_stats[0]
                condition = node.details.get("condition", "")
                
                # Estimate selectivity
                selectivity = self.stats.estimate_selectivity(condition, child_rows)
                
                io_cost = child_io
                cpu_cost = child_cpu + (child_rows * 0.1)  # CPU cost to evaluate filter condition
                total_cost = io_cost + cpu_cost
                output_rows = max(1, int(child_rows * selectivity))
                
        elif op == "Nested Loop Join":
            if len(child_stats) >= 2:
                l_cpu, l_io, l_total, l_rows = child_stats[0]
                r_cpu, r_io, r_total, r_rows = child_stats[1]
                
                # Cost = rows(left) x rows(right)
                io_cost = l_io + (l_rows * r_io)  # outer loop scans inner child
                cpu_cost = l_cpu + r_cpu + (l_rows * r_rows * 0.05)
                total_cost = io_cost + cpu_cost
                output_rows = self.stats.estimate_join_cardinality(l_rows, r_rows, node.details.get("on", ""))
                
        elif op == "Hash Join":
            if len(child_stats) >= 2:
                l_cpu, l_io, l_total, l_rows = child_stats[0]
                r_cpu, r_io, r_total, r_rows = child_stats[1]
                
                # Cost = rows(left) + rows(right)
                io_cost = l_io + r_io
                cpu_cost = l_cpu + r_cpu + (l_rows + r_rows) * 1.5  # Build and probe hash table
                total_cost = io_cost + cpu_cost
                output_rows = self.stats.estimate_join_cardinality(l_rows, r_rows, node.details.get("on", ""))
                
        elif op == "Sort Merge Join":
            if len(child_stats) >= 2:
                l_cpu, l_io, l_total, l_rows = child_stats[0]
                r_cpu, r_io, r_total, r_rows = child_stats[1]
                
                # Cost = sort(left) + sort(right) + merge_cost
                log_l = math.log2(l_rows) if l_rows > 1 else 1.0
                log_r = math.log2(r_rows) if r_rows > 1 else 1.0
                sort_l = l_rows * log_l * 0.2
                sort_r = r_rows * log_r * 0.2
                merge_cost = (l_rows + r_rows) * 0.1
                
                io_cost = l_io + r_io
                cpu_cost = l_cpu + r_cpu + sort_l + sort_r + merge_cost
                total_cost = io_cost + cpu_cost
                output_rows = self.stats.estimate_join_cardinality(l_rows, r_rows, node.details.get("on", ""))
                
        elif op == "Project":
            if child_stats:
                child_cpu, child_io, child_total, child_rows = child_stats[0]
                
                # Apply a very small projection cost
                io_cost = child_io
                cpu_cost = child_cpu + (child_rows * 0.05)
                total_cost = io_cost + cpu_cost
                output_rows = child_rows
                
        # Write values back to physical node attributes
        node.cost = round(total_cost, 2)
        node.rows = output_rows
        node.details["cpu_cost"] = round(cpu_cost, 2)
        node.details["io_cost"] = round(io_cost, 2)
        
        return cpu_cost, io_cost, total_cost, output_rows

if __name__ == "__main__":
    from algebra_tree import build_initial_tree
    
    mock_parsed = {
        "select": ["Student.name"],
        "from": ["Student"],
        "joins": [],
        "where": [{"field": "Student.cgpa", "op": ">", "value": "3.5"}]
    }
    tree = build_initial_tree(mock_parsed)
    estimator = CostEstimator()
    cost, rows = estimator.estimate_cost(tree)
    print(f"Logical Total Cost: {cost}, Rows: {rows}")
