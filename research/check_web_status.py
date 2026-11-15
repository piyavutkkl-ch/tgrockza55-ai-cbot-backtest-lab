import urllib.request
import json

base_url = 'https://piyavutkkl-ch.github.io/tgrockza55-ai-cbot-backtest-lab/'

html_pages = [
    'index.html',
    'data-center.html',
    'research-lab.html',
    'experiment-lab.html',
    'intelligence.html',
    'improvement-audit.html',
    'archive-system.html',
    'database.html',
]

json_endpoints = [
    'data/live_status.json',
    'data/truth_guard.json',
    'data/overview_summary.json',
    'data/intelligence_summary.json',
    'data/audit_summary.json',
    'data/backtest_data.json',
    'assets/database_catalog.json',
]

for ep in html_pages + json_endpoints:
    url = base_url + ep
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as resp:
            status = resp.status
            content = resp.read()
            print(f'URL: {url} -> {status} ({len(content):,} bytes)')
            if ep == 'index.html':
                html = content.decode('utf-8', errors='ignore')
                for c in ['app-shell', 'card-live-demo', 'card-champion-backtest', 'assets/overview.js']:
                    print(f'  Check {c:24}: {"FOUND" if c in html else "MISSING"}')
            elif ep == 'data/live_status.json':
                data = json.loads(content.decode('utf-8'))
                print('  Live Status Timestamp:', data.get('timestamp_local'))
                print('  Forward bot status:', data.get('forward_trading', {}).get('status'))
                print('  Closed Trades N:', data.get('truth_guard', {}).get('metrics_empirical', {}).get('total_closed_trades_N'))
            elif ep == 'data/backtest_data.json':
                db = json.loads(content.decode('utf-8'))
                print('  Strategies in backtest_data:', list(db.keys()))
    except Exception as e:
        print(f'URL: {url} -> ERROR: {e}')
