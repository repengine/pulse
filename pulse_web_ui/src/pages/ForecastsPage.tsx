import React from 'react';
import useFetchData from '../hooks/useApi';

// Define a basic interface for forecast data points
interface ForecastDataPoint {
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
 * ForecastsPage component to display forecasts.
 * Fetches forecasts using the useFetchData hook from the /api/forecasts endpoint.
 */
function ForecastsPage() {
  // Fetch forecast data from the new endpoint
  const { data: forecasts, loading, error } = useFetchData<ForecastDataPoint[]>('/api/forecasts');

  return (
    <div>
      <h1>Forecasts</h1>
      {/* Forecasts Panel */}
      <div className="data-panel">
        <h2>Forecast Data</h2>
        {loading && <p>Loading forecasts...</p>}
        {error && <p>Error fetching forecasts: {error.message}</p>}
        {!loading && !error && (!forecasts || forecasts.length === 0) && (
          <p>No forecast data available.</p>
        )}
        {forecasts && (
          <div>
            {/* Structured display of forecast data */}
            <table>
              <thead>
                <tr>
                  {/* Assuming forecasts is an array of objects, use keys from the first object as headers */}
                  {forecasts.length > 0 && Object.keys(forecasts[0]).map(key => (
                    <th key={key}>{key}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {forecasts.map((forecast, index) => (
                  <tr key={index}>
                    {Object.values(forecast).map((value, valIndex) => (
                      <td key={valIndex}>{formatValue(value)}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

export default ForecastsPage;