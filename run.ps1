# Vaccineasy — Launcher Script
# Run this from the project root to start the app.
# Usage: .\run.ps1

$env:PYTHONPATH = $PSScriptRoot
$ErrorActionPreference = 'Stop'
if (-not (Test-Path -LiteralPath "$PSScriptRoot\.venv\Scripts\streamlit.exe")) {
    throw 'Virtual environment missing. Run: python -m venv .venv, then .\.venv\Scripts\python.exe -m pip install -r requirements.txt'
}
Push-Location -LiteralPath $PSScriptRoot
try {
    & "$PSScriptRoot\.venv\Scripts\streamlit.exe" run "$PSScriptRoot\app\main.py"
} finally {
    Pop-Location
}
