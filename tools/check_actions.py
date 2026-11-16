import urllib.request
import json
import time

url = 'https://api.github.com/repos/piyavutkkl-ch/tgrockza55-ai-cbot-backtest-lab/actions/runs?per_page=3'
req = urllib.request.Request(url, headers={'User-Agent': 'Python'})
try:
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode())
        for run in data.get('workflow_runs', []):
            print(f"{run['id']}: {run['name']} - status={run['status']}, conclusion={run['conclusion']}, sha={run['head_sha'][:7]}")
except Exception as e:
    print('Error:', e)
