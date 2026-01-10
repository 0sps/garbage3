#!/usr/bin/env python3
"""
Kalshi Insider Trading Detector
Scans Kalshi prediction markets for extreme skew indicating potential insider information
"""

import requests
import json
from datetime import datetime
from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class KalshiAnalysis:
    market_id: str
    title: str
    yes_price: float
    no_price: float
    skew: float
    suspicious_score: float
    status: str
    volume: float
    closed: bool

class KalshiInsiderDetector:
    def __init__(self):
        self.base_url = "https://api.elections.kalshi.com"
        self.markets = []
    
    def fetch_active_markets(self) -> List[Dict[str, Any]]:
        """Fetch all open markets from Kalshi Elections API"""
        print("🔍 Fetching markets from Kalshi Elections API...")
        try:
            response = requests.get(f'{self.base_url}/markets', timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Kalshi returns markets in 'markets' key or as direct list
            markets = data.get('markets', data) if isinstance(data, dict) else data
            
            # Filter for open markets only
            open_markets = [m for m in markets if not m.get('closed', False)]
            
            print(f"✅ Found {len(open_markets)} open markets (from {len(markets)} total)")
            return open_markets
            
        except Exception as e:
            print(f"❌ Error fetching markets: {e}")
            return []
    
    def calculate_skew(self, yes_price: float, no_price: float) -> float:
        """Calculate market skew as distance from 50/50"""
        # Normalize prices to probabilities (0-1)
        total = yes_price + no_price
        if total == 0:
            return 0
        yes_prob = yes_price / total
        no_prob = no_price / total
        
        # Skew = absolute distance from neutral 0.5
        return abs(yes_prob - 0.5) * 2
    
    def analyze_market(self, market: Dict[str, Any]) -> KalshiAnalysis:
        """Analyze single market for insider signals"""
        try:
            market_id = market.get('id', '')
            title = market.get('title', market.get('subtitle', 'Unknown'))
            
            # Get prices
            yes_price = float(market.get('yes_price', market.get('yesPrice', 0.5)))
            no_price = float(market.get('no_price', market.get('noPrice', 0.5)))
            
            # Calculate metrics
            skew = self.calculate_skew(yes_price, no_price)
            
            # Convert to probabilities for display
            total = yes_price + no_price if yes_price + no_price > 0 else 1
            yes_prob = yes_price / total * 100
            no_prob = no_price / total * 100
            
            # Suspicious score: 0-10 based on skew from 50/50
            # 0 = perfectly balanced (50/50)
            # 10 = completely skewed (99/1 or 1/99)
            suspicious_score = skew * 10
            
            volume = float(market.get('volume', market.get('volume_24h', 0)))
            closed = market.get('closed', False)
            
            status = "🟢 OPEN" if not closed else "🔴 CLOSED"
            
            return KalshiAnalysis(
                market_id=market_id,
                title=title,
                yes_price=yes_prob,
                no_price=no_prob,
                skew=skew,
                suspicious_score=suspicious_score,
                status=status,
                volume=volume,
                closed=closed
            )
        except Exception as e:
            print(f"Error analyzing market: {e}")
            return None
    
    def run_scan(self, min_score: float = 7.0) -> List[KalshiAnalysis]:
        """Run full insider detection scan"""
        markets = self.fetch_active_markets()
        
        if not markets:
            print("❌ No markets found")
            return []
        
        print(f"🔎 Analyzing {len(markets)} markets for extreme skew...")
        
        results = []
        for market in markets:
            analysis = self.analyze_market(market)
            if analysis and analysis.suspicious_score >= min_score:
                results.append(analysis)
        
        # Sort by suspicious score
        results.sort(key=lambda x: x.suspicious_score, reverse=True)
        
        return results
    
    def print_results(self, results: List[KalshiAnalysis]):
        """Display results in readable format"""
        print('\n' + '='*90)
        print('🚨 KALSHI INSIDER DETECTION - MARKETS WITH EXTREME SKEW')
        print('='*90)
        
        if not results:
            print("\n✅ No suspicious markets found (no extreme skew detected)")
            return
        
        print(f"\n🔴 Found {len(results)} markets with suspicious skew:\n")
        
        for i, market in enumerate(results[:10], 1):
            yes_pct = market.yes_price
            no_pct = market.no_price
            
            # Determine which side is extreme
            if yes_pct > no_pct:
                extreme_side = f"YES at {yes_pct:.1f}%"
                normal_side = f"NO at {no_pct:.1f}%"
            else:
                extreme_side = f"NO at {no_pct:.1f}%"
                normal_side = f"YES at {yes_pct:.1f}%"
            
            print(f"{i}. {market.title[:70]}")
            print(f"   {market.status}")
            print(f"   Suspicious Score: {market.suspicious_score:.1f}/10 🚨")
            print(f"   Odds: {extreme_side} vs {normal_side}")
            print(f"   Volume: ${market.volume:,.0f}")
            print(f"   Market ID: {market.market_id}")
            print()
        
        print('='*90)
        print("💡 WHAT THIS MEANS:")
        print("   • These markets show EXTREME confidence in one outcome")
        print("   • Normal markets are typically 40-60% split or 30-70% for favorites")
        print("   • 95%+ on one side suggests someone has insider information")
        print("   • Monitor if the 1-5% underdog actually wins")
        print('='*90)
        
        # Save to JSON
        results_data = [
            {
                'market_id': r.market_id,
                'title': r.title,
                'yes_price': r.yes_price,
                'no_price': r.no_price,
                'skew': r.skew,
                'suspicious_score': r.suspicious_score,
                'status': r.status,
                'volume': r.volume,
                'timestamp': datetime.now().isoformat()
            }
            for r in results
        ]
        
        with open('kalshi_suspicious_markets.json', 'w') as f:
            json.dump(results_data, f, indent=2)
        
        print(f"\n✅ Results saved to kalshi_suspicious_markets.json")

def main():
    detector = KalshiInsiderDetector()
    results = detector.run_scan(min_score=7.0)  # Markets with score >= 7.0
    detector.print_results(results)

if __name__ == '__main__':
    main()
