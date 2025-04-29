import os
import json
import traceback

def get_latest_forecast_from_log(variable_name: str):
    """
    Reads the *last line* of logs/forecast_output_compressed.jsonl,
    parses the JSON, and extracts forecast data for the specified variable_name
    from the 'examples' list within that JSON object.
    """
    last_line_data = None
    log_file_path = os.path.join(os.path.dirname(__file__), '..', 'logs', 'forecast_output_compressed.jsonl')
    print(f"Attempting to read forecast log: {log_file_path}")

    try:
        if not os.path.exists(log_file_path):
            print(f"Error: Log file not found at {log_file_path}")
            return None, "Log file not found."

        with open(log_file_path, 'rb') as f:
            try:
                f.seek(-2, os.SEEK_END)
                while f.read(1) != b'\n':
                    f.seek(-2, os.SEEK_CUR)
            except OSError:
                f.seek(0)
            last_line = f.readline().decode('utf-8')

        if not last_line.strip():
             print(f"Error: Last line of log file is empty or invalid.")
             return None, "Last line of log file is empty or invalid."

        try:
            last_line_data = json.loads(last_line)
        except json.JSONDecodeError:
            print(f"Error: Failed to decode JSON from the last line: {last_line.strip()}")
            return None, "Failed to decode JSON from the last log entry."

        if not isinstance(last_line_data, dict) or 'examples' not in last_line_data or not isinstance(last_line_data['examples'], list):
            print(f"Error: Last log entry JSON does not contain a valid 'examples' list.")
            return None, "Last log entry JSON does not contain a valid 'examples' list."

        examples = last_line_data['examples']
        if not examples:
            print(f"Error: 'examples' list in the last log entry is empty.")
            return None, f"'examples' list in the last log entry is empty for {variable_name}."

        timestamps = []
        values = []
        for example in examples:
            try:
                timestamp = example['timestamp']
                value = example['exposure'][variable_name]
                timestamps.append(timestamp)
                values.append(value)
            except KeyError as e:
                print(f"Warning: Skipping example due to missing key: {e}. Example: {example}")
                continue
            except TypeError:
                 print(f"Warning: Skipping example due to unexpected structure. Example: {example}")
                 continue

        if not timestamps:
            print(f"Error: No valid data points found for '{variable_name}' in the 'examples' of the last log entry.")
            return None, f"No forecast data found for '{variable_name}' in the latest log entry."

        print(f"Successfully extracted {len(timestamps)} data points for '{variable_name}' from the last log entry.")
        return {
            "timestamps": timestamps,
            "values": values,
            "upper_bound": None,
            "lower_bound": None
        }, None

    except FileNotFoundError:
        print(f"Error: Log file not found at {log_file_path}")
        return None, "Log file not found."
    except Exception as e:
        print(f"Error: Failed to read or process log file {log_file_path}: {e}")
        traceback.print_exc()
        return None, f"Failed to read or process log file: {e}"