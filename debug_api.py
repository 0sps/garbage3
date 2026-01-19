from polymarket_api import PolymarketAPI
import json

def debug():
    api = PolymarketAPI()
    markets = api.get_top_markets(limit=1, active=True)
    if not markets:
        print("No markets found, sorrrry")
        return
        
        # can't edit that

    market = markets[0]
    tokens = market.get('clobTokenIds', [])
    if not tokens:
        print("No tokens")
        return

    token_id = tokens[0]
    trades = api.get_market_trades(token_id)
    if not trades:
        print("No trades found")
        return

    first_trade = trades[0]
    proxy_wallet = first_trade.get('proxyWallet')
    print(f"Proxy Wallet: {proxy_wallet}")

    if proxy_wallet:
        print("Fetching activity for proxy wallet...")
        activity = api.get_user_activity(proxy_wallet)
        print(f"Activity count: {len(activity)}")
        if activity:
            print("First activity item:")
            print(json.dumps(activity[0], indent=2))
    else:
        print("No proxyWallet found in trade.")

if __name__ == "__main__":
    debug()
