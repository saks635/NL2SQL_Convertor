import React from 'react';

const HistoryPanel = ({ history, onLoad }) => {
  return (
    <div className="bg-white p-4 rounded-xl shadow-lg">
      <h3 className="text-lg font-semibold text-gray-800 mb-3 border-b pb-2">Query History</h3>
      {history.length > 0 ? (
        <ul className="space-y-2 max-h-96 overflow-y-auto">
          {history.map((item, index) => (
            <li key={index} className="p-2 rounded-md hover:bg-gray-100 cursor-pointer" onClick={() => onLoad(item)}>
              <p className="text-sm font-medium text-gray-800 truncate" title={item.question}>
                {item.question}
              </p>
              <p className="text-xs text-gray-500 font-mono truncate" title={item.sql}>{item.sql}</p>
            </li>
          ))}
        </ul>
      ) : (
        <p className="text-sm text-gray-500">Your recent successful queries will appear here.</p>
      )}
    </div>
  );
};

export default HistoryPanel;