"""
Multi-Market AI Quantitative Analysis Engine (Backtest Lab)
Calculates Cross-Asset Correlation, Lead-Lag Relationships, and Spread Friction
from d:\\cbot-atgvt\\data\\live_multi_market_feed.csv
"""

import os
import sys
import math
import json
from collections import defaultdict

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

CSV_FILE = r"d:\cbot-atgvt\data\live_multi_market_feed.csv"

def load_data():
    if not os.path.exists(CSV_FILE):
        print(f"Error: {CSV_FILE} not found.", file=sys.stderr)
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

def pivot_series(records):
    by_time = defaultdict(dict)
    symbols = set()
    for r in records:
        by_time[r["time"]][r["symbol"]] = r["mid"]
        symbols.add(r["symbol"])

    sorted_times = sorted(by_time.keys())
    series = {s: [] for s in symbols}
    valid_times = []

    for t in sorted_times:
        row = by_time[t]
        if all(s in row for s in symbols):
            valid_times.append(t)
            for s in symbols:
                series[s].append(row[s])

    return list(symbols), valid_times, series

def calc_returns(prices):
    ret = []
    for i in range(1, len(prices)):
        prev = prices[i - 1]
        curr = prices[i]
        r = (curr - prev) / prev if prev != 0 else 0.0
        ret.append(r)
    return ret

def pearson_corr(x, y):
    n = len(x)
    if n < 2:
        return 0.0
    mean_x = sum(x) / n
    mean_y = sum(y) / n
    var_x = sum((xi - mean_x) ** 2 for xi in x)
    var_y = sum((yi - mean_y) ** 2 for yi in y)
    if var_x == 0 or var_y == 0:
        return 0.0
    cov = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
    return cov / math.sqrt(var_x * var_y)

def analyze():
    records = load_data()
    if not records:
        print("No data available yet.")
        return

    symbols, times, series = pivot_series(records)
    print(f"\n=======================================================")
    print(f"[REPORT] Multi-Market AI Quantitative Analysis Report")
    print(f"=======================================================")
    print(f"Total Snapshots Recorded: {len(times)} timestamps ({len(records)} rows)")
    print(f"Tracked Symbols: {', '.join(symbols)}\n")

    if len(times) < 5:
        print(f"Waiting for more data (current valid points: {len(times)}). Need at least 5 for correlation.")
        return

    # Calculate return series
    returns = {s: calc_returns(series[s]) for s in symbols}

    # 1. Price summary
    print(f"--- 1. Latest Market Prices & Spreads ---")
    for s in sorted(symbols):
        latest = series[s][-1]
        last_rec = next(r for r in reversed(records) if r["symbol"] == s)
        spread_usd = last_rec["spread"]
        spread_pct = (spread_usd / latest) * 100 if latest > 0 else 0
        print(f"- {s:<10}: Price = ${latest:>10.2f} | Spread = {spread_usd:>6.2f} ({spread_pct:.4f}%)")

    # 2. Correlation Matrix
    print(f"\n--- 2. Instantaneous Returns Correlation Matrix ---")
    header_str = f"{'Symbol':<12}" + "".join(f"{s:>12}" for s in sorted(symbols))
    print(header_str)
    print("-" * len(header_str))
    
    corr_matrix = {}
    for s1 in sorted(symbols):
        row_str = f"{s1:<12}"
        corr_matrix[s1] = {}
        for s2 in sorted(symbols):
            if s1 == s2:
                c = 1.0
            else:
                c = pearson_corr(returns[s1], returns[s2])
            corr_matrix[s1][s2] = round(c, 4)
            row_str += f"{c:>12.3f}"
        print(row_str)

    # 3. Lead-Lag Cross-Correlation Analysis
    if "BTCUSD" in returns:
        print(f"\n--- 3. Lead-Lag Cross Correlation (Base: BTCUSD) ---")
        for target in ["ETHUSD", "SOLUSD", "GOLD-PERP"]:
            if target in returns and target != "BTCUSD":
                b = returns["BTCUSD"]
                y = returns[target]
                if len(b) > 4:
                    corr_lead = pearson_corr(b[:-1], y[1:])
                    corr_sync = pearson_corr(b, y)
                    corr_lag  = pearson_corr(b[1:], y[:-1])
                    
                    bias = "BTC LEADS" if corr_lead > corr_lag and corr_lead > 0.05 else ("SYNC" if abs(corr_sync) >= max(abs(corr_lead), abs(corr_lag)) else "TARGET LEADS")
                    print(f"- BTCUSD vs {target:<10}: Lag -1 (BTC Leads)={corr_lead:+.3f} | Sync={corr_sync:+.3f} | Lag +1={corr_lag:+.3f} -> [{bias}]")

    # 4. Actionable Real Trading Takeaways
    print(f"\n--- 4. Actionable Quant Insights for Real Trading ---")
    print(f"1. สภาพคล่องและต้นทุนสเปรดจริง (Execution Friction):")
    for s in sorted(symbols):
        last_rec = next(r for r in reversed(records) if r["symbol"] == s)
        latest = series[s][-1]
        friction = (last_rec["spread"] / latest) * 100
        if friction < 0.05:
            status = "ดีเยี่ยม (ต้นทุนต่ำมาก เหมาะแก่การเทรดสั้น Scalping / M1-M5)"
        elif friction < 0.2:
            status = "ปานกลาง (ควรถือครองอย่างน้อย 3-5 นาทีขึ้นไป)"
        else:
            status = "สเปรดกว้าง (ควรเทรดกรอบใหญ่ M15+)"
        print(f"   * {s}: สเปรด {friction:.4f}% -> {status}")

    print(f"\n=======================================================\n")

if __name__ == "__main__":
    analyze()
