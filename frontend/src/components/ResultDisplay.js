import React from 'react';

const ResultDisplay = ({ result, error }) => {
  if (error) {
    return (
      <div>
        <h2 className="text-xl font-semibold text-gray-700 mb-4">3. Result</h2>
        <div className="bg-red-100 border-l-4 border-red-500 text-red-800 p-4 rounded-md shadow">
          <strong className="font-bold">Error:</strong>
          <p>{error}</p>
        </div>
      </div>
    );
  }

  if (!result) return null;
  
  const { headers, rows } = result;

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-semibold text-gray-700">3. Result</h2>
      {rows.length > 0 ? (
        <div className="overflow-x-auto border border-gray-200 rounded-lg shadow-sm">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-100">
              <tr>
                {headers.map((header, index) => (
                  <th key={index} className="px-6 py-3 text-left text-xs font-medium text-gray-600 uppercase tracking-wider">{header}</th>
                ))}
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {rows.map((row, rowIndex) => (
                <tr key={rowIndex} className="hover:bg-gray-50">
                  {row.map((cell, cellIndex) => (
                    <td key={cellIndex} className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">{cell}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="bg-blue-50 border-l-4 border-blue-400 text-blue-800 p-4 rounded-md">
           ✅ The query executed successfully, but returned no rows.
        </div>
      )}
    </div>
  );
};

export default ResultDisplay;