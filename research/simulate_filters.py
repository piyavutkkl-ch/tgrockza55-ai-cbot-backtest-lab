import json
import glob
import os

docs = os.path.expanduser(r"~\OneDrive\เอกสาร\BacktestLab\local")
files = sorted(glob.glob(os.path.join(docs, "CH_SMC_FIBO*.json")), key=os.path.getmtime, reverse=True)
target = files[0]
with open(target, 'r', encoding='utf-8') as f:
    data = json.load(f)

trades = data.get("trades", [])
print(f"Loaded {len(trades)} trades from {os.path.basename(target)}")

# Let's inspect win/loss by Side (Buy vs Sell)
buys = [t for t in trades if t.get("side") == "Buy"]
sells = [t for t in trades if t.get("side") == "Sell"]

buy_win = [t for t in buys if t.get("net", 0) > 0]
buy_loss = [t for t in buys if t.get("net", 0) < 0]
buy_profit = sum(t.get("net", 0) for t in buys)

sell_win = [t for t in sells if t.get("net", 0) > 0]
sell_loss = [t for t in sells if t.get("net", 0) < 0]
sell_profit = sum(t.get("net", 0) for t in sells)

print(f"\n--- BUYS ---")
print(f"Total: {len(buys)}, Won: {len(buy_win)}, Lost: {len(buy_loss)}, Net Profit: {buy_profit:.2f} USD")

print(f"\n--- SELLS ---")
print(f"Total: {len(sells)}, Won: {len(sell_win)}, Lost: {len(sell_loss)}, Net Profit: {sell_profit:.2f} USD")

# Inspect by Hour of entry
hours = {}
for t in trades:
    h = int(t['entryTime'][11:13])
    hours.setdefault(h, []).append(t.get('net', 0))

print("\n--- By Hour (UTC) ---")
for h in sorted(hours.keys()):
    t_list = hours[h]
    net_h = sum(t_list)
    win_h = len([x for x in t_list if x > 0])
    print(f"Hour {h:02d}:00: {len(t_list):2d} trades, {win_h:2d} wins, Net = {net_h:7.2f} USD")
