# services/schema_parser.py
import sqlite3

def get_structured_schema(db_path, for_prompt=False):
    """
    Extracts schema information and returns it as a structured dictionary.
    If for_prompt is True, returns a simplified string representation.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
    tables = [row[0] for row in cursor.fetchall()]
    
    schema = {}
    prompt_lines = []

    for table in tables:
        cursor.execute(f"PRAGMA table_info('{table}');")
        columns = cursor.fetchall()
        
        cols_data = []
        for col in columns:
            # col: (cid, name, type, notnull, dflt_value, pk)
            cols_data.append({
                "name": col[1],
                "type": col[2],
                "pk": bool(col[5])
            })
        
        schema[table] = cols_data
        
        if for_prompt:
            col_defs = ", ".join([f"{col['name']} ({col['type']})" for col in cols_data])
            prompt_lines.append(f"Table {table}: {col_defs}")

    conn.close()
    
    return "\n".join(prompt_lines) if for_prompt else schema

def get_query_result(db_path, query):
    """Executes a SQL query and returns headers and rows."""
    conn = sqlite3.connect(db_path)
    # Use a row factory for easier dictionary creation later if needed
    conn.row_factory = sqlite3.Row 
    cursor = conn.cursor()
    
    cursor.execute(query)
    
    # Get column headers from the cursor description
    headers = [description[0] for description in cursor.description] if cursor.description else []
    
    rows = cursor.fetchall()
    # Convert rows to plain tuples for JSON serialization
    plain_rows = [tuple(row) for row in rows]
    
    conn.close()
    return headers, plain_rows