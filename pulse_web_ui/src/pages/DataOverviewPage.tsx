import React from 'react';
import useFetchData from '../hooks/useApi';
import { DataOverview } from '../types';

// Define a basic interface for retrodiction data points
interface RetrodictionDataPoint {
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
 * DataOverviewPage component to display an overview of the data.
 * Fetches data using the useFetchData hook.
 */
function DataOverviewPage() {
  // Fetch retrodiction data
  const { data: retrodictionData, loading: loadingRetrodiction, error: errorRetrodiction } = useFetchData<RetrodictionDataPoint[] | RetrodictionDataPoint>('/api/retrodiction');

  return (
    <div>
      <h1>Data Overview</h1>
      {/* Retrodiction Data Panel */}
      <div className="data-panel">
        <h2>Retrodiction Data</h2>
        {loadingRetrodiction && <p>Loading retrodiction data...</p>}
        {errorRetrodiction && <p>Error fetching retrodiction data: {errorRetrodiction.message}</p>}
        {!loadingRetrodiction && !errorRetrodiction && !retrodictionData && (
          <p>No retrodiction data available.</p>
        )}
        {retrodictionData && (
          <div>
            {/* Structured display of retrodiction data */}
            {/* Assuming retrodictionData is an object or array, display in a structured way */}
            {typeof retrodictionData === 'object' && (
              <table>
                <thead>
                  <tr>
                    {/* Assuming retrodictionData is an array of objects, use keys from the first object as headers */}
                    {Array.isArray(retrodictionData) && retrodictionData.length > 0 && Object.keys(retrodictionData[0]).map(key => (
                      <th key={key}>{key}</th>
                    ))}
                     {/* If retrodictionData is a single object, use its keys as headers */}
                    {!Array.isArray(retrodictionData) && Object.keys(retrodictionData).map(key => (
                      <th key={key}>{key}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {/* If retrodictionData is an array, map through it */}
                  {Array.isArray(retrodictionData) && retrodictionData.map((dataPoint, index) => (
                    <tr key={index}>
                      {Object.values(dataPoint).map((value, valIndex) => (
                        <td key={valIndex}>{formatValue(value)}</td>
                      ))}
                    </tr>
                  ))}
                   {/* If retrodictionData is a single object, display its values in a single row */}
                  {!Array.isArray(retrodictionData) && (
                    <tr>
                      {Object.values(retrodictionData).map((value, valIndex) => (
                        <td key={valIndex}>{formatValue(value)}</td>
                      ))}
                    </tr>
                  )}
                </tbody>
              </table>
            )}
          </div>
        )}
      </div>

      {/* Autopilot Placeholder Panel */}
      <div className="data-panel" style={{ marginTop: '20px' }}>
        <h2>Autopilot Information</h2>
        <p>Autopilot Status: Not available (backend placeholder)</p>
        <p>Autopilot Data: Not available (backend placeholder)</p>
        {/* TODO: Replace with actual data fetching and display when backend endpoints are implemented */}
      </div>
    </div>
  );
}

export default DataOverviewPage;