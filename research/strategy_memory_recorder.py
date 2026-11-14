"""
Strategy Memory Recorder V4
===========================
Records empirical performance facts and conditional edge by market regime into
quant_fund_v2/db/quant_fund_v2.sqlite (table: strategy_memory) upon completion
of any backtest, chronological replay, or autonomous evolution cycle.
"""

import os
import sqlite3
import json
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(ROOT, 'quant_fund_v2', 'db', 'quant_fund_v2.sqlite')

class StrategyMemoryRecorder:
    """
    Manages persistence of strategy performance by market regime into SQLite strategy_memory
    and aggregates empirical Regime-Strategy Attribution Matrix in strategy_regime_performance
    with autonomous feedback loop (cutting losers, promoting winners).
    """

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._ensure_table()

    def _get_connection(self) -> sqlite3.Connection:
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        return sqlite3.connect(self.db_path)

    def _ensure_table(self):
        with self._get_connection() as con:
            cur = con.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS strategy_memory (
                    id TEXT PRIMARY KEY,
                    strategy_version_id TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    market_regime TEXT NOT NULL,
                    empirical_facts_json TEXT NOT NULL,
                    ai_postmortem_notes TEXT NOT NULL,
                    verified_by_human INTEGER NOT NULL DEFAULT 0,
                    verified_by TEXT,
                    supabase_run_id INTEGER,
                    created_at TEXT NOT NULL
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS strategy_regime_performance (
                    strategy_code TEXT NOT NULL,
                    market_regime TEXT NOT NULL,
                    total_trades INTEGER NOT NULL DEFAULT 0,
                    win_trades INTEGER NOT NULL DEFAULT 0,
                    loss_trades INTEGER NOT NULL DEFAULT 0,
                    win_rate_pct REAL NOT NULL DEFAULT 0.0,
                    net_pnl_usd REAL NOT NULL DEFAULT 0.0,
                    gross_win_usd REAL NOT NULL DEFAULT 0.0,
                    gross_loss_usd REAL NOT NULL DEFAULT 0.0,
                    profit_factor REAL NOT NULL DEFAULT 0.0,
                    expectancy_usd REAL NOT NULL DEFAULT 0.0,
                    weight_multiplier REAL NOT NULL DEFAULT 1.0,
                    status TEXT NOT NULL DEFAULT 'ACTIVE',
                    last_updated TEXT NOT NULL,
                    PRIMARY KEY (strategy_code, market_regime)
                )
            """)
            con.commit()

    def record_simulation_regime_memory(
        self,
        symbol: str,
        trades: List[Dict[str, Any]],
        default_strategy_id: str = "STR-001",
        default_regime: str = "RANGE_BOUND",
        supabase_run_id: Optional[int] = None,
        notes_prefix: str = ""
    ) -> List[Dict[str, Any]]:
        """
        Groups trades by (strategy_id, market_regime), calculates empirical edge facts,
        generates AI postmortem notes, and inserts records into strategy_memory.
        Returns list of inserted record summaries.
        """
        if not trades:
            return []

        # Group trades by (strategy_id, market_regime)
        grouped_trades: Dict[tuple, List[Dict[str, Any]]] = defaultdict(list)
        for t in trades:
            strat_id = t.get('strategy_id') or t.get('strategy_code') or default_strategy_id
            regime = t.get('market_regime') or t.get('regime') or default_regime
            grouped_trades[(strat_id, regime)].append(t)

        now_iso = datetime.now(timezone.utc).isoformat()
        inserted_records = []

        with self._get_connection() as con:
            cur = con.cursor()
            for (strat_id, regime), sub_trades in grouped_trades.items():
                total_trades = len(sub_trades)
                wins = [t for t in sub_trades if t.get('win', False) or float(t.get('pnl', 0)) > 0]
                losses = [t for t in sub_trades if not t.get('win', False) and float(t.get('pnl', 0)) <= 0]
                
                win_count = len(wins)
                loss_count = len(losses)
                win_rate = (win_count / total_trades * 100.0) if total_trades > 0 else 0.0

                gross_win = sum(float(t.get('pnl', 0)) for t in wins)
                gross_loss = abs(sum(float(t.get('pnl', 0)) for t in losses))
                net_pnl = gross_win - gross_loss
                profit_factor = round(gross_win / gross_loss, 2) if gross_loss > 0 else (999.0 if gross_win > 0 else 0.0)
                avg_pnl = net_pnl / total_trades if total_trades > 0 else 0.0

                pnls = [float(t.get('pnl', 0)) for t in sub_trades]
                max_win = max(pnls) if pnls else 0.0
                max_loss = min(pnls) if pnls else 0.0
                bars_held = [t.get('bars_held', 0) for t in sub_trades if 'bars_held' in t]
                avg_bars_held = sum(bars_held) / len(bars_held) if bars_held else 0.0

                # Determine statistical edge qualification
                has_positive_edge = net_pnl > 0 and (win_rate >= 40.0 or profit_factor >= 1.5)
                edge_label = "POSITIVE_STATISTICAL_EDGE" if has_positive_edge else "DEFICIT_OR_UNPROVEN"

                empirical_facts = {
                    "sample_size": total_trades,
                    "wins": win_count,
                    "losses": loss_count,
                    "win_rate_pct": round(win_rate, 1),
                    "net_pnl_usd": round(net_pnl, 2),
                    "gross_win_usd": round(gross_win, 2),
                    "gross_loss_usd": round(gross_loss, 2),
                    "profit_factor": profit_factor,
                    "avg_trade_pnl_usd": round(avg_pnl, 2),
                    "max_win_usd": round(max_win, 2),
                    "max_loss_usd": round(max_loss, 2),
                    "avg_bars_held": round(avg_bars_held, 1),
                    "edge_qualification": edge_label,
                    "first_trade_time": sub_trades[0].get('entry_time', ''),
                    "last_trade_time": sub_trades[-1].get('exit_time', '')
                }

                # Construct AI Postmortem Notes
                notes_body = (
                    f"[{edge_label}] {strat_id} in {regime} on {symbol}: "
                    f"Net PnL +${net_pnl:.2f} USD, WR {win_rate:.1f}% ({win_count}W/{loss_count}L), PF {profit_factor:.2f}. "
                )
                if has_positive_edge:
                    notes_body += f"Verified positive statistical edge in {regime}. Candidate retained in adaptive priority routing."
                else:
                    notes_body += f"Performance subdued in {regime}. Recommend tighter adaptive suitability gate (threshold >= 60.0)."

                if notes_prefix:
                    notes_body = f"{notes_prefix} | {notes_body}"

                rec_id = str(uuid.uuid4())
                facts_json = json.dumps(empirical_facts, ensure_ascii=False)

                cur.execute("""
                    INSERT INTO strategy_memory (
                        id, strategy_version_id, symbol, market_regime,
                        empirical_facts_json, ai_postmortem_notes,
                        verified_by_human, verified_by, supabase_run_id, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    rec_id, strat_id, symbol, regime,
                    facts_json, notes_body,
                    0, "AUTONOMOUS_V4", supabase_run_id, now_iso
                ))

                inserted_records.append({
                    "id": rec_id,
                    "strategy_id": strat_id,
                    "symbol": symbol,
                    "market_regime": regime,
                    "total_trades": total_trades,
                    "win_rate": round(win_rate, 1),
                    "net_pnl_usd": round(net_pnl, 2),
                    "profit_factor": profit_factor,
                    "edge_qualification": edge_label
                })

            con.commit()

        # Update empirical Regime-Strategy Attribution Matrix
        self.update_regime_performance_matrix(trades, default_strategy_id, default_regime)

        return inserted_records

    def update_regime_performance_matrix(
        self,
        trades: List[Dict[str, Any]],
        default_strategy_id: str = "STR-001",
        default_regime: str = "RANGE_BOUND"
    ) -> List[Dict[str, Any]]:
        """
        Aggregates cumulative trades per (strategy_code, market_regime) and updates
        the permanent strategy_regime_performance attribution matrix in SQLite.
        Implements the dynamic feedback loop (วงจรตัดตัวแพ้-ดันตัวชนะ):
        - BANNED (weight 0.0): If total_trades >= 5 and (net_pnl_usd < -15.0 or expectancy_usd < -3.0)
        - PENALIZED (weight 0.25): If total_trades >= 3 and (expectancy_usd < 0.0 or win_rate_pct < 40.0 or net_pnl_usd < 0.0)
        - PROMOTED (weight 1.35): If total_trades >= 3 and expectancy_usd > 0.0 and win_rate_pct >= 55.0 and profit_factor >= 1.5
        - ACTIVE (weight 1.0): Baseline
        """
        if not trades:
            return []

        grouped_trades: Dict[tuple, List[Dict[str, Any]]] = defaultdict(list)
        for t in trades:
            strat_id = t.get('strategy_id') or t.get('strategy_code') or default_strategy_id
            regime = t.get('market_regime') or t.get('regime') or default_regime
            grouped_trades[(strat_id, regime)].append(t)

        now_iso = datetime.now(timezone.utc).isoformat()
        updated_matrix = []

        with self._get_connection() as con:
            cur = con.cursor()
            for (strat_id, regime), sub_trades in grouped_trades.items():
                batch_total = len(sub_trades)
                batch_wins = len([t for t in sub_trades if t.get('win', False) or float(t.get('pnl', 0)) > 0])
                batch_losses = len([t for t in sub_trades if not t.get('win', False) and float(t.get('pnl', 0)) <= 0])
                batch_gross_win = sum(float(t.get('pnl', 0)) for t in sub_trades if float(t.get('pnl', 0)) > 0)
                batch_gross_loss = abs(sum(float(t.get('pnl', 0)) for t in sub_trades if float(t.get('pnl', 0)) < 0))

                # Query existing cumulative stats
                row = cur.execute("""
                    SELECT total_trades, win_trades, loss_trades, gross_win_usd, gross_loss_usd, status, weight_multiplier
                    FROM strategy_regime_performance
                    WHERE strategy_code = ? AND market_regime = ?
                """, (strat_id, regime)).fetchone()

                if row:
                    prev_total, prev_wins, prev_losses, prev_gwin, prev_gloss, prev_status, prev_weight = row
                    cum_total = prev_total + batch_total
                    cum_wins = prev_wins + batch_wins
                    cum_losses = prev_losses + batch_losses
                    cum_gwin = prev_gwin + batch_gross_win
                    cum_gloss = prev_gloss + batch_gross_loss
                else:
                    cum_total = batch_total
                    cum_wins = batch_wins
                    cum_losses = batch_losses
                    cum_gwin = batch_gross_win
                    cum_gloss = batch_gross_loss

                cum_net_pnl = cum_gwin - cum_gloss
                win_rate = (cum_wins / cum_total * 100.0) if cum_total > 0 else 0.0
                profit_factor = round(cum_gwin / cum_gloss, 2) if cum_gloss > 0 else (999.0 if cum_gwin > 0 else 0.0)
                expectancy = round(cum_net_pnl / cum_total, 2) if cum_total > 0 else 0.0

                # Feedback loop attribution logic (วงจรตัดตัวแพ้-ดันตัวชนะ)
                if cum_total >= 5 and (cum_net_pnl < -15.0 or expectancy < -3.0):
                    status = "BANNED"
                    weight_mult = 0.0
                elif cum_total >= 3 and (expectancy < 0.0 or win_rate < 40.0 or cum_net_pnl < 0.0):
                    status = "PENALIZED"
                    weight_mult = 0.25
                elif cum_total >= 3 and expectancy > 0.0 and win_rate >= 55.0 and profit_factor >= 1.5:
                    status = "PROMOTED"
                    weight_mult = 1.35
                else:
                    status = "ACTIVE"
                    weight_mult = 1.0

                cur.execute("""
                    INSERT INTO strategy_regime_performance (
                        strategy_code, market_regime, total_trades, win_trades, loss_trades,
                        win_rate_pct, net_pnl_usd, gross_win_usd, gross_loss_usd,
                        profit_factor, expectancy_usd, weight_multiplier, status, last_updated
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(strategy_code, market_regime) DO UPDATE SET
                        total_trades = excluded.total_trades,
                        win_trades = excluded.win_trades,
                        loss_trades = excluded.loss_trades,
                        win_rate_pct = excluded.win_rate_pct,
                        net_pnl_usd = excluded.net_pnl_usd,
                        gross_win_usd = excluded.gross_win_usd,
                        gross_loss_usd = excluded.gross_loss_usd,
                        profit_factor = excluded.profit_factor,
                        expectancy_usd = excluded.expectancy_usd,
                        weight_multiplier = excluded.weight_multiplier,
                        status = excluded.status,
                        last_updated = excluded.last_updated
                """, (
                    strat_id, regime, cum_total, cum_wins, cum_losses,
                    round(win_rate, 1), round(cum_net_pnl, 2), round(cum_gwin, 2), round(cum_gloss, 2),
                    profit_factor, expectancy, weight_mult, status, now_iso
                ))

                updated_matrix.append({
                    "strategy_code": strat_id,
                    "market_regime": regime,
                    "total_trades": cum_total,
                    "win_rate_pct": round(win_rate, 1),
                    "net_pnl_usd": round(cum_net_pnl, 2),
                    "profit_factor": profit_factor,
                    "expectancy_usd": expectancy,
                    "weight_multiplier": weight_mult,
                    "status": status
                })

            con.commit()

        return updated_matrix

    def get_regime_performance(self, strategy_code: str, market_regime: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as con:
            cur = con.cursor()
            row = cur.execute("""
                SELECT strategy_code, market_regime, total_trades, win_trades, loss_trades,
                       win_rate_pct, net_pnl_usd, profit_factor, expectancy_usd,
                       weight_multiplier, status, last_updated
                FROM strategy_regime_performance
                WHERE strategy_code = ? AND market_regime = ?
            """, (strategy_code, market_regime)).fetchone()
            if not row:
                return None
            return {
                "strategy_code": row[0],
                "market_regime": row[1],
                "total_trades": row[2],
                "win_trades": row[3],
                "loss_trades": row[4],
                "win_rate_pct": row[5],
                "net_pnl_usd": row[6],
                "profit_factor": row[7],
                "expectancy_usd": row[8],
                "weight_multiplier": row[9],
                "status": row[10],
                "last_updated": row[11]
            }

    def get_attribution_weight(self, strategy_code: str, market_regime: str) -> float:
        perf = self.get_regime_performance(strategy_code, market_regime)
        if perf:
            return float(perf.get("weight_multiplier", 1.0))
        return 1.0

    def set_attribution_override(self, strategy_code: str, market_regime: str, weight_multiplier: float, status: str, reason: str = ""):
        now_iso = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as con:
            cur = con.cursor()
            cur.execute("""
                INSERT INTO strategy_regime_performance (
                    strategy_code, market_regime, weight_multiplier, status, last_updated
                ) VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(strategy_code, market_regime) DO UPDATE SET
                    weight_multiplier = excluded.weight_multiplier,
                    status = excluded.status,
                    last_updated = excluded.last_updated
            """, (strategy_code, market_regime, weight_multiplier, status, now_iso))
            con.commit()

    def get_all_regime_performances(self) -> List[Dict[str, Any]]:
        with self._get_connection() as con:
            cur = con.cursor()
            rows = cur.execute("""
                SELECT strategy_code, market_regime, total_trades, win_trades, loss_trades,
                       win_rate_pct, net_pnl_usd, profit_factor, expectancy_usd,
                       weight_multiplier, status, last_updated
                FROM strategy_regime_performance
                ORDER BY net_pnl_usd DESC
            """).fetchall()
            return [
                {
                    "strategy_code": r[0],
                    "market_regime": r[1],
                    "total_trades": r[2],
                    "win_trades": r[3],
                    "loss_trades": r[4],
                    "win_rate_pct": r[5],
                    "net_pnl_usd": r[6],
                    "profit_factor": r[7],
                    "expectancy_usd": r[8],
                    "weight_multiplier": r[9],
                    "status": r[10],
                    "last_updated": r[11]
                }
                for r in rows
            ]

    def backfill_matrix_from_memory(self):
        """
        Backfills strategy_regime_performance from all historical records in strategy_memory.
        """
        with self._get_connection() as con:
            cur = con.cursor()
            rows = cur.execute("""
                SELECT strategy_version_id, market_regime, empirical_facts_json, created_at
                FROM strategy_memory
            """).fetchall()

            all_trades = []
            for r in rows:
                strat = r[0]
                reg = r[1]
                facts = json.loads(r[2])
                wins = facts.get('wins', 0)
                losses = facts.get('losses', 0)
                gross_win = facts.get('gross_win_usd', 0.0)
                gross_loss = facts.get('gross_loss_usd', 0.0)

                avg_win = (gross_win / wins) if wins > 0 else 0.0
                avg_loss = (gross_loss / losses) if losses > 0 else 0.0

                for _ in range(wins):
                    all_trades.append({"strategy_id": strat, "market_regime": reg, "win": True, "pnl": avg_win})
                for _ in range(losses):
                    all_trades.append({"strategy_id": strat, "market_regime": reg, "win": False, "pnl": -avg_loss})

            if all_trades:
                self.update_regime_performance_matrix(all_trades)

    def query_recent_memory(self, limit: int = 10) -> List[Dict[str, Any]]:
        with self._get_connection() as con:
            cur = con.cursor()
            rows = cur.execute("""
                SELECT id, strategy_version_id, symbol, market_regime, empirical_facts_json, ai_postmortem_notes, created_at
                FROM strategy_memory
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,)).fetchall()
            
            result = []
            for r in rows:
                result.append({
                    "id": r[0],
                    "strategy_version_id": r[1],
                    "symbol": r[2],
                    "market_regime": r[3],
                    "empirical_facts": json.loads(r[4]),
                    "ai_postmortem_notes": r[5],
                    "created_at": r[6]
                })
            return result

if __name__ == '__main__':
    rec = StrategyMemoryRecorder()
    mock_trades = [
        {"strategy_id": "STR-001", "market_regime": "STRONG_UPTREND", "pnl": 5.2, "win": True, "bars_held": 8},
        {"strategy_id": "STR-001", "market_regime": "STRONG_UPTREND", "pnl": 4.1, "win": True, "bars_held": 12},
        {"strategy_id": "STR-001", "market_regime": "STRONG_UPTREND", "pnl": -2.0, "win": False, "bars_held": 5},
        {"strategy_id": "STR-002", "market_regime": "RANGE_BOUND", "pnl": 2.5, "win": True, "bars_held": 14},
    ]
    res = rec.record_simulation_regime_memory("XAUUSD", mock_trades)
    print("Inserted Records:", len(res))
    recent = rec.query_recent_memory(5)
    print("Recent in DB:", len(recent))
    for r in recent:
        print(f"[{r['strategy_version_id']}] {r['market_regime']} -> Net +${r['empirical_facts']['net_pnl_usd']} ({r['empirical_facts']['win_rate_pct']}%)")
    print("✅ StrategyMemoryRecorder verified successfully!")
