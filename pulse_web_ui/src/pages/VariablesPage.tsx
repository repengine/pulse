import React from 'react';
import useFetchData from '../hooks/useApi';

// Define types for the new API endpoints
interface CurrentVariablesData {
  [key: string]: any; // Assuming keys are strings and values can be anything for now
}

interface HistoricalVariablesData {
  [key: string]: any; // Assuming keys are strings and values can be anything for now
}

// Basic value formatter - can be expanded later
const formatValue = (value: any): string => {
  if (value === null || value === undefined) {
    return 'N/A';
  }
  if (typeof value === 'object') {
    return JSON.stringify(value, null, 2); // Pretty print objects
  }
  return String(value);
};

/**
 * VariablesPage component to display current and historical variables.
 * Fetches data using the useFetchData hook from the /api/variables/current and /api/variables/historical endpoints.
 */
function VariablesPage() {
  // Fetch current variable data
  const { data: currentVariables, loading: loadingCurrent, error: errorCurrent } = useFetchData<CurrentVariablesData>('/api/variables/current');

  // Fetch historical variable data
  const { data: historicalVariables, loading: loadingHistorical, error: errorHistorical } = useFetchData<HistoricalVariablesData>('/api/variables/historical');

  return (
    <div>
      <h1>Variables</h1>
      {/* Current Variables Panel */}
      <div className="data-panel">
        <h2>Current Variables</h2>
        {loadingCurrent && <p>Loading current variables...</p>}
        {errorCurrent && <p>Error fetching current variables: {errorCurrent.message}</p>}
        {!loadingCurrent && !errorCurrent && (!currentVariables || Object.keys(currentVariables).length === 0) && (
          <p>No current variable data available.</p>
        )}
        {currentVariables && (
          <div>
            {/* Structured display of current variable data */}
            <table>
              <thead>
                <tr>
                  <th>Variable</th>
                  <th>Value</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(currentVariables || {}).map(([key, value]) => (
                  <tr key={key}>
                    <td>{key}</td>
                    <td>{formatValue(value)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Historical Variables Panel */}
      <div className="data-panel" style={{ marginTop: '20px' }}>
        <h2>Historical Variables</h2>
        {loadingHistorical && <p>Loading historical variables...</p>}
        {errorHistorical && <p>Error fetching historical variables: {errorHistorical.message}</p>}
        {!loadingHistorical && !errorHistorical && (!historicalVariables || Object.keys(historicalVariables).length === 0) && (
          <p>No historical variable data available.</p>
        )}
        {historicalVariables && (
          <div>
            {/* Structured display of historical variable data */}
            {/* Assuming historicalVariables is an object where keys are variable names and values are arrays of historical data points */}
            {Object.entries(historicalVariables || {}).map(([variableName, historicalData]) => (
              <div key={variableName}>
                <h4>{variableName} History</h4>
                <table>
                  <thead>
                    <tr>
                      {/* Assuming historicalData is an array of objects, use keys from the first object as headers */}
                      {Array.isArray(historicalData) && historicalData.length > 0 && Object.keys(historicalData[0]).map(key => (
                        <th key={key}>{key}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {Array.isArray(historicalData) && historicalData.map((dataPoint, index) => (
                      <tr key={index}>
                        {Object.values(dataPoint).map((value, valIndex) => (
                          <td key={valIndex}>{formatValue(value)}</td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default VariablesPage;