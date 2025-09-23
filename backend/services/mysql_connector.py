"""
MySQL Database Connector Service
Provides MySQL connectivity with ODBC and SQLAlchemy support
"""

import os
import logging
from typing import Dict, List, Tuple, Optional, Any
import pymysql
import pyodbc
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
import pandas as pd

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MySQLConnector:
    """Enhanced MySQL connector with multiple connection methods"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize MySQL connector with configuration
        
        Args:
            config: Dictionary containing database configuration
                   {
                       'host': 'localhost',
                       'port': 3306,
                       'user': 'username',
                       'password': 'password',
                       'database': 'database_name',
                       'charset': 'utf8mb4'
                   }
        """
        self.config = config
        self.engine = None
        self.Session = None
        self._init_sqlalchemy()
    
    def _init_sqlalchemy(self):
        """Initialize SQLAlchemy engine and session"""
        try:
            # URL encode password to handle special characters
            from urllib.parse import quote_plus
            encoded_password = quote_plus(self.config['password'])
            
            # Create SQLAlchemy engine with connection pooling
            connection_string = (
                f"mysql+pymysql://{self.config['user']}:{encoded_password}"
                f"@{self.config['host']}:{self.config.get('port', 3306)}"
                f"/{self.config['database']}"
                f"?charset={self.config.get('charset', 'utf8mb4')}"
            )
            
            self.engine = create_engine(
                connection_string,
                pool_size=10,
                max_overflow=20,
                pool_recycle=3600,
                pool_pre_ping=True,
                echo=False  # Set to True for SQL query logging
            )
            
            self.Session = sessionmaker(bind=self.engine)
            logger.info("SQLAlchemy MySQL engine initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize SQLAlchemy engine: {e}")
            raise
    
    def get_odbc_connection_string(self) -> str:
        """
        Generate ODBC connection string for MySQL
        
        Returns:
            ODBC connection string
        """
        return (
            f"DRIVER={{MySQL ODBC 8.0 Driver}};"
            f"SERVER={self.config['host']};"
            f"PORT={self.config.get('port', 3306)};"
            f"DATABASE={self.config['database']};"
            f"UID={self.config['user']};"
            f"PWD={self.config['password']};"
            f"CHARSET={self.config.get('charset', 'utf8mb4')};"
        )
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Test database connection using multiple methods
        
        Returns:
            Dictionary with connection test results
        """
        results = {
            'sqlalchemy': False,
            'pymysql': False,
            'odbc': False,
            'errors': []
        }
        
        # Test SQLAlchemy connection
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            results['sqlalchemy'] = True
            logger.info("SQLAlchemy connection test passed")
        except Exception as e:
            results['errors'].append(f"SQLAlchemy: {str(e)}")
            logger.error(f"SQLAlchemy connection failed: {e}")
        
        # Test PyMySQL connection
        try:
            connection = pymysql.connect(**self.config)
            connection.close()
            results['pymysql'] = True
            logger.info("PyMySQL connection test passed")
        except Exception as e:
            results['errors'].append(f"PyMySQL: {str(e)}")
            logger.error(f"PyMySQL connection failed: {e}")
        
        # Test ODBC connection
        try:
            conn_str = self.get_odbc_connection_string()
            with pyodbc.connect(conn_str) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.close()
            results['odbc'] = True
            logger.info("ODBC connection test passed")
        except Exception as e:
            results['errors'].append(f"ODBC: {str(e)}")
            logger.error(f"ODBC connection failed: {e}")
        
        return results
    
    def get_schema_info(self) -> Dict[str, Any]:
        """
        Extract comprehensive schema information from MySQL database
        
        Returns:
            Dictionary containing database schema information
        """
        schema_info = {
            'database_name': self.config['database'],
            'tables': {},
            'views': {},
            'relationships': [],
            'indexes': {},
            'constraints': {}
        }
        
        try:
            inspector = inspect(self.engine)
            
            # Get table information
            for table_name in inspector.get_table_names():
                columns = inspector.get_columns(table_name)
                primary_keys = inspector.get_pk_constraint(table_name)['constrained_columns']
                foreign_keys = inspector.get_foreign_keys(table_name)
                indexes = inspector.get_indexes(table_name)
                
                schema_info['tables'][table_name] = {
                    'columns': [
                        {
                            'name': col['name'],
                            'type': str(col['type']),
                            'nullable': col['nullable'],
                            'default': col.get('default'),
                            'autoincrement': col.get('autoincrement', False)
                        }
                        for col in columns
                    ],
                    'primary_keys': primary_keys,
                    'foreign_keys': foreign_keys,
                    'row_count': self._get_table_row_count(table_name)
                }
                
                schema_info['indexes'][table_name] = indexes
                
                # Extract relationships
                for fk in foreign_keys:
                    relationship = {
                        'source_table': table_name,
                        'source_columns': fk['constrained_columns'],
                        'target_table': fk['referred_table'],
                        'target_columns': fk['referred_columns'],
                        'constraint_name': fk['name']
                    }
                    schema_info['relationships'].append(relationship)
            
            # Get view information
            for view_name in inspector.get_view_names():
                view_definition = inspector.get_view_definition(view_name)
                schema_info['views'][view_name] = {
                    'definition': view_definition,
                    'columns': inspector.get_columns(view_name)
                }
            
            logger.info(f"Schema extraction completed for database: {self.config['database']}")
            return schema_info
            
        except Exception as e:
            logger.error(f"Failed to extract schema information: {e}")
            raise
    
    def _get_table_row_count(self, table_name: str) -> int:
        """Get approximate row count for a table"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(
                    text(f"SELECT COUNT(*) FROM `{table_name}`")
                )
                return result.scalar()
        except Exception as e:
            logger.warning(f"Could not get row count for table {table_name}: {e}")
            return 0
    
    def execute_query(self, query: str, params: Optional[Dict] = None) -> Tuple[List[str], List[Tuple]]:
        """
        Execute SQL query and return results
        
        Args:
            query: SQL query string
            params: Optional query parameters
            
        Returns:
            Tuple of (column_headers, rows)
        """
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(query), params or {})
                
                if result.returns_rows:
                    headers = list(result.keys())
                    rows = [tuple(row) for row in result.fetchall()]
                    return headers, rows
                else:
                    # For INSERT, UPDATE, DELETE operations
                    return ["Rows Affected"], [(result.rowcount,)]
                    
        except SQLAlchemyError as e:
            logger.error(f"Query execution failed: {e}")
            raise Exception(f"Database query failed: {str(e)}")
    
    def execute_query_to_dataframe(self, query: str, params: Optional[Dict] = None) -> pd.DataFrame:
        """
        Execute SQL query and return results as pandas DataFrame
        
        Args:
            query: SQL query string
            params: Optional query parameters
            
        Returns:
            pandas DataFrame with query results
        """
        try:
            df = pd.read_sql(query, self.engine, params=params)
            return df
        except Exception as e:
            logger.error(f"DataFrame query execution failed: {e}")
            raise
    
    def validate_query_syntax(self, query: str) -> Dict[str, Any]:
        """
        Validate SQL query syntax without executing it
        
        Args:
            query: SQL query to validate
            
        Returns:
            Dictionary with validation results
        """
        validation_result = {
            'is_valid': False,
            'error_message': None,
            'query_type': None,
            'affected_tables': []
        }
        
        try:
            # Use EXPLAIN to validate syntax without execution
            explain_query = f"EXPLAIN {query}"
            
            with self.engine.connect() as conn:
                result = conn.execute(text(explain_query))
                validation_result['is_valid'] = True
                
                # Determine query type
                query_upper = query.strip().upper()
                if query_upper.startswith('SELECT'):
                    validation_result['query_type'] = 'SELECT'
                elif query_upper.startswith('INSERT'):
                    validation_result['query_type'] = 'INSERT'
                elif query_upper.startswith('UPDATE'):
                    validation_result['query_type'] = 'UPDATE'
                elif query_upper.startswith('DELETE'):
                    validation_result['query_type'] = 'DELETE'
                else:
                    validation_result['query_type'] = 'OTHER'
                
                logger.info("Query syntax validation passed")
                
        except Exception as e:
            validation_result['error_message'] = str(e)
            logger.error(f"Query validation failed: {e}")
        
        return validation_result
    
    def get_sample_data(self, table_name: str, limit: int = 10) -> pd.DataFrame:
        """
        Get sample data from a table
        
        Args:
            table_name: Name of the table
            limit: Number of rows to retrieve
            
        Returns:
            pandas DataFrame with sample data
        """
        try:
            query = f"SELECT * FROM `{table_name}` LIMIT {limit}"
            return self.execute_query_to_dataframe(query)
        except Exception as e:
            logger.error(f"Failed to get sample data from {table_name}: {e}")
            raise
    
    def close(self):
        """Close database connections"""
        if self.engine:
            self.engine.dispose()
            logger.info("MySQL connections closed")


# Utility functions for database configuration
def create_mysql_config_from_env() -> Dict[str, Any]:
    """
    Create MySQL configuration from environment variables
    
    Returns:
        Configuration dictionary
    """
    return {
        'host': os.getenv('MYSQL_HOST', 'localhost'),
        'port': int(os.getenv('MYSQL_PORT', 3306)),
        'user': os.getenv('MYSQL_USER', 'root'),
        'password': os.getenv('MYSQL_PASSWORD', ''),
        'database': os.getenv('MYSQL_DATABASE', 'nl2sql_db'),
        'charset': os.getenv('MYSQL_CHARSET', 'utf8mb4')
    }


def create_mysql_config_from_url(database_url: str) -> Dict[str, Any]:
    """
    Create MySQL configuration from database URL
    
    Args:
        database_url: Database URL in format mysql://user:password@host:port/database
        
    Returns:
        Configuration dictionary
    """
    from urllib.parse import urlparse
    
    parsed = urlparse(database_url)
    
    return {
        'host': parsed.hostname or 'localhost',
        'port': parsed.port or 3306,
        'user': parsed.username or 'root',
        'password': parsed.password or '',
        'database': parsed.path.lstrip('/') if parsed.path else 'nl2sql_db',
        'charset': 'utf8mb4'
    }


# Example usage and testing
if __name__ == "__main__":
    # Load configuration from environment
    config = create_mysql_config_from_env()
    
    # Create connector instance
    mysql_conn = MySQLConnector(config)
    
    # Test connection
    test_results = mysql_conn.test_connection()
    print("Connection Test Results:", test_results)
    
    # Get schema information (if connection is successful)
    if test_results['sqlalchemy']:
        try:
            schema = mysql_conn.get_schema_info()
            print(f"Found {len(schema['tables'])} tables in database")
            for table_name in schema['tables']:
                print(f"- {table_name}: {len(schema['tables'][table_name]['columns'])} columns")
        except Exception as e:
            print(f"Schema extraction failed: {e}")
    
    # Close connections
    mysql_conn.close()
