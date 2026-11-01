import os
import time
import numpy as np

docs = os.path.expandvars(r'%USERPROFILE%\OneDrive\เอกสาร')
csv_path = os.path.join(docs, 'BacktestLab', 'data', 'XAUUSD_Minute.csv')
if not os.path.exists(csv_path):
    docs = os.path.expandvars(r'%USERPROFILE%\Documents')
    csv_path = os.path.join(docs, 'BacktestLab', 'data', 'XAUUSD_Minute.csv')

t0 = time.time()
with open(csv_path, 'r', encoding='utf-8') as f:
    header = f.readline()
    data = []
    # parse columns: unix, open, high, low, close, volume
    for line in f:
        p = line.rstrip().split(',')
        data.append((int(p[0]), float(p[1]), float(p[2]), float(p[3]), float(p[4]), float(p[5])))

arr = np.array(data, dtype=[('unix', 'i8'), ('open', 'f8'), ('high', 'f8'), ('low', 'f8'), ('close', 'f8'), ('vol', 'f8')])
t1 = time.time()
print(f"Loaded {len(arr):,} bars into NumPy structured array in {t1-t0:.2f}s")
print(f"Start: unix={arr['unix'][0]} (Price: {arr['close'][0]})")
print(f"End:   unix={arr['unix'][-1]} (Price: {arr['close'][-1]})")
