import sys
import os
import glob
import csv
import math

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.expandvars(r'%LOCALAPPDATA%\BacktestLab\live')

def load_symbol_data(symbol):
    # Load and merge min-*.csv and flow-*.csv
    min_files = sorted(glob.glob(os.path.join(BASE_DIR, symbol, 'min-*.csv')))
    flow_files = sorted(glob.glob(os.path.join(BASE_DIR, symbol, 'flow-*.csv')))
    
    min_rows = {}
    for mf in min_files:
        with open(mf, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for r in reader:
                min_rows[r['time']] = r
                
    flow_rows = {}
    for ff in flow_files:
        with open(ff, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for r in reader:
                flow_rows[r['time']] = r

    # Merge on timestamp (minute level)
    merged = []
    for t in sorted(min_rows.keys()):
        m = min_rows[t]
        f = flow_rows.get(t, {})
        try:
            row = {
                'time': t,
                'open': float(m['open']),
                'high': float(m['high']),
                'low': float(m['low']),
                'close': float(m['close']),
                'spreadAvg': float(m['spreadAvg']) if m['spreadAvg'] else 15.0,
                'bidVol': float(m['bidVol']) if m['bidVol'] else 0.0,
                'askVol': float(m['askVol']) if m['askVol'] else 0.0,
                'imbalance': float(m['imbalance']) if m['imbalance'] else 0.0,
                'depthUpdates': int(m['depthUpdates']) if m['depthUpdates'] else 0,
                'delta': float(f.get('delta', 0)),
                'cvd': float(f.get('cvd', 0)),
                'vwapDay': float(f.get('vwapDay', m['close'])) if f.get('vwapDay') else float(m['close']),
                'sdDay': float(f.get('sdDay', 10.0)) if f.get('sdDay') else 10.0,
                'poc': float(f.get('poc', m['close'])) if f.get('poc') else float(m['close']),
                'vah': float(f.get('vah', m['close'])) if f.get('vah') else float(m['close']),
                'val': float(f.get('val', m['close'])) if f.get('val') else float(m['close']),
                'ladderBid': float(f.get('ladderBid', 0)) if f.get('ladderBid') else 0.0,
                'ladderAsk': float(f.get('ladderAsk', 0)) if f.get('ladderAsk') else 0.0,
            }
            merged.append(row)
        except Exception as e:
            continue
    return merged

def backtest_dom_strategies(symbol, data):
    print("=" * 65)
    print(f"OVERNIGHT 9-HOUR ANALYSIS: {symbol}")
    print(f"Total Minutes Recorded: {len(data)} (~{len(data)/60:.1f} hours)")
    if not data: return
    
    closes = [d['close'] for d in data]
    print(f"Price Span: ${min(closes):.2f} - ${max(closes):.2f} (Swing: ${max(closes)-min(closes):.2f})")
    print(f"Start: {data[0]['time']} | End: {data[-1]['time']}")
    print("-" * 65)

    # 1. STRATEGY A: DOM Order Book Imbalance Exhaustion
    # When price is at 15-min extreme and Order Book Imbalance spikes against the move
    # (e.g. at 15-min High, but imbalance is strongly negative = sellers stacking wall)
    best_dom = None
    best_dom_net = -999999
    
    dom_results = []
    for lookback in [15, 20, 30]:
        for imb_thresh in [0.03, 0.05, 0.08, 0.12]:
            for tp in [35.0, 50.0, 70.0, 90.0] if 'BTC' in symbol else [1.5, 2.5, 3.5]:
                for sl in [25.0, 35.0, 45.0] if 'BTC' in symbol else [1.0, 1.5, 2.0]:
                    trades = []
                    i = lookback
                    while i < len(data) - 20:
                        window_high = max(d['high'] for d in data[i-lookback:i])
                        window_low = min(d['low'] for d in data[i-lookback:i])
                        curr = data[i]
                        
                        side = None
                        # Top of range + Ask Wall (Negative Imbalance) -> SELL
                        if curr['high'] >= window_high - (5.0 if 'BTC' in symbol else 0.2) and curr['imbalance'] <= -imb_thresh:
                            side = 'SELL'
                        # Bottom of range + Bid Wall (Positive Imbalance) -> BUY
                        elif curr['low'] <= window_low + (5.0 if 'BTC' in symbol else 0.2) and curr['imbalance'] >= imb_thresh:
                            side = 'BUY'
                            
                        if side:
                            entry = curr['close']
                            spread = curr['spreadAvg'] * (0.1 if 'BTC' in symbol else 0.01)
                            gross = 0.0
                            exit_idx = i + 1
                            for j in range(i+1, min(i+40, len(data))):
                                p = data[j]['close']
                                d = (p - entry) if side == 'BUY' else (entry - p)
                                if d >= tp:
                                    gross = tp
                                    exit_idx = j
                                    break
                                if d <= -sl:
                                    gross = -sl
                                    exit_idx = j
                                    break
                            else:
                                gross = d
                                exit_idx = min(i+40, len(data)) - 1
                                
                            pnl = (gross - spread) * (0.05 if 'BTC' in symbol else 1.0)
                            trades.append(pnl)
                            i = exit_idx + 1
                        else:
                            i += 1
                            
                    if len(trades) >= 3:
                        wins = [t for t in trades if t > 0]
                        losses = [t for t in trades if t <= 0]
                        wr = len(wins) / len(trades) * 100
                        net = sum(trades)
                        pf = sum(wins) / abs(sum(losses)) if losses and sum(losses) != 0 else 999.0
                        res = {
                            'lookback': lookback,
                            'imb_thresh': imb_thresh,
                            'tp': tp,
                            'sl': sl,
                            'trades': len(trades),
                            'win_rate': round(wr, 1),
                            'net_usd': round(net, 2),
                            'profit_factor': round(pf, 2)
                        }
                        dom_results.append(res)
                        if net > best_dom_net:
                            best_dom_net = net
                            best_dom = res

    dom_results.sort(key=lambda x: x['net_usd'], reverse=True)
    print("\n[STRATEGY 1] DOM Imbalance Wall Absorption (Top 3):")
    for r in dom_results[:3]:
        print(f"  • Lookback={r['lookback']}m, Imbalance={r['imb_thresh']}, TP={r['tp']}, SL={r['sl']} -> Trades={r['trades']}, WR={r['win_rate']}%, Net=+${r['net_usd']} USD, PF={r['profit_factor']}")

    # 2. STRATEGY B: CVD (Cumulative Volume Delta) Divergence
    # When price makes new high but CVD fails to make new high -> Bearish Reversal
    # When price makes new low but CVD fails to make new low -> Bullish Reversal
    cvd_results = []
    for lookback in [15, 20, 30]:
        for tp in [40.0, 60.0, 80.0] if 'BTC' in symbol else [1.5, 2.5]:
            for sl in [25.0, 35.0] if 'BTC' in symbol else [1.0, 1.5]:
                trades = []
                i = lookback
                while i < len(data) - 20:
                    prev_p_high = max(d['high'] for d in data[i-lookback:i])
                    prev_p_low = min(d['low'] for d in data[i-lookback:i])
                    prev_cvd_high = max(d['cvd'] for d in data[i-lookback:i])
                    prev_cvd_low = min(d['cvd'] for d in data[i-lookback:i])
                    
                    curr = data[i]
                    side = None
                    # Price breaks high, but CVD is lower (Absorption of aggressive buyers)
                    if curr['high'] > prev_p_high and curr['cvd'] < prev_cvd_high:
                        side = 'SELL'
                    elif curr['low'] < prev_p_low and curr['cvd'] > prev_cvd_low:
                        side = 'BUY'
                        
                    if side:
                        entry = curr['close']
                        spread = curr['spreadAvg'] * (0.1 if 'BTC' in symbol else 0.01)
                        gross = 0.0
                        exit_idx = i + 1
                        for j in range(i+1, min(i+40, len(data))):
                            p = data[j]['close']
                            d = (p - entry) if side == 'BUY' else (entry - p)
                            if d >= tp:
                                gross = tp
                                exit_idx = j
                                break
                            if d <= -sl:
                                gross = -sl
                                exit_idx = j
                                break
                        else:
                            gross = d
                            exit_idx = min(i+40, len(data)) - 1
                        pnl = (gross - spread) * (0.05 if 'BTC' in symbol else 1.0)
                        trades.append(pnl)
                        i = exit_idx + 1
                    else:
                        i += 1
                        
                if len(trades) >= 3:
                    wins = [t for t in trades if t > 0]
                    losses = [t for t in trades if t <= 0]
                    wr = len(wins) / len(trades) * 100
                    net = sum(trades)
                    pf = sum(wins) / abs(sum(losses)) if losses and sum(losses) != 0 else 999.0
                    cvd_results.append({
                        'lookback': lookback,
                        'tp': tp,
                        'sl': sl,
                        'trades': len(trades),
                        'win_rate': round(wr, 1),
                        'net_usd': round(net, 2),
                        'profit_factor': round(pf, 2)
                    })

    cvd_results.sort(key=lambda x: x['net_usd'], reverse=True)
    print("\n[STRATEGY 2] CVD Volume Delta Divergence (Top 3):")
    for r in cvd_results[:3]:
        print(f"  • Lookback={r['lookback']}m, TP={r['tp']}, SL={r['sl']} -> Trades={r['trades']}, WR={r['win_rate']}%, Net=+${r['net_usd']} USD, PF={r['profit_factor']}")

    # 3. STRATEGY C: Anchored VWAP + DOM Ladder Expansion
    # Fading price back to VWAP when price is stretched >= 1.5 SD
    vwap_results = []
    for sd_mult in [1.2, 1.5, 1.8, 2.0]:
        for tp_ratio in [0.5, 0.8, 1.0]: # Return toward VWAP
            for sl in [30.0, 45.0, 60.0] if 'BTC' in symbol else [1.0, 1.5, 2.0]:
                trades = []
                i = 20
                while i < len(data) - 20:
                    curr = data[i]
                    vwap = curr['vwapDay']
                    sd = curr['sdDay']
                    diff = curr['close'] - vwap
                    
                    side = None
                    if diff >= sd_mult * sd and sd > (15.0 if 'BTC' in symbol else 0.5):
                        side = 'SELL'
                    elif diff <= -sd_mult * sd and sd > (15.0 if 'BTC' in symbol else 0.5):
                        side = 'BUY'
                        
                    if side:
                        entry = curr['close']
                        spread = curr['spreadAvg'] * (0.1 if 'BTC' in symbol else 0.01)
                        target_dist = abs(diff) * tp_ratio
                        gross = 0.0
                        exit_idx = i + 1
                        for j in range(i+1, min(i+50, len(data))):
                            p = data[j]['close']
                            d = (p - entry) if side == 'BUY' else (entry - p)
                            if d >= target_dist:
                                gross = target_dist
                                exit_idx = j
                                break
                            if d <= -sl:
                                gross = -sl
                                exit_idx = j
                                break
                        else:
                            gross = d
                            exit_idx = min(i+50, len(data)) - 1
                        pnl = (gross - spread) * (0.05 if 'BTC' in symbol else 1.0)
                        trades.append(pnl)
                        i = exit_idx + 1
                    else:
                        i += 1
                        
                if len(trades) >= 3:
                    wins = [t for t in trades if t > 0]
                    losses = [t for t in trades if t <= 0]
                    wr = len(wins) / len(trades) * 100
                    net = sum(trades)
                    pf = sum(wins) / abs(sum(losses)) if losses and sum(losses) != 0 else 999.0
                    vwap_results.append({
                        'sd_mult': sd_mult,
                        'tp_ratio': tp_ratio,
                        'sl': sl,
                        'trades': len(trades),
                        'win_rate': round(wr, 1),
                        'net_usd': round(net, 2),
                        'profit_factor': round(pf, 2)
                    })

    vwap_results.sort(key=lambda x: x['net_usd'], reverse=True)
    print("\n[STRATEGY 3] Anchored VWAP Standard Deviation Reversion (Top 3):")
    for r in vwap_results[:3]:
        print(f"  • SD_Mult={r['sd_mult']}, TP_Ratio={r['tp_ratio']}, SL={r['sl']} -> Trades={r['trades']}, WR={r['win_rate']}%, Net=+${r['net_usd']} USD, PF={r['profit_factor']}")

if __name__ == '__main__':
    btc_data = load_symbol_data('BTCUSD')
    backtest_dom_strategies('BTCUSD', btc_data)
    
    gold_data = load_symbol_data('GOLD-PERP')
    backtest_dom_strategies('GOLD-PERP', gold_data)

    eth_data = load_symbol_data('ETHUSD')
    backtest_dom_strategies('ETHUSD', eth_data)
