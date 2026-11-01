import os
import csv
import math

base = os.path.expandvars(r'%LOCALAPPDATA%\BacktestLab\live')

for sym in ['BTCUSD', 'ETHUSD']:
    min_f = os.path.join(base, sym, 'min-2026-11.csv')
    flow_f = os.path.join(base, sym, 'flow-2026-11.csv')
    if os.path.exists(min_f):
        with open(min_f, 'r', encoding='utf-8') as f:
            reader = list(csv.DictReader(f))
        print(f"=== {sym} ===")
        print(f"Total minutes: {len(reader)}")
        if reader:
            print(f"Columns: {list(reader[0].keys())}")
            print(f"Time range: {reader[0]['time']} to {reader[-1]['time']}")
            
        if os.path.exists(flow_f):
            with open(flow_f, 'r', encoding='utf-8') as f:
                f_reader = list(csv.DictReader(f))
            print(f"Flow rows: {len(f_reader)}")
            if f_reader:
                print(f"Flow columns: {list(f_reader[0].keys())}")
