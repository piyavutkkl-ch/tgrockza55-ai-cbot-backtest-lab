import sys, os, csv

sys.stdout.reconfigure(encoding='utf-8')

base = r'C:\Users\Strong Baesus PC1\AppData\Local\BacktestLab\live\XAUUSD'
book_file = os.path.join(base, 'book-2026-11-02.csv')
tick_file = os.path.join(base, 'tick-2026-11-02.csv')

def inspect_book_at_time(target_prefix):
    print(f"\n=================== BOOK SNAPSHOTS AROUND {target_prefix} ===================")
    count = 0
    with open(book_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for r in reader:
            if r['time'].startswith(target_prefix):
                print(f"Time: {r['time']}")
                # Parse bids and asks
                bids = r['bids'].split('|')
                asks = r['asks'].split('|')
                top_bids = bids[:3]
                top_asks = asks[:3]
                print(f"  Bids (top 3): {' | '.join(top_bids)}")
                print(f"  Asks (top 3): {' | '.join(top_asks)}")
                count += 1
                if count >= 4:
                    break

def inspect_ticks_at_time(target_prefix):
    print(f"\n=================== TICKS AROUND {target_prefix} ===================")
    count = 0
    with open(tick_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for r in reader:
            if r['time'].startswith(target_prefix):
                spread = float(r['ask']) - float(r['bid'])
                print(f"Time: {r['time']} | Bid: {r['bid']} | Ask: {r['ask']} | Spread: ${spread:.3f}")
                count += 1
                if count >= 6:
                    break

# Inspect around Top 1 Buy (13:19 UTC) and Top 2 Sell (01:15 UTC)
inspect_book_at_time("13:19")
inspect_ticks_at_time("13:19:0")

inspect_book_at_time("01:15")
inspect_ticks_at_time("01:15:0")
