import re
from typing import Dict, Any, List

def tokenize(sql: str) -> List[tuple]:
    """Tokenizes a SQL query string into type-value pairs."""
    token_specification = [
        ('STRING',   r"'(?:''|[^'])*'|\"(?:\"\"|[^\"])*\""), # String literals with single or double quotes
        ('NUMBER',   r'\d+(?:\.\d+)?'),                     # Integer or decimal number
        ('KEYWORD',  r'\b(?:SELECT|FROM|INNER|LEFT|RIGHT|JOIN|ON|WHERE|AND|OR)\b'),
        ('OP',       r'<=|>=|!=|<>|=|<|>|\*'),              # Comparison operators and *
        ('IDENT',    r'[a-zA-Z_][a-zA-Z0-9_\.]*'),          # Identifiers (like Student.name or Student)
        ('COMMA',    r','),
        ('PAREN',    r'[()]'),
        ('SEMI',     r';'),
        ('SKIP',     r'\s+'),                               # Skip spaces
        ('MISMATCH', r'.'),                                 # Any other character
    ]
    tok_regex = '|'.join(f'(?P<{name}>{pattern})' for name, pattern in token_specification)
    tokens = []
    for mo in re.finditer(tok_regex, sql, flags=re.IGNORECASE):
        kind = mo.lastgroup
        value = mo.group()
        if kind == 'SKIP':
            continue
        elif kind == 'MISMATCH':
            raise ValueError(f"Unexpected character: '{value}'")
        tokens.append((kind, value))
    return tokens

class SQLParser:
    """A production-quality SQL parser for the Query Optimizer Simulator.
    
    Parses SELECT queries containing JOINs (INNER, LEFT, RIGHT), WHERE clauses,
    and multiple filter conditions combined with AND / OR.
    Provides detailed syntax validation and meaningful error messages.
    """
    
    def __init__(self):
        self.tokens = []
        self.pos = 0

    def _peek(self) -> tuple:
        """Returns the current token without consuming it."""
        if self._is_at_end():
            return ('EOF', '')
        return self.tokens[self.pos]

    def _consume(self, expected_kind: str, expected_value: str = None) -> str:
        """Consumes the current token if it matches expected kind and value; otherwise raises error."""
        if self._is_at_end():
            raise ValueError(f"SQL Syntax Error: Unexpected end of query. Expected token type '{expected_kind}'.")
            
        tok_kind, tok_val = self.tokens[self.pos]
        
        if tok_kind != expected_kind:
            raise ValueError(f"SQL Syntax Error: Expected token type '{expected_kind}', got '{tok_val}'.")
            
        if expected_value and tok_val.upper() != expected_value.upper():
            raise ValueError(f"SQL Syntax Error: Expected '{expected_value}', got '{tok_val}'.")
            
        self.pos += 1
        return tok_val

    def _is_at_end(self) -> bool:
        """Checks if all tokens have been processed."""
        return self.pos >= len(self.tokens)

    def parse(self, query: str) -> Dict[str, Any]:
        """Parses a SQL query and returns a structured AST-like dictionary representation.
        
        Validates structure and raises ValueError with readable messages on failure.
        """
        # Validate empty query
        if not query or not query.strip():
            raise ValueError("SQL Syntax Error: Query is empty.")
            
        self.pos = 0
        try:
            self.tokens = tokenize(query)
        except Exception as e:
            raise ValueError(f"SQL Lexical Error: {str(e)}")
            
        if not self.tokens:
            raise ValueError("SQL Syntax Error: No query tokens found.")

        # 1. Parse SELECT
        self._consume('KEYWORD', 'SELECT')
        select_columns = self._parse_select_list()
        
        # 2. Parse FROM
        base_table = self._parse_from()
        
        # 3. Parse JOINs
        joins = self._parse_joins()
        
        # 4. Parse WHERE
        where_clause = self._parse_where()
        
        # Check trailing tokens
        if not self._is_at_end():
            next_tok = self._peek()
            if next_tok[0] != 'SEMI':
                raise ValueError(f"SQL Syntax Error: Unexpected token '{next_tok[1]}' at end of query.")
            self._consume('SEMI')
            
        if not self._is_at_end():
            raise ValueError(f"SQL Syntax Error: Found extra tokens after semicolon: '{self._peek()[1]}'.")
            
        # Build structured result
        return {
            "query_type": "SELECT",
            "select": select_columns,
            "from": [base_table],  # List format for backwards compatibility
            "base_table": base_table,
            "joins": joins,
            "join_conditions": [j["on"] for j in joins],
            "where": where_clause,
            "raw_query": query
        }

    def _parse_select_list(self) -> List[str]:
        """Parses comma-separated select columns or '*'."""
        columns = []
        
        # Expect at least one column
        if self._is_at_end():
            raise ValueError("SQL Syntax Error: Expected column names or '*' after SELECT.")
            
        tok = self._peek()
        if tok[0] == 'OP' and tok[1] == '*':
            self._consume('OP')
            columns.append('*')
        elif tok[0] == 'IDENT':
            columns.append(self._consume('IDENT'))
        else:
            raise ValueError(f"SQL Syntax Error: Expected column name or '*', got '{tok[1]}'.")
            
        # Parse subsequent columns separated by commas
        while not self._is_at_end() and self._peek()[0] == 'COMMA':
            self._consume('COMMA')
            
            if self._is_at_end():
                raise ValueError("SQL Syntax Error: Trailing comma in SELECT column list.")
                
            tok = self._peek()
            if tok[0] == 'KEYWORD' and tok[1].upper() == 'FROM':
                raise ValueError("SQL Syntax Error: Trailing comma before FROM keyword.")
                
            if tok[0] == 'OP' and tok[1] == '*':
                self._consume('OP')
                columns.append('*')
            elif tok[0] == 'IDENT':
                columns.append(self._consume('IDENT'))
            else:
                raise ValueError(f"SQL Syntax Error: Expected column name after comma, got '{tok[1]}'.")
                
        return columns

    def _parse_from(self) -> str:
        """Parses the FROM keyword and the base table name."""
        if self._is_at_end():
            raise ValueError("SQL Syntax Error: Missing FROM clause.")
            
        tok = self._peek()
        if tok[0] != 'KEYWORD' or tok[1].upper() != 'FROM':
            raise ValueError(f"SQL Syntax Error: Expected FROM keyword, got '{tok[1]}'.")
            
        self._consume('KEYWORD')
        
        if self._is_at_end():
            raise ValueError("SQL Syntax Error: Missing table name in FROM clause.")
            
        tok = self._peek()
        if tok[0] != 'IDENT':
            raise ValueError(f"SQL Syntax Error: Expected base table name, got '{tok[1]}'.")
            
        return self._consume('IDENT')

    def _parse_joins(self) -> List[Dict[str, Any]]:
        """Parses zero or more explicit JOIN clauses."""
        joins = []
        
        while not self._is_at_end():
            tok = self._peek()
            
            # Check if this token starts a JOIN (INNER, LEFT, RIGHT, or plain JOIN)
            is_join_start = False
            join_type = "INNER JOIN"
            
            if tok[0] == 'KEYWORD':
                upper_val = tok[1].upper()
                if upper_val in ('INNER', 'LEFT', 'RIGHT'):
                    is_join_start = True
                    first_keyword = self._consume('KEYWORD').upper()
                    
                    if self._is_at_end() or self._peek()[1].upper() != 'JOIN':
                        raise ValueError(f"SQL Syntax Error: Expected JOIN keyword after {first_keyword}.")
                    self._consume('KEYWORD')
                    join_type = f"{first_keyword} JOIN"
                elif upper_val == 'JOIN':
                    is_join_start = True
                    self._consume('KEYWORD')
                    join_type = "INNER JOIN"
                    
            if not is_join_start:
                break
                
            # Expect joined table name
            if self._is_at_end() or self._peek()[0] != 'IDENT':
                raise ValueError(f"SQL Syntax Error: Expected table name after {join_type}.")
            joined_table = self._consume('IDENT')
            
            # Expect ON keyword
            if self._is_at_end() or self._peek()[1].upper() != 'ON':
                raise ValueError(f"SQL Syntax Error: Expected ON keyword after table '{joined_table}' in JOIN.")
            self._consume('KEYWORD')
            
            # Expect join condition: left_col = right_col
            if self._is_at_end() or self._peek()[0] != 'IDENT':
                raise ValueError("SQL Syntax Error: Expected column name in JOIN ON condition.")
            col1 = self._consume('IDENT')
            
            if self._is_at_end() or self._peek()[0] != 'OP' or self._peek()[1] != '=':
                raise ValueError(f"SQL Syntax Error: Expected '=' operator in JOIN condition, got '{self._peek()[1]}'.")
            self._consume('OP')
            
            if self._is_at_end() or self._peek()[0] != 'IDENT':
                raise ValueError("SQL Syntax Error: Expected matching column name in JOIN ON condition.")
            col2 = self._consume('IDENT')
            
            joins.append({
                "table": joined_table,
                "type": join_type,
                "on": f"{col1} = {col2}"
            })
            
        return joins

    def _parse_where(self) -> List[Any]:
        """Parses the optional WHERE clause containing boolean conditions."""
        if self._is_at_end():
            return []
            
        tok = self._peek()
        if tok[0] != 'KEYWORD' or tok[1].upper() != 'WHERE':
            return []
            
        self._consume('KEYWORD')
        where_clause = []
        
        # Parse first condition
        cond = self._parse_condition()
        where_clause.append(cond)
        
        # Check for subsequent conditions linked by AND / OR
        while not self._is_at_end():
            next_tok = self._peek()
            
            if next_tok[0] == 'KEYWORD' and next_tok[1].upper() in ('AND', 'OR'):
                op = self._consume('KEYWORD').upper()
                where_clause.append(op)
                
                # Verify we don't end on an operator
                if self._is_at_end():
                    raise ValueError(f"SQL Syntax Error: Dangling {op} operator in WHERE clause.")
                    
                next_cond = self._parse_condition()
                where_clause.append(next_cond)
            elif next_tok[0] == 'SEMI':
                break
            else:
                # If it's not AND/OR or SEMI, it's a syntax error
                raise ValueError(f"SQL Syntax Error: Unexpected token '{next_tok[1]}' in WHERE clause.")
                
        return where_clause

    def _parse_condition(self) -> Dict[str, str]:
        """Parses a single filter condition (field operator value)."""
        if self._is_at_end():
            raise ValueError("SQL Syntax Error: Expected condition in WHERE clause.")
            
        # Field (must be identifier)
        if self._peek()[0] != 'IDENT':
            raise ValueError(f"SQL Syntax Error: Expected column name, got '{self._peek()[1]}'.")
        field = self._consume('IDENT')
        
        # Operator
        if self._is_at_end():
            raise ValueError(f"SQL Syntax Error: Expected operator after column '{field}'.")
        if self._peek()[0] != 'OP' or self._peek()[1] == '*':
            raise ValueError(f"SQL Syntax Error: Expected comparison operator (e.g. =, >, <), got '{self._peek()[1]}'.")
        op = self._consume('OP')
        
        # Value (number, string, or identifier)
        if self._is_at_end():
            raise ValueError(f"SQL Syntax Error: Expected comparison value after operator '{op}'.")
        val_tok = self._peek()
        if val_tok[0] not in ('NUMBER', 'STRING', 'IDENT'):
            raise ValueError(f"SQL Syntax Error: Expected number, string, or column name, got '{val_tok[1]}'.")
        value = self._consume(val_tok[0])
        
        return {"field": field, "op": op, "value": value}

def validate_schema(parsed_q: Dict[str, Any], schema: Dict[str, Any]) -> None:
    """Validates that all tables and columns referenced in the parsed query exist in the database schema."""
    if not schema or "error" in schema:
        # Schema failed to load or is empty, skip validation
        return

    # 1. Collect all tables in the query
    query_tables = set()
    base_table = parsed_q.get("base_table")
    if base_table:
        query_tables.add(base_table)
    for join in parsed_q.get("joins", []):
        join_table = join.get("table")
        if join_table:
            query_tables.add(join_table)
            
    # Check table existence
    for table in query_tables:
        if table not in schema:
            raise ValueError(f"SQL Schema Error: Unknown table '{table}'. Available tables are: {', '.join(schema.keys())}.")
            
    # Helper to check if a column (qualified or unqualified) exists and is valid
    def validate_column_ref(col_ref: str, context_msg: str):
        if col_ref == "*":
            return
            
        if "." in col_ref:
            parts = col_ref.split(".")
            if len(parts) != 2:
                raise ValueError(f"SQL Schema Error: Malformed column reference '{col_ref}' in {context_msg}.")
            tbl, col = parts
            if tbl not in query_tables:
                raise ValueError(f"SQL Schema Error: Table '{tbl}' referenced in {context_msg} is not included in the FROM or JOIN clauses of this query.")
            # Get table columns
            tbl_cols = [c["name"] for c in schema.get(tbl, [])]
            if col not in tbl_cols:
                raise ValueError(f"SQL Schema Error: Column '{col}' does not exist in table '{tbl}'. Available columns are: {', '.join(tbl_cols)}.")
        else:
            # Unqualified column name: must exist in exactly one of the query tables
            found_in = []
            for tbl in query_tables:
                tbl_cols = [c["name"] for c in schema.get(tbl, [])]
                if col_ref in tbl_cols:
                    found_in.append(tbl)
            if not found_in:
                all_cols_info = []
                for tbl in query_tables:
                    cols = [c["name"] for c in schema.get(tbl, [])]
                    all_cols_info.append(f"{tbl}({', '.join(cols)})")
                raise ValueError(f"SQL Schema Error: Column '{col_ref}' in {context_msg} does not exist in any of the active query tables: {', '.join(all_cols_info)}.")
            if len(found_in) > 1:
                raise ValueError(f"SQL Schema Error: Column '{col_ref}' in {context_msg} is ambiguous. It exists in multiple tables: {', '.join(found_in)}. Please qualify it (e.g. Table.column).")

    # 2. Validate SELECT columns
    for col in parsed_q.get("select", []):
        validate_column_ref(col, "SELECT list")
        
    # 3. Validate JOIN ON conditions
    for join in parsed_q.get("joins", []):
        on_clause = join.get("on", "")
        if on_clause:
            parts = [p.strip() for p in on_clause.split("=")]
            if len(parts) != 2:
                raise ValueError(f"SQL Schema Error: Malformed JOIN ON condition '{on_clause}'. Expected format: Table1.col1 = Table2.col2.")
            validate_column_ref(parts[0], f"JOIN ON clause for '{join['table']}'")
            validate_column_ref(parts[1], f"JOIN ON clause for '{join['table']}'")
            
    # 4. Validate WHERE conditions
    where_clause = parsed_q.get("where", [])
    for cond in where_clause:
        if isinstance(cond, dict):
            field = cond.get("field")
            if field:
                validate_column_ref(field, "WHERE clause")
            # If the value is a column reference (qualified column)
            val = cond.get("value")
            if isinstance(val, str) and "." in val:
                # Check that it starts with a letter or underscore (valid identifier start)
                if val and (val[0].isalpha() or val[0] == '_'):
                    # Double-check it's not a string literal (which has quotes)
                    if not (val.startswith("'") or val.startswith('"')):
                        validate_column_ref(val, "WHERE clause comparison")

if __name__ == "__main__":
    parser = SQLParser()
    test_queries = [
        "SELECT Student.name, Department.name FROM Student JOIN Department ON Student.dept_id = Department.id WHERE Student.cgpa > 3.5 AND Department.id > 2;",
        "SELECT name FROM Student LEFT JOIN Department ON Student.dept_id = Department.id WHERE Student.cgpa <= 3.8 OR Student.cgpa >= 2.0;",
        "SELECT * FROM Student WHERE cgpa = 4.0",
        # Error cases
        "SELECT Student.name FROM",
        "SELECT Student.name FROM Student JOIN Department",
        "SELECT Student.name FROM Student WHERE cgpa > 3.0 AND",
        "SELECT Student.name, FROM Student"
    ]
    for q in test_queries:
        print(f"Query: {q}")
        try:
            print(f"Parsed: {parser.parse(q)}\n")
        except Exception as e:
            print(f"Error: {e}\n")
