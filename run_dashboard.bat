@echo off
echo Starting Polymarket Insider...

start "Polymarket Bot" cmd /k "python bot.py"
start "Web Dashboard" cmd /k "python server.py"

echo.
echo Both services started!
echo Open http://localhost:8000 in your browser.
echo.
pause
