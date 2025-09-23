# NL2SQL - Natural Language to SQL Query Generator

## 🚀 Enhanced Tech Stack Implementation

### 📋 Project Overview
A comprehensive Natural Language to SQL conversion system with multiple frontend options, robust database connectivity, and AI-powered query generation.

### 🛠️ Technology Stack

#### 1. Frontend Options
- **React.js** (Current) - Modern web interface with Tailwind CSS
- **Python Streamlit** - Alternative GUI for rapid prototyping
- **Flask Web Interface** - Server-side rendered option
- **Future Options**: Java (JSP/Servlets, Spring Boot), .NET, PHP, Ruby, Perl

#### 2. Backend Database Support
- **SQLite** (Current) - For development and testing
- **MySQL** - Primary production database
- **MongoDB** - NoSQL option for flexible schema
- **Oracle** - Enterprise database support

#### 3. Database Connectivity
- **ODBC** - Universal database connectivity via pyodbc
- **JDBC** - For Java-based frontends
- **SQLAlchemy** - Python ORM for database abstraction
- **PyMySQL** - Direct MySQL connectivity

#### 4. AI/LLM Integration
- **Google Gemini** - Primary NL to SQL conversion
- **Cohere** - Alternative LLM option
- **Enhanced Prompt Engineering** - Context-aware query generation

#### 5. Database Design Tools
- **ER Diagrams** - Entity-Relationship modeling
- **Relational Models** - Normalized schema design
- **3NF Normalization** - Third Normal Form compliance
- **Schema Validation** - Automated design verification

#### 6. Testing & Validation
- **Data Validation** - Query result accuracy testing
- **Integration Tests** - End-to-end functionality testing
- **Performance Testing** - Query optimization validation
- **Security Testing** - SQL injection prevention

### 📁 Project Structure
```
nl2sql/
├── backend/
│   ├── app.py                 # Main Flask application
│   ├── services/
│   │   ├── schema_parser.py   # Database schema analysis
│   │   ├── gemini_api.py      # Gemini LLM integration
│   │   ├── cohere_api.py      # Cohere LLM integration
│   │   ├── mysql_connector.py # MySQL connectivity
│   │   └── mongodb_connector.py # MongoDB connectivity
│   ├── utils/
│   │   ├── helpers.py         # Utility functions
│   │   ├── validators.py      # Query validation
│   │   └── db_design.py       # Database design tools
│   ├── tests/
│   │   ├── test_sql_generation.py
│   │   ├── test_db_connectivity.py
│   │   └── test_validation.py
│   ├── database_designs/
│   │   ├── er_diagrams/       # Entity-Relationship diagrams
│   │   ├── schemas/           # Database schemas
│   │   └── sample_data/       # Test datasets
│   └── requirements.txt
├── frontend/
│   ├── react-app/             # React.js frontend
│   ├── streamlit-app/         # Streamlit GUI alternative
│   └── flask-templates/       # Server-side templates
├── deployment/
│   ├── docker-compose.yml     # Multi-service deployment
│   ├── Dockerfile.backend     # Backend container
│   ├── Dockerfile.frontend    # Frontend container
│   └── nginx.conf            # Reverse proxy configuration
└── docs/
    ├── architecture.md        # System architecture
    ├── api_documentation.md   # API reference
    └── deployment_guide.md    # Deployment instructions
```

### 🔧 Installation & Setup

#### Prerequisites
- Python 3.8+
- Node.js 16+
- MySQL 8.0+
- Git

#### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

#### Frontend Setup (React)
```bash
cd frontend
npm install
npm start
```

#### Database Setup
```bash
# MySQL setup
mysql -u root -p
CREATE DATABASE nl2sql_db;
GRANT ALL PRIVILEGES ON nl2sql_db.* TO 'nl2sql_user'@'localhost';
```

### 🚀 Quick Start

1. **Clone the repository**
2. **Set up environment variables** (`.env` file)
3. **Install dependencies**
4. **Configure database connections**
5. **Run the application**

### 📊 Database Design Features

#### ER Diagram Tools
- Automated entity extraction from existing databases
- Relationship mapping and cardinality analysis
- Visual diagram generation

#### Normalization Support
- **1NF**: Eliminate repeating groups
- **2NF**: Remove partial dependencies
- **3NF**: Eliminate transitive dependencies
- Automated normalization suggestions

### 🧪 Testing Framework

#### Data Validation Tests
```python
# Example test structure
def test_query_accuracy():
    natural_language = "Show me all customers from New York"
    expected_sql = "SELECT * FROM customers WHERE city = 'New York'"
    generated_sql = generate_sql(natural_language)
    assert validate_sql_equivalence(expected_sql, generated_sql)
```

#### Integration Tests
- End-to-end workflow testing
- Database connectivity validation
- API endpoint testing
- Frontend-backend integration

### 🔒 Security Features
- SQL injection prevention
- Input sanitization
- Query parameter validation
- Rate limiting
- Authentication & authorization (planned)

### 📈 Performance Optimization
- Query execution time monitoring
- Database indexing recommendations
- Caching strategies
- Connection pooling

### 🌟 Advanced Features

#### Multi-Database Support
- Seamless switching between database types
- Schema translation between different DB systems
- Unified query interface

#### AI Enhancement
- Context-aware query generation
- Learning from user feedback
- Query optimization suggestions
- Natural language explanation of SQL queries

### 📚 API Documentation

#### Core Endpoints
- `POST /api/schema` - Extract database schema
- `POST /api/generate-sql` - Generate SQL from natural language
- `POST /api/execute-sql` - Execute SQL queries
- `POST /api/validate-query` - Validate SQL syntax
- `GET /api/supported-databases` - List supported database types

### 🤝 Contributing
1. Fork the repository
2. Create a feature branch
3. Implement your enhancement
4. Add comprehensive tests
5. Submit a pull request

### 📄 License
MIT License - see LICENSE file for details

### 🆘 Support
For issues and questions:
- Create an issue on GitHub
- Check the documentation
- Review the API reference

---

**Version**: 2.0.0  
**Last Updated**: January 2025  
**Maintainer**: SAKSHAM NILAJKAR