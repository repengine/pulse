from flask import Blueprint, render_template, jsonify, request
import plotly.graph_objects as go
import plotly.io as pio
import pandas as pd
import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error
import datetime
from ..simulated_data import get_retrodiction_runs, get_retrodiction_data, HistoricalDataLoader, fetch_historical_yfinance_close, WorldState, simulate_forward # Import necessary components

retrodiction_bp = Blueprint('retrodiction', __name__)

@retrodiction_bp.route('/retrodiction')
def retrodiction():
    """Renders the retrodiction view page."""
    runs = get_retrodiction_runs()
    return render_template('retrodiction.html', runs=runs)

@retrodiction_bp.route('/api/retrodiction_data/<run_id>')
def api_retrodiction_data(run_id):
    """API endpoint to get data for a specific retrodiction run."""
    data = get_retrodiction_data(run_id)
    if not data:
        return jsonify({"error": "Run not found"}), 404

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

    chart_json = pio.to_json(fig) if fig else None
    data['chart_json'] = chart_json
    data.pop("chart_data", None)

    return jsonify(data)

@retrodiction_bp.route('/api/retrodiction/compare/nvidia_stock')
def api_retrodiction_compare_nvidia_stock():
    """
    API endpoint to fetch historical NVDA stock data for comparison.
    Includes placeholders for retrodictive data.
    """
    variable_name = "nvidia_stock"
    ticker = "NVDA"

    try:
        end_date_dt = datetime.datetime.now()
        start_date_dt = end_date_dt - datetime.timedelta(days=365)

        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')

        if start_date_str:
            start_date_dt = datetime.datetime.strptime(start_date_str, '%Y-%m-%d')
        if end_date_str:
            end_date_dt = datetime.datetime.strptime(end_date_str, '%Y-%m-%d')

        if start_date_dt > end_date_dt:
            return jsonify({"error": "Start date cannot be after end date."}), 400

    except ValueError:
        return jsonify({"error": "Invalid date format. Please use YYYY-MM-DD."}), 400
    except Exception as e:
         print(f"Error processing dates: {e}")
         return jsonify({"error": f"Internal server error processing dates: {e}"}), 500

    hist_timestamps = []
    hist_values = []
    hist_data: pd.Series | None = None
    try:
        print(f"Fetching historical data for {ticker} from {start_date_dt.strftime('%Y-%m-%d')} to {end_date_dt.strftime('%Y-%m-%d')}")
        hist_data = fetch_historical_yfinance_close(ticker=ticker, start_date=start_date_dt, end_date=end_date_dt)

        if hist_data is not None and not hist_data.empty:
            if isinstance(hist_data.index, pd.DatetimeIndex):
                 hist_timestamps = hist_data.index.strftime('%Y-%m-%dT%H:%M:%S').tolist()
            else:
                 hist_timestamps = hist_data.index.astype(str).tolist()
            hist_values = hist_data.values.tolist()
            print(f"Successfully fetched {len(hist_values)} historical data points for {ticker}.")
        else:
            print(f"No historical data returned for {ticker} in the specified range.")

    except Exception as e:
        print(f"Error fetching historical data for {ticker}: {e}")
        pass

    retrodictive_values = []
    accuracy_metrics = {}
    retrodictive_timestamps = []

    if hist_values and len(hist_values) > 1:
        if 'WorldState' not in globals() or WorldState is None or 'simulate_forward' not in globals() or simulate_forward is None:
             print("Error: Simulation components not available. Skipping retrodiction.")
             accuracy_metrics = {"error": "Simulation engine components not loaded."}
        else:
            try:
                initial_state = WorldState()
                initial_state.turn = 0
                print(f"Initialized WorldState for retrodiction: Turn {initial_state.turn}. Initial variable seeding relies on simulation engine behavior.")

                loader = None
                if isinstance(hist_data, pd.Series) and not hist_data.empty:
                    loader = HistoricalDataLoader(hist_data)
                    print("HistoricalDataLoader instantiated.")
                else:
                     print("Error: Cannot instantiate HistoricalDataLoader because hist_data is not a valid pandas Series.")
                     accuracy_metrics = {"error": "Failed to load historical data for simulation loader."}
                     simulation_results = []

                num_simulation_turns = len(hist_values) - 1
                if loader:
                     print(f"Calling simulate_forward for {num_simulation_turns} turns...")
                     simulation_results = simulate_forward(
                         state=initial_state,
                         turns=num_simulation_turns,
                         retrodiction_mode=True,
                         retrodiction_loader=loader,
                         return_mode='full'
                     )
                     print(f"simulate_forward returned {len(simulation_results)} results.")

                     if simulation_results:
                         for result in simulation_results:
                             try:
                                 try:
                                     retro_value = result['full_state']['variables']['nvidia_stock']
                                     retrodictive_values.append(retro_value)
                                 except KeyError:
                                     print(f"Warning: Could not find 'nvidia_stock' via path ['full_state']['variables']['nvidia_stock'] in simulation result for a turn. Result: {result}")
                                     retrodictive_values.append(None)
                                 except Exception as extract_e:
                                     print(f"Warning: Error extracting retro value from result: {extract_e}. Result: {result}")
                                     retrodictive_values.append(None)
                             except TypeError:
                                 print(f"Warning: Unexpected result structure. Result: {result}")
                                 retrodictive_values.append(None)

                         if len(hist_timestamps) > 1:
                              retrodictive_timestamps = hist_timestamps[1:len(retrodictive_values) + 1]

                         print(f"Extracted {len(retrodictive_values)} retrodictive values.")

                         actuals_for_comparison = hist_values[1:len(retrodictive_values) + 1]
                         predictions_for_comparison = [v for v in retrodictive_values if v is not None]

                         if len(actuals_for_comparison) > len(predictions_for_comparison):
                             actuals_for_comparison = actuals_for_comparison[:len(predictions_for_comparison)]

                         if len(actuals_for_comparison) == len(predictions_for_comparison) and len(predictions_for_comparison) > 0:
                             try:
                                 actuals_np = np.array(actuals_for_comparison)
                                 predictions_np = np.array(predictions_for_comparison)

                                 mae = mean_absolute_error(actuals_np, predictions_np)
                                 rmse = mean_squared_error(actuals_np, predictions_np, squared=False)
                                 accuracy_metrics = {'mae': round(float(mae), 4), 'rmse': round(float(rmse), 4)}
                                 print(f"Calculated Accuracy Metrics: MAE={accuracy_metrics['mae']}, RMSE={accuracy_metrics['rmse']}")
                             except Exception as metric_e:
                                 print(f"Error calculating accuracy metrics: {metric_e}")
                                 accuracy_metrics = {"error": f"Could not calculate metrics: {metric_e}"}
                         elif len(predictions_for_comparison) == 0:
                             print("Warning: No valid predictions to calculate accuracy.")
                             accuracy_metrics = {"error": "No valid predictions available."}
                         else:
                             print(f"Warning: Length mismatch between actuals ({len(actuals_for_comparison)}) and valid predictions ({len(predictions_for_comparison)}). Cannot calculate accuracy.")
                             accuracy_metrics = {"error": "Length mismatch between actuals and predictions."}

                     else:
                          print("simulate_forward returned no results.")
                          accuracy_metrics = {"error": "Simulation produced no results."}
                elif not loader:
                     pass

            except Exception as sim_e:
                print(f"Error during retrodiction simulation or processing: {sim_e}")
                import traceback
                traceback.print_exc()
                accuracy_metrics = {"error": f"Simulation failed: {sim_e}"}

    elif not hist_values:
         print("No historical data fetched, skipping retrodiction.")
         accuracy_metrics = {"error": "No historical data available."}
    else:
         print("Only one historical data point, skipping retrodiction (need at least two).")
         accuracy_metrics = {"error": "Insufficient historical data for retrodiction (need >= 2 points)."}

    response_data = {
        "variable_name": variable_name,
        "historical_timestamps": hist_timestamps,
        "historical_values": hist_values,
        "retrodictive_timestamps": retrodictive_timestamps,
        "retrodictive_values": retrodictive_values,
        "accuracy_metrics": accuracy_metrics
    }

    return jsonify(response_data)