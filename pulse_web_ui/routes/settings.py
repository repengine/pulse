from flask import Blueprint, render_template, request, redirect, url_for, flash
from ..simulated_data import get_recursive_learning_status, set_recursive_learning_status

settings_bp = Blueprint('settings', __name__)

@settings_bp.route('/settings', methods=['GET', 'POST'])
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