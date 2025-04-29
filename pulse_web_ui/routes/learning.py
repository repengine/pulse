from flask import Blueprint, jsonify, request
from learning.recursion_audit import generate_recursion_report # Import the audit function

learning_bp = Blueprint('learning', __name__)

@learning_bp.route('/api/learning/audit', methods=['POST'])
def api_learning_audit():
    """
    API endpoint to generate an AI training review/audit report.
    Accepts 'previous_batch_id' and 'current_batch_id' in the request body.
    Returns the audit report as a JSON object.
    """
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 415

    data = request.get_json()
    previous_batch_id = data.get('previous_batch_id')
    current_batch_id = data.get('current_batch_id')

    if not previous_batch_id or not current_batch_id:
         return jsonify({"error": "'previous_batch_id' and 'current_batch_id' are required."}), 400

    # Assuming generate_recursion_report can handle batch IDs or that logic to load
    # forecasts from IDs will be added within or before calling it.
    try:
        # Note: The actual implementation of generate_recursion_report might need
        # to be updated to handle batch IDs instead of forecast lists, or
        # logic to load forecasts based on IDs should be added here.
        audit_report = generate_recursion_report(previous_batch_id, current_batch_id)
        return jsonify(audit_report)
    except Exception as e:
        print(f"Error generating audit report for batches {previous_batch_id}, {current_batch_id}: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Failed to generate audit report: {e}"}), 500