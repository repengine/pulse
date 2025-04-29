from flask import Blueprint, render_template, jsonify, request
from ..simulated_data import get_autopilot_status, get_autopilot_run_history, start_autopilot_run, stop_autopilot_run

autopilot_bp = Blueprint('autopilot', __name__)

@autopilot_bp.route('/autopilot')
def autopilot():
    """Renders the autopilot control view page."""
    status = get_autopilot_status()
    history = get_autopilot_run_history()
    return render_template('autopilot.html', status=status, history=history)

@autopilot_bp.route('/api/autopilot/start', methods=['POST'])
def api_autopilot_start():
    """API endpoint to start an autopilot run."""
    if not request.is_json: return jsonify({"error": "Request must be JSON"}), 415
    data = request.get_json()
    goal = data.get('goal')
    constraints = data.get('constraints', 'None')
    if not goal: return jsonify({"error": "Goal is required"}), 400

    success, message = start_autopilot_run(goal, constraints)
    status_code = 200 if success else (409 if "already running" in message else 400)
    return jsonify({"message": message, "status": get_autopilot_status()}), status_code

@autopilot_bp.route('/api/autopilot/stop', methods=['POST'])
def api_autopilot_stop():
    """API endpoint to stop the current autopilot run."""
    success, message = stop_autopilot_run()
    status_code = 200 if success else 400
    return jsonify({"message": message, "status": get_autopilot_status()}), status_code

@autopilot_bp.route('/api/autopilot/status', methods=['GET'])
def api_autopilot_status():
    """API endpoint to get the current autopilot status."""
    status = get_autopilot_status()
    return jsonify(status)

@autopilot_bp.route('/api/autopilot/history', methods=['GET'])
def api_autopilot_history():
    """API endpoint to get the autopilot run history."""
    history = get_autopilot_run_history()
    return jsonify(history)