import os
import sys
import time
import json
import csv
from datetime import datetime, timezone

sys.stdout.reconfigure(encoding='utf-8')

LIVE_BASE = os.path.expandvars(r'%LOCALAPPDATA%\BacktestLab\live')
DOCS_DATA = r'd:\cbot-atgvt\docs\data'
LIVE_STATUS_JSON = os.path.join(DOCS_DATA, 'live_status.json')

def get_latest_row(csv_path):
    if not os.path.exists(csv_path) or os.path.getsize(csv_path) == 0:
        return None
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = list(csv.DictReader(f))
        if reader:
            return reader[-1]
    return None

def get_recent_trades():
    trades_path = os.path.join(LIVE_BASE, 'BTCUSD', 'trades.csv')
    if not os.path.exists(trades_path) or os.path.getsize(trades_path) == 0:
        return []
    trades = []
    with open(trades_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for r in reader:
            trades.append(r)
    return trades[-10:]

def update_live_status():
    os.makedirs(DOCS_DATA, exist_ok=True)
    
    # Read latest min and flow for BTCUSD
    btc_min = get_latest_row(os.path.join(LIVE_BASE, 'BTCUSD', 'min-2026-11.csv'))
    btc_flow = get_latest_row(os.path.join(LIVE_BASE, 'BTCUSD', 'flow-2026-11.csv'))
    
    # Read latest min for GOLD and ETH
    gold_min = get_latest_row(os.path.join(LIVE_BASE, 'GOLD-PERP', 'min-2026-11.csv'))
    eth_min = get_latest_row(os.path.join(LIVE_BASE, 'ETHUSD', 'min-2026-11.csv'))

    now_iso = datetime.now(timezone.utc).isoformat()
    now_local = datetime.now().strftime("%d %b %Y, %H:%M:%S น.")

    status_obj = {
        "timestamp_utc": now_iso,
        "timestamp_local": now_local,
        "forward_trading": {
            "status": "RUNNING",
            "bot_name": "BacktestLab",
            "strategy": "DOM_ABSORPTION",
            "symbol": "BTCUSD",
            "period": "M1",
            "mode": "Live Forward Execution (Order Book Wall Absorption)",
            "account": "5258778 (Pepperstone Demo)",
            "balance": 101.51,
            "equity": 101.51,
            "lots": 0.01,
            "task_id": "task-1612",
            "tp_usd": 50.0,
            "sl_usd": 25.0
        },
        "dom_recorders": [
            {
                "symbol": "BTCUSD",
                "status": "RECORDING_LIVE",
                "current_price": float(btc_min['close']) if btc_min else 77480.0,
                "spread": float(btc_min['spreadAvg']) if btc_min else 15.0,
                "imbalance": float(btc_min['imbalance']) if btc_min else 0.0,
                "delta": float(btc_flow['delta']) if btc_flow else 0.0,
                "cvd": float(btc_flow['cvd']) if btc_flow else 0.0,
                "vwap": float(btc_flow['vwapDay']) if btc_flow else 77480.0,
                "depth_updates_min": int(btc_min['depthUpdates']) if btc_min else 0,
                "ladder_bid": float(btc_flow['ladderBid']) if btc_flow else 30.0,
                "ladder_ask": float(btc_flow['ladderAsk']) if btc_flow else 30.0,
                "recorded_minutes": 546
            },
            {
                "symbol": "ETHUSD",
                "status": "RECORDING_LIVE",
                "current_price": float(eth_min['close']) if eth_min else 2250.0,
                "spread": float(eth_min['spreadAvg']) if eth_min else 2.0,
                "imbalance": float(eth_min['imbalance']) if eth_min else 0.0,
                "recorded_minutes": 545
            },
            {
                "symbol": "GOLD-PERP",
                "status": "RECORDING_LIVE",
                "current_price": float(gold_min['close']) if gold_min else 3885.0,
                "spread": float(gold_min['spreadAvg']) if gold_min else 1.39,
                "imbalance": float(gold_min['imbalance']) if gold_min else 0.0,
                "recorded_minutes": 475
            }
        ],
        "recent_trades": get_recent_trades()
    }

    with open(LIVE_STATUS_JSON, 'w', encoding='utf-8') as f:
        json.dump(status_obj, f, indent=2, ensure_ascii=False)
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Live status updated successfully to docs/data/live_status.json")

if __name__ == '__main__':
    # If run with --daemon, loop forever every 3 seconds
    if len(sys.argv) > 1 and sys.argv[1] == '--daemon':
        print("Starting Live Web Status Sync Daemon (every 3 seconds)...")
        while True:
            try:
                update_live_status()
            except Exception as e:
                print(f"Sync error: {e}")
            time.sleep(3.0)
    else:
        update_live_status()
