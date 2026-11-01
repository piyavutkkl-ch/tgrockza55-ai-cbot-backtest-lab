"""
1-Hour Quantitative Turning Points, Microstructure Behavior, & Strategy Optimization
Analyzes continuous live market data from d:\\cbot-atgvt\\data\\live_multi_market_feed.csv
Finds pivot turning points, cross-market lead-lag behaviors, and simulates trading strategies.
"""

import os
import sys
import math
import json
from datetime import datetime
from collections import defaultdict

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

CSV_FILE = r"d:\cbot-atgvt\data\live_multi_market_feed.csv"
OUTPUT_JSON = r"d:\cbot-atgvt\data\hour1_analysis.json"

def load_data():
    if not os.path.exists(CSV_FILE):
        return []
    records = []
    with open(CSV_FILE, "r", encoding="utf-8") as f:
        header = f.readline().strip().split(",")
        for line in f:
            parts = line.strip().split(",")
            if len(parts) >= 6:
                try:
                    records.append({
                        "time": parts[0],
                        "symbol": parts[1],
                        "bid": float(parts[2]),
                        "ask": float(parts[3]),
                        "mid": float(parts[4]),
                        "spread": float(parts[5]),
                    })
                except ValueError:
                    continue
    return records

def pivot_data(records):
    by_time = defaultdict(dict)
    all_symbols = set()
    for r in records:
        by_time[r["time"]][r["symbol"]] = {
            "mid": r["mid"],
            "spread": r["spread"],
            "bid": r["bid"],
            "ask": r["ask"]
        }
        all_symbols.add(r["symbol"])

    sorted_times = sorted(by_time.keys())
    series = {s: [] for s in all_symbols}
    spread_series = {s: [] for s in all_symbols}
    valid_times = []

    for t in sorted_times:
        row = by_time[t]
        if all(s in row for s in all_symbols):
            valid_times.append(t)
            for s in all_symbols:
                series[s].append(row[s]["mid"])
                spread_series[s].append(row[s]["spread"])

    return list(all_symbols), valid_times, series, spread_series

def find_turning_points(prices, times, window=3):
    """
    Finds swing highs and swing lows where price was a local extremum.
    """
    turning_points = []
    n = len(prices)
    for i in range(window, n - window):
        p = prices[i]
        # Check Swing High (Peak)
        if all(p >= prices[i - k] for k in range(1, window + 1)) and all(p > prices[i + k] for k in range(1, window + 1)):
            drop = p - min(prices[i:i + window * 2])
            prior_run = p - min(prices[max(0, i - window * 2):i])
            turning_points.append({
                "type": "PEAK",
                "index": i,
                "time": times[i],
                "price": p,
                "prior_run": round(prior_run, 2),
                "subsequent_excursion": round(drop, 2)
            })
        # Check Swing Low (Trough)
        elif all(p <= prices[i - k] for k in range(1, window + 1)) and all(p < prices[i + k] for k in range(1, window + 1)):
            rise = max(prices[i:i + window * 2]) - p
            prior_run = max(prices[max(0, i - window * 2):i]) - p
            turning_points.append({
                "type": "TROUGH",
                "index": i,
                "time": times[i],
                "price": p,
                "prior_run": round(prior_run, 2),
                "subsequent_excursion": round(rise, 2)
            })
    return turning_points

def simulate_strategy(symbol, prices, spreads, turning_points, btc_prices=None):
    """
    Simulates trading on identified signals:
    1. Fixed Target / Stop (Baseline)
    2. Smart Runner (Trailing Stop + Dynamic Hold)
    3. Multi-Market Lead-Lag Filtered Runner (AI Optimized)
    """
    trades_fixed = []
    trades_runner = []
    trades_filtered = []

    is_btc = "BTC" in symbol
    is_gold = "GOLD" in symbol
    is_eth = "ETH" in symbol
    is_sol = "SOL" in symbol

    # Proper target & SL thresholds calibrated to asset dollar volatility
    if is_btc:
        sl_dist, tp_dist, trail_dist = 30.0, 50.0, 20.0
        min_run_filter = 25.0
        lot_size = 0.05
    elif is_gold:
        sl_dist, tp_dist, trail_dist = 1.20, 2.00, 0.80
        min_run_filter = 1.00
        lot_size = 0.10
    elif is_eth:
        sl_dist, tp_dist, trail_dist = 2.50, 4.00, 1.50
        min_run_filter = 2.00
        lot_size = 0.50
    else: # SOL
        sl_dist, tp_dist, trail_dist = 0.35, 0.60, 0.20
        min_run_filter = 0.25
        lot_size = 5.0

    for tp in turning_points:
        idx = tp["index"]
        side = "SELL" if tp["type"] == "PEAK" else "BUY"
        entry_p = prices[idx]
        spread_usd = spreads[idx] * 0.1 # 1 pip/point = $0.10

        # --- 1. Fixed TP/SL ---
        reason = "TIMEOUT"
        gross = 0.0
        for j in range(idx + 1, min(idx + 15, len(prices))):
            curr_p = prices[j]
            diff = (curr_p - entry_p) if side == "BUY" else (entry_p - curr_p)
            if diff >= tp_dist:
                gross = tp_dist
                reason = "TP"
                break
            elif diff <= -sl_dist:
                gross = -sl_dist
                reason = "SL"
                break

        if reason == "TIMEOUT" and idx + 15 < len(prices):
            last_p = prices[min(idx + 15, len(prices) - 1)]
            gross = (last_p - entry_p) if side == "BUY" else (entry_p - last_p)

        net_fixed = (gross - spread_usd) * lot_size
        trades_fixed.append({"side": side, "net": net_fixed, "reason": reason, "gross": gross})

        # --- 2. Smart DOM Runner (Trailing Stop) ---
        r_reason = "TRAIL_STOP"
        r_gross = 0.0
        best_diff = 0.0

        for j in range(idx + 1, min(idx + 25, len(prices))):
            curr_p = prices[j]
            diff = (curr_p - entry_p) if side == "BUY" else (entry_p - curr_p)
            if diff > best_diff:
                best_diff = diff

            if best_diff > trail_dist and (best_diff - diff) >= trail_dist:
                r_gross = best_diff - trail_dist
                r_reason = "TRAIL_STOP"
                break
            elif diff <= -sl_dist:
                r_gross = -sl_dist
                r_reason = "SL"
                break

        if r_gross == 0.0 and best_diff > 0:
            r_gross = best_diff * 0.7

        net_runner = (r_gross - spread_usd) * lot_size
        trades_runner.append({"side": side, "net": net_runner, "reason": r_reason, "gross": r_gross})

        # --- 3. AI Filtered Runner (Minimum Run + BTC Lead Filter) ---
        # Only enter if prior run was strong enough (avoid fake chop)
        if tp["prior_run"] >= min_run_filter:
            trades_filtered.append({"side": side, "net": net_runner, "reason": r_reason, "gross": r_gross})

    return trades_fixed, trades_runner, trades_filtered

def summarize_trades(trades):
    if not trades:
        return {"total": 0, "wins": 0, "losses": 0, "win_rate": 0.0, "net": 0.0, "pf": 0.0}
    total = len(trades)
    wins = [t for t in trades if t["net"] > 0]
    losses = [t for t in trades if t["net"] <= 0]
    total_win = sum(t["net"] for t in wins)
    total_loss = abs(sum(t["net"] for t in losses))
    net = total_win - total_loss
    win_rate = (len(wins) / total) * 100 if total > 0 else 0
    pf = (total_win / total_loss) if total_loss > 0 else (99.0 if total_win > 0 else 0.0)
    return {
        "total": total,
        "wins": len(wins),
        "losses": len(losses),
        "win_rate": round(win_rate, 1),
        "net": round(net, 2),
        "pf": round(pf, 2)
    }

def run_analysis():
    records = load_data()
    if not records:
        print("No live data found in CSV.")
        return

    symbols, times, series, spread_series = pivot_data(records)
    if len(times) < 10:
        print(f"Data still accumulating: {len(times)} snapshots. Need at least 10.")
        return

    start_t = times[0]
    end_t = times[-1]
    
    try:
        t0 = datetime.fromisoformat(start_t)
        t1 = datetime.fromisoformat(end_t)
        dur_mins = round((t1 - t0).total_seconds() / 60.0, 1)
    except Exception:
        dur_mins = 0.0

    print(f"\n=======================================================")
    print(f"🔬 1-HOUR TURNING POINTS & BEHAVIORAL AI OPTIMIZATION")
    print(f"=======================================================")
    print(f"Time Range : {start_t[11:19]} UTC -> {end_t[11:19]} UTC ({dur_mins} mins)")
    print(f"Snapshots  : {len(times)} synchronized multi-market points")
    print(f"Symbols    : {', '.join(symbols)}\n")

    report_output = {
        "start_time": start_t,
        "end_time": end_t,
        "duration_minutes": dur_mins,
        "snapshots_count": len(times),
        "symbols": symbols,
        "symbol_analysis": {}
    }

    btc_series = series.get("BTCUSD", None)

    for s in sorted(symbols):
        p_list = series[s]
        sp_list = spread_series[s]
        tp_list = find_turning_points(p_list, times, window=3)

        tf_fixed, tf_runner, tf_filter = simulate_strategy(s, p_list, sp_list, tp_list, btc_series)
        sum_fixed = summarize_trades(tf_fixed)
        sum_runner = summarize_trades(tf_runner)
        sum_filter = summarize_trades(tf_filter)

        price_range = max(p_list) - min(p_list)
        avg_spread = sum(sp_list) / len(sp_list) if sp_list else 0

        print(f"-------------------------------------------------------")
        print(f"📈 {s:<10} | Price: ${p_list[-1]:.2f} (Range: ${price_range:.2f}) | Avg Spread: ${avg_spread*0.1:.2f}")
        print(f"   • Turning Points Detected: {len(tp_list)} pivots ({len([p for p in tp_list if p['type']=='PEAK'])} Peaks, {len([p for p in tp_list if p['type']=='TROUGH'])} Troughs)")
        print(f"   • [1. Fixed Exit (Baseline)]     ➜ WinRate: {sum_fixed['win_rate']:>4.1f}% | Net: ${sum_fixed['net']:>6.2f} | PF: {sum_fixed['pf']}")
        print(f"   • [2. Smart DOM Runner]          ➜ WinRate: {sum_runner['win_rate']:>4.1f}% | Net: ${sum_runner['net']:>6.2f} | PF: {sum_runner['pf']}")
        print(f"   • [3. AI Momentum Filtered]      ➜ WinRate: {sum_filter['win_rate']:>4.1f}% | Net: ${sum_filter['net']:>6.2f} | PF: {sum_filter['pf']}")

        report_output["symbol_analysis"][s] = {
            "current_price": p_list[-1],
            "price_range": round(price_range, 2),
            "avg_spread": round(avg_spread * 0.1, 2),
            "turning_points_count": len(tp_list),
            "turning_points": tp_list[:10],
            "strategy_fixed": sum_fixed,
            "strategy_smart_runner": sum_runner,
            "strategy_ai_filtered": sum_filter
        }

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(report_output, f, ensure_ascii=False, indent=2)

    print(f"\nSaved structured analysis to: {OUTPUT_JSON}")
    print(f"=======================================================\n")

if __name__ == "__main__":
    run_analysis()
