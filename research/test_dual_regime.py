import sys
sys.stdout.reconfigure(encoding='utf-8')
from research.quant_evolution_engine import load_continuous_data

data = load_continuous_data(r'd:\cbot-atgvt\data\live_multi_market_feed.csv')
btc_p = data['BTCUSD']
btc_sp = data['BTC_SP']
gold_p = data['GOLD-PERP']
gold_sp = data['GOLD_SP']

print(f"Total Snapshots: {len(btc_p)}")

# Dual-Regime on BTC:
# If 30-snap range is small: CHOP REGIME -> Fade edges
# If 30-snap range is large: BREAKOUT REGIME -> Ride breakout with Smart Runner
best_dual = None
best_dual_net = -999999

results = []
for chop_range in [25.0, 30.0, 35.0]:
    for trend_range in [45.0, 55.0, 65.0]:
        for chop_tp in [15.0, 20.0, 25.0]:
            for trend_trail in [35.0, 50.0, 60.0]:
                trades = []
                i = 30
                while i < len(btc_p) - 20:
                    window = btc_p[i-30:i]
                    w_high = max(window)
                    w_low = min(window)
                    w_range = w_high - w_low
                    curr = btc_p[i]
                    
                    side = None
                    mode = None
                    
                    # Regime 1: CHOP
                    if w_range < chop_range:
                        if curr <= w_low + 3.0:
                            side = 'BUY'
                            mode = 'CHOP'
                        elif curr >= w_high - 3.0:
                            side = 'SELL'
                            mode = 'CHOP'
                    # Regime 2: BREAKOUT
                    elif w_range >= trend_range:
                        if curr > w_high:
                            side = 'BUY'
                            mode = 'BREAKOUT'
                        elif curr < w_low:
                            side = 'SELL'
                            mode = 'BREAKOUT'
                    
                    if side:
                        entry = curr
                        spread = btc_sp[i] * 0.1
                        exit_idx = i + 1
                        gross = 0.0
                        
                        if mode == 'CHOP':
                            for j in range(i+1, min(i+20, len(btc_p))):
                                p = btc_p[j]
                                d = (p - entry) if side == 'BUY' else (entry - p)
                                if d >= chop_tp:
                                    gross = chop_tp
                                    exit_idx = j
                                    break
                                if d <= -20.0:
                                    gross = -20.0
                                    exit_idx = j
                                    break
                            else:
                                gross = d
                                exit_idx = min(i+20, len(btc_p)) - 1
                        else: # BREAKOUT
                            best_d = 0.0
                            for j in range(i+1, min(i+45, len(btc_p))):
                                p = btc_p[j]
                                d = (p - entry) if side == 'BUY' else (entry - p)
                                if d > best_d: best_d = d
                                if best_d > trend_trail and (best_d - d) >= (trend_trail * 0.5):
                                    gross = best_d - (trend_trail * 0.5)
                                    exit_idx = j
                                    break
                                if d <= -25.0:
                                    gross = -25.0
                                    exit_idx = j
                                    break
                            else:
                                gross = d
                                exit_idx = min(i+45, len(btc_p)) - 1
                                
                        pnl = (gross - spread) * 0.05
                        trades.append(pnl)
                        i = exit_idx + 1
                    else:
                        i += 1
                
                if len(trades) >= 5:
                    wins = [t for t in trades if t > 0]
                    losses = [t for t in trades if t <= 0]
                    wr = len(wins) / len(trades) * 100
                    net = sum(trades)
                    pf = sum(wins) / abs(sum(losses)) if losses and sum(losses) != 0 else 999.0
                    r = {
                        'chop_range': chop_range,
                        'trend_range': trend_range,
                        'chop_tp': chop_tp,
                        'trend_trail': trend_trail,
                        'trades': len(trades),
                        'wr': round(wr, 1),
                        'net': round(net, 2),
                        'pf': round(pf, 2)
                    }
                    results.append(r)
                    if net > best_dual_net:
                        best_dual_net = net
                        best_dual = r

results.sort(key=lambda x: x['net'], reverse=True)
print("=== DUAL-REGIME BTC BACKTEST TOP 5 ===")
for r in results[:5]:
    print(r)
