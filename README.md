# Polymarket Insider Trade Detector

This bot monitors Polymarket for large trades made by fresh accounts (potential insider activity). It also includes a backtesting script to analyze past markets.

## Prerequisites

**You must have Python installed.**
If you haven't installed it, download it from [python.org](https://www.python.org/downloads/).
Ensure you check "Add Python to PATH" during installation.

## Setup

1. Open a terminal in this directory:
   ```powershell
   cd c:\Users\spsfu\polymarketPRoject
   ```

2. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```

## Usage

### Live Monitor
Run the bot to start scanning active markets in real-time:
```powershell
python bot.py
```
*The bot will log "POTENTIAL INSIDER TRADE" alerts to the console and `bot.log`.*

### Backtesting
Run the backtester to analyze closed markets:
```powershell
python backtest.py
```

## Configuration

You can adjust thresholds in `bot.py` and `backtest.py`:
- `LARGE_TRADE_THRESHOLD`: Minimum USD value to consider.
- `MAX_ACCOUNT_HISTORY` / `HISTORY_LIMIT`: Max number of past trades for an account to be considered "fresh".
