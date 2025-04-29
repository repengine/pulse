import random
import datetime
import json
import pandas as pd
import numpy as np
import typing
import os

# Attempt simulation engine imports
try:
    from simulation_engine.simulator_core import simulate_forward, WorldState
except ImportError:
    print("WARNING: Could not import simulation_engine components (WorldState, simulate_forward). Retrodiction will be skipped.")
    if 'WorldState' not in globals(): WorldState = None
    if 'simulate_forward' not in globals(): simulate_forward = None

# Attempt to import the historical data fetching function
try:
    from iris.iris_plugins_variable_ingestion.historical_ingestion_plugin import fetch_historical_yfinance_close
except ImportError:
    print("WARNING: Could not import fetch_historical_yfinance_close from iris plugin. Using dummy function.")
    def fetch_historical_yfinance_close(ticker: str, start_date: datetime.datetime, end_date: datetime.datetime) -> pd.Series | None:
        print(f"DUMMY: Fetching {ticker} from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        try:
            start = pd.to_datetime(start_date)
            end = pd.to_datetime(end_date)
            if start > end:
                start, end = end, start
            dates = pd.date_range(start=start, end=end, freq='B')
            if dates.empty:
                return pd.Series(dtype=float)
            values = [100 + (i % 10) + random.uniform(-2, 2) for i in range(len(dates))]
            return pd.Series(values, index=dates, name='Close')
        except Exception as e:
             print(f"DUMMY ERROR: Failed to generate dummy data: {e}")
             return pd.Series(dtype=float)

# --- Simulated Global State ---
# Replace with a more robust state management solution later
SIMULATED_RECURSIVE_LEARNING_ENABLED = True # Initial state
SIMULATED_AUTOPILOT_STATUS = {"state": "Idle", "current_run": None} # Example state: Idle, Running, Stopped, Error
SIMULATED_AUTOPILOT_HISTORY = [
    {"id": "ap_run_001", "start_time": "2025-04-28 08:00:00", "end_time": "2025-04-28 09:00:00", "goal": "Optimize Alpha", "constraints": "Max CPU 80%", "status": "Completed"},
    {"id": "ap_run_002", "start_time": "2025-04-28 11:00:00", "end_time": "2025-04-28 11:15:00", "goal": "Explore Beta", "constraints": "None", "status": "Stopped"},
]
SIMULATED_VARIABLE_NAMES = ["Temperature_Sensor_A", "Pressure_Valve_X", "Market_Index_SPY", "User_Activity_Score", "System_Load_CPU"]

# --- Placeholder Backend Functions ---
# These simulate fetching data from the core Pulse system.
# Replace these with actual calls later.

def get_system_status():
    """Simulates fetching the overall system status."""
    return random.choice(["Operational", "Idle", "Warning"])

def get_active_processes():
    """Simulates fetching a list of currently running tasks."""
    processes = ["Forecasting Cycle #124", "Autopilot Run 'Optimize Alpha'", "Memory Consolidation"]
    current_ap_status = get_autopilot_status()
    if current_ap_status["state"] == "Running":
        run_info = current_ap_status["current_run"]
        processes.append(f"Autopilot Run '{run_info['goal']}' ({run_info['id']})")
    return random.sample(processes, k=random.randint(0, len(processes)))

def get_retrodiction_runs():
    """Simulates fetching a list of available retrodiction run IDs/names."""
    return [
        {"id": "retro_run_001", "timestamp": "2025-04-27 10:00:00", "name": "Initial Baseline"},
        {"id": "retro_run_002", "timestamp": "2025-04-28 09:30:00", "name": "Post-Parameter Tuning"},
        {"id": "retro_run_003", "timestamp": "2025-04-28 14:15:00", "name": "Latest Analysis"},
    ]

def get_retrodiction_data(run_id: str):
    """
    Simulates fetching detailed data for a specific retrodiction run
    and generating a Plotly figure.
    """
    print(f"Simulating data fetch for run_id: {run_id}")
    if run_id == "retro_run_001":
        base_data = {
            "run_id": run_id, "name": "Initial Baseline", "timestamp": "2025-04-27 10:00:00",
            "summary_metrics": {"accuracy": 0.85, "relevance": 0.75, "f1_score": 0.80},
            "insights": "Initial model shows good baseline accuracy but struggles with relevance on edge cases.",
            "chart_data": {"type": "bar", "labels": ["A", "B", "C"], "values": [10, 20, 15]},
            "detailed_data": [{"feature": "X1", "importance": 0.5}, {"feature": "X2", "importance": 0.3}, {"feature": "X3", "importance": 0.2}]
        }
    elif run_id == "retro_run_002":
         base_data = {
            "run_id": run_id, "name": "Post-Parameter Tuning", "timestamp": "2025-04-28 09:30:00",
            "summary_metrics": {"accuracy": 0.88, "relevance": 0.82, "f1_score": 0.85},
            "insights": "Parameter tuning improved both accuracy and relevance significantly. Model is more robust.",
            "chart_data": {"type": "line", "labels": ["T1", "T2", "T3"], "values": [5, 8, 6]},
            "detailed_data": [{"feature": "X1", "importance": 0.45}, {"feature": "X2", "importance": 0.35}, {"feature": "X3", "importance": 0.20}]
        }
    else: # Default for run_003 or others
        base_data = {
            "run_id": run_id, "name": "Latest Analysis", "timestamp": "2025-04-28 14:15:00",
            "summary_metrics": {"accuracy": 0.90, "relevance": 0.85, "f1_score": 0.87},
            "insights": "Latest model performs well across most metrics. Minor drift detected in feature X3.",
            "chart_data": {"type": "scatter", "labels": ["P1", "P2", "P3"], "values": [12, 9, 15]},
            "detailed_data": [{"feature": "X1", "importance": 0.48}, {"feature": "X2", "importance": 0.32}, {"feature": "X3", "importance": 0.20}]
        }
    return base_data

def get_forecast_sets():
    """Simulates fetching a list of available forecast sets."""
    return [
        {"id": "fc_set_A", "timestamp": "2025-04-28 10:00:00", "name": "Daily Market Trend"},
        {"id": "fc_set_B", "timestamp": "2025-04-28 11:30:00", "name": "Weekly Sentiment Analysis"},
        {"id": "fc_set_C", "timestamp": "2025-04-28 15:00:00", "name": "Hourly System Load"},
    ]

def get_forecast_data(set_id: str):
    """
    Simulates fetching detailed data for a specific forecast set.
    Figure generation moved to API route.
    """
    print(f"Simulating data fetch for forecast set_id: {set_id}")
    base_time = datetime.datetime.now()
    time_points = [(base_time + datetime.timedelta(hours=i)).strftime("%Y-%m-%d %H:%M") for i in range(10)]
    base_value = random.uniform(50, 100)
    values = [base_value + random.uniform(-5, 5) + i*0.5 for i in range(10)]
    upper_bound = [v + random.uniform(2, 5) for v in values]
    lower_bound = [v - random.uniform(2, 5) for v in values]
    actual_values = [v + random.uniform(-4, 4) + random.choice([-1, 1]) * i * 0.1 for i, v in enumerate(values)]

    metrics = {
        "mean_absolute_error": round(random.uniform(1, 5), 2),
        "confidence_score": round(random.uniform(0.7, 0.95), 3),
        "horizon": "10 hours"
    }

    return {
        "set_id": set_id,
        "metrics": metrics,
        "chart_data": {
             "time_points": time_points,
             "values": values,
             "upper_bound": upper_bound,
             "lower_bound": lower_bound,
             "actual_values": actual_values
        }
    }

def get_all_variable_names():
    """Simulates fetching the list of all available variable names."""
    global SIMULATED_VARIABLE_NAMES
    return SIMULATED_VARIABLE_NAMES

def get_variable_data(variable_name: str):
    """
    Simulates fetching historical data for a specific variable
    and generating simulated time-series data.
    """
    global SIMULATED_VARIABLE_NAMES
    if variable_name not in SIMULATED_VARIABLE_NAMES:
        return None

    print(f"Simulating data fetch for variable: {variable_name}")

    base_time = datetime.datetime.now() - datetime.timedelta(days=1)
    num_points = 50
    timestamps = [(base_time + datetime.timedelta(minutes=i*30)).strftime("%Y-%m-%d %H:%M:%S") for i in range(num_points)]

    base_value = abs(hash(variable_name)) % 100
    noise_factor = (abs(hash(variable_name + "noise")) % 10) / 10.0 + 0.5
    trend_factor = (hash(variable_name + "trend") % 3) - 1

    values = []
    current_value = base_value
    for i in range(num_points):
        noise = random.uniform(-1, 1) * noise_factor * (base_value / 20 + 1)
        trend = trend_factor * i * 0.05
        current_value += noise + trend
        if "Sensor" in variable_name and random.random() < 0.05:
             current_value += random.uniform(-5, 5) * noise_factor
        elif "Index" in variable_name and random.random() < 0.02:
             current_value *= random.uniform(0.95, 1.05)
        values.append(round(current_value, 2))

    return {
        "name": variable_name,
        "timestamps": timestamps,
        "values": values
    }

def get_recent_activity(limit=5):
    """Simulates fetching the latest activity log entries."""
    now = datetime.datetime.now()
    activities = [
        {"ts": (now - datetime.timedelta(minutes=random.randint(1,5))).strftime("%Y-%m-%d %H:%M:%S"), "msg": "Forecast 'fc_20250428_1540' generated."},
        {"ts": (now - datetime.timedelta(minutes=random.randint(5,15))).strftime("%Y-%m-%d %H:%M:%S"), "msg": "Autopilot run 'Optimize Alpha' completed."},
        {"ts": (now - datetime.timedelta(minutes=random.randint(15,25))).strftime("%Y-%m-%d %H:%M:%S"), "msg": "Retrodiction analysis started for run 'retro_xyz'."},
        {"ts": (now - datetime.timedelta(minutes=random.randint(25,40))).strftime("%Y-%m-%d %H:%M:%S"), "msg": "Recursive learning status changed to Enabled."},
        {"ts": (now - datetime.timedelta(minutes=random.randint(40,60))).strftime("%Y-%m-%d %H:%M:%S"), "msg": "System status changed to Idle."},
        {"ts": (now - datetime.timedelta(minutes=random.randint(60,90))).strftime("%Y-%m-%d %H:%M:%S"), "msg": "Memory Explorer query executed."},
    ]
    random.shuffle(activities)
    return activities[:limit]

def get_recursive_learning_status():
    """Gets the current simulated recursive learning mode status."""
    global SIMULATED_RECURSIVE_LEARNING_ENABLED
    return SIMULATED_RECURSIVE_LEARNING_ENABLED

def set_recursive_learning_status(new_status: bool):
    """Sets the simulated recursive learning mode status."""
    global SIMULATED_RECURSIVE_LEARNING_ENABLED
    SIMULATED_RECURSIVE_LEARNING_ENABLED = new_status
    print(f"Recursive learning status set to: {new_status}")
    return True

def get_autopilot_status():
    """Simulates fetching the current autopilot status."""
    global SIMULATED_AUTOPILOT_STATUS
    return SIMULATED_AUTOPILOT_STATUS

def get_autopilot_run_history(limit=10):
    """Simulates fetching the autopilot run history."""
    global SIMULATED_AUTOPILOT_HISTORY
    return sorted(SIMULATED_AUTOPILOT_HISTORY, key=lambda x: x["start_time"], reverse=True)[:limit]

def start_autopilot_run(goal: str, constraints: str):
    """Simulates starting an autopilot run."""
    global SIMULATED_AUTOPILOT_STATUS, SIMULATED_AUTOPILOT_HISTORY
    if SIMULATED_AUTOPILOT_STATUS["state"] == "Running":
        print("Autopilot already running.")
        return False, "Autopilot already running."

    run_id = f"ap_run_{len(SIMULATED_AUTOPILOT_HISTORY) + 1:03d}"
    start_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_run = {
        "id": run_id, "start_time": start_time, "end_time": None,
        "goal": goal, "constraints": constraints, "status": "Running"
    }
    SIMULATED_AUTOPILOT_STATUS = {"state": "Running", "current_run": new_run}
    SIMULATED_AUTOPILOT_HISTORY.insert(0, new_run)
    print(f"Autopilot run {run_id} started. Goal: {goal}, Constraints: {constraints}")
    return True, f"Autopilot run {run_id} started."

def stop_autopilot_run():
    """Simulates stopping the current autopilot run."""
    global SIMULATED_AUTOPILOT_STATUS, SIMULATED_AUTOPILOT_HISTORY
    if SIMULATED_AUTOPILOT_STATUS["state"] != "Running":
        print("Autopilot is not running.")
        return False, "Autopilot is not running."

    run_id = SIMULATED_AUTOPILOT_STATUS["current_run"]["id"]
    end_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for run in SIMULATED_AUTOPILOT_HISTORY:
        if run["id"] == run_id:
            run["end_time"] = end_time
            run["status"] = "Stopped"
            break

    SIMULATED_AUTOPILOT_STATUS = {"state": "Stopped", "current_run": None}
    print(f"Autopilot run {run_id} stopped.")
    return True, f"Autopilot run {run_id} stopped."

# --- Memory Explorer Placeholders ---
SIMULATED_MEMORY_ITEMS = {
    "rules": [
        {"id": "R001", "name": "Rule: High Temp -> Alert", "type": "Rule", "confidence": 0.95, "source": "Learned"},
        {"id": "R002", "name": "Rule: Low Pressure -> Warning", "type": "Rule", "confidence": 0.88, "source": "Manual"},
        {"id": "R003", "name": "Rule: Usage Spike -> Scale Up", "type": "Rule", "confidence": 0.91, "source": "Learned"},
    ],
    "concepts": [
        {"id": "C001", "name": "Concept: Temperature Drift", "type": "Concept", "relevance": 0.7, "tags": ["sensor", "anomaly"]},
        {"id": "C002", "name": "Concept: Market Sentiment", "type": "Concept", "relevance": 0.9, "tags": ["finance", "trend"]},
    ],
    "facts": [
         {"id": "F001", "name": "Fact: Sensor S1 Offline", "type": "Fact", "timestamp": "2025-04-28 12:00:00", "source": "Observation"},
         {"id": "F002", "name": "Fact: User Feedback Received", "type": "Fact", "timestamp": "2025-04-28 14:30:00", "source": "Input"},
    ]
}

def get_memory_items(item_type=None):
    """Simulates fetching memory items, optionally filtered by type."""
    if item_type and item_type.lower() in SIMULATED_MEMORY_ITEMS:
        return {item_type.lower(): SIMULATED_MEMORY_ITEMS[item_type.lower()]}
    else:
        return SIMULATED_MEMORY_ITEMS

def get_memory_item_details(item_id):
    """Simulates fetching details for a specific memory item."""
    print(f"Fetching details for memory item: {item_id}")
    for category_items in SIMULATED_MEMORY_ITEMS.values():
        for item in category_items:
            if item["id"] == item_id:
                details = item.copy()
                details["description"] = f"Detailed description for {item['name']} ({item_id}). Lorem ipsum dolor sit amet."
                details["created_at"] = "2025-04-20 10:00:00"
                details["last_updated"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                details["related_items"] = [f"REL_{random.randint(1,10)}" for _ in range(random.randint(0,3))]
                if item['type'] == 'Rule':
                    details['conditions'] = ["Condition A", "Condition B"]
                    details['action'] = "Perform Action X"
                elif item['type'] == 'Concept':
                    details['attributes'] = {"attr1": "value1", "attr2": "value2"}
                return details
    return None

# --- Retrodiction Helper Class ---
class HistoricalDataLoader:
    """Simple loader to provide historical data snapshots for retrodiction."""
    def __init__(self, historical_series: pd.Series):
        self.historical_data = historical_series
        if isinstance(self.historical_data.index, pd.DatetimeIndex):
            self.historical_data = self.historical_data.sort_index()

    def get_snapshot_by_turn(self, turn_index: int) -> dict | None:
        """
        Returns the historical ground truth for the prediction made *at* the given turn index.
        The prediction made at turn_index 't' is for the state at turn 't+1'.
        Therefore, we need to provide the actual historical value from turn 't+1'.
        """
        ground_truth_index = turn_index + 1

        if 0 <= ground_truth_index < len(self.historical_data):
            try:
                ground_truth_value = self.historical_data.iloc[ground_truth_index]
                return {'nvidia_stock': ground_truth_value}
            except IndexError:
                 print(f"Error: Internal IndexError accessing historical data at index {ground_truth_index}.")
                 return None
        else:
            return None