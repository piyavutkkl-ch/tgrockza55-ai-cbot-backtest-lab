import sys, os, csv
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from research.find_high_profit_strategy import load_data, simulate_strategy

bars = load_data('BTCUSD')

def logic_btc_momentum_follow(bars, i, trades):
    curr = bars[i]
    if curr['spreadAvg'] > 20.0: return None
    
    close = curr['close']
    ema20 = curr['ema20']
    ema50 = curr['ema50']
    ema200 = curr['ema200']
    delta = curr.get('delta', 0.0)
    imb = curr.get('imbalance', 0.0)
    
    h20 = max(bars[k]['high'] for k in range(i-20, i))
    l20 = min(bars[k]['low'] for k in range(i-20, i))

    # Trend filter
    is_bull = (ema20 > ema50) and (ema50 > ema200) and (close > ema20)
    is_bear = (ema20 < ema50) and (ema50 < ema200) and (close < ema20)

    # Bullish Trend Following Breakout
    if is_bull and close >= h20 and delta >= 15 and imb >= 0.01:
        return {'side': 'Buy', 'sl_dist': 120.0, 'tp_dist': 300.0, 'use_be': True}

    # Bearish Trend Following Breakout
    if is_bear and close <= l20 and delta <= -15 and imb <= -0.01:
        return {'side': 'Sell', 'sl_dist': 120.0, 'tp_dist': 300.0, 'use_be': True}

    return None

res = simulate_strategy(bars, logic_btc_momentum_follow, symbol='BTCUSD')
print(f"BTCUSD TREND FOLLOWING BREAKOUT:")
print(f"  Trades: {res['trades']} | Win Rate: {res['win_rate']}% ({res['wins']}W / {res['losses']}L)")
print(f"  Gross Profit: +${res['gross_win']} | Gross Loss: -${res['gross_loss']}")
print(f"  Net Profit: +${res['net_pnl']} USD | Profit Factor: {res['pf']} | Max DD: ${res['max_dd']} USD")
