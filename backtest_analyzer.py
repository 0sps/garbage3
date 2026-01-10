#!/usr/bin/env python3
"""
Polymarket Insider Trading Detector - Backtesting Module
Tests whether insider trading signals accurately predict price movements
"""

import requests
import json
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict
import statistics
import time

POLYMARKET_API = "https://clob.polymarket.com"

@dataclass
class BacktestResult:
    """Results from a single backtest"""
    market_id: str
    market_title: str
    signal_timestamp: float
    analysis_timestamp: float
    insider_probability: float
    indicator_scores: Dict
    pre_signal_price: float
    post_signal_price: float
    price_movement: float
    price_movement_pct: float
    predicted_correctly: bool
    outcome_prediction: str
    actual_outcome: Optional[str]
    market_resolved: bool
    time_to_resolution_hours: Optional[float]
    trades_analyzed: int
    
    def to_dict(self):
        return asdict(self)

class PolymarketBacktester:
    """Backtesting system for validating insider trading detector"""
    
    def __init__(self, lookback_days: int = 30):
        self.lookback_days = lookback_days
        self.session = requests.Session()
        self.cache = {}
    
    def fetch_resolved_markets(self, limit: int = 100) -> List[Dict]:
        """Fetch resolved/closed markets for backtesting"""
        print(f"📊 Fetching resolved markets for backtest...")
        try:
            response = self.session.get(
                f"{POLYMARKET_API}/markets",
                params={"limit": limit, "closed": True},
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ Error fetching resolved markets: {e}")
            return []
    
    def fetch_historical_trades(self, market_id: str, limit: int = 5000) -> List[Dict]:
        """Fetch all historical trades for a market"""
        try:
            response = self.session.get(
                f"{POLYMARKET_API}/trades",
                params={"market": market_id, "limit": limit},
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ Error fetching trades: {e}")
            return []
    
    def fetch_market_history(self, market_id: str) -> Dict:
        """Fetch complete market history including resolution"""
        try:
            response = self.session.get(
                f"{POLYMARKET_API}/market/{market_id}",
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ Error fetching market history: {e}")
            return {}
    
    def get_trades_before_timestamp(self, trades: List[Dict], timestamp: float) -> List[Dict]:
        """Filter trades that occurred before a specific timestamp"""
        return [t for t in trades 
                if float(t.get('timestamp', t.get('createdAt', 0))) < timestamp]
    
    def get_trades_after_timestamp(self, trades: List[Dict], timestamp: float, 
                                    window_hours: int = 24) -> List[Dict]:
        """Get trades in window after timestamp"""
        end_time = timestamp + (window_hours * 3600)
        return [t for t in trades 
                if timestamp <= float(t.get('timestamp', t.get('createdAt', 0))) < end_time]
    
    def analyze_position_concentration(self, trades: List[Dict]) -> Tuple[float, Dict]:
        """[Reuse from main detector]"""
        if not trades:
            return 0, {}
        
        address_volumes = defaultdict(float)
        
        for trade in trades:
            try:
                address = trade.get('maker', trade.get('taker', 'unknown'))
                size = float(trade.get('size', 0))
                address_volumes[address] += size
            except (KeyError, ValueError):
                continue
        
        if not address_volumes:
            return 0, {}
        
        total_volume = sum(address_volumes.values())
        market_shares = [vol / total_volume for vol in address_volumes.values()]
        herfindahl = sum(share ** 2 for share in market_shares)
        concentration_score = herfindahl * 10
        
        return min(concentration_score, 10), {
            'herfindahl_index': round(herfindahl, 3),
            'num_unique_addresses': len(address_volumes),
            'concentration_ratio_top3': round(
                sum(sorted(address_volumes.values(), reverse=True)[:3]) / total_volume, 3
            )
        }
    
    def analyze_volume_velocity(self, trades: List[Dict]) -> Tuple[float, Dict]:
        """[Reuse from main detector]"""
        if not trades:
            return 0, {}
        
        trades_sorted = sorted(
            trades,
            key=lambda x: x.get('timestamp', x.get('createdAt', 0))
        )
        
        if len(trades_sorted) < 2:
            return 0, {}
        
        try:
            first_time = float(trades_sorted[0].get('timestamp', trades_sorted[0].get('createdAt', 0)))
            last_time = float(trades_sorted[-1].get('timestamp', trades_sorted[-1].get('createdAt', 0)))
            
            time_diff_hours = (last_time - first_time) / 3600 if last_time != first_time else 1
            trades_per_hour = len(trades_sorted) / max(time_diff_hours, 0.1)
            velocity_score = min(trades_per_hour / 10, 10)
            
            return velocity_score, {'trades_per_hour': round(trades_per_hour, 2)}
        except Exception:
            return 0, {}
    
    def analyze_outcome_skew(self, trades: List[Dict]) -> Tuple[float, Dict]:
        """[Reuse from main detector]"""
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
        largest_share = max([vol / total for vol in outcome_volumes.values()]) if total > 0 else 0
        skew_score = min(abs(largest_share - 0.5) * 20, 10)
        
        sorted_outcomes = sorted(outcome_volumes.items(), key=lambda x: x[1], reverse=True)
        
        return skew_score, {
            'outcome_distribution': {outcome: round(vol / total, 3) 
                                    for outcome, vol in sorted_outcomes},
            'largest_outcome_share': round(largest_share, 3)
        }
    
    def analyze_whale_accumulation(self, trades: List[Dict]) -> Tuple[float, Dict]:
        """[Reuse from main detector]"""
        if not trades:
            return 0, {}
        
        address_trades = defaultdict(list)
        
        for trade in trades:
            try:
                address = trade.get('maker', trade.get('taker', 'unknown'))
                size = float(trade.get('size', 0))
                address_trades[address].append({'size': size})
            except (KeyError, ValueError):
                continue
        
        whale_data = []
        for address, trade_list in address_trades.items():
            total_size = sum(t['size'] for t in trade_list)
            num_trades = len(trade_list)
            
            if num_trades >= 2:
                whale_data.append({
                    'total_position': total_size,
                    'num_trades': num_trades,
                })
        
        if not whale_data:
            return 0, {}
        
        top_position = max([w['total_position'] for w in whale_data])
        whale_score = min(top_position / 1000, 10)  # Normalize
        
        return whale_score, {'top_whale_position': top_position}
    
    def calculate_insider_probability(self, scores: Dict) -> float:
        """Combine indicators into probability score"""
        weights = {
            'concentration': 0.25,
            'velocity': 0.15,
            'skew': 0.20,
            'movement': 0.15,
            'whale': 0.25
        }
        
        weighted_score = (
            scores.get('concentration', 0) * weights['concentration'] +
            scores.get('velocity', 0) * weights['velocity'] +
            scores.get('skew', 0) * weights['skew'] +
            scores.get('whale', 0) * weights['whale']
        )
        
        return min(weighted_score / 10, 1.0)
    
    def get_market_price_at_timestamp(self, trades: List[Dict], timestamp: float) -> Optional[float]:
        """Get the best estimate of market price at a specific timestamp"""
        nearby_trades = sorted(
            [t for t in trades 
             if abs(float(t.get('timestamp', t.get('createdAt', 0))) - timestamp) < 300],
            key=lambda x: abs(float(x.get('timestamp', x.get('createdAt', 0))) - timestamp)
        )
        
        if nearby_trades:
            return float(nearby_trades[0].get('price', nearby_trades[0].get('executionPrice', 0)))
        return None
    
    def get_outcome_skew_for_outcome(self, trades: List[Dict], target_outcome: str) -> float:
        """Get the probability/skew toward a specific outcome"""
        outcome_volumes = defaultdict(float)
        
        for trade in trades:
            try:
                outcome = trade.get('outcome', 'unknown')
                size = float(trade.get('size', 0))
                outcome_volumes[outcome] += size
            except (KeyError, ValueError):
                continue
        
        total = sum(outcome_volumes.values())
        if total == 0:
            return 0.5
        
        return outcome_volumes.get(target_outcome, 0) / total
    
    def find_signal_point(self, trades: List[Dict]) -> Tuple[float, float]:
        """
        Find the point where insider trading signal becomes strongest
        Returns: (timestamp, insider_probability)
        """
        if len(trades) < 10:
            return None, None
        
        trades_sorted = sorted(
            trades,
            key=lambda x: x.get('timestamp', x.get('createdAt', 0))
        )
        
        # Analyze in windows, find point of max signal strength
        max_signal = 0
        signal_timestamp = None
        
        for i in range(10, len(trades_sorted)):
            window_trades = trades_sorted[:i]
            
            concentration_score, _ = self.analyze_position_concentration(window_trades)
            velocity_score, _ = self.analyze_volume_velocity(window_trades)
            skew_score, _ = self.analyze_outcome_skew(window_trades)
            whale_score, _ = self.analyze_whale_accumulation(window_trades)
            
            scores = {
                'concentration': concentration_score,
                'velocity': velocity_score,
                'skew': skew_score,
                'whale': whale_score,
                'movement': 0
            }
            
            signal = self.calculate_insider_probability(scores)
            
            if signal > max_signal:
                max_signal = signal
                signal_timestamp = float(
                    trades_sorted[i].get('timestamp', trades_sorted[i].get('createdAt', 0))
                )
        
        return signal_timestamp, max_signal
    
    def backtest_market(self, market: Dict) -> Optional[BacktestResult]:
        """Run backtest analysis on a resolved market"""
        market_id = market.get('id', '')
        market_title = market.get('title', market.get('question', ''))
        
        if not market_id:
            return None
        
        print(f"  🔍 Backtesting: {market_title[:60]}...")
        
        # Fetch all historical trades
        all_trades = self.fetch_historical_trades(market_id)
        if not all_trades or len(all_trades) < 5:
            return None
        
        # Find the strongest insider signal point
        signal_timestamp, insider_prob = self.find_signal_point(all_trades)
        if signal_timestamp is None:
            return None
        
        # Get trades up to signal point
        trades_at_signal = self.get_trades_before_timestamp(all_trades, signal_timestamp)
        
        # Get trades immediately after (24 hour window)
        trades_after_signal = self.get_trades_after_timestamp(
            all_trades, 
            signal_timestamp, 
            window_hours=24
        )
        
        # Analyze trades at signal point
        concentration_score, _ = self.analyze_position_concentration(trades_at_signal)
        velocity_score, _ = self.analyze_volume_velocity(trades_at_signal)
        skew_score, _ = self.analyze_outcome_skew(trades_at_signal)
        whale_score, _ = self.analyze_whale_accumulation(trades_at_signal)
        
        indicator_scores = {
            'Concentration': round(concentration_score, 2),
            'Velocity': round(velocity_score, 2),
            'Skew': round(skew_score, 2),
            'Whale': round(whale_score, 2),
        }
        
        # Get price before and after signal
        pre_signal_price = self.get_market_price_at_timestamp(trades_at_signal, signal_timestamp)
        post_signal_price = self.get_market_price_at_timestamp(all_trades, signal_timestamp + 3600)
        
        if pre_signal_price is None or post_signal_price is None:
            return None
        
        price_movement = post_signal_price - pre_signal_price
        price_movement_pct = (price_movement / pre_signal_price * 100) if pre_signal_price > 0 else 0
        
        # Determine which outcome the insider was betting on
        skew_before, outcome_skew_data = self.analyze_outcome_skew(trades_at_signal)
        if outcome_skew_data.get('outcome_distribution'):
            outcome_prediction = max(
                outcome_skew_data['outcome_distribution'].items(),
                key=lambda x: x[1]
            )[0]
        else:
            outcome_prediction = 'unknown'
        
        # Check market resolution
        market_history = self.fetch_market_history(market_id)
        market_resolved = market_history.get('resolutionSource') is not None
        actual_outcome = market_history.get('resolvedBy')
        time_to_resolution = None
        predicted_correctly = False
        
        if market_resolved and actual_outcome:
            resolution_timestamp = float(market_history.get('resolvedTime', signal_timestamp + 86400))
            time_to_resolution = (resolution_timestamp - signal_timestamp) / 3600
            predicted_correctly = (outcome_prediction == actual_outcome)
        
        return BacktestResult(
            market_id=market_id,
            market_title=market_title,
            signal_timestamp=signal_timestamp,
            analysis_timestamp=datetime.now().timestamp(),
            insider_probability=insider_prob,
            indicator_scores=indicator_scores,
            pre_signal_price=round(pre_signal_price, 4),
            post_signal_price=round(post_signal_price, 4),
            price_movement=round(price_movement, 4),
            price_movement_pct=round(price_movement_pct, 2),
            predicted_correctly=predicted_correctly,
            outcome_prediction=outcome_prediction,
            actual_outcome=actual_outcome,
            market_resolved=market_resolved,
            time_to_resolution_hours=time_to_resolution,
            trades_analyzed=len(trades_at_signal)
        )
    
    def run_backtest(self, num_markets: int = 30) -> List[BacktestResult]:
        """Run full backtest suite on resolved markets"""
        print(f"\n🧪 POLYMARKET BACKTEST ANALYSIS")
        print(f"⏰ Analyzing {num_markets} resolved markets")
        print("=" * 70)
        
        markets = self.fetch_resolved_markets(limit=num_markets)
        if not markets:
            print("❌ Failed to fetch markets")
            return []
        
        print(f"✅ Fetched {len(markets)} resolved markets\n")
        
        results = []
        for i, market in enumerate(markets, 1):
            result = self.backtest_market(market)
            if result:
                results.append(result)
            
            # Rate limiting
            if i % 10 == 0:
                print(f"   Progress: {i}/{len(markets)} markets analyzed...")
                time.sleep(1)
        
        return results
    
    def print_backtest_results(self, results: List[BacktestResult]):
        """Print formatted backtest results"""
        if not results:
            print("❌ No backtest results to display")
            return
        
        print(f"\n📊 BACKTEST RESULTS ({len(results)} markets)")
        print("=" * 80)
        
        # Calculate accuracy metrics
        predicted_correctly = sum(1 for r in results if r.predicted_correctly)
        accuracy = predicted_correctly / len(results) * 100 if results else 0
        
        avg_price_movement = statistics.mean([r.price_movement_pct for r in results])
        avg_insider_prob = statistics.mean([r.insider_probability for r in results])
        
        # Separate high-signal markets
        high_signal = [r for r in results if r.insider_probability > 0.6]
        very_high_signal = [r for r in results if r.insider_probability > 0.8]
        
        print(f"\n📈 OVERALL METRICS:")
        print(f"   Total markets analyzed: {len(results)}")
        print(f"   Markets resolved: {sum(1 for r in results if r.market_resolved)}")
        print(f"   Prediction accuracy: {accuracy:.1f}%")
        print(f"   Avg price movement after signal: {avg_price_movement:.2f}%")
        print(f"   Avg insider probability: {avg_insider_prob:.1%}")
        
        print(f"\n🚨 HIGH SIGNAL MARKETS:")
        print(f"   Insider Probability > 60%: {len(high_signal)} markets")
        print(f"   Insider Probability > 80%: {len(very_high_signal)} markets")
        
        if very_high_signal:
            print(f"\n   Very High Signal Markets (>80%):")
            for r in sorted(very_high_signal, key=lambda x: x.insider_probability, reverse=True)[:5]:
                print(f"      {r.market_title[:50]}")
                print(f"         Signal: {r.insider_probability:.1%} | Movement: {r.price_movement_pct:+.2f}%")
                print(f"         Prediction: {r.outcome_prediction} | Correct: {r.predicted_correctly}")
                print()
        
        print(f"\n📉 DETAILED BREAKDOWN:")
        print("-" * 80)
        
        for r in sorted(results, key=lambda x: x.insider_probability, reverse=True)[:10]:
            print(f"\n{r.market_title}")
            print(f"   Insider Probability: {r.insider_probability:.1%}")
            print(f"   Indicators:")
            for name, score in r.indicator_scores.items():
                bar = "█" * int(score) + "░" * (10 - int(score))
                print(f"      {name:.<18} {bar} {score:.1f}")
            
            print(f"   Market Response:")
            print(f"      Price before signal: {r.pre_signal_price}")
            print(f"      Price 1hr after: {r.post_signal_price}")
            print(f"      1-hour movement: {r.price_movement_pct:+.2f}%")
            
            if r.market_resolved:
                print(f"   Resolution:")
                print(f"      Predicted: {r.outcome_prediction} | Actual: {r.actual_outcome}")
                print(f"      Correct: {'✅ YES' if r.predicted_correctly else '❌ NO'}")
                if r.time_to_resolution_hours:
                    print(f"      Time to resolution: {r.time_to_resolution_hours:.1f}h")
            else:
                print(f"   Status: Market not yet resolved")
    
    def save_backtest_results(self, results: List[BacktestResult], filename: str = 'backtest_results.json'):
        """Save detailed backtest results to JSON"""
        json_data = [r.to_dict() for r in results]
        
        with open(filename, 'w') as f:
            json.dump(json_data, f, indent=2, default=str)
        
        print(f"\n✅ Detailed backtest results saved to {filename}")
    
    def analyze_indicator_effectiveness(self, results: List[BacktestResult]) -> Dict:
        """Analyze which indicators were most predictive"""
        print(f"\n📊 INDICATOR EFFECTIVENESS ANALYSIS")
        print("=" * 70)
        
        indicator_names = list(results[0].indicator_scores.keys()) if results else []
        indicator_effectiveness = {}
        
        for indicator in indicator_names:
            # Get all scores for this indicator
            scores = [r.indicator_scores[indicator] for r in results]
            
            # Separate correct and incorrect predictions
            correct_scores = [r.indicator_scores[indicator] 
                            for r in results if r.predicted_correctly]
            incorrect_scores = [r.indicator_scores[indicator] 
                              for r in results if not r.predicted_correctly]
            
            avg_correct = statistics.mean(correct_scores) if correct_scores else 0
            avg_incorrect = statistics.mean(incorrect_scores) if incorrect_scores else 0
            
            effectiveness = avg_correct - avg_incorrect if (correct_scores and incorrect_scores) else 0
            
            indicator_effectiveness[indicator] = {
                'avg_when_correct': round(avg_correct, 2),
                'avg_when_incorrect': round(avg_incorrect, 2),
                'effectiveness_delta': round(effectiveness, 2),
                'frequency_in_correct': len(correct_scores),
                'frequency_in_incorrect': len(incorrect_scores)
            }
        
        # Print ranked effectiveness
        ranked = sorted(
            indicator_effectiveness.items(),
            key=lambda x: x[1]['effectiveness_delta'],
            reverse=True
        )
        
        print(f"\nIndicator Effectiveness (ranked by predictive power):\n")
        for indicator, metrics in ranked:
            print(f"{indicator}:")
            print(f"   Avg score when prediction CORRECT: {metrics['avg_when_correct']:.2f}")
            print(f"   Avg score when prediction WRONG:   {metrics['avg_when_incorrect']:.2f}")
            print(f"   Effectiveness delta: {metrics['effectiveness_delta']:+.2f}")
            print()
        
        return indicator_effectiveness


def main():
    """Run backtesting"""
    backtester = PolymarketBacktester(lookback_days=30)
    
    try:
        results = backtester.run_backtest(num_markets=30)
        
        if results:
            backtester.print_backtest_results(results)
            backtester.analyze_indicator_effectiveness(results)
            backtester.save_backtest_results(results)
        else:
            print("❌ No successful backtest results")
        
    except KeyboardInterrupt:
        print("\n⏸️  Backtest cancelled by user")
    except Exception as e:
        print(f"❌ Error during backtest: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
