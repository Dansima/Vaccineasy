# Vaccineasy — Launcher Script
# Run this from the project root to start the app.
# Usage: .\run.ps1

$env:PYTHONPATH = $PSScriptRoot
& "$PSScriptRoot\.venv\Scripts\streamlit.exe" run "$PSScriptRoot\app\main.py"
