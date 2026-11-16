import os
import glob
import re

strat_glob = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'cbot', 'BacktestLab', 'Strategies', '*.cs')
for f in sorted(glob.glob(strat_glob)):
    with open(f, 'r', encoding='utf-8') as fp:
        c = fp.read()
    m = re.search(r'public override string Code => "([^"]+)"', c)
    p = re.search(r'public override string\[\] ParamNames => new\[\]\s*\{([^}]+)\}', c)
    if m:
        params = p.group(1).replace('"', '').strip() if p else 'None'
        print(f"{m.group(1):28s} | {params}")
