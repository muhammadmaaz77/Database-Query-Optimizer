from typing import List, Optional, Dict, Any

class AlgebraNode:
    """Represents a node in the Relational Algebra logical plan tree."""
    
    def __init__(self, node_type: str, attributes: Dict[str, Any], children: Optional[List['AlgebraNode']] = None):
        self.node_type = node_type  # "Projection", "Selection", "Join", "Relation"
        self.attributes = attributes  # e.g., {"columns": [...]}, {"condition": "cgpa > 3.5"}, {"on": "dept_id = id"}
        self.children = children if children is not None else []
        
    def to_dict(self) -> Dict[str, Any]:
        """Serializes the relational algebra tree to a dictionary format (useful for JSON visualization)."""
        return {
            "node_type": self.node_type,
            "attributes": self.attributes,
            "children": [child.to_dict() for child in self.children]
        }
        
    def print_tree(self, level: int = 0) -> str:
        """Generates a text-based tree representation."""
        indent = "  " * level
        node_str = f"{indent}└── [{self.node_type}]"
        
        if self.node_type == "Projection":
            node_str += f" columns: {', '.join(self.attributes.get('columns', []))}"
        elif self.node_type == "Selection":
            node_str += f" condition: {self.attributes.get('condition', '')}"
        elif self.node_type == "Join":
            node_str += f" type: {self.attributes.get('type', 'INNER')}, on: {self.attributes.get('on', '')}"
        elif self.node_type in ("Relation", "Scan"):
            node_str += f" table: {self.attributes.get('table', '')}"
            
        lines = [node_str]
        for child in self.children:
            lines.append(child.print_tree(level + 1))
        return "\n".join(lines)

def build_initial_tree(parsed_query: Dict[str, Any]) -> AlgebraNode:
    """Builds a logical relational algebra tree from a parsed query dictionary.
    
    Order of operations:
    1. Relation nodes for base tables.
    2. Join nodes for joins (INNER, LEFT, RIGHT, CROSS).
    3. Selection node for WHERE conditions.
    4. Projection node for SELECT columns.
    """
    # 1. Start with Relation for the base table
    tables = parsed_query.get("from", [])
    if not tables:
        raise ValueError("No table specified in FROM clause")
        
    base_table = tables[0]
    current_node = AlgebraNode("Relation", {"table": base_table})
    
    # 2. Add Join Nodes
    for join in parsed_query.get("joins", []):
        join_table = join["table"]
        on_cond = join["on"]
        join_type = join.get("type", "INNER JOIN")
        right_child = AlgebraNode("Relation", {"table": join_table})
        current_node = AlgebraNode("Join", {"type": join_type, "on": on_cond}, [current_node, right_child])
        
    # If there are additional tables in FROM (cross product fallback)
    for tbl in tables[1:]:
        right_child = AlgebraNode("Relation", {"table": tbl})
        current_node = AlgebraNode("Join", {"type": "CROSS JOIN", "on": "None"}, [current_node, right_child])
        
    # 3. Add Selection Node (WHERE clause)
    where_conditions = parsed_query.get("where", [])
    if where_conditions:
        # Construct the Selection condition string dynamically from structured/raw elements
        parts = []
        for cond in where_conditions:
            if isinstance(cond, dict):
                parts.append(f"{cond['field']} {cond['op']} {cond['value']}")
            else:
                parts.append(str(cond))
        condition_str = " ".join(parts)
        current_node = AlgebraNode("Selection", {"condition": condition_str}, [current_node])
        
    # 4. Add Projection Node (SELECT clause)
    select_columns = parsed_query.get("select", [])
    if select_columns:
        current_node = AlgebraNode("Projection", {"columns": select_columns}, [current_node])
        
    return current_node

if __name__ == "__main__":
    mock_parsed = {
        "select": ["Student.name", "Department.name"],
        "from": ["Student"],
        "joins": [{"table": "Department", "type": "INNER JOIN", "on": "Student.dept_id = Department.id"}],
        "where": [{"field": "Student.cgpa", "op": ">", "value": "3.5"}, "AND", {"field": "Department.id", "op": ">", "value": "2"}]
    }
    
    tree = build_initial_tree(mock_parsed)
    print("Logical Relational Algebra Tree:")
    print(tree.print_tree())
