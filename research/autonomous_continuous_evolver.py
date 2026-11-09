"""
Autonomous Multi-Asset Continuous Evolution Daemon
===================================================
Develops, tests, and evolves champion bots for each asset one-by-one in a continuous loop:
- XAUUSD (Gold Spot)
- BTCUSD (Bitcoin)
- ETHUSD (Ethereum)
- GOLD-PERP (Gold Perpetual)

Fitness Objective:
1. Daily Profitability: Win Rate on daily closes >= 80% - 100%
2. Profit Factor >= 1.5 - 2.5+
3. Minimal Drawdown (< $15 USD on 0.01 lot)
4. Full Cost Accounting (Pepperstone Spreads + Slippage + Commission)
"""

import sys, os, csv, json, math
from collections import defaultdict
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIVE_DATA_DIR = os.path.join(ROOT, 'data', 'live')
DOCS_DATA_DIR = os.path.join(ROOT, 'docs', 'data')

def load_asset_data(symbol):
    min_file = os.path.join(LIVE_DATA_DIR, symbol, 'min-2026-11.csv')
    flow_file = os.path.join(LIVE_DATA_DIR, symbol, 'flow-2026-11.csv')
    
    if not os.path.exists(min_file):
        return []
        
    flow_map = {}
    if os.path.exists(flow_file):
        with open(flow_file, 'r', encoding='utf-8', errors='replace') as fp:
            for r in csv.DictReader(fp):
                flow_map[r['time']] = r
                
    bars = []
    with open(min_file, 'r', encoding='utf-8', errors='replace') as fp:
        for r in csv.DictReader(fp):
            t = r['time']
            fl = flow_map.get(t, {})
            try:
                c = float(r['close'])
                o = float(r['open'])
                h = float(r['high'])
                l = float(r['low'])
                sp = float(r.get('spreadAvg', 0.15) or 0.15)
                imb = float(r.get('imbalance', 0) or 0)
                delta = float(fl.get('delta', 0) or 0)
                cvd = float(fl.get('cvd', 0) or 0)
                vwap = float(fl.get('vwapDay', 0) or fl.get('vwapSession', 0) or c)
                sd = float(fl.get('sdDay', 0) or 3.5)
                if sd <= 0: sd = 3.5
                
                next_imp = r.get('nextImpact', '')
                min_to_next = float(r.get('minToNext', 999) or 999)
                last_imp = r.get('lastImpact', '')
                min_since_last = float(r.get('minSinceLast', 999) or 999)
                
                day = t.split()[0]
                hour = int(t.split()[1].split(':')[0]) if len(t.split()) > 1 else 0
                
                bars.append({
                    'time': t,
                    'day': day,
                    'hour': hour,
                    'open': o, 'high': h, 'low': l, 'close': c,
                    'range': max(h - l, 0.01),
                    'spread': sp,
                    'imbalance': imb,
                    'delta': delta,
                    'cvd': cvd,
                    'vwap': vwap,
                    'sd': sd,
                    'next_impact': next_imp,
                    'min_to_next': min_to_next,
                    'last_impact': last_imp,
                    'min_since_last': min_since_last
                })
            except Exception:
                continue
                
    # Precompute rolling metrics: EMA 50, EMA 200, ATR 14, 15-bar Extrema
    n = len(bars)
    if n > 0:
        closes = [b['close'] for b in bars]
        def calc_ema(vals, period):
            ema = [vals[0]]
            k = 2.0 / (period + 1.0)
            for v in vals[1:]:
                ema.append(v * k + ema[-1] * (1.0 - k))
            return ema
        ema50 = calc_ema(closes, 50)
        ema200 = calc_ema(closes, 200)
        
        atr = [bars[i]['range'] for i in range(n)]
        for i in range(14, n):
            atr[i] = sum(bars[j]['range'] for j in range(i-13, i+1)) / 14.0
            
        hh_15 = [bars[i]['high'] for i in range(n)]
        ll_15 = [bars[i]['low'] for i in range(n)]
        for i in range(15, n):
            hh_15[i] = max(bars[j]['high'] for j in range(i-15, i))
            ll_15[i] = min(bars[j]['low'] for j in range(i-15, i))
            
        for i in range(n):
            bars[i]['ema50'] = ema50[i]
            bars[i]['ema200'] = ema200[i]
            bars[i]['atr'] = atr[i]
            bars[i]['hh_15'] = hh_15[i]
            bars[i]['ll_15'] = ll_15[i]
            
    return bars

def evaluate_simulation(bars, symbol, cfg):
    # Dynamic lot multiplier & empirical trading friction per asset
    if 'XAU' in symbol:
        lot_multiplier = 1.0
        comm = 0.07
        spread_max = 0.25
    elif 'GOLD' in symbol:
        lot_multiplier = 1.0
        comm = 0.05
        spread_max = 2.2
    elif 'BTC' in symbol:
        lot_multiplier = 0.01
        comm = 0.0
        spread_max = 35.0
    else: # ETH
        lot_multiplier = 0.01
        comm = 0.0
        spread_max = 3.5
        
    sl_dist = cfg['sl']
    rr = cfg['rr']
    tp_dist = sl_dist * rr
    be_r = cfg.get('be_r', 1.0)
    sd_mult = cfg.get('sd_mult', 1.0)
    delta_th = cfg.get('delta_th', 5.0)
    imb_th = cfg.get('imb_th', 0.02)
    session_filter = cfg.get('session_filter', 'ALL')
    strat_type = cfg['type']
    smart_dom_exit = cfg.get('smart_dom_exit', False)
    macro_trend = cfg.get('macro_trend', True)
    
    trades = []
    equity = 100.0
    pos = None
    n = len(bars)
    
    buy_cooldown = -1
    sell_cooldown = -1
    consec_buy_loss = 0
    consec_sell_loss = 0
    
    for i in range(50, n):
        curr = bars[i]
        c = curr['close']
        h = curr['high']
        l = curr['low']
        sp = curr['spread']
        vwap = curr['vwap']
        sd = curr['sd']
        delta = curr['delta']
        imb = curr['imbalance']
        hour = curr['hour']
        atr = curr['atr']
        hh = curr['hh_15']
        ll = curr['ll_15']
        rng = max(hh - ll, atr)
        
        # 1. Manage Active Position
        if pos is not None:
            side = pos['side']
            entry = pos['entry']
            
            # Breakeven lock
            if be_r > 0 and not pos['be_locked']:
                if side == 'BUY' and (h - entry) >= (sl_dist * be_r):
                    pos['sl'] = entry + sp + 0.05
                    pos['be_locked'] = True
                elif side == 'SELL' and (entry - l) >= (sl_dist * be_r):
                    pos['sl'] = entry - sp - 0.05
                    pos['be_locked'] = True
                    
            exit_trade = False
            exit_price = c
            reason = "EXIT"
            
            # Smart DOM early exit if opposite wall appears while in profit
            if smart_dom_exit:
                if side == 'BUY' and (c - entry) >= (sl_dist * 0.4) and imb < -0.04:
                    exit_trade = True
                    exit_price = c
                    reason = "DOM_EXIT"
                elif side == 'SELL' and (entry - c) >= (sl_dist * 0.4) and imb > 0.04:
                    exit_trade = True
                    exit_price = c + sp
                    reason = "DOM_EXIT"
                    
            if not exit_trade:
                if side == 'BUY':
                    if l <= pos['sl']:
                        exit_trade = True
                        exit_price = pos['sl']
                        reason = "BE" if pos['be_locked'] else "SL"
                    elif h >= pos['tp']:
                        exit_trade = True
                        exit_price = pos['tp']
                        reason = "TP"
                else: # SELL
                    if h >= pos['sl']:
                        exit_trade = True
                        exit_price = pos['sl']
                        reason = "BE" if pos['be_locked'] else "SL"
                    elif l <= pos['tp']:
                        exit_trade = True
                        exit_price = pos['tp']
                        reason = "TP"
                        
            if exit_trade:
                pnl = (exit_price - entry) * lot_multiplier if side == 'BUY' else (entry - exit_price) * lot_multiplier
                pnl -= (sp * lot_multiplier + comm)
                equity += pnl
                
                if reason == "SL":
                    if side == 'BUY':
                        consec_buy_loss += 1
                        if consec_buy_loss >= 2: buy_cooldown = i + 20
                    else:
                        consec_sell_loss += 1
                        if consec_sell_loss >= 2: sell_cooldown = i + 20
                elif pnl > 0:
                    if side == 'BUY': consec_buy_loss = 0
                    else: consec_sell_loss = 0
                    
                trades.append({
                    'id': len(trades) + 1,
                    'day': pos['day'],
                    'side': side,
                    'entry_time': pos['time'],
                    'exit_time': curr['time'],
                    'entry': round(entry, 2),
                    'exit': round(exit_price, 2),
                    'pnl': round(pnl, 2),
                    'win': pnl > 0,
                    'reason': reason
                })
                pos = None
                continue
                
        # 2. Check News Void Gate
        if curr['min_to_next'] <= 30 and curr['next_impact'] in ['HIGH', 'EXTREME']:
            continue
        if curr['min_since_last'] <= 60 and curr['last_impact'] in ['HIGH', 'EXTREME']:
            continue
            
        # 3. Spread Shield
        if sp > spread_max:
            continue
            
        # 4. Session Filter
        if session_filter == 'ASIA' and not (0 <= hour < 7):
            continue
        elif session_filter == 'LONDON' and not (7 <= hour < 13):
            continue
        elif session_filter == 'NY' and not (13 <= hour < 21):
            continue
            
        # 5. Evaluate Signal
        buy_sig = False
        sell_sig = False
        
        lower_band = vwap - (sd * sd_mult)
        upper_band = vwap + (sd * sd_mult)
        
        if strat_type == 'VWAP_ABSORPTION':
            # Mean reversion at VWAP SD stretch with Volume Delta absorption
            buy_sig = (l <= lower_band) and (delta >= delta_th)
            sell_sig = (h >= upper_band) and (delta <= -delta_th)
            
        elif strat_type == 'DOM_ABSORPTION':
            # Order Book Imbalance Wall at Range Extrema
            range_tol = cfg.get('range_tol', 0.15)
            buy_sig = (c <= ll + rng * range_tol) and (imb >= imb_th)
            sell_sig = (c >= hh - rng * range_tol) and (imb <= -imb_th)
            
        elif strat_type == 'FOUR_PILLAR_ENSEMBLE':
            # Confluence of VWAP stretch + DOM Imbalance + Delta Absorption
            buy_sig = (l <= lower_band or c <= ll + rng * 0.15) and (imb >= imb_th) and (delta >= 0)
            sell_sig = (h >= upper_band or c >= hh - rng * 0.15) and (imb <= -imb_th) and (delta <= 0)
            
        # Macro Trend Shield
        if macro_trend:
            if c > curr['ema50'] and curr['ema50'] > curr['ema200']:
                sell_sig = False
            elif c < curr['ema50'] and curr['ema50'] < curr['ema200']:
                buy_sig = False
                
        if buy_sig and i >= buy_cooldown:
            pos = {
                'side': 'BUY',
                'entry': c + sp,
                'sl': (c + sp) - sl_dist,
                'tp': (c + sp) + tp_dist,
                'be_locked': False,
                'time': curr['time'],
                'day': curr['day']
            }
        elif sell_sig and i >= sell_cooldown:
            pos = {
                'side': 'SELL',
                'entry': c,
                'sl': c + sl_dist,
                'tp': c - tp_dist,
                'be_locked': False,
                'time': curr['time'],
                'day': curr['day']
            }
            
    if not trades:
        return None
        
    wins = [t['pnl'] for t in trades if t['win']]
    losses = [t['pnl'] for t in trades if not t['win']]
    total_net = sum(t['pnl'] for t in trades)
    pf = sum(wins) / abs(sum(losses)) if losses and sum(losses) != 0 else (99.0 if wins else 0.0)
    wr = len(wins) / len(trades) * 100.0
    
    daily_pnl = defaultdict(float)
    daily_counts = defaultdict(int)
    for t in trades:
        daily_pnl[t['day']] += t['pnl']
        daily_counts[t['day']] += 1
        
    pos_days = sum(1 for d, p in daily_pnl.items() if p > 0)
    tot_days = len(daily_pnl)
    daily_wr = (pos_days / tot_days * 100.0) if tot_days > 0 else 0.0
    
    peak = 0.0
    max_dd = 0.0
    cum = 0.0
    for t in trades:
        cum += t['pnl']
        if cum > peak: peak = cum
        dd = peak - cum
        if dd > max_dd: max_dd = dd
        
    # Fitness Objective: High Daily Win Rate (>=80%) + High Profit Factor + Substantial Net Profit - Low DD
    fitness = (daily_wr * 1.0) + (min(pf, 5.0) * 20.0) + (total_net * 2.0) - (max_dd * 1.0)
    if total_net <= 0:
        fitness -= 500
    if daily_wr < 60.0:
        fitness -= 100
        
    return {
        'trades': len(trades),
        'wins': len(wins),
        'losses': len(losses),
        'win_rate': round(wr, 1),
        'net_pnl': round(total_net, 2),
        'profit_factor': round(pf, 2),
        'max_dd': round(max_dd, 2),
        'active_days': tot_days,
        'positive_days': pos_days,
        'daily_win_rate': round(daily_wr, 1),
        'daily_pnl': {k: round(v, 2) for k, v in sorted(daily_pnl.items())},
        'daily_counts': dict(daily_counts),
        'fitness': round(fitness, 2),
        'trades_sample': trades
    }

def evolve_asset(symbol, bars):
    print(f"\n" + "="*80, flush=True)
    print(f"🔥 EVOLVING ASSET: {symbol} ({len(bars)} continuous live M1 bars)", flush=True)
    print("="*80, flush=True)
    
    param_grid = []
    
    if 'XAU' in symbol or 'GOLD' in symbol:
        # 1. VWAP Absorption Focus
        for sl in [3.0, 4.0, 5.0]:
            for rr in [2.0, 2.5, 3.0]:
                for be in [0.0, 1.0]:
                    for sd in [0.8, 1.0, 1.2]:
                        for d_th in [5.0, 10.0]:
                            param_grid.append({
                                'type': 'VWAP_ABSORPTION',
                                'sl': sl, 'rr': rr, 'be_r': be, 'sd_mult': sd,
                                'delta_th': d_th, 'imb_th': 0.02,
                                'session_filter': 'ALL', 'smart_dom_exit': False, 'macro_trend': True
                            })
        # 2. DOM Absorption Focus
        for sl in [3.0, 4.0, 5.0]:
            for rr in [2.0, 2.5, 3.0]:
                for be in [0.0, 1.0]:
                    for imb in [0.015, 0.025]:
                        for s_dom in [True, False]:
                            param_grid.append({
                                'type': 'DOM_ABSORPTION',
                                'sl': sl, 'rr': rr, 'be_r': be, 'sd_mult': 1.0,
                                'delta_th': 5.0, 'imb_th': imb,
                                'session_filter': 'ALL', 'smart_dom_exit': s_dom, 'macro_trend': True
                            })
    elif 'BTC' in symbol:
        # DOM Absorption Focus
        for sl in [60.0, 80.0, 100.0, 120.0]:
            for rr in [1.8, 2.2, 2.6]:
                for be in [0.0, 1.0]:
                    for imb in [0.015, 0.025, 0.035]:
                        for s_dom in [True, False]:
                            for sf in ['ALL', 'NY']:
                                param_grid.append({
                                    'type': 'DOM_ABSORPTION',
                                    'sl': sl, 'rr': rr, 'be_r': be, 'sd_mult': 1.5,
                                    'delta_th': 10.0, 'imb_th': imb,
                                    'session_filter': sf, 'smart_dom_exit': s_dom, 'macro_trend': True
                                })
        # Four Pillar Ensemble
        for sl in [80.0, 100.0]:
            for rr in [2.0, 2.5, 3.0]:
                for be in [0.0, 1.0]:
                    for sf in ['ALL', 'NY']:
                        param_grid.append({
                            'type': 'FOUR_PILLAR_ENSEMBLE',
                            'sl': sl, 'rr': rr, 'be_r': be, 'sd_mult': 1.5,
                            'delta_th': 10.0, 'imb_th': 0.02,
                            'session_filter': sf, 'smart_dom_exit': False, 'macro_trend': True
                        })
    else: # ETHUSD
        # DOM Absorption Focus
        for sl in [3.0, 4.0, 5.0, 6.0]:
            for rr in [2.0, 2.5, 2.8]:
                for be in [0.0, 1.0]:
                    for imb in [0.015, 0.025]:
                        for s_dom in [True, False]:
                            for sf in ['ASIA', 'ALL']:
                                param_grid.append({
                                    'type': 'DOM_ABSORPTION',
                                    'sl': sl, 'rr': rr, 'be_r': be, 'sd_mult': 1.5,
                                    'delta_th': 5.0, 'imb_th': imb,
                                    'session_filter': sf, 'smart_dom_exit': s_dom, 'macro_trend': True
                                })
                                
    all_results = []
    for cfg in param_grid:
        res = evaluate_simulation(bars, symbol, cfg)
        if res and res['trades'] >= 5:
            all_results.append({
                'config': cfg,
                'metrics': res,
                'fitness': res['fitness']
            })
            
    all_results.sort(key=lambda x: x['fitness'], reverse=True)
    print(f"Tested {len(param_grid)} parameter permutations. Survivors: {len(all_results)}", flush=True)
    
    if all_results:
        # Prioritize: Daily Win Rate >= 80%, PF >= 1.5, Net PnL > 0
        top_tier = [x for x in all_results if x['metrics']['daily_win_rate'] >= 75.0 and x['metrics']['net_pnl'] > 0]
        if not top_tier:
            top_tier = [x for x in all_results if x['metrics']['net_pnl'] > 0]
        if not top_tier:
            top_tier = all_results
            
        champ = sorted(top_tier, key=lambda x: (x['metrics']['daily_win_rate'], x['metrics']['profit_factor'], x['metrics']['net_pnl']), reverse=True)[0]
        m = champ['metrics']
        c = champ['config']
        print(f"\n🏆 CHAMPION DISCOVERED FOR {symbol}:", flush=True)
        print(f"  • Strategy Type:    {c['type']} (Session: {c['session_filter']})", flush=True)
        print(f"  • Parameters:       SL={c['sl']}, RR={c['rr']}, BE={c['be_r']}R, SD_Mult={c['sd_mult']}, IMB={c['imb_th']}, SmartDOM={c['smart_dom_exit']}", flush=True)
        print(f"  • Net Profit:       +${m['net_pnl']} USD", flush=True)
        print(f"  • Profit Factor:    {m['profit_factor']}", flush=True)
        print(f"  • Win Rate:         {m['win_rate']}% ({m['wins']}W / {m['losses']}L in {m['trades']} trades)", flush=True)
        print(f"  • Daily Win Rate:   {m['daily_win_rate']}% ({m['positive_days']}/{m['active_days']} days profitable)", flush=True)
        print(f"  • Max Drawdown:     ${m['max_dd']} USD", flush=True)
        print(f"  • Daily PnL:        {m['daily_pnl']}", flush=True)
        return champ
    else:
        print(f"No survivor for {symbol}", flush=True)
        return None

def main():
    print("="*80, flush=True)
    print("🚀 LAUNCHING AUTONOMOUS MULTI-ASSET QUANT EVOLUTION HARNESS", flush=True)
    print("="*80, flush=True)
    
    symbols = ['XAUUSD', 'BTCUSD', 'ETHUSD', 'GOLD-PERP']
    champions = {}
    
    for sym in symbols:
        bars = load_asset_data(sym)
        if not bars:
            print(f"Warning: No live data for {sym}", flush=True)
            continue
        champ = evolve_asset(sym, bars)
        if champ:
            champions[sym] = champ
            
    print("\n" + "="*80, flush=True)
    print("📊 MULTI-ASSET PORTFOLIO ENSEMBLE SUMMARY", flush=True)
    print("="*80, flush=True)
    
    portfolio_daily_pnl = defaultdict(float)
    portfolio_daily_counts = defaultdict(int)
    total_net = 0.0
    total_trades = 0
    total_wins = 0
    total_losses = 0
    
    all_trades = []
    for sym, ch in champions.items():
        m = ch['metrics']
        total_net += m['net_pnl']
        total_trades += m['trades']
        total_wins += m['wins']
        total_losses += m['losses']
        for d, pnl in m['daily_pnl'].items():
            portfolio_daily_pnl[d] += pnl
        for d, cnt in m['daily_counts'].items():
            portfolio_daily_counts[d] += cnt
        for t in ch['metrics'].get('trades_sample', []):
            all_trades.append({**t, 'symbol': sym})
            
    pos_days = sum(1 for d, p in portfolio_daily_pnl.items() if p > 0)
    tot_days = len(portfolio_daily_pnl)
    port_daily_wr = (pos_days / tot_days * 100.0) if tot_days > 0 else 0.0
    
    all_wins = [t['pnl'] for t in all_trades if t['win']]
    all_losses = [t['pnl'] for t in all_trades if not t['win']]
    port_pf = sum(all_wins) / abs(sum(all_losses)) if all_losses and sum(all_losses) != 0 else 99.0
    
    print(f"• Total Portfolio Net Profit: +${total_net:.2f} USD", flush=True)
    print(f"• Combined Win Rate:          {total_wins / total_trades * 100:.1f}% ({total_wins}W / {total_losses}L in {total_trades} trades)", flush=True)
    print(f"• Portfolio Profit Factor:     {port_pf:.2f}", flush=True)
    print(f"• Portfolio Daily Win Rate:    {port_daily_wr:.1f}% ({pos_days}/{tot_days} Days Green)", flush=True)
    print(f"• Daily Ensemble Breakdown:", flush=True)
    for d, p in sorted(portfolio_daily_pnl.items()):
        cnt = portfolio_daily_counts[d]
        icon = "✅ +" if p > 0 else "❌ -"
        print(f"    {d}: {icon}${abs(p):>6.2f} USD ({cnt:>2} trades)", flush=True)
        
    # Save to docs/data/autonomous_champions.json
    save_data = {
        'evolved_at_utc': datetime.utcnow().isoformat(),
        'portfolio_summary': {
            'net_profit_usd': round(total_net, 2),
            'total_trades': total_trades,
            'win_rate_pct': round(total_wins / total_trades * 100, 1),
            'profit_factor': round(port_pf, 2),
            'daily_win_rate_pct': round(port_daily_wr, 1),
            'positive_days': pos_days,
            'total_days': tot_days,
            'daily_pnl': {k: round(v, 2) for k, v in sorted(portfolio_daily_pnl.items())},
            'daily_counts': dict(portfolio_daily_counts)
        },
        'champions': {
            sym: {
                'config': ch['config'],
                'metrics': {k: v for k, v in ch['metrics'].items() if k != 'trades_sample'}
            } for sym, ch in champions.items()
        }
    }
    
    out_file = os.path.join(DOCS_DATA_DIR, 'autonomous_champions.json')
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(save_data, f, indent=2, ensure_ascii=False)
        
    print(f"\nSaved master evolution results to {out_file}!", flush=True)

if __name__ == '__main__':
    main()
