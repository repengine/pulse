from flask import Flask, render_template, jsonify, request, redirect, url_for, flash
from waitress import serve # Import waitress
import random
import datetime
import json # For Plotly JSON encoding
import plotly.graph_objects as go
import plotly.io as pio
import pandas as pd
import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error
import typing # Import typing

# Attempt simulation engine imports
try:
    # Attempt to import simulation components. The code below will check if they exist.
    from simulation_engine.simulator_core import simulate_forward, WorldState
except ImportError:
    # Log the warning, but don't define dummies. Checks later will handle absence.
    print("WARNING: Could not import simulation_engine components (WorldState, simulate_forward). Retrodiction will be skipped.")
    # Ensure the names exist but are None, so 'in globals()' checks work predictably.
    # This might not be strictly necessary depending on Python version, but adds safety.
    if 'WorldState' not in globals(): WorldState = None
    if 'simulate_forward' not in globals(): simulate_forward = None


# Attempt to import the historical data fetching function
try:
    # Adjust the path based on your project structure if necessary
    from iris.iris_plugins_variable_ingestion.historical_ingestion_plugin import fetch_historical_yfinance_close
except ImportError:
    # Provide a dummy function if the import fails, so the app can still run
    print("WARNING: Could not import fetch_historical_yfinance_close from iris plugin. Using dummy function.")
    def fetch_historical_yfinance_close(ticker: str, start_date: datetime.datetime, end_date: datetime.datetime) -> pd.Series | None:
        """Dummy function to simulate fetching data if the real import fails. Matches expected signature."""
        print(f"DUMMY: Fetching {ticker} from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        # Return a dummy pandas Series matching expected output (or None, though this dummy doesn't return None)
        try:
            start = pd.to_datetime(start_date)
            end = pd.to_datetime(end_date)
            # Ensure start is before end
            if start > end:
                start, end = end, start # Swap if needed
            dates = pd.date_range(start=start, end=end, freq='B') # Business days
            if dates.empty:
                return pd.Series(dtype=float) # Return empty series if date range is invalid or empty
            values = [100 + (i % 10) + random.uniform(-2, 2) for i in range(len(dates))] # Simple dummy data
            return pd.Series(values, index=dates, name='Close')
        except Exception as e:
             print(f"DUMMY ERROR: Failed to generate dummy data: {e}")
             return pd.Series(dtype=float) # Return empty series on error
import os # Added import

# Initialize Flask App
app = Flask(__name__)
app.secret_key = 'dev_secret_key' # Required for flash messages - use a proper secret in production!

# --- Simulated Global State ---
# Replace with a more robust state management solution later
SIMULATED_RECURSIVE_LEARNING_ENABLED = True # Initial state
SIMULATED_AUTOPILOT_STATUS = {"state": "Idle", "current_run": None} # Example state: Idle, Running, Stopped, Error
SIMULATED_AUTOPILOT_HISTORY = [
    {"id": "ap_run_001", "start_time": "2025-04-28 08:00:00", "end_time": "2025-04-28 09:00:00", "goal": "Optimize Alpha", "constraints": "Max CPU 80%", "status": "Completed"},
    {"id": "ap_run_002", "start_time": "2025-04-28 11:00:00", "end_time": "2025-04-28 11:15:00", "goal": "Explore Beta", "constraints": "None", "status": "Stopped"},
]
SIMULATED_VARIABLE_NAMES = ["Temperature_Sensor_A", "Pressure_Valve_X", "Market_Index_SPY", "User_Activity_Score", "System_Load_CPU"]

# Simulated Variable State (for editing)
# This structure holds the current value and type for each variable
SIMULATED_VARIABLE_STATE = {
    "Temperature_Sensor_A": {"value": 22.5, "type": "number"},
    "Pressure_Valve_X": {"value": 150.0, "type": "number"},
    "Market_Index_SPY": {"value": 5200.50, "type": "number"},
    "User_Activity_Score": {"value": 85, "type": "number"},
    "System_Load_CPU": {"value": 0.35, "type": "number"},
    # Add a boolean example
    "Recursive_Learning_Enabled": {"value": True, "type": "boolean"}
}


# --- Placeholder Backend Functions ---
# These simulate fetching data from the core Pulse system.
# Replace these with actual calls later.

def get_system_status():
    """Simulates fetching the overall system status."""
    # Possible values: Operational, Idle, Warning, Error
    return random.choice(["Operational", "Idle", "Warning"]) # Add some randomness

def get_active_processes():
    """Simulates fetching a list of currently running tasks."""
    processes = ["Forecasting Cycle #124", "Autopilot Run 'Optimize Alpha'", "Memory Consolidation"]
    # Include autopilot if running
    current_ap_status = get_autopilot_status()
    if current_ap_status["state"] == "Running":
        run_info = current_ap_status["current_run"]
        processes.append(f"Autopilot Run '{run_info['goal']}' ({run_info['id']})")
    return random.sample(processes, k=random.randint(0, len(processes))) # Random subset

def get_retrodiction_runs():
    """Simulates fetching a list of available retrodiction run IDs/names."""
    return [
        {"id": "retro_run_001", "timestamp": "2025-04-27 10:00:00", "name": "Initial Baseline"},
        {"id": "retro_run_002", "timestamp": "2025-04-28 09:30:00", "name": "Post-Parameter Tuning"},
        {"id": "retro_run_003", "timestamp": "2025-04-28 14:15:00", "name": "Latest Analysis"},
    ]

def get_retrodiction_data(run_id: str):
    """
    Simulates fetching detailed data for a specific retrodiction run
    and generating a Plotly figure.
    """
    print(f"Simulating data fetch for run_id: {run_id}") # Log to console
    if run_id == "retro_run_001":
        base_data = {
            "run_id": run_id, "name": "Initial Baseline", "timestamp": "2025-04-27 10:00:00",
            "summary_metrics": {"accuracy": 0.85, "relevance": 0.75, "f1_score": 0.80},
            "insights": "Initial model shows good baseline accuracy but struggles with relevance on edge cases.",
            "chart_data": {"type": "bar", "labels": ["A", "B", "C"], "values": [10, 20, 15]},
            "detailed_data": [{"feature": "X1", "importance": 0.5}, {"feature": "X2", "importance": 0.3}, {"feature": "X3", "importance": 0.2}]
        }
    elif run_id == "retro_run_002":
         base_data = {
            "run_id": run_id, "name": "Post-Parameter Tuning", "timestamp": "2025-04-28 09:30:00",
            "summary_metrics": {"accuracy": 0.88, "relevance": 0.82, "f1_score": 0.85},
            "insights": "Parameter tuning improved both accuracy and relevance significantly. Model is more robust.",
            "chart_data": {"type": "line", "labels": ["T1", "T2", "T3"], "values": [5, 8, 6]},
            "detailed_data": [{"feature": "X1", "importance": 0.45}, {"feature": "X2", "importance": 0.35}, {"feature": "X3", "importance": 0.20}]
        }
    else: # Default for run_003 or others
        base_data = {
            "run_id": run_id, "name": "Latest Analysis", "timestamp": "2025-04-28 14:15:00",
            "summary_metrics": {"accuracy": 0.90, "relevance": 0.85, "f1_score": 0.87},
            "insights": "Latest model performs well across most metrics. Minor drift detected in feature X3.",
            "chart_data": {"type": "scatter", "labels": ["P1", "P2", "P3"], "values": [12, 9, 15]},
            "detailed_data": [{"feature": "X1", "importance": 0.48}, {"feature": "X2", "importance": 0.32}, {"feature": "X3", "importance": 0.20}]
        }
    return base_data # Return base data, figure generation moved to API route

def get_forecast_sets():
    """Simulates fetching a list of available forecast sets."""
    return [
        {"id": "fc_set_A", "timestamp": "2025-04-28 10:00:00", "name": "Daily Market Trend"},
        {"id": "fc_set_B", "timestamp": "2025-04-28 11:30:00", "name": "Weekly Sentiment Analysis"},
        {"id": "fc_set_C", "timestamp": "2025-04-28 15:00:00", "name": "Hourly System Load"},
    ]

def get_forecast_data(set_id: str):
    """
    Simulates fetching detailed data for a specific forecast set.
    Figure generation moved to API route.
    """
    print(f"Simulating data fetch for forecast set_id: {set_id}")
    # Simulate time series data
    base_time = datetime.datetime.now()
    time_points = [(base_time + datetime.timedelta(hours=i)).strftime("%Y-%m-%d %H:%M") for i in range(10)]
    base_value = random.uniform(50, 100)
    values = [base_value + random.uniform(-5, 5) + i*0.5 for i in range(10)] # Simple trend + noise
    upper_bound = [v + random.uniform(2, 5) for v in values]
    lower_bound = [v - random.uniform(2, 5) for v in values]
    # Simulate actual values based on the forecast with more noise
    actual_values = [v + random.uniform(-4, 4) + random.choice([-1, 1]) * i * 0.1 for i, v in enumerate(values)]


    # Simulate some metrics
    metrics = {
        "mean_absolute_error": round(random.uniform(1, 5), 2),
        "confidence_score": round(random.uniform(0.7, 0.95), 3),
        "horizon": "10 hours"
    }

    # Return data needed for chart generation
    return {
        "set_id": set_id,
        "metrics": metrics,
        "chart_data": { # Data for chart, not the figure itself
             "time_points": time_points,
             "values": values,
             "upper_bound": upper_bound,
             "lower_bound": lower_bound,
             "actual_values": actual_values # Add actuals here
        }
    }
def get_all_variable_names():
    """Simulates fetching the list of all available variable names."""
    global SIMULATED_VARIABLE_NAMES
    # Also include the variable from the simulated state
    all_names = list(set(SIMULATED_VARIABLE_NAMES + list(SIMULATED_VARIABLE_STATE.keys())))
    return all_names

@app.route('/api/variables/<variable_name>', methods=['GET'])
def api_get_variable(variable_name):
    """API endpoint to get the current value and type for a specific variable."""
    global SIMULATED_VARIABLE_STATE
    variable_info = SIMULATED_VARIABLE_STATE.get(variable_name)
    if variable_info:
        return jsonify({"name": variable_name, "value": variable_info["value"], "type": variable_info["type"]})
    else:
        return jsonify({"error": "Variable not found"}), 404

@app.route('/api/variables/<variable_name>', methods=['PUT'])
def api_update_variable(variable_name):
    """API endpoint to update the value of a specific variable."""
    global SIMULATED_VARIABLE_STATE
    if variable_name not in SIMULATED_VARIABLE_STATE:
        return jsonify({"error": "Variable not found"}), 404

    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 415

    data = request.get_json()
    if 'value' not in data:
        return jsonify({"error": "Missing 'value' in request body"}), 400

    new_value = data['value']
    current_type = SIMULATED_VARIABLE_STATE[variable_name]["type"]

    # Basic type validation (can be expanded)
    if current_type == "number":
        try:
            new_value = float(new_value)
        except (ValueError, TypeError):
            return jsonify({"error": f"Invalid value for number type: {new_value}"}), 400
    elif current_type == "boolean":
        if not isinstance(new_value, bool):
             # Attempt to convert string "true" or "false"
             if isinstance(new_value, str):
                 if new_value.lower() == 'true':
                     new_value = True
                 elif new_value.lower() == 'false':
                     new_value = False
                 else:
                     return jsonify({"error": f"Invalid value for boolean type: {new_value}"}), 400
             else:
                return jsonify({"error": f"Invalid value for boolean type: {new_value}"}), 400
    # Add other type checks as needed (e.g., string, list)

    SIMULATED_VARIABLE_STATE[variable_name]["value"] = new_value
    print(f"Updated variable '{variable_name}' to value: {new_value}")

    return jsonify({"message": f"Variable '{variable_name}' updated successfully.", "value": new_value, "type": current_type})


def get_variable_data(variable_name: str):
    """
    Simulates fetching historical data for a specific variable
    and generating simulated time-series data.
    """
    global SIMULATED_VARIABLE_NAMES
    # Check if the variable exists in either the historical names or the simulated state
    if variable_name not in SIMULATED_VARIABLE_NAMES and variable_name not in SIMULATED_VARIABLE_STATE:
        return None # Variable not found

    print(f"Simulating data fetch for variable: {variable_name}")

    # Simulate time series data - make it slightly different per variable
    base_time = datetime.datetime.now() - datetime.timedelta(days=1) # Start from yesterday
    num_points = 50
    timestamps = [(base_time + datetime.timedelta(minutes=i*30)).strftime("%Y-%m-%d %H:%M:%S") for i in range(num_points)]

    # Generate values with some variation based on name hash
    # Use a consistent seed for reproducibility based on variable name
    random.seed(hash(variable_name))
    base_value = abs(hash(variable_name)) % 100 # Base value based on name
    noise_factor = (abs(hash(variable_name + "noise")) % 10) / 10.0 + 0.5 # Noise level
    trend_factor = (hash(variable_name + "trend") % 3) - 1 # Trend direction (-1, 0, 1)

    values = []
    current_value = base_value
    for i in range(num_points):
        noise = random.uniform(-1, 1) * noise_factor * (base_value / 20 + 1) # Scale noise with base
        trend = trend_factor * i * 0.05 # Gentle trend
        current_value += noise + trend
        # Add some occasional larger jumps for specific variables
        if "Sensor" in variable_name and random.random() < 0.05:
             current_value += random.uniform(-5, 5) * noise_factor
        elif "Index" in variable_name and random.random() < 0.02:
             current_value *= random.uniform(0.95, 1.05)
        values.append(round(current_value, 2))

    # Reset random seed for other functions
    random.seed(datetime.datetime.now().timestamp())


    return {
        "name": variable_name,
        "timestamps": timestamps,
        "values": values
    }

def get_recent_activity(limit=5):
    """Simulates fetching the latest activity log entries."""
    now = datetime.datetime.now()
    activities = [
        {"ts": (now - datetime.timedelta(minutes=random.randint(1,5))).strftime("%Y-%m-%d %H:%M:%S"), "msg": "Forecast 'fc_20250428_1540' generated."},
        {"ts": (now - datetime.timedelta(minutes=random.randint(5,15))).strftime("%Y-%m-%d %H:%M:%S"), "msg": "Autopilot run 'Optimize Alpha' completed."},
        {"ts": (now - datetime.timedelta(minutes=random.randint(15,25))).strftime("%Y-%m-%d %H:%M:%S"), "msg": "Retrodiction analysis started for run 'retro_xyz'."},
        {"ts": (now - datetime.timedelta(minutes=random.randint(25,40))).strftime("%Y-%m-%d %H:%M:%S"), "msg": "Recursive learning status changed to Enabled."},
        {"ts": (now - datetime.timedelta(minutes=random.randint(40,60))).strftime("%Y-%m-%d %H:%M:%S"), "msg": "System status changed to Idle."},
        {"ts": (now - datetime.timedelta(minutes=random.randint(60,90))).strftime("%Y-%m-%d %H:%M:%S"), "msg": "Memory Explorer query executed."},
    ]
    random.shuffle(activities)
    return activities[:limit]

def get_recursive_learning_status():
    """Gets the current simulated recursive learning mode status."""
    global SIMULATED_RECURSIVE_LEARNING_ENABLED
    return SIMULATED_RECURSIVE_LEARNING_ENABLED

def set_recursive_learning_status(new_status: bool):
    """Sets the simulated recursive learning mode status."""
    global SIMULATED_RECURSIVE_LEARNING_ENABLED
    SIMULATED_RECURSIVE_LEARNING_ENABLED = new_status
    print(f"Recursive learning status set to: {new_status}") # Log change
    return True # Indicate success/failure

# --- Autopilot Placeholders ---

def get_autopilot_status():
    """Simulates fetching the current autopilot status."""
    global SIMULATED_AUTOPILOT_STATUS
    return SIMULATED_AUTOPILOT_STATUS

def get_autopilot_run_history(limit=10):
    """Simulates fetching the autopilot run history."""
    global SIMULATED_AUTOPILOT_HISTORY
    return sorted(SIMULATED_AUTOPILOT_HISTORY, key=lambda x: x["start_time"], reverse=True)[:limit]

def start_autopilot_run(goal: str, constraints: str):
    """Simulates starting an autopilot run."""
    global SIMULATED_AUTOPILOT_STATUS, SIMULATED_AUTOPILOT_HISTORY
    if SIMULATED_AUTOPILOT_STATUS["state"] == "Running":
        print("Autopilot already running.")
        return False, "Autopilot already running."

    run_id = f"ap_run_{len(SIMULATED_AUTOPILOT_HISTORY) + 1:03d}"
    start_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_run = {
        "id": run_id, "start_time": start_time, "end_time": None,
        "goal": goal, "constraints": constraints, "status": "Running"
    }
    SIMULATED_AUTOPILOT_STATUS = {"state": "Running", "current_run": new_run}
    SIMULATED_AUTOPILOT_HISTORY.insert(0, new_run) # Prepend for easy sorting
    print(f"Autopilot run {run_id} started. Goal: {goal}, Constraints: {constraints}")
    return True, f"Autopilot run {run_id} started."

def stop_autopilot_run():
    """Simulates stopping the current autopilot run."""
    global SIMULATED_AUTOPILOT_STATUS, SIMULATED_AUTOPILOT_HISTORY
    if SIMULATED_AUTOPILOT_STATUS["state"] != "Running":
        print("Autopilot is not running.")
        return False, "Autopilot is not running."

    run_id = SIMULATED_AUTOPILOT_STATUS["current_run"]["id"]
    end_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Update history
    for run in SIMULATED_AUTOPILOT_HISTORY:
        if run["id"] == run_id:
            run["end_time"] = end_time
            run["status"] = "Stopped"
            break

    SIMULATED_AUTOPILOT_STATUS = {"state": "Stopped", "current_run": None}
    print(f"Autopilot run {run_id} stopped.")
    return True, f"Autopilot run {run_id} stopped."

# Helper function to read the latest forecast data from the compressed log file
def get_latest_forecast_from_log(variable_name: str):
    """
    Reads the *last line* of logs/forecast_output_compressed.jsonl,
    parses the JSON, and extracts forecast data for the specified variable_name
    from the 'examples' list within that JSON object.
    """
    last_line_data = None
    log_file_path = os.path.join(os.path.dirname(__file__), '..', 'logs', 'forecast_output_compressed.jsonl')
    print(f"Attempting to read forecast log: {log_file_path}")

    try:
        if not os.path.exists(log_file_path):
            print(f"Error: Log file not found at {log_file_path}")
            return None, "Log file not found."

        # Read the last line of the file
        with open(log_file_path, 'rb') as f: # Open in binary mode for seeking
            try:
                f.seek(-2, os.SEEK_END) # Jump near the end, handle potential newline
                while f.read(1) != b'\n':
                    f.seek(-2, os.SEEK_CUR)
            except OSError: # Handle file smaller than buffer or beginning of file
                f.seek(0)
            last_line = f.readline().decode('utf-8')

        if not last_line.strip():
             print(f"Error: Last line of log file is empty or invalid.")
             return None, "Last line of log file is empty or invalid."

        # Parse the JSON from the last line
        try:
            last_line_data = json.loads(last_line)
        except json.JSONDecodeError:
            print(f"Error: Failed to decode JSON from the last line: {last_line.strip()}")
            return None, "Failed to decode JSON from the last log entry."

        # Check for 'examples' key and structure
        if not isinstance(last_line_data, dict) or 'examples' not in last_line_data or not isinstance(last_line_data['examples'], list):
            print(f"Error: Last log entry JSON does not contain a valid 'examples' list.")
            return None, "Last log entry JSON does not contain a valid 'examples' list."

        examples = last_line_data['examples']
        if not examples:
            print(f"Error: 'examples' list in the last log entry is empty.")
            return None, f"'examples' list in the last log entry is empty for {variable_name}."

        # Extract timestamps and values for the specific variable
        timestamps = []
        values = []
        for example in examples:
            try:
                # Safely access nested keys
                timestamp = example['timestamp']
                value = example['exposure'][variable_name]
                timestamps.append(timestamp)
                values.append(value)
            except KeyError as e:
                # Skip examples where the variable or required keys are missing
                print(f"Warning: Skipping example due to missing key: {e}. Example: {example}")
                continue
            except TypeError:
                 print(f"Warning: Skipping example due to unexpected structure. Example: {example}")
                 continue

        # Check if any data was actually found for the variable
        if not timestamps:
            print(f"Error: No valid data points found for '{variable_name}' in the 'examples' of the last log entry.")
            return None, f"No forecast data found for '{variable_name}' in the latest log entry."

        print(f"Successfully extracted {len(timestamps)} data points for '{variable_name}' from the last log entry.")
        return {
            "timestamps": timestamps,
            "values": values,
            # Bounds are not available in this structure
            "upper_bound": None,
            "lower_bound": None
        }, None # Return data and no error message

    except FileNotFoundError: # Should be caught by os.path.exists, but keep for safety
        print(f"Error: Log file not found at {log_file_path}")
        return None, "Log file not found."
    except Exception as e:
        print(f"Error: Failed to read or process log file {log_file_path}: {e}")
        # Add more specific error logging if needed
        import traceback
        traceback.print_exc()
        return None, f"Failed to read or process log file: {e}"

# --- Routes ---

@app.route('/')
def dashboard():
    """Renders the main dashboard page."""
    system_status = get_system_status()
    active_processes = get_active_processes()
    recent_activity = get_recent_activity()
    recursive_learning_status = get_recursive_learning_status()
    recursive_learning_status_str = "Enabled" if recursive_learning_status else "Disabled"
    return render_template('dashboard.html',
                           system_status=system_status,
                           active_processes=active_processes,
                           recent_activity=recent_activity,
                           recursive_learning_status=recursive_learning_status_str)

@app.route('/retrodiction')
def retrodiction():
    """Renders the retrodiction view page."""
    runs = get_retrodiction_runs()
    return render_template('retrodiction.html', runs=runs)

@app.route('/forecasting')
def forecasting():
    """Renders the forecasting view page."""
    forecast_sets = get_forecast_sets()
    return render_template('forecasting.html', forecast_sets=forecast_sets)

@app.route('/memory_explorer')
def memory_explorer():
    """Renders the memory explorer view page."""
    # Fetch initial items (e.g., all categories for browsing)
    items_by_category = get_memory_items()
    return render_template('memory_explorer.html', items_by_category=items_by_category)

@app.route('/autopilot')
def autopilot():
    """Renders the autopilot control view page."""
    status = get_autopilot_status()
    history = get_autopilot_run_history()
    return render_template('autopilot.html', status=status, history=history)

@app.route('/variables')
def variable_explorer():
    """Renders the variable explorer page."""
    return render_template('variable_explorer.html')
@app.route('/settings', methods=['GET', 'POST'])
def settings():
    """Renders the settings view page and handles updates."""
    if request.method == 'POST':
        new_status = 'recursive_learning' in request.form
        success = set_recursive_learning_status(new_status)
        if success:
            flash(f"Recursive Learning status updated to {'Enabled' if new_status else 'Disabled'}.", 'success')
        else:
            flash("Failed to update Recursive Learning status.", 'error')
        return redirect(url_for('settings'))

    recursive_learning_enabled = get_recursive_learning_status()
    return render_template('settings.html', recursive_learning_enabled=recursive_learning_enabled)

# --- API Endpoints ---

# --- Memory Explorer Placeholders ---
SIMULATED_MEMORY_ITEMS = {
    "rules": [
        {"id": "R001", "name": "Rule: High Temp -> Alert", "type": "Rule", "confidence": 0.95, "source": "Learned"},
        {"id": "R002", "name": "Rule: Low Pressure -> Warning", "type": "Rule", "confidence": 0.88, "source": "Manual"},
        {"id": "R003", "name": "Rule: Usage Spike -> Scale Up", "type": "Rule", "confidence": 0.91, "source": "Learned"},
    ],
    "concepts": [
        {"id": "C001", "name": "Concept: Temperature Drift", "type": "Concept", "relevance": 0.7, "tags": ["sensor", "anomaly"]},
        {"id": "C002", "name": "Concept: Market Sentiment", "type": "Concept", "relevance": 0.9, "tags": ["finance", "trend"]},
    ],
    "facts": [
         {"id": "F001", "name": "Fact: Sensor S1 Offline", "type": "Fact", "timestamp": "2025-04-28 12:00:00", "source": "Observation"},
         {"id": "F002", "name": "Fact: User Feedback Received", "type": "Fact", "timestamp": "2025-04-28 14:30:00", "source": "Input"},
    ]
}

def get_memory_items(item_type=None):
    """Simulates fetching memory items, optionally filtered by type."""
    if item_type and item_type.lower() in SIMULATED_MEMORY_ITEMS:
        return {item_type.lower(): SIMULATED_MEMORY_ITEMS[item_type.lower()]}
    else:
        # Return all items structured by category
        return SIMULATED_MEMORY_ITEMS

def get_memory_item_details(item_id):
    """Simulates fetching details for a specific memory item."""
    print(f"Fetching details for memory item: {item_id}")
    for category_items in SIMULATED_MEMORY_ITEMS.values():
        for item in category_items:
            if item["id"] == item_id:
                # Simulate more details based on type
                details = item.copy()
                details["description"] = f"Detailed description for {item['name']} ({item_id}). Lorem ipsum dolor sit amet."
                details["created_at"] = "2025-04-20 10:00:00" # Example static detail
                details["last_updated"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                details["related_items"] = [f"REL_{random.randint(1,10)}" for _ in range(random.randint(0,3))] # Example related IDs
                if item['type'] == 'Rule':
                    details['conditions'] = ["Condition A", "Condition B"]
                    details['action'] = "Perform Action X"
                elif item['type'] == 'Concept':
                    details['attributes'] = {"attr1": "value1", "attr2": "value2"}
                return details
    return None # Not found
@app.route('/api/retrodiction_data/<run_id>')
def api_retrodiction_data(run_id):
    """API endpoint to get data for a specific retrodiction run."""
    data = get_retrodiction_data(run_id)
    if not data:
        return jsonify({"error": "Run not found"}), 404

    # Generate Plotly Figure based on chart_data
    fig = None
    chart_info = data.get("chart_data")
    if chart_info:
        chart_type = chart_info.get("type")
        labels = chart_info.get("labels")
        values = chart_info.get("values")
        if chart_type == "bar":
            fig = go.Figure(data=[go.Bar(x=labels, y=values)])
        elif chart_type == "line":
            fig = go.Figure(data=[go.Scatter(x=labels, y=values, mode='lines+markers')])
        elif chart_type == "scatter":
             fig = go.Figure(data=[go.Scatter(x=labels, y=values, mode='markers')])
        if fig:
             fig.update_layout(title=f"Chart for {data['name']}")

    # Convert figure to JSON string if it exists
    chart_json = pio.to_json(fig) if fig else None
    data['chart_json'] = chart_json # Add the JSON string to the response
    data.pop("chart_data", None) # Remove original chart_data dict

    return jsonify(data)

@app.route('/api/forecast_data/<set_id>')
def api_forecast_data(set_id):
    """API endpoint to get data for a specific forecast set."""
    data = get_forecast_data(set_id)
    if not data:
        return jsonify({"error": "Forecast set not found"}), 404

    # Generate Plotly Figure based on chart_data
    fig = None
    # Generate Plotly Figure based on chart_data
    fig = None
    chart_info = data.get("chart_data")
    if chart_info:
         # Generate Plotly Figure with confidence bounds
        fig = go.Figure([
            # Forecast Line
            go.Scatter(name='Forecast', x=chart_info['time_points'], y=chart_info['values'], mode='lines', line=dict(color='rgb(31, 119, 180)')),
            # Confidence Bounds (invisible lines for fill area)
            go.Scatter(name='Upper Bound', x=chart_info['time_points'], y=chart_info['upper_bound'], mode='lines', marker=dict(color="#444"), line=dict(width=0), showlegend=False),
            go.Scatter(name='Lower Bound', x=chart_info['time_points'], y=chart_info['lower_bound'], marker=dict(color="#444"), line=dict(width=0), mode='lines', fillcolor='rgba(68, 68, 68, 0.3)', fill='tonexty', showlegend=False, hoverinfo='skip'), # Skip hover for bounds area
             # Actual Values Line/Markers
            go.Scatter(name='Actuals', x=chart_info['time_points'], y=chart_info.get('actual_values', []), mode='markers', marker=dict(color='rgb(255, 127, 14)', size=8), line=dict(dash='dot')) # Use .get for safety if actuals are missing
        ])
        fig.update_layout(
            title=f'Forecast vs Actuals for Set {set_id}',
            yaxis_title='Value',
            hovermode="x unified",
            legend_title_text='Legend' # Add a legend title
        )

    # Convert figure to JSON string if it exists
    chart_json = pio.to_json(fig) if fig else None
    data['chart_json'] = chart_json # Add the JSON string to the response
    data.pop("chart_data", None) # Remove original chart_data dict

    return jsonify(data)

@app.route('/api/forecasts/list')
def api_forecasts_list():
    """API endpoint to get the list of available forecast sets."""
    forecast_sets = get_forecast_sets()
    return jsonify(forecast_sets)

@app.route('/api/forecast_data/variable/<variable_name>')
def api_forecast_data_variable(variable_name):
    """
    API endpoint to get the latest forecast data for a specific variable
    by parsing the 'examples' list from the last line of the compressed log file.
    """
    print(f"API request received for variable: {variable_name}")
    forecast_data, error_msg = get_latest_forecast_from_log(variable_name)

    if error_msg:
        # Use 404 for "not found" errors (file or data points), 500 otherwise
        status_code = 404 if "not found" in error_msg.lower() or "no forecast data found" in error_msg.lower() else 500
        print(f"API Error for {variable_name}: {error_msg} (Status: {status_code})")
        return jsonify({"error": error_msg}), status_code

    if not forecast_data:
        # Fallback, should be caught by error_msg
        print(f"API Error for {variable_name}: Unknown error retrieving data.")
        return jsonify({"error": "Failed to retrieve forecast data."}), 500

    # Generate Plotly Figure based on the extracted data (timestamps and values only)
    fig = None
    try:
        fig = go.Figure()

        fig.add_trace(go.Scatter(
            name='Forecast',
            x=forecast_data['timestamps'], # From the 'examples' list
            y=forecast_data['values'],     # From the 'examples' list
            mode='lines+markers',          # Show markers as well
            line=dict(color='rgb(31, 119, 180)')
        ))

        # Confidence bounds are NOT plotted as they are not in the 'examples' structure
        fig.update_layout(
            title=f'Latest Forecast Exposure for {variable_name}', # Updated title
            yaxis_title='Forecasted Exposure Value', # Updated axis label
            xaxis_title='Timestamp',
            hovermode="x unified",
            legend_title_text='Data Series' # Updated legend title
        )

        chart_json = pio.to_json(fig)
        print(f"Successfully generated Plotly JSON for {variable_name} from last log entry.")
        return jsonify({"variable_name": variable_name, "chart_json": chart_json})

    except Exception as e:
        print(f"Error generating Plotly JSON for {variable_name}: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Failed to generate chart: {e}"}), 500

@app.route('/api/autopilot/start', methods=['POST'])
def api_autopilot_start():
    """API endpoint to start an autopilot run."""
    if not request.is_json: return jsonify({"error": "Request must be JSON"}), 415
    data = request.get_json()
    goal = data.get('goal')
    constraints = data.get('constraints', 'None') # Default constraints
    if not goal: return jsonify({"error": "Goal is required"}), 400

    success, message = start_autopilot_run(goal, constraints)
    status_code = 200 if success else (409 if "already running" in message else 400)
    return jsonify({"message": message, "status": get_autopilot_status()}), status_code

@app.route('/api/autopilot/stop', methods=['POST'])
def api_autopilot_stop():
    """API endpoint to stop the current autopilot run."""
    success, message = stop_autopilot_run()
    status_code = 200 if success else 400
    return jsonify({"message": message, "status": get_autopilot_status()}), status_code

@app.route('/api/memory_item/<item_id>')
def api_memory_item_details(item_id):
    """API endpoint to get details for a specific memory item."""
    details = get_memory_item_details(item_id)
    if details:
        return jsonify(details)
    else:
        return jsonify({"error": "Memory item not found"}), 404

@app.route('/api/system_status')
def api_system_status():
    """API endpoint to get system status."""
    status_data = {
        "status": get_system_status(),
        "active_processes": get_active_processes(),
        "recursive_learning": get_recursive_learning_status(),
        "cpu_usage": round(random.uniform(5, 50), 1), # Example metric
        "memory_usage": round(random.uniform(100, 1000), 1) # Example metric
    }
    return jsonify(status_data)
@app.route('/api/variables/list')
def api_variables_list():
    """API endpoint to get the list of available variable names."""
    variable_names = get_all_variable_names()
    return jsonify(variable_names)

@app.route('/api/variables/data/<variable_name>')
def api_variable_data(variable_name):
    """API endpoint to get historical data and chart for a specific variable."""
    data = get_variable_data(variable_name)
    if not data:
        return jsonify({"error": "Variable not found"}), 404

    # Generate Plotly Figure
    fig = None
    timestamps = data.get("timestamps")
    values = data.get("values")

    if timestamps and values:
        fig = go.Figure(data=[go.Scatter(x=timestamps, y=values, mode='lines+markers', name=variable_name)])
        fig.update_layout(
            title=f"Historical Data for {variable_name}",
            xaxis_title="Timestamp",
            yaxis_title="Value",
            hovermode="x unified"
        )

    # Convert figure to JSON string if it exists
    chart_json = pio.to_json(fig) if fig else None

    # Prepare response
    response_data = {
        "name": variable_name,
        "chart_json": chart_json
    }

    return jsonify(response_data)


@app.route('/api/data/overview')
def api_data_overview():
    """API endpoint to get an overview of available data."""
    data_overview = {
      "overview": [
        "System Status",
        "Active Processes",
        "Recent Activity",
        "Available Variables",
        "Forecast Sets",
        "Retrodiction Runs"
      ]
    }
    return jsonify(data_overview)

@app.route('/api/logs')
def api_logs():
    """API endpoint to get logs with optional filtering and search."""
    severity_filter = request.args.get('severity')
    start_date_str = request.args.get('startDate')
    end_date_str = request.args.get('endDate')
    search_query = request.args.get('search', '').lower() # Case-insensitive search

    # --- Simulated Log Data ---
    # Generate a more extensive list of simulated logs for testing filters
    simulated_logs = []
    now = datetime.datetime.now()
    log_messages = [
        "System initialized successfully.",
        "User 'admin' logged in.",
        "Database connection established.",
        "Processing data batch 101.",
        "Warning: Disk space low on volume C:.",
        "Error: Failed to connect to external API.",
        "Forecast model updated.",
        "Starting daily backup.",
        "User 'guest' logged out.",
        "INFO: Data sync completed.",
        "WARN: High memory usage detected.",
        "ERROR: Unhandled exception in process X.",
        "System shutdown initiated.",
        "INFO: Report generated successfully.",
        "WARN: API response time slow.",
        "DEBUG: Variable 'temp' value is 25.5.", # Add DEBUG level for completeness
        "INFO: Configuration reloaded.",
        "ERROR: File not found: config.yaml.",
        "WARN: Potential data inconsistency detected.",
        "INFO: Scheduled task 'cleanup' finished.",
    ]
    severity_levels = ["INFO", "WARN", "ERROR", "DEBUG"] # Include DEBUG

    for i in range(50): # Generate 50 simulated logs
        timestamp = now - datetime.timedelta(minutes=random.randint(1, 60*24*7)) # Logs from last 7 days
        severity = random.choice(severity_levels)
        message = random.choice(log_messages)
        simulated_logs.append({
            "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "severity": severity,
            "message": message
        })

    # Sort logs by timestamp (most recent first)
    simulated_logs.sort(key=lambda x: x['timestamp'], reverse=True)

    # --- Filtering ---
    filtered_logs = simulated_logs

    if severity_filter:
        filtered_logs = [log for log in filtered_logs if log['severity'] == severity_filter.upper()]

    if start_date_str:
        try:
            start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d')
            # Include logs from the start of the start_date
            filtered_logs = [log for log in filtered_logs if datetime.datetime.strptime(log['timestamp'], "%Y-%m-%d %H:%M:%S") >= start_date]
        except ValueError:
            # Ignore invalid date filter
            pass

    if end_date_str:
        try:
            end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d')
            # Include logs up to the end of the end_date
            end_date = end_date.replace(hour=23, minute=59, second=59)
            filtered_logs = [log for log in filtered_logs if datetime.datetime.strptime(log['timestamp'], "%Y-%m-%d %H:%M:%S") <= end_date]
        except ValueError:
            # Ignore invalid date filter
            pass

    # --- Searching ---
    if search_query:
        filtered_logs = [log for log in filtered_logs if search_query in log['message'].lower()]

    return jsonify(filtered_logs)


# --- Retrodiction Helper Class ---
class HistoricalDataLoader:
    """Simple loader to provide historical data snapshots for retrodiction."""
    def __init__(self, historical_series: pd.Series):
        # Keep the original series to easily access values by integer index later
        self.historical_data = historical_series
        # Ensure the index is sorted if it's a DatetimeIndex, crucial for iloc lookup
        if isinstance(self.historical_data.index, pd.DatetimeIndex):
            self.historical_data = self.historical_data.sort_index()


    def get_snapshot_by_turn(self, turn_index: int) -> dict | None:
        """
        Returns the historical ground truth for the prediction made *at* the given turn index.
        The prediction made at turn_index 't' is for the state at turn 't+1'.
        Therefore, we need to provide the actual historical value from turn 't+1'.
        """
        # Calculate the index corresponding to the ground truth needed for the prediction made at turn_index
        ground_truth_index = turn_index + 1

        if 0 <= ground_truth_index < len(self.historical_data):
            try:
                # Use iloc for integer-based indexing on the Series
                ground_truth_value = self.historical_data.iloc[ground_truth_index]
                # The key here must match the variable name used in WorldState
                return {'nvidia_stock': ground_truth_value}
            except IndexError:
                 # This should theoretically not happen due to the length check, but added for safety
                 print(f"Error: Internal IndexError accessing historical data at index {ground_truth_index}.")
                 return None
            except Exception as e: # Catch other potential errors during access
                 print(f"Error accessing historical data at index {ground_truth_index}: {e}")
                 return None
        else:
            # This occurs when the simulation asks for the ground truth for the turn *after* the last historical point
            # Or if the turn_index itself is invalid.
            # print(f"Debug: Requested ground truth for turn {turn_index} (needs index {ground_truth_index}), which is out of bounds for historical data (length {len(self.historical_data)}).")
            return None


@app.route('/api/retrodiction/compare/nvidia_stock')
def api_retrodiction_compare_nvidia_stock():
    """
    API endpoint to fetch historical NVDA stock data for comparison.
    Includes placeholders for retrodictive data.
    """
    variable_name = "nvidia_stock" # Corresponds to NVDA ticker in the fetch function context
    ticker = "NVDA" # Ticker for yfinance

    # --- Date Handling ---
    try:
        # Default dates: today and one year ago
        end_date_dt = datetime.datetime.now()
        start_date_dt = end_date_dt - datetime.timedelta(days=365)

        # Override with request args if provided
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')

        if start_date_str:
            start_date_dt = datetime.datetime.strptime(start_date_str, '%Y-%m-%d')
        if end_date_str:
            end_date_dt = datetime.datetime.strptime(end_date_str, '%Y-%m-%d')

        # Basic validation: start date should not be after end date
        if start_date_dt > end_date_dt:
            return jsonify({"error": "Start date cannot be after end date."}), 400

    except ValueError:
        return jsonify({"error": "Invalid date format. Please use YYYY-MM-DD."}), 400
    except Exception as e:
         print(f"Error processing dates: {e}")
         return jsonify({"error": f"Internal server error processing dates: {e}"}), 500


    # --- Fetch Historical Data ---
    hist_timestamps = []
    hist_values = []
    hist_data: pd.Series | None = None # Initialize hist_data to None with type hint
    try:
        print(f"Fetching historical data for {ticker} from {start_date_dt.strftime('%Y-%m-%d')} to {end_date_dt.strftime('%Y-%m-%d')}")
        # Use the (potentially dummy) imported function
        hist_data = fetch_historical_yfinance_close(ticker=ticker, start_date=start_date_dt, end_date=end_date_dt)

        if hist_data is not None and not hist_data.empty:
            # Convert pandas Series to lists for JSON
            # Ensure index is datetime before formatting
            if isinstance(hist_data.index, pd.DatetimeIndex):
                 hist_timestamps = hist_data.index.strftime('%Y-%m-%dT%H:%M:%S').tolist() # ISO 8601 format often preferred for JS
            else:
                 # Handle non-datetime index if necessary, though yfinance usually returns DatetimeIndex
                 hist_timestamps = hist_data.index.astype(str).tolist()
            hist_values = hist_data.values.tolist()
            print(f"Successfully fetched {len(hist_values)} historical data points for {ticker}.")
        else:
            print(f"No historical data returned for {ticker} in the specified range.")
            # Keep lists empty if no data

    except Exception as e:
        print(f"Error fetching historical data for {ticker}: {e}")
        # Return error but still with the basic structure and empty historical lists
        # Don't return 500 here, just log the error and return empty data for now
        # return jsonify({"error": f"Failed to fetch historical data: {e}"}), 500
        pass # Keep lists empty


    # --- Retrodiction Simulation ---
    retrodictive_values = []
    accuracy_metrics = {}
    retrodictive_timestamps = [] # Will align with historical[1:]

    # Only run simulation if we have historical data (at least 2 points needed for 1 simulation step)
    if hist_values and len(hist_values) > 1:
        # Check if simulation components were imported successfully
        if 'WorldState' not in globals() or WorldState is None or 'simulate_forward' not in globals() or simulate_forward is None:
             print("Error: Simulation components not available. Skipping retrodiction.")
             accuracy_metrics = {"error": "Simulation engine components not loaded."}
        else:
            # Proceed with simulation only if components are available
            try: # Main try block for simulation
                # 1. WorldState Initialization - Basic initialization
                initial_state = WorldState()
                initial_state.turn = 0
                # We cannot reliably set .variables or .overlays without knowing WorldState's structure.
                # Assume the simulation engine handles seeding based on the first step or loader.
                # We will rely on the simulation *output* structure later.
                print(f"Initialized WorldState for retrodiction: Turn {initial_state.turn}. Initial variable seeding relies on simulation engine behavior.")


                # Indent the following block to be inside the main try:
                # 2. Instantiate Loader (Only if hist_data is a valid Series)
                loader = None
                if isinstance(hist_data, pd.Series) and not hist_data.empty:
                    loader = HistoricalDataLoader(hist_data) # Pass the original Series
                    print("HistoricalDataLoader instantiated.")
                else:
                     print("Error: Cannot instantiate HistoricalDataLoader because hist_data is not a valid pandas Series.")
                     # Set accuracy error early if loader cannot be created
                     accuracy_metrics = {"error": "Failed to load historical data for simulation loader."}
                     # Skip simulation if loader failed
                     simulation_results = [] # Ensure simulation_results is defined

                # 3. Call simulate_forward (Only if loader was created)
                num_simulation_turns = len(hist_values) - 1 # Simulate up to the last point
                # Ensure loader was created (implies hist_data was valid)
                # No need to check simulate_forward again, already checked above
                if loader:
                     print(f"Calling simulate_forward for {num_simulation_turns} turns...")
                     simulation_results = simulate_forward(
                         state=initial_state,
                         turns=num_simulation_turns,
                         retrodiction_mode=True,
                         retrodiction_loader=loader,
                         return_mode='full' # Need full state to extract variables
                     )
                     print(f"simulate_forward returned {len(simulation_results)} results.")

                     # 4. Extract Retrodictive Series
                     if simulation_results:
                         for result in simulation_results:
                             # Adjust path based on actual WorldState structure if needed
                             try:
                                 # The result for turn 't' contains the state *after* the simulation step for that turn
                                 # This state includes the prediction for the *next* turn's variable value.
                                 # Revert to dictionary access within try/except
                                 try:
                                     retro_value = result['full_state']['variables']['nvidia_stock']
                                     retrodictive_values.append(retro_value)
                                 except KeyError:
                                     print(f"Warning: Could not find 'nvidia_stock' via path ['full_state']['variables']['nvidia_stock'] in simulation result for a turn. Result: {result}")
                                     retrodictive_values.append(None) # Append None if extraction failed
                                 except Exception as extract_e: # Catch other potential errors during extraction (e.g., None values)
                                     print(f"Warning: Error extracting retro value from result: {extract_e}. Result: {result}")
                                     retrodictive_values.append(None)
                             except TypeError:
                                 print(f"Warning: Unexpected result structure. Result: {result}")
                                 retrodictive_values.append(None)

                         # Align timestamps: Retrodictive values correspond to historical values from index 1 onwards
                         # Ensure retrodictive_timestamps has the same length as retrodictive_values
                         if len(hist_timestamps) > 1:
                              retrodictive_timestamps = hist_timestamps[1:len(retrodictive_values) + 1]

                         print(f"Extracted {len(retrodictive_values)} retrodictive values.")

                         # 5. Calculate Accuracy
                         # Compare historical values (from index 1) with retrodictive values
                         actuals_for_comparison = hist_values[1:len(retrodictive_values) + 1] # Ground truth corresponding to predictions
                         predictions_for_comparison = [v for v in retrodictive_values if v is not None] # Filter out potential Nones if errors occurred

                         # Adjust actuals length if predictions are shorter due to Nones
                         if len(actuals_for_comparison) > len(predictions_for_comparison):
                             actuals_for_comparison = actuals_for_comparison[:len(predictions_for_comparison)]


                         # Ensure lengths match after filtering Nones before calculating metrics
                         if len(actuals_for_comparison) == len(predictions_for_comparison) and len(predictions_for_comparison) > 0:
                             # Corrected indentation for try/except/elif/else block
                             try:
                                 # Convert to numpy arrays for robust calculation
                                 actuals_np = np.array(actuals_for_comparison)
                                 predictions_np = np.array(predictions_for_comparison)

                                 mae = mean_absolute_error(actuals_np, predictions_np)
                                 rmse = mean_squared_error(actuals_np, predictions_np, squared=False) # Calculate RMSE
                                 # Explicitly cast to float before rounding
                                 accuracy_metrics = {'mae': round(float(mae), 4), 'rmse': round(float(rmse), 4)}
                                 print(f"Calculated Accuracy Metrics: MAE={accuracy_metrics['mae']}, RMSE={accuracy_metrics['rmse']}")
                             except Exception as metric_e: # Correct indentation for except
                                 print(f"Error calculating accuracy metrics: {metric_e}")
                                 accuracy_metrics = {"error": f"Could not calculate metrics: {metric_e}"}
                         elif len(predictions_for_comparison) == 0: # Correct indentation for elif
                             print("Warning: No valid predictions to calculate accuracy.")
                             accuracy_metrics = {"error": "No valid predictions available."}
                         else: # Correct indentation for else
                             # This case should ideally not be reached after length adjustment, but kept for safety
                             print(f"Warning: Length mismatch between actuals ({len(actuals_for_comparison)}) and valid predictions ({len(predictions_for_comparison)}). Cannot calculate accuracy.")
                             accuracy_metrics = {"error": "Length mismatch between actuals and predictions."}

                     else:
                          print("simulate_forward returned no results.")
                          accuracy_metrics = {"error": "Simulation produced no results."}
                # Handle case where loader wasn't created
                elif not loader:
                     # Error message already set when loader creation failed
                     pass # accuracy_metrics should already contain the error
                 # Removed the 'else' for simulate_forward check as it's done earlier

            except Exception as sim_e: # Catch simulation-specific errors
                print(f"Error during retrodiction simulation or processing: {sim_e}")
                import traceback
                traceback.print_exc()
                accuracy_metrics = {"error": f"Simulation failed: {sim_e}"}

    elif not hist_values:
         print("No historical data fetched, skipping retrodiction.")
         accuracy_metrics = {"error": "No historical data available."}
    else: # Only 1 data point
         print("Only one historical data point, skipping retrodiction (need at least two).")
         accuracy_metrics = {"error": "Insufficient historical data for retrodiction (need >= 2 points)."}


    # --- Prepare Response ---
    response_data = {
        "variable_name": variable_name,
        "historical_timestamps": hist_timestamps,
        "historical_values": hist_values,
        "retrodictive_timestamps": retrodictive_timestamps, # Use aligned timestamps
        "retrodictive_values": retrodictive_values,
        "accuracy_metrics": accuracy_metrics
    }

    return jsonify(response_data)
# --- Main Execution ---

if __name__ == '__main__':
    # Using waitress instead of app.run() due to WSGI server instability on this system
    print("Starting server with Waitress on http://127.0.0.1:5002...")
    serve(app, host='0.0.0.0', port=5002)