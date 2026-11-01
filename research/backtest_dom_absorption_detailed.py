import sys
import os
import glob
import csv

sys.stdout.reconfigure(encoding='utf-8')
from research.analyze_overnight_dom_flow import load_symbol_data

def run_detailed_backtest(symbol, lookback, imb_thresh, tp_usd, sl_usd, risk_rr, trade_size):
    data = load_symbol_data(symbol)
    if not data:
        print(f"No data found for {symbol}")
        return

    print("=" * 75)
    print(f"DETAILED BACKTEST REPORT: {symbol} (DOM_ABSORPTION STRATEGY)")
    print("=" * 75)
    print(f"Dataset Span:       {data[0]['time']} to {data[-1]['time']} ({len(data)} minutes / ~{len(data)/60:.1f} hours)")
    print(f"Starting Capital:   $100.00 USD")
    print(f"Parameters:         Lookback={lookback}m, ImbalanceThresh={imb_thresh}, SL=${sl_usd:.2f}, TP=${tp_usd:.2f} (RR {risk_rr:.1f}:1)")
    print(f"Position Size:      {trade_size} units (Single Position Only)")
    print("-" * 75)

    balance = 100.0
    peak_balance = 100.0
    max_drawdown_usd = 0.0
    max_drawdown_pct = 0.0

    trades = []
    i = lookback

    while i < len(data) - 20:
        window_high = max(d['high'] for d in data[i-lookback:i])
        window_low = min(d['low'] for d in data[i-lookback:i])
        curr = data[i]
        
        tol = (window_high - window_low) * 0.08
        current_bid = curr['close']
        current_ask = curr['close']
        imbalance = curr['imbalance']
        
        side = None
        trigger_reason = ""

        # ขา SELL: ราคาแตะโซน High + Ask Wall (Negative Imbalance)
        if current_bid >= window_high - tol and imbalance <= -imb_thresh:
            side = 'SELL'
            trigger_reason = f"Touched High (${window_high:.2f}) + Ask Wall Imb ({imbalance:+.3f})"
        # ขา BUY: ราคาแตะโซน Low + Bid Wall (Positive Imbalance)
        elif current_ask <= window_low + tol and imbalance >= imb_thresh:
            side = 'BUY'
            trigger_reason = f"Touched Low (${window_low:.2f}) + Bid Wall Imb ({imbalance:+.3f})"

        if side:
            entry_time = curr['time']
            entry_price = curr['close']
            spread_usd = curr['spreadAvg'] * (0.1 if 'BTC' in symbol else 0.01)
            
            exit_time = None
            exit_price = None
            exit_reason = None
            gross = 0.0
            exit_idx = i + 1

            for j in range(i + 1, min(i + 40, len(data))):
                p = data[j]['close']
                d = (p - entry_price) if side == 'BUY' else (entry_price - p)
                
                # 1. Take Profit
                if d >= tp_usd:
                    gross = tp_usd
                    exit_price = (entry_price + tp_usd) if side == 'BUY' else (entry_price - tp_usd)
                    exit_reason = "Take Profit (TP Hit)"
                    exit_time = data[j]['time']
                    exit_idx = j
                    break
                    
                # 2. Stop Loss
                if d <= -sl_usd:
                    gross = -sl_usd
                    exit_price = (entry_price - sl_usd) if side == 'BUY' else (entry_price + sl_usd)
                    exit_reason = "Stop Loss (SL Hit)"
                    exit_time = data[j]['time']
                    exit_idx = j
                    break

                # 3. Smart DOM Exit: หากกำไรเกิน 50% แล้วเจอกำแพงฝั่งตรงข้าม
                if d >= tp_usd * 0.5:
                    if side == 'BUY' and data[j]['imbalance'] <= -(imb_thresh * 1.5):
                        gross = d
                        exit_price = p
                        exit_reason = "Smart DOM Exit (Opposite Ask Wall)"
                        exit_time = data[j]['time']
                        exit_idx = j
                        break
                    elif side == 'SELL' and data[j]['imbalance'] >= (imb_thresh * 1.5):
                        gross = d
                        exit_price = p
                        exit_reason = "Smart DOM Exit (Opposite Bid Wall)"
                        exit_time = data[j]['time']
                        exit_idx = j
                        break
            else:
                gross = d
                exit_price = data[min(i + 40, len(data)) - 1]['close']
                exit_reason = "Time Horizon Exit (40m)"
                exit_time = data[min(i + 40, len(data)) - 1]['time']
                exit_idx = min(i + 40, len(data)) - 1

            # Calculate Net PnL after spread
            pnl = (gross - spread_usd) * trade_size
            balance += pnl
            
            if balance > peak_balance:
                peak_balance = balance
            dd_usd = peak_balance - balance
            dd_pct = (dd_usd / peak_balance) * 100.0 if peak_balance > 0 else 0.0
            if dd_usd > max_drawdown_usd:
                max_drawdown_usd = dd_usd
                max_drawdown_pct = dd_pct

            trade_record = {
                'id': len(trades) + 1,
                'entry_time': entry_time,
                'exit_time': exit_time,
                'side': side,
                'entry_price': entry_price,
                'exit_price': exit_price,
                'trigger': trigger_reason,
                'exit_reason': exit_reason,
                'pnl': pnl,
                'balance': balance,
                'win': pnl > 0
            }
            trades.append(trade_record)
            i = exit_idx + 1 # wait until position closes
        else:
            i += 1

    wins = [t for t in trades if t['pnl'] > 0]
    losses = [t for t in trades if t['pnl'] <= 0]
    win_rate = (len(wins) / len(trades) * 100.0) if trades else 0.0
    gross_win = sum(t['pnl'] for t in wins)
    gross_loss = abs(sum(t['pnl'] for t in losses))
    net_pnl = sum(t['pnl'] for t in trades)
    pf = (gross_win / gross_loss) if gross_loss > 0 else 999.0

    print(f"{'#':<3} | {'Entry Time':<16} | {'Side':<4} | {'Entry':<9} | {'Exit':<9} | {'Net PnL':<10} | {'Balance':<9} | {'Exit Reason'}")
    print("-" * 75)
    for t in trades:
        pnl_str = f"{t['pnl']:+.2f} USD"
        print(f"{t['id']:<3} | {t['entry_time']:<16} | {t['side']:<4} | {t['entry_price']:<9.2f} | {t['exit_price']:<9.2f} | {pnl_str:<10} | ${t['balance']:<8.2f} | {t['exit_reason']}")

    print("-" * 75)
    print("BACKTEST SUMMARY PERFORMANCE METRICS:")
    print(f"• Total Trades:         {len(trades)}")
    print(f"• Winning Trades:       {len(wins)} ({win_rate:.1f}%)")
    print(f"• Losing Trades:        {len(losses)} ({100.0 - win_rate:.1f}%)")
    print(f"• Gross Profit:         +${gross_win:.2f} USD")
    print(f"• Gross Loss:           -${gross_loss:.2f} USD")
    print(f"• Net Profit:           +${net_pnl:.2f} USD (+{net_pnl:.1f}% on $100 capital)")
    print(f"• Profit Factor (PF):   {pf:.2f}")
    print(f"• Final Balance:        ${balance:.2f} USD")
    print(f"• Max Drawdown:         ${max_drawdown_usd:.2f} USD ({max_drawdown_pct:.1f}%)")
    print("=" * 75)

if __name__ == '__main__':
    # 1. Backtest BTCUSD
    run_detailed_backtest('BTCUSD', lookback=15, imb_thresh=0.03, tp_usd=50.0, sl_usd=25.0, risk_rr=2.0, trade_size=0.05)
    print("\n" * 2)
    # 2. Backtest ETHUSD
    run_detailed_backtest('ETHUSD', lookback=20, imb_thresh=0.03, tp_usd=3.5, sl_usd=1.0, risk_rr=3.5, trade_size=1.0)
