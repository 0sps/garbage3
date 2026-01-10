#!/usr/bin/env python3
"""
Polymarket Insider Trading Detector - GraphQL Version
Uses The Graph API instead of CLOB API for trade data
"""

import requests
import json
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from collections import defaultdict
import statistics
import time

GRAPH_API = "https://api.thegraph.com/subgraphs/name/polymarket/polymarket"

@dataclass
class QuickAnalysis:
    """Quick analysis of a market"""
    market_id: str
    market_title: str
    price_indicator: str
    volume_indicator: str
    likelihood_summary: str
    suspicious_score: float

class PolymarketLiveDetector:
    """Fast insider trading detector using market snapshot data"""
    
    def __init__(self):
        self.session = requests.Session()
    
    def fetch_active_markets(self, limit: int = 50) -> List[Dict]:
        """Fetch active markets with snapshot data"""
        print(f"📊 Fetching active markets from Polymarket...")
        try:
            response = self.session.get(
                "https://clob.polymarket.com/markets",
                params={"limit": limit, "closed": False},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            if isinstance(data, list):
                return [m for m in data if isinstance(m, dict)]
            elif isinstance(data, dict) and 'data' in data:
                return data['data'] if isinstance(data['data'], list) else []
            return []
        except Exception as e:
            print(f"❌ Error fetching markets: {e}")
            return []
    
    def analyze_market_snapshot(self, market: Dict) -> Optional[QuickAnalysis]:
        """Quick analysis based on market snapshot"""
        try:
            market_id = market.get('id', market.get('condition_id', ''))
            title = market.get('title', market.get('question', 'Unknown'))
            
            if not market_id or isinstance(market_id, str) and not market_id.strip():
                return None
            
            # Extract token information
            tokens = market.get('tokens', [])
            if len(tokens) < 2:
                return None
            
            # Analyze token prices for skew
            prices = [float(t.get('price', 0)) for t in tokens if isinstance(t, dict)]
            
            if not prices or len(prices) < 2:
                return None
            
            total_price = sum(prices)
            if total_price == 0:
                return None
            
            # Calculate skew
            skew_ratios = [p / total_price for p in prices]
            max_skew = max(skew_ratios)
            min_skew = min(skew_ratios)
            
            # Calculate suspicious score based on skew
            # Neutral = 0.5 each, Extreme = 1.0/0.0
            skew_distance_from_neutral = abs(max_skew - 0.5)
            suspicious_score = min(skew_distance_from_neutral * 20, 10)  # 0-10 scale
            
            # Determine price indicators
            if max_skew > 0.85:
                price_indicator = "🔴 EXTREME SKEW"
            elif max_skew > 0.75:
                price_indicator = "🟠 HIGH SKEW"
            elif max_skew > 0.65:
                price_indicator = "🟡 MODERATE SKEW"
            else:
                price_indicator = "🟢 BALANCED"
            
            # Volume would need trade data, so we skip for now
            volume_indicator = "⚪ UNKNOWN (needs trade data)"
            
            # Determine summary
            if suspicious_score > 7:
                likelihood_summary = "HIGH - Extreme market skew detected"
            elif suspicious_score > 5:
                likelihood_summary = "MODERATE - Notable skew detected"
            else:
                likelihood_summary = "LOW - Market relatively balanced"
            
            return QuickAnalysis(
                market_id=market_id,
                market_title=title[:70],
                price_indicator=price_indicator,
                volume_indicator=volume_indicator,
                likelihood_summary=likelihood_summary,
                suspicious_score=suspicious_score
            )
        
        except Exception as e:
            return None
    
    def run_quick_scan(self, num_markets: int = 30) -> List[QuickAnalysis]:
        """Quick scan of markets"""
        print(f"\n🔴 POLYMARKET LIVE SCAN")
        print(f"⏰ Analyzing {num_markets} active markets")
        print("=" * 80)
        
        markets = self.fetch_active_markets(limit=num_markets)
        
        if not markets:
            print("❌ No markets returned from API")
            return []
        
        print(f"✅ Found {len(markets)} active markets\n")
        
        results = []
        for market in markets:
            analysis = self.analyze_market_snapshot(market)
            if analysis:
                results.append(analysis)
        
        # Sort by suspicious score
        results.sort(key=lambda x: x.suspicious_score, reverse=True)
        
        return results
    
    def print_results(self, results: List[QuickAnalysis]):
        """Print formatted results"""
        print(f"\n📊 TOP SUSPICIOUS MARKETS")
        print("=" * 80)
        
        for i, analysis in enumerate(results[:15], 1):
            print(f"\n{i}. 🚨 Suspicious Score: {analysis.suspicious_score:.1f}/10")
            print(f"   Market: {analysis.market_title}")
            print(f"   {analysis.price_indicator}")
            print(f"   {analysis.likelihood_summary}")
            print(f"   Market ID: {analysis.market_id}")

def main():
    detector = PolymarketLiveDetector()
    
    try:
        results = detector.run_quick_scan(num_markets=50)
        detector.print_results(results)
        
        # Save results
        json_results = [
            {
                'market_title': r.market_title,
                'market_id': r.market_id,
                'suspicious_score': float(r.suspicious_score),
                'price_indicator': r.price_indicator,
                'likelihood_summary': r.likelihood_summary
            }
            for r in results
        ]
        
        with open('live_scan_results.json', 'w') as f:
            json.dump(json_results, f, indent=2)
        
        print(f"\n✅ Results saved to live_scan_results.json")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
