import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

base = os.path.expandvars(r"%LOCALAPPDATA%\BacktestLab\live")
print(f"=== CHECKING LIVE DIRECTORY: {base} ===\n")

if not os.path.exists(base):
    print("Directory does not exist!")
    sys.exit(0)

stats = {}
for root, dirs, files in os.walk(base):
    for f in files:
        fp = os.path.join(root, f)
        size_kb = os.path.getsize(fp) / 1024
        lines = 0
        header = ""
        first_line = ""
        last_line = ""
        if f.endswith(".csv"):
            try:
                with open(fp, "r", encoding="utf-8", errors="ignore") as fl:
                    first = True
                    for line in fl:
                        lines += 1
                        if first:
                            header = line.strip()
                            first = False
                        elif lines == 2:
                            first_line = line.strip()
                        last_line = line.strip()
            except Exception:
                pass
        rel = os.path.relpath(fp, base)
        parts = rel.split(os.sep)
        symbol = parts[0] if len(parts) > 1 else "ROOT"
        file_type = parts[1] if len(parts) > 1 else parts[0]
        
        if symbol not in stats:
            stats[symbol] = []
        stats[symbol].append({
            'file': file_type,
            'rel': rel,
            'size_kb': size_kb,
            'lines': lines,
            'first': first_line,
            'last': last_line,
            'mtime': os.path.getmtime(fp)
        })

for sym, flist in stats.items():
    print(f"==================================================")
    print(f"  SYMBOL: {sym}")
    print(f"==================================================")
    for item in sorted(flist, key=lambda x: x['file']):
        print(f"  📄 {item['file']:25s} | {item['size_kb']:9.1f} KB | {item['lines']:7d} rows")
        if item['first']:
            # Extract timestamp if possible
            t_start = item['first'].split(',')[0] if ',' in item['first'] else item['first'][:20]
            t_end = item['last'].split(',')[0] if ',' in item['last'] else item['last'][:20]
            print(f"     Time range: {t_start} -> {t_end}")
    print()
