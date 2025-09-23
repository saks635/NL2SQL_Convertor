"""
Enhanced NL2SQL Flask Application
Supports both SQLite (file upload) and MySQL (live database) modes
"""

import os
import sqlite3
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import existing services
from services.schema_parser import get_structured_schema, get_query_result
from services.gemini_api import call_gemini
from services.cohere_api import call_cohere
from utils.helpers import format_prompt, clean_sql

# Import new MySQL services
from services.mysql_connector import MySQLConnector, create_mysql_config_from_env
from services.mongodb_connector import MongoDBConnector, create_mongodb_config_from_env

# Import database design tools
from utils.db_design import DatabaseDesignAnalyzer

# --- App Setup ---
app = Flask(__name__)
CORS(app)
UPLOAD_FOLDER = "uploads"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Global database connectors (initialized when needed)
mysql_connector = None
mongodb_connector = None

# --- Enhanced Utility Functions ---

def get_mysql_connector():
    """Get or create MySQL connector"""
    global mysql_connector
    if mysql_connector is None:
        try:
            config = create_mysql_config_from_env()
            mysql_connector = MySQLConnector(config)
            # Test connection
            test_results = mysql_connector.test_connection()
            if not test_results['sqlalchemy']:
                raise Exception("MySQL connection failed")
        except Exception as e:
            print(f"MySQL connector initialization failed: {e}")
            mysql_connector = None
    return mysql_connector

def get_mongodb_connector():
    """Get or create MongoDB connector"""
    global mongodb_connector
    if mongodb_connector is None:
        try:
            config = create_mongodb_config_from_env()
            mongodb_connector = MongoDBConnector(config)
            # Test connection
            test_results = mongodb_connector.test_connection()
            if not test_results['connection']:
                raise Exception("MongoDB connection failed")
        except Exception as e:
            print(f"MongoDB connector initialization failed: {e}")
            mongodb_connector = None
    return mongodb_connector

def process_db_file():
    """Process uploaded SQLite database file"""
    if 'db_file' not in request.files:
        return None, jsonify({"error": "No database file provided."}), 400
    
    db_file = request.files["db_file"]
    filename = secure_filename(db_file.filename)
    db_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    db_file.save(db_path)
    return db_path, None, None

# --- API Endpoints ---

@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint with database connectivity status"""
    mysql_conn = get_mysql_connector()
    mongo_conn = get_mongodb_connector()
    
    status = {
        "status": "healthy",
        "databases": {
            "sqlite": "available",
            "mysql": "available" if mysql_conn else "unavailable",
            "mongodb": "available" if mongo_conn else "unavailable"
        },
        "ai_models": {
            "gemini": "available" if os.getenv('GEMINI_API_KEY') else "unavailable",
            "cohere": "available" if os.getenv('COHERE_API_KEY') else "unavailable"
        }
    }
    
    return jsonify(status)

@app.route("/api/databases", methods=["GET"])
def list_databases():
    """List available database connections"""
    databases = []
    
    # Always available: SQLite upload
    databases.append({
        "type": "sqlite",
        "name": "SQLite File Upload",
        "description": "Upload a .db file for analysis",
        "available": True,
        "connection_method": "file_upload"
    })
    
    # MySQL if configured
    mysql_conn = get_mysql_connector()
    if mysql_conn:
        config = create_mysql_config_from_env()
        databases.append({
            "type": "mysql",
            "name": f"MySQL ({config['database']})",
            "description": f"Live MySQL database on {config['host']}",
            "available": True,
            "connection_method": "live_connection"
        })
    
    # MongoDB if configured
    mongo_conn = get_mongodb_connector()
    if mongo_conn:
        config = create_mongodb_config_from_env()
        databases.append({
            "type": "mongodb",
            "name": f"MongoDB ({config['database']})",
            "description": f"Live MongoDB database on {config['host']}",
            "available": True,
            "connection_method": "live_connection"
        })
    
    return jsonify({"databases": databases})

@app.route("/api/schema", methods=["POST"])
def get_schema():
    """Extract and return database schema (supports multiple database types)"""
    db_type = request.form.get("db_type", "sqlite")
    
    try:
        if db_type == "sqlite":
            # Original SQLite file upload logic
            db_path, error_response, status_code = process_db_file()
            if error_response:
                return error_response, status_code
            
            schema = get_structured_schema(db_path)
            
            # Clean up file
            if db_path and os.path.exists(db_path):
                os.remove(db_path)
            
            return jsonify(schema)
            
        elif db_type == "mysql":
            mysql_conn = get_mysql_connector()
            if not mysql_conn:
                return jsonify({"error": "MySQL connection not available"}), 500
            
            schema_info = mysql_conn.get_schema_info()
            
            # Convert to format expected by frontend
            formatted_schema = {
                "database_name": schema_info["database_name"],
                "tables": {}
            }
            
            for table_name, table_info in schema_info["tables"].items():
                formatted_schema["tables"][table_name] = {
                    "columns": table_info["columns"],
                    "row_count": table_info["row_count"]
                }
            
            return jsonify(formatted_schema)
            
        elif db_type == "mongodb":
            mongo_conn = get_mongodb_connector()
            if not mongo_conn:
                return jsonify({"error": "MongoDB connection not available"}), 500
            
            schema_info = mongo_conn.get_schema_info()
            
            # Convert MongoDB collections to table-like format
            formatted_schema = {
                "database_name": schema_info["database_name"],
                "tables": {}
            }
            
            for collection_name, collection_info in schema_info["collections"].items():
                # Convert MongoDB fields to SQL-like columns
                columns = []
                for field_path, field_info in collection_info["fields"].items():
                    columns.append({
                        "name": field_path.replace(".", "_"),
                        "type": field_info["types"][0] if field_info["types"] else "TEXT",
                        "nullable": field_info["frequency"] < 1.0
                    })
                
                formatted_schema["tables"][collection_name] = {
                    "columns": columns,
                    "row_count": collection_info["document_count"]
                }
            
            return jsonify(formatted_schema)
        
        else:
            return jsonify({"error": f"Unsupported database type: {db_type}"}), 400
            
    except Exception as e:
        return jsonify({"error": f"Failed to read schema: {str(e)}"}), 500

@app.route("/api/generate-sql", methods=["POST"])
def generate_sql():
    """Generate SQL from natural language question (supports multiple database types)"""
    db_type = request.form.get("db_type", "sqlite")
    question = request.form.get("question")
    model = request.form.get("llm", "gemini")
    
    if not question:
        return jsonify({"error": "No question provided"}), 400
    
    try:
        # Get schema based on database type
        if db_type == "sqlite":
            db_path, error_response, status_code = process_db_file()
            if error_response:
                return error_response, status_code
            
            schema_for_prompt = get_structured_schema(db_path, for_prompt=True)
            
            # Clean up file after getting schema
            if db_path and os.path.exists(db_path):
                os.remove(db_path)
                
        elif db_type == "mysql":
            mysql_conn = get_mysql_connector()
            if not mysql_conn:
                return jsonify({"error": "MySQL connection not available"}), 500
            
            schema_info = mysql_conn.get_schema_info()
            # Convert to prompt format
            schema_for_prompt = format_mysql_schema_for_prompt(schema_info)
            
        elif db_type == "mongodb":
            mongo_conn = get_mongodb_connector()
            if not mongo_conn:
                return jsonify({"error": "MongoDB connection not available"}), 500
            
            schema_info = mongo_conn.get_schema_info()
            # Convert to SQL-like prompt format
            schema_for_prompt = format_mongodb_schema_for_prompt(schema_info)
            
        else:
            return jsonify({"error": f"Unsupported database type: {db_type}"}), 400
        
        # Generate SQL using LLM
        prompt = format_prompt(question, schema_for_prompt, db_type)
        
        if model == "gemini":
            raw_sql = call_gemini(prompt)
        elif model == "cohere":
            raw_sql = call_cohere(prompt)
        else:
            return jsonify({"error": "Invalid LLM model selected."}), 400
        
        sql_query = clean_sql(raw_sql)
        
        return jsonify({
            "sql": sql_query,
            "database_type": db_type,
            "model_used": model
        })
        
    except Exception as e:
        return jsonify({"error": f"Failed to generate SQL: {str(e)}"}), 500

@app.route("/api/execute-sql", methods=["POST"])
def execute_sql():
    """Execute SQL query (supports multiple database types)"""
    db_type = request.form.get("db_type", "sqlite")
    sql_query = request.form.get("sql")
    
    if not sql_query:
        return jsonify({"error": "No SQL query provided."}), 400
    
    try:
        if db_type == "sqlite":
            # Original SQLite logic
            db_path, error_response, status_code = process_db_file()
            if error_response:
                return error_response, status_code
            
            headers, rows = get_query_result(db_path, sql_query)
            
            # Clean up file
            if db_path and os.path.exists(db_path):
                os.remove(db_path)
            
            return jsonify({"headers": headers, "rows": rows})
            
        elif db_type == "mysql":
            mysql_conn = get_mysql_connector()
            if not mysql_conn:
                return jsonify({"error": "MySQL connection not available"}), 500
            
            headers, rows = mysql_conn.execute_query(sql_query)
            return jsonify({"headers": headers, "rows": rows})
            
        elif db_type == "mongodb":
            # For MongoDB, we'll need to convert SQL to aggregation pipeline
            # This is a simplified implementation
            mongo_conn = get_mongodb_connector()
            if not mongo_conn:
                return jsonify({"error": "MongoDB connection not available"}), 500
            
            # For now, return an error suggesting aggregation pipeline usage
            return jsonify({
                "error": "Direct SQL execution not supported for MongoDB. Use aggregation pipelines instead.",
                "suggestion": "MongoDB queries require aggregation pipelines rather than SQL syntax."
            }), 400
            
        else:
            return jsonify({"error": f"Unsupported database type: {db_type}"}), 400
            
    except Exception as e:
        return jsonify({"error": f"Query execution failed: {str(e)}"}), 500

@app.route("/api/analyze-schema", methods=["POST"])
def analyze_schema():
    """Analyze database schema for normalization and design patterns"""
    db_type = request.form.get("db_type", "sqlite")
    
    try:
        analyzer = DatabaseDesignAnalyzer()
        
        if db_type == "sqlite":
            db_path, error_response, status_code = process_db_file()
            if error_response:
                return error_response, status_code
            
            schema = analyzer.analyze_existing_database(db_path)
            normalization_analysis = analyzer.check_normalization_level(schema)
            
            # Clean up file
            if db_path and os.path.exists(db_path):
                os.remove(db_path)
            
            return jsonify({
                "schema_name": schema.name,
                "tables_count": len(schema.tables),
                "relationships_count": len(schema.relationships),
                "normalization_analysis": normalization_analysis
            })
            
        else:
            return jsonify({"error": "Schema analysis currently supported only for SQLite"}), 400
            
    except Exception as e:
        return jsonify({"error": f"Schema analysis failed: {str(e)}"}), 500

# --- Helper Functions ---

def format_mysql_schema_for_prompt(schema_info):
    """Convert MySQL schema info to prompt format"""
    prompt_schema = []
    for table_name, table_info in schema_info["tables"].items():
        table_desc = f"Table: {table_name}\n"
        for column in table_info["columns"]:
            table_desc += f"  - {column['name']} ({column['type']})\n"
        prompt_schema.append(table_desc)
    return "\n".join(prompt_schema)

def format_mongodb_schema_for_prompt(schema_info):
    """Convert MongoDB schema info to SQL-like prompt format"""
    prompt_schema = []
    for collection_name, collection_info in schema_info["collections"].items():
        table_desc = f"Collection (as Table): {collection_name}\n"
        for field_path, field_info in collection_info["fields"].items():
            field_type = field_info["types"][0] if field_info["types"] else "TEXT"
            table_desc += f"  - {field_path.replace('.', '_')} ({field_type})\n"
        prompt_schema.append(table_desc)
    return "\n".join(prompt_schema)

# --- Enhanced Format Prompt ---
def format_prompt(question, schema, db_type="sqlite"):
    """Enhanced prompt formatting with database type awareness"""
    base_prompt = f"""
You are an expert SQL query generator. Given a database schema and a natural language question, 
generate a precise SQL query.

Database Type: {db_type.upper()}
Database Schema:
{schema}

Question: {question}

Important:
- Generate only the SQL query, no explanations
- Use proper {db_type.upper()} syntax
- Ensure the query is syntactically correct
- Use appropriate table and column names from the schema
"""
    
    if db_type == "mysql":
        base_prompt += """
- Use MySQL-specific functions when needed
- Use backticks for table/column names if they contain special characters
"""
    elif db_type == "mongodb":
        base_prompt += """
- Generate SQL that could conceptually work with the document structure
- Treat nested fields as separate columns (use underscore notation)
"""
    
    base_prompt += "\nSQL Query:"
    
    return base_prompt

if __name__ == "__main__":
    # Initialize database connections on startup
    print("🚀 Starting Enhanced NL2SQL Application...")
    
    mysql_conn = get_mysql_connector()
    if mysql_conn:
        print("✅ MySQL connection established")
    else:
        print("⚠️ MySQL connection not available")
    
    mongo_conn = get_mongodb_connector()
    if mongo_conn:
        print("✅ MongoDB connection established")
    else:
        print("⚠️ MongoDB connection not available")
    
    port = int(os.environ.get("PORT", 5000))
    print(f"🌐 Server starting on port {port}")
    app.run(debug=False, host="0.0.0.0", port=port)
