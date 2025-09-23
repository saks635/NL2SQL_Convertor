"""
MongoDB Database Connector Service
Provides MongoDB connectivity and document-to-SQL conversion capabilities
"""

import os
import logging
from typing import Dict, List, Tuple, Optional, Any, Union
import pymongo
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure
import pandas as pd
from bson import ObjectId
import json
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MongoDBConnector:
    """Enhanced MongoDB connector with document analysis capabilities"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize MongoDB connector with configuration
        
        Args:
            config: Dictionary containing database configuration
                   {
                       'host': 'localhost',
                       'port': 27017,
                       'username': 'username',
                       'password': 'password',
                       'database': 'database_name',
                       'auth_database': 'admin'
                   }
        """
        self.config = config
        self.client = None
        self.database = None
        self._init_connection()
    
    def _init_connection(self):
        """Initialize MongoDB connection"""
        try:
            # Build connection URI
            if self.config.get('username') and self.config.get('password'):
                connection_uri = (
                    f"mongodb://{self.config['username']}:{self.config['password']}"
                    f"@{self.config['host']}:{self.config.get('port', 27017)}"
                    f"/{self.config.get('auth_database', 'admin')}"
                )
            else:
                connection_uri = f"mongodb://{self.config['host']}:{self.config.get('port', 27017)}"
            
            self.client = MongoClient(
                connection_uri,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000,
                socketTimeoutMS=5000
            )
            
            self.database = self.client[self.config['database']]
            logger.info("MongoDB connection initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize MongoDB connection: {e}")
            raise
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Test MongoDB connection
        
        Returns:
            Dictionary with connection test results
        """
        results = {
            'connection': False,
            'database_access': False,
            'error': None
        }
        
        try:
            # Test basic connection
            self.client.admin.command('ismaster')
            results['connection'] = True
            logger.info("MongoDB connection test passed")
            
            # Test database access
            collections = self.database.list_collection_names()
            results['database_access'] = True
            results['collections_count'] = len(collections)
            logger.info(f"Database access test passed. Found {len(collections)} collections")
            
        except ConnectionFailure as e:
            results['error'] = f"Connection failed: {str(e)}"
            logger.error(f"MongoDB connection failed: {e}")
        except Exception as e:
            results['error'] = str(e)
            logger.error(f"MongoDB test failed: {e}")
        
        return results
    
    def get_schema_info(self) -> Dict[str, Any]:
        """
        Extract schema information from MongoDB collections
        
        Returns:
            Dictionary containing database schema information
        """
        schema_info = {
            'database_name': self.config['database'],
            'collections': {},
            'total_documents': 0,
            'indexes': {}
        }
        
        try:
            collection_names = self.database.list_collection_names()
            
            for collection_name in collection_names:
                collection = self.database[collection_name]
                
                # Get collection stats
                stats = self.database.command("collStats", collection_name)
                document_count = stats.get('count', 0)
                
                # Analyze document structure by sampling
                sample_docs = list(collection.find().limit(100))
                field_analysis = self._analyze_document_structure(sample_docs)
                
                # Get indexes
                indexes = list(collection.list_indexes())
                
                schema_info['collections'][collection_name] = {
                    'document_count': document_count,
                    'size_bytes': stats.get('size', 0),
                    'fields': field_analysis,
                    'indexes': indexes,
                    'sample_document': sample_docs[0] if sample_docs else None
                }
                
                schema_info['total_documents'] += document_count
                schema_info['indexes'][collection_name] = indexes
            
            logger.info(f"Schema extraction completed for database: {self.config['database']}")
            return schema_info
            
        except Exception as e:
            logger.error(f"Failed to extract schema information: {e}")
            raise
    
    def _analyze_document_structure(self, documents: List[Dict]) -> Dict[str, Any]:
        """
        Analyze document structure to understand field types and patterns
        
        Args:
            documents: List of sample documents
            
        Returns:
            Dictionary with field analysis
        """
        field_stats = {}
        
        for doc in documents:
            self._analyze_document_fields(doc, field_stats, "")
        
        # Calculate field statistics
        total_docs = len(documents)
        field_analysis = {}
        
        for field_path, stats in field_stats.items():
            field_analysis[field_path] = {
                'types': list(stats['types'].keys()),
                'frequency': stats['count'] / total_docs if total_docs > 0 else 0,
                'null_count': stats['null_count'],
                'sample_values': list(stats['sample_values'])[:5]
            }
        
        return field_analysis
    
    def _analyze_document_fields(self, doc: Dict, field_stats: Dict, prefix: str):
        """Recursively analyze document fields"""
        if not isinstance(doc, dict):
            return
        
        for key, value in doc.items():
            field_path = f"{prefix}.{key}" if prefix else key
            
            if field_path not in field_stats:
                field_stats[field_path] = {
                    'types': {},
                    'count': 0,
                    'null_count': 0,
                    'sample_values': set()
                }
            
            field_stats[field_path]['count'] += 1
            
            if value is None:
                field_stats[field_path]['null_count'] += 1
                value_type = 'null'
            else:
                value_type = type(value).__name__
                
                # Add sample values (limit to avoid memory issues)
                if len(field_stats[field_path]['sample_values']) < 10:
                    if isinstance(value, (str, int, float, bool)):
                        field_stats[field_path]['sample_values'].add(str(value))
                    elif isinstance(value, datetime):
                        field_stats[field_path]['sample_values'].add(value.isoformat())
                    elif isinstance(value, ObjectId):
                        field_stats[field_path]['sample_values'].add(str(value))
            
            # Track type frequency
            if value_type not in field_stats[field_path]['types']:
                field_stats[field_path]['types'][value_type] = 0
            field_stats[field_path]['types'][value_type] += 1
            
            # Recursively analyze nested documents
            if isinstance(value, dict):
                self._analyze_document_fields(value, field_stats, field_path)
            elif isinstance(value, list) and len(value) > 0 and isinstance(value[0], dict):
                # Analyze first element of array if it's a document
                self._analyze_document_fields(value[0], field_stats, f"{field_path}[]")
    
    def execute_aggregation(self, collection_name: str, pipeline: List[Dict]) -> List[Dict]:
        """
        Execute MongoDB aggregation pipeline
        
        Args:
            collection_name: Name of the collection
            pipeline: Aggregation pipeline
            
        Returns:
            List of aggregation results
        """
        try:
            collection = self.database[collection_name]
            results = list(collection.aggregate(pipeline))
            
            # Convert ObjectIds to strings for JSON serialization
            for result in results:
                self._convert_objectids_to_strings(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Aggregation execution failed: {e}")
            raise Exception(f"MongoDB aggregation failed: {str(e)}")
    
    def find_documents(self, collection_name: str, query: Dict = None, 
                      projection: Dict = None, limit: int = 100) -> List[Dict]:
        """
        Find documents in a collection
        
        Args:
            collection_name: Name of the collection
            query: MongoDB query filter
            projection: Fields to include/exclude
            limit: Maximum number of documents to return
            
        Returns:
            List of documents
        """
        try:
            collection = self.database[collection_name]
            cursor = collection.find(query or {}, projection)
            
            if limit:
                cursor = cursor.limit(limit)
            
            documents = list(cursor)
            
            # Convert ObjectIds to strings
            for doc in documents:
                self._convert_objectids_to_strings(doc)
            
            return documents
            
        except Exception as e:
            logger.error(f"Document query failed: {e}")
            raise Exception(f"MongoDB query failed: {str(e)}")
    
    def _convert_objectids_to_strings(self, obj):
        """Recursively convert ObjectIds to strings for JSON serialization"""
        if isinstance(obj, dict):
            for key, value in obj.items():
                obj[key] = self._convert_objectids_to_strings(value)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                obj[i] = self._convert_objectids_to_strings(item)
        elif isinstance(obj, ObjectId):
            return str(obj)
        elif isinstance(obj, datetime):
            return obj.isoformat()
        return obj
    
    def convert_to_relational_format(self, collection_name: str, 
                                   flatten_nested: bool = True) -> pd.DataFrame:
        """
        Convert MongoDB collection to relational format (DataFrame)
        
        Args:
            collection_name: Name of the collection
            flatten_nested: Whether to flatten nested documents
            
        Returns:
            pandas DataFrame
        """
        try:
            documents = self.find_documents(collection_name, limit=1000)
            
            if not documents:
                return pd.DataFrame()
            
            if flatten_nested:
                # Flatten nested documents
                flattened_docs = []
                for doc in documents:
                    flattened = self._flatten_document(doc)
                    flattened_docs.append(flattened)
                documents = flattened_docs
            
            df = pd.DataFrame(documents)
            return df
            
        except Exception as e:
            logger.error(f"Failed to convert collection to relational format: {e}")
            raise
    
    def _flatten_document(self, doc: Dict, parent_key: str = '', sep: str = '.') -> Dict:
        """
        Flatten nested document structure
        
        Args:
            doc: Document to flatten
            parent_key: Parent key for nested fields
            sep: Separator for nested field names
            
        Returns:
            Flattened document
        """
        items = []
        for key, value in doc.items():
            new_key = f"{parent_key}{sep}{key}" if parent_key else key
            
            if isinstance(value, dict):
                items.extend(self._flatten_document(value, new_key, sep).items())
            elif isinstance(value, list):
                # Handle arrays - for simplicity, convert to string representation
                items.append((new_key, str(value)))
            else:
                items.append((new_key, value))
        
        return dict(items)
    
    def generate_sql_equivalent_schema(self, collection_name: str) -> Dict[str, Any]:
        """
        Generate SQL-equivalent schema for a MongoDB collection
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            Dictionary with SQL-equivalent table schema
        """
        try:
            schema_info = self.get_schema_info()
            collection_info = schema_info['collections'].get(collection_name, {})
            fields = collection_info.get('fields', {})
            
            sql_schema = {
                'table_name': collection_name,
                'columns': []
            }
            
            for field_path, field_info in fields.items():
                # Map MongoDB types to SQL types
                mongodb_types = field_info['types']
                sql_type = self._map_mongodb_type_to_sql(mongodb_types)
                
                column_info = {
                    'name': field_path.replace('.', '_'),  # Replace dots with underscores
                    'type': sql_type,
                    'nullable': field_info['frequency'] < 1.0,  # If not in all documents
                    'mongodb_path': field_path
                }
                
                sql_schema['columns'].append(column_info)
            
            return sql_schema
            
        except Exception as e:
            logger.error(f"Failed to generate SQL schema: {e}")
            raise
    
    def _map_mongodb_type_to_sql(self, mongodb_types: List[str]) -> str:
        """
        Map MongoDB field types to SQL data types
        
        Args:
            mongodb_types: List of MongoDB types found for the field
            
        Returns:
            SQL data type string
        """
        # Priority mapping - more specific types take precedence
        type_priority = {
            'ObjectId': 'VARCHAR(24)',
            'str': 'TEXT',
            'int': 'INTEGER',
            'float': 'DECIMAL(10,2)',
            'bool': 'BOOLEAN',
            'datetime': 'TIMESTAMP',
            'list': 'JSON',
            'dict': 'JSON',
            'null': 'TEXT'
        }
        
        for mongo_type in ['ObjectId', 'datetime', 'int', 'float', 'bool', 'str', 'dict', 'list']:
            if mongo_type in mongodb_types:
                return type_priority[mongo_type]
        
        return 'TEXT'  # Default fallback
    
    def create_aggregation_for_sql_query(self, sql_like_query: Dict[str, Any]) -> List[Dict]:
        """
        Convert SQL-like query parameters to MongoDB aggregation pipeline
        
        Args:
            sql_like_query: Dictionary with SQL-like query structure
                          {
                              'select': ['field1', 'field2'],
                              'where': {'field': 'value'},
                              'limit': 100,
                              'sort': {'field': 1}
                          }
        
        Returns:
            MongoDB aggregation pipeline
        """
        pipeline = []
        
        # Add match stage (WHERE equivalent)
        if sql_like_query.get('where'):
            pipeline.append({"$match": sql_like_query['where']})
        
        # Add projection stage (SELECT equivalent)
        if sql_like_query.get('select'):
            projection = {field: 1 for field in sql_like_query['select']}
            pipeline.append({"$project": projection})
        
        # Add sort stage (ORDER BY equivalent)
        if sql_like_query.get('sort'):
            pipeline.append({"$sort": sql_like_query['sort']})
        
        # Add limit stage
        if sql_like_query.get('limit'):
            pipeline.append({"$limit": sql_like_query['limit']})
        
        return pipeline
    
    def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")


# Utility functions for MongoDB configuration
def create_mongodb_config_from_env() -> Dict[str, Any]:
    """
    Create MongoDB configuration from environment variables
    
    Returns:
        Configuration dictionary
    """
    return {
        'host': os.getenv('MONGODB_HOST', 'localhost'),
        'port': int(os.getenv('MONGODB_PORT', 27017)),
        'username': os.getenv('MONGODB_USERNAME'),
        'password': os.getenv('MONGODB_PASSWORD'),
        'database': os.getenv('MONGODB_DATABASE', 'nl2sql_db'),
        'auth_database': os.getenv('MONGODB_AUTH_DATABASE', 'admin')
    }


def create_mongodb_config_from_uri(mongodb_uri: str) -> Dict[str, Any]:
    """
    Create MongoDB configuration from connection URI
    
    Args:
        mongodb_uri: MongoDB connection URI
        
    Returns:
        Configuration dictionary
    """
    from urllib.parse import urlparse
    
    parsed = urlparse(mongodb_uri)
    
    return {
        'host': parsed.hostname or 'localhost',
        'port': parsed.port or 27017,
        'username': parsed.username,
        'password': parsed.password,
        'database': parsed.path.lstrip('/') if parsed.path else 'nl2sql_db',
        'auth_database': 'admin'
    }


# Example usage and testing
if __name__ == "__main__":
    # Load configuration from environment
    config = create_mongodb_config_from_env()
    
    # Create connector instance
    mongo_conn = MongoDBConnector(config)
    
    # Test connection
    test_results = mongo_conn.test_connection()
    print("Connection Test Results:", test_results)
    
    # Get schema information (if connection is successful)
    if test_results['connection']:
        try:
            schema = mongo_conn.get_schema_info()
            print(f"Found {len(schema['collections'])} collections in database")
            for collection_name in schema['collections']:
                collection_info = schema['collections'][collection_name]
                print(f"- {collection_name}: {collection_info['document_count']} documents, "
                      f"{len(collection_info['fields'])} unique fields")
        except Exception as e:
            print(f"Schema extraction failed: {e}")
    
    # Close connections
    mongo_conn.close()
