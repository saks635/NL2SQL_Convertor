import React from 'react';
import Spinner from './Spinner';

const SchemaViewer = ({ schema, loading, error }) => {
  return (
    <div className="bg-white p-4 rounded-xl shadow-lg">
      <h3 className="text-lg font-semibold text-gray-800 mb-3 border-b pb-2">Database Schema</h3>
      {loading && <div className="flex justify-center p-4"><Spinner /></div>}
      {error && <p className="text-sm text-red-600">{error}</p>}
      {!loading && !error && !schema && <p className="text-sm text-gray-500">Upload a database to see its schema.</p>}
      {schema && (
        <div className="space-y-4 max-h-96 overflow-y-auto">
          {Object.entries(schema).map(([tableName, columns]) => (
            <div key={tableName}>
              <h4 className="font-bold text-gray-700">{tableName}</h4>
              <ul className="pl-4 mt-1 text-sm text-gray-600">
                {columns.map(col => (
                  <li key={col.name} className="flex items-center">
                    {col.pk && <span className="text-yellow-500 mr-2" title="Primary Key">🔑</span>}
                    {col.name} <span className="text-gray-400 ml-2">({col.type})</span>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default SchemaViewer;