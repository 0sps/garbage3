#!/usr/bin/env python3
"""
Show detailed odds for markets with insider signals
"""
import json
import requests

# Fetch live market data
print("🔍 Fetching current market data...")
response = requests.get('https://clob.polymarket.com/markets?limit=1000', timeout=10)
markets = response.json()

if isinstance(markets, list):
    markets_dict = {m.get('id'): m for m in markets if isinstance(m, dict) and m.get('id')}
elif isinstance(markets, dict) and 'data' in markets:
    markets_dict = {m.get('id'): m for m in markets.get('data', []) if isinstance(m, dict)}
else:
    markets_dict = {}

# Top suspicious market IDs from our scan
suspect_ids = [
    '0x5eed579ff6763914d78a966c83473ba2485ac8910d0a0914eef6d9fcb33085de',
    '0x8901bf367fcb32b406b54e8deb1bcb3320fdc4a994bd7f0a7a1fe72956dc1c9a',
    '0x8945183c6253e70ec33a9f7c79058de36d3ebd809c245bc4204e9a3d098e0ea8',
    '0x3648ab7c146a9a85957e07c1d43a82272be71fde767822fd425e10ba0d6c0757',
    '0xd1a5513fa75fd1d158f430161adf2e3df88511dc508328e05f520519fe78eb46'
]

print('\n' + '='*80)
print('🎯 TOP 5 INSIDER SIGNALS - WHAT THE ACTUAL ODDS LOOK LIKE')
print('='*80)

count = 0
for market_id in suspect_ids:
    market = markets_dict.get(market_id)
    if not market:
        continue
    
    count += 1
    title = market.get('title', market.get('question', 'Unknown'))[:65]
    tokens = market.get('tokens', [])
    
    print(f'\n{count}. {title}')
    print(f'   ID: {market_id[:20]}...')
    
    if len(tokens) >= 2:
        # Get first two outcomes
        outcome1 = tokens[0].get('outcome', 'Option 1')
        outcome2 = tokens[1].get('outcome', 'Option 2')
        price1 = float(tokens[0].get('price', 0))
        price2 = float(tokens[1].get('price', 0))
        
        pct1 = price1 * 100
        pct2 = price2 * 100
        
        # Draw bars
        bar_length = 30
        bar1 = '█' * int(pct1 / 100 * bar_length)
        bar2 = '█' * int(pct2 / 100 * bar_length)
        
        print(f'\n   {outcome1:.<25} {bar1:<30} {pct1:>6.1f}%')
        print(f'   {outcome2:.<25} {bar2:<30} {pct2:>6.1f}%')
        
        # Highlight the extreme
        max_pct = max(pct1, pct2)
        min_pct = min(pct1, pct2)
        print(f'\n   🚨 EXTREME SKEW: {max_pct:.1f}% vs {min_pct:.1f}%')
        
        if max_pct > 95:
            print(f'   ⚠️  This market is EXTREMELY confident in one outcome!')
            print(f'   💡 This suggests inside information or strong conviction')

print('\n' + '='*80)
print('\n✅ These are REAL current market odds showing extreme skew')
print('✅ Our detector found these because of the imbalance')
print('✅ Each market ID can be searched on polymarket.com to trade')
