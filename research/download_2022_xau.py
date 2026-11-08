import requests
import sys
import os
import datetime

sys.stdout.reconfigure(encoding='utf-8')

url = 'https://huggingface.co/datasets/Pcitycrypto/xauusd/resolve/main/XAUUSD_1m.csv'
size = 229897908

# Start offset for 2022: around 191142244
start_offset = 191142200

# Binary search for 2023-01-02 (end of 2022)
low = start_offset
high = size

for step in range(25):
    mid = (low + high) // 2
    r = requests.get(url, headers={'Range': f'bytes={mid}-{mid+200}'}, timeout=10)
    lines = r.text.splitlines()
    if len(lines) > 1:
        first_line = lines[1]
        dt = first_line.split(',')[0]
        if dt < '2023-01-02':
            low = mid
        else:
            high = mid

end_offset = high + 500
print(f"2022 Range: bytes={start_offset}-{end_offset} (~{(end_offset - start_offset)/1024/1024:.2f} MB)")

# Download the exact 2022 chunk
out_path = r"d:\cbot-atgvt\data\XAUUSD_2022_Minute.csv"
os.makedirs(os.path.dirname(out_path), exist_ok=True)

print("Downloading 2022 XAU/USD data chunk...")
r = requests.get(url, headers={'Range': f'bytes={start_offset}-{end_offset}'}, timeout=60)
raw_text = r.text

lines = raw_text.splitlines()
print(f"Total raw lines in chunk: {len(lines)}")

# Parse and format into standard format matching XAUUSD_Minute.csv:
# Format: unix,open,high,low,close,volume
clean_rows = []
for line in lines:
    parts = line.strip().split(',')
    if len(parts) >= 6:
        dt_str = parts[0]
        if dt_str.startswith('2022-'):
            try:
                # 2022-01-03 01:04:00
                dt = datetime.datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')
                unix_ts = int(dt.replace(tzinfo=datetime.timezone.utc).timestamp())
                o = float(parts[1])
                h = float(parts[2])
                l = float(parts[3])
                c = float(parts[4])
                vol = float(parts[5])
                clean_rows.append(f"{unix_ts},{o:.2f},{h:.2f},{l:.2f},{c:.2f},{vol:.0f}")
            except Exception:
                continue

print(f"Clean 2022 bars parsed: {len(clean_rows):,}")
print(f"First bar: {clean_rows[0]}")
print(f"Last bar:  {clean_rows[-1]}")

with open(out_path, 'w', encoding='utf-8') as f:
    f.write("unix,open,high,low,close,volume\n")
    for row in clean_rows:
        f.write(row + "\n")

print(f"Successfully saved 2022 data to: {out_path}")
