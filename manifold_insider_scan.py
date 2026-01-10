#!/usr/bin/env python3
"""
Manifold Markets Insider Trading Detector
Scans Manifold prediction markets for extreme skew indicating potential insider information
"""

import requests
import json
from datetime import datetime
from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class ManifoldAnalysis:
    market_id: str
    title: str
    yes_price: float
    no_price: float
    skew: float
    suspicious_score: float
    status: str
    volume: float
    url: str

class ManifoldInsiderDetector:
    def __init__(self):
        self.base_url = "https://api.manifold.markets/v0"
    
    def fetch_active_markets(self) -> List[Dict[str, Any]]:
        """Fetch open markets from Manifold with best liquidity"""
        print("🔍 Fetching markets from Manifold Markets...")
        try:
            # Get markets sorted by volume/liquidity
            response = requests.get(f'{self.base_url}/markets', params={'limit': 1000}, timeout=10)
            response.raise_for_status()
            markets = response.json()
            
            # Filter for open markets with valid probabilities
            open_markets = [
                m for m in markets 
                if not m.get('isResolved', False) 
                and m.get('probability') is not None
                and m.get('volume24Hours', 0) > 10  # Some minimum volume
            ]
            
            print(f"✅ Found {len(open_markets)} open markets (from {len(markets)} total)")
            return open_markets
            
        except Exception as e:
            print(f"❌ Error fetching markets: {e}")
            return []
    
    def calculate_skew(self, yes_prob: float) -> float:
        """Calculate market skew as distance from 50/50"""
        # yes_prob is already 0-1, no_prob is 1 - yes_prob
        no_prob = 1 - yes_prob
        
        # Skew = absolute distance from neutral 0.5
        return abs(yes_prob - 0.5) * 2
    
    def analyze_market(self, market: Dict[str, Any]) -> ManifoldAnalysis:
        """Analyze single market for insider signals"""
        try:
            market_id = market.get('id', '')
            title = market.get('question', 'Unknown')
            
            # Get probability (0-1)
            yes_prob = float(market.get('probability', 0.5))
            no_prob = 1 - yes_prob
            
            # Convert to percentages
            yes_price = yes_prob * 100
            no_price = no_prob * 100
            
            # Calculate metrics
            skew = self.calculate_skew(yes_prob)
            
            # Suspicious score: 0-10 based on skew from 50/50
            suspicious_score = min(skew * 10, 10.0)
            
            volume = float(market.get('volume24Hours', 0))
            is_resolved = market.get('isResolved', False)
            status = "🟢 OPEN" if not is_resolved else "🔴 CLOSED"
            
            url = f"https://manifold.markets/{market.get('creatorUsername', '')}/{market_id}"
            
            return ManifoldAnalysis(
                market_id=market_id,
                title=title,
                yes_price=yes_price,
                no_price=no_price,
                skew=skew,
                suspicious_score=suspicious_score,
                status=status,
                volume=volume,
                url=url
            )
        except Exception as e:
            print(f"Error analyzing market: {e}")
            return None
    
    def run_scan(self, min_score: float = 7.0) -> List[ManifoldAnalysis]:
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
    
    def print_results(self, results: List[ManifoldAnalysis]):
        """Display results in readable format"""
        print('\n' + '='*100)
        print('🚨 MANIFOLD MARKETS INSIDER DETECTION - MARKETS WITH EXTREME SKEW')
        print('='*100)
        
        if not results:
            print("\n✅ No suspicious markets found (no extreme skew detected)")
            return
        
        print(f"\n🔴 Found {len(results)} markets with suspicious skew:\n")
        
        for i, market in enumerate(results[:15], 1):
            yes_pct = market.yes_price
            no_pct = market.no_price
            
            # Determine which side is extreme
            if yes_pct > no_pct:
                extreme_side = f"YES at {yes_pct:.1f}%"
                normal_side = f"NO at {no_pct:.1f}%"
            else:
                extreme_side = f"NO at {no_pct:.1f}%"
                normal_side = f"YES at {yes_pct:.1f}%"
            
            print(f"{i}. {market.title[:80]}")
            print(f"   {market.status}")
            print(f"   Suspicious Score: {market.suspicious_score:.1f}/10 🚨")
            print(f"   Odds: {extreme_side} vs {normal_side}")
            print(f"   24h Volume: ${market.volume:,.0f}")
            print(f"   🔗 {market.url[:70]}...")
            print()
        
        print('='*100)
        print("💡 WHAT THIS MEANS:")
        print("   • These markets show EXTREME confidence in one outcome")
        print("   • Normal markets are typically 35-65% split")
        print("   • 90%+ on one side suggests someone has insider information")
        print("   • Monitor if the 1-10% underdog actually wins")
        print('='*100)
        
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
                'volume_24h': r.volume,
                'url': r.url,
                'timestamp': datetime.now().isoformat()
            }
            for r in results
        ]
        
        with open('manifold_suspicious_markets.json', 'w') as f:
            json.dump(results_data, f, indent=2)
        
        print(f"\n✅ Results saved to manifold_suspicious_markets.json")

def main():
    detector = ManifoldInsiderDetector()
    results = detector.run_scan(min_score=7.0)
    detector.print_results(results)

if __name__ == '__main__':
    main()
