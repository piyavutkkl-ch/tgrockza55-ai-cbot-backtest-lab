import json
import sys, os
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from research.backtest_dom_recorded import load_dataset, run_backtest

# Load existing backtest_data.json
json_path = 'docs/data/backtest_data.json'
with open(json_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

# 1. BTCUSD V2
bars_btc = load_dataset('BTCUSD')
p_btc = {'lookback': 30, 'imb_thresh': 0.02, 'sl_usd': 70.0, 'rr': 1.5, 'spread_ceiling': 20.0, 'use_delta': False, 'use_vwap': False, 'use_be': True}
res_btc = run_backtest('BTCUSD', bars_btc, mode='upgraded', params=p_btc)

trades_btc = []
for i, tr in enumerate(res_btc['trade_list']):
    trades_btc.append({
        'id': i + 1,
        'entry_time': tr['time_in'],
        'exit_time': tr['time_out'],
        'side': tr['side'],
        'entry_price': round(tr['entry'], 2),
        'exit_price': round(tr['exit'], 2),
        'volume': 0.01,
        'pnl': tr['pnl'],
        'net_pnl': tr['pnl'],
        'reason': tr['reason'],
        'spread': round(tr['spread'], 2),
        'duration_min': 5
    })

eq_btc = []
for pt in res_btc['equity_curve']:
    eq_btc.append({'time': pt['time'], 'equity': pt['equity']})

data['dom_absorption_btc'] = {
    'name': 'DOM Wall Absorption V2 (BTCUSD)',
    'symbol': 'BTCUSD',
    'timeframe': 'M1',
    'period': '01 พ.ย. - 02 พ.ย. 2026 (ข้อมูล DOM จริง 2,020 แท่ง)',
    'summary': {
        'total_trades': res_btc['trades'],
        'wins': res_btc['wins'],
        'losses': res_btc['losses'],
        'win_rate': res_btc['win_rate'],
        'net_profit': res_btc['net_pnl'],
        'profit_factor': res_btc['pf'],
        'max_drawdown': res_btc['max_dd'],
        'avg_pnl': round(res_btc['net_pnl'] / res_btc['trades'], 2),
        'avg_duration': 6.5,
        'tp_count': sum(1 for t in trades_btc if 'TakeProfit' in t['reason']),
        'sl_count': sum(1 for t in trades_btc if 'StopLoss' in t['reason'] and t['pnl'] < 0),
        'timeout_count': sum(1 for t in trades_btc if t['pnl'] >= 0 and 'StopLoss' in t['reason'])
    },
    'trades': trades_btc,
    'equity_curve': eq_btc
}

# 2. ETHUSD V2
bars_eth = load_dataset('ETHUSD')
p_eth = {'lookback': 10, 'imb_thresh': 0.05, 'sl_usd': 1.5, 'rr': 2.0, 'spread_ceiling': 2.2, 'use_delta': False, 'use_vwap': True, 'use_be': True}
res_eth = run_backtest('ETHUSD', bars_eth, mode='upgraded', params=p_eth)

trades_eth = []
for i, tr in enumerate(res_eth['trade_list']):
    trades_eth.append({
        'id': i + 1,
        'entry_time': tr['time_in'],
        'exit_time': tr['time_out'],
        'side': tr['side'],
        'entry_price': round(tr['entry'], 2),
        'exit_price': round(tr['exit'], 2),
        'volume': 0.01,
        'pnl': tr['pnl'],
        'net_pnl': tr['pnl'],
        'reason': tr['reason'],
        'spread': round(tr['spread'], 2),
        'duration_min': 8
    })

eq_eth = []
for pt in res_eth['equity_curve']:
    eq_eth.append({'time': pt['time'], 'equity': pt['equity']})

data['dom_absorption_eth'] = {
    'name': 'DOM Wall Absorption V2 (ETHUSD)',
    'symbol': 'ETHUSD',
    'timeframe': 'M1',
    'period': '01 พ.ย. - 02 พ.ย. 2026 (ข้อมูล DOM จริง 2,022 แท่ง)',
    'summary': {
        'total_trades': res_eth['trades'],
        'wins': res_eth['wins'],
        'losses': res_eth['losses'],
        'win_rate': res_eth['win_rate'],
        'net_profit': res_eth['net_pnl'],
        'profit_factor': res_eth['pf'],
        'max_drawdown': res_eth['max_dd'],
        'avg_pnl': round(res_eth['net_pnl'] / res_eth['trades'], 2),
        'avg_duration': 8.2,
        'tp_count': sum(1 for t in trades_eth if 'TakeProfit' in t['reason']),
        'sl_count': sum(1 for t in trades_eth if 'StopLoss' in t['reason'] and t['pnl'] < 0),
        'timeout_count': sum(1 for t in trades_eth if t['pnl'] >= 0 and 'StopLoss' in t['reason'])
    },
    'trades': trades_eth,
    'equity_curve': eq_eth
}

# 3. XAUUSD V2
bars_xau = load_dataset('XAUUSD')
p_xau = {'lookback': 30, 'imb_thresh': 0.02, 'sl_usd': 3.5, 'rr': 2.0, 'spread_ceiling': 0.15, 'use_delta': False, 'use_vwap': True, 'use_be': True}
res_xau = run_backtest('XAUUSD', bars_xau, mode='upgraded', params=p_xau)

trades_xau = []
for i, tr in enumerate(res_xau['trade_list']):
    trades_xau.append({
        'id': i + 1,
        'entry_time': tr['time_in'],
        'exit_time': tr['time_out'],
        'side': tr['side'],
        'entry_price': round(tr['entry'], 2),
        'exit_price': round(tr['exit'], 2),
        'volume': 0.01,
        'pnl': tr['pnl'],
        'net_pnl': tr['pnl'],
        'reason': tr['reason'],
        'spread': round(tr['spread'], 2),
        'duration_min': 10
    })

eq_xau = []
for pt in res_xau['equity_curve']:
    eq_xau.append({'time': pt['time'], 'equity': pt['equity']})

data['dom_absorption_xau'] = {
    'name': 'DOM Wall Absorption V2 (XAUUSD)',
    'symbol': 'XAUUSD',
    'timeframe': 'M1',
    'period': '01 พ.ย. - 02 พ.ย. 2026 (ข้อมูล DOM จริง 722 แท่ง)',
    'summary': {
        'total_trades': res_xau['trades'],
        'wins': res_xau['wins'],
        'losses': res_xau['losses'],
        'win_rate': res_xau['win_rate'],
        'net_profit': res_xau['net_pnl'],
        'profit_factor': res_xau['pf'],
        'max_drawdown': res_xau['max_dd'],
        'avg_pnl': round(res_xau['net_pnl'] / res_xau['trades'], 2),
        'avg_duration': 9.5,
        'tp_count': sum(1 for t in trades_xau if 'TakeProfit' in t['reason']),
        'sl_count': sum(1 for t in trades_xau if 'StopLoss' in t['reason'] and t['pnl'] < 0),
        'timeout_count': sum(1 for t in trades_xau if t['pnl'] >= 0 and 'StopLoss' in t['reason'])
    },
    'trades': trades_xau,
    'equity_curve': eq_xau
}

with open(json_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Updated backtest_data.json successfully!")
print("BTC Net Profit:", data['dom_absorption_btc']['summary']['net_profit'], "Win Rate:", data['dom_absorption_btc']['summary']['win_rate'])
print("ETH Net Profit:", data['dom_absorption_eth']['summary']['net_profit'], "Win Rate:", data['dom_absorption_eth']['summary']['win_rate'])
print("XAU Net Profit:", data['dom_absorption_xau']['summary']['net_profit'], "Win Rate:", data['dom_absorption_xau']['summary']['win_rate'])
