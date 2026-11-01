import json
import glob
import os

docs = os.path.expanduser(r"~\OneDrive\เอกสาร\BacktestLab\local")
files = sorted(glob.glob(os.path.join(docs, "*Minute30*.json")), key=os.path.getmtime, reverse=True)
if not files:
    files = sorted(glob.glob(os.path.join(docs, "*m30*.json")), key=os.path.getmtime, reverse=True)

target = files[0]
print(f"Reading: {os.path.basename(target)}")
with open(target, 'r', encoding='utf-8') as f:
    data = json.load(f)

trades = data.get("trades", [])
print(f"Total trades: {len(trades)}")

months = {}
for t in trades:
    m = t['entryTime'][:7]
    months.setdefault(m, []).append(t)

print("=== Monthly Breakdown (CH_SMC_FIBO M30) ===")
for m in sorted(months.keys()):
    m_trades = months[m]
    wins = [x for x in m_trades if x.get('net', 0) > 0]
    losses = [x for x in m_trades if x.get('net', 0) < 0]
    p = sum(x.get('net', 0) for x in m_trades)
    gw = sum(x.get('net', 0) for x in wins)
    gl = abs(sum(x.get('net', 0) for x in losses)) if losses else 0.001
    pf = gw / gl if gl > 0 else 0
    print(f"Month {m}: {len(m_trades):2d} trades, {len(wins):2d} wins ({len(wins)/len(m_trades)*100:4.1f}%), Net = {p:+7.2f} USD, PF = {pf:.2f}")

print("\nTrade details (first 10):")
for t in trades[:10]:
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
