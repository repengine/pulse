#!/usr/bin/env python
"""
Pulse API Server
This provides the backend API for the Pulse Desktop UI
Runs on port 5002 by default
"""

from flask import Flask, request, jsonify
import os
import datetime
import threading
import time
import random
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("pulse-api-server")

# Try to import Pulse modules, but handle gracefully if not available
try:
    # from analytics.forecast_pipeline_runner import run_forecast_pipeline # F401
    # from analytics.recursion_audit import generate_recursion_report # F401
    # from dev_tools.pulse_ui_plot import load_variable_trace, plot_variables # F401
    # import core.pulse_config # F401
    # from operator_interface.learning_log_viewer import ( # F401
    #     load_learning_events, # F401
    #     summarize_learning_events, # F401
    # ) # F401
    # from analytics.variable_cluster_engine import summarize_clusters # F401

    has_pulse_modules = True
except ImportError as e:
    logger.warning(f"Some Pulse modules could not be imported: {e}")
    logger.warning("Running in compatibility mode with simulated data")
    has_pulse_modules = False

app = Flask(__name__)

# Global state
autopilot_status = "stopped"
autopilot_runs = []
retrodiction_runs = {}
forecast_cache = {}

# Default variables for simulating forecasts
SIMULATED_VARIABLES = [
    "inflation",
    "unemployment",
    "gdp_growth",
    "interest_rate",
    "housing_starts",
    "consumer_confidence",
    "industrial_production",
    "retail_sales",
    "commodity_prices",
    "market_volatility",
    "geopolitical_tension",
    "innovation_rate",
    "hope",
    "rage",
    "social_cohesion",
    "trust_in_institutions",
]


def generate_simulated_forecasts():
    """Generates simulated forecasts for testing."""
    forecasts = {}
    for var in SIMULATED_VARIABLES:
        # Generate a value between -10 and 10, with one decimal place
        forecasts[var] = round(random.uniform(-10, 10), 1)
    return forecasts


# Simulate some initial data
if not has_pulse_modules:
    forecast_cache = generate_simulated_forecasts()

    # Create some simulated autopilot history
    for i in range(3):
        start_time = datetime.datetime.now() - datetime.timedelta(days=i + 1)
        end_time = start_time + datetime.timedelta(hours=random.uniform(1, 8))
        autopilot_runs.append(
            {
                "run_id": f"sim-run-{i}",
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "status": random.choice(["completed", "failed", "stopped"]),
            }
        )

# --- API Endpoints ---


@app.route("/api/status", methods=["GET"])
def status():
    """API server status endpoint."""
    return jsonify(
        {
            "status": "online",
            "timestamp": datetime.datetime.now().isoformat(),
            "api_version": "1.0.0",
            "pulse_modules_available": has_pulse_modules,
        }
    )


@app.route("/api/forecasts/status", methods=["GET"])
def forecast_engine_status():
    """Forecast engine status endpoint."""
    return jsonify(
        {"status": "ready", "last_update": datetime.datetime.now().isoformat()}
    )


@app.route("/api/forecasts/latest/all", methods=["GET"])
def get_latest_forecasts():
    """Get the latest forecasts for all variables."""
    global forecast_cache

    # Always generate new forecasts when requested
    forecast_cache = generate_simulated_forecasts()

    # In a real implementation, this would fetch from the forecast engine
    if has_pulse_modules:
        try:
            # This is a placeholder for actual forecast retrieval logic
            # Implement the actual logic based on your forecast engine
            pass
        except Exception as e:
            logger.error(f"Error fetching forecasts: {e}")
            # We've already generated new forecast data above

    return jsonify(forecast_cache)


@app.route("/api/autopilot/status", methods=["GET"])
def get_autopilot_status():
    """Get the current status of the autopilot."""
    global autopilot_status
    return jsonify(
        {"status": autopilot_status, "updated_at": datetime.datetime.now().isoformat()}
    )


@app.route("/api/autopilot/start", methods=["POST"])
def start_autopilot():
    """Start the autopilot."""
    global autopilot_status

    if autopilot_status == "running":
        return jsonify({"status": "error", "error": "Autopilot is already running"})

    # In a real implementation, this would start the autopilot process
    autopilot_status = "running"

    # Add a new run to the history
    run_id = f"run-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}"
    autopilot_runs.append(
        {
            "run_id": run_id,
            "start_time": datetime.datetime.now().isoformat(),
            "end_time": None,
            "status": "running",
        }
    )

    return jsonify({"status": "success", "run_id": run_id})


@app.route("/api/autopilot/stop", methods=["POST"])
def stop_autopilot():
    """Stop the autopilot."""
    global autopilot_status

    if autopilot_status == "stopped":
        return jsonify({"status": "error", "error": "Autopilot is not running"})

    # In a real implementation, this would stop the autopilot process
    autopilot_status = "stopped"

    # Update the current run in the history
    for run in autopilot_runs:
        if run["status"] == "running":
            run["status"] = "stopped"
            run["end_time"] = datetime.datetime.now().isoformat()

    return jsonify({"status": "success"})


@app.route("/api/autopilot/history", methods=["GET"])
def get_autopilot_history():
    """Get the history of autopilot runs."""
    return jsonify(autopilot_runs)


@app.route("/api/retrodiction/run", methods=["POST"])
def run_retrodiction():
    """Run a retrodiction simulation."""
    params = request.json

    # Validate parameters
    if not params or not params.get("start_date"):
        return jsonify(
            {"status": "error", "error": "start_date is required in JSON body"}
        )

    run_id = f"retro-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}"

    # Store the run
    retrodiction_runs[run_id] = {
        "status": "running",
        "start_time": datetime.datetime.now().isoformat(),
        "end_time": None,
        "params": params,
        "progress": "0%",
    }

    # Start a background thread to simulate the retrodiction run
    threading.Thread(target=simulate_retrodiction_run, args=(run_id,)).start()

    return jsonify({"status": "started", "run_id": run_id})


@app.route("/api/retrodiction/status/<run_id>", methods=["GET"])
def get_retrodiction_status(run_id):
    """Get the status of a retrodiction run."""
    if run_id not in retrodiction_runs:
        return jsonify({"status": "error", "error": f"Run ID {run_id} not found"})

    run_data = retrodiction_runs[run_id]

    # If the run is completed, include results
    if run_data["status"] == "completed":
        return jsonify(
            {
                "status": "completed",
                "start_time": run_data["start_time"],
                "end_time": run_data["end_time"],
                "results": run_data.get("results", {}),
            }
        )
    elif run_data["status"] == "failed":
        return jsonify(
            {
                "status": "failed",
                "error": run_data.get("error", "Unknown error"),
                "start_time": run_data["start_time"],
                "end_time": run_data["end_time"],
            }
        )
    else:
        return jsonify(
            {
                "status": "running",
                "progress": run_data["progress"],
                "start_time": run_data["start_time"],
            }
        )


@app.route("/api/learning/audit", methods=["POST"])
def run_learning_audit():
    """Run a learning audit."""
    params = request.json

    if (
        not params
        or not params.get("previous_batch_id")
        or not params.get("current_batch_id")
    ):
        return jsonify(
            {
                "status": "error",
                "error": "Both previous_batch_id and current_batch_id are required in JSON body",
            })

    # Simulate an audit report
    report = {
        "confidence_delta": round(random.uniform(-0.2, 0.2), 2),
        "retrodiction_error_delta": round(random.uniform(-0.3, 0.1), 2),
        "trust_distribution_current": {
            "high": random.randint(30, 70),
            "medium": random.randint(20, 40),
            "low": random.randint(5, 20),
        },
        "arc_shift_summary": {
            "improved": random.randint(3, 15),
            "degraded": random.randint(1, 8),
            "unchanged": random.randint(20, 40),
        },
    }

    return jsonify({"status": "success", "report": report})


def simulate_retrodiction_run(run_id):
    """Simulates a retrodiction run in the background."""
    run_data = retrodiction_runs[run_id]

    try:
        # Simulate progress
        for progress in ["10%", "30%", "50%", "70%", "90%"]:
            time.sleep(random.uniform(0.5, 1.5))  # Simulate processing time
            run_data["progress"] = progress

        # Generate simulated results
        params = run_data["params"]
        variables = params.get(
            "variables_of_interest",
            ["inflation", "unemployment", "gdp_growth", "interest_rate"],
        )

        results = {
            "retrodiction_summary": {
                "start_date": params.get("start_date"),
                "days": params.get("days", 30),
                "accuracy": round(random.uniform(0.6, 0.95), 2),
            },
            "variable_results": {},
        }

        for var in variables:
            # Generate a time series of values
            values = []
            base_value = random.uniform(-5, 5)
            for i in range(params.get("days", 30)):
                # Add some randomness but keep a trend
                value = (
                    base_value
                    + (i * random.uniform(-0.1, 0.1))
                    + random.uniform(-0.5, 0.5)
                )
                values.append(round(value, 2))

            results["variable_results"][var] = {
                "values": values,
                "mean": round(sum(values) / len(values), 2),
                "min": round(min(values), 2),
                "max": round(max(values), 2),
                "error_rate": round(random.uniform(0.01, 0.15), 3),
            }

        # Update run data
        run_data["status"] = "completed"
        run_data["end_time"] = datetime.datetime.now().isoformat()
        run_data["results"] = results

    except Exception as e:
        # Handle any errors
        run_data["status"] = "failed"
        run_data["error"] = str(e)
        run_data["end_time"] = datetime.datetime.now().isoformat()
        logger.error(f"Error in retrodiction run {run_id}: {e}")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5002))
    logger.info(f"Starting Pulse API Server on port {port}")
    app.run(host="0.0.0.0", port=port)
