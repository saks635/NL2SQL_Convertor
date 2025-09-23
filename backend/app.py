import os
import sqlite3
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename

# Note: We are importing new helper functions
from services.schema_parser import get_structured_schema, get_query_result
from services.gemini_api import call_gemini
from services.cohere_api import call_cohere
from utils.helpers import format_prompt, clean_sql

# --- App Setup ---
app = Flask(__name__)
CORS(app)
UPLOAD_FOLDER = "uploads"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# --- Utility Function ---
def process_db_file():
    if 'db_file' not in request.files:
        return None, jsonify({"error": "No database file provided."}), 400
    
    db_file = request.files["db_file"]
    filename = secure_filename(db_file.filename)
    db_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    db_file.save(db_path)
    return db_path, None, None

# --- API Endpoints ---

@app.route("/api/schema", methods=["POST"])
def get_schema():
    """Endpoint to extract and return the schema from a DB file."""
    db_path, error_response, status_code = process_db_file()
    if error_response:
        return error_response, status_code

    try:
        schema = get_structured_schema(db_path)
        return jsonify(schema)
    except Exception as e:
        return jsonify({"error": f"Failed to read schema: {str(e)}"}), 500
    finally:
        if db_path and os.path.exists(db_path):
            os.remove(db_path)

@app.route("/api/generate-sql", methods=["POST"])
def generate_sql():
    """Endpoint to generate SQL from a natural language question."""
    db_path, error_response, status_code = process_db_file()
    if error_response:
        return error_response, status_code

    try:
        question = request.form.get("question")
        model = request.form.get("llm")
        
        # We use the structured schema for a better prompt context
        schema_for_prompt = get_structured_schema(db_path, for_prompt=True)
        prompt = format_prompt(question, schema_for_prompt)

        if model == "gemini":
            raw_sql = call_gemini(prompt)
        elif model == "cohere":
            raw_sql = call_cohere(prompt)
        else:
            return jsonify({"error": "Invalid LLM model selected."}), 400
        
        sql_query = clean_sql(raw_sql)
        return jsonify({"sql": sql_query})

    except Exception as e:
        return jsonify({"error": f"Failed to generate SQL: {str(e)}"}), 500
    finally:
        if db_path and os.path.exists(db_path):
            os.remove(db_path)

@app.route("/api/execute-sql", methods=["POST"])
def execute_sql():
    """Endpoint to execute a given SQL query."""
    db_path, error_response, status_code = process_db_file()
    if error_response:
        return error_response, status_code

    try:
        sql_query = request.form.get("sql")
        if not sql_query:
            return jsonify({"error": "No SQL query provided."}), 400
            
        headers, rows = get_query_result(db_path, sql_query)
        return jsonify({"headers": headers, "rows": rows})

    except Exception as e:
        return jsonify({"error": f"Query execution failed: {str(e)}"}), 500
    finally:
        if db_path and os.path.exists(db_path):
            os.remove(db_path)


if __name__ == "__main__":
    app.run(debug=True, port=5000)