import sqlite3
import os
from config import Config

def get_db_connection():
    """Establishes a connection to the SQLite database."""
    # Ensure data directory exists
    os.makedirs(Config.DATABASE_DIR, exist_ok=True)
    conn = sqlite3.connect(Config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the database schema if it doesn't exist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create Department Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Department (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )
    ''')
    
    # Create Teacher Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Teacher (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            dept_id INTEGER,
            FOREIGN KEY (dept_id) REFERENCES Department (id)
        )
    ''')
    
    # Create Student Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Student (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            dept_id INTEGER,
            cgpa REAL CHECK (cgpa >= 0.0 AND cgpa <= 4.0),
            FOREIGN KEY (dept_id) REFERENCES Department (id)
        )
    ''')
    
    # Create Course Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Course (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            teacher_id INTEGER,
            FOREIGN KEY (teacher_id) REFERENCES Teacher (id)
        )
    ''')
    
    conn.commit()
    conn.close()

def execute_query(query: str, params: tuple = ()):
    """Executes a read query and returns the column headers and result rows."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(query, params)
        # Fetch results
        columns = [description[0] for description in cursor.description] if cursor.description else []
        rows = [dict(row) for row in cursor.fetchall()]
        return {"success": True, "columns": columns, "rows": rows, "error": None}
    except Exception as e:
        return {"success": False, "columns": [], "rows": [], "error": str(e)}
    finally:
        conn.close()

def get_schema():
    """Returns database schema information (tables, columns, and types)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    schema = {}
    try:
        # Get all table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        tables = [row[0] for row in cursor.fetchall()]
        
        for table in tables:
            cursor.execute(f"PRAGMA table_info({table})")
            columns = []
            for col in cursor.fetchall():
                columns.append({
                    "name": col[1],
                    "type": col[2],
                    "notnull": bool(col[3]),
                    "primary_key": bool(col[5])
                })
            schema[table] = columns
        return schema
    except Exception as e:
        return {"error": str(e)}
    finally:
        conn.close()
