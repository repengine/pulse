import React, { useEffect } from 'react';
import useApi from '../hooks/useApi';

interface AutopilotStatus {
  status: string;
  // Add other status fields as needed
}

interface AutopilotHistoryEntry {
  run_id: string;
  start_time: string;
  end_time: string | null;
  status: string;
  // Add other history fields as needed
}

function AutopilotPage() {
  const { data: status, loading: statusLoading, error: statusError, get: fetchStatus } = useApi<AutopilotStatus>('/api/autopilot/status');
  const { data: history, loading: historyLoading, error: historyError, get: fetchHistory } = useApi<AutopilotHistoryEntry[]>('/api/autopilot/history');
  const { loading: startLoading, error: startError, post: startAutopilot } = useApi<any>('/api/autopilot/start');
  const { loading: stopLoading, error: stopError, post: stopAutopilot } = useApi<any>('/api/autopilot/stop');

  useEffect(() => {
    fetchStatus();
    fetchHistory();
    // Set up polling for status if needed
    const statusPollingInterval = setInterval(() => {
      fetchStatus();
    }, 5000); // Poll status every 5 seconds

    // Set up polling for history if needed (less frequent)
    const historyPollingInterval = setInterval(() => {
      fetchHistory();
    }, 30000); // Poll history every 30 seconds


    return () => {
      clearInterval(statusPollingInterval);
      clearInterval(historyPollingInterval);
    };
  }, [fetchStatus, fetchHistory]);

  const handleStart = () => {
    startAutopilot('/api/autopilot/start', {}); // POST request with an empty body
  };

  const handleStop = () => {
    stopAutopilot('/api/autopilot/stop', {}); // POST request with an empty body
  };

  return (
    <div>
      <h1>Autopilot</h1>

      {/* Autopilot Controls */}
      <div className="data-panel">
        <h2>Controls</h2>
        <button onClick={handleStart} disabled={startLoading}>
          {startLoading ? 'Starting...' : 'Start Autopilot'}
        </button>
        <button onClick={handleStop} disabled={stopLoading} style={{ marginLeft: '10px' }}>
          {stopLoading ? 'Stopping...' : 'Stop Autopilot'}
        </button>
        {startError && <p>Error starting autopilot: {startError.message}</p>}
        {stopError && <p>Error stopping autopilot: {stopError.message}</p>}
      </div>

      {/* Autopilot Status */}
      <div className="data-panel" style={{ marginTop: '20px' }}>
        <h2>Status</h2>
        {statusLoading && <p>Loading status...</p>}
        {statusError && <p>Error fetching status: {statusError.message}</p>}
        {status && (
          <div>
            <p>Current Status: {status.status}</p>
            {/* Display other status fields */}
          </div>
        )}
      </div>

      {/* Autopilot History */}
      <div className="data-panel" style={{ marginTop: '20px' }}>
        <h2>History</h2>
        {historyLoading && <p>Loading history...</p>}
        {historyError && <p>Error fetching history: {historyError.message}</p>}
        {history && history.length > 0 ? (
          <table>
            <thead>
              <tr>
                <th>Run ID</th>
                <th>Start Time</th>
                <th>End Time</th>
                <th>Status</th>
                {/* Add other history headers */}
              </tr>
            </thead>
            <tbody>
              {history.map((entry) => (
                <tr key={entry.run_id}>
                  <td>{entry.run_id}</td>
                  <td>{entry.start_time}</td>
                  <td>{entry.end_time || 'N/A'}</td>
                  <td>{entry.status}</td>
                  {/* Display other history fields */}
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          !historyLoading && !historyError && <p>No history available.</p>
        )}
      </div>
    </div>
  );
}

export default AutopilotPage;