REM pulse_ui_start.bat
REM Launches the Pulse CLI UI with hook help on Windows.
REM Usage: Double-click or run from command prompt. Requires Python in PATH.
@echo off
echo 🚀 Launching Pulse CLI UI...
python pulse_ui_shell.py --help_hooks
if %errorlevel% neq 0 echo [ERROR] Python not found or script failed.
pause