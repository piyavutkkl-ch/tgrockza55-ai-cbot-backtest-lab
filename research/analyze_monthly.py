import json
import os

path = os.path.expanduser(r"~\OneDrive\เอกสาร\BacktestLab\local\CH_SMC_FIBO-XAUUSD-Minute15.json")
if not os.path.exists(path):
    print("Not found")
    exit(0)

with open(path, 'r', encoding='utf-8') as f:
    data = json.load(f)

trades = data.get("trades", [])

months = {}
for t in trades:
    m = t['entryTime'][:7]
    months.setdefault(m, []).append(t)

print("=== Monthly Breakdown (CH_SMC_FIBO M15) ===")
for m in sorted(months.keys()):
    m_trades = months[m]
    wins = [x for x in m_trades if x.get('net', 0) > 0]
    losses = [x for x in m_trades if x.get('net', 0) < 0]
    p = sum(x.get('net', 0) for x in m_trades)
    gw = sum(x.get('net', 0) for x in wins)
    gl = abs(sum(x.get('net', 0) for x in losses)) if losses else 0.001
    pf = gw / gl if gl > 0 else 0
    print(f"Month {m}: {len(m_trades):2d} trades, {len(wins):2d} wins ({len(wins)/len(m_trades)*100:4.1f}%), Net = {p:+7.2f} USD, PF = {pf:.2f}")
