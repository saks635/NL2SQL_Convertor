import React, { useState, useEffect } from 'react';
import axios from 'axios';

const SqlEditor = ({ sql, dbFile, setQueryResult, setError, setLoading, loadingExecution, onSuccess }) => {
  const [editableSql, setEditableSql] = useState(sql);
  const [copySuccess, setCopySuccess] = useState('');

  // Update the text area if a new query is generated for the same file
  useEffect(() => {
    setEditableSql(sql);
  }, [sql]);

  const handleExecuteSql = async () => {
    if (!dbFile) {
      setError(prev => ({...prev, execution: 'Database file not found.'}));
      return;
    }
    setLoading(prev => ({...prev, execution: true }));
    setError({ schema: '', sql: '', execution: '' });
    setQueryResult(null);

    const formData = new FormData();
    formData.append('db_file', dbFile);
    formData.append('sql', editableSql);

    try {
      const response = await axios.post('http://127.0.0.1:5000/api/execute-sql', formData);
      setQueryResult(response.data);
      onSuccess(editableSql); // Notify parent of success for history
    } catch (err) {
      setError(prev => ({...prev, execution: err.response?.data?.error || 'Failed to execute query.' }));
    } finally {
      setLoading(prev => ({...prev, execution: false }));
    }
  };

  const copyToClipboard = () => {
    navigator.clipboard.writeText(editableSql).then(() => {
      setCopySuccess('Copied!');
      setTimeout(() => setCopySuccess(''), 2000);
    }, () => {
      setCopySuccess('Failed to copy.');
      setTimeout(() => setCopySuccess(''), 2000);
    });
  };

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-semibold text-gray-700">2. Edit & Execute SQL</h2>
      <div className="font-mono relative">
        <textarea
          value={editableSql}
          onChange={(e) => setEditableSql(e.target.value)}
          rows="6"
          className="w-full p-3 pr-20 border border-gray-300 rounded-md shadow-sm bg-gray-50 focus:ring-blue-500 focus:border-blue-500"
        />
        <button onClick={copyToClipboard} className="absolute top-2 right-2 bg-gray-200 text-gray-600 px-3 py-1 rounded text-xs hover:bg-gray-300">
          {copySuccess || 'Copy'}
        </button>
      </div>
      <div className="text-center">
        <button onClick={handleExecuteSql} className="bg-green-600 text-white font-bold px-8 py-2.5 rounded-lg hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:bg-gray-400" disabled={loadingExecution}>
          {loadingExecution ? 'Executing...' : 'Execute Query'}
        </button>
      </div>
    </div>
  );
};

export default SqlEditor;