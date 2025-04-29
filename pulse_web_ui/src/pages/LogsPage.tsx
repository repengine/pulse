import React, { useState, useEffect } from 'react';
import useFetchData from '../hooks/useApi';
import { Logs } from '../types';

/**
 * LogsPage component to display logs.
 * Fetches logs using the useFetchData hook.
 */
function LogsPage() {
  const [severityFilter, setSeverityFilter] = useState('');
  const [startDateFilter, setStartDateFilter] = useState('');
  const [endDateFilter, setEndDateFilter] = useState('');
  const [searchQuery, setSearchQuery] = useState('');

  // Construct the API URL with query parameters
  const apiUrl = `/api/logs?severity=${severityFilter}&startDate=${startDateFilter}&endDate=${endDateFilter}&search=${encodeURIComponent(searchQuery)}`;

  const { data: logs, loading, error } = useFetchData<Logs>(apiUrl);

  return (
    <div>
      <h1>Logs</h1>
      <div className="data-panel">
        <h2>Filter Logs</h2>
        <div style={{ marginBottom: '10px' }}>
          <label htmlFor="severityFilter">Severity:</label>
          <select id="severityFilter" value={severityFilter} onChange={(e) => setSeverityFilter(e.target.value)}>
            <option value="">All</option>
            <option value="INFO">INFO</option>
            <option value="WARN">WARN</option>
            <option value="ERROR">ERROR</option>
          </select>
        </div>
        <div style={{ marginBottom: '10px' }}>
          <label htmlFor="startDateFilter">Start Date:</label>
          <input type="date" id="startDateFilter" value={startDateFilter} onChange={(e) => setStartDateFilter(e.target.value)} />
        </div>
        <div style={{ marginBottom: '10px' }}>
          <label htmlFor="endDateFilter">End Date:</label>
          <input type="date" id="endDateFilter" value={endDateFilter} onChange={(e) => setEndDateFilter(e.target.value)} />
        </div>
        <div style={{ marginBottom: '20px' }}>
          <label htmlFor="searchQuery">Search Message:</label>
          <input type="text" id="searchQuery" value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} />
        </div>

        <h2>Logs Content</h2>
        {loading && <p>Loading logs...</p>}
        {error && <p style={{ color: 'red' }}>Error fetching logs: {error.message}</p>}
        {logs && logs.length > 0 ? (
          <ul>
            {logs.map((log, index) => (
              <li key={index} style={{ marginBottom: '10px', borderBottom: '1px solid #eee', paddingBottom: '5px' }}>
                <strong>[{log.timestamp}]</strong> <span style={{ color: log.severity === 'ERROR' ? 'red' : log.severity === 'WARN' ? 'orange' : 'black' }}>{log.severity}</span>: {log.message}
              </li>
            ))}
          </ul>
        ) : (
          !loading && !error && <p>No logs available.</p>
        )}
      </div>
    </div>
  );
}

export default LogsPage;