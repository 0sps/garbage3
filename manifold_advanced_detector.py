#!/usr/bin/env python3
"""
Manifold Markets Advanced Insider Detection
Uses multiple indicators beyond skew to detect insider information:
- Volume velocity (recent volume vs historical)
- Liquidity concentration
- Time pressure (closing soon with extreme skew)
- Trader concentration (few wallets = coordinated manipulation or inside info)
- Probability momentum (rapid shifts)
- Creator track record
"""

import requests
import json
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import List, Dict, Any
import math

@dataclass
class AdvancedAnalysis:
    market_id: str
    title: str
    yes_price: float
    no_price: float
    skew_score: float
    volume_velocity_score: float
    liquidity_score: float
    time_pressure_score: float
    creator_score: float
    trader_concentration_score: float
    total_score: float
    status: str
    url: str

class ManifoldAdvancedDetector:
    def __init__(self):
        self.base_url = "https://api.manifold.markets/v0"
        self.creator_cache = {}
    
    def fetch_active_markets(self) -> List[Dict[str, Any]]:
        """Fetch open markets from Manifold"""
        print("🔍 Fetching markets from Manifold Markets...")
        try:
            response = requests.get(f'{self.base_url}/markets', params={'limit': 1000}, timeout=10)
            response.raise_for_status()
            markets = response.json()
            
            # Filter for open markets with min volume
            open_markets = [
                m for m in markets 
                if not m.get('isResolved', False) 
                and m.get('probability') is not None
                and m.get('volume24Hours', 0) > 0  # Any volume = active
            ]
            
            print(f"✅ Found {len(open_markets)} open markets")
            return open_markets
            
        except Exception as e:
            print(f"❌ Error fetching markets: {e}")
            return []
    
    def calculate_skew_score(self, yes_prob: float) -> float:
        """Score based on distance from 50/50 (0-10)"""
        skew = abs(yes_prob - 0.5) * 2
        return min(skew * 10, 10.0)
    
    def calculate_volume_velocity(self, market: Dict) -> float:
        """Score rapid volume increase (suggests sudden new information)
        
        Extreme score (8-10): Heavy volume today vs week average
        Moderate score (5-7): Noticeable volume increase
        Low score (0-4): Normal trading
        """
        vol_24h = market.get('volume24Hours', 0)
        total_vol = market.get('volume', 1)  # Avoid division by zero
        
        if total_vol == 0:
            return 0
        
        # If 24h volume is >50% of all volume, something just happened
        volume_ratio = vol_24h / total_vol if total_vol > 0 else 0
        
        # Score: high ratio = suspicious
        velocity_score = min(volume_ratio * 15, 10.0)
        
        return velocity_score
    
    def calculate_liquidity_score(self, market: Dict) -> float:
        """Score based on liquidity depth
        
        High liquidity with extreme skew = someone with deep pockets pushed it
        Low liquidity with extreme skew = possible whale manipulation
        """
        liquidity = market.get('totalLiquidity', 100)
        
        # Higher liquidity with strong positions is actually suspicious
        # Someone willing to put real money in = confidence
        # Normalize: 0 if liquidity < $100, high if liquidity > $10k
        
        if liquidity < 100:
            return 8.0  # Low liquidity but extreme skew = whales only
        elif liquidity < 1000:
            return 6.0
        elif liquidity < 10000:
            return 4.0
        else:
            return 2.0  # High liquidity, more distributed
    
    def calculate_time_pressure(self, market: Dict) -> float:
        """Score: markets closing soon with extreme skew are more suspicious
        
        If market resolves in hours and has 99% odds, that's race condition
        If market resolves in months and has 99% odds, less suspicious (time for correction)
        """
        close_time = market.get('closeTime', None)
        if not close_time:
            return 0
        
        now_ms = datetime.now().timestamp() * 1000
        time_remaining_ms = close_time - now_ms
        
        if time_remaining_ms < 0:
            return 0  # Already closed
        
        hours_remaining = time_remaining_ms / (1000 * 60 * 60)
        
        # Score high if closing very soon
        if hours_remaining < 1:
            return 9.0  # Less than 1 hour - race condition
        elif hours_remaining < 24:
            return 7.0  # Today
        elif hours_remaining < 7 * 24:
            return 5.0  # This week
        elif hours_remaining < 30 * 24:
            return 2.0  # This month
        else:
            return 0.0  # Plenty of time
    
    def get_creator_track_record(self, creator_id: str) -> float:
        """Check if creator is a known accurate forecaster (0-10 score)
        
        Harder to implement without full history, so we'll estimate:
        - If creator_id is in cache, use cached score
        - For now, return neutral 5.0
        """
        # TODO: In a real system, we'd track creator accuracy over time
        return 5.0
    
    def calculate_trader_concentration(self, market: Dict) -> float:
        """Score: How concentrated are the positions?
        
        Few unique bettors = insider coordination or whale manipulation
        Many unique bettors = dispersed knowledge (less suspicious)
        """
        bettor_count = market.get('uniqueBettorCount', 1)
        volume = market.get('volume', 1)
        
        if bettor_count < 2:
            return 9.0  # Only 1 bettor - 100% concentration
        
        # Rough heuristic: if avg bet size is >$1k per bettor, concentrated
        avg_bet = volume / bettor_count if bettor_count > 0 else 0
        
        if avg_bet > 1000:
            return 8.0
        elif avg_bet > 500:
            return 6.0
        elif avg_bet > 100:
            return 4.0
        else:
            return 1.0
    
    def is_gaming_the_system(self, market: Dict[str, Any]) -> bool:
        """Filter out test markets and obvious gaming/manipulation
        
        Returns True if market should be excluded
        """
        question = market.get('question', '').lower()
        creator = market.get('creatorUsername', '').lower()
        
        # Test/gaming keywords
        gaming_keywords = [
            'resolving', 'test', 'testing', 'will resolve',
            'resolves to', 'resolves by', 'resolve',
            'trivial', 'obvious', 'proof of concept',
            'pump', 'dump', 'manipulation',
            'game', 'gaming',
        ]
        
        # Known test accounts
        test_accounts = ['bonatschi', 'kooshal', 'testuser', 'test_']
        
        # Check keywords in question
        for keyword in gaming_keywords:
            if keyword in question:
                return True
        
        # Check test accounts
        for test_account in test_accounts:
            if test_account in creator:
                return True
        
        # Markets closing in < 24 hours with extreme skew = race conditions (gaming)
        close_time_ms = market.get('closeTime', 0)
        now_ms = datetime.now().timestamp() * 1000
        hours_remaining = (close_time_ms - now_ms) / (1000 * 60 * 60)
        
        probability = market.get('probability', 0.5)
        skew = abs(probability - 0.5) * 2
        
        # If closes in <6 hours AND >90% skew = race condition/gaming
        if hours_remaining < 6 and skew > 0.90:
            return True
        
        return False
    
    def analyze_market(self, market: Dict[str, Any]) -> AdvancedAnalysis:
        """Comprehensive insider detection analysis"""
        try:
            market_id = market.get('id', '')
            title = market.get('question', 'Unknown')
            
            # Get probability
            yes_prob = float(market.get('probability', 0.5))
            no_prob = 1 - yes_prob
            
            # Calculate all scores
            skew_score = self.calculate_skew_score(yes_prob)
            velocity_score = self.calculate_volume_velocity(market)
            liquidity_score = self.calculate_liquidity_score(market)
            time_pressure_score = self.calculate_time_pressure(market)
            creator_score = self.get_creator_track_record(market.get('creatorId', ''))
            concentration_score = self.calculate_trader_concentration(market)
            
            # Weighted total (skew is primary but others matter)
            total_score = (
                skew_score * 0.35 +           # 35% - primary indicator
                velocity_score * 0.20 +       # 20% - sudden activity
                time_pressure_score * 0.15 +  # 15% - time pressure
                concentration_score * 0.15 +  # 15% - trader concentration
                liquidity_score * 0.10 +      # 10% - liquidity depth
                creator_score * 0.05          # 5% - creator track record
            )
            
            is_resolved = market.get('isResolved', False)
            status = "🟢 OPEN" if not is_resolved else "🔴 CLOSED"
            
            creator_username = market.get('creatorUsername', '')
            market_slug = market.get('slug', market_id)
            url = f"https://manifold.markets/{creator_username}/{market_slug}"
            
            return AdvancedAnalysis(
                market_id=market_id,
                title=title,
                yes_price=yes_prob * 100,
                no_price=no_prob * 100,
                skew_score=skew_score,
                volume_velocity_score=velocity_score,
                liquidity_score=liquidity_score,
                time_pressure_score=time_pressure_score,
                creator_score=creator_score,
                trader_concentration_score=concentration_score,
                total_score=total_score,
                status=status,
                url=url
            )
        except Exception as e:
            print(f"Error analyzing market: {e}")
            return None
    
    def run_scan(self, min_score: float = 6.0) -> List[AdvancedAnalysis]:
        """Run full advanced insider detection"""
        markets = self.fetch_active_markets()
        
        if not markets:
            return []
        
        # Filter out gaming/test markets
        legitimate_markets = [m for m in markets if not self.is_gaming_the_system(m)]
        print(f"🔎 Analyzing {len(legitimate_markets)} legitimate markets (filtered {len(markets) - len(legitimate_markets)} gaming/test markets)...")
        
        results = []
        for market in legitimate_markets:
            analysis = self.analyze_market(market)
            if analysis and analysis.total_score >= min_score:
                results.append(analysis)
        
        # Sort by total score
        results.sort(key=lambda x: x.total_score, reverse=True)
        
        return results
    
    def print_results(self, results: List[AdvancedAnalysis]):
        """Display results with breakdown"""
        print('\n' + '='*120)
        print('🚨 ADVANCED INSIDER DETECTION - MANIFOLD MARKETS')
        print('='*120)
        
        if not results:
            print("\n✅ No highly suspicious markets found")
            return
        
        print(f"\n🔴 Found {len(results)} highly suspicious markets:\n")
        
        for i, m in enumerate(results[:20], 1):
            odds_str = f"{m.yes_price:.1f}% YES / {m.no_price:.1f}% NO"
            
            print(f"{i}. {m.title[:75]}")
            print(f"   {m.status}")
            print(f"   Odds: {odds_str}")
            print(f"   🎯 TOTAL SCORE: {m.total_score:.1f}/10")
            print(f"      ├─ Skew:              {m.skew_score:.1f}/10 (odds imbalance)")
            print(f"      ├─ Volume Velocity:   {m.volume_velocity_score:.1f}/10 (recent activity spike)")
            print(f"      ├─ Time Pressure:     {m.time_pressure_score:.1f}/10 (closes soon)")
            print(f"      ├─ Trader Concentration: {m.trader_concentration_score:.1f}/10 (few wallets)")
            print(f"      ├─ Liquidity:         {m.liquidity_score:.1f}/10 (depth)")
            print(f"      └─ Creator Track:     {m.creator_score:.1f}/10 (historical accuracy)")
            print(f"   🔗 {m.url}")
            print()
        
        print('='*120)
        print("💡 INTERPRETATION:")
        print("   🔴 9-10:  Extremely suspicious - likely insider information")
        print("   🟠 7-8:   Highly suspicious - strong indicators of edge")
        print("   🟡 5-6:   Moderately suspicious - multiple minor signals")
        print("   🟢 0-4:   Low suspicion - normal market behavior")
        print()
        print("   Key indicators:")
        print("   • Skew: Extreme confidence in one outcome (99%+ is extreme)")
        print("   • Volume Velocity: Sudden spike in trading (new info arrived)")
        print("   • Time Pressure: Market closes soon with extreme skew (race condition)")
        print("   • Trader Concentration: Few wallets controlling positions (coordination)")
        print("   • Liquidity: Low liquidity suggests only whales are willing to trade")
        print('='*120)
        
        # Save to JSON
        results_data = [
            {
                'market_id': m.market_id,
                'title': m.title,
                'yes_price': m.yes_price,
                'no_price': m.no_price,
                'total_score': m.total_score,
                'skew_score': m.skew_score,
                'volume_velocity_score': m.volume_velocity_score,
                'liquidity_score': m.liquidity_score,
                'time_pressure_score': m.time_pressure_score,
                'trader_concentration_score': m.trader_concentration_score,
                'creator_score': m.creator_score,
                'status': m.status,
                'url': m.url,
                'timestamp': datetime.now().isoformat()
            }
            for m in results
        ]
        
        with open('manifold_advanced_signals.json', 'w') as f:
            json.dump(results_data, f, indent=2)
        
        print(f"\n✅ Detailed results saved to manifold_advanced_signals.json")

def main():
    detector = ManifoldAdvancedDetector()
    results = detector.run_scan(min_score=6.0)
    detector.print_results(results)

if __name__ == '__main__':
    main()
