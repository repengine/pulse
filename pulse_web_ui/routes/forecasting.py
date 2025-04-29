from flask import Blueprint, render_template, jsonify
import plotly.graph_objects as go
import plotly.io as pio
from ..simulated_data import get_forecast_sets, get_forecast_data
from ..utils import get_latest_forecast_from_log, get_latest_forecast_all_variables

forecasting_bp = Blueprint('forecasting', __name__)

@forecasting_bp.route('/forecasting')
def forecasting():
    """Renders the forecasting view page."""
    forecast_sets = get_forecast_sets()
    return render_template('forecasting.html', forecast_sets=forecast_sets)

@forecasting_bp.route('/api/forecast_data/<set_id>')
def api_forecast_data(set_id):
    """API endpoint to get data for a specific forecast set."""
    data = get_forecast_data(set_id)
    if not data:
        return jsonify({"error": "Forecast set not found"}), 404

    fig = None
    chart_info = data.get("chart_data")
    if chart_info:
        fig = go.Figure([
            go.Scatter(name='Forecast', x=chart_info['time_points'], y=chart_info['values'], mode='lines', line=dict(color='rgb(31, 119, 180)')),
            go.Scatter(name='Upper Bound', x=chart_info['time_points'], y=chart_info['upper_bound'], mode='lines', marker=dict(color="#444"), line=dict(width=0), showlegend=False),
            go.Scatter(name='Lower Bound', x=chart_info['time_points'], y=chart_info['lower_bound'], marker=dict(color="#444"), line=dict(width=0), mode='lines', fillcolor='rgba(68, 68, 68, 0.3)', fill='tonexty', showlegend=False, hoverinfo='skip'),
            go.Scatter(name='Actuals', x=chart_info['time_points'], y=chart_info.get('actual_values', []), mode='markers', marker=dict(color='rgb(255, 127, 14)', size=8), line=dict(dash='dot'))
        ])
        fig.update_layout(
            title=f'Forecast vs Actuals for Set {set_id}',
            yaxis_title='Value',
            hovermode="x unified",
            legend_title_text='Legend'
        )

    chart_json = pio.to_json(fig) if fig else None
    data['chart_json'] = chart_json
    data.pop("chart_data", None)

    return jsonify(data)

@forecasting_bp.route('/api/forecast_data/variable/<variable_name>')
def api_forecast_data_variable(variable_name):
    """
    API endpoint to get the latest forecast data for a specific variable
    by parsing the 'examples' list from the last line of the compressed log file.
    """
    print(f"API request received for variable: {variable_name}")
    forecast_data, error_msg = get_latest_forecast_from_log(variable_name)

    if error_msg:
        status_code = 404 if "not found" in error_msg.lower() or "no forecast data found" in error_msg.lower() else 500
        print(f"API Error for {variable_name}: {error_msg} (Status: {status_code})")
        return jsonify({"error": error_msg}), status_code

    if not forecast_data:
        print(f"API Error for {variable_name}: Unknown error retrieving data.")
        return jsonify({"error": "Failed to retrieve forecast data."}), 500

    fig = None
    try:
        fig = go.Figure()

        fig.add_trace(go.Scatter(
            name='Forecast',
            x=forecast_data['timestamps'],
            y=forecast_data['values'],
            mode='lines+markers',
            line=dict(color='rgb(31, 119, 180)')
        ))

        fig.update_layout(
            title=f'Latest Forecast Exposure for {variable_name}',
            yaxis_title='Forecasted Exposure Value',
            xaxis_title='Timestamp',
            hovermode="x unified",
            legend_title_text='Data Series'
        )

        chart_json = pio.to_json(fig)
        print(f"Successfully generated Plotly JSON for {variable_name} from last log entry.")
        return jsonify({"variable_name": variable_name, "chart_json": chart_json})

    except Exception as e:
        print(f"Error generating Plotly JSON for {variable_name}: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Failed to generate chart: {e}"}), 500

@forecasting_bp.route('/api/forecasts/latest/all', methods=['GET'])
def api_forecasts_latest_all():
    """
    API endpoint to get the latest forecast data for all variables
    by parsing the 'examples' list from the last line of the compressed log file.
    Returns a JSON object mapping variable names to their forecast data.
    """
    print("API request received for latest forecasts for all variables.")
    all_forecast_data, error_msg = get_latest_forecast_all_variables()

    if error_msg:
        status_code = 404 if "not found" in error_msg.lower() or "empty" in error_msg.lower() else 500
        print(f"API Error for all variables: {error_msg} (Status: {status_code})")
        return jsonify({"error": error_msg}), status_code

    if not all_forecast_data:
        print("API Error for all variables: Unknown error retrieving data.")
        return jsonify({"error": "Failed to retrieve forecast data for all variables."}), 500

    print(f"Successfully retrieved forecast data for {len(all_forecast_data)} variables.")
    return jsonify(all_forecast_data)