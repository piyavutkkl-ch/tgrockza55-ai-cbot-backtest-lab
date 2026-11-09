"""
Synthesize Master Autonomous Portfolio Across All 4 Assets
===========================================================
Aggregates the evolved champion bots:
1. XAUUSD: QuantFund VWAP Equilibrium + Macro Trend Shield (Net +$86.00 USD, PF 2.34)
2. BTCUSD: DOM Wall Absorption + Smart DOM Exit (Net +$25.83 USD, PF 1.55, Daily WR 83.3%)
3. ETHUSD: Asian Liquidity DOM Absorption (Net +$0.42 USD, PF 1.53, Daily WR 80.0%)
4. GOLD-PERP: Perp Order Book Imbalance Absorption (Net +$28.03 USD, PF 1.87, Daily WR 80.0%)
"""

import os, json
from collections import defaultdict
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS_DATA_DIR = os.path.join(ROOT, 'docs', 'data')

# Evolved Champions Data
champions = {
    'XAUUSD': {
        'name': 'XAUUSD · QuantFund VWAP Absorption & Trend Shield',
        'strategy_type': 'VWAP_ABSORPTION',
        'session': 'ALL',
        'parameters': {
            'sl_dist': 4.0,
            'rr_ratio': 2.5,
            'tp_dist': 10.0,
            'be_r': 0.0,
            'sd_mult': 1.0,
            'delta_threshold': 5.0,
            'macro_trend_shield': True,
            'circuit_breaker': True
        },
        'metrics': {
            'trades': 31,
            'win_rate': 48.4,
            'net_pnl_usd': 86.00,
            'profit_factor': 2.34,
            'max_dd_usd': 12.00,
            'daily_win_rate_pct': 60.0,
            'daily_pnl': {
                '2026-11-02': 70.00,
                '2026-11-03': -2.00,
                '2026-11-04': 4.00,
                '2026-11-05': 16.00,
                '2026-11-06': -2.00
            }
        }
    },
    'BTCUSD': {
        'name': 'BTCUSD · L2 Order Book DOM Wall Absorption',
        'strategy_type': 'DOM_ABSORPTION',
        'session': 'ALL',
        'parameters': {
            'sl_dist': 100.0,
            'rr_ratio': 1.8,
            'tp_dist': 180.0,
            'be_r': 1.0,
            'imb_thresh': 0.025,
            'smart_dom_exit': True,
            'news_gate': True
        },
        'metrics': {
            'trades': 96,
            'win_rate': 54.2,
            'net_pnl_usd': 25.83,
            'profit_factor': 1.55,
            'max_dd_usd': 9.42,
            'daily_win_rate_pct': 83.3,
            'daily_pnl': {
                '2026-11-01': 1.28,
                '2026-11-02': 13.61,
                '2026-11-03': 0.62,
                '2026-11-04': -2.21,
                '2026-11-05': 10.40,
                '2026-11-06': 2.13
            }
        }
    },
    'ETHUSD': {
        'name': 'ETHUSD · Asian Liquidity Imbalance Absorption',
        'strategy_type': 'DOM_ABSORPTION',
        'session': 'ASIA',
        'parameters': {
            'sl_dist': 2.5,
            'rr_ratio': 2.8,
            'tp_dist': 7.0,
            'be_r': 1.0,
            'imb_thresh': 0.015,
            'smart_dom_exit': True,
            'news_gate': True
        },
        'metrics': {
            'trades': 56,
            'win_rate': 53.6,
            'net_pnl_usd': 0.42,
            'profit_factor': 1.53,
            'max_dd_usd': 0.16,
            'daily_win_rate_pct': 80.0,
            'daily_pnl': {
                '2026-11-01': 0.08,
                '2026-11-02': -0.05,
                '2026-11-03': 0.11,
                '2026-11-05': 0.02,
                '2026-11-06': 0.26
            }
        }
    },
    'GOLD-PERP': {
        'name': 'GOLD-PERP · Binance Perp Order Book Absorption',
        'strategy_type': 'DOM_ABSORPTION',
        'session': 'ALL',
        'parameters': {
            'sl_dist': 5.0,
            'rr_ratio': 2.5,
            'tp_dist': 12.5,
            'be_r': 1.0,
            'sd_mult': 1.0,
            'imb_thresh': 0.025,
            'smart_dom_exit': False
        },
        'metrics': {
            'trades': 13,
            'win_rate': 53.8,
            'net_pnl_usd': 28.03,
            'profit_factor': 1.87,
            'max_dd_usd': 16.20,
            'daily_win_rate_pct': 80.0,
            'daily_pnl': {
                '2026-11-02': 1.39,
                '2026-11-03': 12.13,
                '2026-11-04': 12.11,
                '2026-11-05': 7.79,
                '2026-11-06': -5.39
            }
        }
    }
}

# Aggregate Portfolio
portfolio_pnl = defaultdict(float)
total_trades = 0
total_wins = 0

for sym, data in champions.items():
    m = data['metrics']
    total_trades += m['trades']
    total_wins += int(m['trades'] * m['win_rate'] / 100.0)
    for d, p in m['daily_pnl'].items():
        portfolio_pnl[d] += p

tot_days = len(portfolio_pnl)
pos_days = sum(1 for p in portfolio_pnl.values() if p > 0)
ens_daily_wr = (pos_days / tot_days * 100.0) if tot_days > 0 else 0.0
total_net = sum(portfolio_pnl.values())

print("="*80)
print("🚀 MASTER AUTONOMOUS MULTI-ASSET ENSEMBLE RESULTS")
print("="*80)
print(f"• Total Portfolio Net Profit: +${total_net:.2f} USD")
print(f"• Total Executed Trades:      {total_trades} trades ({total_wins} Wins / {total_trades - total_wins} Losses)")
print(f"• Ensemble Win Rate:          {total_wins / total_trades * 100:.1f}%")
print(f"• DAILY WIN RATE:             {pos_days}/{tot_days} = {ens_daily_wr:.1f}% GREEN DAYS!")
print("\n📅 Daily Breakdown:")
for d in sorted(portfolio_pnl.keys()):
    p = portfolio_pnl[d]
    icon = "✅ +" if p > 0 else "❌ -"
    print(f"  {d}: {icon}${abs(p):>6.2f} USD")

# Save master autonomous output
output = {
    'synthesized_at_utc': datetime.utcnow().isoformat(),
    'portfolio_summary': {
        'net_profit_usd': round(total_net, 2),
        'total_trades': total_trades,
        'win_rate_pct': round(total_wins / total_trades * 100.0, 1),
        'daily_win_rate_pct': round(ens_daily_wr, 1),
        'positive_days': pos_days,
        'total_days': tot_days,
        'daily_pnl': {k: round(v, 2) for k, v in sorted(portfolio_pnl.items())}
    },
    'champions': champions
}

out_file = os.path.join(DOCS_DATA_DIR, 'autonomous_champions.json')
with open(out_file, 'w', encoding='utf-8') as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print(f"\nSaved master results to {out_file}!")
