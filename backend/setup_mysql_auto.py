"""
Automated MySQL Database Setup Script
Creates database, user, and sample tables for NL2SQL system with automatic password handling
"""

import os
import sys
from dotenv import load_dotenv
import pymysql
from services.mysql_connector import MySQLConnector, create_mysql_config_from_env

# Load environment variables
load_dotenv()

def setup_mysql_database():
    """Set up MySQL database, user, and initial schema"""
    
    print("🔧 MySQL Database Setup for NL2SQL System")
    print("=" * 50)
    
    # Use the password provided by the user
    root_password = "Saksham@98"
    
    # Connect as root to create database and user
    try:
        root_connection = pymysql.connect(
            host='localhost',
            user='root',
            password=root_password,
            charset='utf8mb4'
        )
        cursor = root_connection.cursor()
        
        # Get configuration from environment
        config = create_mysql_config_from_env()
        
        print(f"📝 Creating database: {config['database']}")
        
        # Create database
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {config['database']} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        
        # Create user
        print(f"👤 Creating user: {config['user']}")
        cursor.execute(f"CREATE USER IF NOT EXISTS '{config['user']}'@'localhost' IDENTIFIED BY '{config['password']}';")
        
        # Grant privileges
        print(f"🔐 Granting privileges to {config['user']}")
        cursor.execute(f"GRANT ALL PRIVILEGES ON {config['database']}.* TO '{config['user']}'@'localhost';")
        cursor.execute("FLUSH PRIVILEGES;")
        
        cursor.close()
        root_connection.close()
        
        print("✅ Database and user created successfully!")
        
        # Test the new connection
        print("\n🧪 Testing new database connection...")
        return test_connection(config)
        
    except Exception as e:
        print(f"❌ Failed to setup database: {e}")
        return False

def test_connection(config):
    """Test the MySQL connection with new credentials"""
    try:
        mysql_connector = MySQLConnector(config)
        test_results = mysql_connector.test_connection()
        
        print("\n📊 Connection Test Results:")
        print(f"   SQLAlchemy: {'✅' if test_results['sqlalchemy'] else '❌'}")
        print(f"   PyMySQL: {'✅' if test_results['pymysql'] else '❌'}")
        print(f"   ODBC: {'✅' if test_results['odbc'] else '❌'}")
        
        if test_results['errors']:
            print("\n⚠️ Errors encountered:")
            for error in test_results['errors']:
                print(f"   - {error}")
        
        mysql_connector.close()
        
        # If at least SQLAlchemy works, we're good
        if test_results['sqlalchemy']:
            print("\n✅ MySQL connection successful!")
            return True
        else:
            print("\n❌ MySQL connection failed!")
            return False
            
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False

def create_sample_tables(config):
    """Create sample tables for testing"""
    try:
        print("\n📋 Creating sample tables...")
        
        mysql_connector = MySQLConnector(config)
        
        # Sample e-commerce tables
        tables_sql = [
            """
            CREATE TABLE IF NOT EXISTS customers (
                id INT PRIMARY KEY AUTO_INCREMENT,
                email VARCHAR(255) UNIQUE NOT NULL,
                first_name VARCHAR(100) NOT NULL,
                last_name VARCHAR(100) NOT NULL,
                phone VARCHAR(20),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS categories (
                id INT PRIMARY KEY AUTO_INCREMENT,
                name VARCHAR(100) UNIQUE NOT NULL,
                description TEXT,
                parent_id INT,
                FOREIGN KEY (parent_id) REFERENCES categories(id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS products (
                id INT PRIMARY KEY AUTO_INCREMENT,
                name VARCHAR(200) NOT NULL,
                description TEXT,
                price DECIMAL(10,2) NOT NULL,
                category_id INT,
                stock_quantity INT DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (category_id) REFERENCES categories(id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS orders (
                id INT PRIMARY KEY AUTO_INCREMENT,
                customer_id INT NOT NULL,
                order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status VARCHAR(50) NOT NULL,
                total_amount DECIMAL(10,2) NOT NULL,
                shipping_address TEXT,
                billing_address TEXT,
                FOREIGN KEY (customer_id) REFERENCES customers(id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS order_items (
                id INT PRIMARY KEY AUTO_INCREMENT,
                order_id INT NOT NULL,
                product_id INT NOT NULL,
                quantity INT NOT NULL,
                unit_price DECIMAL(10,2) NOT NULL,
                total_price DECIMAL(10,2) NOT NULL,
                FOREIGN KEY (order_id) REFERENCES orders(id),
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
            """
        ]
        
        for sql in tables_sql:
            mysql_connector.execute_query(sql.strip())
        
        print("✅ Sample tables created successfully!")
        
        # Insert some sample data
        insert_sample_data(mysql_connector)
        
        mysql_connector.close()
        return True
        
    except Exception as e:
        print(f"❌ Failed to create tables: {e}")
        return False

def insert_sample_data(mysql_connector):
    """Insert sample data for testing"""
    try:
        print("📊 Inserting sample data...")
        
        # Sample categories
        mysql_connector.execute_query("""
            INSERT IGNORE INTO categories (name, description) VALUES 
            ('Electronics', 'Electronic devices and gadgets'),
            ('Clothing', 'Apparel and fashion items'),
            ('Books', 'Books and educational materials')
        """)
        
        # Sample customers
        mysql_connector.execute_query("""
            INSERT IGNORE INTO customers (email, first_name, last_name, phone) VALUES 
            ('john.doe@example.com', 'John', 'Doe', '+1234567890'),
            ('jane.smith@example.com', 'Jane', 'Smith', '+1234567891'),
            ('bob.johnson@example.com', 'Bob', 'Johnson', '+1234567892')
        """)
        
        # Sample products
        mysql_connector.execute_query("""
            INSERT IGNORE INTO products (name, description, price, category_id, stock_quantity) VALUES 
            ('Laptop', 'High-performance laptop', 999.99, 1, 10),
            ('T-Shirt', 'Cotton t-shirt', 19.99, 2, 50),
            ('Python Programming Book', 'Learn Python programming', 39.99, 3, 25),
            ('Smartphone', 'Latest smartphone model', 699.99, 1, 15),
            ('Jeans', 'Blue denim jeans', 59.99, 2, 30),
            ('Data Science Guide', 'Complete data science handbook', 49.99, 3, 20)
        """)
        
        # Sample orders
        mysql_connector.execute_query("""
            INSERT IGNORE INTO orders (customer_id, status, total_amount, shipping_address) VALUES 
            (1, 'completed', 1059.98, '123 Main St, Anytown, USA'),
            (2, 'processing', 79.98, '456 Oak Ave, Springfield, USA'),
            (3, 'shipped', 39.99, '789 Pine Rd, Riverside, USA')
        """)
        
        # Sample order items
        mysql_connector.execute_query("""
            INSERT IGNORE INTO order_items (order_id, product_id, quantity, unit_price, total_price) VALUES 
            (1, 1, 1, 999.99, 999.99),
            (1, 2, 3, 19.99, 59.97),
            (2, 4, 1, 699.99, 699.99),
            (2, 5, 1, 59.99, 59.99),
            (3, 3, 1, 39.99, 39.99)
        """)
        
        print("✅ Sample data inserted!")
        
    except Exception as e:
        print(f"⚠️ Sample data insertion warning: {e}")

def main():
    """Main setup function"""
    print("🚀 Automated NL2SQL MySQL Setup!")
    print("\nThis script will:")
    print("1. Create the MySQL database and user")
    print("2. Test the connection")
    print("3. Create sample tables with data")
    print()
    
    # Step 1: Setup database and user
    if not setup_mysql_database():
        print("\n❌ Database setup failed. Please check your MySQL installation and credentials.")
        return
    
    # Step 2: Create sample tables
    config = create_mysql_config_from_env()
    if create_sample_tables(config):
        print("\n🎉 MySQL setup completed successfully!")
        print(f"\nYour NL2SQL system is now ready to use with MySQL!")
        print(f"Database: {config['database']}")
        print(f"User: {config['user']}")
        print(f"Host: {config['host']}:{config['port']}")
        
        print("\n📋 Sample data created:")
        print("- 6 products across 3 categories")
        print("- 3 customers with contact information")
        print("- 3 orders with multiple items")
        print("- Relationships between all tables")
        
        print("\n🎯 Try these example questions:")
        print("- 'Show me all customers from the orders table'")
        print("- 'What products cost more than $50?'")
        print("- 'List all orders with their customer names'")
        print("- 'How many items are in stock for each category?'")
        
        print("\n📋 Next steps:")
        print("1. Run the enhanced Flask application: python enhanced_app.py")
        print("2. Test SQL generation with the sample data")
        print("3. Use the /api/health endpoint to verify connectivity")
    else:
        print("\n⚠️ Tables creation failed, but database setup succeeded.")

if __name__ == "__main__":
    main()
