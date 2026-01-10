#!/usr/bin/env python3
"""
Market Detail Lookup - Use Market IDs to find trades, prices, and details
"""

import requests
import json
from typing import Dict, List, Optional

CLOB_API = "https://clob.polymarket.com"
POLYMARKET_WEB = "https://polymarket.com"

class MarketDetailLookup:
    """Look up detailed information about markets using their IDs"""
    
    def __init__(self):
        self.session = requests.Session()
    
    def get_market_details(self, market_id: str) -> Optional[Dict]:
        """Get full details about a market"""
        print(f"\n🔍 Looking up market details for: {market_id}")
        
        try:
            response = self.session.get(
                f"{CLOB_API}/market/{market_id}",
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ Error fetching market details: {e}")
            return None
    
    def get_orderbook(self, market_id: str) -> Optional[Dict]:
        """Get current order book for a market"""
        print(f"📊 Fetching order book...")
        
        try:
            response = self.session.get(
                f"{CLOB_API}/orderbook/{market_id}",
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"⚠️  Orderbook not available: {e}")
            return None
    
    def get_market_trades(self, market_id: str, limit: int = 100) -> Optional[List[Dict]]:
        """Try to get recent trades for a market"""
        print(f"💱 Fetching recent trades...")
        
        try:
            response = self.session.get(
                f"{CLOB_API}/trades",
                params={"market": market_id, "limit": limit},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and 'data' in data:
                return data.get('data', [])
            return None
        except Exception as e:
            print(f"⚠️  Trades endpoint not accessible: {e}")
            return None
    
    def print_market_details(self, market: Dict):
        """Pretty print market details"""
        print("\n" + "="*80)
        print(f"📌 MARKET: {market.get('title', market.get('question', 'Unknown'))}")
        print("="*80)
        
        print(f"\nBasic Info:")
        print(f"  Market ID: {market.get('id', market.get('condition_id', 'Unknown'))}")
        print(f"  Status: {'OPEN' if market.get('active') else 'CLOSED'}")
        print(f"  Accepting Orders: {market.get('accepting_orders', False)}")
        
        # Token/outcome information
        tokens = market.get('tokens', [])
        if tokens and len(tokens) >= 2:
            print(f"\n💰 Current Odds:")
            for i, token in enumerate(tokens[:4]):  # Show up to 4 outcomes
                outcome = token.get('outcome', 'Unknown')
                price = float(token.get('price', 0))
                print(f"  {i+1}. {outcome}: {price*100:.2f}%")
        
        # Market details
        print(f"\nMarket Details:")
        print(f"  Volume (24h): ${market.get('volume24h', 'Unknown')}")
        print(f"  Liquidity: ${market.get('liquidity', 'Unknown')}")
        
        # Resolution info
        if market.get('resolvedBy'):
            print(f"\n✅ RESOLVED: {market.get('resolvedBy')}")
        else:
            print(f"\n⏰ End Date: {market.get('end_date_iso', 'Unknown')}")
        
        # Direct link
        slug = market.get('market_slug')
        if slug:
            web_url = f"{POLYMARKET_WEB}/market/{slug}"
            print(f"\n🔗 View on Polymarket: {web_url}")
    
    def analyze_market(self, market_id: str):
        """Full analysis of a market"""
        market = self.get_market_details(market_id)
        
        if not market:
            print(f"❌ Could not fetch market {market_id}")
            return
        
        self.print_market_details(market)
        
        # Try to get orderbook
        orderbook = self.get_orderbook(market_id)
        if orderbook:
            print(f"\n📈 Orderbook Data:")
            print(json.dumps(orderbook, indent=2)[:500] + "...")
        
        # Try to get trades
        trades = self.get_market_trades(market_id)
        if trades:
            print(f"\n💱 Recent Trades ({len(trades)} trades):")
            for i, trade in enumerate(trades[:5]):  # Show first 5
                print(f"  Trade {i+1}: {trade}")
        
        return market


def main():
    """Example usage"""
    lookup = MarketDetailLookup()
    
    # Example: Use one of the market IDs from the scan
    market_id = "0x5eed579ff6763914d78a966c83473ba2485ac8910d0a0914eef6d9fcb33085de"
    
    print("\n" + "="*80)
    print("🎯 MARKET DETAIL LOOKUP")
    print("="*80)
    print(f"\nThis tool lets you:")
    print("  1. Get full market details (odds, volume, status)")
    print("  2. View current order book")
    print("  3. See recent trades")
    print("  4. Get direct link to market on Polymarket UI")
    
    lookup.analyze_market(market_id)


if __name__ == "__main__":
    main()
