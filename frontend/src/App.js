import React, { useState, useEffect } from 'react';
import axios from 'axios';

import QueryForm from './components/QueryForm';
import SchemaViewer from './components/SchemaViewer';
import SqlEditor from './components/SqlEditor';
import ResultDisplay from './components/ResultDisplay';
import HistoryPanel from './components/HistoryPanel';

function App() {
  // State management for all new features
  const [dbFile, setDbFile] = useState(null);
  const [schema, setSchema] = useState(null);
  const [question, setQuestion] = useState('');
  const [generatedSql, setGeneratedSql] = useState('');
  const [queryResult, setQueryResult] = useState(null);
  const [history, setHistory] = useState([]);

  // States for loading and errors
  const [loading, setLoading] = useState({ schema: false, sql: false, execution: false });
  const [error, setError] = useState({ schema: '', sql: '', execution: '' });

  // Load history from localStorage on initial render
  useEffect(() => {
    const savedHistory = localStorage.getItem('nl2sql-history');
    if (savedHistory) {
      setHistory(JSON.parse(savedHistory));
    }
  }, []);

  // Handle DB file upload and fetch schema
  const handleFileChange = async (file) => {
    if (!file) {
      setSchema(null);
      setDbFile(null);
      return;
    }
    setDbFile(file);
    setSchema(null);
    setGeneratedSql('');
    setQueryResult(null);
    setError({ schema: '', sql: '', execution: '' });
    setLoading(prev => ({ ...prev, schema: true }));

    const formData = new FormData();
    formData.append('db_file', file);

    try {
      const response = await axios.post('http://127.0.0.1:5000/api/schema', formData);
      setSchema(response.data);
      setError(prev => ({ ...prev, schema: '' }));
    } catch (err) {
      setError(prev => ({ ...prev, schema: err.response?.data?.error || 'Failed to fetch schema.' }));
    } finally {
      setLoading(prev => ({ ...prev, schema: false }));
    }
  };

  // Add a successful query to history and save to localStorage
  const addToHistory = (item) => {
    const newHistory = [item, ...history.slice(0, 49)]; // Keep latest 50
    setHistory(newHistory);
    localStorage.setItem('nl2sql-history', JSON.stringify(newHistory));
  };
  
  // Re-run a query from history
  const loadFromHistory = (item) => {
      setQuestion(item.question);
      setGeneratedSql(item.sql);
      setQueryResult(null); // Clear previous results
      setError({ schema: '', sql: '', execution: '' });
  };


  return (
    <div className="bg-gray-100 min-h-screen font-sans">
      <header className="bg-white shadow-sm sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <h1 className="text-2xl font-bold text-gray-800 flex items-center">
            <span className="text-3xl mr-3">🧠</span>
            Natural Language to SQL Generator
          </h1>
        </div>
      </header>

      <div className="max-w-7xl mx-auto p-4 sm:p-6 lg:p-8">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          
          {/* Left Panel: Schema and History */}
          <aside className="lg:col-span-3 space-y-8">
            <SchemaViewer schema={schema} loading={loading.schema} error={error.schema} />
            <HistoryPanel history={history} onLoad={loadFromHistory} />
          </aside>

          {/* Main Content: Form, Editor, Results */}
          <main className="lg:col-span-9 space-y-8">
            <div className="bg-white p-6 rounded-xl shadow-lg">
              <QueryForm
                onFileChange={handleFileChange}
                setQuestion={setQuestion}
                question={question}
                dbFile={dbFile}
                setGeneratedSql={setGeneratedSql}
                setQueryResult={setQueryResult}
                setError={setError}
                setLoading={setLoading}
                loadingSql={loading.sql}
              />
            </div>

            {generatedSql && (
              <div className="bg-white p-6 rounded-xl shadow-lg">
                <SqlEditor 
                  sql={generatedSql}
                  dbFile={dbFile}
                  setQueryResult={setQueryResult}
                  setError={setError}
                  setLoading={setLoading}
                  loadingExecution={loading.execution}
                  onSuccess={(finalSql) => addToHistory({ question, sql: finalSql, date: new Date().toISOString() })}
                />
              </div>
            )}
            
            {(queryResult || error.execution) && (
               <div className="bg-white p-6 rounded-xl shadow-lg">
                <ResultDisplay result={queryResult} error={error.execution} />
              </div>
            )}
          </main>

        </div>
      </div>
    </div>
  );
}

export default App;