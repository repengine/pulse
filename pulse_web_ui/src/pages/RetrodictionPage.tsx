import React, { useState, useEffect } from 'react';
import useApi from '../hooks/useApi';

interface RetrodictionRunParams {
  startDate: string;
  days: number;
  variables: string[];
}

interface RetrodictionRunResponse {
  run_id: string;
}

interface RetrodictionStatus {
  status: string;
  progress: number;
}

interface RetrodictionData {
  // Define structure based on expected API response for data, including Plotly chart data
  chart_data: any; // Placeholder for Plotly chart data
  // other result fields
}

function RetrodictionPage() {
  const [runParams, setRunParams] = useState<RetrodictionRunParams>({
    startDate: '',
    days: 7,
    variables: [],
  });
  const [runId, setRunId] = useState<string | null>(null);
  const [runStatus, setRunStatus] = useState<RetrodictionStatus | null>(null);
  const [runData, setRunData] = useState<RetrodictionData | null>(null);
  const [pollingInterval, setPollingInterval] = useState<NodeJS.Timeout | null>(null);

  const { data: runResponse, loading: runLoading, error: runError, post } = useApi<RetrodictionRunResponse>('/api/retrodiction/run');
  const { data: statusResponse, loading: statusLoading, error: statusError, get: getStatus } = useApi<RetrodictionStatus>(runId ? `/api/retrodiction/status/${runId}` : '');
  const { data: dataResponse, loading: dataLoading, error: dataError, get: getData } = useApi<RetrodictionData>(runId ? `/api/retrodiction_data/${runId}` : '');

  useEffect(() => {
    if (runResponse && runResponse.run_id) {
      setRunId(runResponse.run_id);
      // Start polling for status
      const interval = setInterval(() => {
        getStatus();
      }, 2000); // Poll every 2 seconds
      setPollingInterval(interval);
    }
  }, [runResponse]);

  useEffect(() => {
    if (statusResponse) {
      setRunStatus(statusResponse);
      if (statusResponse.status === 'completed' || statusResponse.status === 'failed') {
        // Stop polling
        if (pollingInterval) {
          clearInterval(pollingInterval);
          setPollingInterval(null);
        }
        if (statusResponse.status === 'completed') {
          // Fetch results
          getData();
        }
      }
    }
  }, [statusResponse]);

  useEffect(() => {
    if (dataResponse) {
      setRunData(dataResponse);
    }
  }, [dataResponse]);

  const handleRunRetrodiction = () => {
    post('/api/retrodiction/run', runParams);
  };

  return (
    <div>
      <h1>Retrodiction</h1>

      {/* Input Panel */}
      <div className="data-panel">
        <h2>Run Retrodiction</h2>
        <div>
          <label htmlFor="startDate">Start Date:</label>
          <input
            type="date"
            id="startDate"
            value={runParams.startDate}
            onChange={(e) => setRunParams({ ...runParams, startDate: e.target.value })}
          />
        </div>
        <div>
          <label htmlFor="days">Days:</label>
          <input
            type="number"
            id="days"
            value={runParams.days}
            onChange={(e) => setRunParams({ ...runParams, days: parseInt(e.target.value, 10) })}
          />
        </div>
        <div>
          <label htmlFor="variables">Variables (comma-separated):</label>
          <input
            type="text"
            id="variables"
            value={runParams.variables.join(',')}
            onChange={(e) => setRunParams({ ...runParams, variables: e.target.value.split(',').map(v => v.trim()) })}
          />
        </div>
        <button onClick={handleRunRetrodiction} disabled={runLoading}>
          {runLoading ? 'Running...' : 'Run Retrodiction'}
        </button>
        {runError && <p>Error triggering run: {runError.message}</p>}
      </div>

      {/* Status Panel */}
      <div className="data-panel">
        <h2>Run Status</h2>
        {runId && <p>Run ID: {runId}</p>}
        {statusLoading && <p>Loading status...</p>}
        {statusError && <p>Error fetching status: {statusError.message}</p>}
        {runStatus && (
          <div>
            <p>Status: {runStatus.status}</p>
            <p>Progress: {runStatus.progress}%</p>
          </div>
        )}
      </div>

      {/* Results Panel */}
      <div className="data-panel">
        <h2>Run Results</h2>
        {dataLoading && <p>Loading results...</p>}
        {dataError && <p>Error fetching results: {dataError.message}</p>}
        {runData && (
          <div>
            {/* Display results, including Plotly chart */}
            {/* Placeholder for Plotly chart */}
            {runData.chart_data && (
              <div>
                <h3>Plotly Chart</h3>
                {/* You would integrate a Plotly React component here */}
                <pre>{JSON.stringify(runData.chart_data, null, 2)}</pre>
              </div>
            )}
            {/* Display other results */}
          </div>
        )}
      </div>
    </div>
  );
}

export default RetrodictionPage;