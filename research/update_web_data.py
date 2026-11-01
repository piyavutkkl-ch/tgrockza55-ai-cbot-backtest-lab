import os
import sys
import json
import csv
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')
from research.analyze_overnight_dom_flow import load_symbol_data

def generate_dom_absorption_strategy(symbol, lookback, imb_thresh, tp_usd, sl_usd, risk_rr, trade_size):
    data = load_symbol_data(symbol)
    if not data: return None

    balance = 100.0
    peak = 100.0
    max_dd = 0.0
    equity_curve = [[data[0]['time'], round(balance, 2)]]
    trades = []
    
    i = lookback
    while i < len(data) - 20:
        window_high = max(d['high'] for d in data[i-lookback:i])
        window_low = min(d['low'] for d in data[i-lookback:i])
        curr = data[i]
        
        tol = (window_high - window_low) * 0.08
        current_bid = curr['close']
        current_ask = curr['close']
        imbalance = curr['imbalance']
        
        side = None
        trigger_reason = ""
        dom_reason = ""
        structure_reason = ""

        # ขา SELL: ราคาแตะโซน High + Ask Wall (Negative Imbalance)
        if current_bid >= window_high - tol and imbalance <= -imb_thresh:
            side = 'Sell'
            trigger_reason = f"ราคาแตะแนวต้าน High {window_high:.2f} + Ask Wall หนาแน่น"
            dom_reason = f"Order Book Ask Imbalance = {imbalance:+.3f} (มีคนตั้งขายดูดซับแรงซื้อ)"
            structure_reason = f"Exhaustion Zone ขอบบน 15m High ({window_high:.2f})"
        # ขา BUY: ราคาแตะโซน Low + Bid Wall (Positive Imbalance)
        elif current_ask <= window_low + tol and imbalance >= imb_thresh:
            side = 'Buy'
            trigger_reason = f"ราคาแตะแนวรับ Low {window_low:.2f} + Bid Wall หนาแน่น"
            dom_reason = f"Order Book Bid Imbalance = {imbalance:+.3f} (มีคนตั้งรับซื้อดูดซับแรงขาย)"
            structure_reason = f"Exhaustion Zone ขอบล่าง 15m Low ({window_low:.2f})"

        if side:
            entry_time = curr['time']
            entry_price = curr['close']
            spread_usd = curr['spreadAvg'] * (0.1 if 'BTC' in symbol else 0.01)
            
            sl_price = (entry_price - sl_usd) if side == 'Buy' else (entry_price + sl_usd)
            tp_price = (entry_price + tp_usd) if side == 'Buy' else (entry_price - tp_usd)

            gross = 0.0
            exit_time = None
            exit_price = None
            exit_reason = None
            exit_idx = i + 1

            for j in range(i + 1, min(i + 40, len(data))):
                p = data[j]['close']
                d = (p - entry_price) if side == 'Buy' else (entry_price - p)
                
                # TP
                if d >= tp_usd:
                    gross = tp_usd
                    exit_price = tp_price
                    exit_reason = "TP"
                    exit_time = data[j]['time']
                    exit_idx = j
                    break
                # SL
                if d <= -sl_usd:
                    gross = -sl_usd
                    exit_price = sl_price
                    exit_reason = "SL"
                    exit_time = data[j]['time']
                    exit_idx = j
                    break
                # Smart DOM Exit
                if d >= tp_usd * 0.5:
                    if side == 'Buy' and data[j]['imbalance'] <= -(imb_thresh * 1.5):
                        gross = d
                        exit_price = p
                        exit_reason = "SmartExit"
                        exit_time = data[j]['time']
                        exit_idx = j
                        break
                    elif side == 'Sell' and data[j]['imbalance'] >= (imb_thresh * 1.5):
                        gross = d
                        exit_price = p
                        exit_reason = "SmartExit"
                        exit_time = data[j]['time']
                        exit_idx = j
                        break
            else:
                gross = d
                exit_price = data[min(i + 40, len(data)) - 1]['close']
                exit_reason = "Timeout"
                exit_time = data[min(i + 40, len(data)) - 1]['time']
                exit_idx = min(i + 40, len(data)) - 1

            net_pnl = (gross - spread_usd) * trade_size
            balance += net_pnl
            if balance > peak: peak = balance
            dd = peak - balance
            if dd > max_dd: max_dd = dd
            
            equity_curve.append([exit_time, round(balance, 2)])

            # Build candle snippet around trade (7 bars before, holding bars, 5 bars after)
            c_start = max(0, i - 7)
            c_end = min(len(data), exit_idx + 6)
            candles = []
            for k in range(c_start, c_end):
                bar = data[k]
                t_str = bar['time'].split(' ')[-1] if ' ' in bar['time'] else bar['time']
                candles.append({
                    'time': t_str,
                    'open': bar['open'],
                    'high': bar['high'],
                    'low': bar['low'],
                    'close': bar['close'],
                    'vwap': bar['vwapDay'],
                    'is_entry': (k == i),
                    'is_exit': (k == exit_idx),
                    'is_holding': (i <= k <= exit_idx)
                })

            trade_obj = {
                'id': len(trades) + 1,
                'time': entry_time,
                'exit_time': exit_time,
                'side': side,
                'entry_p': round(entry_price, 2),
                'exit_p': round(exit_price, 2),
                'sl_p': round(sl_price, 2),
                'tp_p': round(tp_price, 2),
                'gross': round(gross * trade_size, 2),
                'net': round(net_pnl, 2),
                'reason': exit_reason,
                'dur_min': exit_idx - i,
                'spread': round(spread_usd, 2),
                'comm': 0.0,
                'entry_reason': trigger_reason,
                'dom_reason': dom_reason,
                'structure_reason': structure_reason,
                'analysis': f"กลยุทธ์ DOM Absorption: เข้า {side} ตามกำแพงสมุดคำสั่ง ณ จุดเลี้ยวขอบบน/ล่าง ปิดด้วย {exit_reason} กำไร {net_pnl:+.2f} USD",
                'candles': candles,
                'entry_idx_rel': i - c_start,
                'exit_idx_rel': exit_idx - c_start
            }
            trades.append(trade_obj)
            i = exit_idx + 1
        else:
            i += 1

    wins = [t for t in trades if t['net'] > 0]
    losses = [t for t in trades if t['net'] <= 0]
    win_rate = round(len(wins) / len(trades) * 100.0, 1) if trades else 0
    gross_win = sum(t['net'] for t in wins)
    gross_loss = abs(sum(t['net'] for t in losses))
    pf = round(gross_win / gross_loss, 2) if gross_loss > 0 else 999.0

    summary = {
        'total_trades': len(trades),
        'wins': len(wins),
        'losses': len(losses),
        'win_rate': win_rate,
        'net_profit': round(balance - 100.0, 2),
        'profit_factor': pf,
        'max_drawdown': round(max_dd, 2),
        'avg_pnl': round((balance - 100.0) / len(trades), 2) if trades else 0,
        'avg_duration': round(sum(t['dur_min'] for t in trades) / len(trades), 1) if trades else 0,
        'tp_count': len([t for t in trades if t['reason'] == 'TP']),
        'sl_count': len([t for t in trades if t['reason'] == 'SL']),
        'timeout_count': len([t for t in trades if t['reason'] == 'SmartExit'])
    }

    return {
        'name': f"DOM Wall Absorption ({symbol})",
        'summary': summary,
        'trades': trades,
        'equity_curve': equity_curve
    }

def update_web_database():
    json_path = r'd:\cbot-atgvt\docs\data\backtest_data.json'
    with open(json_path, 'r', encoding='utf-8') as f:
        db = json.load(f)

    print("Generating DOM Absorption for BTCUSD...")
    btc_strat = generate_dom_absorption_strategy('BTCUSD', lookback=15, imb_thresh=0.03, tp_usd=50.0, sl_usd=25.0, risk_rr=2.0, trade_size=0.05)
    if btc_strat:
        db['dom_absorption_btc'] = btc_strat
        print(f"BTC Strategy: {btc_strat['summary']}")

    print("Generating DOM Absorption for ETHUSD...")
    eth_strat = generate_dom_absorption_strategy('ETHUSD', lookback=20, imb_thresh=0.03, tp_usd=3.5, sl_usd=1.0, risk_rr=3.5, trade_size=1.0)
    if eth_strat:
        db['dom_absorption_eth'] = eth_strat
        print(f"ETH Strategy: {eth_strat['summary']}")

    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(db, f, indent=2, ensure_ascii=False)
    print("Updated docs/data/backtest_data.json successfully!")

if __name__ == '__main__':
    update_web_database()
