import React, { useState } from 'react';
import axios from 'axios';

const QueryForm = ({ onFileChange, setQuestion, question, dbFile, setGeneratedSql, setQueryResult, setError, setLoading, loadingSql }) => {
  const [llm, setLlm] = useState('gemini');

  const handleGenerateSql = async (e) => {
    e.preventDefault();
    if (!dbFile || !question) {
      setError(prev => ({ ...prev, sql: 'Please provide a database file and a question.'}));
      return;
    }

    setLoading(prev => ({...prev, sql: true }));
    setError({ schema: '', sql: '', execution: '' });
    setGeneratedSql('');
    setQueryResult(null);
    
    const formData = new FormData();
    formData.append('db_file', dbFile);
    formData.append('question', question);
    formData.append('llm', llm);

    try {
      const response = await axios.post('http://127.0.0.1:5000/api/generate-sql', formData);
      setGeneratedSql(response.data.sql);
    } catch (err) {
      setError(prev => ({...prev, sql: err.response?.data?.error || 'Failed to generate SQL.' }));
    } finally {
      setLoading(prev => ({...prev, sql: false }));
    }
  };

  return (
    <form onSubmit={handleGenerateSql} className="space-y-5">
       <h2 className="text-xl font-semibold text-gray-700">1. Ask a Question</h2>
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Upload SQLite DB File</label>
        <input type="file" accept=".db,.sqlite,.sqlite3" onChange={(e) => onFileChange(e.target.files[0])} required className="w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"/>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Choose LLM Model</label>
        <select value={llm} onChange={(e) => setLlm(e.target.value)} className="w-full p-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500">
          <option value="gemini">Gemini</option>
          <option value="cohere">Cohere</option>
        </select>
      </div>
      
      <div>
        <label htmlFor="question" className="block text-sm font-medium text-gray-700 mb-1">Your Question</label>
        <textarea id="question" rows="4" value={question} onChange={(e) => setQuestion(e.target.value)} placeholder="e.g., Show me all albums by the artist Queen" required className="w-full p-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500" />
      </div>

      <div className="text-center">
        <button type="submit" className="bg-blue-600 text-white font-bold px-8 py-2.5 rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:bg-gray-400" disabled={!dbFile || loadingSql}>
          {loadingSql ? 'Generating...' : 'Generate SQL'}
        </button>
      </div>
    </form>
  );
};

export default QueryForm;