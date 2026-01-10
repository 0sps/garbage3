#!/usr/bin/env python3
"""
Polymarket Insider Trading Detection Script
Analyzes trades to identify potential insider information signals
"""

import requests
import json
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
from dataclasses import dataclass
from collections import defaultdict
import statistics

# Polymarket API endpoints
POLYMARKET_API = "https://clob.polymarket.com"
GRAPH_API = "https://api.thegraph.com/subgraphs/name/polymarket/polymarket"

@dataclass
class TradeAnalysis:
    """Structure for storing trade analysis results"""
    market_id: str
    market_title: str
    sentiment_score: float
    risk_score: float
    insider_probability: float
    indicators: Dict[str, any]
    recent_trades: List[Dict]
    whale_addresses: List[Dict]
    
    def __repr__(self):
        return (f"Market: {self.market_title[:50]}\n"
                f"  Insider Probability: {self.insider_probability:.1%}\n"
                f"  Risk Score: {self.risk_score:.1f}/10\n"
                f"  Key Indicators: {self.indicators}")

class PolymarketInsiderDetector:
    """Main class for detecting insider trading signals on Polymarket"""
    
    def __init__(self, lookback_days: int = 7):
        self.lookback_days = lookback_days
        self.session = requests.Session()
        
    def fetch_active_markets(self, limit: int = 50) -> List[Dict]:
        """Fetch active prediction markets"""
        print(f"📊 Fetching active markets from Polymarket...")
        try:
            # Using CLOB API for active markets
            response = self.session.get(
                f"{POLYMARKET_API}/markets",
                params={"limit": limit, "closed": False},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            # Handle both array and object responses
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and 'data' in data:
                return data['data'] if isinstance(data['data'], list) else [data]
            elif isinstance(data, dict):
                return [data]
            return []
        except Exception as e:
            print(f"❌ Error fetching markets: {e}")
            return []
    
    def fetch_market_trades(self, market_id: str) -> List[Dict]:
        """Fetch recent trades for a specific market"""
        try:
            # Try CLOB API first
            response = self.session.get(
                f"{POLYMARKET_API}/trades",
                params={
                    "market": market_id,
                    "limit": 1000
                },
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and 'data' in data:
                return data['data'] if isinstance(data['data'], list) else [data]
            return []
        except Exception as e:
            # If trades endpoint fails, return empty
            return []
    
    def fetch_market_details(self, market_id: str) -> Dict:
        """Fetch detailed market information"""
        try:
            response = self.session.get(
                f"{POLYMARKET_API}/market/{market_id}",
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ Error fetching market details: {e}")
            return {}
    
    def analyze_position_concentration(self, trades: List[Dict]) -> Tuple[float, Dict]:
        """
        Analyze if positions are concentrated among few addresses
        HIGH: Potential insider info - few addresses control large positions
        SCORE: 0-10 (higher = more suspicious)
        """
        if not trades:
            return 0, {}
        
        address_volumes = defaultdict(float)
        address_outcomes = defaultdict(lambda: defaultdict(float))
        
        for trade in trades:
            try:
                address = trade.get('maker', trade.get('taker', 'unknown'))
                size = float(trade.get('size', 0))
                outcome = trade.get('outcome', 'unknown')
                
                address_volumes[address] += size
                address_outcomes[address][outcome] += size
            except (KeyError, ValueError):
                continue
        
        if not address_volumes:
            return 0, {}
        
        # Calculate concentration using Herfindahl index (0-1, higher = more concentrated)
        total_volume = sum(address_volumes.values())
        market_shares = [vol / total_volume for vol in address_volumes.values()]
        herfindahl = sum(share ** 2 for share in market_shares)
        
        # Get top addresses
        top_addresses = sorted(
            address_volumes.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        # Calculate score: higher concentration = higher score
        concentration_score = herfindahl * 10
        
        analysis = {
            'herfindahl_index': round(herfindahl, 3),
            'num_unique_addresses': len(address_volumes),
            'concentration_ratio_top3': round(
                sum([vol for _, vol in top_addresses[:3]]) / total_volume,
                3
            ),
            'total_volume': round(total_volume, 2),
            'top_addresses': [
                {
                    'address': addr[:10] + '...',
                    'volume': round(vol, 2),
                    'primary_outcome': max(address_outcomes[addr].items(),
                                         key=lambda x: x[1])[0]
                }
                for addr, vol in top_addresses
            ]
        }
        
        return concentration_score, analysis
    
    def analyze_volume_velocity(self, trades: List[Dict]) -> Tuple[float, Dict]:
        """
        Analyze how quickly positions are being accumulated
        HIGH: Rapid accumulation might indicate information advantage
        SCORE: 0-10 (higher = faster accumulation)
        """
        if not trades:
            return 0, {}
        
        trades_sorted = sorted(
            trades,
            key=lambda x: x.get('timestamp', x.get('createdAt', 0))
        )
        
        if len(trades_sorted) < 2:
            return 0, {}
        
        # Calculate volume per time period (trades per hour)
        try:
            first_time = float(trades_sorted[0].get('timestamp', trades_sorted[0].get('createdAt', 0)))
            last_time = float(trades_sorted[-1].get('timestamp', trades_sorted[-1].get('createdAt', 0)))
            
            time_diff_hours = (last_time - first_time) / 3600 if last_time != first_time else 1
            trades_per_hour = len(trades_sorted) / max(time_diff_hours, 0.1)
            
            # Recent volume (last 24 hours if available)
            recent_trades = [t for t in trades_sorted 
                           if (last_time - float(t.get('timestamp', t.get('createdAt', 0)))) < 86400]
            recent_volume = sum(float(t.get('size', 0)) for t in recent_trades)
            
            velocity_score = min(trades_per_hour / 10, 10)  # Normalize to 0-10
            
            analysis = {
                'trades_per_hour': round(trades_per_hour, 2),
                'recent_24h_trades': len(recent_trades),
                'recent_24h_volume': round(recent_volume, 2),
                'velocity_score': round(velocity_score, 2)
            }
            
            return velocity_score, analysis
        except Exception:
            return 0, {}
    
    def analyze_outcome_skew(self, trades: List[Dict]) -> Tuple[float, Dict]:
        """
        Analyze if trading is skewed toward one outcome
        HIGH: Unusual skew might indicate information about likely outcome
        SCORE: 0-10 (higher = more skewed)
        """
        if not trades:
            return 0, {}
        
        outcome_volumes = defaultdict(float)
        
        for trade in trades:
            try:
                outcome = trade.get('outcome', 'unknown')
                size = float(trade.get('size', 0))
                outcome_volumes[outcome] += size
            except (KeyError, ValueError):
                continue
        
        if not outcome_volumes:
            return 0, {}
        
        total = sum(outcome_volumes.values())
        if total == 0:
            return 0, {}
        
        sorted_outcomes = sorted(outcome_volumes.items(), key=lambda x: x[1], reverse=True)
        
        # Calculate skew: how dominant is the largest outcome
        largest_share = sorted_outcomes[0][1] / total if sorted_outcomes else 0
        
        # Score: 0 at 50/50, peaks at 100/0 (score of 10)
        skew_score = abs(largest_share - 0.5) * 20  # Maps 0.5->0, 1.0->10
        skew_score = min(skew_score, 10)
        
        analysis = {
            'outcome_distribution': {
                outcome: round(vol / total, 3)
                for outcome, vol in sorted_outcomes
            },
            'largest_outcome_share': round(largest_share, 3),
            'skew_score': round(skew_score, 2)
        }
        
        return skew_score, analysis
    
    def analyze_price_movement(self, trades: List[Dict]) -> Tuple[float, Dict]:
        """
        Analyze unusual price movements around trades
        HIGH: Sharp price changes might indicate information-driven trading
        SCORE: 0-10 (higher = more unusual)
        """
        if not trades:
            return 0, {}
        
        trades_sorted = sorted(
            trades,
            key=lambda x: x.get('timestamp', x.get('createdAt', 0))
        )
        
        if len(trades_sorted) < 3:
            return 0, {}
        
        try:
            # Get price changes across trades
            prices = []
            for trade in trades_sorted:
                price = float(trade.get('price', trade.get('executionPrice', 0)))
                size = float(trade.get('size', 0))
                if price > 0:
                    prices.append(price)
            
            if len(prices) < 2:
                return 0, {}
            
            # Calculate volatility of prices
            price_changes = [abs(prices[i] - prices[i-1]) / prices[i-1] 
                           for i in range(1, len(prices)) if prices[i-1] != 0]
            
            if not price_changes:
                return 0, {}
            
            avg_change = statistics.mean(price_changes)
            volatility = statistics.stdev(price_changes) if len(price_changes) > 1 else 0
            
            # Higher volatility = more suspicious
            movement_score = min((avg_change + volatility) * 50, 10)
            
            analysis = {
                'avg_price_change': round(avg_change, 4),
                'price_volatility': round(volatility, 4),
                'price_range': (round(min(prices), 4), round(max(prices), 4)),
                'movement_score': round(movement_score, 2)
            }
            
            return movement_score, analysis
        except Exception:
            return 0, {}
    
    def analyze_whale_accumulation(self, trades: List[Dict]) -> Tuple[float, Dict]:
        """
        Identify and track whale addresses accumulating large positions
        HIGH: Single entities building large positions quickly
        SCORE: 0-10 (higher = more whale activity)
        """
        if not trades:
            return 0, {}
        
        address_trades = defaultdict(list)
        
        for trade in trades:
            try:
                address = trade.get('maker', trade.get('taker', 'unknown'))
                size = float(trade.get('size', 0))
                timestamp = float(trade.get('timestamp', trade.get('createdAt', 0)))
                price = float(trade.get('price', trade.get('executionPrice', 0)))
                
                address_trades[address].append({
                    'size': size,
                    'timestamp': timestamp,
                    'price': price
                })
            except (KeyError, ValueError):
                continue
        
        # Find whales (addresses with large total positions)
        whale_data = []
        for address, trade_list in address_trades.items():
            total_size = sum(t['size'] for t in trade_list)
            num_trades = len(trade_list)
            
            if num_trades >= 2:
                trade_list_sorted = sorted(trade_list, key=lambda x: x['timestamp'])
                time_span = trade_list_sorted[-1]['timestamp'] - trade_list_sorted[0]['timestamp']
                
                whale_data.append({
                    'address': address[:10] + '...',
                    'total_position': total_size,
                    'num_trades': num_trades,
                    'avg_trade_size': total_size / num_trades,
                    'accumulation_time_hours': time_span / 3600 if time_span > 0 else 0,
                    'accumulation_speed': total_size / max(time_span / 3600, 1)
                })
        
        if not whale_data:
            return 0, {}
        
        # Sort by position size
        whale_data.sort(key=lambda x: x['total_position'], reverse=True)
        
        # Whale score based on top whale's position
        if whale_data:
            top_whale = whale_data[0]
            # Score higher if rapid accumulation
            whale_score = min(top_whale['accumulation_speed'] / 100, 10)
        else:
            whale_score = 0
        
        analysis = {
            'num_whale_addresses': len(whale_data),
            'top_whales': whale_data[:5]
        }
        
        return whale_score, analysis
    
    def calculate_insider_probability(self, scores: Dict) -> float:
        """
        Calculate overall insider trading probability (0-1)
        Combines all indicators with weights
        """
        weights = {
            'concentration': 0.25,
            'velocity': 0.15,
            'skew': 0.20,
            'movement': 0.15,
            'whale': 0.25
        }
        
        weighted_score = (
            scores['concentration'] * weights['concentration'] +
            scores['velocity'] * weights['velocity'] +
            scores['skew'] * weights['skew'] +
            scores['movement'] * weights['movement'] +
            scores['whale'] * weights['whale']
        )
        
        # Normalize to 0-1 (divide by max score of 10)
        return min(weighted_score / 10, 1.0)
    
    def analyze_market(self, market: Dict) -> TradeAnalysis:
        """Analyze a single market for insider trading signals"""
        if isinstance(market, str):
            return None
            
        market_id = market.get('id', market.get('market_id', market.get('condition_id', '')))
        market_title = market.get('title', market.get('question', market.get('description', 'Unknown Market')))
        
        if not market_id:
            return None
        
        print(f"  📈 Analyzing: {market_title[:60]}...")
        
        # Fetch trades
        trades = self.fetch_market_trades(market_id)
        
        if not trades:
            # Can't analyze without trade data
            return None
        
        # Run all analyses
        concentration_score, concentration_analysis = self.analyze_position_concentration(trades)
        velocity_score, velocity_analysis = self.analyze_volume_velocity(trades)
        skew_score, skew_analysis = self.analyze_outcome_skew(trades)
        movement_score, movement_analysis = self.analyze_price_movement(trades)
        whale_score, whale_analysis = self.analyze_whale_accumulation(trades)
        
        scores = {
            'concentration': concentration_score,
            'velocity': velocity_score,
            'skew': skew_score,
            'movement': movement_score,
            'whale': whale_score
        }
        
        insider_prob = self.calculate_insider_probability(scores)
        
        # Risk score (subjective combination of indicators)
        risk_score = (concentration_score + velocity_score + skew_score) / 3
        
        indicators = {
            'Concentration Score': round(concentration_score, 2),
            'Velocity Score': round(velocity_score, 2),
            'Outcome Skew Score': round(skew_score, 2),
            'Price Movement Score': round(movement_score, 2),
            'Whale Activity Score': round(whale_score, 2),
        }
        
        recent_trades = sorted(
            trades,
            key=lambda x: x.get('timestamp', x.get('createdAt', 0)),
            reverse=True
        )[:10]
        
        return TradeAnalysis(
            market_id=market_id,
            market_title=market_title,
            sentiment_score=skew_score,
            risk_score=risk_score,
            insider_probability=insider_prob,
            indicators=indicators,
            recent_trades=recent_trades,
            whale_addresses=whale_analysis.get('top_whales', [])
        )
    
    def run_detection(self, num_markets: int = 20) -> List[TradeAnalysis]:
        """Run insider trading detection across top markets"""
        print(f"\n🔍 Polymarket Insider Trading Detector")
        print(f"⏰ Lookback period: {self.lookback_days} days")
        print(f"=" * 60)
        
        # Fetch active markets
        markets = self.fetch_active_markets(limit=num_markets)
        
        if not markets:
            print("❌ Failed to fetch markets")
            return []
        
        print(f"✅ Found {len(markets)} active markets\n")
        
        results = []
        for market in markets:
            analysis = self.analyze_market(market)
            if analysis:
                results.append(analysis)
        
        # Sort by insider probability
        results.sort(key=lambda x: x.insider_probability, reverse=True)
        
        return results
    
    def print_results(self, results: List[TradeAnalysis], top_n: int = 10):
        """Print formatted results"""
        print(f"\n📊 TOP {min(top_n, len(results))} SUSPICIOUS MARKETS")
        print("=" * 80)
        
        for i, analysis in enumerate(results[:top_n], 1):
            print(f"\n{i}. 🚨 INSIDER PROBABILITY: {analysis.insider_probability:.1%}")
            print(f"   Market: {analysis.market_title}")
            print(f"   Risk Score: {analysis.risk_score:.1f}/10")
            print(f"   Market ID: {analysis.market_id}")
            
            print(f"\n   📊 Indicator Scores:")
            for indicator, score in analysis.indicators.items():
                bar = "█" * int(score) + "░" * (10 - int(score))
                print(f"      {indicator:.<25} {bar} {score:.1f}")
            
            if analysis.whale_addresses:
                print(f"\n   🐋 Top Whale Addresses:")
                for whale in analysis.whale_addresses[:3]:
                    print(f"      {whale['address']}: ${whale['total_position']:.2f} "
                          f"({whale['num_trades']} trades)")
            
            print()


def main():
    """Main execution"""
    detector = PolymarketInsiderDetector(lookback_days=7)
    
    try:
        results = detector.run_detection(num_markets=20)
        detector.print_results(results, top_n=10)
        
        # Save detailed results to JSON
        json_results = [
            {
                'market_title': r.market_title,
                'market_id': r.market_id,
                'insider_probability': float(r.insider_probability),
                'risk_score': float(r.risk_score),
                'indicators': {k: float(v) if isinstance(v, (int, float)) else v 
                             for k, v in r.indicators.items()}
            }
            for r in results
        ]
        
        with open('insider_trading_analysis.json', 'w') as f:
            json.dump(json_results, f, indent=2)
        
        print(f"\n✅ Detailed results saved to insider_trading_analysis.json")
        
    except KeyboardInterrupt:
        print("\n⏸️  Analysis cancelled by user")
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
