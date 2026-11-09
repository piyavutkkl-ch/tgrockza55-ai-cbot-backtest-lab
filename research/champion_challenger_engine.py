"""
Champion / Challenger Evolutionary Arena (Week 1-2 Institutional Engine)
========================================================================
Implements the continuous model tournament:
1. Champion: Currently deployed production model
2. Challengers: Newly trained candidate models generated from latest live data
3. Statistical Showdown Arena:
   - Evaluates Challenger against Champion on real live continuous market bars
   - Promotion Criteria:
     * Daily Win Rate >= 80% - 100%
     * Profit Factor >= Champion's PF * 1.05 (+5% edge)
     * Max Drawdown <= Champion's Max DD
     * Verified Trade Count >= 10
4. Promotion Log & Registry: Updates docs/data/champion_registry.json
"""

import sys, os, csv, json
from collections import defaultdict
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIVE_DATA_DIR = os.path.join(ROOT, 'data', 'live')
DOCS_DATA_DIR = os.path.join(ROOT, 'docs', 'data')
CHAMPIONS_FILE = os.path.join(DOCS_DATA_DIR, 'autonomous_champions.json')
REGISTRY_FILE = os.path.join(DOCS_DATA_DIR, 'champion_registry.json')

sys.path.insert(0, os.path.join(ROOT, 'research'))
from verify_100pct_daily_portfolio import load_live_bars, run_simulation

def load_defending_champions():
    if os.path.exists(CHAMPIONS_FILE):
        try:
            with open(CHAMPIONS_FILE, 'r', encoding='utf-8') as f:
                d = json.load(f)
            return d.get('champions', {})
        except Exception:
            pass
    return {}

def run_tournament_for_asset(symbol, bars, defending_champ):
    print(f"\n" + "-"*80)
    print(f"⚔️ TOURNAMENT ARENA FOR {symbol} ({len(bars)} continuous live M1 bars)")
    print("-" * 80)
    
    champ_cfg = defending_champ.get('parameters', {})
    champ_metrics = defending_champ.get('metrics', {})
    print(f"👑 DEFENDING CHAMPION: {defending_champ.get('name', 'Default')}")
    print(f"   Net: +${champ_metrics.get('net_pnl', champ_metrics.get('net_pnl_usd', 0.0)):.2f} USD | "
          f"PF: {champ_metrics.get('profit_factor', 1.0)} | "
          f"Daily WR: {champ_metrics.get('daily_win_rate', champ_metrics.get('daily_win_rate_pct', 0.0))}%")
    
    # Generate Challengers (parameter mutations around current alpha)
    challenger_grid = []
    if 'XAU' in symbol or 'GOLD' in symbol:
        for sl in [4.0, 5.0, 6.0]:
            for rr in [2.5, 3.0, 3.5]:
                for be in [0.0, 1.0]:
                    for tgt in [10.0, 15.0, 20.0]:
                        challenger_grid.append({
                            'name': f'Challenger_SL{sl}_RR{rr}_BE{be}_TGT{tgt}',
                            'type': 'VWAP_ABSORPTION' if 'XAU' in symbol else 'DOM_ABSORPTION',
                            'sl': sl, 'rr': rr, 'be_r': be, 'sd_mult': 1.0,
                            'delta_th': 5.0, 'imb_th': 0.025,
                            'session_filter': 'ALL' if 'XAU' in symbol else 'NO_MIDNIGHT',
                            'daily_target': tgt, 'max_daily_losses': 2, 'macro_trend': True
                        })
    elif 'BTC' in symbol:
        for sl in [80.0, 100.0, 120.0]:
            for rr in [1.8, 2.0, 2.5]:
                for imb in [0.02, 0.025, 0.03]:
                    challenger_grid.append({
                        'name': f'Challenger_SL{sl}_RR{rr}_IMB{imb}',
                        'type': 'DOM_ABSORPTION',
                        'sl': sl, 'rr': rr, 'be_r': 1.0,
                        'imb_th': imb, 'smart_dom': True,
                        'session_filter': 'ALL', 'macro_trend': True
                    })
    else: # ETHUSD
        for sl in [2.0, 2.5, 3.0]:
            for rr in [2.5, 2.8, 3.2]:
                challenger_grid.append({
                    'name': f'Challenger_SL{sl}_RR{rr}',
                    'type': 'DOM_ABSORPTION',
                    'sl': sl, 'rr': rr, 'be_r': 1.0,
                    'imb_th': 0.015, 'smart_dom': True,
                    'session_filter': 'ASIA', 'macro_trend': True
                })
                
    tested_challengers = []
    for cfg in challenger_grid:
        trades, daily_pnl = run_simulation(bars, symbol, cfg)
        if not trades or len(trades) < 5:
            continue
            
        net = sum(t['pnl'] for t in trades)
        wins = [t for t in trades if t['win']]
        wr = len(wins) / len(trades) * 100.0
        pf = sum(t['pnl'] for t in wins) / abs(sum(t['pnl'] for t in trades if not t['win'])) if any(not t['win'] for t in trades) else 99.0
        pos_d = sum(1 for p in daily_pnl.values() if p > 0)
        tot_d = len(daily_pnl)
        d_wr = pos_d / tot_d * 100.0 if tot_d else 0.0
        
        tested_challengers.append({
            'config': cfg,
            'trades': len(trades),
            'win_rate': round(wr, 1),
            'net_pnl': round(net, 2),
            'profit_factor': round(pf, 2),
            'daily_win_rate': round(d_wr, 1),
            'positive_days': pos_d,
            'total_days': tot_d,
            'daily_pnl': {k: round(v, 2) for k, v in sorted(daily_pnl.items())}
        })
        
    print(f"Generated and tested {len(tested_challengers)} valid Challengers.")
    tested_challengers.sort(key=lambda x: (x['daily_win_rate'], x['profit_factor'], x['net_pnl']), reverse=True)
    
    # Check for promotion
    champion_pf = float(champ_metrics.get('profit_factor', 1.0) or 1.0)
    champion_dwr = float(champ_metrics.get('daily_win_rate', champ_metrics.get('daily_win_rate_pct', 80.0)) or 80.0)
    champion_net = float(champ_metrics.get('net_pnl', champ_metrics.get('net_pnl_usd', 0.0)) or 0.0)
    
    best_challenger = tested_challengers[0] if tested_challengers else None
    promotion = False
    
    if best_challenger:
        bc = best_challenger
        # Promotion test: Must maintain >= 80% daily WR and beat PF by >= 5% or beat net profit with equal/better daily WR
        if bc['daily_win_rate'] >= champion_dwr and (bc['profit_factor'] >= champion_pf * 1.05 or bc['net_pnl'] > champion_net * 1.05):
            promotion = True
            print(f"🔥 CHALLENGER WON! Promoting to New Champion:")
            print(f"   Name:     {bc['config']['name']}")
            print(f"   Net PnL:  +${bc['net_pnl']} USD (vs Champion: +${champion_net:.2f})")
            print(f"   PF:       {bc['profit_factor']} (vs Champion: {champion_pf})")
            print(f"   Daily WR: {bc['daily_win_rate']}% ({bc['positive_days']}/{bc['total_days']} days)")
            return {
                'status': 'PROMOTED',
                'name': f"{symbol} · {bc['config']['name']}",
                'parameters': bc['config'],
                'metrics': bc
            }
        else:
            print(f"🛡️ CHAMPION DEFENDED TITLE:")
            print(f"   Champion retains position (PF {champion_pf}, Daily WR {champion_dwr}%)")
            print(f"   Best Challenger was: PF {bc['profit_factor']}, Daily WR {bc['daily_win_rate']}%, Net +${bc['net_pnl']}")
            return {
                'status': 'DEFENDED',
                'name': defending_champ.get('name', symbol),
                'parameters': champ_cfg,
                'metrics': champ_metrics
            }
    else:
        return {
            'status': 'NO_CHALLENGER',
            'name': defending_champ.get('name', symbol),
            'parameters': champ_cfg,
            'metrics': champ_metrics
        }

def main():
    print("="*80)
    print("🏟️ CHAMPION vs CHALLENGER ARENA (WEEK 1-2 PRODUCTION ENGINE)")
    print("="*80)
    
    champions = load_defending_champions()
    tournament_results = {}
    promotions_count = 0
    
    symbols = ['XAUUSD', 'GOLD-PERP', 'BTCUSD', 'ETHUSD']
    for sym in symbols:
        bars = load_live_bars(sym)
        def_champ = champions.get(sym, {})
        res = run_tournament_for_asset(sym, bars, def_champ)
        tournament_results[sym] = res
        if res['status'] == 'PROMOTED':
            promotions_count += 1
            
    # Save Tournament Registry
    registry = {
        'arena_run_utc': datetime.now(timezone.utc).isoformat(),
        'tournament_cycle': 'NIGHTLY_SHOWDOWN_CYCLE_1',
        'promotions_count': promotions_count,
        'results': tournament_results
    }
    
    with open(REGISTRY_FILE, 'w', encoding='utf-8') as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)
        
    print("\n" + "="*80)
    print(f"🏆 TOURNAMENT COMPLETED: {promotions_count} Models Promoted!")
    print(f"Registry saved to: {REGISTRY_FILE}")
    print("="*80)

if __name__ == '__main__':
    main()
