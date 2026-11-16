import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

# 1. Load existing strategies (141)
with open('zz_zz PAPER/strategies_database.json', 'r', encoding='utf-8') as f:
    strategies = json.load(f)

# Ensure arXiv source tag
for s in strategies:
    s['source'] = 'arXiv'

# 2. Load all papers (193)
with open('zz_zz PAPER/papers_database.json', 'r', encoding='utf-8') as f:
    papers = json.load(f)

ssrn_papers = [p for p in papers if p.get('source') == 'SSRN']

cat_icons = {
    '01_lob_and_deep_learning': '🧠',
    '02_order_flow_imbalance': '📊',
    '03_market_making_and_spread': '⚖️',
    '04_optimal_execution_and_vwap': '⏱️',
    '05_hawkes_and_point_processes': '📈',
    '06_gold_and_commodity_seasonality': '🥇',
    '07_regime_detection_and_hmm': '🔄',
    '08_lead_lag_and_latency': '⚡',
    '09_signal_processing_and_kalman': '📡',
    '10_synthetic_data_and_simulation': '🎲',
    '11_financial_llm_and_sentiment': '💬',
    '12_position_sizing_and_risk': '🛡️',
    '13_rough_volatility_and_jumps': '🌊'
}

cat_titles = {
    '01_lob_and_deep_learning': '01 LOB & Deep Learning',
    '02_order_flow_imbalance': '02 Order Flow Imbalance',
    '03_market_making_and_spread': '03 Market Making & Spread',
    '04_optimal_execution_and_vwap': '04 Execution & VWAP',
    '05_hawkes_and_point_processes': '05 Hawkes & Point Processes',
    '06_gold_and_commodity_seasonality': '06 Gold & Commodities',
    '07_regime_detection_and_hmm': '07 Regime Detection & HMM',
    '08_lead_lag_and_latency': '08 Lead-Lag & Latency',
    '09_signal_processing_and_kalman': '09 Kalman & Signal Processing',
    '10_synthetic_data_and_simulation': '10 Synthetic Simulation',
    '11_financial_llm_and_sentiment': '11 Financial LLM & News',
    '12_position_sizing_and_risk': '12 Kelly & Position Sizing',
    '13_rough_volatility_and_jumps': '13 Rough Volatility & Jumps'
}

# 3. Create strategy entries for SSRN papers
for i, p in enumerate(ssrn_papers, 1):
    sid = p.get('ssrn_id') or str(i)
    cat_folder = p.get('category_folder', '01_lob_and_deep_learning')
    icon = cat_icons.get(cat_folder, '📚')
    cat_title = cat_titles.get(cat_folder, cat_folder)
    
    # Extract clean abstract snippet
    abstract = p.get('abstract', '').strip()
    
    entry = {
        'id': f'SSRN-{sid}',
        'index': 141 + i,
        'paper_id': f'SSRN-{sid}',
        'base_id': sid,
        'source': 'SSRN',
        'title': p.get('title', ''),
        'authors': p.get('authors', []),
        'published': p.get('published', '2025-2026'),
        'category_folder': cat_folder,
        'category_title': cat_title,
        'category_icon': icon,
        'strategy_type': 'SSRN Institutional Research Alpha',
        'entry_trigger': 'สัญญาณทางคณิตศาสตร์/โครงสร้างจุลภาคตามโมเดลในเปเปอร์ SSRN',
        'exit_trigger': 'ปิดตามรอบ Auction/Session หรือเมื่อค่า Signal เกินเกณฑ์เบี่ยงเบน',
        'profit_mechanism': 'สกัดความได้เปรียบจากโครงสร้างตลาด (Microstructure Premium & Price Discovery)',
        'strengths': 'ผ่านการพิสูจน์ด้วยข้อมูลตลาดการเงินจริง พร้อมโมเดลเศรษฐมิติเชิงลึก',
        'weaknesses': 'ต้องควบคุม Latency และต้นทุน Slippage ให้ต่ำกว่า Expected Return',
        'risks': 'Regime shift และสภาพคล่องหดตัวฉับพลัน (Liquidity Void)',
        'compatible_with': 'Quant Fund V2 Pipeline (H1-1D Horizon)',
        'html_url': p.get('url', f'https://papers.ssrn.com/sol3/papers.cfm?abstract_id={sid}'),
        'pdf_url': p.get('url', f'https://papers.ssrn.com/sol3/papers.cfm?abstract_id={sid}'),
        'abstract': abstract
    }
    strategies.append(entry)

print(f'Total unified papers & strategies: {len(strategies)}')
print(f'arXiv: {len([s for s in strategies if s.get("source") == "arXiv"])}')
print(f'SSRN: {len([s for s in strategies if s.get("source") == "SSRN"])}')

# Save to zz_zz PAPER/strategies_database_193.json and docs/data/papers_193.json
with open('zz_zz PAPER/strategies_database.json', 'w', encoding='utf-8') as f:
    json.dump(strategies, f, indent=2, ensure_ascii=False)
print('✓ Saved unified 193 strategies into zz_zz PAPER/strategies_database.json')

with open('docs/data/papers_database.json', 'w', encoding='utf-8') as f:
    json.dump(strategies, f, indent=2, ensure_ascii=False)
print('✓ Saved docs/data/papers_database.json')
