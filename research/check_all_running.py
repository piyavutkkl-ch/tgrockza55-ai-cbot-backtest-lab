import json
import os

ls_path = r'd:\cbot-atgvt\docs\data\live_status.json'
with open(ls_path, 'r', encoding='utf-8') as f:
    ls = json.load(f)

print("=== LIVE SYSTEM STATUS ===")
print("Timestamp:", ls.get("timestamp_local"))
print("Summary:", ls.get("summary"))
print("Forward Trading:", ls.get("forward_trading"))

print("\n--- BOTS FLEET ---")
for b in ls.get("bots_fleet", []):
    sym = b.get("symbol")
    st = b.get("status")
    pr = b.get("last_price")
    imb = b.get("last_imbalance")
    cvd = b.get("last_cvd")
    up = b.get("last_update_str")
    print(f"[{sym:<9}] Status: {st:<7} | Price: {pr} | Imbalance: {imb} | CVD: {cvd} | Updated: {up}")

print("\n--- RECENT DEALS ---")
deals = ls.get("recent_closed_deals", [])
print(f"Total Closed Deals: {len(deals)}")
for d in deals[-10:]:
    print(d)
