import React, { useState, useEffect } from 'react';
import axios from 'axios';

import QueryForm from './components/QueryForm';
import SchemaViewer from './components/SchemaViewer';
import SqlEditor from './components/SqlEditor';
import ResultDisplay from './components/ResultDisplay';
import HistoryPanel from './components/HistoryPanel';
import DatabaseSelector from './components/DatabaseSelector';

function App() {
  // Enhanced state management for multi-database support
  const [dbType, setDbType] = useState('sqlite'); // 'sqlite', 'mysql', 'mongodb'
  const [dbFile, setDbFile] = useState(null);
  const [schema, setSchema] = useState(null);
  const [question, setQuestion] = useState('');
  const [generatedSql, setGeneratedSql] = useState('');
  const [queryResult, setQueryResult] = useState(null);
  const [history, setHistory] = useState([]);
  const [availableDatabases, setAvailableDatabases] = useState([]);
  const [systemHealth, setSystemHealth] = useState(null);

  // States for loading and errors
  const [loading, setLoading] = useState({ 
    schema: false, 
    sql: false, 
    execution: false,
    health: false 
  });
  const [error, setError] = useState({ 
    schema: '', 
    sql: '', 
    execution: '',
    health: '' 
  });

  // Load system health and available databases on mount
  useEffect(() => {
    checkSystemHealth();
    loadAvailableDatabases();
    
    // Load history from localStorage
    const savedHistory = localStorage.getItem('nl2sql-history');
    if (savedHistory) {
      setHistory(JSON.parse(savedHistory));
    }
  }, []);

  // Check system health and database connectivity
  const checkSystemHealth = async () => {
    setLoading(prev => ({ ...prev, health: true }));
    try {
      const response = await axios.get('http://127.0.0.1:5000/api/health');
      setSystemHealth(response.data);
      setError(prev => ({ ...prev, health: '' }));
    } catch (err) {
      setError(prev => ({ ...prev, health: 'Cannot connect to backend server' }));
      setSystemHealth(null);
    } finally {
      setLoading(prev => ({ ...prev, health: false }));
    }
  };

  // Load available database connections
  const loadAvailableDatabases = async () => {
    try {
      const response = await axios.get('http://127.0.0.1:5000/api/databases');
      setAvailableDatabases(response.data.databases || []);
    } catch (err) {
      console.error('Failed to load available databases:', err);
      setAvailableDatabases([]);
    }
  };

  // Handle database type change
  const handleDatabaseTypeChange = (newDbType) => {
    setDbType(newDbType);
    setSchema(null);
    setGeneratedSql('');
    setQueryResult(null);
    setError({ schema: '', sql: '', execution: '', health: error.health });
    
    // If switching to MySQL/MongoDB, load schema immediately
    if (newDbType !== 'sqlite') {
      handleSchemaLoad(newDbType);
    }
  };

  // Handle DB file upload for SQLite or schema load for MySQL/MongoDB
  const handleFileChange = async (file) => {
    if (!file && dbType === 'sqlite') {
      setSchema(null);
      setDbFile(null);
      return;
    }
    
    setDbFile(file);
    await handleSchemaLoad(dbType, file);
  };

  // Load schema based on database type
  const handleSchemaLoad = async (databaseType, file = null) => {
    setSchema(null);
    setGeneratedSql('');
    setQueryResult(null);
    setError(prev => ({ ...prev, schema: '', sql: '', execution: '' }));
    setLoading(prev => ({ ...prev, schema: true }));

    try {
      let response;
      
      if (databaseType === 'sqlite') {
        if (!file) return;
        const formData = new FormData();
        formData.append('db_file', file);
        formData.append('db_type', 'sqlite');
        response = await axios.post('http://127.0.0.1:5000/api/schema', formData);
      } else {
        // For MySQL/MongoDB - no file upload needed
        const formData = new FormData();
        formData.append('db_type', databaseType);
        response = await axios.post('http://127.0.0.1:5000/api/schema', formData);
      }
      
      setSchema(response.data);
      setError(prev => ({ ...prev, schema: '' }));
    } catch (err) {
      setError(prev => ({ 
        ...prev, 
        schema: err.response?.data?.error || `Failed to fetch ${databaseType} schema.` 
      }));
    } finally {
      setLoading(prev => ({ ...prev, schema: false }));
    }
  };

  // Add a successful query to history
  const addToHistory = (item) => {
    const newHistory = [{
      ...item,
      dbType: dbType,
      timestamp: new Date().toISOString()
    }, ...history.slice(0, 49)]; // Keep latest 50
    setHistory(newHistory);
    localStorage.setItem('nl2sql-history', JSON.stringify(newHistory));
  };
  
  // Re-run a query from history
  const loadFromHistory = (item) => {
    if (item.dbType && item.dbType !== dbType) {
      setDbType(item.dbType);
    }
    setQuestion(item.question);
    setGeneratedSql(item.sql);
    setQueryResult(null);
    setError({ schema: '', sql: '', execution: '', health: error.health });
  };

  // Enhanced SQL generation with database type
  const generateSql = async (questionText, llmModel = 'gemini') => {
    if (!questionText.trim()) return;
    
    setLoading(prev => ({ ...prev, sql: true }));
    setError(prev => ({ ...prev, sql: '' }));
    
    try {
      let formData = new FormData();
      formData.append('question', questionText);
      formData.append('llm', llmModel);
      formData.append('db_type', dbType);
      
      if (dbType === 'sqlite' && dbFile) {
        formData.append('db_file', dbFile);
      }
      
      const response = await axios.post('http://127.0.0.1:5000/api/generate-sql', formData);
      setGeneratedSql(response.data.sql);
      setError(prev => ({ ...prev, sql: '' }));
    } catch (err) {
      setError(prev => ({ 
        ...prev, 
        sql: err.response?.data?.error || 'Failed to generate SQL.' 
      }));
    } finally {
      setLoading(prev => ({ ...prev, sql: false }));
    }
  };

  return (
    <div className="bg-gray-100 min-h-screen font-sans">
      <header className="bg-white shadow-sm sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold text-gray-800 flex items-center">
              <span className="text-3xl mr-3">🧠</span>
              Enhanced NL2SQL Generator
            </h1>
            
            {/* System Health Indicator */}
            <div className="flex items-center space-x-4">
              {loading.health ? (
                <div className="flex items-center text-yellow-600">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-yellow-600 mr-2"></div>
                  Checking...
                </div>
              ) : error.health ? (
                <div className="flex items-center text-red-600">
                  <span className="w-3 h-3 bg-red-500 rounded-full mr-2"></span>
                  Backend Offline
                </div>
              ) : systemHealth ? (
                <div className="flex items-center text-green-600">
                  <span className="w-3 h-3 bg-green-500 rounded-full mr-2"></span>
                  System Healthy
                </div>
              ) : null}
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto p-4 sm:p-6 lg:p-8">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          
          {/* Left Panel: Database Selector, Schema, and History */}
          <aside className="lg:col-span-3 space-y-6">
            {/* Database Selector */}
            <DatabaseSelector
              dbType={dbType}
              onDbTypeChange={handleDatabaseTypeChange}
              availableDatabases={availableDatabases}
              systemHealth={systemHealth}
            />
            
            {/* Schema Viewer */}
            <SchemaViewer 
              schema={schema} 
              loading={loading.schema} 
              error={error.schema}
              dbType={dbType}
            />
            
            {/* History Panel */}
            <HistoryPanel 
              history={history} 
              onLoad={loadFromHistory}
              currentDbType={dbType}
            />
          </aside>

          {/* Main Content: Form, Editor, Results */}
          <main className="lg:col-span-9 space-y-6">
            {/* Query Form */}
            <div className="bg-white p-6 rounded-xl shadow-lg">
              <QueryForm
                onFileChange={handleFileChange}
                setQuestion={setQuestion}
                question={question}
                dbFile={dbFile}
                dbType={dbType}
                onGenerateSql={generateSql}
                loadingSql={loading.sql}
                sqlError={error.sql}
                schema={schema}
              />
            </div>

            {/* SQL Editor */}
            {generatedSql && (
              <div className="bg-white p-6 rounded-xl shadow-lg">
                <SqlEditor 
                  sql={generatedSql}
                  dbFile={dbFile}
                  dbType={dbType}
                  setQueryResult={setQueryResult}
                  setError={setError}
                  setLoading={setLoading}
                  loadingExecution={loading.execution}
                  onSuccess={(finalSql) => addToHistory({ 
                    question, 
                    sql: finalSql, 
                    date: new Date().toISOString() 
                  })}
                />
              </div>
            )}
            
            {/* Results Display */}
            {(queryResult || error.execution) && (
               <div className="bg-white p-6 rounded-xl shadow-lg">
                <ResultDisplay 
                  result={queryResult} 
                  error={error.execution}
                  dbType={dbType}
                />
              </div>
            )}
          </main>

        </div>
      </div>
    </div>
  );
}

export default App;
