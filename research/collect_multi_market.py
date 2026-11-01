"""
Multi-Market Continuous Live Data Collector (Non-Stop Daemon)
Collects synchronized multi-symbol data (BTCUSD, GOLD-PERP, ETHUSD, SOLUSD)
continuously into d:\\cbot-atgvt\\data\\live_multi_market_feed.csv
"""

import os
import sys
import json
import time
import subprocess
from datetime import datetime, timezone

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

CTRADER_CLI = "ctrader-cli"
CTID = "piyavut.ch@gmail.com"
PWD_FILE = r"D:\C2\IDP\password.pwd"
ACCOUNT = "5258778"
SYMBOLS = "BTCUSD,GOLD-PERP,ETHUSD,SOLUSD"

DATA_DIR = r"d:\cbot-atgvt\data"
CSV_FILE = os.path.join(DATA_DIR, "live_multi_market_feed.csv")

def ensure_csv_header():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(CSV_FILE) or os.path.getsize(CSV_FILE) == 0:
        with open(CSV_FILE, "w", encoding="utf-8") as f:
            f.write("timestamp_utc,symbol,bid,ask,mid,spread,high_24h,low_24h,open_24h,change_pct_24h,range_pct_24h\n")

def fetch_multi_prices():
    cmd = [
        CTRADER_CLI,
        "prices",
        f"--symbols={SYMBOLS}",
        f"--ctid={CTID}",
        f"--pwd-file={PWD_FILE}",
        f"--account={ACCOUNT}",
        "-q"
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
        raw = proc.stdout
        json_start = raw.find("{")
        if json_start != -1:
            json_str = raw[json_start:]
            data = json.loads(json_str)
            return data.get("results", [])
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Transient price fetch warning: {e}", file=sys.stderr, flush=True)
    return []

def record_snapshot():
    ensure_csv_header()
    now_utc = datetime.now(timezone.utc).isoformat()
    results = fetch_multi_prices()
    if not results:
        return 0, []

    rows = []
    summary_items = []
    for r in results:
        if not r.get("ok"):
            continue
        q = r.get("quote", {})
        sym = q.get("symbolName", "")
        bid = q.get("bid", 0.0)
        ask = q.get("ask", 0.0)
        mid = round((bid + ask) / 2.0, 4) if (bid and ask) else 0.0
        spread = q.get("spread", 0.0)
        high = q.get("high", 0.0)
        low = q.get("low", 0.0)
        open_p = q.get("open", 0.0)
        chg_pct = round(((mid - open_p) / open_p) * 100.0, 4) if open_p > 0 else 0.0
        rng_pct = round(((high - low) / mid) * 100.0, 4) if mid > 0 else 0.0

        line = f"{now_utc},{sym},{bid},{ask},{mid},{spread},{high},{low},{open_p},{chg_pct},{rng_pct}\n"
        rows.append(line)
        summary_items.append(f"{sym}: {mid}")

    with open(CSV_FILE, "a", encoding="utf-8") as f:
        f.writelines(rows)
        f.flush()

    return len(rows), summary_items

def get_file_size_kb():
    if os.path.exists(CSV_FILE):
        return os.path.getsize(CSV_FILE) / 1024.0
    return 0.0

if __name__ == "__main__":
    count_arg = sys.argv[1] if len(sys.argv) > 1 else "0"
    continuous = count_arg in ["0", "-1", "continuous", "--continuous"]
    count = 0 if continuous else int(count_arg)
    interval = float(sys.argv[2]) if len(sys.argv) > 2 else 3.0

    print(f"=== Multi-Market Continuous Live Data Collector ===", flush=True)
    print(f"Target Symbols: {SYMBOLS}", flush=True)
    print(f"Mode: {'CONTINUOUS (Non-Stop Daemon)' if continuous else f'{count} snapshots'}", flush=True)
    print(f"Target File: {CSV_FILE}", flush=True)
    print(f"Current File Size: {get_file_size_kb():.2f} KB\n", flush=True)

    iteration = 0
    success_count = 0

    while True:
        iteration += 1
        t0 = time.time()
        try:
            n, items = record_snapshot()
            if n > 0:
                success_count += 1
                if iteration % 5 == 0 or iteration <= 3:
                    file_size = get_file_size_kb()
                    print(f"[{iteration}] {datetime.now().strftime('%H:%M:%S')} - Recorded {n} symbols | File: {file_size:.1f} KB | {' | '.join(items)}", flush=True)
            else:
                print(f"[{iteration}] {datetime.now().strftime('%H:%M:%S')} - Skipped (empty response)", flush=True)
        except Exception as ex:
            print(f"[{iteration}] {datetime.now().strftime('%H:%M:%S')} - Handled error: {ex}", file=sys.stderr, flush=True)
            time.sleep(3)

        if not continuous and iteration >= count:
            break

        elapsed = time.time() - t0
        rem_sleep = max(1.0, interval - elapsed)
        time.sleep(rem_sleep)

    print(f"\nCollector stopped. Total saved: {success_count} snapshots ({get_file_size_kb():.1f} KB).", flush=True)
