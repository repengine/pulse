from flask import Flask, jsonify, request, Response
from typing import Dict, List, Any, Tuple

app = Flask(__name__)

# Sample data - In a real application, this would be stored in a database
sample_variables = [
    {"name": "temperature", "value": 25.5, "type": "float"},
    {"name": "is_active", "value": True, "type": "boolean"},
    {"name": "user_count", "value": 150, "type": "integer"},
]

@app.route('/api/logs', methods=['GET'])
def get_logs() -> Response:
    """
    Basic endpoint to return a list of sample log entries.
    """
    sample_logs = [
        {"timestamp": "2023-10-27T10:00:00Z", "severity": "INFO", "message": "Application started successfully."},
        {"timestamp": "2023-10-27T10:05:15Z", "severity": "WARNING", "message": "Disk usage is above 80%."},
        {"timestamp": "2023-10-27T10:10:30Z", "severity": "ERROR", "message": "Database connection failed."},
    ]
    return jsonify(sample_logs)

@app.route('/api/variables', methods=['GET'])
def get_variables() -> Response:
    """
    Basic endpoint to return a list of sample variables.
    """
    return jsonify(sample_variables)

@app.route('/api/variables/<string:variable_name>', methods=['PUT'])
def update_variable(variable_name: str) -> Tuple[Response, int]:
    """
    Endpoint to update a specific variable's value.
    """
    data = request.json
    if not data or 'value' not in data:
        return jsonify({"error": "Invalid request body"}), 400

    # Find and update the variable
    updated_variable = None
    for variable in sample_variables:
        if variable['name'] == variable_name:
            # Attempt to convert the value to the correct type
            try:
                if variable['type'] == 'float':
                    variable['value'] = float(data['value'])
                elif variable['type'] == 'integer':
                    variable['value'] = int(data['value'])
                elif variable['type'] == 'boolean':
                    # Convert string boolean to actual boolean
                    if isinstance(data['value'], str):
                        variable['value'] = data['value'].lower() == 'true'
                    else:
                         variable['value'] = bool(data['value'])
                else:
                    # Default to string for other types
                    variable['value'] = str(data['value'])
                updated_variable = variable
                break
            except ValueError:
                return jsonify({"error": f"Invalid value for type {variable['type']}"}), 400


    if updated_variable:
        return jsonify({"message": "Variable updated successfully", "variable": updated_variable}), 200
    else:
        return jsonify({"error": "Variable not found"}), 404


@app.route('/api/forecasts', methods=['GET'])
def get_forecasts() -> Response:
    """
    Basic endpoint to return a list of sample forecasts.
    """
    sample_forecasts = [
        {"id": "forecast_001", "name": "Sales Forecast Q4", "data": [100, 120, 110]},
        {"id": "forecast_002", "name": "Inventory Forecast Nov", "data": [500, 480, 510]},
    ]
    return jsonify(sample_forecasts)

if __name__ == '__main__':
    # This part is for running the script directly for testing.
    # In a real application, this would be integrated into a larger framework.
    app.run(debug=True, port=5000)