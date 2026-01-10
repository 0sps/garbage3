from polymarket_api import PolymarketAPI
import logging
import time
import csv
import os
from datetime import datetime, timedelta

# --- Configuration ---
BACKTEST_LIMIT = 100          # Markets to check
LARGE_TRADE_THRESHOLD = 50    # Min USD value (Lowered for testing)
HISTORY_LIMIT = 100           # Relaxed limit to find *something*
DATA_FILE = "all_trades.csv"

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def log_trade_to_csv(trade_data):
    # trade_data: [timestamp, market, outcome, price, size, value, user, user_trade_count, flag]
    # Ensure file exists
    file_exists = os.path.exists(DATA_FILE)
    with open(DATA_FILE, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['timestamp', 'market', 'outcome', 'price', 'size', 'value', 'user', 'user_trade_count', 'flag'])
        writer.writerow(trade_data)

def run_backtest():
    api = PolymarketAPI()
    logger.info("Starting Backtest (Last 7 Days)...")
    
    # Calculate cutoff
    cutoff_time = time.time() - (7 * 24 * 60 * 60)
    logger.info(f"Scanning for trades after: {datetime.fromtimestamp(cutoff_time)}")

    # Get closed AND active markets to be thorough
    markets = api.get_top_markets(limit=BACKTEST_LIMIT, active=True)
    # Also fetch some closed ones if needed, but active usually has the recent action
    
    logger.info(f"Scanning {len(markets)} markets...")
    
    suspicious_count = 0
    
    for market in markets:
        question = market.get('question')
        tokens = market.get('clobTokenIds', [])
        outcomes = market.get('outcomes', [])
        
        if not tokens: continue

        for idx, token_id in enumerate(tokens):
            outcome_label = outcomes[idx] if idx < len(outcomes) else "Unknown"
            
            # Fetch trades
            trades = api.get_market_trades(token_id)
            
            for trade in trades:
                ts = float(trade.get('timestamp', 0))
                if ts < cutoff_time:
                    continue # Skip old trades
                
                price = float(trade.get('price', 0))
                size = float(trade.get('size', 0))
                value = price * size
                
                if value > LARGE_TRADE_THRESHOLD:
                    # FIX: Use proxyWallet 
                    taker = trade.get('taker') or trade.get('taker_address') or trade.get('proxyWallet')
                    if not taker: continue
                    
                    # Analyze User
                    activity = api.get_user_activity(taker)
                    trade_count = len(activity)
                    
                    if trade_count <= HISTORY_LIMIT:
                        suspicious_count += 1
                        
                        flag = "HISTORICAL_INSIDER"
                        if price < 0.20:
                            flag = "HISTORICAL_CONTRARIAN"
                        
                        logger.info(f"🚨 {flag}: {question} ({outcome_label}) - ${value:.0f} by {taker[:6]}...")
                        
                        # Log to CSV for Dashboard
                        log_trade_to_csv([
                            ts,
                            question,
                            outcome_label,
                            price,
                            size,
                            value,
                            taker,
                            trade_count,
                            flag
                        ])
                        
    logger.info(f"\nBacktest Complete. Found {suspicious_count} suspicious trades.")
    logger.info(f"Results saved to {DATA_FILE} and should appear in Dashboard.")

if __name__ == "__main__":
    run_backtest()
