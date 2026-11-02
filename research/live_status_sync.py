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
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = list(csv.DictReader(f))
            if reader:
                return reader[-1]
    except Exception:
        pass
    return None

def count_minutes(symbol):
    csv_path = os.path.join(LIVE_BASE, symbol, 'min-2026-11.csv')
    if not os.path.exists(csv_path):
        return 0
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            return max(0, sum(1 for _ in f) - 1)
    except Exception:
        return 0

def get_trades(symbol):
    trades_path = os.path.join(LIVE_BASE, symbol, 'trades.csv')
    if not os.path.exists(trades_path) or os.path.getsize(trades_path) == 0:
        return []
    trades = []
    try:
        with open(trades_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for r in reader:
                trades.append(r)
    except Exception:
        pass
    return trades

def update_live_status():
    os.makedirs(DOCS_DATA, exist_ok=True)
    
    # Read latest min and flow for BTCUSD
    btc_min = get_latest_row(os.path.join(LIVE_BASE, 'BTCUSD', 'min-2026-11.csv'))
    btc_flow = get_latest_row(os.path.join(LIVE_BASE, 'BTCUSD', 'flow-2026-11.csv'))
    
    # Read latest min and flow for ETHUSD & GOLD-PERP & XAUUSD
    eth_min = get_latest_row(os.path.join(LIVE_BASE, 'ETHUSD', 'min-2026-11.csv'))
    eth_flow = get_latest_row(os.path.join(LIVE_BASE, 'ETHUSD', 'flow-2026-11.csv'))
    gold_min = get_latest_row(os.path.join(LIVE_BASE, 'GOLD-PERP', 'min-2026-11.csv'))
    xau_min = get_latest_row(os.path.join(LIVE_BASE, 'XAUUSD', 'min-2026-11.csv'))

    btc_trades = get_trades("BTCUSD")
    eth_trades = get_trades("ETHUSD")
    xau_trades = get_trades("XAUUSD")
    all_trades = btc_trades + eth_trades + xau_trades

    # Determine balance from latest close trade
    current_balance = 100.05
    if all_trades:
        for t in reversed(all_trades):
            if t.get('balance'):
                try:
                    current_balance = float(t['balance'])
                    break
                except ValueError:
                    pass

    now_iso = datetime.now(timezone.utc).isoformat()
    now_local = datetime.now().strftime("%d %b %Y, %H:%M:%S น.")

    status_obj = {
        "timestamp_utc": now_iso,
        "timestamp_local": now_local,
        "forward_trading": {
            "status": "RUNNING",
            "bot_name": "BacktestLab (DOM_ABSORPTION)",
            "symbols": "BTCUSD + ETHUSD + XAUUSD (3 บอทขนานกัน)",
            "period": "M1",
            "mode": "Live Forward Execution (Order Book Wall Absorption)",
            "account": "5258778 (Pepperstone Demo)",
            "balance": round(current_balance, 2),
            "equity": round(current_balance, 2),
            "total_trades": len([t for t in all_trades if t.get('event') == 'CLOSE']),
            "active_bots": [
                {
                    "symbol": "BTCUSD",
                    "status": "RUNNING",
                    "lots": 0.01,
                    "tp_usd": 91.0,
                    "sl_usd": 35.0,
                    "recorded_minutes": count_minutes("BTCUSD")
                },
                {
                    "symbol": "ETHUSD",
                    "status": "RUNNING",
                    "lots": 0.01,
                    "tp_usd": 11.7,
                    "sl_usd": 4.5,
                    "recorded_minutes": count_minutes("ETHUSD")
                },
                {
                    "symbol": "XAUUSD",
                    "status": "RUNNING",
                    "lots": 0.01,
                    "tp_usd": 6.0,
                    "sl_usd": 2.5,
                    "recorded_minutes": count_minutes("XAUUSD")
                }
            ]
        },
        "dom_recorders": [
            {
                "symbol": "BTCUSD",
                "status": "FORWARD_TRADING_LIVE",
                "current_price": float(btc_min['close']) if btc_min and 'close' in btc_min else 77950.0,
                "spread": float(btc_min['spreadAvg']) if btc_min and 'spreadAvg' in btc_min else 15.0,
                "imbalance": float(btc_min['imbalance']) if btc_min and 'imbalance' in btc_min else 0.0,
                "delta": float(btc_flow['delta']) if btc_flow and 'delta' in btc_flow else 0.0,
                "cvd": float(btc_flow['cvd']) if btc_flow and 'cvd' in btc_flow else 0.0,
                "vwap": float(btc_flow['vwapDay']) if btc_flow and 'vwapDay' in btc_flow else 77950.0,
                "recorded_minutes": count_minutes("BTCUSD")
            },
            {
                "symbol": "ETHUSD",
                "status": "FORWARD_TRADING_LIVE",
                "current_price": float(eth_min['close']) if eth_min and 'close' in eth_min else 2265.0,
                "spread": float(eth_min['spreadAvg']) if eth_min and 'spreadAvg' in eth_min else 2.0,
                "imbalance": float(eth_min['imbalance']) if eth_min and 'imbalance' in eth_min else 0.0,
                "delta": float(eth_flow['delta']) if eth_flow and 'delta' in eth_flow else 0.0,
                "cvd": float(eth_flow['cvd']) if eth_flow and 'cvd' in eth_flow else 0.0,
                "recorded_minutes": count_minutes("ETHUSD")
            },
            {
                "symbol": "GOLD-PERP",
                "status": "RECORDING_LIVE",
                "current_price": float(gold_min['close']) if gold_min and 'close' in gold_min else 3885.0,
                "spread": float(gold_min['spreadAvg']) if gold_min and 'spreadAvg' in gold_min else 1.4,
                "recorded_minutes": count_minutes("GOLD-PERP")
            },
            {
                "symbol": "XAUUSD",
                "status": "FORWARD_TRADING_LIVE",
                "current_price": float(xau_min['close']) if xau_min and 'close' in xau_min else 2740.0,
                "spread": float(xau_min['spreadAvg']) if xau_min and 'spreadAvg' in xau_min else 0.12,
                "recorded_minutes": count_minutes("XAUUSD")
            }
        ],
        "recent_trades": all_trades[-10:]
    }

    # Write atomic JSON
    tmp_path = LIVE_STATUS_JSON + '.tmp'
    with open(tmp_path, 'w', encoding='utf-8') as f:
        json.dump(status_obj, f, indent=2, ensure_ascii=False)
    os.replace(tmp_path, LIVE_STATUS_JSON)

if __name__ == '__main__':
    if '--daemon' in sys.argv:
        print("Starting Live Status Sync Daemon (updating every 3 seconds)...")
        while True:
            try:
                update_live_status()
            except Exception as e:
                print(f"Error in sync: {e}")
            time.sleep(3)
    else:
        update_live_status()
        print(f"Updated {LIVE_STATUS_JSON} successfully!")
