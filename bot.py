from polymarket_api import PolymarketAPI
import logging
import time
import csv
import os

# --- Configuration ---
LARGE_TRADE_THRESHOLD = 400
MAX_ACCOUNT_HISTORY = 10
CHECK_INTERVAL = 30
TOP_MARKETS_COUNT = 50
LOG_FILE = "bot.log"
DATA_FILE = "all_trades.csv"

# Logging Setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def init_csv():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['timestamp', 'market', 'outcome', 'price', 'size', 'value', 'user', 'user_trade_count', 'flag'])

def log_trade_to_csv(trade_data):
    with open(DATA_FILE, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(trade_data)

def analyze_user(api, user_address):
    activity = api.get_user_activity(user_address)
    trade_count = len(activity)
    return {
        "is_fresh": trade_count <= MAX_ACCOUNT_HISTORY,
        "trade_count": trade_count
    }

def run_bot():
    api = PolymarketAPI()
    init_csv()
    logger.info(f"Starting Bot. Logging all trades > ${LARGE_TRADE_THRESHOLD} to {DATA_FILE}")
    
    seen_trade_ids = set()
    
    while True:
        try:
            markets = api.get_top_markets(limit=TOP_MARKETS_COUNT, active=True)
            logger.info(f"Scanning {len(markets)} active markets...")
            
            for market in markets:
                market_question = market.get('question', 'Unknown')
                tokens = market.get('clobTokenIds', [])
                outcomes = market.get('outcomes', [])
                
                if not tokens or len(tokens) != len(outcomes):
                    continue

                for idx, token_id in enumerate(tokens):
                    outcome = outcomes[idx] if idx < len(outcomes) else "Unknown"
                    trades = api.get_market_trades(token_id)
                    
                    for trade in trades:
                        trade_id = trade.get('id') or f"{trade.get('transactionHash')}_{trade.get('timestamp')}"
                        if trade_id in seen_trade_ids:
                            continue
                        seen_trade_ids.add(trade_id)
                        
                        price = float(trade.get('price', 0))
                        size = float(trade.get('size', 0))
                        value = price * size
                        
                        # Log EVERY trade as requested
                        taker = trade.get('taker') or trade.get('taker_address') or trade.get('proxyWallet')
                        user_stats = {"trade_count": -1} # Default if not analyzed
                        flag = ""
                        
                        # Deep analysis ONLY on LARGE trades to avoid API bans
                        if value > LARGE_TRADE_THRESHOLD and taker:
                            user_analysis = analyze_user(api, taker)
                            user_stats = user_analysis
                            
                            if user_analysis['is_fresh']:
                                flag = "FRESH_INSIDER"
                                if price < 0.20:
                                    flag = "CONTRARIAN_INSIDER"
                                
                                logger.warning(
                                    f"🚨 {flag} 🚨\n"
                                    f"Market: {market_question} | {outcome}\n"
                                    f"Bet: ${value:.0f} @ {price:.2f}\n"
                                    f"User: {taker} ({user_analysis['trade_count']} history)"
                                )
                        
                        # Write to CSV
                        log_trade_to_csv([
                            time.time(),
                            market_question,
                            outcome,
                            price,
                            size,
                            value,
                            taker,
                            user_stats['trade_count'],
                            flag
                        ])

            time.sleep(CHECK_INTERVAL)
            
        except KeyboardInterrupt:
            logger.info("Bot stopped by user.")
            break
        except Exception as e:
            logger.error(f"Error: {e}")
            time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    run_bot()
