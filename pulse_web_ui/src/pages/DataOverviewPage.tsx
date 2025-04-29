import React from 'react';
import useFetchData from '../hooks/useApi';
import { DataOverview } from '../types';

/**
 * DataOverviewPage component to display an overview of the data.
 * Fetches data using the useFetchData hook.
 */
function DataOverviewPage() {
  const { data, loading, error } = useFetchData<DataOverview>('/api/data/overview');

  return (
    <div>
      <h1>Data Overview</h1>
      {/* Data Display Panel */}
      <div style={{ border: '1px solid black', padding: '20px', margin: '20px' }}>
        <h2>Data Overview Content</h2>
        {loading && <p>Loading...</p>}
        {error && <p>Error: {error.message}</p>}
        {data && (
          <div>
            {Object.entries(data).map(([key, value]) => (
              <div key={key}>
                <h3>{key}</h3>
                <pre>{JSON.stringify(value, null, 2)}</pre>
              </div>
            ))}
          </div>
        )}
        {!loading && !error && !data && (
          <p>No data overview available.</p>
        )}
      </div>
    </div>
  );
}

export default DataOverviewPage;