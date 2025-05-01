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

# Base API endpoint prefix
API_PREFIX = '/api'

# === Forecast endpoints ===
@app.route(f'{API_PREFIX}/forecasts', methods=['GET'])
def get_forecasts():
    # Fetch historical forecast data
    limit = request.args.get('limit', default=10, type=int)
    domain = request.args.get('domain', default=None, type=str)
    forecast_history = load_forecast_history(limit=limit, domain_filter=domain)
    return jsonify(forecast_history)

@app.route(f'{API_PREFIX}/forecasts/latest/all', methods=['GET'])
def get_latest_forecasts():
    """Returns the latest forecast values for all variables."""
    try:
        latest_forecasts = {}
        # Get all variables that have forecasts
        forecast_vars = variable_registry.get_forecast_variables()
        
        for var_name in forecast_vars:
            # Get the latest forecast for each variable
            latest_forecasts[var_name] = variable_registry.get_forecast_value(var_name)
            
        return jsonify(latest_forecasts)
    except Exception as e:
        return jsonify({"error": f"Error fetching latest forecasts: {str(e)}"}), 500

@app.route(f'{API_PREFIX}/forecasts/status', methods=['GET'])
def get_forecast_status():
    """Returns the status of the forecasting engine."""
    try:
        # Check if the forecast engine is ready
        # This is a simple implementation; you might want to add more comprehensive checks
        if variable_registry.is_initialized() and feature_store.is_initialized():
            return jsonify({"status": "ready"})
        else:
            return jsonify({"status": "not_ready"})
    except Exception as e:
        return jsonify({"error": f"Error checking forecast engine status: {str(e)}"}), 500

# === Retrodiction endpoints ===
@app.route(f'{API_PREFIX}/retrodiction', methods=['GET'])
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

@app.route(f'{API_PREFIX}/retrodiction/run', methods=['POST'])
def run_retrodiction_simulation():
    """Starts a retrodiction simulation."""
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        start_date = data.get('start_date')
        days = data.get('days', 10)
        variables_of_interest = data.get('variables_of_interest', [])
        
        if not start_date:
            return jsonify({"error": "start_date is required"}), 400
            
        # Generate a unique run ID
        from uuid import uuid4
        run_id = str(uuid4())
        
        # In a real implementation, you'd start this as a background process
        # For now, we'll just store that we've started the simulation
        from threading import Thread
        
        # Start the simulation in a background thread
        Thread(target=_run_retrodiction_background, 
               args=(run_id, start_date, days, variables_of_interest)).start()
        
        return jsonify({"status": "started", "run_id": run_id})
    except Exception as e:
        return jsonify({"error": f"Error starting retrodiction: {str(e)}"}), 500

def _run_retrodiction_background(run_id, start_date, days, variables_of_interest):
    """Runs the retrodiction simulation in the background."""
    from time import sleep
    import json
    import os
    
    # Create a status file for this run
    status = {
        "status": "running",
        "progress": "0%",
        "start_date": start_date,
        "days": days,
        "variables_of_interest": variables_of_interest
    }
    
    # Ensure the directory exists
    os.makedirs("./simulation_engine/runs", exist_ok=True)
    
    with open(f"./simulation_engine/runs/{run_id}.json", "w") as f:
        json.dump(status, f)
    
    try:
        # Simulate work with progress updates
        for i in range(1, 11):
            sleep(1)  # Simulating work
            status["progress"] = f"{i*10}%"
            with open(f"./simulation_engine/runs/{run_id}.json", "w") as f:
                json.dump(status, f)
        
        # Simulate results
        results = {}
        for var in variables_of_interest:
            results[var] = {
                "predicted": [round(0.5 + i*0.1, 2) for i in range(days)],
                "actual": [round(0.6 + i*0.08, 2) for i in range(days)],
                "dates": [(datetime.fromisoformat(start_date) + 
                          datetime.timedelta(days=i)).strftime("%Y-%m-%d") 
                          for i in range(days)]
            }
        
        # Update status to completed with results
        status["status"] = "completed"
        status["results"] = results
        with open(f"./simulation_engine/runs/{run_id}.json", "w") as f:
            json.dump(status, f)
            
    except Exception as e:
        # Update status to failed
        status["status"] = "failed"
        status["error"] = str(e)
        with open(f"./simulation_engine/runs/{run_id}.json", "w") as f:
            json.dump(status, f)

@app.route(f'{API_PREFIX}/retrodiction/status/<run_id>', methods=['GET'])
def get_retrodiction_status(run_id):
    """Gets the status of a retrodiction simulation."""
    try:
        import os
        import json
        
        status_file = f"./simulation_engine/runs/{run_id}.json"
        
        if not os.path.exists(status_file):
            return jsonify({"error": f"No status found for run ID: {run_id}"}), 404
            
        with open(status_file, "r") as f:
            status = json.load(f)
            
        return jsonify(status)
    except Exception as e:
        return jsonify({"error": f"Error getting retrodiction status: {str(e)}"}), 500

# === Autopilot endpoints ===
@app.route(f'{API_PREFIX}/autopilot/status', methods=['GET'])
def get_autopilot_status():
    # Autopilot status endpoint - Not implemented due to missing functions
    return jsonify({"message": "Autopilot status endpoint - Not implemented yet", "status": "unknown"})

@app.route(f'{API_PREFIX}/autopilot/data', methods=['GET'])
def get_autopilot_data():
    # Autopilot data endpoint - Not implemented due to missing functions
    return jsonify({"message": "Autopilot data endpoint - Not implemented yet", "data": {}})

# === Variables endpoints ===
@app.route(f'{API_PREFIX}/variables/current', methods=['GET'])
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

@app.route(f'{API_PREFIX}/variables/historical', methods=['GET'])
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

# === Training Review Submission endpoints ===
@app.route(f'{API_PREFIX}/forecasts/submit_review', methods=['POST'])
def submit_forecast_for_review():
    """
    Submits forecast data for training review.
    Expected POST data: {
        "forecast_data": {...},
        "timestamp": "ISO timestamp",
        "metadata": {
            "submitted_by": "string",
            "submission_type": "string",
            "notes": "string"
        }
    }
    """
    try:
        # Get the request data
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "error": "No data provided"}), 400
            
        # Validate required fields
        if "forecast_data" not in data:
            return jsonify({"status": "error", "error": "Missing forecast_data field"}), 400
            
        # Generate a submission ID
        from datetime import datetime
        import uuid
        
        submission_id = f"forecast-{uuid.uuid4()}"
        timestamp = data.get("timestamp", datetime.now().isoformat())
        
        # Store the submission data
        from core.training_review_store import store_training_submission
        
        metadata = data.get("metadata", {})
        metadata["submission_id"] = submission_id
        metadata["submission_date"] = timestamp
        
        # Store the submission in the training review system
        result = store_training_submission(
            submission_type="forecast",
            submission_id=submission_id,
            data=data["forecast_data"],
            metadata=metadata
        )
        
        if result:
            return jsonify({
                "status": "success", 
                "submission_id": submission_id,
                "message": "Forecast data submitted for training review"
            })
        else:
            return jsonify({
                "status": "error",
                "error": "Failed to store submission data"
            }), 500
            
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": f"Error processing request: {str(e)}"
        }), 500

@app.route(f'{API_PREFIX}/retrodiction/submit_review', methods=['POST'])
def submit_retrodiction_for_review():
    """
    Submits retrodiction results for training review.
    Expected POST data: {
        "retrodiction_data": {...},
        "timestamp": "ISO timestamp",
        "metadata": {
            "submitted_by": "string",
            "submission_type": "string",
            "notes": "string"
        }
    }
    """
    try:
        # Get the request data
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "error": "No data provided"}), 400
            
        # Validate required fields
        if "retrodiction_data" not in data:
            return jsonify({"status": "error", "error": "Missing retrodiction_data field"}), 400
            
        # Generate a submission ID
        from datetime import datetime
        import uuid
        
        submission_id = f"retrodiction-{uuid.uuid4()}"
        timestamp = data.get("timestamp", datetime.now().isoformat())
        
        # Store the submission data
        from core.training_review_store import store_training_submission
        
        metadata = data.get("metadata", {})
        metadata["submission_id"] = submission_id
        metadata["submission_date"] = timestamp
        
        # Store the submission in the training review system
        result = store_training_submission(
            submission_type="retrodiction",
            submission_id=submission_id,
            data=data["retrodiction_data"],
            metadata=metadata
        )
        
        if result:
            return jsonify({
                "status": "success", 
                "submission_id": submission_id,
                "message": "Retrodiction data submitted for training review"
            })
        else:
            return jsonify({
                "status": "error",
                "error": "Failed to store submission data"
            }), 500
            
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": f"Error processing request: {str(e)}"
        }), 500

# === Status endpoint ===
@app.route(f'{API_PREFIX}/status', methods=['GET'])
def get_status():
    """Get the overall system status."""
    return jsonify({
        "status": "online",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    })

if __name__ == '__main__':
    # This is for development purposes. In production, use a proper WSGI server.
    app.run(host='127.0.0.1', port=5002, debug=True)