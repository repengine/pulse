from flask import Blueprint, render_template, jsonify
import plotly.graph_objects as go
import plotly.io as pio
from ..simulated_data import get_all_variable_names, get_variable_data

variables_bp = Blueprint('variables', __name__)

@variables_bp.route('/variables')
def variable_explorer():
    """Renders the variable explorer page."""
    return render_template('variable_explorer.html')

@variables_bp.route('/api/variables/list')
def api_variables_list():
    """API endpoint to get the list of available variable names."""
    variable_names = get_all_variable_names()
    return jsonify(variable_names)

@variables_bp.route('/api/variables/data/<variable_name>')
def api_variable_data(variable_name):
    """API endpoint to get historical data and chart for a specific variable."""
    data = get_variable_data(variable_name)
    if not data:
        return jsonify({"error": "Variable not found"}), 404

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

    chart_json = pio.to_json(fig) if fig else None

    response_data = {
        "name": variable_name,
        "chart_json": chart_json
    }

    return jsonify(response_data)