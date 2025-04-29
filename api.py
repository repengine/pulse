from flask import Flask, jsonify, request
from datetime import datetime

from forecast_engine.forecast_memory import load_forecast_history
from simulation_engine.simulate_backward import run_retrodiction
from core.variable_registry import VariableRegistry
from core.feature_store import FeatureStore

# Autopilot functions not found, leaving as placeholders
# from intelligence.autopilot import get_autopilot_status, get_autopilot_data

# Initialize core components
variable_registry = VariableRegistry()
feature_store = FeatureStore()

app = Flask(__name__)

@app.route('/api/forecasts', methods=['GET'])
def get_forecasts():
    # Fetch historical forecast data
    limit = request.args.get('limit', default=10, type=int)
    domain = request.args.get('domain', default=None, type=str)
    forecast_history = load_forecast_history(limit=limit, domain_filter=domain)
    return jsonify(forecast_history)

@app.route('/api/retrodiction', methods=['GET'])
def get_retrodiction():
    # Fetch retrodiction data
    # Requires snapshot_time and steps parameters
    snapshot_time_str = request.args.get('snapshot_time')
    steps = request.args.get('steps', default=10, type=int)
    
    if not snapshot_time_str:
        return jsonify({"error": "snapshot_time parameter is required"}), 400
        
    # Parse snapshot_time string to datetime object
    try:
        snapshot_time = datetime.fromisoformat(snapshot_time_str)
    except ValueError:
        return jsonify({"error": "Invalid snapshot_time format. Please use ISO 8601 format (e.g., 'YYYY-MM-DDTHH:MM:SS')."}), 400
        
    try:
        retrodiction_data = run_retrodiction(snapshot_time=snapshot_time, steps=steps)
        return jsonify(retrodiction_data)
    except Exception as e:
        return jsonify({"error": f"Error running retrodiction: {e}"}), 500

@app.route('/api/autopilot/status', methods=['GET'])
def get_autopilot_status():
    # Autopilot status endpoint - Not implemented due to missing functions
    return jsonify({"message": "Autopilot status endpoint - Not implemented yet", "status": "unknown"})

@app.route('/api/autopilot/data', methods=['GET'])
def get_autopilot_data():
    # Autopilot data endpoint - Not implemented due to missing functions
    return jsonify({"message": "Autopilot data endpoint - Not implemented yet", "data": {}})

@app.route('/api/variables/current', methods=['GET'])
def get_current_variables():
    # Fetch current variable values
    # Assuming variable_registry has a method to get all current values or a snapshot
    # Based on list_code_definition_names, get_live_value gets one variable at a time.
    # A new method might be needed in VariableRegistry to get all.
    # For now, returning a placeholder or attempting to get a few known variables.
    
    # Attempting to get a few known variables as an example
    current_variables = {
        "example_variable_1": variable_registry.get_live_value("example_variable_1"),
        "example_variable_2": variable_registry.get_live_value("example_variable_2"),
    }
    
    # Note: This requires 'example_variable_1' and 'example_variable_2' to exist and have live bindings.
    # A more robust implementation would iterate through registered variables or have a dedicated method.
    
    return jsonify(current_variables)

@app.route('/api/variables/historical', methods=['GET'])
def get_historical_variables():
    # Fetch historical variable values
    # Requires a variable name parameter
    variable_name = request.args.get('name')
    
    if not variable_name:
        return jsonify({"error": "name parameter is required"}), 400
        
    try:
        # Assuming feature_store.get returns a pandas Series or similar
        historical_data = feature_store.get(variable_name)
        # Convert pandas Series to dictionary for JSON response
        if historical_data is not None:
            return jsonify(historical_data.to_dict())
        else:
            return jsonify({"error": f"Historical data for {variable_name} not found"}), 404
    except Exception as e:
        return jsonify({"error": f"Error fetching historical data: {e}"}), 500

if __name__ == '__main__':
    # This is for development purposes. In production, use a proper WSGI server.
    app.run(debug=True)