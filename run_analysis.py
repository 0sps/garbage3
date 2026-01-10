#!/usr/bin/env python3
"""
Unified Polymarket Prediction & Backtesting Suite
Identifies insider trading signals that predict large line movements
"""

import sys
import argparse
from insider_trading_detector import PolymarketInsiderDetector
from backtest_analyzer import PolymarketBacktester

def run_live_analysis():
    """Run real-time insider detection on active markets"""
    print("\n" + "="*80)
    print("🔴 LIVE MARKET ANALYSIS - PREDICTING LARGE LINE CHANGES")
    print("="*80)
    
    detector = PolymarketInsiderDetector(lookback_days=7)
    results = detector.run_detection(num_markets=30)
    
    if results:
        detector.print_results(results, top_n=15)
        
        # Save to file
        import json
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
        
        with open('live_analysis_results.json', 'w') as f:
            json.dump(json_results, f, indent=2)
        
        print(f"\n✅ Live analysis saved to live_analysis_results.json")

def run_backtest():
    """Run backtesting on resolved markets to validate accuracy"""
    print("\n" + "="*80)
    print("📊 HISTORICAL BACKTEST - VALIDATING PREDICTION ACCURACY")
    print("="*80)
    
    backtester = PolymarketBacktester(lookback_days=30)
    results = backtester.run_backtest(num_markets=30)
    
    if results:
        backtester.print_backtest_results(results)
        backtester.analyze_indicator_effectiveness(results)
        backtester.save_backtest_results(results)

def run_quick_backtest():
    """Quick backtest with fewer markets"""
    print("\n" + "="*80)
    print("⚡ QUICK BACKTEST (10 markets)")
    print("="*80)
    
    backtester = PolymarketBacktester(lookback_days=30)
    results = backtester.run_backtest(num_markets=10)
    
    if results:
        backtester.print_backtest_results(results)
        backtester.save_backtest_results(results, 'quick_backtest_results.json')

def main():
    parser = argparse.ArgumentParser(
        description="Polymarket Insider Trading Detector - Predicts Large Line Changes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_analysis.py live          # Run live market analysis
  python run_analysis.py backtest      # Full backtest (30 markets)
  python run_analysis.py quick         # Quick backtest (10 markets)
  python run_analysis.py both          # Run both live and backtest
        """
    )
    
    parser.add_argument(
        'mode',
        choices=['live', 'backtest', 'quick', 'both'],
        help='Analysis mode to run'
    )
    
    args = parser.parse_args()
    
    try:
        if args.mode == 'live':
            run_live_analysis()
        elif args.mode == 'backtest':
            run_backtest()
        elif args.mode == 'quick':
            run_quick_backtest()
        elif args.mode == 'both':
            run_live_analysis()
            print("\n\n")
            run_backtest()
        
        print("\n✅ Analysis complete!")
        
    except KeyboardInterrupt:
        print("\n⏸️  Analysis cancelled by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
