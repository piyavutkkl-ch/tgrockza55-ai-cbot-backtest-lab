import os
import sys
import time
import json
import csv
import glob
import subprocess
from datetime import datetime, timezone

sys.stdout.reconfigure(encoding='utf-8')

LIVE_BASE = os.path.expandvars(r'%LOCALAPPDATA%\BacktestLab\live')
REPO_ROOT = r'd:\cbot-atgvt'
DOCS_DATA = os.path.join(REPO_ROOT, 'docs', 'data')
LIVE_STATUS_JSON = os.path.join(DOCS_DATA, 'live_status.json')

BOT_CONFIGS = [
    {
        "id": "bot_btc_dom",
        "symbol": "BTCUSD",
        "name": "BTCUSD · DOM Absorption",
        "type": "FORWARD_TRADING",
        "strategy": "DOM_ABSORPTION",
        "lots": 0.01,
        "sl_usd": 35.0,
        "tp_usd": 91.0,
        "rr_ratio": 2.6,
        "defense": "Quantum Stealth RAM SL (±5% Jitter)",
        "role_desc": "เทรดสดดักจังหวะกำแพงสภาพคล่อง (Ask/Bid Wall Absorption)",
        "icon": "🪙"
    },
    {
        "id": "bot_eth_dom",
        "symbol": "ETHUSD",
        "name": "ETHUSD · DOM Absorption",
        "type": "FORWARD_TRADING",
        "strategy": "DOM_ABSORPTION",
        "lots": 0.01,
        "sl_usd": 4.5,
        "tp_usd": 11.7,
        "rr_ratio": 2.6,
        "defense": "Quantum Stealth RAM SL (±5% Jitter)",
        "role_desc": "เทรดสดดักจังหวะกำแพงสภาพคล่อง (Ask/Bid Wall Absorption)",
        "icon": "🔷"
    },
    {
        "id": "bot_xau_dom",
        "symbol": "XAUUSD",
        "name": "XAUUSD · DOM Absorption",
        "type": "FORWARD_TRADING",
        "strategy": "DOM_ABSORPTION",
        "lots": 0.01,
        "sl_usd": 2.5,
        "tp_usd": 6.0,
        "rr_ratio": 2.4,
        "defense": "Quantum Stealth RAM SL (±5% Jitter)",
        "role_desc": "เทรดสดดักจังหวะทองคำรอบลอนดอน & นิวยอร์ก (รอวอลุ่มช่วงบ่าย)",
        "icon": "🟡"
    },
    {
        "id": "bot_gold_perp_recorder",
        "symbol": "GOLD-PERP",
        "name": "GOLD-PERP · DOM L2 Recorder",
        "type": "DOM_RECORDER",
        "strategy": "ORDER_BOOK_RECORDER",
        "lots": 0.00,
        "sl_usd": 0.0,
        "tp_usd": 0.0,
        "rr_ratio": 0.0,
        "defense": "Passive 24h Depth Capture",
        "role_desc": "บันทึกข้อมูลสมุดคำสั่ง Level 2 Depth ทุก 2 วินาที ตลอด 24 ชม.",
        "icon": "📊"
    },
    {
        "id": "bot_legacy_smc_fibo",
        "symbol": "XAUUSD",
        "name": "SMC Fibo 5M (Legacy Model)",
        "type": "BACKTEST_ONLY",
        "strategy": "SMC_FIBO_5M",
        "lots": 0.01,
        "sl_usd": 2.0,
        "tp_usd": 6.0,
        "rr_ratio": 3.0,
        "defense": "Standard Hard SL",
        "role_desc": "กลยุทธ์โครงสร้างราคา SMC (หยุดรันชั่วคราว - รอเปรียบเทียบ)",
        "icon": "⏸️",
        "force_offline": True,
        "offline_reason": "สลับให้ DOM Absorption รันหลัก"
    }
]

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
                r['symbol'] = symbol
                trades.append(r)
    except Exception:
        pass
    return trades

def inspect_bot_telemetry(cfg, now_epoch):
    sym = cfg["symbol"]
    sdir = os.path.join(LIVE_BASE, sym)
    
    # Calculate PnL stats for this symbol
    sym_trades = get_trades(sym)
    sym_closes = [t for t in sym_trades if t.get('event') == 'CLOSE']
    net_pnl = round(sum(float(t.get('net', 0) or 0) for t in sym_closes), 2)
    wins = len([t for t in sym_closes if float(t.get('net', 0) or 0) > 0])
    losses = len([t for t in sym_closes if float(t.get('net', 0) or 0) < 0])
    win_rate = round(wins / len(sym_closes) * 100, 1) if sym_closes else 0.0

    pnl_info = {
        "closed_trades": len(sym_closes),
        "net_pnl": net_pnl,
        "wins": wins,
        "losses": losses,
        "win_rate": win_rate
    }

    if cfg.get("force_offline"):
        return {
            **cfg,
            **pnl_info,
            "is_online": False,
            "status": "OFFLINE",
            "heartbeat_seconds": 99999,
            "heartbeat_desc": "ออฟไลน์ (หยุดการทำงาน)",
            "current_price": 0.0,
            "spread": 0.0,
            "imbalance": 0.0,
            "delta": 0.0,
            "cvd": 0.0,
            "vwap": 0.0,
            "recorded_minutes": 0,
            "open_positions": 0
        }

    if not os.path.exists(sdir):
        return {
            **cfg,
            **pnl_info,
            "is_online": False,
            "status": "OFFLINE",
            "heartbeat_seconds": 99999,
            "heartbeat_desc": "ไม่มีไดเรกทอรีข้อมูล",
            "current_price": 0.0,
            "spread": 0.0,
            "imbalance": 0.0,
            "delta": 0.0,
            "cvd": 0.0,
            "vwap": 0.0,
            "recorded_minutes": 0,
            "open_positions": 0
        }

    min_file = os.path.join(sdir, 'min-2026-11.csv')
    flow_file = os.path.join(sdir, 'flow-2026-11.csv')
    books = glob.glob(os.path.join(sdir, 'book-*.csv'))
    latest_book = max(books, key=os.path.getmtime) if books else None

    mtimes = []
    if os.path.exists(min_file): mtimes.append(os.path.getmtime(min_file))
    if os.path.exists(flow_file): mtimes.append(os.path.getmtime(flow_file))
    if latest_book and os.path.exists(latest_book): mtimes.append(os.path.getmtime(latest_book))

    if not mtimes:
        diff_sec = 99999
    else:
        diff_sec = max(0.0, now_epoch - max(mtimes))

    is_online = (diff_sec <= 60.0)
    status = "LIVE" if is_online else "OFFLINE"

    if diff_sec < 2.0:
        heartbeat_desc = "เมื่อสักครู่ (< 2 วิ)"
    elif diff_sec < 60.0:
        heartbeat_desc = f"{int(diff_sec)} วินาทีที่แล้ว"
    elif diff_sec < 3600.0:
        heartbeat_desc = f"{int(diff_sec / 60)} นาทีที่แล้ว"
    else:
        heartbeat_desc = f"{int(diff_sec / 3600)} ชม. ที่แล้ว"

    min_row = get_latest_row(min_file)
    flow_row = get_latest_row(flow_file)

    curr_price = float(min_row['close']) if min_row and 'close' in min_row else 0.0
    spread = float(min_row['spreadAvg']) if min_row and 'spreadAvg' in min_row else 0.0
    imbalance = float(min_row['imbalance']) if min_row and 'imbalance' in min_row else 0.0
    delta = float(flow_row['delta']) if flow_row and 'delta' in flow_row else 0.0
    cvd = float(flow_row['cvd']) if flow_row and 'cvd' in flow_row else 0.0
    vwap = float(flow_row['vwapDay']) if flow_row and 'vwapDay' in flow_row else curr_price

    return {
        **cfg,
        **pnl_info,
        "is_online": is_online,
        "status": status,
        "heartbeat_seconds": round(diff_sec, 1),
        "heartbeat_desc": heartbeat_desc,
        "current_price": curr_price,
        "spread": spread,
        "imbalance": imbalance,
        "delta": delta,
        "cvd": cvd,
        "vwap": vwap,
        "recorded_minutes": count_minutes(sym),
        "open_positions": 0
    }

def update_live_status():
    os.makedirs(DOCS_DATA, exist_ok=True)
    now_epoch = time.time()

    bots_telemetry = [inspect_bot_telemetry(cfg, now_epoch) for cfg in BOT_CONFIGS]

    btc_trades = get_trades("BTCUSD")
    eth_trades = get_trades("ETHUSD")
    xau_trades = get_trades("XAUUSD")
    all_trades = btc_trades + eth_trades + xau_trades
    all_trades.sort(key=lambda x: x.get('time', ''))

    all_closed = [t for t in all_trades if t.get('event') == 'CLOSE']
    all_opens = {t.get('id'): t for t in all_trades if t.get('event') == 'OPEN'}

    current_balance = 97.48
    if all_closed:
        for t in reversed(all_closed):
            if t.get('balance'):
                try:
                    current_balance = float(t['balance'])
                    break
                except ValueError:
                    pass

    total_net_pnl = round(current_balance - 100.0, 2)
    total_net_pct = round((current_balance - 100.0) / 100.0 * 100, 2)
    total_wins = len([t for t in all_closed if float(t.get('net', 0) or 0) > 0])
    total_losses = len([t for t in all_closed if float(t.get('net', 0) or 0) < 0])
    total_gross_win = round(sum(float(t.get('net', 0) or 0) for t in all_closed if float(t.get('net', 0) or 0) > 0), 2)
    total_gross_loss = round(sum(float(t.get('net', 0) or 0) for t in all_closed if float(t.get('net', 0) or 0) < 0), 2)
    win_rate = round(total_wins / len(all_closed) * 100, 1) if all_closed else 0.0

    # Build paired recent deals for the table
    recent_deals = []
    for c in reversed(all_closed[-10:]):
        op = all_opens.get(c.get('id'), {})
        entry_p = float(op.get('price', 0) or 0) if op.get('price') else float(c.get('price', 0) or 0)
        exit_p = float(c.get('price', 0) or 0)
        net_val = float(c.get('net', 0) or 0)
        recent_deals.append({
            "id": c.get('id'),
            "symbol": c.get('symbol', 'BTCUSD'),
            "side": c.get('side', 'Sell'),
            "close_time": c.get('time', ''),
            "entry_price": entry_p,
            "exit_price": exit_p,
            "net": net_val,
            "reason": c.get('reason', 'Closed'),
            "spread": float(c.get('spread', 0) or 0),
            "slippage": float(c.get('slippage', 0) or 0),
            "balance": float(c.get('balance', 0) or current_balance)
        })

    now_iso = datetime.now(timezone.utc).isoformat()
    now_local = datetime.now().strftime("%d %b %Y, %H:%M:%S น.")

    online_bots_count = sum(1 for b in bots_telemetry if b["is_online"])
    total_forward_bots = sum(1 for b in bots_telemetry if b["type"] == "FORWARD_TRADING")
    online_forward_bots = sum(1 for b in bots_telemetry if b["type"] == "FORWARD_TRADING" and b["is_online"])

    status_obj = {
        "timestamp_utc": now_iso,
        "timestamp_local": now_local,
        "epoch": now_epoch,
        "summary": {
            "total_bots": len(bots_telemetry),
            "online_bots": online_bots_count,
            "offline_bots": len(bots_telemetry) - online_bots_count,
            "forward_online": online_forward_bots,
            "forward_total": total_forward_bots,
            "fleet_status": "ALL_ONLINE" if online_forward_bots == total_forward_bots else "PARTIAL_ONLINE"
        },
        "forward_trading": {
            "status": "RUNNING" if online_forward_bots > 0 else "OFFLINE",
            "bot_name": "BacktestLab (DOM_ABSORPTION)",
            "symbols": "BTCUSD + ETHUSD + XAUUSD",
            "account": "5258778 (Pepperstone Demo)",
            "initial_deposit": 100.00,
            "balance": round(current_balance, 2),
            "equity": round(current_balance, 2),
            "net_pnl": total_net_pnl,
            "net_pnl_pct": total_net_pct,
            "gross_win": total_gross_win,
            "gross_loss": total_gross_loss,
            "total_trades": len(all_closed),
            "wins": total_wins,
            "losses": total_losses,
            "win_rate": win_rate,
            "open_positions": 0
        },
        "bots_fleet": bots_telemetry,
        "recent_trades": all_trades[-10:],
        "recent_closed_deals": recent_deals
    }

    # Write atomic JSON
    tmp_path = LIVE_STATUS_JSON + '.tmp'
    with open(tmp_path, 'w', encoding='utf-8') as f:
        json.dump(status_obj, f, indent=2, ensure_ascii=False)
    os.replace(tmp_path, LIVE_STATUS_JSON)

last_git_push = 0

def maybe_git_push():
    global last_git_push
    now = time.time()
    if now - last_git_push < 45:
        return
    try:
        res = subprocess.run(['git', 'status', '--porcelain', 'docs/data/live_status.json'], cwd=REPO_ROOT, capture_output=True, text=True)
        if res.stdout.strip():
            subprocess.run(['git', 'add', 'docs/data/live_status.json'], cwd=REPO_ROOT, check=True)
            subprocess.run(['git', 'commit', '-m', f"chore(live): auto-sync bot fleet status ({datetime.now().strftime('%H:%M:%S')})"], cwd=REPO_ROOT, check=True)
            subprocess.run(['git', 'push', 'origin', 'main'], cwd=REPO_ROOT, check=True)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Pushed live fleet status to GitHub Pages successfully!")
            last_git_push = now
    except Exception as e:
        print(f"Git push skipped/error: {e}")

if __name__ == '__main__':
    if '--daemon' in sys.argv:
        print("Starting Enhanced Live Status Sync Daemon with PnL Telemetry...")
        while True:
            try:
                update_live_status()
                maybe_git_push()
            except Exception as e:
                print(f"Error in sync daemon: {e}")
            time.sleep(3)
    else:
        update_live_status()
        print(f"Updated {LIVE_STATUS_JSON} successfully!")
