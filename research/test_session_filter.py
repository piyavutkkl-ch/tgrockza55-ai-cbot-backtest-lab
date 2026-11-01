import json
import os

docs = os.path.expanduser(r"~\OneDrive\เอกสาร\BacktestLab\local\CH_SMC_FIBO-XAUUSD-Minute15.json")
with open(docs, 'r', encoding='utf-8') as f:
    data = json.load(f)

trades = data.get("trades", [])

# Filter 1: London session only (07:00 to 11:59 UTC)
london_trades = [t for t in trades if 7 <= int(t['entryTime'][11:13]) <= 11]
l_win = [t for t in london_trades if t.get('net', 0) > 0]
l_profit = sum(t.get('net', 0) for t in london_trades)
print(f"=== London Session (07:00 - 11:59 UTC) ===")
print(f"Total: {len(london_trades)}, Wins: {len(l_win)}, Win Rate: {len(l_win)/len(london_trades)*100:.1f}%")
print(f"Net Profit: +{l_profit:.2f} USD")
gross_win = sum(t.get('net', 0) for t in l_win)
gross_loss = abs(sum(t.get('net', 0) for t in london_trades if t.get('net', 0) < 0))
print(f"Profit Factor: {gross_win / gross_loss:.2f}")

# Filter 2: All sessions EXCEPT US News hour (12:00 - 13:59 UTC)
no_news_trades = [t for t in trades if int(t['entryTime'][11:13]) not in [12, 13]]
nn_win = [t for t in no_news_trades if t.get('net', 0) > 0]
nn_profit = sum(t.get('net', 0) for t in no_news_trades)
print(f"\n=== Exclude News Spike Hours (12:00 - 13:59 UTC) ===")
print(f"Total: {len(no_news_trades)}, Wins: {len(nn_win)}, Win Rate: {len(nn_win)/len(no_news_trades)*100:.1f}%")
print(f"Net Profit: +{nn_profit:.2f} USD")
nn_gross_win = sum(t.get('net', 0) for t in nn_win)
nn_gross_loss = abs(sum(t.get('net', 0) for t in no_news_trades if t.get('net', 0) < 0))
print(f"Profit Factor: {nn_gross_win / nn_gross_loss:.2f}")
