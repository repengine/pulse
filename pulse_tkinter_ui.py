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

        # Set up a better visual style
        style = ttk.Style()
        if 'clam' in style.theme_names():  # Check if the theme is available
            style.theme_use('clam')
        
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
        ttk.Label(self.learning_frame, text="Learning & Training Review", style="Header.TLabel").pack(pady=10)
        
        # Create frame for the batch ID inputs
        input_frame = ttk.LabelFrame(self.learning_frame, text="Run AI Training Audit", padding=10)
        input_frame.pack(padx=10, pady=10, fill="x")
        
        # Previous Batch ID
        prev_batch_frame = ttk.Frame(input_frame)
        prev_batch_frame.pack(pady=5, fill="x")
        ttk.Label(prev_batch_frame, text="Previous Batch ID:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.previous_batch_id_entry = ttk.Entry(prev_batch_frame, width=30)
        self.previous_batch_id_entry.grid(row=0, column=1, padx=5, pady=5)
        
        # Current Batch ID
        curr_batch_frame = ttk.Frame(input_frame)
        curr_batch_frame.pack(pady=5, fill="x")
        ttk.Label(curr_batch_frame, text="Current Batch ID:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.current_batch_id_entry = ttk.Entry(curr_batch_frame, width=30)
        self.current_batch_id_entry.grid(row=0, column=1, padx=5, pady=5)
        
        # Trigger button
        trigger_button = ttk.Button(input_frame, text="Run AI Training Audit", command=self.trigger_ai_training_audit)
        trigger_button.pack(pady=10)
        
        # Status label
        self.ai_review_status_label = ttk.Label(input_frame, text="")
        self.ai_review_status_label.pack(pady=5)
        
        # Results frame
        results_frame = ttk.LabelFrame(self.learning_frame, text="Audit Report", padding=10)
        results_frame.pack(padx=10, pady=10, fill="both", expand=True)
        
        # Create report text area
        self.audit_report_text = scrolledtext.ScrolledText(results_frame, wrap=tk.WORD)
        self.audit_report_text.pack(fill="both", expand=True)

    def _init_analysis_tab(self):
        """Initializes the Analysis tab."""
        # Header
        ttk.Label(self.analysis_frame, text="Pulse Analysis Tools", style="Header.TLabel").pack(pady=10)
        
        # Create variable analysis section
        var_analysis_frame = ttk.LabelFrame(self.analysis_frame, text="Variable Analysis", padding=10)
        var_analysis_frame.pack(padx=10, pady=10, fill="x")
        
        # Variable selector and load button
        var_selector_frame = ttk.Frame(var_analysis_frame)
        var_selector_frame.pack(pady=5, fill="x")
        
        ttk.Label(var_selector_frame, text="Variable:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.variable_entry = ttk.Entry(var_selector_frame, width=30)
        self.variable_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        load_var_btn = ttk.Button(var_selector_frame, text="Load Variable Data", 
                                 command=self.load_variable_data)
        load_var_btn.grid(row=0, column=2, padx=5, pady=5)
        
        # Variable visualization frame
        self.var_viz_frame = ttk.Frame(var_analysis_frame)
        self.var_viz_frame.pack(pady=10, fill="both", expand=True)
        
        # Symbolic analysis section
        symbolic_frame = ttk.LabelFrame(self.analysis_frame, text="Symbolic Analysis", padding=10)
        symbolic_frame.pack(padx=10, pady=10, fill="x", expand=True)
        
        # Buttons for different analyses
        btn_frame = ttk.Frame(symbolic_frame)
        btn_frame.pack(fill="x", pady=5)
        
        cluster_btn = ttk.Button(btn_frame, text="View Variable Clusters", 
                              command=self.view_variable_clusters)
        cluster_btn.grid(row=0, column=0, padx=5, pady=5)
        
        contradiction_btn = ttk.Button(btn_frame, text="View Symbolic Contradictions", 
                                     command=self.view_symbolic_contradictions)
        contradiction_btn.grid(row=0, column=1, padx=5, pady=5)
        
        # Results text area
        self.analysis_result_text = scrolledtext.ScrolledText(symbolic_frame, wrap=tk.WORD, height=15)
        self.analysis_result_text.pack(pady=5, fill="both", expand=True)
        
    def load_variable_data(self):
        """Loads and visualizes data for a selected variable."""
        variable_name = self.variable_entry.get().strip()
        if not variable_name:
            messagebox.showwarning("Input Required", "Please enter a variable name.")
            return
        
        # Clear previous visualization
        for widget in self.var_viz_frame.winfo_children():
            widget.destroy()
            
        # Check if we have the imported module
        if not self.has_pulse_modules:
            messagebox.showerror("Module Error", "Required Pulse modules are not available.")
            return
            
        try:
            # This would normally use the imported load_variable_trace and plot_variables functions
            # For now, display a placeholder message
            ttk.Label(self.var_viz_frame, text=f"Loading data for: {variable_name}...").pack(pady=10)
            
            # Try to load and plot if the modules are available
            try:
                data = load_variable_trace(variable_name)
                fig = plot_variables([variable_name], data)
                
                # Create matplotlib canvas
                canvas_frame = ttk.Frame(self.var_viz_frame)
                canvas_frame.pack(fill=tk.BOTH, expand=True)
                
                canvas = FigureCanvasTkAgg(fig, master=canvas_frame)
                canvas.draw()
                canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
                
                # Add a toolbar for interactive features
                from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk
                toolbar = NavigationToolbar2Tk(canvas, canvas_frame)
                toolbar.update()
                
                self.log_activity(f"Loaded variable data for {variable_name}")
            except Exception as e:
                ttk.Label(self.var_viz_frame, text=f"Failed to load/plot data: {str(e)}").pack(pady=10)
                print(f"Error in load_variable_data: {e}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load variable data: {str(e)}")
    
    def view_variable_clusters(self):
        """Displays variable clusters from the memory system."""
        self.analysis_result_text.delete("1.0", tk.END)
        
        if not self.has_pulse_modules:
            self.analysis_result_text.insert(tk.END, "Required Pulse modules are not available.")
            return
            
        try:
            # Try to get cluster data using imported function
            clusters = summarize_clusters()
            digest = format_variable_cluster_digest_md(limit=10)
            
            if digest:
                self.analysis_result_text.insert(tk.END, digest)
            else:
                self.analysis_result_text.insert(tk.END, "No variable clusters found or digestible.")
                
            self.log_activity("Viewed variable clusters")
        except Exception as e:
            self.analysis_result_text.insert(tk.END, f"Failed to load variable clusters: {str(e)}")
            print(f"Error in view_variable_clusters: {e}")
    
    def view_symbolic_contradictions(self):
        """Displays symbolic contradictions from the system."""
        self.analysis_result_text.delete("1.0", tk.END)
        
        if not self.has_pulse_modules:
            self.analysis_result_text.insert(tk.END, "Required Pulse modules are not available.")
            return
            
        try:
            # Try to get contradiction data using imported function
            conflicts = load_symbolic_conflict_events()
            digest = format_contradiction_cluster_md(conflicts)
            
            if digest:
                self.analysis_result_text.insert(tk.END, digest)
            else:
                self.analysis_result_text.insert(tk.END, "No symbolic contradictions found.")
                
            self.log_activity("Viewed symbolic contradictions")
        except Exception as e:
            self.analysis_result_text.insert(tk.END, f"Failed to load symbolic contradictions: {str(e)}")
            print(f"Error in view_symbolic_contradictions: {e}")

    def _init_diagnostics_tab(self):
        """Initializes the Diagnostics tab."""
        # Header
        ttk.Label(self.diagnostics_frame, text="System Diagnostics", style="Header.TLabel").pack(pady=10)
        
        # System health section
        health_frame = ttk.LabelFrame(self.diagnostics_frame, text="System Health", padding=10)
        health_frame.pack(padx=10, pady=10, fill="x")
        
        # Run diagnostics button
        run_diag_btn = ttk.Button(health_frame, text="Run System Diagnostics", 
                                 command=self.run_system_diagnostics)
        run_diag_btn.pack(pady=5)
        
        # System resources section
        resources_frame = ttk.Frame(health_frame)
        resources_frame.pack(fill="x", pady=5)
        
        ttk.Label(resources_frame, text="Memory Usage:").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.memory_usage_label = ttk.Label(resources_frame, text="N/A")
        self.memory_usage_label.grid(row=0, column=1, padx=5, pady=2, sticky="w")
        
        ttk.Label(resources_frame, text="CPU Usage:").grid(row=1, column=0, padx=5, pady=2, sticky="w")
        self.cpu_usage_label = ttk.Label(resources_frame, text="N/A")
        self.cpu_usage_label.grid(row=1, column=1, padx=5, pady=2, sticky="w")
        
        ttk.Label(resources_frame, text="Disk Space:").grid(row=2, column=0, padx=5, pady=2, sticky="w")
        self.disk_space_label = ttk.Label(resources_frame, text="N/A")
        self.disk_space_label.grid(row=2, column=1, padx=5, pady=2, sticky="w")
        
        # Log analysis section
        logs_frame = ttk.LabelFrame(self.diagnostics_frame, text="Log Analysis", padding=10)
        logs_frame.pack(padx=10, pady=10, fill="x")
        
        log_controls_frame = ttk.Frame(logs_frame)
        log_controls_frame.pack(fill="x", pady=5)
        
        ttk.Label(log_controls_frame, text="Log File:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.log_file_combo = ttk.Combobox(log_controls_frame, 
                                           values=["system.log", "forecast.log", "retrodiction.log", "learning.log", "error.log"])
        self.log_file_combo.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.log_file_combo.current(0)  # Select first item by default
        
        load_log_btn = ttk.Button(log_controls_frame, text="Load Log", command=self.load_log_file)
        load_log_btn.grid(row=0, column=2, padx=5, pady=5)
        
        # Log viewer
        self.log_text = scrolledtext.ScrolledText(logs_frame, height=15, wrap=tk.WORD)
        self.log_text.pack(pady=5, fill="both", expand=True)
        
        # Autopilot history table
        history_frame = ttk.LabelFrame(self.diagnostics_frame, text="Autopilot History", padding=10)
        history_frame.pack(padx=10, pady=10, fill="both", expand=True)
        
        # Create the treeview for autopilot history
        self.autopilot_history_tree = ttk.Treeview(history_frame, 
                                                 columns=("ID", "Start Time", "End Time", "Status"),
                                                 show="headings",
                                                 selectmode="browse")
        
        # Define column headings
        self.autopilot_history_tree.heading("ID", text="Run ID")
        self.autopilot_history_tree.heading("Start Time", text="Start Time")
        self.autopilot_history_tree.heading("End Time", text="End Time")
        self.autopilot_history_tree.heading("Status", text="Status")
        
        # Configure column widths
        self.autopilot_history_tree.column("ID", width=100)
        self.autopilot_history_tree.column("Start Time", width=150)
        self.autopilot_history_tree.column("End Time", width=150)
        self.autopilot_history_tree.column("Status", width=100)
        
        # Add scrollbar
        history_scrollbar = ttk.Scrollbar(history_frame, orient="vertical", 
                                         command=self.autopilot_history_tree.yview)
        self.autopilot_history_tree.configure(yscrollcommand=history_scrollbar.set)
        
        # Pack everything
        self.autopilot_history_tree.pack(side="left", fill="both", expand=True)
        history_scrollbar.pack(side="right", fill="y")
        
    def run_system_diagnostics(self):
        """Runs system diagnostics and updates the UI."""
        try:
            # Update memory usage
            import psutil
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            self.memory_usage_label.config(text=f"{memory_percent}% ({memory.used // 1024 // 1024} MB)")
            
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            self.cpu_usage_label.config(text=f"{cpu_percent}%")
            
            # Disk space
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            self.disk_space_label.config(text=f"{disk_percent}% used ({disk.free // 1024 // 1024 // 1024} GB free)")
            
            # Log diagnostics run
            self.log_activity("System diagnostics completed")
            
        except ImportError:
            self.memory_usage_label.config(text="psutil not installed")
            self.cpu_usage_label.config(text="psutil not installed")
            self.disk_space_label.config(text="psutil not installed")
            messagebox.showinfo("Missing Dependency", "The psutil library is required for system diagnostics. Install with: pip install psutil")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to run diagnostics: {str(e)}")
    
    def load_log_file(self):
        """Loads and displays the selected log file."""
        log_file = self.log_file_combo.get()
        if not log_file:
            return
            
        # Clear previous content
        self.log_text.delete("1.0", tk.END)
        
        # Try to find log file
        log_path = os.path.join("logs", log_file)
        if not os.path.exists(log_path):
            self.log_text.insert(tk.END, f"Log file not found: {log_path}")
            return
            
        try:
            with open(log_path, "r") as f:
                log_content = f.read()
                self.log_text.insert(tk.END, log_content)
                self.log_activity(f"Loaded log file: {log_file}")
        except Exception as e:
            self.log_text.insert(tk.END, f"Error reading log file: {str(e)}")
            print(f"Error reading log file: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = PulseApp(root)
    root.mainloop()