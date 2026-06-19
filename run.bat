@echo off
REM ParkPulse one-click launcher for Windows.
REM Creates a virtual env, installs deps, runs the pipeline, opens the demo.
setlocal
cd /d "%~dp0"

if not exist ".venv" (
  echo [setup] creating virtual environment...
  python -m venv .venv
)
call .venv\Scripts\activate.bat

echo [setup] installing dependencies...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo [run] building results (python run_all.py)...
python run_all.py

echo [run] launching demo (close this window or press Ctrl+C to stop)...
streamlit run app.py

endlocal
