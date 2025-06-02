#!/usr/bin/env python
"""
Pulse GUI Launcher
This script launches the Pulse Desktop UI along with the required API server
"""

import os
import sys
import time
import subprocess
import tkinter as tk
import logging
from tkinter import messagebox
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("pulse-launcher")


def check_dependencies():
    """Check if all required dependencies are installed."""
    required_packages = ["flask", "requests", "matplotlib", "numpy", "pandas"]

    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)

    if missing_packages:
        logger.warning(f"Missing dependencies: {', '.join(missing_packages)}")
        return False, missing_packages

    return True, []


def install_dependencies(packages):
    """Install missing dependencies."""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install"] + packages)
        return True
    except subprocess.CalledProcessError:
        return False


def start_api_server():
    """Start the Pulse API server in a separate process."""
    api_server_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "../api/server.py"
    )

    try:
        if os.name == "nt":  # Windows
            # Use pythonw to avoid a console window
            process = subprocess.Popen(
                [sys.executable, api_server_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
        else:  # Unix/Linux/Mac
            process = subprocess.Popen(
                [sys.executable, api_server_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

        logger.info("API server started")
        return process
    except Exception as e:
        logger.error(f"Failed to start API server: {e}")
        return None


def wait_for_api_server(timeout=10):
    """Wait for the API server to become available."""
    url = "http://127.0.0.1:5002/api/status"
    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            response = requests.get(url, timeout=2)
            if (
                response.status_code == 200
                and response.json().get("status") == "online"
            ):
                logger.info("API server is online")
                return True
        except requests.RequestException:
            logger.info("API server not yet available...")

        time.sleep(1)

    logger.warning(f"API server did not become available within {timeout} seconds")
    return False


def start_gui():
    """Start the Pulse GUI."""
    gui_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "../pulse_desktop/tkinter_ui.py"
    )

    try:
        subprocess.call([sys.executable, gui_path])
        logger.info("GUI process exited")
    except Exception as e:
        logger.error(f"Failed to start GUI: {e}")


def show_error_dialog(message):
    """Show an error dialog to the user."""
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    messagebox.showerror("Pulse GUI Launcher Error", message)
    root.destroy()


def main():
    """Main entry point."""
    print("Starting Pulse Desktop GUI...")

    # Check dependencies
    deps_ok, missing_packages = check_dependencies()
    if not deps_ok:
        message = f"Missing dependencies: {
            ', '.join(missing_packages)}\n\nWould you like to install them now?"
        root = tk.Tk()
        root.withdraw()
        install = messagebox.askyesno("Missing Dependencies", message)
        root.destroy()

        if install:
            print("Installing missing dependencies...")
            if not install_dependencies(missing_packages):
                show_error_dialog(
                    "Failed to install dependencies. Please install them manually and try again."
                )
                return
        else:
            print("Cannot continue without required dependencies.")
            return

    # Start the API server
    api_process = start_api_server()
    if not api_process:
        show_error_dialog(
            "Failed to start API server. Please check the logs for details."
        )
        return

    # Wait for the API server to become available
    if not wait_for_api_server(timeout=10):
        logger.warning(
            "API server may not be fully operational, but will continue starting the GUI"
        )

    # Start the GUI (blocking call)
    start_gui()

    # Once GUI exits, terminate the API server
    logger.info("Terminating API server...")
    try:
        api_process.terminate()
        api_process.wait(timeout=5)
    except Exception as e:
        logger.error(f"Error terminating API server: {e}")
        # Try to kill it forcibly if termination fails
        try:
            api_process.kill()
        except Exception:
            pass


if __name__ == "__main__":
    main()
