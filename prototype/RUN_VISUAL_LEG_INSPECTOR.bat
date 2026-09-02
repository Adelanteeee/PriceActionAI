@echo off
setlocal
cd /d "%~dp0\.."

echo ============================================================
echo  PriceActionAI Parallel Visual Swing + Leg Inspector
echo  Locked engines remain unchanged. Manual visual review only.
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
echo MT5 must be OPEN and logged in before continuing.
echo Default run: XAUUSD_o / M15 / 1000 bars
echo.
python -m prototype.visual_leg_inspector --symbol XAUUSD_o --timeframe M15 --bars 1000
if errorlevel 1 goto :error

echo.
echo Inspector finished successfully.
pause
exit /b 0

:error
echo.
echo Inspector failed. Read the error message above.
pause
exit /b 1
