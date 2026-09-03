@echo off
setlocal
cd /d "%~dp0\.."

echo ============================================================
echo  PriceActionAI Parallel Trend Leg Visual Validator v1
echo  Manual evidence review only - no automatic Trend label
echo ============================================================

echo.
echo Checking Python dependencies...
python -c "import pandas, plotly, MetaTrader5" >nul 2>&1
if errorlevel 1 (
  echo Installing required Python packages...
  python -m pip install pandas plotly MetaTrader5
  if errorlevel 1 goto :error
)

echo.
echo MT5 must be OPEN and logged in.
echo Running XAUUSD_o on M5 M15 M30 H1...
echo.
python -m prototype.trend_leg_visual_validator --symbol XAUUSD_o --bars 1200 --timeframes M5 M15 M30 H1
if errorlevel 1 goto :error

echo.
echo Trend Leg Visual Validator finished successfully.
pause
exit /b 0

:error
echo.
echo Trend Leg Visual Validator failed. Read the error above.
pause
exit /b 1
