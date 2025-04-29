import React from 'react';
import { Routes, Route, Link } from 'react-router-dom';
import DataOverviewPage from './pages/DataOverviewPage';
import LogsPage from './pages/LogsPage';
import VariablesPage from './pages/VariablesPage';
import ForecastsPage from './pages/ForecastsPage';
import './App.css'; // Import the CSS file

function App() {
  return (
    <div className="container"> {/* Apply container class */}
      <nav>
        <ul>
          <li><Link to="/">Data Overview</Link></li>
          <li><Link to="/logs">Logs</Link></li>
          <li><Link to="/variables">Variables</Link></li>
          <li><Link to="/forecasts">Forecasts</Link></li>
        </ul>
      </nav>

      <div className="page-content"> {/* Apply page-content class */}
        <Routes>
          <Route path="/" element={<DataOverviewPage />} />
          <Route path="/logs" element={<LogsPage />} />
          <Route path="/variables" element={<VariablesPage />} />
          <Route path="/forecasts" element={<ForecastsPage />} />
        </Routes>
      </div>
    </div>
  );
}

export default App;