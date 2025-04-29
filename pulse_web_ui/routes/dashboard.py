from flask import Blueprint, render_template
from ..simulated_data import get_system_status, get_active_processes, get_recent_activity, get_recursive_learning_status

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
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