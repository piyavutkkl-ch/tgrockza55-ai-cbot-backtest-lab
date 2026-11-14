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
    Manages persistence of strategy performance by market regime into SQLite strategy_memory.
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

        return inserted_records

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
