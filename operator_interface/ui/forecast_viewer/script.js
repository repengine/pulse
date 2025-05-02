document.addEventListener('DOMContentLoaded', () => {
    fetchForecastData();
});

async function fetchForecastData() {
    // In a real application, this would fetch from a backend endpoint.
    // For this proof-of-concept, we'll use a simulated JSON object.
    const simulatedForecastData = {
        "digest_summary": "Summary of the forecast digest.",
        "individual_forecasts": [
            {
                "id": "forecast1",
                "outcome": "Outcome of forecast 1.",
                "confidence": 0.8,
                "potential_paths": ["Path A", "Path B"],
                "causal_explanation": {
                    "variable1": "Influence of variable 1 on forecast 1.",
                    "variable2": "Influence of variable 2 on forecast 1."
                }
            },
            {
                "id": "forecast2",
                "outcome": "Outcome of forecast 2.",
                "confidence": 0.6,
                "potential_paths": ["Path X", "Path Y", "Path Z"],
                "causal_explanation": {
                    "variableA": "Influence of variable A on forecast 2."
                }
            }
        ],
        "divergence": "Information about forecast divergence.",
        "fragmentation": "Information about forecast fragmentation.",
        "most_evolved_forecasts": ["forecast1"]
    };

    displayForecasts(simulatedForecastData);
}

function displayForecasts(data) {
    const container = document.getElementById('forecast-container');
    container.innerHTML = ''; // Clear previous content

    if (data && data.individual_forecasts) {
        data.individual_forecasts.forEach(forecast => {
            const forecastElement = document.createElement('div');
            forecastElement.classList.add('forecast-item');

            forecastElement.innerHTML = `
                <h3>Forecast ID: ${forecast.id}</h3>
                <p><strong>Outcome:</strong> ${forecast.outcome}</p>
                <p><strong>Confidence:</strong> <span class="confidence-level">${(forecast.confidence * 100).toFixed(1)}%</span></p>
                <p><strong>Potential Paths:</strong> ${forecast.potential_paths.join(', ')}</p>
                <div class="causal-explanation">
                    <h4>Causal Explanation:</h4>
                    ${Object.entries(forecast.causal_explanation).map(([variable, explanation]) => `
                        <p><strong>${variable}:</strong> ${explanation}</p>
                    `).join('')}
                </div>
            `;

            container.appendChild(forecastElement);
        });
    } else {
        container.innerHTML = '<p>No forecast data available.</p>';
    }
}