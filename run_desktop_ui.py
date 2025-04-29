import webview
import threading
import sys
import os

# Import the Flask app object using a relative path
try:
    # Assuming run_desktop_ui.py is in the project root (one level above pulse_web_ui)
    from pulse_web_ui.app import app as flask_app
except ImportError as e:
    print(f"Error importing Flask app from pulse_web_ui.app: {e}")
    print("Ensure 'pulse_web_ui/app.py' exists and the script is run from the project root.")
    sys.exit(1)

# --- pywebview Configuration ---

# Define the target function for the webview thread
# pywebview needs the Flask app to be running when it starts.
# Although pywebview can start a Flask app, running it explicitly
# in a thread gives more control and clarity, especially if waitress
# is preferred or needed later.
# Note: For simplicity here, we let pywebview manage the Flask app directly.
# If using waitress was strictly required even with pywebview, you'd start
# waitress in a separate thread here *before* webview.start().

if __name__ == '__main__':
    # Create the pywebview window, passing the Flask app object directly
    # pywebview will handle starting a basic WSGI server for the Flask app.
    window_title = "Pulse Desktop UI"
    window = webview.create_window(window_title, flask_app)

    # Start the pywebview event loop (this also starts the Flask app's server)
    print(f"Starting {window_title}...")
    webview.start(debug=True) # Enable debug for more detailed output
    print(f"{window_title} closed.")