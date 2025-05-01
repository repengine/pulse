import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog, scrolledtext
import requests
import json
import os
import sys
import threading
import matplotlib
matplotlib.use('TkAgg')  # Must be before importing pyplot
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import matplotlib.pyplot as plt  # for plt.setp in date‐label rotation
from datetime import datetime    # for timestamp in clear_selected_log

# Add the parent directory to sys.path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import modules from the Pulse system
try:
    from learning.forecast_pipeline_runner import run_forecast_pipeline
    from learning.recursion_audit import generate_recursion_report
    from dev_tools.pulse_ui_plot import load_variable_trace, plot_variables
    import core.pulse_config
    from operator_interface.learning_log_viewer import load_learning_events, summarize_learning_events
    from memory.variable_cluster_engine import summarize_clusters
    from operator_interface.variable_cluster_digest_formatter import format_variable_cluster_digest_md
    from operator_interface.mutation_digest_exporter import export_full_digest
    from operator_interface.symbolic_contradiction_digest import format_contradiction_cluster_md, load_symbolic_conflict_events
except ImportError as e:
    print(f"Warning: Some Pulse modules could not be imported: {e}")
    print("Some features may be disabled")

class PulseApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Pulse Desktop UI")
        self.root.geometry("1024x768")  # Larger default size for better visibility

        # Initialize polling job variable
        self.autopilot_status_polling_job = None

        # Set up a better visual style
        style = ttk.Style()
        # Configure some custom styles
        style.configure('TLabel', font=('Arial', 11))
        style.configure('TButton', font=('Arial', 11))
        style.configure('TNotebook.Tab', font=('Arial', 11), padding=[10, 4])
        style.configure('Header.TLabel', font=('Arial', 12, 'bold'))
        
        # Main frame with padding
        main_frame = ttk.Frame(root, padding="10")
        main_frame.pack(fill="both", expand=True)
        
        # Create a status bar at the bottom
        self.status_bar = ttk.Label(root, text="Ready", relief="sunken", anchor="w", padding=(5, 2))
        self.status_bar.pack(side="bottom", fill="x")

        # Create a notebook (tabbed interface) for different sections
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(pady=5, padx=5, expand=True, fill="both")

        # Create frames for each section
        self.dashboard_frame = ttk.Frame(self.notebook, padding="10")
        self.forecasts_frame = ttk.Frame(self.notebook, padding="10")
        self.retrodiction_frame = ttk.Frame(self.notebook, padding="10")
        self.autopilot_frame = ttk.Frame(self.notebook, padding="10")
        self.learning_frame = ttk.Frame(self.notebook, padding="10")  # Renamed from ai_training_review_frame
        self.analysis_frame = ttk.Frame(self.notebook, padding="10")  # New
        self.diagnostics_frame = ttk.Frame(self.notebook, padding="10")  # New
        
        # Add frames to the notebook in the desired order
        self.notebook.add(self.dashboard_frame, text="Dashboard")
        self.notebook.add(self.forecasts_frame, text="Forecasts")
        self.notebook.add(self.retrodiction_frame, text="Retrodiction")
        self.notebook.add(self.autopilot_frame, text="Autopilot")
        self.notebook.add(self.learning_frame, text="Learning & Training")
        self.notebook.add(self.analysis_frame, text="Analysis")
        self.notebook.add(self.diagnostics_frame, text="Diagnostics")
        
        # Track whether modules were successfully imported
        self.has_pulse_modules = 'core.pulse_config' in sys.modules

        # --- Initialize tab contents ---
        self._init_dashboard_tab()
        self._init_forecasts_tab()
        self._init_retrodiction_tab()
        self._init_autopilot_tab()
        self._init_learning_tab()  # Renamed from ai_training_review
        self._init_analysis_tab()  # New
        self._init_diagnostics_tab()  # New

        # Bind tab change event
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_change)

        # --- Backend Communication Mechanism ---
        self.backend_url = "http://127.0.0.1:5002/api" # Base URL for the Flask backend
        
        # Initialize status
        self.update_status("Pulse Desktop UI ready")

    def update_status(self, message):
        """Updates the status bar with a message."""
        self.status_bar.config(text=message)

    def _init_dashboard_tab(self):
        """Initializes the Dashboard tab with system overview and quick access buttons."""
        # Header
        ttk.Label(self.dashboard_frame, text="Pulse System Dashboard", style="Header.TLabel").pack(pady=(10, 20))
        
        # System status display
        status_frame = ttk.LabelFrame(self.dashboard_frame, text="System Status", padding=10)
        status_frame.pack(padx=10, pady=10, fill="x")

        # Create a frame for status indicators
        indicators_frame = ttk.Frame(status_frame)
        indicators_frame.pack(fill="x", expand=True)
        
        # Status indicators
        backend_status = ttk.Label(indicators_frame, text="Backend: Unknown")
        backend_status.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.backend_status = backend_status
        
        forecast_status = ttk.Label(indicators_frame, text="Forecast Engine: Unknown")
        forecast_status.grid(row=0, column=1, padx=10, pady=5, sticky="w")
        self.forecast_status = forecast_status
        
        autopilot_status = ttk.Label(indicators_frame, text="Autopilot: Unknown")
        autopilot_status.grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.dashboard_autopilot_status = autopilot_status
        
        # Check connection button
        check_button = ttk.Button(status_frame, text="Check Connections", 
                                 command=self.check_connections)
        check_button.pack(pady=(10, 5))

        # Quick Actions section
        actions_frame = ttk.LabelFrame(self.dashboard_frame, text="Quick Actions", padding=10)
        actions_frame.pack(padx=10, pady=10, fill="x")

        # Create a grid for buttons
        btn_frame = ttk.Frame(actions_frame)
        btn_frame.pack(fill="both", expand=True)
        
        # Row 1 buttons
        run_forecast_btn = ttk.Button(btn_frame, text="Run Forecast", 
                                     command=lambda: self.notebook.select(1))  # Switch to Forecasts tab
        run_forecast_btn.grid(row=0, column=0, padx=10, pady=5, sticky="ew")
        
        run_retrodiction_btn = ttk.Button(btn_frame, text="Run Retrodiction", 
                                         command=lambda: self.notebook.select(2))  # Switch to Retrodiction tab
        run_retrodiction_btn.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        
        # Row 2 buttons
        start_autopilot_btn = ttk.Button(btn_frame, text="Start Autopilot", command=self.start_autopilot_from_dash)
        start_autopilot_btn.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        
        view_analysis_btn = ttk.Button(btn_frame, text="Analysis Tools", 
                                      command=lambda: self.notebook.select(5))  # Switch to Analysis tab
        view_analysis_btn.grid(row=1, column=1, padx=10, pady=5, sticky="ew")

        # Configure grid columns to expand equally
        btn_frame.columnconfigure(0, weight=1)
        btn_frame.columnconfigure(1, weight=1)

        # Recent Activity section
        activity_frame = ttk.LabelFrame(self.dashboard_frame, text="Recent Activity", padding=10)
        activity_frame.pack(padx=10, pady=10, fill="both", expand=True)
        
        # Activity log
        self.activity_log = scrolledtext.ScrolledText(activity_frame, height=10)
        self.activity_log.pack(fill="both", expand=True)
        self.activity_log.insert(tk.END, "Pulse Desktop UI started\n")
        self.activity_log.config(state="disabled")  # Make read-only

        # Check connections on startup
        self.root.after(1000, self.check_connections)

    def check_connections(self):
        """Check connections to various system components."""
        self.update_status("Checking connections...")
        
        # Check backend connection
        try:
            backend_status = self.make_request('GET', '/status')
            if backend_status and backend_status.get('status') == 'online':
                self.backend_status.config(text="Backend: Online", foreground="green")
                self.log_activity("Backend connection successful")
            else:
                self.backend_status.config(text="Backend: Offline", foreground="red")
                self.log_activity("Backend connection failed")
        except Exception:
            self.backend_status.config(text="Backend: Error", foreground="red")
            self.log_activity("Backend connection error")
        
        # Check forecast engine
        try:
            forecast_status = self.make_request('GET', '/forecasts/status')
            if forecast_status and forecast_status.get('status') == 'ready':
                self.forecast_status.config(text="Forecast Engine: Ready", foreground="green")
                self.log_activity("Forecast engine is ready")
            else:
                self.forecast_status.config(text="Forecast Engine: Not Ready", foreground="orange")
                self.log_activity("Forecast engine is not ready")
        except Exception:
            self.forecast_status.config(text="Forecast Engine: Unknown", foreground="gray")
        
        # Check autopilot status
        try:
            autopilot_status = self.make_request('GET', '/autopilot/status')
            if autopilot_status and autopilot_status.get('status'):
                status_text = autopilot_status.get('status').capitalize()
                color = "green" if status_text == "Running" else "gray"
                self.dashboard_autopilot_status.config(text=f"Autopilot: {status_text}", foreground=color)
                self.log_activity(f"Autopilot status: {status_text}")
            else:
                self.dashboard_autopilot_status.config(text="Autopilot: Unknown", foreground="gray")
        except Exception:
            self.dashboard_autopilot_status.config(text="Autopilot: Error", foreground="red")
        
        self.update_status("Connection check completed")

    def log_activity(self, message):
        """Add a message to the activity log with timestamp."""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Enable editing temporarily
        self.activity_log.config(state="normal")
        
        # Insert at the beginning
        self.activity_log.insert("1.0", f"[{timestamp}] {message}\n")
        
        # Make read-only again
        self.activity_log.config(state="disabled")

    def start_autopilot_from_dash(self):
        """Start autopilot from the dashboard."""
        self.start_autopilot()
        self.log_activity("Started Autopilot from Dashboard")
        # Update dashboard status
        self.dashboard_autopilot_status.config(text="Autopilot: Running", foreground="green")

    def _init_forecasts_tab(self):
        """Initializes the Forecasts tab."""
        # Create a frame for the forecast display and controls
        forecast_controls_frame = ttk.Frame(self.forecasts_frame)
        forecast_controls_frame.pack(pady=10, fill="x")
        
        # Refresh button
        self.refresh_button = ttk.Button(forecast_controls_frame, text="Refresh Forecasts", command=self.fetch_forecasts)
        self.refresh_button.pack(side="left", padx=10)
        
        # Add button to submit forecasts for training review
        self.submit_forecast_button = ttk.Button(forecast_controls_frame, text="Submit for Training Review", 
                                            command=self.submit_forecasts_for_review)
        self.submit_forecast_button.pack(side="left", padx=10)
        self.submit_forecast_button.config(state="disabled")  # Initially disabled until forecasts are loaded
        
        # Status label for messages
        self.forecasts_status_label = ttk.Label(self.forecasts_frame, text="")
        self.forecasts_status_label.pack(pady=5, fill="x")
        
        # Create a frame to contain the table and chart side by side
        content_frame = ttk.Frame(self.forecasts_frame)
        content_frame.pack(expand=True, fill="both", padx=10)
        
        # Create a frame for the table on the left
        table_frame = ttk.Frame(content_frame)
        table_frame.pack(side="left", expand=True, fill="both", padx=(0, 5))
        
        # Treeview to display forecasts
        self.forecasts_tree = ttk.Treeview(table_frame, columns=("Variable", "Value"), show="headings")
        self.forecasts_tree.heading("Variable", text="Variable")
        self.forecasts_tree.heading("Value", text="Value")
        self.forecasts_tree.pack(expand=True, fill="both")
        
        # Add a scrollbar for the treeview
        tree_scrollbar = ttk.Scrollbar(self.forecasts_tree, orient="vertical", command=self.forecasts_tree.yview)
        self.forecasts_tree.configure(yscrollcommand=tree_scrollbar.set)
        tree_scrollbar.pack(side="right", fill="y")
        
        # Create a frame for the chart on the right
        chart_frame = ttk.Frame(content_frame)
        chart_frame.pack(side="right", expand=True, fill="both", padx=(5, 0))
        
        # Add a label
        ttk.Label(chart_frame, text="Forecast Visualization").pack(pady=(0, 5))
        
        # Create a frame for the matplotlib chart
        self.forecast_chart_frame = ttk.Frame(chart_frame)
        self.forecast_chart_frame.pack(expand=True, fill="both")

    def fetch_forecasts(self):
        """Fetches the latest forecasts and updates the UI."""
        self.forecasts_status_label.config(text="Fetching forecasts...")
        self.forecasts_tree.delete(*self.forecasts_tree.get_children())  # Clear existing data

        data = self.make_request('GET', '/forecasts/latest/all')

        if data:
            self.forecasts_status_label.config(text="Forecasts loaded successfully.")
            # Populate table
            for variable, value in data.items():
                self.forecasts_tree.insert("", "end", values=(variable, value))
            
            # Enable the submit button
            self.submit_forecast_button.config(state="normal")
            
            # Store the current forecast data for submission
            self.current_forecast_data = data
            
            # Generate visualization
            self._visualize_forecast(data)
        else:
            self.forecasts_status_label.config(text="Failed to fetch forecasts.")
            self.submit_forecast_button.config(state="disabled")  # Disable the submit button

    def _visualize_forecast(self, forecast_data):
        """Creates a rich visualization of the forecast data using matplotlib."""
        # Clear any existing plot
        for widget in self.forecast_chart_frame.winfo_children():
            widget.destroy()
            
        if not forecast_data or not isinstance(forecast_data, dict):
            return
        
        # Extract variable names and their time series data
        variables = {}
        for var_name, var_data in forecast_data.items():
            # Skip non-dict entries which might be metadata
            if not isinstance(var_data, dict):
                continue
                
            # Extract historical and forecasted values
            if 'historical' in var_data and 'forecasted' in var_data:
                variables[var_name] = {
                    'historical': var_data.get('historical', []),
                    'forecasted': var_data.get('forecasted', []),
                    'dates': var_data.get('dates', 
                        list(range(len(var_data.get('historical', [])) + len(var_data.get('forecasted', [])))))
                }
        
        if not variables:
            # No suitable data to plot
            return
        
        # Create a new figure with multiple subplots
        fig = Figure(figsize=(8, 6), dpi=100)
        
        # Plot each variable in its own subplot
        num_vars = len(variables)
        rows = max(1, (num_vars + 1) // 2)  # Determine grid layout
        cols = min(2, num_vars)
        
        # Create subplots for each variable
        var_index = 1
        for var_name, var_data in variables.items():
            ax = fig.add_subplot(rows, cols, var_index)
            
            # Extract data
            historical = var_data['historical']
            forecasted = var_data['forecasted']
            dates = var_data['dates']
            
            # Determine plot points
            x_hist = dates[:len(historical)] if dates else list(range(len(historical)))
            x_forecast = dates[len(historical):] if dates else list(range(len(historical), len(historical) + len(forecasted)))
            
            # Plot historical data
            ax.plot(x_hist, historical, 'b-', label='Historical', marker='o', markersize=4)
            
            # Plot forecasted data
            ax.plot(x_forecast, forecasted, 'r--', label='Forecast', marker='x', markersize=4)
            
            # Add confidence intervals (if available)
            if 'confidence_lower' in var_data and 'confidence_upper' in var_data:
                lower = var_data['confidence_lower']
                upper = var_data['confidence_upper']
                ax.fill_between(x_forecast, lower, upper, color='red', alpha=0.2, label='Confidence Interval')
            else:
                # Generate simple error bands based on forecast volatility
                if len(forecasted) > 1:
                    volatility = sum([abs(forecasted[i] - forecasted[i-1]) for i in range(1, len(forecasted))]) / (len(forecasted) - 1)
                    upper = [f + volatility for f in forecasted]
                    lower = [f - volatility for f in forecasted]
                    ax.fill_between(x_forecast, lower, upper, color='red', alpha=0.2, label='Uncertainty Range')
            
            # Customize the plot
            ax.set_title(var_name)
            ax.set_xlabel('Time')
            ax.set_ylabel('Value')
            ax.legend(loc='best')
            ax.grid(True, linestyle='--', alpha=0.7)
            
            # Add a vertical line to separate historical from forecasted data
            if x_hist and x_forecast:
                split_point = x_hist[-1] + (x_forecast[0] - x_hist[-1])/2 if len(x_hist) > 0 and len(x_forecast) > 0 else len(historical)
                ax.axvline(x=split_point, color='gray', linestyle='--', alpha=0.8)
                ax.text(split_point, ax.get_ylim()[0], "Forecast Start", rotation=90, va='bottom', ha='right', alpha=0.7)
            
            # Rotate x-axis labels if they're dates
            if any(isinstance(x, str) for x in dates):
                plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
                
            var_index += 1
        
        # Add scenario comparison if we have space (and multiple scenarios)
        if 'scenarios' in forecast_data and var_index <= rows * cols:
            ax_scenarios = fig.add_subplot(rows, cols, var_index)
            
            # Plot all scenarios for the first variable
            if variables and forecast_data.get('scenarios'):
                first_var = list(variables.keys())[0]
                scenarios = forecast_data['scenarios']
                
                x_forecast = dates[len(historical):] if dates and 'historical' in var_data else list(range(len(forecasted)))
                
                # Plot each scenario
                for scenario_name, scenario_data in scenarios.items():
                    if first_var in scenario_data and 'values' in scenario_data[first_var]:
                        scenario_values = scenario_data[first_var]['values']
                        ax_scenarios.plot(x_forecast, scenario_values, '--', label=scenario_name, alpha=0.7)
                
                ax_scenarios.set_title(f'Scenario Comparison: {first_var}')
                ax_scenarios.set_xlabel('Time')
                ax_scenarios.set_ylabel('Value')
                ax_scenarios.legend(loc='best')
                ax_scenarios.grid(True, linestyle='--', alpha=0.7)
        
        fig.tight_layout()
        
        # Create canvas with toolbar for interactive features
        from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk
        
        canvas_frame = ttk.Frame(self.forecast_chart_frame)
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        canvas = FigureCanvasTkAgg(fig, master=canvas_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Add the matplotlib toolbar for interactive features (zoom, pan, save)
        toolbar_frame = ttk.Frame(self.forecast_chart_frame)
        toolbar_frame.pack(fill=tk.X)
        toolbar = NavigationToolbar2Tk(canvas, toolbar_frame)
        toolbar.update()

    def submit_forecasts_for_review(self):
        """Submits the current forecast data for training review."""
        if not hasattr(self, 'current_forecast_data') or not self.current_forecast_data:
            messagebox.showerror("Submission Error", "No forecast data available to submit.")
            return
            
        self.forecasts_status_label.config(text="Submitting forecasts for training review...", foreground="blue")
        
        # Prepare submission data
        submission_data = {
            "forecast_data": self.current_forecast_data,
            "timestamp": self._get_current_timestamp(),
            "metadata": {
                "submitted_by": "UI",
                "submission_type": "manual_review",
                "notes": "Submitted from Pulse Desktop UI for training review"
            }
        }
        
        # Optional notes from user
        notes = simpledialog.askstring("Training Review Notes", 
                                     "Add any notes about this forecast submission (optional):")
        if notes:
            submission_data["metadata"]["notes"] = notes
        
        # Submit the request
        response = self.make_request('POST', '/forecasts/submit_review', data=submission_data)
        
        if response and response.get('status') == 'success':
            self.forecasts_status_label.config(
                text=f"Forecasts submitted for training review! Submission ID: {response.get('submission_id', 'unknown')}",
                foreground="green"
            )
            self.log_activity("Submitted forecasts for training review")
            messagebox.showinfo("Submission Complete", 
                              f"Forecasts have been submitted for training review.\nSubmission ID: {response.get('submission_id', 'unknown')}")
        else:
            error_msg = response.get('error', 'Unknown error') if response else "Failed to submit"
            self.forecasts_status_label.config(
                text=f"Failed to submit forecasts: {error_msg}",
                foreground="red"
            )
            messagebox.showerror("Submission Error", f"Failed to submit forecasts: {error_msg}")

    def _get_current_timestamp(self):
        """Returns the current timestamp in ISO format."""
        from datetime import datetime
        return datetime.now().isoformat()

    def _init_retrodiction_tab(self):
        """Initializes the Retrodiction tab."""
        ttk.Label(self.retrodiction_frame, text="Retrodiction Simulation", style="Header.TLabel").pack(pady=10)

        # Input fields
        input_frame = ttk.Frame(self.retrodiction_frame)
        input_frame.pack(pady=5, fill="x", padx=10)

        ttk.Label(input_frame, text="Start Date (YYYY-MM-DD):").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.start_date_entry = ttk.Entry(input_frame, width=20)
        self.start_date_entry.grid(row=0, column=1, padx=5, pady=2, sticky="ew")

        ttk.Label(input_frame, text="Days:").grid(row=1, column=0, padx=5, pady=2, sticky="w")
        self.days_entry = ttk.Entry(input_frame, width=20)
        self.days_entry.grid(row=1, column=1, padx=5, pady=2, sticky="ew")

        ttk.Label(input_frame, text="Variables of Interest (comma-separated):").grid(row=2, column=0, padx=5, pady=2, sticky="w")
        self.variables_of_interest_entry = ttk.Entry(input_frame, width=40)
        self.variables_of_interest_entry.grid(row=2, column=1, padx=5, pady=2, sticky="ew")

        # Control buttons frame
        control_frame = ttk.Frame(self.retrodiction_frame)
        control_frame.pack(pady=10, fill="x", padx=10)
        
        # Run Button
        self.run_retrodiction_button = ttk.Button(control_frame, text="Run Retrodiction Simulation", 
                                             command=self._run_retrodiction_simulation)
        self.run_retrodiction_button.pack(side="left", padx=5)
        
        # Add button to submit retrodiction for training review
        self.submit_retrodiction_button = ttk.Button(control_frame, text="Submit for Training Review", 
                                            command=self.submit_retrodiction_for_review)
        self.submit_retrodiction_button.pack(side="left", padx=5)
        self.submit_retrodiction_button.config(state="disabled")  # Initially disabled

        # Status Label
        self.retrodiction_status_label = ttk.Label(self.retrodiction_frame, text="")
        self.retrodiction_status_label.pack(pady=5, padx=10, fill="x")

        # Create a frame for results (table and visualization)
        results_frame = ttk.Frame(self.retrodiction_frame)
        results_frame.pack(expand=True, fill="both", padx=10, pady=5)
        
        # Split into left and right panes
        left_frame = ttk.Frame(results_frame)
        left_frame.pack(side="left", expand=True, fill="both", padx=(0, 5))
        
        right_frame = ttk.Frame(results_frame)
        right_frame.pack(side="right", expand=True, fill="both", padx=(5, 0))
        
        # Text results on the left
        ttk.Label(left_frame, text="Raw Results:").pack(anchor="w")
        self.retrodiction_results_text = tk.Text(left_frame, height=10, width=40)
        self.retrodiction_results_text.pack(expand=True, fill="both")
        
        # Add scrollbar to text widget
        text_scrollbar = ttk.Scrollbar(self.retrodiction_results_text, orient="vertical", command=self.retrodiction_results_text.yview)
        self.retrodiction_results_text.configure(yscrollcommand=text_scrollbar.set)
        text_scrollbar.pack(side="right", fill="y")
        
        # Visualization on the right
        ttk.Label(right_frame, text="Visualization:").pack(anchor="w")
        self.retrodiction_chart_frame = ttk.Frame(right_frame)
        self.retrodiction_chart_frame.pack(expand=True, fill="both")

    def _run_retrodiction_simulation(self):
        """Runs a retrodiction simulation with the entered parameters."""
        # Get input values
        start_date = self.start_date_entry.get().strip()
        days_str = self.days_entry.get().strip()
        variables = self.variables_of_interest_entry.get().strip()
        
        # Validate inputs
        if not start_date:
            messagebox.showerror("Input Error", "Please enter a start date.")
            return
            
        try:
            days = int(days_str) if days_str else 7  # Default to 7 days
        except ValueError:
            messagebox.showerror("Input Error", "Days must be a valid number.")
            return
            
        # Prepare variables list
        variable_list = [v.strip() for v in variables.split(',') if v.strip()] if variables else []
        
        # Update status
        self.retrodiction_status_label.config(text="Running retrodiction simulation...", foreground="blue")
        self.run_retrodiction_button.config(state="disabled")  # Disable button during processing
        
        # Clear previous results
        self.retrodiction_results_text.delete("1.0", tk.END)
        for widget in self.retrodiction_chart_frame.winfo_children():
            widget.destroy()
            
        # Prepare simulation parameters
        simulation_params = {
            "start_date": start_date,
            "days": days,
            "variables": variable_list
        }
        
        # Run simulation as a background thread to keep UI responsive
        threading.Thread(target=self._run_retrodiction_background, args=(simulation_params,), daemon=True).start()
        
    def _run_retrodiction_background(self, params):
        """Runs the retrodiction simulation in a background thread."""
        try:
            # Make API request to run retrodiction
            response = self.make_request('POST', '/retrodiction/run', data=params)
            
            # Use after() to update UI from the main thread
            if response and response.get('status') == 'success':
                self.root.after(0, self._handle_retrodiction_success, response)
            else:
                error_msg = response.get('error', 'Unknown error') if response else "Failed to run retrodiction"
                self.root.after(0, self._handle_retrodiction_error, error_msg)
        except Exception as e:
            self.root.after(0, self._handle_retrodiction_error, str(e))
    
    def _handle_retrodiction_success(self, response):
        """Handles successful retrodiction simulation."""
        # Update status
        self.retrodiction_status_label.config(text="Retrodiction completed successfully.", foreground="green")
        self.run_retrodiction_button.config(state="normal")  # Re-enable button
        
        # Enable the submit button
        self.submit_retrodiction_button.config(state="normal")
        
        # Store the results for submission
        self.current_retrodiction_results = response.get('results', {})
        
        # Display raw results
        formatted_results = json.dumps(self.current_retrodiction_results, indent=2)
        self.retrodiction_results_text.insert("1.0", formatted_results)
        
        # Create visualization
        self._visualize_retrodiction(self.current_retrodiction_results)
        
        # Log activity
        self.log_activity("Completed retrodiction simulation")
    
    def _handle_retrodiction_error(self, error_message):
        """Handles retrodiction simulation error."""
        self.retrodiction_status_label.config(text=f"Error: {error_message}", foreground="red")
        self.run_retrodiction_button.config(state="normal")  # Re-enable button
        self.submit_retrodiction_button.config(state="disabled")  # Disable submit button
        self.log_activity(f"Retrodiction failed: {error_message}")
    
    def _visualize_retrodiction(self, retrodiction_data):
        """Creates a visualization of the retrodiction results."""
        # Clear any existing plot
        for widget in self.retrodiction_chart_frame.winfo_children():
            widget.destroy()
            
        if not retrodiction_data or not isinstance(retrodiction_data, dict):
            return
            
        # Get variables with historical and retrodicted values
        variables = {}
        for var_name, var_data in retrodiction_data.items():
            if not isinstance(var_data, dict):
                continue
                
            if 'historical' in var_data and 'retrodicted' in var_data:
                variables[var_name] = {
                    'historical': var_data.get('historical', []),
                    'retrodicted': var_data.get('retrodicted', []),
                    'dates': var_data.get('dates', [])
                }
        
        if not variables:
            return
            
        # Create figure and plot
        fig = Figure(figsize=(8, 6), dpi=100)
        
        # Determine grid layout based on number of variables
        num_vars = len(variables)
        rows = max(1, (num_vars + 1) // 2)
        cols = min(2, num_vars)
        
        var_index = 1
        for var_name, var_data in variables.items():
            ax = fig.add_subplot(rows, cols, var_index)
            
            historical = var_data['historical']
            retrodicted = var_data['retrodicted']
            dates = var_data['dates'] if var_data['dates'] else list(range(len(historical) + len(retrodicted)))
            
            # Plot historical data
            x_hist = dates[:len(historical)] if dates else list(range(len(historical)))
            ax.plot(x_hist, historical, 'b-', label='Actual', marker='o', markersize=4)
            
            # Plot retrodicted data
            x_retro = dates[len(historical):] if dates else list(range(len(historical), len(historical) + len(retrodicted)))
            ax.plot(x_retro, retrodicted, 'g--', label='Retrodicted', marker='x', markersize=4)
            
            # Add a vertical line to separate historical from retrodicted
            if x_hist and x_retro:
                split_point = x_hist[-1]
                ax.axvline(x=split_point, color='gray', linestyle='--', alpha=0.8)
                ax.text(split_point, ax.get_ylim()[0], "Retrodiction Start", rotation=90, va='bottom', ha='right', alpha=0.7)
            
            # Customize the plot
            ax.set_title(var_name)
            ax.set_xlabel('Time')
            ax.set_ylabel('Value')
            ax.legend(loc='best')
            ax.grid(True, linestyle='--', alpha=0.7)
            
            # Rotate x-axis labels if they're dates
            if any(isinstance(x, str) for x in dates):
                plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
                
            var_index += 1
        
        fig.tight_layout()
        
        # Create canvas with toolbar
        from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk
        
        canvas_frame = ttk.Frame(self.retrodiction_chart_frame)
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        canvas = FigureCanvasTkAgg(fig, master=canvas_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Add toolbar
        toolbar_frame = ttk.Frame(self.retrodiction_chart_frame)
        toolbar_frame.pack(fill=tk.X)
        toolbar = NavigationToolbar2Tk(canvas, toolbar_frame)
        toolbar.update()
    
    def submit_retrodiction_for_review(self):
        """Submits the current retrodiction results for training review."""
        if not hasattr(self, 'current_retrodiction_results') or not self.current_retrodiction_results:
            messagebox.showerror("Submission Error", "No retrodiction results available to submit.")
            return
            
        self.retrodiction_status_label.config(text="Submitting retrodiction for training review...", foreground="blue")
        
        # Prepare submission data
        submission_data = {
            "retrodiction_results": self.current_retrodiction_results,
            "timestamp": self._get_current_timestamp(),
            "metadata": {
                "submitted_by": "UI",
                "submission_type": "manual_review",
                "notes": "Submitted from Pulse Desktop UI for training review"
            }
        }
        
        # Optional notes from user
        notes = simpledialog.askstring("Training Review Notes", 
                                     "Add any notes about this retrodiction submission (optional):")
        if notes:
            submission_data["metadata"]["notes"] = notes
            
        # Submit the request
        response = self.make_request('POST', '/retrodiction/submit_review', data=submission_data)
        
        if response and response.get('status') == 'success':
            self.retrodiction_status_label.config(
                text=f"Retrodiction submitted for training review! Submission ID: {response.get('submission_id', 'unknown')}",
                foreground="green"
            )
            self.log_activity("Submitted retrodiction for training review")
            messagebox.showinfo("Submission Complete",
                             f"Retrodiction has been submitted for training review.\nSubmission ID: {response.get('submission_id', 'unknown')}")
        else:
            error_msg = response.get('error', 'Unknown error') if response else "Failed to submit"
            self.retrodiction_status_label.config(
                text=f"Failed to submit retrodiction: {error_msg}",
                foreground="red"
            )
            messagebox.showerror("Submission Error", f"Failed to submit retrodiction: {error_msg}")

    def _init_autopilot_tab(self):
        """Initializes the Autopilot tab."""
        # Header
        ttk.Label(self.autopilot_frame, text="Pulse Autopilot Control", style="Header.TLabel").pack(pady=(10, 20))
        
        # Control panel
        control_panel = ttk.LabelFrame(self.autopilot_frame, text="Autopilot Control Panel", padding=10)
        control_panel.pack(padx=10, pady=10, fill="x")
        
        # Status indicator
        status_frame = ttk.Frame(control_panel)
        status_frame.pack(fill="x", pady=5)
        
        ttk.Label(status_frame, text="Status:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.autopilot_status_label = ttk.Label(status_frame, text="Unknown", foreground="gray")
        self.autopilot_status_label.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        # Add buttons for autopilot control
        button_frame = ttk.Frame(control_panel)
        button_frame.pack(fill="x", pady=10)
        
        self.start_button = ttk.Button(button_frame, text="Start Autopilot", command=self.start_autopilot)
        self.start_button.grid(row=0, column=0, padx=5, pady=5)
        
        self.stop_button = ttk.Button(button_frame, text="Stop Autopilot", command=self.stop_autopilot)
        self.stop_button.grid(row=0, column=1, padx=5, pady=5)
        self.stop_button.config(state="disabled")  # Initially disabled
        
        self.check_status_button = ttk.Button(button_frame, text="Check Status", command=self.check_autopilot_status)
        self.check_status_button.grid(row=0, column=2, padx=5, pady=5)
        
        # Configuration section
        config_frame = ttk.LabelFrame(self.autopilot_frame, text="Autopilot Configuration", padding=10)
        config_frame.pack(padx=10, pady=10, fill="x")
        
        # Run mode selection
        mode_frame = ttk.Frame(config_frame)
        mode_frame.pack(fill="x", pady=5)
        
        ttk.Label(mode_frame, text="Run Mode:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.run_mode = tk.StringVar(value="standard")
        mode_combo = ttk.Combobox(mode_frame, textvariable=self.run_mode, 
                                  values=["standard", "aggressive", "conservative", "learning"])
        mode_combo.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        mode_combo.config(state="readonly")
        
        # Interval setting
        interval_frame = ttk.Frame(config_frame)
        interval_frame.pack(fill="x", pady=5)
        
        ttk.Label(interval_frame, text="Check Interval (seconds):").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.check_interval = tk.StringVar(value="300")
        interval_entry = ttk.Entry(interval_frame, textvariable=self.check_interval, width=10)
        interval_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        # Advanced options
        advanced_frame = ttk.LabelFrame(config_frame, text="Advanced Options", padding=10)
        advanced_frame.pack(fill="x", pady=10, expand=True)
        
        # Checkboxes for options
        self.enable_learning = tk.BooleanVar(value=True)
        ttk.Checkbutton(advanced_frame, text="Enable Learning", variable=self.enable_learning).pack(anchor="w", pady=2)
        
        self.enable_alerts = tk.BooleanVar(value=True)
        ttk.Checkbutton(advanced_frame, text="Enable Alerts", variable=self.enable_alerts).pack(anchor="w", pady=2)
        
        self.aggressive_mode = tk.BooleanVar(value=False)
        ttk.Checkbutton(advanced_frame, text="Aggressive Intervention", variable=self.aggressive_mode).pack(anchor="w", pady=2)
        
        # Save config button
        save_button = ttk.Button(config_frame, text="Save Configuration", command=self.save_autopilot_config)
        save_button.pack(pady=10)
        
        # Log section
        log_frame = ttk.LabelFrame(self.autopilot_frame, text="Autopilot Activity Log", padding=10)
        log_frame.pack(padx=10, pady=10, fill="both", expand=True)
        
        # Create a scrolled text for the log
        self.autopilot_log = scrolledtext.ScrolledText(log_frame)
        self.autopilot_log.pack(fill="both", expand=True)
        self.autopilot_log.config(state="disabled")  # Make read-only initially
        
        # Check status once on tab initialization
        self.root.after(1000, self.check_autopilot_status)

    def start_autopilot(self):
        """Starts the autopilot system."""
        # Get configuration
        run_mode = self.run_mode.get()
        interval = self.check_interval.get()
        
        try:
            interval = int(interval)
            if interval < 10:
                messagebox.showwarning("Invalid Interval", "Interval must be at least 10 seconds.")
                return
        except ValueError:
            messagebox.showwarning("Invalid Interval", "Interval must be a valid number.")
            return
        
        # Prepare configuration
        config = {
            "mode": run_mode,
            "check_interval": interval,
            "enable_learning": self.enable_learning.get(),
            "enable_alerts": self.enable_alerts.get(),
            "aggressive_intervention": self.aggressive_mode.get()
        }
        
        # Send start request
        response = self.make_request('POST', '/autopilot/start', data=config)
        
        if response and response.get('status') == 'started':
            self.autopilot_status_label.config(text="Running", foreground="green")
            self.start_button.config(state="disabled")
            self.stop_button.config(state="normal")
            self._update_autopilot_log("Autopilot started in " + run_mode + " mode")
            messagebox.showinfo("Autopilot Started", "Autopilot has been started successfully.")
        else:
            error_msg = response.get('error', 'Unknown error') if response else "Failed to start"
            self._update_autopilot_log("Failed to start: " + error_msg)
            messagebox.showerror("Start Error", f"Failed to start autopilot: {error_msg}")
    
    def stop_autopilot(self):
        """Stops the autopilot system."""
        response = self.make_request('POST', '/autopilot/stop')
        
        if response and response.get('status') == 'stopped':
            self.autopilot_status_label.config(text="Stopped", foreground="gray")
            self.start_button.config(state="normal")
            self.stop_button.config(state="disabled")
            self._update_autopilot_log("Autopilot stopped")
            messagebox.showinfo("Autopilot Stopped", "Autopilot has been stopped successfully.")
        else:
            error_msg = response.get('error', 'Unknown error') if response else "Failed to stop"
            self._update_autopilot_log("Failed to stop: " + error_msg)
            messagebox.showerror("Stop Error", f"Failed to stop autopilot: {error_msg}")
    
    def check_autopilot_status(self):
        """Checks the current status of the autopilot system."""
        response = self.make_request('GET', '/autopilot/status')
        
        if response and 'status' in response:
            status = response['status']
            if status == 'running':
                self.autopilot_status_label.config(text="Running", foreground="green")
                self.start_button.config(state="disabled")
                self.stop_button.config(state="normal")
                
                # Get additional info
                if 'mode' in response:
                    self.run_mode.set(response['mode'])
                if 'last_action' in response:
                    self._update_autopilot_log("Last action: " + response['last_action'])
            else:
                self.autopilot_status_label.config(text="Stopped", foreground="gray")
                self.start_button.config(state="normal")
                self.stop_button.config(state="disabled")
        else:
            self.autopilot_status_label.config(text="Unknown", foreground="orange")
    
    def save_autopilot_config(self):
        """Saves the autopilot configuration."""
        # Validate settings
        try:
            interval = int(self.check_interval.get())
            if interval < 10:
                messagebox.showwarning("Invalid Interval", "Interval must be at least 10 seconds.")
                return
        except ValueError:
            messagebox.showwarning("Invalid Interval", "Interval must be a valid number.")
            return
            
        # Prepare configuration
        config = {
            "mode": self.run_mode.get(),
            "check_interval": interval,
            "enable_learning": self.enable_learning.get(),
            "enable_alerts": self.enable_alerts.get(),
            "aggressive_intervention": self.aggressive_mode.get()
        }
        
        # Send config update request
        response = self.make_request('POST', '/autopilot/configure', data=config)
        
        if response and response.get('status') == 'configured':
            self._update_autopilot_log("Configuration saved successfully")
            messagebox.showinfo("Configuration Saved", "Autopilot configuration has been saved.")
        else:
            error_msg = response.get('error', 'Unknown error') if response else "Failed to save configuration"
            self._update_autopilot_log("Failed to save configuration: " + error_msg)
            messagebox.showerror("Configuration Error", f"Failed to save configuration: {error_msg}")
    
    def _update_autopilot_log(self, message):
        """Updates the autopilot log with a message."""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Enable editing temporarily
        self.autopilot_log.config(state="normal")
        
        # Insert at the beginning
        self.autopilot_log.insert("1.0", f"[{timestamp}] {message}\n")
        
        # Make read-only again
        self.autopilot_log.config(state="disabled")

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

            response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
            return response.json()

        except requests.exceptions.RequestException as e:
            print(f"Error making request to {url}: {e}")
            return None

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
            self._stop_autopilot_status_polling()  # Stop polling when switching away

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
        self.audit_report_text.delete("1.0", tk.END)  # Clear previous report

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
            self.fetch_autopilot_history()  # Refresh history after starting
        else:
            error_message = data.get('error', 'Failed to start autopilot.') if data else 'Failed to start autopilot.'
            self.autopilot_status_label.config(text=f"Autopilot Status: Error - {error_message}")
        self._start_autopilot_status_polling()  # Ensure polling is active

    def stop_autopilot(self):
        """Stops the autopilot."""
        self.autopilot_status_label.config(text="Stopping Autopilot...")
        data = self.make_request('POST', '/autopilot/stop')
        if data and data.get('status') == 'success':
            self.autopilot_status_label.config(text="Autopilot Status: Stopped")
            self.fetch_autopilot_history()  # Refresh history after stopping
        else:
            error_message = data.get('error', 'Failed to stop autopilot.') if data else 'Failed to stop autopilot.'
            self.autopilot_status_label.config(text=f"Autopilot Status: Error - {error_message}")
        self._stop_autopilot_status_polling()  # Stop polling when stopped

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
        self.autopilot_history_tree.delete(*self.autopilot_history_tree.get_children())  # Clear existing data
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
            print(f"Error fetching autopilot history: {error_message}")

    def _start_autopilot_status_polling(self):
        """Starts periodic polling for autopilot status."""
        self._stop_autopilot_status_polling()  # Stop any existing polling first
        self.fetch_autopilot_status()  # Fetch immediately
        self.autopilot_status_polling_job = self.root.after(5000, self._start_autopilot_status_polling)

    def _stop_autopilot_status_polling(self):
        """Stops periodic polling for autopilot status."""
        if self.autopilot_status_polling_job:
            self.root.after_cancel(self.autopilot_status_polling_job)
            self.autopilot_status_polling_job = None

    def _init_learning_tab(self):
        """Initializes the Learning & Training tab."""
        # Header
        ttk.Label(self.learning_frame, text="Learning & Training Review", style="Header.TLabel").pack(pady=(10, 20))
        
        # Training Audit Controls Panel
        audit_frame = ttk.LabelFrame(self.learning_frame, text="Training Audit Controls", padding=10)
        audit_frame.pack(padx=10, pady=10, fill="x")
        
        # Batch IDs for comparison
        batch_frame = ttk.Frame(audit_frame)
        batch_frame.pack(fill="x", pady=5)
        
        ttk.Label(batch_frame, text="Previous Batch ID:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.previous_batch_id_entry = ttk.Entry(batch_frame, width=30)
        self.previous_batch_id_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        ttk.Label(batch_frame, text="Current Batch ID:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.current_batch_id_entry = ttk.Entry(batch_frame, width=30)
        self.current_batch_id_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        
        # Trigger audit button
        audit_button = ttk.Button(audit_frame, text="Trigger AI Training Audit", 
                                command=self.trigger_ai_training_audit)
        audit_button.pack(pady=10)
        
        # Status label
        self.ai_review_status_label = ttk.Label(audit_frame, text="")
        self.ai_review_status_label.pack(pady=5, fill="x")
        
        # Audit Report Display
        report_frame = ttk.LabelFrame(self.learning_frame, text="Audit Report", padding=10)
        report_frame.pack(padx=10, pady=10, fill="both", expand=True)
        
        # Add a text area for the audit report
        self.audit_report_text = scrolledtext.ScrolledText(report_frame, height=10)
        self.audit_report_text.pack(fill="both", expand=True)
        
        # Learning Log Summary Section
        log_frame = ttk.LabelFrame(self.learning_frame, text="Learning Log Summary", padding=10)
        log_frame.pack(padx=10, pady=10, fill="x")
        
        # Add a button to load learning events
        load_log_button = ttk.Button(log_frame, text="Load Learning Events", 
                                   command=self.load_learning_events)
        load_log_button.pack(pady=5)
        
        # Learning log summary text area
        self.learning_log_summary = scrolledtext.ScrolledText(log_frame, height=6)
        self.learning_log_summary.pack(fill="both", expand=True)
        
    def load_learning_events(self):
        """Loads and displays learning events from the learning log."""
        try:
            # Import the needed function if available
            if self.has_pulse_modules and 'learning.recursion_audit' in sys.modules:
                from operator_interface.learning_log_viewer import load_learning_events, summarize_learning_events
                
                # Load the events
                events = load_learning_events(limit=20)  # Limit to the most recent 20 events
                
                if events:
                    # Summarize them
                    summary = summarize_learning_events(events)
                    
                    # Build a formatted display
                    summary_text = "Learning Event Summary:\n\n"
                    for event_type, count in summary.items():
                        summary_text += f"- {event_type}: {count} events\n"
                    
                    summary_text += "\n\nRecent Events:\n"
                    for event in events[:5]:  # Show the 5 most recent events
                        timestamp = event.get("timestamp", "Unknown time")
                        event_type = event.get("event_type", "Unknown event")
                        summary_text += f"\n[{timestamp}] {event_type}\n"
                        
                        # Show some details for certain event types
                        if "data" in event:
                            if event_type == "variable_weight_change" and "variable" in event["data"]:
                                var = event["data"].get("variable", "")
                                old = event["data"].get("old_weight", "")
                                new = event["data"].get("new_weight", "")
                                summary_text += f"  Variable: {var}, Weight: {old} → {new}\n"
                            elif event_type == "symbolic_upgrade" and "plan" in event["data"]:
                                plan = event["data"].get("plan", {})
                                summary_text += f"  Plan: {str(plan)}\n"
                    
                    # Update the text area
                    self.learning_log_summary.delete("1.0", tk.END)
                    self.learning_log_summary.insert(tk.END, summary_text)
                else:
                    self.learning_log_summary.delete("1.0", tk.END)
                    self.learning_log_summary.insert(tk.END, "No learning events found in the log.")
            else:
                self.learning_log_summary.delete("1.0", tk.END)
                self.learning_log_summary.insert(tk.END, "Learning log viewer module is not available.")
        except Exception as e:
            self.learning_log_summary.delete("1.0", tk.END)
            self.learning_log_summary.insert(tk.END, f"Error loading learning events: {str(e)}")

    def _init_analysis_tab(self):
        """Initializes the Analysis tab with tools for data analysis and visualization."""
        # Header
        ttk.Label(self.analysis_frame, text="Data Analysis Tools", style="Header.TLabel").pack(pady=(10, 20))
        
        # Create a notebook for different analysis tools
        analysis_notebook = ttk.Notebook(self.analysis_frame)
        analysis_notebook.pack(fill="both", expand=True, padx=5, pady=5)
        
        # --- Variable Trace Analysis ---
        var_trace_frame = ttk.Frame(analysis_notebook, padding=10)
        analysis_notebook.add(var_trace_frame, text="Variable Trace")
        
        # Variable selection
        var_select_frame = ttk.Frame(var_trace_frame)
        var_select_frame.pack(fill="x", pady=5)
        
        ttk.Label(var_select_frame, text="Variable:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.var_combo = ttk.Combobox(var_select_frame, width=30)
        self.var_combo.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        # Add data range options
        ttk.Label(var_select_frame, text="Time Range:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.time_range_combo = ttk.Combobox(var_select_frame, width=30, 
                                            values=["Last 24 Hours", "Last 7 Days", "Last 30 Days", "All Time"])
        self.time_range_combo.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        self.time_range_combo.current(0)  # Set default
        
        # Load button
        load_button = ttk.Button(var_select_frame, text="Load Variable Data", 
                                command=self.load_variable_trace)
        load_button.grid(row=2, column=1, padx=5, pady=5, sticky="e")
        
        # Plot frame
        self.var_trace_plot_frame = ttk.Frame(var_trace_frame)
        self.var_trace_plot_frame.pack(fill="both", expand=True, pady=10)
        
        # --- Recursion Analysis ---
        recursion_frame = ttk.Frame(analysis_notebook, padding=10)
        analysis_notebook.add(recursion_frame, text="Recursion Audit")
        
        # Previous batch ID
        prev_batch_frame = ttk.Frame(recursion_frame)
        prev_batch_frame.pack(fill="x", pady=5)
        
        ttk.Label(prev_batch_frame, text="Previous Batch ID:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.previous_batch_id_entry = ttk.Entry(prev_batch_frame, width=30)
        self.previous_batch_id_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        # Current batch ID
        curr_batch_frame = ttk.Frame(recursion_frame)
        curr_batch_frame.pack(fill="x", pady=5)
        
        ttk.Label(curr_batch_frame, text="Current Batch ID:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.current_batch_id_entry = ttk.Entry(curr_batch_frame, width=30)
        self.current_batch_id_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        # Run audit button
        audit_button = ttk.Button(recursion_frame, text="Run Recursion Audit", 
                                 command=self.trigger_ai_training_audit)
        audit_button.pack(pady=10)
        
        # Status label
        self.ai_review_status_label = ttk.Label(recursion_frame, text="")
        self.ai_review_status_label.pack(pady=5)
        
        # Audit report text area
        report_frame = ttk.LabelFrame(recursion_frame, text="Audit Report")
        report_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.audit_report_text = scrolledtext.ScrolledText(report_frame, wrap=tk.WORD)
        self.audit_report_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        # --- Cluster Visualization ---
        cluster_frame = ttk.Frame(analysis_notebook, padding=10)
        analysis_notebook.add(cluster_frame, text="Cluster Analysis")
        
        # Cluster type selection
        cluster_type_frame = ttk.Frame(cluster_frame)
        cluster_type_frame.pack(fill="x", pady=5)
        
        ttk.Label(cluster_type_frame, text="Cluster Type:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.cluster_type_combo = ttk.Combobox(cluster_type_frame, width=30, 
                                             values=["Variable Clusters", "Rule Clusters", "Symbolic Overlays"])
        self.cluster_type_combo.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.cluster_type_combo.current(0)  # Set default
        
        # Visualization options
        viz_options_frame = ttk.Frame(cluster_frame)
        viz_options_frame.pack(fill="x", pady=5)
        
        ttk.Label(viz_options_frame, text="Chart Type:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.chart_type_combo = ttk.Combobox(viz_options_frame, width=30, 
                                           values=["Network Graph", "Heatmap", "Dendrogram"])
        self.chart_type_combo.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.chart_type_combo.current(0)  # Set default
        
        # Visualize button
        viz_button = ttk.Button(cluster_frame, text="Generate Visualization", 
                              command=self.generate_cluster_visualization)
        viz_button.pack(pady=10)
        
        # Visualization frame
        self.cluster_viz_frame = ttk.Frame(cluster_frame)
        self.cluster_viz_frame.pack(fill="both", expand=True, pady=10)
        
        # --- Learning Metrics ---
        learning_metrics_frame = ttk.Frame(analysis_notebook, padding=10)
        analysis_notebook.add(learning_metrics_frame, text="Learning Metrics")
        
        # Time period selection
        time_period_frame = ttk.Frame(learning_metrics_frame)
        time_period_frame.pack(fill="x", pady=5)
        
        ttk.Label(time_period_frame, text="Time Period:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.time_period_combo = ttk.Combobox(time_period_frame, width=30, 
                                            values=["Last 24 Hours", "Last 7 Days", "Last 30 Days", "All Time"])
        self.time_period_combo.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.time_period_combo.current(0)  # Set default
        
        # Metrics selection
        metrics_frame = ttk.Frame(learning_metrics_frame)
        metrics_frame.pack(fill="x", pady=5)
        
        ttk.Label(metrics_frame, text="Metrics:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        # Checkbuttons for different metrics
        self.accuracy_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(metrics_frame, text="Prediction Accuracy", 
                       variable=self.accuracy_var).grid(row=0, column=1, padx=5, pady=2, sticky="w")
        
        self.trust_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(metrics_frame, text="Trust Scores", 
                       variable=self.trust_var).grid(row=1, column=1, padx=5, pady=2, sticky="w")
        
        self.learning_events_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(metrics_frame, text="Learning Events", 
                       variable=self.learning_events_var).grid(row=2, column=1, padx=5, pady=2, sticky="w")
        
        # Generate report button
        report_button = ttk.Button(learning_metrics_frame, text="Generate Learning Report", 
                                  command=self.generate_learning_report)
        report_button.pack(pady=10)
        
        # Report display area
        report_display_frame = ttk.LabelFrame(learning_metrics_frame, text="Learning Report")
        report_display_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.learning_report_text = scrolledtext.ScrolledText(report_display_frame, wrap=tk.WORD)
        self.learning_report_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        # --- Export Section (at bottom of main frame) ---
        export_frame = ttk.Frame(self.analysis_frame)
        export_frame.pack(fill="x", pady=10, padx=10)
        
        ttk.Button(export_frame, text="Export Current Analysis", 
                  command=self.export_current_analysis).pack(side="left", padx=5)
        
        ttk.Button(export_frame, text="Export All Analyses", 
                  command=self.export_all_analyses).pack(side="left", padx=5)

    def generate_cluster_visualization(self):
        """Generates and displays cluster visualizations."""
        cluster_type = self.cluster_type_combo.get()
        chart_type = self.chart_type_combo.get()
        
        self.update_status(f"Generating {chart_type} visualization for {cluster_type}...")
        
        try:
            # Clear the visualization frame
            for widget in self.cluster_viz_frame.winfo_children():
                widget.destroy()
                
            if hasattr(self, 'has_pulse_modules') and self.has_pulse_modules:
                # Try to use real data if modules are available
                try:
                    if cluster_type == "Variable Clusters":
                        from memory.variable_cluster_engine import summarize_clusters
                        clusters = summarize_clusters()
                        self._visualize_clusters(clusters, chart_type)
                    elif cluster_type == "Rule Clusters":
                        # Import and visualize rule clusters
                        self.generate_dummy_cluster_visualization(chart_type)
                    else:
                        # Fallback for other types
                        self.generate_dummy_cluster_visualization(chart_type)
                except Exception as e:
                    self.update_status(f"Error getting cluster data: {str(e)}")
                    self.generate_dummy_cluster_visualization(chart_type)
            else:
                # Generate dummy visualization if modules aren't available
                self.generate_dummy_cluster_visualization(chart_type)
                self.update_status("Generated sample visualization (modules not available)")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate visualization: {str(e)}")
            self.update_status(f"Error generating visualization: {str(e)}")
            
    def _visualize_clusters(self, clusters, chart_type):
        """Visualizes real cluster data."""
        if not clusters:
            # Use dummy visualization if no real data
            self.generate_dummy_cluster_visualization(chart_type)
            return
            
        # Create figure
        fig = Figure(figsize=(8, 6), dpi=100)
        
        # Implementation would depend on the specific format of cluster data
        # This is a placeholder that would be implemented based on actual data
        ax = fig.add_subplot(111)
        ax.text(0.5, 0.5, "Real cluster data visualization would go here",
               ha='center', va='center', fontsize=12)
        
        # Create canvas
        canvas = FigureCanvasTkAgg(fig, master=self.cluster_viz_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Add toolbar
        from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk
        toolbar = NavigationToolbar2Tk(canvas, self.cluster_viz_frame)
        toolbar.update()
        
    def generate_dummy_cluster_visualization(self, chart_type="Network Graph"):
        """Generates a dummy cluster visualization for the UI."""
        # Clear the frame
        for widget in self.cluster_viz_frame.winfo_children():
            widget.destroy()
            
        # Create figure and axis
        fig = Figure(figsize=(8, 6), dpi=100)
        
        if chart_type == "Network Graph":
            # Create a simple network graph
            ax = fig.add_subplot(111)
            
            # Node positions
            pos = {
                'A': (0, 0), 'B': (1, 1), 'C': (2, 0), 'D': (0, 2),
                'E': (3, 1), 'F': (2, 2), 'G': (1, 3), 'H': (3, 3)
            }
            
            # Draw nodes
            for node, position in pos.items():
                ax.plot(position[0], position[1], 'o', markersize=15, 
                       color='skyblue', alpha=0.8)
                ax.text(position[0], position[1], node, fontsize=10, 
                       ha='center', va='center')
            
            # Draw edges
            edges = [('A', 'B'), ('A', 'C'), ('B', 'D'), ('C', 'E'), 
                    ('D', 'F'), ('E', 'F'), ('D', 'G'), ('F', 'H')]
            
            for edge in edges:
                ax.plot([pos[edge[0]][0], pos[edge[1]][0]], 
                       [pos[edge[0]][1], pos[edge[1]][1]], 'k-', alpha=0.4)
            
            ax.set_title("Sample Network Graph")
            ax.set_xlim(-1, 4)
            ax.set_ylim(-1, 4)
            ax.axis('off')
            
        elif chart_type == "Heatmap":
            # Create a heatmap
            ax = fig.add_subplot(111)
            
            # Generate dummy data
            import numpy as np
            data = np.random.rand(8, 8)
            for i in range(8):
                for j in range(8):
                    if i == j:
                        data[i, j] = 1  # Diagonal should be 1 (self-similarity)
                    else:
                        data[i, j] = data[j, i]  # Make it symmetric
            
            im = ax.imshow(data, cmap='viridis')
            
            # Add labels
            variables = ['var_A', 'var_B', 'var_C', 'var_D', 
                        'var_E', 'var_F', 'var_G', 'var_H']
            
            ax.set_xticks(np.arange(len(variables)))
            ax.set_yticks(np.arange(len(variables)))
            ax.set_xticklabels(variables)
            ax.set_yticklabels(variables)
            
            # Rotate x-axis labels
            import matplotlib.pyplot as plt
            plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")
            
            # Add colorbar
            cbar = fig.colorbar(im)
            cbar.set_label('Similarity')
            
            ax.set_title("Sample Heatmap")
            fig.tight_layout()
            
        elif chart_type == "Dendrogram":
            # Create a dendrogram
            ax = fig.add_subplot(111)
            
            # Generate dummy data
            import numpy as np
            try:
                from scipy.cluster import hierarchy
                
                # Random distance matrix
                np.random.seed(42)
                X = np.random.rand(8, 10)
                Z = hierarchy.linkage(X, 'ward')
                
                # Labels
                labels = ['var_A', 'var_B', 'var_C', 'var_D', 
                         'var_E', 'var_F', 'var_G', 'var_H']
                
                # Plot dendrogram
                hierarchy.dendrogram(Z, labels=labels, ax=ax, leaf_rotation=90)
                ax.set_title('Sample Dendrogram')
            except ImportError:
                ax.text(0.5, 0.5, "scipy not available to create dendrogram", 
                       ha='center', va='center')
                ax.set_title('Could not create dendrogram')
            
            fig.tight_layout()
        
        # Create canvas
        canvas = FigureCanvasTkAgg(fig, master=self.cluster_viz_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Add toolbar
        from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk
        toolbar = NavigationToolbar2Tk(canvas, self.cluster_viz_frame)
        toolbar.update()

    def _init_diagnostics_tab(self):
        """Initializes the Diagnostics tab with system health monitoring and debug tools."""
        # Header
        ttk.Label(self.diagnostics_frame, text="System Diagnostics", style="Header.TLabel").pack(pady=(10, 20))
        
        # System Health Monitoring
        health_frame = ttk.LabelFrame(self.diagnostics_frame, text="System Health", padding=10)
        health_frame.pack(padx=10, pady=10, fill="x")
        
        # Memory usage
        mem_frame = ttk.Frame(health_frame)
        mem_frame.pack(fill="x", pady=5)
        
        ttk.Label(mem_frame, text="Memory Usage:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.memory_usage_label = ttk.Label(mem_frame, text="Unknown")
        self.memory_usage_label.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        # Processing load
        cpu_frame = ttk.Frame(health_frame)
        cpu_frame.pack(fill="x", pady=5)
        
        ttk.Label(cpu_frame, text="CPU Usage:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.cpu_usage_label = ttk.Label(cpu_frame, text="Unknown")
        self.cpu_usage_label.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        # Refresh button
        ttk.Button(health_frame, text="Refresh Metrics", 
                  command=self.refresh_system_metrics).pack(pady=10)
        
        # Logs & Debug
        logs_frame = ttk.LabelFrame(self.diagnostics_frame, text="Logs & Debug Info", padding=10)
        logs_frame.pack(padx=10, pady=10, fill="both", expand=True)
        
        # Log selection
        log_select_frame = ttk.Frame(logs_frame)
        log_select_frame.pack(fill="x", pady=5)
        
        ttk.Label(log_select_frame, text="Select Log:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.log_combo = ttk.Combobox(log_select_frame, width=30)
        self.log_combo.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        # Add some default log options
        log_options = ["Application Log", "Forecast Engine Log", "Simulation Engine Log", 
                      "Learning System Log", "Errors Log"]
        self.log_combo['values'] = log_options
        self.log_combo.current(0)  # Set default selection
        
        # View log button
        ttk.Button(log_select_frame, text="View Log", 
                  command=self.view_selected_log).grid(row=0, column=2, padx=5, pady=5)
        
        # Clear log button
        ttk.Button(log_select_frame, text="Clear Log", 
                  command=self.clear_selected_log).grid(row=0, column=3, padx=5, pady=5)
        
        # Log content
        log_content_frame = ttk.Frame(logs_frame)
        log_content_frame.pack(fill="both", expand=True, pady=5)
        
        self.log_content = scrolledtext.ScrolledText(log_content_frame, height=15)
        self.log_content.pack(fill="both", expand=True)
        
        # Tools & Actions
        tools_frame = ttk.LabelFrame(self.diagnostics_frame, text="Diagnostic Tools", padding=10)
        tools_frame.pack(padx=10, pady=10, fill="x")
        
        # Buttons for various tools
        tools_btn_frame = ttk.Frame(tools_frame)
        tools_btn_frame.pack(fill="x", pady=5)
        
        ttk.Button(tools_btn_frame, text="Test Connections", 
                  command=self.test_connections).grid(row=0, column=0, padx=5, pady=5)
        
        ttk.Button(tools_btn_frame, text="Verify Data Integrity", 
                  command=self.verify_data_integrity).grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Button(tools_btn_frame, text="Check Module Status", 
                  command=self.check_module_status).grid(row=0, column=2, padx=5, pady=5)
        
        # Result display
        self.diagnostics_result = scrolledtext.ScrolledText(tools_frame, height=6)
        self.diagnostics_result.pack(fill="both", expand=True, pady=5)
        self.diagnostics_result.insert(tk.END, "Run a diagnostic tool to see results")
        self.diagnostics_result.config(state="disabled")  # Make read-only initially

    def refresh_system_metrics(self):
        """Refreshes system metrics display."""
        try:
            import psutil
            # Get memory usage
            mem = psutil.virtual_memory()
            mem_percent = mem.percent
            mem_used_gb = mem.used / (1024 ** 3)  # Convert bytes to GB
            mem_total_gb = mem.total / (1024 ** 3)  # Convert bytes to GB
            
            # Update memory label
            self.memory_usage_label.config(
                text=f"{mem_percent}% ({mem_used_gb:.2f} GB / {mem_total_gb:.2f} GB)"
            )
            
            # Get CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            self.cpu_usage_label.config(text=f"{cpu_percent}%")
            
            self.update_status("System metrics refreshed")
        except ImportError:
            self.memory_usage_label.config(text="psutil module not available")
            self.cpu_usage_label.config(text="psutil module not available")
            self.update_status("Could not refresh system metrics - psutil module not available")
        except Exception as e:
            self.memory_usage_label.config(text="Error")
            self.cpu_usage_label.config(text="Error")
            self.update_status(f"Error refreshing system metrics: {e}")

    def view_selected_log(self):
        """Displays the selected log file content."""
        log_type = self.log_combo.get()
        self.log_content.delete("1.0", tk.END)
        
        # Map log selection to log file paths
        log_files = {
            "Application Log": "logs/app.log",
            "Forecast Engine Log": "logs/forecast_engine.log",
            "Simulation Engine Log": "logs/simulation_engine.log",
            "Learning System Log": "logs/learning_system.log",
            "Errors Log": "logs/errors.log"
        }
        
        log_path = log_files.get(log_type)
        if not log_path:
            self.log_content.insert(tk.END, f"No log file defined for: {log_type}")
            return
        
        try:
            if os.path.exists(log_path):
                with open(log_path, "r", encoding="utf-8") as f:
                    # Get last 100 lines (most recent logs)
                    lines = f.readlines()[-100:]
                    for line in lines:
                        self.log_content.insert(tk.END, line)
                self.update_status(f"Loaded log: {log_type}")
            else:
                self.log_content.insert(tk.END, f"Log file not found: {log_path}")
                self.update_status(f"Log file not found: {log_path}")
        except Exception as e:
            self.log_content.insert(tk.END, f"Error loading log: {str(e)}")
            self.update_status(f"Error loading log: {str(e)}")

    def clear_selected_log(self):
        """Clears the selected log file."""
        log_type = self.log_combo.get()
        
        # Map log selection to log file paths
        log_files = {
            "Application Log": "logs/app.log",
            "Forecast Engine Log": "logs/forecast_engine.log",
            "Simulation Engine Log": "logs/simulation_engine.log",
            "Learning System Log": "logs/learning_system.log",
            "Errors Log": "logs/errors.log"
        }
        
        log_path = log_files.get(log_type)
        if not log_path:
            messagebox.showwarning("Not Found", f"No log file defined for: {log_type}")
            return
        
        # Ask for confirmation
        confirm = messagebox.askyesno("Confirm", f"Are you sure you want to clear the {log_type}?")
        if not confirm:
            return
            
        try:
            # Open the file in write mode (which truncates it)
            with open(log_path, "w", encoding="utf-8") as f:
                f.write(f"Log cleared on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            
            self.log_content.delete("1.0", tk.END)
            self.log_content.insert(tk.END, f"Log {log_type} has been cleared.")
            self.update_status(f"Log cleared: {log_type}")
            self.log_activity(f"Cleared log: {log_type}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to clear log: {str(e)}")
            self.update_status(f"Error clearing log: {str(e)}")

    def test_connections(self):
        """Tests connections to various services."""
        self.diagnostics_result.config(state="normal")
        self.diagnostics_result.delete("1.0", tk.END)
        self.diagnostics_result.insert(tk.END, "Testing connections...\n")
        
        # Test backend connection
        try:
            backend_status = self.make_request('GET', '/status')
            if backend_status and backend_status.get('status') == 'online':
                self.diagnostics_result.insert(tk.END, "✓ Backend: Connected\n")
            else:
                self.diagnostics_result.insert(tk.END, "✗ Backend: Not reachable\n")
        except Exception:
            self.diagnostics_result.insert(tk.END, "✗ Backend: Error connecting\n")
        
        # Test database connection
        try:
            db_status = self.make_request('GET', '/database/status')
            if db_status and db_status.get('status') == 'connected':
                self.diagnostics_result.insert(tk.END, "✓ Database: Connected\n")
            else:
                self.diagnostics_result.insert(tk.END, "✗ Database: Not connected\n")
        except Exception:
            self.diagnostics_result.insert(tk.END, "✗ Database: Error checking status\n")
        
        # Test file system access
        try:
            logs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
            if os.path.exists(logs_dir) and os.access(logs_dir, os.R_OK | os.W_OK):
                self.diagnostics_result.insert(tk.END, "✓ File System: Read/Write access OK\n")
            else:
                self.diagnostics_result.insert(tk.END, "✗ File System: Access issues\n")
        except Exception:
            self.diagnostics_result.insert(tk.END, "✗ File System: Error checking access\n")
        
        self.diagnostics_result.insert(tk.END, "\nConnection tests completed.")
        self.diagnostics_result.config(state="disabled")
        self.update_status("Connection tests completed")

    def verify_data_integrity(self):
        """Verifies data integrity of various files."""
        self.diagnostics_result.config(state="normal")
        self.diagnostics_result.delete("1.0", tk.END)
        self.diagnostics_result.insert(tk.END, "Checking data integrity...\n")
        
        # Define critical files to check
        critical_files = [
            "config/simulation_config.yaml",
            "config/variables_config.yaml",
            "config/rules_config.yaml"
        ]
        
        for file_path in critical_files:
            full_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), file_path)
            if os.path.exists(full_path):
                try:
                    with open(full_path, "r", encoding="utf-8") as f:
                        # Try to load and parse the file based on extension
                        if file_path.endswith('.yaml') or file_path.endswith('.yml'):
                            import yaml
                            yaml.safe_load(f)
                            self.diagnostics_result.insert(tk.END, f"✓ {file_path}: Valid YAML\n")
                        elif file_path.endswith('.json'):
                            import json
                            json.load(f)
                            self.diagnostics_result.insert(tk.END, f"✓ {file_path}: Valid JSON\n")
                        else:
                            # For other files, just check they're readable
                            f.read()
                            self.diagnostics_result.insert(tk.END, f"✓ {file_path}: Readable\n")
                except Exception as e:
                    self.diagnostics_result.insert(tk.END, f"✗ {file_path}: Error - {str(e)}\n")
            else:
                self.diagnostics_result.insert(tk.END, f"✗ {file_path}: Not found\n")
        
        self.diagnostics_result.insert(tk.END, "\nData integrity check completed.")
        self.diagnostics_result.config(state="disabled")
        self.update_status("Data integrity check completed")

    def check_module_status(self):
        """Checks the status of Pulse modules."""
        self.diagnostics_result.config(state="normal")
        self.diagnostics_result.delete("1.0", tk.END)
        self.diagnostics_result.insert(tk.END, "Checking module status...\n")
        
        # Check if required modules are available
        modules_to_check = [
            "core.pulse_config",
            "learning.forecast_pipeline_runner",
            "learning.recursion_audit",
            "memory.variable_cluster_engine",
            "symbolic_system.symbolic_convergence_detector"
        ]
        
        for module_name in modules_to_check:
            if module_name in sys.modules:
                self.diagnostics_result.insert(tk.END, f"✓ {module_name}: Loaded\n")
            else:
                # Try to import
                try:
                    __import__(module_name)
                    self.diagnostics_result.insert(tk.END, f"✓ {module_name}: Available\n")
                except ImportError:
                    self.diagnostics_result.insert(tk.END, f"✗ {module_name}: Not available\n")
        
        # Also check optional dependencies
        optional_modules = [
            "pandas",
            "numpy",
            "matplotlib",
            "scikit-learn",
            "statsmodels",
            "networkx"
        ]
        
        self.diagnostics_result.insert(tk.END, "\nOptional dependencies:\n")
        for module_name in optional_modules:
            try:
                __import__(module_name)
                self.diagnostics_result.insert(tk.END, f"✓ {module_name}: Installed\n")
            except ImportError:
                self.diagnostics_result.insert(tk.END, f"✗ {module_name}: Not installed\n")
        
        self.diagnostics_result.insert(tk.END, "\nModule status check completed.")
        self.diagnostics_result.config(state="disabled")
        self.update_status("Module status check completed")

    def load_variable_trace(self):
        """Loads and visualizes a variable's trace data."""
        selected_var = self.var_combo.get()
        time_range = self.time_range_combo.get()
        
        if not selected_var:
            messagebox.showwarning("Selection Required", "Please select a variable to analyze.")
            return
            
        self.update_status(f"Loading variable trace for {selected_var}...")
        
        try:
            # Clear any existing plot
            for widget in self.var_trace_plot_frame.winfo_children():
                widget.destroy()
                
            # Try to use the imported function if available
            if hasattr(self, 'has_pulse_modules') and self.has_pulse_modules:
                # Define time windows based on selection
                time_windows = {
                    "Last 24 Hours": 1,
                    "Last 7 Days": 7,
                    "Last 30 Days": 30,
                    "All Time": None
                }
                days = time_windows.get(time_range)
                
                # Load data using the imported function
                try:
                    from dev_tools.pulse_ui_plot import load_variable_trace, plot_variables
                    trace_data = load_variable_trace(selected_var, days=days)
                    
                    # Plot the data
                    fig = plot_variables([selected_var], trace_data)
                    
                    # Create matplotlib canvas
                    canvas = FigureCanvasTkAgg(fig, master=self.var_trace_plot_frame)
                    canvas.draw()
                    
                    # Pack canvas
                    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
                    
                    # Add toolbar
                    from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk
                    toolbar = NavigationToolbar2Tk(canvas, self.var_trace_plot_frame)
                    toolbar.update()
                    
                    self.update_status(f"Variable trace for {selected_var} loaded successfully")
                except Exception as e:
                    messagebox.showerror("Plot Error", f"Error plotting data: {str(e)}")
                    self.generate_dummy_variable_plot(selected_var)
            else:
                # Fallback with dummy data for testing UI
                self.generate_dummy_variable_plot(selected_var)
                self.update_status(f"Generated sample data for {selected_var} (modules not available)")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load variable trace: {str(e)}")
            self.update_status(f"Error loading variable trace: {str(e)}")
            
    def generate_dummy_variable_plot(self, variable_name):
        """Generates a dummy plot for testing when real data isn't available."""
        # Clear the frame
        for widget in self.var_trace_plot_frame.winfo_children():
            widget.destroy()
        
        # Create figure and axis
        fig = Figure(figsize=(8, 4), dpi=100)
        ax = fig.add_subplot(111)
        
        # Generate dummy data
        import random
        x = list(range(100))
        y = [random.random() * random.randint(1, 5) for _ in range(100)]
        
        # Add some trend for visual interest
        for i in range(10, 30):
            y[i] *= 1.5
        for i in range(50, 80):
            y[i] *= 0.7
        
        # Plot
        ax.plot(x, y, 'b-', label=variable_name)
        ax.set_title(f"Sample Data for {variable_name}")
        ax.set_xlabel("Time")
        ax.set_ylabel("Value")
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        fig.tight_layout()
        
        # Create canvas
        canvas = FigureCanvasTkAgg(fig, master=self.var_trace_plot_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Add toolbar
        from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk
        toolbar = NavigationToolbar2Tk(canvas, self.var_trace_plot_frame)
        
    def generate_learning_report(self):
        """Generates and displays a learning metrics report."""
        time_period = self.time_period_combo.get()
        include_accuracy = self.accuracy_var.get()
        include_trust = self.trust_var.get()
        include_events = self.learning_events_var.get()
        
        self.update_status(f"Generating learning report for {time_period}...")
        
        # Clear the report text
        self.learning_report_text.delete("1.0", tk.END)
        
        try:
            if hasattr(self, 'has_pulse_modules') and self.has_pulse_modules:
                try:
                    # Try to use the actual learning log viewer if available
                    from operator_interface.learning_log_viewer import load_learning_events, summarize_learning_events
                    
                    # Load learning events
                    learning_events = load_learning_events(limit=100)  # Adjust limit as needed
                    summary = summarize_learning_events(learning_events)
                    
                    # Display header
                    self.learning_report_text.insert(tk.END, f"Learning Report for {time_period}\n")
                    self.learning_report_text.insert(tk.END, "="*50 + "\n\n")
                    
                    # Display summary
                    self.learning_report_text.insert(tk.END, "SUMMARY\n")
                    self.learning_report_text.insert(tk.END, "-"*30 + "\n")
                    
                    for event_type, count in summary.items():
                        self.learning_report_text.insert(tk.END, f"{event_type}: {count} events\n")
                    
                    # Display details based on selected options
                    if include_events:
                        self.learning_report_text.insert(tk.END, "\nRECENT LEARNING EVENTS\n")
                        self.learning_report_text.insert(tk.END, "-"*30 + "\n")
                        
                        for event in learning_events[:10]:  # Show top 10 events
                            event_type = event.get("event_type", "unknown")
                            timestamp = event.get("timestamp", "unknown")
                            self.learning_report_text.insert(tk.END, f"{timestamp} - {event_type}\n")
                            
                            # Show some data details
                            data = event.get("data", {})
                            for key, value in data.items():
                                if isinstance(value, (str, int, float, bool)):
                                    self.learning_report_text.insert(tk.END, f"  {key}: {value}\n")
                            
                            self.learning_report_text.insert(tk.END, "\n")
                    
                    self.update_status("Learning report generated successfully")
                except Exception as e:
                    self.learning_report_text.insert(tk.END, f"Error generating report with actual module: {str(e)}\n")
                    # Fall back to dummy report
                    self.generate_dummy_learning_report(time_period, include_accuracy, include_trust, include_events)
            else:
                # Generate dummy report if modules not available
                self.generate_dummy_learning_report(time_period, include_accuracy, include_trust, include_events)
                self.update_status("Generated sample learning report (modules not available)")
        except Exception as e:
            self.learning_report_text.insert(tk.END, f"Error generating report: {str(e)}")
            self.update_status(f"Error generating learning report: {str(e)}")

    def generate_dummy_learning_report(self, time_period, include_accuracy, include_trust, include_events):
        """Generates a dummy learning report for the UI."""
        from datetime import datetime, timedelta
        
        self.learning_report_text.insert(tk.END, f"Learning Report for {time_period}\n")
        self.learning_report_text.insert(tk.END, "="*50 + "\n\n")
        
        # Summary section
        self.learning_report_text.insert(tk.END, "SUMMARY\n")
        self.learning_report_text.insert(tk.END, "-"*30 + "\n")
        self.learning_report_text.insert(tk.END, "variable_weight_change: 24 events\n")
        self.learning_report_text.insert(tk.END, "symbolic_upgrade: 8 events\n")
        self.learning_report_text.insert(tk.END, "revision_trigger: 12 events\n")
        self.learning_report_text.insert(tk.END, "arc_regret: 6 events\n")
        self.learning_report_text.insert(tk.END, "learning_summary: 2 events\n\n")
        
        if include_accuracy:
            self.learning_report_text.insert(tk.END, "ACCURACY METRICS\n")
            self.learning_report_text.insert(tk.END, "-"*30 + "\n")
            self.learning_report_text.insert(tk.END, "Overall Prediction Accuracy: 76.3%\n")
            self.learning_report_text.insert(tk.END, "Symbolic Arc Prediction: 82.1%\n")
            self.learning_report_text.insert(tk.END, "Capital Outcome Prediction: 71.8%\n\n")
        
        if include_trust:
            self.learning_report_text.insert(tk.END, "TRUST METRICS\n")
            self.learning_report_text.insert(tk.END, "-"*30 + "\n")
            self.learning_report_text.insert(tk.END, "Average Trust Score: 0.723\n")
            self.learning_report_text.insert(tk.END, "Rule Confidence: 0.851\n")
            self.learning_report_text.insert(tk.END, "Variable Volatility Index: 0.342\n\n")
        
        if include_events:
            self.learning_report_text.insert(tk.END, "RECENT LEARNING EVENTS\n")
            self.learning_report_text.insert(tk.END, "-"*30 + "\n")
            
            # Generate some dummy events
            now = datetime.now()
            event_types = ["variable_weight_change", "symbolic_upgrade", "revision_trigger", "arc_regret"]
            
            for i in range(10):
                event_time = (now - timedelta(hours=i*3)).strftime("%Y-%m-%d %H:%M:%S")
                event_type = event_types[i % len(event_types)]
                
                self.learning_report_text.insert(tk.END, f"{event_time} - {event_type}\n")
                
                if event_type == "variable_weight_change":
                    var_name = f"var_{chr(65 + i % 8)}"  # var_A to var_H
                    self.learning_report_text.insert(tk.END, f"  variable: {var_name}\n")
                    self.learning_report_text.insert(tk.END, f"  old_weight: {0.8 + (i % 5) * 0.05:.2f}\n")
                    self.learning_report_text.insert(tk.END, f"  new_weight: {0.75 + (i % 7) * 0.05:.2f}\n")
                elif event_type == "symbolic_upgrade":
                    self.learning_report_text.insert(tk.END, f"  hope: +{(i % 10) * 0.03:.2f}\n")
                    self.learning_report_text.insert(tk.END, f"  despair: -{(i % 8) * 0.02:.2f}\n")
                elif event_type == "revision_trigger":
                    self.learning_report_text.insert(tk.END, f"  reason: {'fragmentation > threshold' if i % 2 else 'confidence < minimum'}\n")
                elif event_type == "arc_regret":
                    self.learning_report_text.insert(tk.END, f"  arc_hope: {(i % 10) * 0.1:.2f}\n")
                    self.learning_report_text.insert(tk.END, f"  arc_despair: {(10 - i % 10) * 0.1:.2f}\n")
                
                self.learning_report_text.insert(tk.END, "\n")

    def export_current_analysis(self):
        """Exports the current analysis to a file."""
        from datetime import datetime
        
        active_tab = self.notebook.select()
        tab_text = self.notebook.tab(active_tab, "text")
        
        if tab_text != "Analysis":
            messagebox.showinfo("Export", "Please navigate to the Analysis tab to export analysis.")
            return
            
        # Determine which analysis is showing
        notebook_tab_idx = None
        for child in self.analysis_frame.winfo_children():
            if isinstance(child, ttk.Notebook):
                notebook_tab_idx = child.index(child.select())
                break
                
        if notebook_tab_idx is None:
            messagebox.showwarning("Export Error", "Could not determine the current analysis tab.")
            return
        
        try:
            # Default filename based on analysis type
            analysis_types = ["variable_trace", "recursion_audit", "cluster_analysis", "learning_metrics"]
            default_filename = f"{analysis_types[notebook_tab_idx]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Ask for save location
            file_path = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf"), ("PNG files", "*.png"), 
                         ("All files", "*.*")],
                initialfile=default_filename
            )
            
            if not file_path:  # User cancelled
                return
                
            # For demonstration, we'll just create a text file
            with open(file_path, 'w') as f:
                f.write(f"Pulse Analysis Export: {default_filename}\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write("This is a placeholder for the actual analysis export functionality.\n")
            
            messagebox.showinfo("Export Complete", f"Analysis exported to {file_path}")
            self.update_status(f"Analysis exported to {file_path}")
            
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export analysis: {str(e)}")
            self.update_status(f"Export error: {str(e)}")

    def export_all_analyses(self):
        """Exports all analyses to a comprehensive report."""
        from datetime import datetime
        
        try:
            # Ask for directory to save in
            export_dir = filedialog.askdirectory(title="Select Export Directory")
            
            if not export_dir:  # User cancelled
                return
                
            # Create a common filename for all exports
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            base_filename = f"pulse_analyses_{timestamp}"
            
            # For demonstration, we'll just create a text file
            report_path = os.path.join(export_dir, f"{base_filename}.txt")
            
            with open(report_path, 'w') as f:
                f.write(f"Pulse Comprehensive Analysis Report\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write("This is a placeholder for the actual comprehensive export functionality.\n")
                f.write("In a real implementation, this would include:\n")
                f.write("1. Variable trace analysis\n")
                f.write("2. Recursion audit results\n")
                f.write("3. Cluster visualizations\n")
                f.write("4. Learning metrics\n")
            
            messagebox.showinfo("Export Complete", f"All analyses exported to {report_path}")
            self.update_status(f"All analyses exported to {report_path}")
            
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export analyses: {str(e)}")
            self.update_status(f"Export error: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = PulseApp(root)
    root.mainloop()