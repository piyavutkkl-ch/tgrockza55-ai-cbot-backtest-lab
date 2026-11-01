import json
import glob
import os

docs = os.path.expanduser(r"~\OneDrive\เอกสาร\BacktestLab\local")
files = sorted(glob.glob(os.path.join(docs, "CH_SMC_FIBO*.json")), key=os.path.getmtime, reverse=True)
if not files:
    print("No files found!")
    exit(0)

target = files[0]
print(f"Reading: {os.path.basename(target)}")
with open(target, 'r', encoding='utf-8') as f:
    data = json.load(f)

summary = data.get("summary", {})
print("=== Summary ===")
for k in ["net_profit", "profit_factor", "win_rate", "total_trades", "max_dd_pct", "average_trade"]:
    print(f"  {k}: {summary.get(k)}")

trades = data.get("trades", [])
print(f"\nTotal trades: {len(trades)}")
winners = [t for t in trades if t.get("net", 0) > 0]
losers = [t for t in trades if t.get("net", 0) < 0]
be_trades = [t for t in trades if abs(t.get("net", 0)) < 0.5]

print(f"Winners: {len(winners)}, Losers: {len(losers)}, Breakeven/Scratch: {len(be_trades)}")

if winners:
    avg_win = sum(t.get("net", 0) for t in winners) / len(winners)
    print(f"Avg Win: {avg_win:.2f} USD")
if losers:
    avg_loss = sum(t.get("net", 0) for t in losers) / len(losers)
    print(f"Avg Loss: {avg_loss:.2f} USD")

print("\nAll trades:")
for t in trades:
    side = t.get("side")
    net = t.get("net", 0)
    entry_p = t.get("entryPrice")
    exit_p = t.get("exitPrice")
    sl = t.get("sl")
    tp = t.get("tp")
    pips = t.get("pips")
    entry_t = t.get("entryTime")
    exit_t = t.get("exitTime")
    print(f"  [{entry_t} -> {exit_t}] {side:4s} Entry={entry_p:8.2f}, Exit={exit_p:8.2f}, SL={sl}, TP={tp}, Pips={pips:6.1f}, Net={net:6.2f}")
