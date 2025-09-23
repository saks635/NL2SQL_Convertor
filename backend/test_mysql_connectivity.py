"""
Quick Test Script for MySQL NL2SQL Integration
Tests database connectivity, schema extraction, and basic functionality
"""

from services.mysql_connector import MySQLConnector, create_mysql_config_from_env
from services.gemini_api import call_gemini
from utils.helpers import clean_sql
import json

def test_mysql_connectivity():
    """Test MySQL database connectivity and basic operations"""
    
    print("🧪 Testing MySQL NL2SQL Integration")
    print("=" * 40)
    
    # Test 1: Database Connection
    print("\n1️⃣ Testing Database Connection...")
    try:
        config = create_mysql_config_from_env()
        mysql_conn = MySQLConnector(config)
        
        test_results = mysql_conn.test_connection()
        print(f"   SQLAlchemy: {'✅' if test_results['sqlalchemy'] else '❌'}")
        print(f"   PyMySQL: {'✅' if test_results['pymysql'] else '❌'}")
        
        if not test_results['sqlalchemy']:
            print("❌ MySQL connection failed!")
            return False
        
        print("✅ Database connection successful!")
        
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False
    
    # Test 2: Schema Extraction
    print("\n2️⃣ Testing Schema Extraction...")
    try:
        schema_info = mysql_conn.get_schema_info()
        print(f"   Database: {schema_info['database_name']}")
        print(f"   Tables found: {len(schema_info['tables'])}")
        
        for table_name, table_info in schema_info['tables'].items():
            print(f"   - {table_name}: {len(table_info['columns'])} columns, {table_info['row_count']} rows")
        
        print("✅ Schema extraction successful!")
        
    except Exception as e:
        print(f"❌ Schema extraction failed: {e}")
        return False
    
    # Test 3: Sample Query Execution
    print("\n3️⃣ Testing Query Execution...")
    try:
        # Test simple query
        headers, rows = mysql_conn.execute_query("SELECT COUNT(*) as total_customers FROM customers")
        print(f"   Query result: {headers} = {rows}")
        
        # Test join query
        headers, rows = mysql_conn.execute_query("""
            SELECT c.first_name, c.last_name, COUNT(o.id) as order_count 
            FROM customers c 
            LEFT JOIN orders o ON c.id = o.customer_id 
            GROUP BY c.id, c.first_name, c.last_name
        """)
        print(f"   Join query returned {len(rows)} customers with order counts")
        
        print("✅ Query execution successful!")
        
    except Exception as e:
        print(f"❌ Query execution failed: {e}")
        return False
    
    # Test 4: NL to SQL Generation (if Gemini API key is available)
    print("\n4️⃣ Testing NL to SQL Generation...")
    try:
        import os
        if not os.getenv('GEMINI_API_KEY'):
            print("⚠️ Gemini API key not found, skipping AI test")
        else:
            # Create schema prompt
            schema_for_prompt = format_mysql_schema_for_prompt(schema_info)
            
            question = "Show me all customers with their email addresses"
            prompt = f"""
You are an expert SQL query generator. Generate a precise SQL query for MySQL.

Database Schema:
{schema_for_prompt}

Question: {question}

Generate only the SQL query, no explanations.
SQL Query:"""
            
            print(f"   Question: {question}")
            raw_sql = call_gemini(prompt)
            sql_query = clean_sql(raw_sql)
            print(f"   Generated SQL: {sql_query}")
            
            # Execute the generated SQL
            headers, rows = mysql_conn.execute_query(sql_query)
            print(f"   Results: {len(rows)} rows returned")
            
            print("✅ NL to SQL generation successful!")
    
    except Exception as e:
        print(f"⚠️ NL to SQL test failed: {e}")
    
    # Test 5: Sample Data Verification
    print("\n5️⃣ Testing Sample Data...")
    try:
        sample_queries = [
            ("Total Products", "SELECT COUNT(*) FROM products"),
            ("Products > $50", "SELECT name, price FROM products WHERE price > 50"),
            ("Categories", "SELECT name, description FROM categories"),
            ("Recent Orders", "SELECT id, customer_id, status, total_amount FROM orders")
        ]
        
        for desc, query in sample_queries:
            headers, rows = mysql_conn.execute_query(query)
            print(f"   {desc}: {len(rows)} records")
        
        print("✅ Sample data verification successful!")
        
    except Exception as e:
        print(f"❌ Sample data test failed: {e}")
        return False
    
    # Cleanup
    mysql_conn.close()
    
    print("\n🎉 All MySQL tests completed successfully!")
    print("\n📋 Your NL2SQL MySQL integration is ready!")
    print("\n🚀 Next steps:")
    print("   1. Start the enhanced Flask app: python enhanced_app.py")
    print("   2. Use the React frontend or test with API calls")
    print("   3. Try these example questions:")
    print("      - 'Show me all customers'")
    print("      - 'What products cost more than $100?'")
    print("      - 'List orders with customer names'")
    
    return True

def format_mysql_schema_for_prompt(schema_info):
    """Convert MySQL schema info to prompt format"""
    prompt_schema = []
    for table_name, table_info in schema_info["tables"].items():
        table_desc = f"Table: {table_name}\n"
        for column in table_info["columns"]:
            table_desc += f"  - {column['name']} ({column['type']})\n"
        prompt_schema.append(table_desc)
    return "\n".join(prompt_schema)

if __name__ == "__main__":
    test_mysql_connectivity()
