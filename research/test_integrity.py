with open(r'd:\cbot-atgvt\docs\index.html', 'r', encoding='utf-8') as f:
    text = f.read()

checks = [
    'dom_absorption_btc',
    'id="tab-dom-abs-btc"',
    'id="tab-dom-abs-eth"',
    'id="live-forward-card"',
    'fetchLiveStatus()',
    'setInterval(fetchLiveStatus, 3000)'
]
for c in checks:
    print(f"Check: {c:35} -> {'FOUND' if c in text else 'MISSING'}")
