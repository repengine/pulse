@echo off
echo Starting Pulse GUI...
python pulse_gui_launcher.py
if %errorlevel% neq 0 (
    echo Error starting Pulse GUI
    pause
)