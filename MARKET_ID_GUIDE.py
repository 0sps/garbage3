#!/usr/bin/env python3
"""
Complete Guide: What to Do With Market IDs
Demonstrates all the ways to use market IDs to track and analyze markets
"""

import requests
import json
from datetime import datetime

class MarketIDGuide:
    """Shows you exactly what you can do with market IDs"""
    
    @staticmethod
    def guide():
        print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                   WHAT YOU CAN DO WITH MARKET IDs                          ║
╚════════════════════════════════════════════════════════════════════════════╝

The market ID is your KEY to everything. Here are all the ways you can use it:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1️⃣  VIEW THE MARKET ON POLYMARKET UI
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   The EASIEST way to use market IDs:
   
   Market ID: 0x5eed579ff6763914d78a966c83473ba2485ac8910d0a0914eef6d9fcb33085de
   
   → Go to: https://polymarket.com/markets
   → Search for the market ID in the search bar
   → Or: Copy the market_slug from our JSON results
   
   Once you're viewing the market, you can:
   ✓ See live price movements
   ✓ See recent trades in real-time
   ✓ Place your own trades
   ✓ Monitor odds as they change
   ✓ Read market description & resolution criteria

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

2️⃣  MONITOR PRICE MOVEMENTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   Write down the odds when we detect EXTREME SKEW:
   
   Example from our scan:
   • Market: NCAAB: Arizona State vs. Nevada
   • Suspicious Score: 10/10 (EXTREME)
   • Arizona State showing as 99%+ likely
   
   ACTION: 
   1. Note the current odds (99.5% for Arizona)
   2. Check the market 1 hour later
   3. Check again 24 hours later
   4. Compare how much the odds moved
   
   EXPECTED: If our insider signal is correct, you'll see:
   → Large swings (up to +/- 10-20% movement)
   → Movement in the direction of the initial skew
   → This validates our detection algorithm

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

3️⃣  TRADE ON THE MARKET
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   If you have conviction in our signal:
   
   STRATEGY 1 - Follow the Skew:
   • Market shows 99% Arizona, 1% Nevada
   • Our algorithm says: EXTREME SKEW (10/10)
   • Interpretation: Market knows Arizona will win
   • Trade: Bet on Arizona at 99¢ (or buy YES at 0.99)
   
   STRATEGY 2 - Fade Extreme Moves:
   • If a market suddenly goes 99% one direction
   • Could be a pump-and-dump or manipulation
   • Trade: Bet AGAINST the extreme (contrarian)
   • Wait for correction back to 60-70% range
   
   STRATEGY 3 - Monitor for Validation:
   • Don't trade yet - just watch
   • Run our scan every hour
   • See if the same markets stay extreme
   • See if prices move as predicted
   • Build confidence before risking money

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

4️⃣  CORRELATE WITH EVENTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   Use market IDs to investigate WHY there's extreme skew:
   
   Our scan found: "NCAAB: Arizona State vs. Nevada - 10/10 EXTREME"
   
   ACTION:
   1. Google: "Arizona State Nevada game news"
   2. Check if key players are injured
   3. Check if game was postponed
   4. Check if one team is resting starters
   5. Check social media for betting sharp picks
   
   RESULT: If you find news → VALIDATES our signal
           If no news → Market might have inside info!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

5️⃣  TRACK THE OUTCOME
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   After the market resolves, verify our accuracy:
   
   Example Timeline:
   Jan 9, 3pm:  Our scan → Arizona 99%, Score 10/10
   Jan 9, 8pm:  Arizona wins 85-72
   Jan 10, 2am: Market resolves to "Arizona" (YES winners get paid)
   
   RECORD: ✓ CORRECT prediction!
           → Validates our skew detection
           → Adds confidence for next signal
           
   This is exactly what our BACKTEST script does automatically!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

6️⃣  BUILD A MONITORING DASHBOARD
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   Create a spreadsheet to track signals over time:
   
   | Market ID | Market Title | Initial Skew | Current Skew | Moved? | Outcome |
   |-----------|--------------|--------------|--------------|--------|---------|
   | 0x5eed... | AZ vs NEV    | 99%/1%       | 98%/2%       | No     | TBD     |
   | 0x8901... | TN vs Duke   | 95%/5%       | 92%/8%       | Yes!   | TBD     |
   | 0x8945... | Clips vs ORL  | 97%/3%       | 89%/11%      | Yes!   | TBD     |
   
   This shows which signals are MOST PREDICTIVE of price movement!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

7️⃣  AUTOMATED MONITORING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   You could run our scanner every 1 hour:
   
   • 9am:  Run scan → Find extreme skew markets
   • 10am: Run scan → See if odds moved
   • 11am: Run scan → Did predictions come true?
   
   This builds a real-time validation of the system!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 RECOMMENDED NEXT STEPS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STEP 1: VALIDATE (This Week)
   ✓ Take the top 5 market IDs from our scan
   ✓ Open each on polymarket.com
   ✓ Record the current odds
   ✓ Set reminders to check prices in 24-48 hours
   ✓ See how much they move
   
STEP 2: BACKTEST (This Week)
   ✓ Run: python backtest_analyzer.py quick
   ✓ See historical accuracy of our signals
   ✓ Compare prediction vs actual outcomes
   ✓ Measure our edge
   
STEP 3: TRADE (If Validated)
   ✓ Once you see prices moving as predicted
   ✓ Place small test trades
   ✓ Track performance
   ✓ Scale up if it works

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 EXAMPLE - WHAT A MARKET LOOKS LIKE ON POLYMARKET:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

You'll see something like:

   NCAAB: Arizona State Sun Devils vs. Nevada Wolf Pack

   Arizona State    ████████████████████████████ 98%    $0.98
   Nevada          ██ 2%                                $0.02
   
   Volume: $1.2M in last 24 hours
   Open Interest: $340K
   
   Recent Trades:
   • Someone bought 500 YES shares at $0.97 (2 hours ago) ← Large order!
   • Someone bought 200 YES shares at $0.96 (5 hours ago)
   • Market moved from 85% → 98% in 24 hours ← HUGE MOVE!
   
   👆 THIS is the kind of price movement our signals predict!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Questions? Run:
   python quick_scan.py           # Get fresh market IDs
   python market_detail_lookup.py  # Look up specific market
   python backtest_analyzer.py    # Validate on historical data

""")

if __name__ == "__main__":
    MarketIDGuide.guide()
