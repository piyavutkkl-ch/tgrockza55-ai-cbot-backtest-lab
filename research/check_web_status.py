import urllib.request
import json

base_url = 'https://tgrockza55-ai.github.io/tgrockza55-ai-cbot-backtest-lab/'

endpoints = [
    'index.html',
    'data/live_status.json',
    'data/backtest_data.json'
]

for ep in endpoints:
    url = base_url + ep
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as resp:
            status = resp.status
            content = resp.read()
            print(f'URL: {url}')
            print(f'Status: {status}, Size: {len(content):,} bytes')
            if ep == 'index.html':
                html = content.decode('utf-8', errors='ignore')
                checks = [
                    'dom_absorption_btc',
                    'tab-dom-abs-btc',
                    'live-forward-card',
                    'fetchLiveStatus'
                ]
                for c in checks:
                    found = 'FOUND' if c in html else 'NOT FOUND'
                    print(f'  Check {c:20}: {found}')
            elif ep == 'data/live_status.json':
                data = json.loads(content.decode('utf-8'))
                print('  Live Status Timestamp:', data.get('timestamp_local'))
                print('  Forward bot status:', data.get('forward_trading', {}).get('status'))
                print('  BTC Mid Price:', data.get('dom_recorders', [{}])[0].get('current_price'))
            elif ep == 'data/backtest_data.json':
                db = json.loads(content.decode('utf-8'))
                print('  Strategies in backtest_data:', list(db.keys()))
    except Exception as e:
        print(f'URL: {url} -> ERROR: {e}')
