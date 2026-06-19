from flask import Flask, render_template, request, jsonify
from config import Config
from database import init_db, execute_query, get_schema
from fake_data import generate_fake_data
from parser import SQLParser
from algebra_tree import build_initial_tree
from optimizer import QueryOptimizer
from cost_estimator import CostEstimator
import time

app = Flask(__name__)
app.config.from_object(Config)

# Initialize database and populate data on startup
with app.app_context():
    # Create tables
    init_db()
    # Generate fake data if tables are empty
    try:
        generate_fake_data()
    except Exception as e:
        print(f"Error generating fake data: {e}")

@app.route('/')
def index():
    """Renders the main dashboard of the Query Optimizer Simulator."""
    schema = get_schema()
    return render_template('index.html', schema=schema)

@app.route('/api/schema', methods=['GET'])
def get_db_schema():
    """API endpoint to fetch the current database schema."""
    schema = get_schema()
    return jsonify(schema)

@app.route('/api/execute', methods=['POST'])
def execute_sql():
    """API endpoint to parse, optimize, estimate cost, plan, and execute a SQL query."""
    data = request.get_json() or {}
    query = data.get("query", "").strip()
    
    if not query:
        return jsonify({
            "success": False, 
            "parsed_query": None,
            "algebra_tree": None,
            "physical_plans": [],
            "cost_analysis": [],
            "best_plan": {},
            "errors": "Query cannot be empty.",
            "error": "Query cannot be empty."
        }), 400
        
    parser = SQLParser()
    optimizer = QueryOptimizer()
    estimator = CostEstimator()
    
    result = {
        "success": True,
        "query": query,
        "parsed_query": None,
        "algebra_tree": None,
        "physical_plans": [],
        "cost_analysis": [],
        "best_plan": {},
        "errors": None,
        # Backward compatibility fields
        "parsed": None,
        "logical_plan": None,
        "optimized_plan": None,
        "physical_plan": None,
        "cost_estimation": None,
        "execution_result": None,
        "execution_time_ms": 0,
        "error": None
    }
    
    # 1. Parse Query
    try:
        parsed_q = parser.parse(query)
        result["parsed_query"] = parsed_q
        result["parsed"] = parsed_q
        
        # Validate table and column schema reference existence
        from parser import validate_schema
        schema = get_schema()
        validate_schema(parsed_q, schema)
    except Exception as e:
        error_msg = str(e)
        return jsonify({
            "success": False,
            "parsed_query": None,
            "algebra_tree": None,
            "physical_plans": [],
            "cost_analysis": [],
            "best_plan": {},
            "errors": error_msg,
            "error": error_msg
        })
        
    # 2. Build Logical Relational Algebra Tree
    try:
        logical_tree = build_initial_tree(parsed_q)
        logical_tree_dict = logical_tree.to_dict()
        result["algebra_tree"] = logical_tree_dict
        result["logical_plan"] = logical_tree_dict
    except Exception as e:
        error_msg = f"Logical Plan Error: {str(e)}"
        return jsonify({
            "success": False,
            "parsed_query": parsed_q,
            "algebra_tree": None,
            "physical_plans": [],
            "cost_analysis": [],
            "best_plan": {},
            "errors": error_msg,
            "error": error_msg
        })
        
    # 3. Optimize & Generate Physical Plans with Costs
    try:
        optimized_tree, opt_summary = optimizer.optimize(logical_tree, parsed_q)
        result["optimized_plan"] = optimized_tree.to_dict()
        result["physical_plans"] = opt_summary["physical_plans"]
        result["cost_analysis"] = opt_summary["cost_analysis"]
        result["best_plan"] = opt_summary["best_plan"]
        
        # Comparison dashboard fields
        result["before_optimization"] = opt_summary["before_optimization"]
        result["after_optimization"] = opt_summary["after_optimization"]
        result["cost_reduction_pct"] = opt_summary["cost_reduction_pct"]
        result["optimization_explanations"] = opt_summary["optimization_explanations"]
        
        # Set physical_plan to the Best Plan's tree for backward compatibility
        result["physical_plan"] = opt_summary["best_plan"]["tree"]
    except Exception as e:
        error_msg = f"Optimizer Error: {str(e)}"
        return jsonify({
            "success": False,
            "parsed_query": parsed_q,
            "algebra_tree": logical_tree_dict,
            "physical_plans": [],
            "cost_analysis": [],
            "best_plan": {},
            "errors": error_msg,
            "error": error_msg
        })
        
    # 4. Estimate Cost (uses logical optimized tree)
    try:
        cost, rows = estimator.estimate_cost(optimized_tree)
        result["cost_estimation"] = {
            "total_cost": round(cost, 2),
            "estimated_rows": rows
        }
    except Exception as e:
        error_msg = f"Cost Estimator Error: {str(e)}"
        return jsonify({
            "success": False,
            "parsed_query": parsed_q,
            "algebra_tree": logical_tree_dict,
            "physical_plans": [],
            "cost_analysis": [],
            "best_plan": {},
            "errors": error_msg,
            "error": error_msg
        })
        
    # 5. Execute Actual Query on SQLite to get output rows
    start_time = time.perf_counter()
    db_result = execute_query(query)
    end_time = time.perf_counter()
    
    result["execution_time_ms"] = round((end_time - start_time) * 1000, 4)
    
    if db_result["success"]:
        result["execution_result"] = {
            "columns": db_result["columns"],
            "rows": db_result["rows"][:100],  # Limit to first 100 rows for performance
            "total_rows": len(db_result["rows"])
        }
    else:
        error_msg = f"Database Execution Error: {db_result['error']}"
        return jsonify({
            "success": False,
            "parsed_query": parsed_q,
            "algebra_tree": logical_tree_dict,
            "physical_plans": [],
            "cost_analysis": [],
            "best_plan": {},
            "errors": error_msg,
            "error": error_msg
        })
        
    return jsonify(result)

@app.route('/api/statistics', methods=['GET'])
def get_db_statistics():
    """API endpoint to fetch database statistics."""
    from statistics_manager import DBStatistics
    stats = DBStatistics()
    stats.refresh()
    total_records = sum(stats.table_counts.values())
    return jsonify({
        "success": True,
        "num_tables": len(stats.table_counts),
        "total_records": total_records,
        "table_counts": stats.table_counts,
        "indexed_columns": stats.indexed_columns
    })

@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
