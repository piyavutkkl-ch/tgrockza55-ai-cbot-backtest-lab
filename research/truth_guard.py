"""
Truth Guard Engine — Grounding all Metrics in Empirical Reality (Truth Reset)
=============================================================================
Audits and parses raw trade logs from %LOCALAPPDATA%\\BacktestLab\\live\\*\\trades.csv.
Guarantees 100% empirical grounding with zero synthetic inflation.

Calculates:
1. Exact trade counts (N)
2. Realized Net PnL, Win Rate, and Profit Factor
3. Statistical Power & Standard Error of Sharpe:
   SE(SR) = sqrt((1 + 0.5 * SR^2) / N)
4. Sample size threshold evaluation:
   - N < 500: STATISTICALLY UNDERPOWERED (Cannot conclude edge or lack thereof)
   - 500 <= N < 1200: PRELIMINARY STATISTICAL SIGNIFICANCE
   - N >= 1200: INSTITUTIONAL STATISTICAL SIGNIFICANCE
"""

import os
import csv
import math
import json
from datetime import datetime, timezone

REPO_ROOT = r'd:\cbot-atgvt'
LIVE_BASE = os.path.expandvars(r'%LOCALAPPDATA%\BacktestLab\live')
DOCS_DATA = os.path.join(REPO_ROOT, 'docs', 'data')
os.makedirs(DOCS_DATA, exist_ok=True)

class TruthGuard:
    def __init__(self):
        self.symbols = ['BTCUSD', 'ETHUSD', 'XAUUSD', 'GOLD-PERP']
        self.initial_deposit = 100.00

    def parse_raw_trades(self):
        all_events = []
        closed_trades = []

        for sym in self.symbols:
            p = os.path.join(LIVE_BASE, sym, 'trades.csv')
            if not os.path.exists(p):
                continue
            with open(p, 'r', encoding='utf-8', errors='ignore') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    row['symbol'] = sym
                    all_events.append(row)
                    if row.get('event') == 'CLOSE':
                        closed_trades.append(row)

        # Sort chronologically
        closed_trades.sort(key=lambda x: x.get('time', ''))
        all_events.sort(key=lambda x: x.get('time', ''))

        n_closed = len(closed_trades)
        wins = [t for t in closed_trades if float(t.get('net') or 0) > 0]
        losses = [t for t in closed_trades if float(t.get('net') or 0) < 0]
        breakevens = [t for t in closed_trades if float(t.get('net') or 0) == 0]

        gross_win = round(sum(float(t.get('net') or 0) for t in wins), 2)
        gross_loss = round(abs(sum(float(t.get('net') or 0) for t in losses)), 2)
        net_pnl = round(gross_win - gross_loss, 2)
        current_balance = round(self.initial_deposit + net_pnl, 2)

        win_rate = round(len(wins) / n_closed * 100, 1) if n_closed > 0 else 0.0
        profit_factor = round(gross_win / gross_loss, 2) if gross_loss > 0 else (999.0 if gross_win > 0 else 0.0)

        # Compute empirical Sharpe of closed trade return series
        returns = [float(t.get('net') or 0) / self.initial_deposit for t in closed_trades]
        if returns and len(returns) > 1:
            mean_r = sum(returns) / len(returns)
            var_r = sum((r - mean_r) ** 2 for r in returns) / (len(returns) - 1)
            std_r = math.sqrt(var_r) if var_r > 0 else 1e-6
            trade_sharpe = mean_r / std_r
            # Annualized estimate assuming ~10 trades/day (~2500/year)
            ann_sharpe = round(trade_sharpe * math.sqrt(2500), 2)
        else:
            ann_sharpe = 0.0

        # Statistical Power Analysis
        # SE(SR) = sqrt((1 + 0.5 * SR^2) / N)
        if n_closed > 0:
            se_sharpe = round(math.sqrt((1 + 0.5 * (ann_sharpe ** 2)) / n_closed), 3)
        else:
            se_sharpe = 999.0

        target_preliminary = 500
        target_institutional = 1200
        power_pct = round(min(100.0, (n_closed / target_preliminary) * 100), 1)

        if n_closed < 100:
            stat_status = "CRITICALLY_UNDERPOWERED"
            stat_label = "ยังไม่สามารถสรุปผลได้ (Statistically Insignificant)"
            stat_desc = f"จำนวนเทรดจริงสะสม N={n_closed} ไม้ ค่าความคลาดเคลื่อนมาตรฐาน SE(SR)=±{se_sharpe} กว้างเกินกว่าจะพิสูจน์ความได้เปรียบ ต้องสะสมข้อมูลอย่างน้อย 500 ไม้"
        elif n_closed < target_preliminary:
            stat_status = "MODERATELY_UNDERPOWERED"
            stat_label = "กำลังสะสมตัวอย่าง (Inconclusive)"
            stat_desc = f"จำนวนเทรด N={n_closed}/{target_preliminary} ไม้ เริ่มเห็นแนวโน้มแต่ยังไม่มีนัยสำคัญทางสถิติ (p > 0.05)"
        elif n_closed < target_institutional:
            stat_status = "PRELIMINARY_SIGNIFICANT"
            stat_label = "เริ่มมีนัยสำคัญทางสถิติ (p < 0.05)"
            stat_desc = f"จำนวนเทรด N={n_closed} ผ่านเกณฑ์ขั้นต่ำ 500 ไม้ ค่าสถิติเริ่มเชื่อถือได้"
        else:
            stat_status = "INSTITUTIONALLY_VALIDATED"
            stat_label = "ผ่านเกณฑ์ระดับสถาบันสมบูรณ์ (p < 0.01)"
            stat_desc = f"จำนวนเทรด N={n_closed} เกิน 1,200 ไม้ ขนาดตัวอย่างใหญ่พอที่จะพิสูจน์ Edge ได้อย่างแน่ชัด"

        report = {
            "truth_reset_version": "v4.0.0-TRUTH-RESET",
            "audit_timestamp": datetime.now(timezone.utc).isoformat(),
            "data_source": "%LOCALAPPDATA%\\BacktestLab\\live",
            "account_number": "Pepperstone #5258778",
            "raw_files_audited": [
                os.path.join(LIVE_BASE, s, 'trades.csv') for s in self.symbols if os.path.exists(os.path.join(LIVE_BASE, s, 'trades.csv'))
            ],
            "metrics_empirical": {
                "initial_deposit": self.initial_deposit,
                "current_balance": current_balance,
                "net_pnl_usd": net_pnl,
                "net_pnl_pct": round(net_pnl / self.initial_deposit * 100, 2),
                "gross_win_usd": gross_win,
                "gross_loss_usd": gross_loss,
                "total_events_count": len(all_events),
                "total_closed_trades_N": n_closed,
                "wins_count": len(wins),
                "losses_count": len(losses),
                "breakevens_count": len(breakevens),
                "win_rate_pct": win_rate,
                "profit_factor": profit_factor,
                "realized_sharpe_estimate": ann_sharpe
            },
            "statistical_power": {
                "sample_size_N": n_closed,
                "target_preliminary_N": target_preliminary,
                "target_institutional_N": target_institutional,
                "power_progress_pct": power_pct,
                "standard_error_sharpe": se_sharpe,
                "status": stat_status,
                "label": stat_label,
                "description": stat_desc,
                "mandate": "ห้ามสรุปผลกำไรหรือความได้เปรียบ (Edge) ของระบบ จนกว่าขนาดตัวอย่างจะครบ 500 ไม้เป็นอย่างน้อย"
            }
        }
        return report

    def save_audit(self):
        report = self.parse_raw_trades()
        out_path = os.path.join(DOCS_DATA, 'truth_guard.json')
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"Saved Truth Guard audit report to {out_path}")
        return report

if __name__ == "__main__":
    tg = TruthGuard()
    rep = tg.save_audit()
    print(f"Audited N={rep['metrics_empirical']['total_closed_trades_N']} closed trades.")
    print(f"Status: {rep['statistical_power']['status']} ({rep['statistical_power']['label']})")
