import os
import sys
import time
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')

path_2022 = r"d:\cbot-atgvt\data\XAUUSD_2022_Minute.csv"

# Existing 2023-2026 path
path_2023_2026 = os.path.expandvars(r'%USERPROFILE%\OneDrive\เอกสาร\BacktestLab\data\XAUUSD_Minute.csv')
if not os.path.exists(path_2023_2026):
    path_2023_2026 = os.path.expandvars(r'%USERPROFILE%\Documents\BacktestLab\data\XAUUSD_Minute.csv')

merged_path = r"d:\cbot-atgvt\data\XAUUSD_2022_2026_Minute.csv"

print(f"Reading 2022 data from: {path_2022}")
t0 = time.time()
rows_dict = {}

with open(path_2022, 'r', encoding='utf-8') as f:
    f.readline() # header
    for line in f:
        p = line.rstrip().split(',')
        if len(p) >= 6:
            rows_dict[int(p[0])] = (float(p[1]), float(p[2]), float(p[3]), float(p[4]), float(p[5]))

print(f"Loaded 2022: {len(rows_dict):,} bars")

print(f"Reading 2023-2026 data from: {path_2023_2026}")
with open(path_2023_2026, 'r', encoding='utf-8') as f:
    f.readline() # header
    for line in f:
        p = line.rstrip().split(',')
        if len(p) >= 6:
            rows_dict[int(p[0])] = (float(p[1]), float(p[2]), float(p[3]), float(p[4]), float(p[5]))

sorted_unix = sorted(rows_dict.keys())
print(f"Total Unique M1 Bars: {len(sorted_unix):,} (spanning {time.strftime('%Y-%m-%d', time.gmtime(sorted_unix[0]))} to {time.strftime('%Y-%m-%d', time.gmtime(sorted_unix[-1]))})")

print(f"Writing merged dataset to: {merged_path}")
with open(merged_path, 'w', encoding='utf-8') as f:
    f.write("unix,open,high,low,close,volume\n")
    for u in sorted_unix:
        o, h, l, c, v = rows_dict[u]
        f.write(f"{u},{o:.2f},{h:.2f},{l:.2f},{c:.2f},{v:.0f}\n")

print(f"Finished writing merged dataset in {time.time()-t0:.2f}s. File size: {os.path.getsize(merged_path)/1024/1024:.2f} MB")
