from algebra_tree import AlgebraNode
from typing import Dict, Any, List

class PhysicalPlanNode:
    """Represents a node in the physical query execution plan tree.
    
    Includes details about physical operators (e.g., Table Scan vs Index Scan,
    Nested Loop Join vs Hash Join vs Sort Merge Join, Filter, Project).
    """
    
    def __init__(self, operator_name: str, details: Dict[str, Any], cost: float, rows: int, children: List['PhysicalPlanNode'] = None):
        self.operator_name = operator_name  # e.g., "Seq Scan", "Index Scan", "Filter", "Hash Join", etc.
        self.details = details  # e.g., {"table": "Student", "index": "pk_Student_id"}
        self.cost = cost
        self.rows = rows
        self.children = children if children is not None else []
        
    def to_dict(self) -> Dict[str, Any]:
        """Serializes the physical plan to a dictionary format."""
        return {
            "operator": self.operator_name,
            "details": self.details,
            "cost": round(self.cost, 2),
            "rows": self.rows,
            "children": [child.to_dict() for child in self.children]
        }

def is_indexed_access(table_name: str, parsed_query: Dict[str, Any]) -> bool:
    """Simulates checking if an index is available for lookup on this table.
    
    Student.id, Department.id, Teacher.id, Course.id are simulated as indexed columns.
    Checks both WHERE filter clauses and JOIN ON conditions.
    """
    indexed_columns = {
        "Student": ["id"],
        "Department": ["id"],
        "Teacher": ["id"],
        "Course": ["id"]
    }
    
    allowed_cols = indexed_columns.get(table_name, [])
    if not allowed_cols:
        return False
        
    # 1. Check filter conditions (WHERE clause)
    where_conditions = parsed_query.get("where", [])
    for cond in where_conditions:
        if isinstance(cond, dict):
            field = cond.get("field", "")
            for col in allowed_cols:
                if field == col or field == f"{table_name}.{col}":
                    return True
                    
    # 2. Check JOIN ON conditions
    for join in parsed_query.get("joins", []):
        on_clause = join.get("on", "")
        if on_clause:
            # Split condition e.g. "Student.dept_id = Department.id"
            parts = [p.strip() for p in on_clause.split("=")]
            for part in parts:
                for col in allowed_cols:
                    if part == col or part == f"{table_name}.{col}":
                        return True
                        
    return False

def build_physical_node(logical_node: AlgebraNode, plan_type: str, parsed_query: Dict[str, Any]) -> PhysicalPlanNode:
    """Recursively maps a logical Relational Algebra node to a Physical Plan Node."""
    node_type = logical_node.node_type
    
    # Process children recursively
    physical_children = [build_physical_node(child, plan_type, parsed_query) for child in logical_node.children]
    
    details = {}
    operator = ""
    cost = 0.0
    rows = 0
    
    if node_type in ("Scan", "Relation"):
        table = logical_node.attributes.get("table")
        details["table"] = table
        
        # Check index availability (Plans B & C allow Index Scans on indexed attributes)
        if plan_type in ("B", "C") and is_indexed_access(table, parsed_query):
            operator = "Index Scan"
            details["index"] = f"pk_{table}_id"
        else:
            operator = "Seq Scan"
            
    elif node_type == "Selection":
        operator = "Filter"
        details["condition"] = logical_node.attributes.get("condition", "")
        
    elif node_type == "Join":
        join_type = logical_node.attributes.get("type", "INNER JOIN")
        on_clause = logical_node.attributes.get("on", "")
        details["join_type"] = join_type
        details["on"] = on_clause
        
        # Select join algorithm based on plan type
        if plan_type == "A":
            operator = "Nested Loop Join"
        elif plan_type == "B":
            operator = "Hash Join"
        elif plan_type == "C":
            operator = "Sort Merge Join"
            
    elif node_type == "Projection":
        operator = "Project"
        details["columns"] = logical_node.attributes.get("columns", [])
        
    else:
        operator = f"Physical {node_type}"
        details = logical_node.attributes
        
    return PhysicalPlanNode(operator, details, cost, rows, physical_children)

def generate_alternative_plans(logical_tree: AlgebraNode, parsed_query: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generates three alternative physical execution plans from a single logical tree."""
    plans = []
    
    # Plan A: Sequential Table Scan + Nested Loop Join
    plan_a = build_physical_node(logical_tree, "A", parsed_query)
    plans.append({
        "id": "PlanA",
        "name": "Plan A",
        "description": "Sequential Table Scan + Nested Loop Join",
        "tree": plan_a.to_dict()
    })
    
    # Plan B: Index Scan + Hash Join
    plan_b = build_physical_node(logical_tree, "B", parsed_query)
    plans.append({
        "id": "PlanB",
        "name": "Plan B",
        "description": "Index Scan (simulated) + Hash Join",
        "tree": plan_b.to_dict()
    })
    
    # Plan C: Index Scan + Sort Merge Join
    plan_c = build_physical_node(logical_tree, "C", parsed_query)
    plans.append({
        "id": "PlanC",
        "name": "Plan C",
        "description": "Index Scan (simulated) + Sort Merge Join",
        "tree": plan_c.to_dict()
    })
    
    return plans

if __name__ == "__main__":
    from algebra_tree import build_initial_tree
    
    mock_parsed = {
        "select": ["Student.name", "Department.name"],
        "from": ["Student"],
        "joins": [{"table": "Department", "type": "INNER JOIN", "on": "Student.dept_id = Department.id"}],
        "where": [{"field": "Student.id", "op": "=", "value": "45"}]
    }
    
    tree = build_initial_tree(mock_parsed)
    plans = generate_alternative_plans(tree, mock_parsed)
    
    import json
    print("Alternative Physical Plans:")
    print(json.dumps(plans, indent=2))
