with open(r'd:\cbot-atgvt\docs\index.html', 'r', encoding='utf-8') as f:
    html = f.read()

ids = [
    'live-clock', 'live-price', 'live-spread', 'live-imbalance', 
    'live-imbalance-desc', 'live-cvd', 'live-balance', 
    'tab-dom-abs-btc', 'tab-dom-abs-eth', 
    'beginner-guide-drawer', 'guide-btn-text',
    'chart-selected-title', 'chart-date-badge', 'chart-time-badge',
    'trade-banner-bar', 'trade-table-body', 'inspector-content'
]

for i in ids:
    found = f'id="{i}"' in html
    print(f"{i:25} : {'FOUND' if found else 'MISSING!'}")
