from flask import Blueprint, jsonify
from ..simulated_data import get_system_status, get_active_processes, get_recursive_learning_status

data_api_bp = Blueprint('data_api', __name__)

@data_api_bp.route('/api/system_status')
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

@data_api_bp.route('/api/data/overview')
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