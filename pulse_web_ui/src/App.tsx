import React from 'react';
import { Routes, Route, Link } from 'react-router-dom';
import DataOverviewPage from './pages/DataOverviewPage';
import LogsPage from './pages/LogsPage';
import VariablesPage from './pages/VariablesPage';
import ForecastsPage from './pages/ForecastsPage';

function App() {
  return (
    <div>
      <nav>
        <ul>
          <li><Link to="/">Data Overview</Link></li>
          <li><Link to="/logs">Logs</Link></li>
          <li><Link to="/variables">Variables</Link></li>
          <li><Link to="/forecasts">Forecasts</Link></li>
        </ul>
      </nav>

      <Routes>
        <Route path="/" element={<DataOverviewPage />} />
        <Route path="/logs" element={<LogsPage />} />
        <Route path="/variables" element={<VariablesPage />} />
        <Route path="/forecasts" element={<ForecastsPage />} />
      </Routes>
    </div>
  );
}

export default App;