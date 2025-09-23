"""
Database Design and Normalization Utilities
Provides tools for ER diagram generation, normalization analysis, and schema design
"""

import os
import json
import logging
from typing import Dict, List, Tuple, Set, Any, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter
import sqlite3
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class Column:
    """Represents a database column"""
    name: str
    data_type: str
    nullable: bool = True
    primary_key: bool = False
    foreign_key: Optional[str] = None  # Format: "table.column"
    unique: bool = False
    default_value: Any = None
    description: str = ""


@dataclass
class Table:
    """Represents a database table"""
    name: str
    columns: List[Column]
    primary_keys: List[str]
    foreign_keys: List[Dict[str, str]]  # [{source_col: str, target_table: str, target_col: str}]
    indexes: List[str] = None
    description: str = ""
    
    def __post_init__(self):
        if self.indexes is None:
            self.indexes = []


@dataclass
class Relationship:
    """Represents a relationship between tables"""
    source_table: str
    target_table: str
    source_columns: List[str]
    target_columns: List[str]
    relationship_type: str  # "one-to-one", "one-to-many", "many-to-many"
    constraint_name: str = ""


@dataclass
class DatabaseSchema:
    """Represents a complete database schema"""
    name: str
    tables: List[Table]
    relationships: List[Relationship]
    views: List[Dict[str, Any]] = None
    indexes: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.views is None:
            self.views = []
        if self.indexes is None:
            self.indexes = []


class DatabaseDesignAnalyzer:
    """Analyzes and designs database schemas with normalization support"""
    
    def __init__(self):
        self.design_patterns = {
            'user_management': {
                'tables': ['users', 'roles', 'permissions', 'user_roles'],
                'description': 'Standard user management pattern'
            },
            'e_commerce': {
                'tables': ['customers', 'products', 'orders', 'order_items', 'categories'],
                'description': 'E-commerce domain pattern'
            },
            'blog_cms': {
                'tables': ['users', 'posts', 'categories', 'comments', 'tags', 'post_tags'],
                'description': 'Blog/CMS content management pattern'
            }
        }
    
    def analyze_existing_database(self, db_path: str) -> DatabaseSchema:
        """
        Analyze existing database and extract schema information
        
        Args:
            db_path: Path to database file
            
        Returns:
            DatabaseSchema object with extracted information
        """
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            table_names = [row[0] for row in cursor.fetchall()]
            
            tables = []
            relationships = []
            
            for table_name in table_names:
                # Get table schema
                cursor.execute(f"PRAGMA table_info({table_name});")
                columns_info = cursor.fetchall()
                
                # Get foreign keys
                cursor.execute(f"PRAGMA foreign_key_list({table_name});")
                fk_info = cursor.fetchall()
                
                # Create Column objects
                columns = []
                primary_keys = []
                foreign_keys = []
                
                for col_info in columns_info:
                    col_id, name, data_type, not_null, default_val, pk = col_info
                    
                    column = Column(
                        name=name,
                        data_type=data_type,
                        nullable=not not_null,
                        primary_key=bool(pk),
                        default_value=default_val
                    )
                    
                    columns.append(column)
                    
                    if pk:
                        primary_keys.append(name)
                
                # Process foreign keys
                for fk in fk_info:
                    fk_id, seq, target_table, source_col, target_col, on_update, on_delete, match = fk
                    foreign_keys.append({
                        'source_column': source_col,
                        'target_table': target_table,
                        'target_column': target_col
                    })
                    
                    # Mark column as foreign key
                    for col in columns:
                        if col.name == source_col:
                            col.foreign_key = f"{target_table}.{target_col}"
                    
                    # Create relationship
                    relationship = Relationship(
                        source_table=table_name,
                        target_table=target_table,
                        source_columns=[source_col],
                        target_columns=[target_col],
                        relationship_type="many-to-one",  # Default assumption
                        constraint_name=f"fk_{table_name}_{source_col}"
                    )
                    relationships.append(relationship)
                
                # Create Table object
                table = Table(
                    name=table_name,
                    columns=columns,
                    primary_keys=primary_keys,
                    foreign_keys=foreign_keys
                )
                tables.append(table)
            
            conn.close()
            
            schema = DatabaseSchema(
                name=os.path.basename(db_path).replace('.db', ''),
                tables=tables,
                relationships=relationships
            )
            
            logger.info(f"Analyzed database schema: {len(tables)} tables, {len(relationships)} relationships")
            return schema
            
        except Exception as e:
            logger.error(f"Failed to analyze database: {e}")
            raise
    
    def check_normalization_level(self, schema: DatabaseSchema) -> Dict[str, Any]:
        """
        Analyze schema for normalization level (1NF, 2NF, 3NF)
        
        Args:
            schema: DatabaseSchema to analyze
            
        Returns:
            Dictionary with normalization analysis
        """
        analysis = {
            'first_normal_form': {'compliant': True, 'violations': []},
            'second_normal_form': {'compliant': True, 'violations': []},
            'third_normal_form': {'compliant': True, 'violations': []},
            'recommendations': []
        }
        
        for table in schema.tables:
            # Check 1NF: No repeating groups, atomic values
            for column in table.columns:
                if any(keyword in column.name.lower() for keyword in ['json', 'array', 'list', 'multi']):
                    analysis['first_normal_form']['violations'].append({
                        'table': table.name,
                        'column': column.name,
                        'issue': 'Potential non-atomic values'
                    })
                    analysis['first_normal_form']['compliant'] = False
            
            # Check 2NF: Full functional dependency on primary key
            if len(table.primary_keys) > 1:  # Composite primary key
                non_key_columns = [col for col in table.columns if col.name not in table.primary_keys]
                for col in non_key_columns:
                    # This is a simplified check - in practice, would need dependency analysis
                    if col.name.startswith(table.primary_keys[0].split('_')[0]):
                        analysis['second_normal_form']['violations'].append({
                            'table': table.name,
                            'column': col.name,
                            'issue': 'Partial dependency on composite key'
                        })
                        analysis['second_normal_form']['compliant'] = False
            
            # Check 3NF: No transitive dependencies
            # Look for columns that might depend on non-key columns
            for col1 in table.columns:
                for col2 in table.columns:
                    if (col1 != col2 and 
                        not col1.primary_key and not col2.primary_key and
                        col1.name.replace('_id', '') in col2.name):
                        analysis['third_normal_form']['violations'].append({
                            'table': table.name,
                            'columns': [col1.name, col2.name],
                            'issue': 'Potential transitive dependency'
                        })
                        analysis['third_normal_form']['compliant'] = False
        
        # Generate recommendations
        if not analysis['first_normal_form']['compliant']:
            analysis['recommendations'].append("Split non-atomic values into separate columns or tables")
        
        if not analysis['second_normal_form']['compliant']:
            analysis['recommendations'].append("Move partially dependent columns to separate tables")
        
        if not analysis['third_normal_form']['compliant']:
            analysis['recommendations'].append("Remove transitive dependencies by creating lookup tables")
        
        return analysis
    
    def generate_normalized_schema(self, schema: DatabaseSchema) -> DatabaseSchema:
        """
        Generate a normalized version of the schema
        
        Args:
            schema: Original schema to normalize
            
        Returns:
            Normalized DatabaseSchema
        """
        normalized_tables = []
        normalized_relationships = []
        
        for table in schema.tables:
            # Start with the original table
            normalized_table = Table(
                name=table.name,
                columns=table.columns.copy(),
                primary_keys=table.primary_keys.copy(),
                foreign_keys=table.foreign_keys.copy(),
                description=table.description + " (normalized)"
            )
            
            # Identify potential normalization improvements
            lookup_tables = self._identify_lookup_tables(table)
            
            for lookup_table_name, lookup_columns in lookup_tables.items():
                # Create lookup table
                lookup_table = Table(
                    name=lookup_table_name,
                    columns=[
                        Column(name="id", data_type="INTEGER", primary_key=True, nullable=False),
                        *lookup_columns
                    ],
                    primary_keys=["id"],
                    foreign_keys=[],
                    description=f"Lookup table for {table.name}"
                )
                normalized_tables.append(lookup_table)
                
                # Add foreign key to main table
                fk_column = Column(
                    name=f"{lookup_table_name}_id",
                    data_type="INTEGER",
                    foreign_key=f"{lookup_table_name}.id"
                )
                
                # Remove original columns and add FK
                normalized_table.columns = [
                    col for col in normalized_table.columns 
                    if col.name not in [lc.name for lc in lookup_columns]
                ]
                normalized_table.columns.append(fk_column)
                
                # Create relationship
                relationship = Relationship(
                    source_table=table.name,
                    target_table=lookup_table_name,
                    source_columns=[fk_column.name],
                    target_columns=["id"],
                    relationship_type="many-to-one"
                )
                normalized_relationships.append(relationship)
            
            normalized_tables.append(normalized_table)
        
        return DatabaseSchema(
            name=schema.name + "_normalized",
            tables=normalized_tables,
            relationships=schema.relationships + normalized_relationships
        )
    
    def _identify_lookup_tables(self, table: Table) -> Dict[str, List[Column]]:
        """Identify columns that should be moved to lookup tables"""
        lookup_tables = {}
        
        # Look for columns with enum-like patterns
        enum_patterns = ['status', 'type', 'category', 'level', 'priority']
        
        for column in table.columns:
            for pattern in enum_patterns:
                if pattern in column.name.lower() and not column.primary_key:
                    lookup_table_name = f"{table.name}_{pattern}s"
                    if lookup_table_name not in lookup_tables:
                        lookup_tables[lookup_table_name] = []
                    
                    lookup_tables[lookup_table_name].append(
                        Column(
                            name=pattern,
                            data_type=column.data_type,
                            description=f"{pattern.title()} values"
                        )
                    )
        
        return lookup_tables
    
    def generate_er_diagram_dot(self, schema: DatabaseSchema) -> str:
        """
        Generate DOT notation for ER diagram visualization
        
        Args:
            schema: Database schema to visualize
            
        Returns:
            DOT notation string
        """
        dot_content = f"""
digraph ER_Diagram {{
    rankdir=TB;
    node [shape=plaintext];
    
    // Title
    title [label=<<B>{schema.name} ER Diagram</B>>, shape=plaintext, fontsize=16];
    
"""
        
        # Generate table nodes
        for table in schema.tables:
            dot_content += f"""
    // Table: {table.name}
    {table.name} [label=<
        <TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0">
            <TR><TD BGCOLOR="lightblue"><B>{table.name.upper()}</B></TD></TR>
"""
            
            for column in table.columns:
                key_indicator = ""
                if column.primary_key:
                    key_indicator = " [PK]"
                elif column.foreign_key:
                    key_indicator = " [FK]"
                
                dot_content += f'            <TR><TD ALIGN="LEFT">{column.name} ({column.data_type}){key_indicator}</TD></TR>\n'
            
            dot_content += """        </TABLE>
    >];
"""
        
        # Generate relationships
        for relationship in schema.relationships:
            relationship_label = relationship.relationship_type.replace('-', '\\n')
            dot_content += f"""
    {relationship.source_table} -> {relationship.target_table} [label="{relationship_label}"];
"""
        
        dot_content += "\n}"
        
        return dot_content
    
    def export_schema_to_sql(self, schema: DatabaseSchema, dialect: str = "mysql") -> str:
        """
        Export schema as SQL CREATE statements
        
        Args:
            schema: Database schema to export
            dialect: SQL dialect ("mysql", "postgresql", "sqlite")
            
        Returns:
            SQL CREATE statements
        """
        sql_statements = []
        
        # Add header comment
        sql_statements.append(f"-- Database Schema: {schema.name}")
        sql_statements.append(f"-- Generated for {dialect.upper()}")
        sql_statements.append(f"-- Tables: {len(schema.tables)}")
        sql_statements.append("")
        
        # Type mapping for different dialects
        type_mapping = {
            'mysql': {
                'INTEGER': 'INT',
                'TEXT': 'TEXT',
                'REAL': 'DECIMAL(10,2)',
                'BLOB': 'BLOB',
                'VARCHAR': 'VARCHAR'
            },
            'postgresql': {
                'INTEGER': 'INTEGER',
                'TEXT': 'TEXT',
                'REAL': 'DECIMAL',
                'BLOB': 'BYTEA',
                'VARCHAR': 'VARCHAR'
            },
            'sqlite': {
                'INTEGER': 'INTEGER',
                'TEXT': 'TEXT',
                'REAL': 'REAL',
                'BLOB': 'BLOB',
                'VARCHAR': 'TEXT'
            }
        }
        
        mapping = type_mapping.get(dialect, type_mapping['mysql'])
        
        # Create tables
        for table in schema.tables:
            sql_statements.append(f"-- Table: {table.name}")
            if table.description:
                sql_statements.append(f"-- {table.description}")
            
            create_stmt = f"CREATE TABLE {table.name} (\n"
            
            column_definitions = []
            for column in table.columns:
                col_def = f"    {column.name} {mapping.get(column.data_type, column.data_type)}"
                
                if not column.nullable:
                    col_def += " NOT NULL"
                
                if column.default_value is not None:
                    if isinstance(column.default_value, str):
                        col_def += f" DEFAULT '{column.default_value}'"
                    else:
                        col_def += f" DEFAULT {column.default_value}"
                
                if column.unique:
                    col_def += " UNIQUE"
                
                column_definitions.append(col_def)
            
            # Add primary key constraint
            if table.primary_keys:
                pk_constraint = f"    PRIMARY KEY ({', '.join(table.primary_keys)})"
                column_definitions.append(pk_constraint)
            
            create_stmt += ",\n".join(column_definitions) + "\n);\n"
            sql_statements.append(create_stmt)
        
        # Add foreign key constraints
        for table in schema.tables:
            for fk in table.foreign_keys:
                alter_stmt = (
                    f"ALTER TABLE {table.name} "
                    f"ADD FOREIGN KEY ({fk['source_column']}) "
                    f"REFERENCES {fk['target_table']}({fk['target_column']});"
                )
                sql_statements.append(alter_stmt)
        
        return "\n".join(sql_statements)
    
    def save_schema_documentation(self, schema: DatabaseSchema, output_dir: str):
        """
        Save comprehensive schema documentation
        
        Args:
            schema: Database schema to document
            output_dir: Directory to save documentation
        """
        os.makedirs(output_dir, exist_ok=True)
        
        # Save JSON representation
        schema_dict = {
            'name': schema.name,
            'tables': [asdict(table) for table in schema.tables],
            'relationships': [asdict(rel) for rel in schema.relationships],
            'views': schema.views,
            'indexes': schema.indexes
        }
        
        json_path = os.path.join(output_dir, f"{schema.name}_schema.json")
        with open(json_path, 'w') as f:
            json.dump(schema_dict, f, indent=2)
        
        # Save ER diagram DOT file
        dot_content = self.generate_er_diagram_dot(schema)
        dot_path = os.path.join(output_dir, f"{schema.name}_er_diagram.dot")
        with open(dot_path, 'w', encoding='utf-8') as f:
            f.write(dot_content)
        
        # Save SQL export
        for dialect in ['mysql', 'postgresql', 'sqlite']:
            sql_content = self.export_schema_to_sql(schema, dialect)
            sql_path = os.path.join(output_dir, f"{schema.name}_{dialect}.sql")
            with open(sql_path, 'w') as f:
                f.write(sql_content)
        
        # Save normalization analysis
        normalization_analysis = self.check_normalization_level(schema)
        analysis_path = os.path.join(output_dir, f"{schema.name}_normalization_analysis.json")
        with open(analysis_path, 'w') as f:
            json.dump(normalization_analysis, f, indent=2)
        
        logger.info(f"Schema documentation saved to {output_dir}")


# Sample database schemas for demonstration
def create_sample_ecommerce_schema() -> DatabaseSchema:
    """Create a sample e-commerce database schema"""
    
    # Define tables
    customers = Table(
        name="customers",
        columns=[
            Column("id", "INTEGER", primary_key=True, nullable=False),
            Column("email", "VARCHAR(255)", nullable=False, unique=True),
            Column("first_name", "VARCHAR(100)", nullable=False),
            Column("last_name", "VARCHAR(100)", nullable=False),
            Column("phone", "VARCHAR(20)"),
            Column("created_at", "TIMESTAMP", nullable=False),
            Column("updated_at", "TIMESTAMP")
        ],
        primary_keys=["id"],
        foreign_keys=[],
        description="Customer information"
    )
    
    categories = Table(
        name="categories",
        columns=[
            Column("id", "INTEGER", primary_key=True, nullable=False),
            Column("name", "VARCHAR(100)", nullable=False, unique=True),
            Column("description", "TEXT"),
            Column("parent_id", "INTEGER", foreign_key="categories.id")
        ],
        primary_keys=["id"],
        foreign_keys=[{"source_column": "parent_id", "target_table": "categories", "target_column": "id"}],
        description="Product categories"
    )
    
    products = Table(
        name="products",
        columns=[
            Column("id", "INTEGER", primary_key=True, nullable=False),
            Column("name", "VARCHAR(200)", nullable=False),
            Column("description", "TEXT"),
            Column("price", "DECIMAL(10,2)", nullable=False),
            Column("category_id", "INTEGER", foreign_key="categories.id"),
            Column("stock_quantity", "INTEGER", nullable=False, default_value=0),
            Column("created_at", "TIMESTAMP", nullable=False),
            Column("updated_at", "TIMESTAMP")
        ],
        primary_keys=["id"],
        foreign_keys=[{"source_column": "category_id", "target_table": "categories", "target_column": "id"}],
        description="Product catalog"
    )
    
    orders = Table(
        name="orders",
        columns=[
            Column("id", "INTEGER", primary_key=True, nullable=False),
            Column("customer_id", "INTEGER", foreign_key="customers.id", nullable=False),
            Column("order_date", "TIMESTAMP", nullable=False),
            Column("status", "VARCHAR(50)", nullable=False),
            Column("total_amount", "DECIMAL(10,2)", nullable=False),
            Column("shipping_address", "TEXT"),
            Column("billing_address", "TEXT")
        ],
        primary_keys=["id"],
        foreign_keys=[{"source_column": "customer_id", "target_table": "customers", "target_column": "id"}],
        description="Customer orders"
    )
    
    order_items = Table(
        name="order_items",
        columns=[
            Column("id", "INTEGER", primary_key=True, nullable=False),
            Column("order_id", "INTEGER", foreign_key="orders.id", nullable=False),
            Column("product_id", "INTEGER", foreign_key="products.id", nullable=False),
            Column("quantity", "INTEGER", nullable=False),
            Column("unit_price", "DECIMAL(10,2)", nullable=False),
            Column("total_price", "DECIMAL(10,2)", nullable=False)
        ],
        primary_keys=["id"],
        foreign_keys=[
            {"source_column": "order_id", "target_table": "orders", "target_column": "id"},
            {"source_column": "product_id", "target_table": "products", "target_column": "id"}
        ],
        description="Individual items within orders"
    )
    
    # Define relationships
    relationships = [
        Relationship("customers", "orders", ["id"], ["customer_id"], "one-to-many"),
        Relationship("categories", "products", ["id"], ["category_id"], "one-to-many"),
        Relationship("categories", "categories", ["id"], ["parent_id"], "one-to-many"),
        Relationship("orders", "order_items", ["id"], ["order_id"], "one-to-many"),
        Relationship("products", "order_items", ["id"], ["product_id"], "one-to-many")
    ]
    
    return DatabaseSchema(
        name="ecommerce_system",
        tables=[customers, categories, products, orders, order_items],
        relationships=relationships
    )


if __name__ == "__main__":
    # Example usage
    analyzer = DatabaseDesignAnalyzer()
    
    # Create sample e-commerce schema
    ecommerce_schema = create_sample_ecommerce_schema()
    
    # Analyze normalization
    normalization_analysis = analyzer.check_normalization_level(ecommerce_schema)
    print("Normalization Analysis:")
    print(f"1NF Compliant: {normalization_analysis['first_normal_form']['compliant']}")
    print(f"2NF Compliant: {normalization_analysis['second_normal_form']['compliant']}")
    print(f"3NF Compliant: {normalization_analysis['third_normal_form']['compliant']}")
    
    # Generate ER diagram
    er_diagram = analyzer.generate_er_diagram_dot(ecommerce_schema)
    print("\nER Diagram (DOT format):")
    print(er_diagram[:500] + "..." if len(er_diagram) > 500 else er_diagram)
    
    # Export to SQL
    mysql_sql = analyzer.export_schema_to_sql(ecommerce_schema, "mysql")
    print(f"\nMySQL Schema (first 500 chars):")
    print(mysql_sql[:500] + "..." if len(mysql_sql) > 500 else mysql_sql)
