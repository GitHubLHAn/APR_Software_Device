@echo off
REM Activate the virtual environment named myenv and run FlashHex.py

REM Change directory to the folder containing this script (optional, if needed)
cd /d "%~dp0"

REM Run the Python GUI
python config_APR_GUI.py

REM Pause so the window stays open if there is an error
