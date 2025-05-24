import os
import tkinter as tk
from tkinter import scrolledtext, ttk, font
from chatmode.conversational_core import ConversationalCore
import threading  # To run LLM processing in a separate thread
import json


class ConversationalGUI(tk.Tk):
    def __init__(self):
        """
        Initializes the enhanced Conversational GUI.
        """
        super().__init__()

        self.title("Pulse AI Conversational Interface")
        self.geometry("900x700")  # Larger default size for more content

        # Set theme colors
        self.bg_color = "#F0F0F0"  # Light gray background
        self.accent_color = "#4a86e8"  # Blue accent
        self.configure(bg=self.bg_color)

        # Initialize the ConversationalCore
        self.conversational_core = ConversationalCore()

        # Setup the main layout
        self._setup_ui()

        # Setup state variables
        self.processing = False
        self.current_intent = "general_query"
        self.llm_model_type = tk.StringVar(value="openai")
        self.llm_model_name = tk.StringVar(value="gpt-3.5-turbo")

        # --- Initial Messages ---
        self.display_message(
            "Pulse AI: Hello! How can I help you with the Pulse codebase today?\n"
        )
        self.display_system_message(
            "Type a query, choose a command from the dropdown, or click the buttons below for common actions."
        )

    def _setup_ui(self):
        """Sets up the UI components with an improved layout"""
        # Create main frames
        self.top_frame = tk.Frame(self, bg=self.bg_color)
        self.top_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

        self.main_frame = tk.Frame(self, bg=self.bg_color)
        self.main_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.bottom_frame = tk.Frame(self, bg=self.bg_color)
        self.bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)

        # Setup frames for different content areas
        self._setup_title_area()
        self._setup_conversation_area()
        self._setup_structured_output_area()
        self._setup_input_area()
        self._setup_command_buttons()
        self._setup_status_area()
        self._setup_settings_button()

    def _setup_title_area(self):
        """Sets up the title area with Pulse branding"""
        title_frame = tk.Frame(self.top_frame, bg=self.bg_color)
        title_frame.pack(fill=tk.X)

        title_font = font.Font(family="Arial", size=16, weight="bold")
        title_label = tk.Label(
            title_frame,
            text="Pulse AI Conversational Interface",
            font=title_font,
            bg=self.bg_color,
            fg=self.accent_color,
        )
        title_label.pack(side=tk.LEFT, pady=5)

        # Add mode indicator
        self.mode_var = tk.StringVar(value="Conversation Mode")
        mode_label = tk.Label(
            title_frame,
            textvariable=self.mode_var,
            bg=self.accent_color,
            fg="white",
            padx=10,
            pady=2,
            relief=tk.RAISED,
        )
        mode_label.pack(side=tk.RIGHT, pady=5)

    def _setup_conversation_area(self):
        """Sets up the main conversation history area"""
        conversation_frame = ttk.LabelFrame(
            self.main_frame, text="Conversation History"
        )
        conversation_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        # Chat history display with improved styling
        self.history_display = scrolledtext.ScrolledText(
            conversation_frame,
            wrap=tk.WORD,
            state="disabled",
            font=("Arial", 10),
            bg="white",
            padx=10,
            pady=10,
        )
        self.history_display.pack(fill=tk.BOTH, expand=True)

    def _setup_structured_output_area(self):
        """Sets up the area for structured outputs like forecasts, simulations"""
        output_frame = ttk.LabelFrame(self.main_frame, text="Structured Output")
        output_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))

        # Create notebook for different types of structured outputs
        self.output_notebook = ttk.Notebook(output_frame)
        self.output_notebook.pack(fill=tk.BOTH, expand=True)

        # Create tabs for different output types
        self.forecast_tab = ttk.Frame(self.output_notebook)
        self.simulation_tab = ttk.Frame(self.output_notebook)
        self.memory_tab = ttk.Frame(self.output_notebook)
        self.symbolic_tab = ttk.Frame(self.output_notebook)

        self.output_notebook.add(self.forecast_tab, text="Forecasts")
        self.output_notebook.add(self.simulation_tab, text="Simulations")
        self.output_notebook.add(self.memory_tab, text="Memory")
        self.output_notebook.add(self.symbolic_tab, text="Symbolic")

        # Add a tab for recursive learning status
        self.recursive_learning_tab = ttk.Frame(self.output_notebook)
        self.output_notebook.add(self.recursive_learning_tab, text="Recursive Learning")

        # Add content to each tab
        self.forecast_output = scrolledtext.ScrolledText(
            self.forecast_tab, wrap=tk.WORD, state="disabled", font=("Arial", 10)
        )
        self.forecast_output.pack(fill=tk.BOTH, expand=True)

        self.simulation_output = scrolledtext.ScrolledText(
            self.simulation_tab, wrap=tk.WORD, state="disabled", font=("Arial", 10)
        )
        self.simulation_output.pack(fill=tk.BOTH, expand=True)

        self.memory_output = scrolledtext.ScrolledText(
            self.memory_tab, wrap=tk.WORD, state="disabled", font=("Arial", 10)
        )
        self.memory_output.pack(fill=tk.BOTH, expand=True)

        self.symbolic_output = scrolledtext.ScrolledText(
            self.symbolic_tab, wrap=tk.WORD, state="disabled", font=("Arial", 10)
        )
        self.symbolic_output.pack(fill=tk.BOTH, expand=True)

        # Create recursive learning tab with status display and controls
        self.recursive_learning_frame = ttk.Frame(self.recursive_learning_tab)
        self.recursive_learning_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Status display area
        status_frame = ttk.LabelFrame(
            self.recursive_learning_frame, text="Learning Cycles Status"
        )
        status_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.learning_status = scrolledtext.ScrolledText(
            status_frame, wrap=tk.WORD, height=10, state="disabled", font=("Arial", 10)
        )
        self.learning_status.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Controls frame
        controls_frame = ttk.LabelFrame(self.recursive_learning_frame, text="Controls")
        controls_frame.pack(fill=tk.X, padx=5, pady=5)

        # Start cycle frame
        start_frame = ttk.Frame(controls_frame)
        start_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(start_frame, text="Variables:").pack(side=tk.LEFT, padx=(0, 5))
        self.learning_variables = tk.Entry(start_frame, width=25)
        self.learning_variables.pack(side=tk.LEFT, padx=(0, 10))
        self.learning_variables.insert(0, "spx_close,us_10y_yield")

        ttk.Label(start_frame, text="Batch days:").pack(side=tk.LEFT, padx=(0, 5))
        self.batch_days = tk.Entry(start_frame, width=5)
        self.batch_days.pack(side=tk.LEFT, padx=(0, 10))
        self.batch_days.insert(0, "30")

        self.start_learning_btn = ttk.Button(
            start_frame, text="Start Learning Cycle", command=self._start_learning_cycle
        )
        self.start_learning_btn.pack(side=tk.RIGHT, padx=5)

        # Control frame
        control_frame = ttk.Frame(controls_frame)
        control_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(control_frame, text="Cycle ID:").pack(side=tk.LEFT, padx=(0, 5))
        self.cycle_id = tk.Entry(control_frame, width=15)
        self.cycle_id.pack(side=tk.LEFT, padx=(0, 10))

        self.stop_learning_btn = ttk.Button(
            control_frame, text="Stop Cycle", command=self._stop_learning_cycle
        )
        self.stop_learning_btn.pack(side=tk.LEFT, padx=5)

        self.refresh_status_btn = ttk.Button(
            control_frame, text="Refresh Status", command=self._refresh_learning_status
        )
        self.refresh_status_btn.pack(side=tk.LEFT, padx=5)

        # Initialize recursive learning output
        self.recursive_learning_output = scrolledtext.ScrolledText(
            self.recursive_learning_frame,
            wrap=tk.WORD,
            height=10,
            state="disabled",
            font=("Arial", 10),
        )
        self.recursive_learning_output.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def _setup_input_area(self):
        """Sets up the enhanced input area with command selection and text input"""
        input_frame = tk.Frame(self.bottom_frame, bg=self.bg_color)
        input_frame.pack(fill=tk.X, pady=5)

        # Command dropdown for common operations
        command_label = tk.Label(input_frame, text="Command:", bg=self.bg_color)
        command_label.pack(side=tk.LEFT, padx=(0, 5))

        self.command_var = tk.StringVar(value="General Query")
        commands = [
            "General Query",
            "Run Simulation",
            "Get Data",
            "Get Forecast",
            "Get Trust Score",
            "Query Memory",
            "Query Symbolic System",
        ]
        self.command_dropdown = ttk.Combobox(
            input_frame,
            textvariable=self.command_var,
            values=commands,
            width=20,
            state="readonly",
        )
        self.command_dropdown.pack(side=tk.LEFT, padx=5)

        # User Input Field with improved styling
        query_label = tk.Label(input_frame, text="Input:", bg=self.bg_color)
        query_label.pack(side=tk.LEFT, padx=(10, 5))

        self.user_input = tk.Entry(
            input_frame, font=("Arial", 11), bd=2, relief=tk.GROOVE, width=50
        )
        self.user_input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.user_input.bind("<Return>", self.send_message_event)  # Bind Enter key

        # Process Button
        self.send_button = tk.Button(
            input_frame,
            text="Send",
            command=self.send_message,
            bg=self.accent_color,
            fg="white",
            padx=10,
        )
        self.send_button.pack(side=tk.RIGHT, padx=5)

        # Parameter frame for structured inputs when using specific commands
        self.param_frame = tk.Frame(self.bottom_frame, bg=self.bg_color)
        self.param_frame.pack(fill=tk.X, pady=5)

        # Initially hide parameter frame
        self.param_frame.pack_forget()

        # Command type changes should update the parameter frame
        self.command_dropdown.bind("<<ComboboxSelected>>", self._update_parameter_frame)

    def _update_parameter_frame(self, event=None):
        """Updates the parameter input fields based on selected command"""
        command = self.command_var.get()

        # Clear existing widgets
        for widget in self.param_frame.winfo_children():
            widget.destroy()

        # If general query, hide parameter frame
        if command == "General Query":
            self.param_frame.pack_forget()
            return

        # Show parameter frame
        self.param_frame.pack(fill=tk.X, pady=5)

        # Add parameter fields based on command type
        if command == "Run Simulation":
            tk.Label(
                self.param_frame, text="Simulation Parameters:", bg=self.bg_color
            ).pack(side=tk.LEFT)
            self.simulation_params = tk.Entry(self.param_frame, width=50)
            self.simulation_params.pack(side=tk.LEFT, padx=5)

        elif command == "Get Data":
            tk.Label(self.param_frame, text="Symbol:", bg=self.bg_color).pack(
                side=tk.LEFT
            )
            self.data_symbol = tk.Entry(self.param_frame, width=10)
            self.data_symbol.pack(side=tk.LEFT, padx=5)

            tk.Label(self.param_frame, text="Data Type:", bg=self.bg_color).pack(
                side=tk.LEFT
            )
            self.data_type = ttk.Combobox(
                self.param_frame,
                values=["historical_prices", "news", "fundamentals"],
                width=15,
            )
            self.data_type.pack(side=tk.LEFT, padx=5)

            tk.Label(self.param_frame, text="Date Range:", bg=self.bg_color).pack(
                side=tk.LEFT
            )
            self.date_range = tk.Entry(self.param_frame, width=20)
            self.date_range.pack(side=tk.LEFT, padx=5)

        elif command == "Get Forecast":
            tk.Label(self.param_frame, text="Symbol:", bg=self.bg_color).pack(
                side=tk.LEFT
            )
            self.forecast_symbol = tk.Entry(self.param_frame, width=10)
            self.forecast_symbol.pack(side=tk.LEFT, padx=5)

        elif command == "Get Trust Score":
            tk.Label(self.param_frame, text="Item:", bg=self.bg_color).pack(
                side=tk.LEFT
            )
            self.trust_item = tk.Entry(self.param_frame, width=30)
            self.trust_item.pack(side=tk.LEFT, padx=5)

        elif command == "Query Memory" or command == "Query Symbolic System":
            tk.Label(self.param_frame, text="Query:", bg=self.bg_color).pack(
                side=tk.LEFT
            )
            self.query_text = tk.Entry(self.param_frame, width=50)
            self.query_text.pack(side=tk.LEFT, padx=5)

    def _setup_command_buttons(self):
        """Sets up quick-access buttons for common operations"""
        button_frame = tk.Frame(self.bottom_frame, bg=self.bg_color)
        button_frame.pack(fill=tk.X, pady=5)

        # Style for quick buttons
        button_style = {"font": ("Arial", 9), "padx": 5, "pady": 2, "bd": 1}

        # Quick buttons for common operations
        tk.Button(
            button_frame,
            text="Show Latest Forecast",
            command=lambda: self._quick_command("get_forecast"),
            **button_style,
        ).pack(side=tk.LEFT, padx=2)
        tk.Button(
            button_frame,
            text="Run Simulation",
            command=lambda: self._quick_command("run_simulation"),
            **button_style,
        ).pack(side=tk.LEFT, padx=2)
        tk.Button(
            button_frame,
            text="Get Trust Scores",
            command=lambda: self._quick_command("get_trust_score"),
            **button_style,
        ).pack(side=tk.LEFT, padx=2)
        tk.Button(
            button_frame,
            text="Clear History",
            command=self._clear_history,
            **button_style,
        ).pack(side=tk.RIGHT, padx=2)

    def _quick_command(self, command):
        """Triggers UI to set up for a specific command"""
        command_mapping = {
            "run_simulation": "Run Simulation",
            "get_data": "Get Data",
            "get_forecast": "Get Forecast",
            "get_trust_score": "Get Trust Score",
            "query_memory": "Query Memory",
            "query_symbolic_system": "Query Symbolic System",
        }

        if command in command_mapping:
            self.command_var.set(command_mapping[command])
            self._update_parameter_frame()
            # Set focus to the appropriate input field
            self.after(100, lambda: self.user_input.focus_set())

    def _setup_status_area(self):
        """Sets up the status area for processing indicators and system messages"""
        status_frame = tk.Frame(self.bottom_frame, bg=self.bg_color, height=30)
        status_frame.pack(fill=tk.X, pady=(10, 0))

        # Processing indicator
        self.status_var = tk.StringVar(value="Ready")
        self.status_label = tk.Label(
            status_frame,
            textvariable=self.status_var,
            fg="green",
            bg=self.bg_color,
            font=("Arial", 9, "italic"),
        )
        self.status_label.pack(side=tk.LEFT)

        # Progress bar for visual feedback during processing
        self.progress_bar = ttk.Progressbar(
            status_frame, mode="indeterminate", length=200
        )
        self.progress_bar.pack(side=tk.RIGHT, padx=10)

        # System message display
        self.system_message_var = tk.StringVar()
        self.system_message_label = tk.Label(
            status_frame,
            textvariable=self.system_message_var,
            fg="blue",
            bg=self.bg_color,
            font=("Arial", 9),
        )
        self.system_message_label.pack(side=tk.LEFT, padx=20)

    def display_message(self, message):
        """
        Displays a message in the conversation history area.
        """
        self.history_display.config(state="normal")
        self.history_display.insert(tk.END, message)
        self.history_display.yview(tk.END)  # Auto-scroll to the bottom
        self.history_display.config(state="disabled")

    def display_system_message(self, message):
        """
        Displays a system message in the status area.
        """
        self.system_message_var.set(message)

    def _setup_settings_button(self):
        """
        Adds a settings button to the title area for configuring the LLM model.
        """
        # Find the title frame to add the settings button
        title_frame = None
        for child in self.top_frame.winfo_children():
            if isinstance(child, tk.Frame):
                title_frame = child
                break

        if not title_frame:
            # If we can't find the title frame, create a new one
            title_frame = tk.Frame(self.top_frame, bg=self.bg_color)
            title_frame.pack(fill=tk.X)

        # Create settings button
        self.settings_button = tk.Button(
            title_frame,
            text="⚙️ Settings",
            command=self._show_settings_dialog,
            bg=self.bg_color,
            fg=self.accent_color,
            padx=5,
            pady=2,
            relief=tk.GROOVE,
        )
        self.settings_button.pack(side=tk.RIGHT, padx=10, pady=5)

    def _show_settings_dialog(self):
        """
        Display a dialog for configuring LLM settings (model type, API key, etc).
        """
        settings_dialog = tk.Toplevel(self)
        settings_dialog.title("LLM Settings")
        settings_dialog.geometry("500x400")
        settings_dialog.transient(self)  # Make dialog modal
        settings_dialog.grab_set()
        settings_dialog.configure(bg=self.bg_color)

        # Model Type Selection
        model_type_frame = tk.LabelFrame(
            settings_dialog, text="Model Type", padx=10, pady=10, bg=self.bg_color
        )
        model_type_frame.pack(fill=tk.X, padx=10, pady=10)

        # Radio buttons for model type
        openai_radio = tk.Radiobutton(
            model_type_frame,
            text="OpenAI API",
            variable=self.llm_model_type,
            value="openai",
            bg=self.bg_color,
        )
        openai_radio.pack(anchor=tk.W)

        mock_radio = tk.Radiobutton(
            model_type_frame,
            text="Mock (No API required)",
            variable=self.llm_model_type,
            value="mock",
            bg=self.bg_color,
        )
        mock_radio.pack(anchor=tk.W)

        # OpenAI Settings Frame (only visible when OpenAI is selected)
        openai_frame = tk.LabelFrame(
            settings_dialog, text="OpenAI Settings", padx=10, pady=10, bg=self.bg_color
        )
        openai_frame.pack(fill=tk.X, padx=10, pady=10)

        # OpenAI API Key
        api_key_frame = tk.Frame(openai_frame, bg=self.bg_color)
        api_key_frame.pack(fill=tk.X, pady=5)

        tk.Label(api_key_frame, text="API Key:", bg=self.bg_color).pack(
            side=tk.LEFT, padx=(0, 5)
        )

        # Create variable for API key
        self.api_key_var = tk.StringVar(value=os.environ.get("OPENAI_API_KEY", ""))
        api_key_entry = tk.Entry(
            api_key_frame, textvariable=self.api_key_var, width=40, show="*"
        )
        api_key_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # Toggle button to show/hide API key
        self.show_key = tk.BooleanVar(value=False)

        def toggle_api_key_visibility():
            if self.show_key.get():
                api_key_entry.config(show="")
            else:
                api_key_entry.config(show="*")

        show_key_check = tk.Checkbutton(
            api_key_frame,
            text="Show",
            variable=self.show_key,
            command=toggle_api_key_visibility,
            bg=self.bg_color,
        )
        show_key_check.pack(side=tk.RIGHT)

        # OpenAI Model Selection
        model_frame = tk.Frame(openai_frame, bg=self.bg_color)
        model_frame.pack(fill=tk.X, pady=5)

        tk.Label(model_frame, text="Model:", bg=self.bg_color).pack(
            side=tk.LEFT, padx=(0, 5)
        )

        model_choices = ["gpt-4-turbo", "gpt-4o", "gpt-3.5-turbo"]
        model_dropdown = ttk.Combobox(
            model_frame,
            textvariable=self.llm_model_name,
            values=model_choices,
            width=20,
        )
        model_dropdown.pack(side=tk.LEFT, padx=5)

        # Cost Estimation Frame
        cost_frame = tk.LabelFrame(
            openai_frame, text="Estimated Costs", padx=10, pady=10, bg=self.bg_color
        )
        cost_frame.pack(fill=tk.X, pady=10)

        tk.Label(
            cost_frame,
            text="GPT-4 Turbo: $0.01/1K input, $0.03/1K output",
            bg=self.bg_color,
        ).pack(anchor=tk.W)
        tk.Label(
            cost_frame, text="GPT-4o: $0.01/1K input, $0.03/1K output", bg=self.bg_color
        ).pack(anchor=tk.W)
        tk.Label(
            cost_frame,
            text="GPT-3.5 Turbo: $0.0005/1K input, $0.0015/1K output",
            bg=self.bg_color,
        ).pack(anchor=tk.W)

        # Buttons Frame for Settings Dialog
        button_frame = tk.Frame(settings_dialog, bg=self.bg_color)
        button_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=10)

        # Save settings button
        save_button = tk.Button(
            button_frame,
            text="Save Settings",
            command=lambda: self._save_settings(settings_dialog),
            bg=self.accent_color,
            fg="white",
            padx=10,
        )
        save_button.pack(side=tk.RIGHT, padx=5)

        # Cancel button
        cancel_button = tk.Button(
            button_frame,
            text="Cancel",
            command=settings_dialog.destroy,
            bg=self.bg_color,
            padx=10,
        )
        cancel_button.pack(side=tk.RIGHT, padx=5)

        # Update visibility based on current model type
        def update_frame_visibility(*args):
            if self.llm_model_type.get() == "openai":
                openai_frame.pack(fill=tk.X, padx=10, pady=10)
            else:
                openai_frame.pack_forget()

        # Set up trace to track changes to model type
        self.llm_model_type.trace_add("write", update_frame_visibility)

        # Initial visibility setup
        update_frame_visibility()

        # Set dialog position relative to main window
        settings_dialog.update_idletasks()
        x = (
            self.winfo_rootx()
            + (self.winfo_width() - settings_dialog.winfo_width()) // 2
        )
        y = (
            self.winfo_rooty()
            + (self.winfo_height() - settings_dialog.winfo_height()) // 2
        )
        settings_dialog.geometry(f"+{x}+{y}")

    def _save_settings(self, dialog):
        """
        Save settings from the dialog and update the LLM model.

        Args:
            dialog: The settings dialog to close after saving
        """
        model_type = self.llm_model_type.get()
        model_name = self.llm_model_name.get()
        api_key = self.api_key_var.get()

        # Update environment variable for API key
        if api_key:
            os.environ["OPENAI_API_KEY"] = api_key

        # Update the LLM model in the conversational core
        try:
            # Update the model in the ConversationalCore
            from chatmode.llm_integration.llm_model import LLMModel

            new_model = LLMModel(
                model_name=model_name, model_type=model_type, api_key=api_key
            )

            # Replace the model in the conversational core
            self.conversational_core.llm_model = new_model

            # Show success message
            self.display_system_message(
                f"LLM settings updated: {model_type} model {model_name}"
            )

            # Close the dialog
            dialog.destroy()
        except Exception as e:
            # Show error message
            import tkinter.messagebox as messagebox

            messagebox.showerror("Error", f"Failed to update model settings: {str(e)}")

    def display_structured_output(self, output_type, data):
        """
        Displays structured data in the appropriate tab.

        Args:
            output_type (str): Type of output ('forecast', 'simulation', 'memory', 'symbolic')
            data (dict/list/str): The data to display
        """
        # Select the appropriate output area based on type
        if output_type == "forecast":
            output_area = self.forecast_output
            self.output_notebook.select(0)  # Select forecast tab
        elif output_type == "simulation":
            output_area = self.simulation_output
            self.output_notebook.select(1)  # Select simulation tab
        elif output_type == "memory":
            output_area = self.memory_output
            self.output_notebook.select(2)  # Select memory tab
        elif output_type == "symbolic":
            output_area = self.symbolic_output
            self.output_notebook.select(3)  # Select symbolic tab
        else:
            # Default to forecast if type not recognized
            output_area = self.forecast_output
            self.output_notebook.select(0)

        # Format data for display
        if isinstance(data, (dict, list)):
            formatted_data = json.dumps(data, indent=2)
        else:
            formatted_data = str(data)

        # Update the output area
        output_area.config(state="normal")
        output_area.delete(1.0, tk.END)
        output_area.insert(tk.END, formatted_data)
        output_area.config(state="disabled")

    def _clear_history(self):
        """Clears the conversation history"""
        self.history_display.config(state="normal")
        self.history_display.delete(1.0, tk.END)
        self.history_display.config(state="disabled")
        self.display_message(
            "Pulse AI: Conversation history cleared. How can I help you?\n"
        )

    def send_message_event(self, event):
        """
        Handles sending message when Enter key is pressed.
        """
        self.send_message()

    def _get_parameters_from_ui(self):
        """
        Gets parameters from UI based on current command type.

        Returns:
            dict: Parameters extracted from UI
        """
        command = self.command_var.get()
        parameters = {}

        if command == "Run Simulation" and hasattr(self, "simulation_params"):
            # Simple parsing - in real app would need more structured input
            try:
                parameters = json.loads(self.simulation_params.get())
            except json.JSONDecodeError as _e:
                parameters = {"simulation_text": self.simulation_params.get()}

        elif command == "Get Data" and hasattr(self, "data_symbol"):
            parameters = {
                "symbol": self.data_symbol.get(),
                "data_type": self.data_type.get(),
                "date_range": self.date_range.get().split(",")
                if self.date_range.get()
                else None,
            }

        elif command == "Get Forecast" and hasattr(self, "forecast_symbol"):
            parameters = {"symbol": self.forecast_symbol.get()}

        elif command == "Get Trust Score" and hasattr(self, "trust_item"):
            parameters = {"item": self.trust_item.get()}

        elif command == "Query Memory" and hasattr(self, "query_text"):
            parameters = {"query": self.query_text.get()}

        elif command == "Query Symbolic System" and hasattr(self, "query_text"):
            parameters = {"query": self.query_text.get()}

        return parameters

    def send_message(self):
        """
        Sends the user's message to the conversational core and displays the response.
        Enhanced to handle different command types and show appropriate output.
        """
        # Get text from input field
        user_text = self.user_input.get().strip()

        # If empty and not using a structured command, do nothing
        if not user_text and self.command_var.get() == "General Query":
            return

        # Get command type
        command_type = self.command_var.get()

        # Get parameters if applicable
        parameters = self._get_parameters_from_ui()

        # Map UI command to intent
        command_to_intent = {
            "General Query": "general_query",
            "Run Simulation": "run_simulation",
            "Get Data": "get_data",
            "Get Forecast": "get_forecast",
            "Get Trust Score": "get_trust_score",
            "Query Memory": "query_memory",
            "Query Symbolic System": "query_symbolic_system",
            # Add recursive learning command mappings
            "Start Recursive Learning": "start_recursive_learning",
            "Stop Recursive Learning": "stop_recursive_learning",
            "Get Recursive Learning Status": "get_recursive_learning_status",
            "Configure Recursive Learning": "configure_recursive_learning",
            "Get Recursive Learning Metrics": "get_recursive_learning_metrics",
        }

        intent = command_to_intent.get(command_type, "general_query")

        # Modify user_text to reflect command if needed
        if command_type != "General Query" and not user_text:
            user_text = f"{command_type}: {json.dumps(parameters)}"

        # Display user message in conversation history
        self.display_message(f"User: {user_text}\n")
        self.user_input.delete(0, tk.END)  # Clear input field

        # Show processing state
        self.processing = True
        self.send_button.config(
            state="disabled"
        )  # Disable send button while processing
        self.status_var.set("Processing...")
        self.status_label.config(fg="orange")
        self.progress_bar.start(10)  # Start progress bar animation

        # Process the query in a separate thread to keep the GUI responsive
        threading.Thread(
            target=self._process_query_in_thread, args=(user_text, intent, parameters)
        ).start()

    def _process_query_in_thread(
        self, user_text, intent="general_query", parameters=None
    ):
        """
        Processes the query using the conversational core in a separate thread.
        Enhanced to handle different output types based on intent.
        """
        try:
            # Update UI to show processing
            self.after(
                0,
                lambda: self.display_system_message(f"Processing {intent} request..."),
            )

            # Use intent-specific parameters if provided
            if parameters is None:
                parameters = {}

            # Call the processing logic for the query
            response, retrieved_snippets = self.conversational_core.process_query(
                user_text
            )

            # Display the response in the main GUI thread
            self.after(0, lambda: self.display_message(f"Pulse AI: {response}\n"))

            # Handle different output types based on intent
            if intent == "run_simulation":
                # Assuming the response contains simulation results
                self.after(
                    0,
                    lambda: self.display_structured_output(
                        "simulation", {"response": response, "parameters": parameters}
                    ),
                )

            elif intent == "get_forecast":
                self.after(
                    0,
                    lambda: self.display_structured_output(
                        "forecast", {"response": response, "parameters": parameters}
                    ),
                )

            elif intent == "query_memory":
                self.after(
                    0,
                    lambda: self.display_structured_output(
                        "memory", {"response": response, "parameters": parameters}
                    ),
                )

            elif intent == "query_symbolic_system":
                self.after(
                    0,
                    lambda: self.display_structured_output(
                        "symbolic", {"response": response, "parameters": parameters}
                    ),
                )

            # Optionally display retrieved snippets
            if retrieved_snippets:
                # Format snippets for display - handle both string and dictionary formats
                snippet_lines = []
                for s in retrieved_snippets:
                    if isinstance(s, dict):
                        # New format: dictionary with text and metadata
                        text = s.get("text", "")[:300] + "..."
                        metadata = s.get("metadata", {})
                        file_path = metadata.get("file_path", "Unknown")
                        snippet_lines.append(
                            f"--- Snippet from {file_path} ---\n{text}"
                        )
                    else:
                        # Old format: simple string
                        snippet_lines.append(f"--- Snippet ---\n{str(s)[:300]}...")

                snippet_text = "\n\n".join(snippet_lines)
                self.after(
                    0,
                    lambda: self.display_message(
                        f"Retrieved Snippets:\n{snippet_text}\n"
                    ),
                )

            # Update status to show success
            self.after(0, lambda: self.status_var.set("Ready"))
            self.after(0, lambda: self.status_label.config(fg="green"))
            self.after(
                0, lambda: self.display_system_message("Query processed successfully.")
            )

        except Exception as e:
            # Display error in conversation and status area
            self.after(
                0, lambda error_msg=str(e): self.display_message(f"Error processing query: {error_msg}\n")
            )
            self.after(0, lambda: self.status_var.set("Error"))
            self.after(0, lambda: self.status_label.config(fg="red"))
            self.after(0, lambda error_msg=str(e): self.display_system_message(f"Error: {error_msg}"))
            print(f"Error processing query: {str(e)}")

        finally:
            # Stop progress bar and re-enable the send button
            self.after(0, lambda: self.progress_bar.stop())
            self.after(0, lambda: self.send_button.config(state="normal"))
            self.processing = False

    # ------ Recursive Learning Control Methods ------

    def _start_learning_cycle(self):
        """
        Start a new recursive learning cycle based on UI settings.
        """
        # Get variables from entry field
        variables_text = self.learning_variables.get().strip()
        variables = [v.strip() for v in variables_text.split(",") if v.strip()]

        # Get batch days
        try:
            batch_days = int(self.batch_days.get().strip())
        except ValueError:
            batch_days = 30  # Default

        # Construct the command
        command_text = f"start recursive learning with variables={variables_text}, batch_size_days={batch_days}"

        # Display as user message and process it
        self.display_message(f"User: {command_text}\n")

        # Process the command
        self._process_recursive_learning_command(
            "start_recursive_learning",
            {"variables": variables, "batch_size_days": batch_days},
        )

    def _stop_learning_cycle(self):
        """
        Stop a recursive learning cycle.
        """
        # Get cycle ID from entry field
        cycle_id = self.cycle_id.get().strip()

        # Construct the command
        command_text = (
            f"stop recursive learning cycle {cycle_id if cycle_id else 'all'}"
        )

        # Display as user message and process it
        self.display_message(f"User: {command_text}\n")

        # Process the command
        self._process_recursive_learning_command(
            "stop_recursive_learning", {"cycle_id": cycle_id if cycle_id else None}
        )

    def _refresh_learning_status(self):
        """
        Refresh the recursive learning status display.
        """
        # Construct the command
        command_text = "get recursive learning status"

        # Display as user message and process it
        self.display_message(f"User: {command_text}\n")

        # Process the command
        self._process_recursive_learning_command("get_recursive_learning_status", {})

    def _process_recursive_learning_command(self, intent, parameters):
        """
        Process a recursive learning command using the conversational core.

        Args:
            intent (str): The intent name
            parameters (dict): Parameters for the command
        """
        # Show processing state
        self.processing = True
        self.send_button.config(state="disabled")
        self.status_var.set("Processing Recursive Learning Command...")
        self.status_label.config(fg="orange")
        self.progress_bar.start(10)

        # Process in a separate thread
        threading.Thread(
            target=self._execute_recursive_learning_command, args=(intent, parameters)
        ).start()

    def _execute_recursive_learning_command(self, intent, parameters):
        """
        Execute a recursive learning command in a separate thread.

        Args:
            intent (str): The intent name
            parameters (dict): Parameters for the command
        """
        try:
            # Execute the appropriate tool based on intent
            tool = self.conversational_core.tool_registry.get_tool(intent)
            if tool:
                result = tool.execute(parameters)

                # Display result
                if result.get("status") == "success":
                    # Extract the actual result
                    data = result.get("result", {})

                    # Update UI with response
                    self.after(
                        0,
                        lambda: self.display_message(
                            f"Pulse AI: Successfully executed {intent}.\n"
                        ),
                    )

                    # Update status display
                    self.after(0, lambda: self._update_learning_status_display(data))

                    # Update the output area
                    self.after(
                        0,
                        lambda: self.display_structured_output(
                            "recursive_learning", data
                        ),
                    )

                    # Select the recursive learning tab
                    self.after(
                        0, lambda: self.output_notebook.select(4)
                    )  # Index 4 is the recursive learning tab
                else:
                    # Display error
                    error = result.get("error", "Unknown error")
                    self.after(
                        0,
                        lambda: self.display_message(
                            f"Error executing {intent}: {error}\n"
                        ),
                    )
            else:
                self.after(
                    0,
                    lambda: self.display_message(
                        f"Error: No tool found for intent '{intent}'\n"
                    ),
                )

        except Exception as e:
            self.after(
                0,
                lambda msg=str(e): self.display_message(
                    f"Error processing recursive learning command: {msg}\n"
                ),
            )

        finally:
            # Reset UI state
            self.after(0, lambda: self.progress_bar.stop())
            self.after(0, lambda: self.send_button.config(state="normal"))
            self.after(0, lambda: self.status_var.set("Ready"))
            self.after(0, lambda: self.status_label.config(fg="green"))
            self.processing = False

    def _update_learning_status_display(self, data):
        """
        Update the recursive learning status display with data.

        Args:
            data (dict): Data from the recursive learning command
        """
        # Clear current status
        self.learning_status.config(state="normal")
        self.learning_status.delete(1.0, tk.END)

        # Format the status information
        if data.get("status") == "started":
            # New cycle started
            self.learning_status.insert(tk.END, "Started new learning cycle:\n")
            self.learning_status.insert(tk.END, f"  ID: {data.get('cycle_id')}\n")
            self.learning_status.insert(
                tk.END, f"  Variables: {', '.join(data.get('variables', []))}\n"
            )
            self.learning_status.insert(
                tk.END,
                f"  Period: {data.get('time_period', {}).get('start')} to {data.get('time_period', {}).get('end')}\n",
            )
            self.learning_status.insert(
                tk.END, f"  Batches: {data.get('batches', {}).get('total', 0)}\n"
            )

            # Auto-fill the cycle ID field
            self.cycle_id.delete(0, tk.END)
            self.cycle_id.insert(0, data.get("cycle_id", ""))

        elif "cycles" in data:
            # Status of all cycles
            cycles = data.get("cycles", [])
            if not cycles:
                self.learning_status.insert(
                    tk.END, "No active learning cycles found.\n"
                )
            else:
                self.learning_status.insert(
                    tk.END, f"Active learning cycles: {len(cycles)}\n\n"
                )
                for cycle in cycles:
                    self.learning_status.insert(
                        tk.END, f"Cycle ID: {cycle.get('cycle_id')}\n"
                    )
                    self.learning_status.insert(
                        tk.END, f"  Status: {cycle.get('status', 'unknown')}\n"
                    )
                    self.learning_status.insert(
                        tk.END,
                        f"  Progress: {cycle.get('progress', {}).get('percentage', '0%')}\n",
                    )
                    self.learning_status.insert(
                        tk.END, f"  Start time: {cycle.get('start_time')}\n"
                    )
                    self.learning_status.insert(tk.END, "\n")

        elif "cycle_id" in data:
            # Single cycle status
            self.learning_status.insert(tk.END, f"Cycle ID: {data.get('cycle_id')}\n")
            self.learning_status.insert(
                tk.END, f"Status: {data.get('status', 'unknown')}\n"
            )

            progress = data.get("progress", {})
            if progress:
                self.learning_status.insert(
                    tk.END, f"Progress: {progress.get('percentage', '0%')} "
                )
                self.learning_status.insert(
                    tk.END,
                    f"({progress.get('completed_batches', 0)}/{progress.get('total_batches', 0)} batches)\n",
                )

            performance = data.get("performance", {})
            if performance:
                self.learning_status.insert(tk.END, "Performance metrics:\n")
                for key, value in performance.items():
                    self.learning_status.insert(tk.END, f"  {key}: {value}\n")

        # Reset state
        self.learning_status.config(state="disabled")


if __name__ == "__main__":
    # To run this GUI, you need to have built the vector store first
    # by running chatmode/vector_store/build_vector_store.py

    app = ConversationalGUI()
    app.mainloop()
