import urllib.request
import sys

sys.stdout.reconfigure(encoding='utf-8')

for aid in ['2403.09267', '2408.03594', '2003.00130', '1808.03668']:
    url = f"https://arxiv.org/html/{aid}"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req) as resp:
            print(f"[{aid}] HTML full text available! Status: {resp.status}, size: {len(resp.read())} bytes")
    except urllib.error.HTTPError as e:
        print(f"[{aid}] No direct HTML (HTTP {e.code}), use abs/PDF")
    except Exception as e:
        print(f"[{aid}] Error: {e}")
