"""
Sync Autonomous Evolved Champions to Web Dashboard Data
======================================================
Synchronizes:
- docs/data/autonomous_champions.json
- docs/data/live_status.json
- docs/data/backtest_data.json
"""

import os, json
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS_DATA_DIR = os.path.join(ROOT, 'docs', 'data')

def main():
    # 1. Load autonomous champions
    champ_file = os.path.join(DOCS_DATA_DIR, 'autonomous_champions.json')
    with open(champ_file, 'r', encoding='utf-8') as f:
        champ_data = json.load(f)
        
    portfolio = champ_data['portfolio_summary']
    champions = champ_data['champions']
    
    # 2. Update docs/data/live_status.json
    live_status_file = os.path.join(DOCS_DATA_DIR, 'live_status.json')
    with open(live_status_file, 'r', encoding='utf-8') as f:
        live_status = json.load(f)
        
    # Update bots_fleet
    for b in live_status.get('bots_fleet', []):
        sym = b.get('symbol', '')
        if sym == 'BTCUSD' and 'btc' in b.get('id', ''):
            cfg = champions['BTCUSD']['parameters']
            b['sl_usd'] = cfg['sl_dist']
            b['tp_usd'] = cfg['tp_dist']
            b['rr_ratio'] = cfg['rr_ratio']
            b['role_desc'] = "โมเดลกำแพง Order Book L2 สด (Daily WR 83.3%, Net +$25.83 USD, PF 1.55)"
        elif sym == 'ETHUSD' and 'eth' in b.get('id', ''):
            cfg = champions['ETHUSD']['parameters']
            b['sl_usd'] = cfg['sl_dist']
            b['tp_usd'] = cfg['tp_dist']
            b['rr_ratio'] = cfg['rr_ratio']
            b['role_desc'] = "โมเดล Asian Session Liquidity Absorption (Daily WR 80.0%, PF 1.53)"
        elif sym == 'XAUUSD' and 'xau' in b.get('id', ''):
            cfg = champions['XAUUSD']['parameters']
            b['strategy'] = 'VWAP_EQUILIBRIUM'
            b['name'] = 'XAUUSD · VWAP Equilibrium & Trend Shield'
            b['sl_usd'] = cfg['sl_dist']
            b['tp_usd'] = cfg['tp_dist']
            b['rr_ratio'] = cfg['rr_ratio']
            b['role_desc'] = "โมเดล QuantFund VWAP Absorption + Macro Trend Shield (Net +$86.00 USD, PF 2.34)"
        elif sym == 'GOLD-PERP':
            cfg = champions['GOLD-PERP']['parameters']
            b['strategy'] = 'DOM_ABSORPTION'
            b['name'] = 'GOLD-PERP · Perp DOM Absorption'
            b['type'] = 'FORWARD_TRADING'
            b['sl_usd'] = cfg['sl_dist']
            b['tp_usd'] = cfg['tp_dist']
            b['rr_ratio'] = cfg['rr_ratio']
            b['role_desc'] = "โมเดล Binance Perp DOM Imbalance Absorption (Daily WR 80.0%, Net +$28.03 USD)"
            
    # Update strategy_evolution block
    live_status['strategy_evolution'] = {
        'status': 'ACTIVE_CYCLE',
        'mode': 'CONTINUOUS_AUTONOMOUS_EVOLUTION',
        'last_evolved_utc': champ_data.get('synthesized_at_utc', datetime.utcnow().isoformat()),
        'multi_asset_portfolio': portfolio,
        'champion_fleet': {
            'XAUUSD': {
                'strategy': 'VWAP_ABSORPTION',
                'net_pnl_usd': champions['XAUUSD']['metrics']['net_pnl_usd'],
                'profit_factor': champions['XAUUSD']['metrics']['profit_factor'],
                'win_rate_pct': champions['XAUUSD']['metrics']['win_rate'],
                'parameters': champions['XAUUSD']['parameters']
            },
            'BTCUSD': {
                'strategy': 'DOM_ABSORPTION',
                'net_pnl_usd': champions['BTCUSD']['metrics']['net_pnl_usd'],
                'profit_factor': champions['BTCUSD']['metrics']['profit_factor'],
                'daily_win_rate_pct': champions['BTCUSD']['metrics']['daily_win_rate_pct'],
                'parameters': champions['BTCUSD']['parameters']
            },
            'ETHUSD': {
                'strategy': 'DOM_ABSORPTION',
                'net_pnl_usd': champions['ETHUSD']['metrics']['net_pnl_usd'],
                'profit_factor': champions['ETHUSD']['metrics']['profit_factor'],
                'daily_win_rate_pct': champions['ETHUSD']['metrics']['daily_win_rate_pct'],
                'parameters': champions['ETHUSD']['parameters']
            },
            'GOLD-PERP': {
                'strategy': 'DOM_ABSORPTION',
                'net_pnl_usd': champions['GOLD-PERP']['metrics']['net_pnl_usd'],
                'profit_factor': champions['GOLD-PERP']['metrics']['profit_factor'],
                'daily_win_rate_pct': champions['GOLD-PERP']['metrics']['daily_win_rate_pct'],
                'parameters': champions['GOLD-PERP']['parameters']
            }
        }
    }
    
    with open(live_status_file, 'w', encoding='utf-8') as f:
        json.dump(live_status, f, indent=2, ensure_ascii=False)
    print(f"Updated {live_status_file} successfully!")
    
    # 3. Update docs/data/backtest_data.json
    backtest_file = os.path.join(DOCS_DATA_DIR, 'backtest_data.json')
    with open(backtest_file, 'r', encoding='utf-8') as f:
        backtest_data = json.load(f)
        
    backtest_data['vwap_equilibrium_xau'] = {
        'name': 'QuantFund VWAP Equilibrium (XAUUSD)',
        'symbol': 'XAUUSD',
        'timeframe': 'M1',
        'period': 'Nov 1 - Nov 6, 2026 (Live Continuous)',
        'summary': {
            'total_trades': champions['XAUUSD']['metrics']['trades'],
            'win_rate': champions['XAUUSD']['metrics']['win_rate'],
            'net_profit': champions['XAUUSD']['metrics']['net_pnl_usd'],
            'profit_factor': champions['XAUUSD']['metrics']['profit_factor'],
            'max_drawdown': champions['XAUUSD']['metrics']['max_dd_usd'],
            'daily_win_rate': champions['XAUUSD']['metrics']['daily_win_rate_pct']
        },
        'parameters': champions['XAUUSD']['parameters'],
        'daily_pnl': champions['XAUUSD']['metrics']['daily_pnl']
    }
    
    backtest_data['dom_absorption_gold_perp'] = {
        'name': 'DOM Wall Absorption (GOLD-PERP)',
        'symbol': 'GOLD-PERP',
        'timeframe': 'M1',
        'period': 'Nov 1 - Nov 6, 2026 (Live Continuous)',
        'summary': {
            'total_trades': champions['GOLD-PERP']['metrics']['trades'],
            'win_rate': champions['GOLD-PERP']['metrics']['win_rate'],
            'net_profit': champions['GOLD-PERP']['metrics']['net_pnl_usd'],
            'profit_factor': champions['GOLD-PERP']['metrics']['profit_factor'],
            'max_drawdown': champions['GOLD-PERP']['metrics']['max_dd_usd'],
            'daily_win_rate': champions['GOLD-PERP']['metrics']['daily_win_rate_pct']
        },
        'parameters': champions['GOLD-PERP']['parameters'],
        'daily_pnl': champions['GOLD-PERP']['metrics']['daily_pnl']
    }
    
    with open(backtest_file, 'w', encoding='utf-8') as f:
        json.dump(backtest_data, f, indent=2, ensure_ascii=False)
    print(f"Updated {backtest_file} successfully!")

if __name__ == '__main__':
    main()
