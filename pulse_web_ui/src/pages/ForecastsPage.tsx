import React from 'react';
import useFetchData from '../hooks/useApi';
import { Forecasts } from '../types';
import { Line } from 'react-chartjs-2';
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend } from 'chart.js';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend);

/**
 * ForecastsPage component to display forecasts.
 * Fetches forecasts using the useFetchData hook.
 */
function ForecastsPage() {
  const { data: forecasts, loading, error } = useFetchData<Forecasts>('/api/forecasts');

  return (
    <div>
      <h1>Forecasts</h1>
      {/* Forecasts Panel */}
      <div style={{ border: '1px solid black', padding: '20px', margin: '20px' }}>
        <h2>Forecasts Content</h2>
        {loading && <p>Loading forecasts...</p>}
        {error && <p>Error fetching forecasts: {error.message}</p>}
        {forecasts && (
          <div>
            {Object.keys(forecasts).map((forecastName) => (
              <div key={forecastName} style={{ border: '1px solid #ccc', margin: '10px', padding: '10px' }}>
                <h3>{forecastName}</h3>
                {/* Display a chart for array data */}
                {Array.isArray(forecasts[forecastName]) ? (
                  <div style={{ width: '100%', height: '200px' }}>
                    <Line
                      data={{
                        labels: forecasts[forecastName].map((_, index) => index.toString()), // Simple index labels
                        datasets: [
                          {
                            label: forecastName,
                            data: forecasts[forecastName],
                            fill: false,
                            backgroundColor: 'rgb(75, 192, 192)',
                            borderColor: 'rgba(75, 192, 192, 0.2)',
                          },
                        ],
                      }}
                      options={{
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                          title: {
                            display: true,
                            text: `${forecastName} Forecast`,
                          },
                        },
                        scales: {
                          x: {
                            title: {
                              display: true,
                              text: 'Time Step',
                            },
                          },
                          y: {
                            title: {
                              display: true,
                              text: 'Value',
                            },
                          },
                        },
                      }}
                    />
                  </div>
                ) : (
                  <p>Data type: {typeof forecasts[forecastName]}</p>
                )}
              </div>
            ))}
          </div>
        )}
        {!loading && !error && !forecasts && (
          <p>No forecasts available.</p>
        )}
      </div>
    </div>
  );
}

export default ForecastsPage;