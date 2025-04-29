import tkinter as tk
from tkinter import ttk
import requests
import json

class PulseApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Pulse Desktop UI")
        self.root.geometry("800x600")

        # Create a notebook (tabbed interface) for different sections
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(pady=10, padx=10, expand=True, fill="both")

        # Create frames for each section
        self.forecasts_frame = ttk.Frame(self.notebook, padding="10")
        self.retrodiction_frame = ttk.Frame(self.notebook, padding="10")
        self.autopilot_frame = ttk.Frame(self.notebook, padding="10")
        self.ai_training_review_frame = ttk.Frame(self.notebook, padding="10")

        # Add frames to the notebook
        self.notebook.add(self.forecasts_frame, text="Forecasts")
        self.notebook.add(self.retrodiction_frame, text="Retrodiction")
        self.notebook.add(self.autopilot_frame, text="Autopilot")
        self.notebook.add(self.ai_training_review_frame, text="AI Training Review")

        # --- Placeholder UI elements/comments for each section ---

        # Forecasts Section
        # Forecasts Section
        # Add specific UI elements for displaying forecasts here
        # Example: Treeview for listing forecasts, buttons for actions

        # Treeview to display forecasts
        self.forecasts_tree = ttk.Treeview(self.forecasts_frame, columns=("Variable", "Value"), show="headings")
        self.forecasts_tree.heading("Variable", text="Variable")
        self.forecasts_tree.heading("Value", text="Value")
        self.forecasts_tree.pack(pady=10, padx=10, expand=True, fill="both")

        # Refresh button
        self.refresh_button = ttk.Button(self.forecasts_frame, text="Refresh Forecasts", command=self.fetch_forecasts)
        self.refresh_button.pack(pady=10)

        # Status label for messages
        self.forecasts_status_label = ttk.Label(self.forecasts_frame, text="")
        self.forecasts_status_label.pack(pady=5)

        # Bind tab change event to load forecasts
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_change)

        # Retrodiction Section
        # Retrodiction Section UI Elements
        ttk.Label(self.retrodiction_frame, text="Retrodiction Simulation").pack(pady=10)

        # Input fields
        input_frame = ttk.Frame(self.retrodiction_frame)
        input_frame.pack(pady=5)

        ttk.Label(input_frame, text="Start Date (YYYY-MM-DD):").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.start_date_entry = ttk.Entry(input_frame, width=20)
        self.start_date_entry.grid(row=0, column=1, padx=5, pady=2, sticky="ew")

        ttk.Label(input_frame, text="Days:").grid(row=1, column=0, padx=5, pady=2, sticky="w")
        self.days_entry = ttk.Entry(input_frame, width=20)
        self.days_entry.grid(row=1, column=1, padx=5, pady=2, sticky="ew")

        ttk.Label(input_frame, text="Variables of Interest (comma-separated):").grid(row=2, column=0, padx=5, pady=2, sticky="w")
        self.variables_of_interest_entry = ttk.Entry(input_frame, width=40)
        self.variables_of_interest_entry.grid(row=2, column=1, padx=5, pady=2, sticky="ew")

        # Run Button
        self.run_retrodiction_button = ttk.Button(self.retrodiction_frame, text="Run Retrodiction Simulation", command=self._run_retrodiction_simulation)
        self.run_retrodiction_button.pack(pady=10)

        # Status Label
        self.retrodiction_status_label = ttk.Label(self.retrodiction_frame, text="")
        self.retrodiction_status_label.pack(pady=5)

        # Results Display
        ttk.Label(self.retrodiction_frame, text="Results:").pack(pady=5)
        self.retrodiction_results_text = tk.Text(self.retrodiction_frame, height=10, width=80)
        self.retrodiction_results_text.pack(pady=5, expand=True, fill="both")

        # Add specific UI elements for running retrodiction and displaying results here
        # Example: Button to trigger retrodiction, text area for output

        # Autopilot Section
        # Control buttons
        control_frame = ttk.Frame(self.autopilot_frame)
        control_frame.pack(pady=10)

        self.start_autopilot_button = ttk.Button(control_frame, text="Start Autopilot", command=self.start_autopilot)
        self.start_autopilot_button.pack(side="left", padx=5)

        self.stop_autopilot_button = ttk.Button(control_frame, text="Stop Autopilot", command=self.stop_autopilot)
        self.stop_autopilot_button.pack(side="left", padx=5)

        # Status display
        self.autopilot_status_label = ttk.Label(self.autopilot_frame, text="Autopilot Status: Unknown")
        self.autopilot_status_label.pack(pady=10)

        # History display
        ttk.Label(self.autopilot_frame, text="Autopilot History:").pack(pady=5)
        self.autopilot_history_tree = ttk.Treeview(self.autopilot_frame, columns=("Run ID", "Start Time", "End Time", "Status"), show="headings")
        self.autopilot_history_tree.heading("Run ID", text="Run ID")
        self.autopilot_history_tree.heading("Start Time", text="Start Time")
        self.autopilot_history_tree.heading("End Time", text="End Time")
        self.autopilot_history_tree.heading("Status", text="Status")
        self.autopilot_history_tree.pack(pady=5, expand=True, fill="both")

        # Placeholder methods (will implement logic next)
        self.autopilot_status_polling_job = None # To store the after job ID

        # Add specific UI elements for managing autopilot settings and status here
        # Example: Checkboxes for options, status labels

        # AI Training Review Section
        ai_review_input_frame = ttk.Frame(self.ai_training_review_frame)
        ai_review_input_frame.pack(pady=10)

        ttk.Label(ai_review_input_frame, text="Previous Batch ID:").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.previous_batch_id_entry = ttk.Entry(ai_review_input_frame, width=30)
        self.previous_batch_id_entry.grid(row=0, column=1, padx=5, pady=2, sticky="ew")

        ttk.Label(ai_review_input_frame, text="Current Batch ID:").grid(row=1, column=0, padx=5, pady=2, sticky="w")
        self.current_batch_id_entry = ttk.Entry(ai_review_input_frame, width=30)
        self.current_batch_id_entry.grid(row=1, column=1, padx=5, pady=2, sticky="ew")

        self.trigger_audit_button = ttk.Button(self.ai_training_review_frame, text="Trigger AI Training Audit", command=self.trigger_ai_training_audit)
        self.trigger_audit_button.pack(pady=10)

        ttk.Label(self.ai_training_review_frame, text="Audit Report:").pack(pady=5)
        self.audit_report_text = tk.Text(self.ai_training_review_frame, height=15, width=80)
        self.audit_report_text.pack(pady=5, expand=True, fill="both")

        self.ai_review_status_label = ttk.Label(self.ai_training_review_frame, text="")
        self.ai_review_status_label.pack(pady=5)

        # Add specific UI elements for reviewing AI training data and results here
        # Example: Data display, review controls

        # --- Backend Communication Mechanism ---
        self.backend_url = "http://127.0.0.1:5002/api" # Base URL for the Flask backend

    def make_request(self, method, endpoint, data=None):
        """
        Makes an HTTP request to the Pulse Flask backend.

        Args:
            method (str): HTTP method ('GET' or 'POST').
            endpoint (str): API endpoint (e.g., '/forecasts/latest/all').
            data (dict, optional): JSON data for POST requests. Defaults to None.

        Returns:
            dict or None: JSON response from the backend, or None if an error occurred.
        """
        url = f"{self.backend_url}{endpoint}"
        try:
            if method.upper() == 'GET':
                response = requests.get(url)
            elif method.upper() == 'POST':
                response = requests.post(url, json=data)
            else:
                print(f"Unsupported HTTP method: {method}")
                return None

            response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
            return response.json()

        except requests.exceptions.RequestException as e:
            print(f"Error making request to {url}: {e}")
            return None

    # Example usage (can be called from UI elements later)
    def fetch_forecasts(self):
        """Fetches the latest forecasts and updates the UI."""
        self.forecasts_status_label.config(text="Fetching forecasts...")
        self.forecasts_tree.delete(*self.forecasts_tree.get_children()) # Clear existing data

        data = self.make_request('GET', '/forecasts/latest/all')

        if data:
            self.forecasts_status_label.config(text="Forecasts loaded successfully.")
            # Assuming data is a dictionary where keys are variable names and values are forecast values
            for variable, value in data.items():
                self.forecasts_tree.insert("", "end", values=(variable, value))
        else:
            self.forecasts_status_label.config(text="Failed to fetch forecasts.")

    def on_tab_change(self, event):
        """Handles tab change event to load data for the selected tab."""
        selected_tab_index = self.notebook.index(self.notebook.select())
        tab_text = self.notebook.tab(selected_tab_index, "text")

        if tab_text == "Forecasts":
            self.fetch_forecasts()
        elif tab_text == "Autopilot":
            self.fetch_autopilot_status()
            self.fetch_autopilot_history()
            self._start_autopilot_status_polling()
        else:
            self._stop_autopilot_status_polling() # Stop polling when switching away

    def run_retrodiction(self, params):
        data = self.make_request('POST', '/retrodiction/run', data=params)
        if data:
            print("Retrodiction Result:", data)
            # Process and display retrodiction results in the UI

    def _run_retrodiction_simulation(self):
        """Triggers a retrodiction simulation run."""
        start_date = self.start_date_entry.get()
        days = self.days_entry.get()
        variables_str = self.variables_of_interest_entry.get()
        variables_of_interest = [v.strip() for v in variables_str.split(',') if v.strip()]

        params = {
            "start_date": start_date,
            "days": int(days) if days.isdigit() else None, # Convert days to int if valid
            "variables_of_interest": variables_of_interest
        }

        self.retrodiction_status_label.config(text="Starting retrodiction simulation...")
        self.retrodiction_results_text.delete("1.0", tk.END) # Clear previous results

        response_data = self.make_request('POST', '/retrodiction/run', data=params)

        if response_data and 'run_id' in response_data:
            run_id = response_data['run_id']
            self.retrodiction_status_label.config(text=f"Simulation started with Run ID: {run_id}. Polling status...")
            self._poll_retrodiction_status(run_id)
        else:
            error_message = response_data.get('error', 'Failed to start retrodiction simulation.') if response_data else 'Failed to start retrodiction simulation.'
            self.retrodiction_status_label.config(text=f"Error: {error_message}")

    def _poll_retrodiction_status(self, run_id):
        """Polls the backend for the retrodiction simulation status."""
        endpoint = f'/retrodiction/status/{run_id}'
        status_data = self.make_request('GET', endpoint)

        if status_data:
            status = status_data.get('status')
            if status == 'completed':
                self.retrodiction_status_label.config(text=f"Simulation {run_id} completed.")
                self._display_retrodiction_results(status_data.get('results', {}))
            elif status == 'failed':
                error_message = status_data.get('error', 'Simulation failed.')
                self.retrodiction_status_label.config(text=f"Simulation {run_id} failed: {error_message}")
            else: # running or pending
                progress = status_data.get('progress', 'N/A')
                self.retrodiction_status_label.config(text=f"Simulation {run_id} status: {status} (Progress: {progress})")
                # Poll again after 2 seconds
                self.root.after(2000, self._poll_retrodiction_status, run_id)
        else:
            self.retrodiction_status_label.config(text=f"Error polling status for {run_id}. Stopping poll.")

    def _display_retrodiction_results(self, results):
        """Displays the retrodiction simulation results in the UI."""
        self.retrodiction_results_text.delete("1.0", tk.END)
        try:
            # Pretty print JSON results
            formatted_results = json.dumps(results, indent=4)
            self.retrodiction_results_text.insert(tk.END, formatted_results)
        except Exception as e:
            self.retrodiction_results_text.insert(tk.END, f"Error displaying results: {e}\n{results}")

    def trigger_ai_training_audit(self):
        """Triggers an AI training audit and displays the report."""
        previous_batch_id = self.previous_batch_id_entry.get()
        current_batch_id = self.current_batch_id_entry.get()

        if not previous_batch_id or not current_batch_id:
            self._update_ai_review_status("Please enter both Previous Batch ID and Current Batch ID.", "red")
            return

        params = {
            "previous_batch_id": previous_batch_id,
            "current_batch_id": current_batch_id
        }

        self._update_ai_review_status("Triggering AI training audit...", "blue")
        self.audit_report_text.delete("1.0", tk.END) # Clear previous report

        response_data = self.make_request('POST', '/api/learning/audit', data=params)

        if response_data:
            if response_data.get('status') == 'success':
                self._update_ai_review_status("Audit completed successfully.", "green")
                self._display_audit_report(response_data.get('report', {}))
            else:
                error_message = response_data.get('error', 'Audit failed.')
                self._update_ai_review_status(f"Audit failed: {error_message}", "red")
                self.audit_report_text.insert(tk.END, f"Error: {error_message}")
        else:
            self._update_ai_review_status("Failed to trigger audit request.", "red")
            self.audit_report_text.insert(tk.END, "Error: Failed to trigger audit request.")

    def _display_audit_report(self, report):
        """Displays the audit report in the text area."""
        self.audit_report_text.delete("1.0", tk.END)
        try:
            formatted_report = json.dumps(report, indent=4)
            self.audit_report_text.insert(tk.END, formatted_report)
        except Exception as e:
            self.audit_report_text.insert(tk.END, f"Error displaying report: {e}\n{report}")

    def _update_ai_review_status(self, message, color="black"):
        """Updates the AI review status label with a message and color."""
        self.ai_review_status_label.config(text=message, foreground=color)

    def start_autopilot(self):
        """Starts the autopilot."""
        self.autopilot_status_label.config(text="Starting Autopilot...")
        data = self.make_request('POST', '/autopilot/start')
        if data and data.get('status') == 'success':
            self.autopilot_status_label.config(text="Autopilot Status: Started")
            self.fetch_autopilot_history() # Refresh history after starting
        else:
            error_message = data.get('error', 'Failed to start autopilot.') if data else 'Failed to start autopilot.'
            self.autopilot_status_label.config(text=f"Autopilot Status: Error - {error_message}")
        self._start_autopilot_status_polling() # Ensure polling is active

    def stop_autopilot(self):
        """Stops the autopilot."""
        self.autopilot_status_label.config(text="Stopping Autopilot...")
        data = self.make_request('POST', '/autopilot/stop')
        if data and data.get('status') == 'success':
            self.autopilot_status_label.config(text="Autopilot Status: Stopped")
            self.fetch_autopilot_history() # Refresh history after stopping
        else:
            error_message = data.get('error', 'Failed to stop autopilot.') if data else 'Failed to stop autopilot.'
            self.autopilot_status_label.config(text=f"Autopilot Status: Error - {error_message}")
        self._stop_autopilot_status_polling() # Stop polling when stopped

    def fetch_autopilot_status(self):
        """Fetches and updates the current autopilot status."""
        data = self.make_request('GET', '/autopilot/status')
        if data and 'status' in data:
            self.autopilot_status_label.config(text=f"Autopilot Status: {data['status']}")
        else:
            error_message = data.get('error', 'Failed to fetch status.') if data else 'Failed to fetch status.'
            self.autopilot_status_label.config(text=f"Autopilot Status: Error - {error_message}")

    def fetch_autopilot_history(self):
        """Fetches and displays the autopilot history."""
        self.autopilot_history_tree.delete(*self.autopilot_history_tree.get_children()) # Clear existing data
        data = self.make_request('GET', '/autopilot/history')
        if data and isinstance(data, list):
            for run in data:
                run_id = run.get('run_id', 'N/A')
                start_time = run.get('start_time', 'N/A')
                end_time = run.get('end_time', 'N/A')
                status = run.get('status', 'N/A')
                self.autopilot_history_tree.insert("", "end", values=(run_id, start_time, end_time, status))
        else:
            error_message = data.get('error', 'Failed to fetch history.') if data and isinstance(data, dict) else 'Failed to fetch history.'
            # Optionally display error in the history area or status label
            print(f"Error fetching autopilot history: {error_message}")


    def _start_autopilot_status_polling(self):
        """Starts periodic polling for autopilot status."""
        self._stop_autopilot_status_polling() # Stop any existing polling first
        self.fetch_autopilot_status() # Fetch immediately
        # Poll every 5 seconds
        self.autopilot_status_polling_job = self.root.after(5000, self._start_autopilot_status_polling)

    def _stop_autopilot_status_polling(self):
        """Stops periodic polling for autopilot status."""
        if self.autopilot_status_polling_job:
            self.root.after_cancel(self.autopilot_status_polling_job)
            self.autopilot_status_polling_job = None


if __name__ == "__main__":
    root = tk.Tk()
    app = PulseApp(root)
    root.mainloop()