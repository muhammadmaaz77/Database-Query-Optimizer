from algebra_tree import AlgebraNode, build_initial_tree
from execution_plans import generate_alternative_plans, PhysicalPlanNode
from cost_estimator import CostEstimator
from typing import Dict, Any, Tuple, List
import copy

class QueryOptimizer:
    """Logical & Physical Query Optimizer with Rule-Based & Cost-Based Optimization."""
    
    def __init__(self):
        self.estimator = CostEstimator()
        
    def optimize(self, logical_tree: AlgebraNode, parsed_query: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Performs full query optimization.
        
        1. Evaluates the unoptimized plan costs.
        2. Applies Logical Optimization Rules (Join Reordering, Selection Pushdown, Projection Pushdown).
        3. Generates and costs the optimized physical plans.
        4. Selects the best plan, generates explanations, and calculates cost reduction.
        
        Returns:
            Tuple: (optimized_logical_tree, result_summary_dict)
        """
        self.estimator.refresh_stats()
        explanations = []
        
        # --- BEFORE OPTIMIZATION ---
        # Make copies of the initial state
        initial_parsed = copy.deepcopy(parsed_query)
        initial_logical_tree = build_initial_tree(initial_parsed)
        initial_logical_dict = initial_logical_tree.to_dict()
        
        # Generate and cost initial physical plans
        initial_raw_plans = generate_alternative_plans(initial_logical_tree, initial_parsed)
        initial_physical_plans = []
        for p in initial_raw_plans:
            node_root = self._dict_to_physical_node(p["tree"])
            self.estimator.calculate_and_populate_tree(node_root)
            p["tree"] = node_root.to_dict()
            initial_physical_plans.append(p)
            
        # Get cheapest initial plan
        initial_plans_cost = [self._get_root_cost(self._dict_to_physical_node(p["tree"])) for p in initial_physical_plans]
        min_initial_cost = min(initial_plans_cost) if initial_plans_cost else 0.0
        
        best_initial_idx = initial_plans_cost.index(min_initial_cost) if initial_plans_cost else 0
        best_initial_plan = initial_physical_plans[best_initial_idx]
        
        # --- LOGICAL OPTIMIZATION RULES (AFTER) ---
        # Rule 1: Join Reordering
        reordered_parsed, join_expl = self._apply_join_reordering(initial_parsed)
        explanations.extend(join_expl)
        
        # Build logical tree from reordered query
        logical_tree_step2 = build_initial_tree(reordered_parsed)
        
        # Rule 2: Selection Pushdown
        logical_tree_step3, select_expl = self._push_down_selections(logical_tree_step2)
        explanations.extend(select_expl)
        
        # Rule 3: Projection Pushdown
        optimized_logical_tree, project_expl = self._apply_projection_pushdown(
            logical_tree_step3, 
            reordered_parsed.get("select", []),
            reordered_parsed.get("where", []),
            reordered_parsed.get("joins", [])
        )
        explanations.extend(project_expl)
        
        # --- AFTER OPTIMIZATION PLAN COSTING ---
        optimized_logical_dict = optimized_logical_tree.to_dict()
        optimized_raw_plans = generate_alternative_plans(optimized_logical_tree, reordered_parsed)
        
        optimized_physical_plans = []
        cost_analysis = []
        
        for p in optimized_raw_plans:
            node_root = self._dict_to_physical_node(p["tree"])
            cpu, io, total, rows = self.estimator.calculate_and_populate_tree(node_root)
            p["tree"] = node_root.to_dict()
            optimized_physical_plans.append(p)
            
            scan_type = self._get_scan_type(node_root)
            join_type = self._get_join_type(node_root)
            
            cost_analysis.append({
                "plan_id": p["id"],
                "name": p["name"],
                "scan_type": scan_type,
                "join_type": join_type,
                "cpu_cost": round(cpu, 2),
                "io_cost": round(io, 2),
                "total_cost": round(total, 2),
                "estimated_rows": rows,
                "rank": 999
            })
            
        # Rank optimized plans
        sorted_analysis = sorted(cost_analysis, key=lambda x: x["total_cost"])
        for rank, entry in enumerate(sorted_analysis, 1):
            entry["rank"] = rank
            
        for entry in cost_analysis:
            for s_entry in sorted_analysis:
                if entry["plan_id"] == s_entry["plan_id"]:
                    entry["rank"] = s_entry["rank"]
                    
        # Select best optimized plan
        best_opt_entry = sorted_analysis[0]
        best_opt_p = next(p for p in optimized_physical_plans if p["id"] == best_opt_entry["plan_id"])
        
        # Generate explanations about physical selection
        if best_opt_entry["join_type"] != "N/A":
            explanations.append(f"Physical operator choice: selected {best_opt_entry['name']} because {best_opt_entry['join_type']} is cheaper than Nested Loop Join.")
        if "Index Scan" in best_opt_entry["scan_type"]:
            explanations.append(f"Physical operator choice: selected Index Scan for primary key index lookup on table(s).")
            
        # Calculate cost reduction
        min_opt_cost = best_opt_entry["total_cost"]
        cost_reduction = min_initial_cost - min_opt_cost
        cost_reduction_pct = round((cost_reduction / min_initial_cost) * 100, 2) if min_initial_cost > 0 else 0.0
        if cost_reduction_pct < 0:
            cost_reduction_pct = 0.0
            
        explanations.append(f"Optimization completed. Total estimated plan cost reduced from {min_initial_cost} to {min_opt_cost} ({cost_reduction_pct}% reduction).")
        
        # Generate best plan rationale
        if best_opt_entry["join_type"] != "N/A":
            why_selected = (
                f"Selected because it has the lowest total estimated cost ({best_opt_entry['total_cost']}). "
                f"It utilizes an efficient {best_opt_entry['join_type']} join operator and {best_opt_entry['scan_type']} access paths, "
                f"benefiting from selections pushed down to base relations."
            )
        else:
            why_selected = (
                f"Selected because it has the lowest total estimated cost ({best_opt_entry['total_cost']}). "
                f"It utilizes {best_opt_entry['scan_type']} access paths."
            )
            
        best_plan = {
            "id": best_opt_p["id"],
            "name": best_opt_p["name"],
            "description": best_opt_p["description"],
            "total_cost": best_opt_entry["total_cost"],
            "join_algorithm": best_opt_entry["join_type"],
            "scan_strategy": best_opt_entry["scan_type"],
            "why_selected": why_selected,
            "tree": best_opt_p["tree"]
        }
        
        # Package comparison payload
        result_summary = {
            "physical_plans": optimized_physical_plans,
            "cost_analysis": cost_analysis,
            "best_plan": best_plan,
            "before_optimization": {
                "logical_tree": initial_logical_dict,
                "physical_plans": initial_physical_plans,
                "best_plan": best_initial_plan,
                "cost": min_initial_cost
            },
            "after_optimization": {
                "logical_tree": optimized_logical_dict,
                "physical_plans": optimized_physical_plans,
                "best_plan": best_plan,
                "cost": min_opt_cost
            },
            "cost_reduction_pct": cost_reduction_pct,
            "optimization_explanations": explanations
        }
        
        return optimized_logical_tree, result_summary

    # --- RULE 1: JOIN REORDERING ---
    def _apply_join_reordering(self, parsed_query: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
        explanations = []
        joins = parsed_query.get("joins", [])
        if len(joins) < 2:
            return parsed_query, explanations
            
        base_table = parsed_query.get("base_table")
        join1 = joins[0]
        join2 = joins[1]
        
        # Build alternative: BaseTable JOIN Join2 JOIN Join1
        alt_query = copy.deepcopy(parsed_query)
        alt_query["joins"] = [join2, join1]
        alt_query["join_conditions"] = [join2["on"], join1["on"]]
        
        try:
            tree1 = build_initial_tree(parsed_query)
            tree2 = build_initial_tree(alt_query)
            
            cost1, _ = self.estimator.estimate_cost(tree1)
            cost2, _ = self.estimator.estimate_cost(tree2)
            
            if cost2 < cost1:
                explanations.append(
                    f"Join reordering: swapped join order from ({base_table} JOIN {join1['table']}) JOIN {join2['table']} "
                    f"to ({base_table} JOIN {join2['table']}) JOIN {join1['table']} "
                    f"because it reduces intermediate relation costs (from {cost1} to {cost2})."
                )
                return alt_query, explanations
            else:
                explanations.append(
                    f"Join ordering: keeping original join order ({base_table} JOIN {join1['table']}) JOIN {join2['table']} "
                    f"because it is cheaper than the alternative ({cost1} < {cost2})."
                )
        except Exception:
            pass
            
        return parsed_query, explanations

    # --- RULE 2: SELECTION PUSHDOWN ---
    def _push_down_selections(self, node: AlgebraNode) -> Tuple[AlgebraNode, List[str]]:
        explanations = []
        
        if node.node_type == "Selection" and len(node.children) == 1 and node.children[0].node_type == "Join":
            selection_node = node
            join_node = node.children[0]
            condition_str = selection_node.attributes.get("condition", "")
            
            import re
            conds = re.split(r'\s+AND\s+', condition_str, flags=re.IGNORECASE)
            
            left_tables = self._find_relation_tables(join_node.children[0])
            right_tables = self._find_relation_tables(join_node.children[1])
            
            pushed_left = []
            pushed_right = []
            remaining = []
            
            for cond in conds:
                ref_tables = []
                # Simple table name lookup in condition
                for t in ("Student", "Department", "Teacher", "Course"):
                    if t.lower() in cond.lower():
                        ref_tables.append(t)
                        
                if not ref_tables:
                    # Fallback check for common columns
                    if "cgpa" in cond.lower():
                        ref_tables.append("Student")
                    else:
                        remaining.append(cond)
                        continue
                        
                is_left = all(t in left_tables for t in ref_tables)
                is_right = all(t in right_tables for t in ref_tables)
                
                if is_left and not is_right:
                    pushed_left.append(cond)
                elif is_right and not is_left:
                    pushed_right.append(cond)
                else:
                    remaining.append(cond)
                    
            if pushed_left:
                c_str = " AND ".join(pushed_left)
                join_node.children[0] = self._insert_selection(join_node.children[0], c_str)
                explanations.append(f"Selection pushdown: pushed filter '{c_str}' down to table(s): {left_tables}.")
                
            if pushed_right:
                c_str = " AND ".join(pushed_right)
                join_node.children[1] = self._insert_selection(join_node.children[1], c_str)
                explanations.append(f"Selection pushdown: pushed filter '{c_str}' down to table(s): {right_tables}.")
                
            if remaining:
                selection_node.attributes["condition"] = " AND ".join(remaining)
                selection_node.children[0] = join_node
                new_root = selection_node
            else:
                new_root = join_node
                explanations.append("Logical query rewrite: eliminated top-level Selection node by pushing all filters down.")
                
            # Recurse join branches
            join_node.children[0], left_expl = self._push_down_selections(join_node.children[0])
            join_node.children[1], right_expl = self._push_down_selections(join_node.children[1])
            explanations.extend(left_expl)
            explanations.extend(right_expl)
            return new_root, explanations
        else:
            pushed_children = []
            for child in node.children:
                opt_child, child_expl = self._push_down_selections(child)
                pushed_children.append(opt_child)
                explanations.extend(child_expl)
            node.children = pushed_children
            return node, explanations

    def _insert_selection(self, node: AlgebraNode, condition: str) -> AlgebraNode:
        if node.node_type == "Selection":
            old_cond = node.attributes.get("condition", "")
            node.attributes["condition"] = f"{old_cond} AND {condition}"
            return node
        return AlgebraNode("Selection", {"condition": condition}, [node])

    def _find_relation_tables(self, node: AlgebraNode) -> List[str]:
        if node.node_type == "Relation":
            return [node.attributes.get("table")]
        tables = []
        for child in node.children:
            tables.extend(self._find_relation_tables(child))
        return tables

    # --- RULE 3: PROJECTION PUSHDOWN ---
    def _apply_projection_pushdown(self, node: AlgebraNode, select_columns: List[str], where_clause: List[Any], joins: List[Dict[str, Any]]) -> Tuple[AlgebraNode, List[str]]:
        explanations = []
        referenced = set()
        
        for col in select_columns:
            if col != "*":
                referenced.add(col)
                
        for item in where_clause:
            if isinstance(item, dict):
                referenced.add(item.get("field", ""))
                val = item.get("value", "")
                if isinstance(val, str) and "." in val:
                    referenced.add(val)
            elif isinstance(item, str) and "." in item:
                referenced.add(item)
                
        for join in joins:
            on_clause = join.get("on", "")
            if on_clause:
                parts = [p.strip() for p in on_clause.split("=")]
                referenced.update(parts)
                
        def prune(n: AlgebraNode):
            if n.node_type == "Relation":
                table_name = n.attributes.get("table")
                table_cols = []
                for ref in referenced:
                    if "." in ref:
                        parts = ref.split(".")
                        if parts[0].lower() == table_name.lower():
                            table_cols.append(parts[1])
                    else:
                        schemas = {
                            "Student": ["id", "name", "dept_id", "cgpa"],
                            "Department": ["id", "name"],
                            "Teacher": ["id", "name", "dept_id"],
                            "Course": ["id", "name", "teacher_id"]
                        }
                        if ref in schemas.get(table_name, []):
                            table_cols.append(ref)
                            
                if not table_cols:
                    schemas = {
                        "Student": ["id", "name", "dept_id", "cgpa"],
                        "Department": ["id", "name"],
                        "Teacher": ["id", "name", "dept_id"],
                        "Course": ["id", "name", "teacher_id"]
                    }
                    table_cols = schemas.get(table_name, ["id"])
                    
                table_cols = list(set(table_cols))
                n.attributes["pruned_columns"] = table_cols
                explanations.append(f"Projection pushdown: pruned table '{table_name}' columns. Scanned set: {table_cols}.")
                
            for child in n.children:
                prune(child)
                
        prune(node)
        return node, explanations

    # --- UTILS ---
    def _dict_to_physical_node(self, d: Dict[str, Any]) -> PhysicalPlanNode:
        children = [self._dict_to_physical_node(c) for c in d.get("children", [])]
        return PhysicalPlanNode(
            operator_name=d["operator"],
            details=d.get("details", {}),
            cost=d.get("cost", 0.0),
            rows=d.get("rows", 0),
            children=children
        )

    def _get_root_cost(self, node: PhysicalPlanNode) -> float:
        return node.cost

    def _get_scan_type(self, node: PhysicalPlanNode) -> str:
        op = node.operator_name
        if op in ("Seq Scan", "Index Scan"):
            return op
        child_scans = [self._get_scan_type(c) for c in node.children]
        if "Index Scan" in child_scans:
            return "Index Scan"
        if "Seq Scan" in child_scans:
            return "Seq Scan"
        return "N/A"

    def _get_join_type(self, node: PhysicalPlanNode) -> str:
        op = node.operator_name
        if op in ("Nested Loop Join", "Hash Join", "Sort Merge Join"):
            return op
        for c in node.children:
            jt = self._get_join_type(c)
            if jt != "N/A":
                return jt
        return "N/A"
