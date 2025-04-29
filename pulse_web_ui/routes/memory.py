from flask import Blueprint, render_template, jsonify
from ..simulated_data import get_memory_items, get_memory_item_details

memory_bp = Blueprint('memory', __name__)

@memory_bp.route('/memory_explorer')
def memory_explorer():
    """Renders the memory explorer view page."""
    items_by_category = get_memory_items()
    return render_template('memory_explorer.html', items_by_category=items_by_category)

@memory_bp.route('/api/memory_item/<item_id>')
def api_memory_item_details(item_id):
    """API endpoint to get details for a specific memory item."""
    details = get_memory_item_details(item_id)
    if details:
        return jsonify(details)
    else:
        return jsonify({"error": "Memory item not found"}), 404