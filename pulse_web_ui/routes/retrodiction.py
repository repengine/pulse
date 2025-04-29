from flask import Blueprint, render_template, jsonify, request
import plotly.graph_objects as go
import plotly.io as pio
import pandas as pd
import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error
import datetime
import uuid # Import uuid for generating unique run IDs
import threading # Import threading for running simulations in the background
import time # Import time for simulating progress
import random # Import random for dummy data

from ..simulated_data import get_retrodiction_runs, get_retrodiction_data, HistoricalDataLoader, fetch_historical_yfinance_close, WorldState, simulate_forward # Import necessary components

retrodiction_bp = Blueprint('retrodiction', __name__)

# --- Global state for tracking retrodiction runs ---
# In a real application, this would be a database or more persistent storage
RETRODICTION_RUNS = {}
RETRODICTION_STATUS = {}

# --- Helper function to run simulation in background ---
def run_simulation_in_background(run_id, start_date, days, variables_of_interest):
    """Simulates running a retrodiction simulation."""
    RETRODICTION_STATUS[run_id] = {"status": "Running", "progress": 0, "message": "Starting simulation..."}
    print(f"Starting background simulation for run_id: {run_id}")

    try:
        # Simulate fetching historical data
        end_date_dt = start_date + datetime.timedelta(days=days)
        hist_data = fetch_historical_yfinance_close(ticker="NVDA", start_date=start_date, end_date=end_date_dt) # Using NVDA as a placeholder

        if hist_data is None or hist_data.empty:
            RETRODICTION_STATUS[run_id] = {"status": "Error", "progress": 0, "message": "Failed to fetch historical data."}
            print(f"Simulation failed for run_id {run_id}: Failed to fetch historical data.")
            return

        loader = HistoricalDataLoader(hist_data)
        initial_state = WorldState() # Assuming WorldState can be initialized without parameters for a new run
        initial_state.turn = 0

        num_simulation_turns = len(hist_data) - 1
        simulation_results = []

        if 'simulate_forward' in globals() and simulate_forward is not None:
            # Simulate progress updates
            for i in range(num_simulation_turns):
                # In a real scenario, simulate_forward would ideally yield progress
                # For now, we simulate progress based on turns
                time.sleep(0.1) # Simulate work
                RETRODICTION_STATUS[run_id]["progress"] = int(((i + 1) / num_simulation_turns) * 100)
                RETRODICTION_STATUS[run_id]["message"] = f"Simulating turn {i+1}/{num_simulation_turns}..."

            # Call the actual simulate_forward once (or in chunks if it supports it)
            # This is a simplification; a real implementation might need to handle large simulations differently
            simulation_results = simulate_forward(
                state=initial_state,
                turns=num_simulation_turns,
                retrodiction_mode=True,
                retrodiction_loader=loader,
                return_mode='full'
            )
            print(f"simulate_forward completed for run_id {run_id} with {len(simulation_results)} results.")

        else:
            print("Simulation engine components not available. Skipping actual simulation.")
            # Simulate some dummy results if simulation engine is not available
            simulation_results = [{"full_state": {"variables": {"nvidia_stock": random.uniform(100, 300)}}} for _ in range(num_simulation_turns)]
            RETRODICTION_STATUS[run_id]["progress"] = 100
            RETRODICTION_STATUS[run_id]["message"] = "Simulation engine not available, generated dummy results."


        # Process results and store
        retrodictive_values = []
        retrodictive_timestamps = []
        hist_values = hist_data.values.tolist()

        # Corrected strftime usage
        if isinstance(hist_data.index, pd.DatetimeIndex):
             hist_timestamps = hist_data.index.strftime('%Y-%m-%dT%H:%M:%S').tolist()
        else:
             hist_timestamps = hist_data.index.astype(str).tolist()


        for result in simulation_results:
            try:
                # Extract retrodictive value for a placeholder variable (e.g., nvidia_stock)
                # In a real scenario, this would depend on variables_of_interest
                retro_value = result['full_state']['variables'].get('nvidia_stock') # Use .get for safety
                retrodictive_values.append(retro_value)
            except (KeyError, TypeError):
                retrodictive_values.append(None)

        if len(hist_timestamps) > 1:
             retrodictive_timestamps = hist_timestamps[1:len(retrodictive_values) + 1]

        # Calculate accuracy metrics (simplified)
        accuracy_metrics = {}
        actuals_for_comparison = hist_values[1:len(retrodictive_values) + 1]
        predictions_for_comparison = [v for v in retrodictive_values if v is not None]

        if len(actuals_for_comparison) == len(predictions_for_comparison) and len(predictions_for_comparison) > 0:
            try:
                actuals_np = np.array(actuals_for_comparison)
                predictions_np = np.array(predictions_for_comparison)
                mae = mean_absolute_error(actuals_np, predictions_np)
                rmse = mean_squared_error(actuals_np, predictions_np, squared=False)
                accuracy_metrics = {'mae': round(float(mae), 4), 'rmse': round(float(rmse), 4)}
            except Exception as metric_e:
                print(f"Error calculating accuracy metrics for run {run_id}: {metric_e}")
                accuracy_metrics = {"error": f"Could not calculate metrics: {metric_e}"}
        elif len(predictions_for_comparison) == 0:
             accuracy_metrics = {"error": "No valid predictions available."}
        else:
             accuracy_metrics = {"error": "Length mismatch between actuals and predictions."}


        RETRODICTION_RUNS[run_id] = {
            "run_id": run_id,
            "start_date": start_date.strftime('%Y-%m-%d'),
            "days": days,
            "variables_of_interest": variables_of_interest,
            "historical_timestamps": hist_timestamps,
            "historical_values": hist_values,
            "retrodictive_timestamps": retrodictive_timestamps,
            "retrodictive_values": retrodictive_values,
            "accuracy_metrics": accuracy_metrics,
            "status": "Completed",
            "completion_time": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        RETRODICTION_STATUS[run_id] = {"status": "Completed", "progress": 100, "message": "Simulation completed."}
        print(f"Simulation completed successfully for run_id: {run_id}")

    except Exception as e:
        print(f"Error during background simulation for run_id {run_id}: {e}")
        import traceback
        traceback.print_exc()
        RETRODICTION_STATUS[run_id] = {"status": "Error", "progress": RETRODICTION_STATUS[run_id].get("progress", 0), "message": f"Simulation failed: {e}"}

retrodiction_bp = Blueprint('retrodiction', __name__)

@retrodiction_bp.route('/retrodiction')
def retrodiction():
    """Renders the retrodiction view page."""
    runs = get_retrodiction_runs()
    return render_template('retrodiction.html', runs=runs)

@retrodiction_bp.route('/api/retrodiction/run', methods=['POST'])
def api_retrodiction_run():
    """
    API endpoint to start a retrodiction simulation.
    Accepts start_date, days, and optionally variables_of_interest.
    Returns a unique run_id.
    """
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 415

    data = request.get_json()
    start_date_str = data.get('start_date')
    days = data.get('days')
    variables_of_interest = data.get('variables_of_interest') # Optional

    if not start_date_str or days is None:
        return jsonify({"error": "Missing required parameters: start_date and days"}), 400

    try:
        start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d')
        days = int(days)
        if days <= 0:
             return jsonify({"error": "Days must be a positive integer."}), 400
    except ValueError:
        return jsonify({"error": "Invalid date format (use YYYY-MM-DD) or days is not an integer."}), 400

    run_id = str(uuid.uuid4())
    print(f"Starting retrodiction run with ID: {run_id}")

    # Start the simulation in a background thread
    thread = threading.Thread(target=run_simulation_in_background, args=(run_id, start_date, days, variables_of_interest))
    thread.start()

    return jsonify({"run_id": run_id, "message": "Retrodiction simulation started."}), 202 # 202 Accepted

@retrodiction_bp.route('/api/retrodiction/status/<run_id>', methods=['GET'])
def api_retrodiction_status(run_id):
    """
    API endpoint to get the status of a retrodiction simulation.
    """
    status = RETRODICTION_STATUS.get(run_id)
    if status:
        return jsonify(status)
    else:
        return jsonify({"error": "Run ID not found"}), 404

@retrodiction_bp.route('/api/retrodiction_data/<run_id>', methods=['GET'])
def api_retrodiction_data(run_id):
    """API endpoint to get data for a specific retrodiction run."""
    # This existing endpoint will now fetch from the global RETRODICTION_RUNS dictionary
    data = RETRODICTION_RUNS.get(run_id) # Fetch from global state
    if not data:
        # Fallback to simulated_data if not found in global state (for existing simulated runs)
        data = get_retrodiction_data(run_id)
        if not data:
             return jsonify({"error": "Run not found"}), 404

    # The rest of the logic for generating the chart remains the same
    fig = None
    chart_info = data.get("chart_data") # Note: New runs won't have "chart_data" in this format
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
             fig.update_layout(title=f"Chart for {data.get('name', run_id)}") # Use run_id if name is missing

    # For new runs, create a chart from historical and retrodictive values
    if 'historical_timestamps' in data and 'retrodictive_timestamps' in data:
         fig = go.Figure()
         if data.get('historical_timestamps') and data.get('historical_values'):
              fig.add_trace(go.Scatter(x=data['historical_timestamps'], y=data['historical_values'], mode='lines+markers', name='Historical'))
         if data.get('retrodictive_timestamps') and data.get('retrodictive_values'):
              fig.add_trace(go.Scatter(x=data['retrodictive_timestamps'], y=data['retrodictive_values'], mode='lines+markers', name='Retrodictive'))

         fig.update_layout(
             title=f"Retrodiction Run {run_id}",
             xaxis_title="Timestamp",
             yaxis_title="Value",
             hovermode="x unified"
         )


    chart_json = pio.to_json(fig) if fig else None
    data['chart_json'] = chart_json
    # data.pop("chart_data", None) # Remove old chart_data if it exists

    return jsonify(data)