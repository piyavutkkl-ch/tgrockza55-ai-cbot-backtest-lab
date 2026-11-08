"""
Node 10 & Governance Persistence Layer:
Primary Storage: Supabase PostgreSQL (`https://wmaoopzqgutzxoxiqqgs.supabase.co` via Edge Function `lab`)
Local Storage: On-demand / Periodic Local Backup (`export_local_backup` -> `.json.gz` & local SQLite cache)
"""

import contextlib
import gzip
import json
import os
import sqlite3
import urllib.request
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from ..state import AdminRiskPolicy

DB_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_SQLITE_PATH = os.path.join(DB_DIR, "quant_fund_v2.sqlite")
BACKUP_DIR = os.path.join(os.path.dirname(DB_DIR), "backups")
WEB_BACKUP_LATEST = os.path.join(r"d:\cbot-atgvt\docs\data", "supabase_v2_backup_latest.json")


def _load_supabase_lab_config() -> Optional[Dict[str, str]]:
    """Loads Supabase Edge Function `lab` URL and `ingestKey` from `MyDocuments\\BacktestLab\\config.json`."""
    try:
        import ctypes.wintypes
        buf = ctypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH)
        ctypes.windll.shell32.SHGetFolderPathW(None, 5, None, 0, buf)
        candidates = [
            os.path.join(buf.value, "BacktestLab", "config.json"),
            os.path.expanduser("~\\Documents\\BacktestLab\\config.json"),
        ]
        for cfg_path in candidates:
            if cfg_path and os.path.exists(cfg_path):
                with open(cfg_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if data.get("apiUrl") and data.get("ingestKey"):
                        return {
                            "apiUrl": str(data["apiUrl"]).rstrip("/"),
                            "ingestKey": str(data["ingestKey"]),
                        }
    except Exception:
        pass
    return None


class StrategyMemoryStore:
    def __init__(self, db_path: str = DEFAULT_SQLITE_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_tables()

    @contextlib.contextmanager
    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            with conn:
                yield conn
        finally:
            conn.close()

    def _post_supabase_lab(self, route: str, payload: Dict[str, Any], timeout: int = 8) -> Optional[Dict[str, Any]]:
        """Pushes data to Supabase PostgreSQL via Edge Function `lab` (`x-ingest-key`)."""
        if os.environ.get("QF_V2_DB_PATH"):
            # Skip remote calls during isolated unit tests
            return None
        sb_cfg = _load_supabase_lab_config()
        if not sb_cfg:
            return None
        try:
            url = f"{sb_cfg['apiUrl']}/{route.lstrip('/')}"
            body = json.dumps(payload, default=str, ensure_ascii=False).encode("utf-8")
            req = urllib.request.Request(
                url,
                data=body,
                headers={
                    "Content-Type": "application/json; charset=utf-8",
                    "x-ingest-key": sb_cfg["ingestKey"],
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception:
            return None

    def _init_tables(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS risk_policies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    policy_version TEXT UNIQUE NOT NULL,
                    hard_max_dd_pct REAL NOT NULL,
                    hard_max_risk_per_trade_pct REAL NOT NULL,
                    hard_min_profit_factor REAL NOT NULL,
                    hard_min_oos_pf REAL NOT NULL,
                    max_worker_iterations INTEGER NOT NULL,
                    daily_token_limit INTEGER NOT NULL,
                    daily_cost_limit_usd REAL NOT NULL,
                    created_by TEXT NOT NULL DEFAULT 'SYSTEM_ADMIN',
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS strategy_versions (
                    id TEXT PRIMARY KEY,
                    hypothesis_id TEXT NOT NULL,
                    strategy_code TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    iteration_num INTEGER NOT NULL,
                    csharp_class_name TEXT NOT NULL,
                    source_code_sha256 TEXT NOT NULL,
                    dataset_sha256 TEXT NOT NULL,
                    parameters_json TEXT NOT NULL,
                    compile_passed INTEGER NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS workflow_audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    hypothesis_id TEXT,
                    strategy_version_id TEXT,
                    node_name TEXT NOT NULL,
                    agent_model TEXT NOT NULL,
                    prompt_version TEXT NOT NULL,
                    policy_version TEXT NOT NULL,
                    input_payload TEXT NOT NULL,
                    output_payload TEXT NOT NULL,
                    tokens_used INTEGER NOT NULL DEFAULT 0,
                    estimated_cost_usd REAL NOT NULL DEFAULT 0.0,
                    verdict TEXT,
                    verdict_reasons TEXT,
                    executed_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS deployment_approvals (
                    id TEXT PRIMARY KEY,
                    strategy_version_id TEXT NOT NULL,
                    stage_type TEXT NOT NULL,
                    approved_by TEXT NOT NULL,
                    target_environment TEXT NOT NULL,
                    kill_switch_triggered INTEGER NOT NULL DEFAULT 0,
                    approved_at TEXT NOT NULL
                );

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
                );
                """
            )
            now = datetime.now(timezone.utc).isoformat()
            conn.execute(
                """
                INSERT OR IGNORE INTO risk_policies (
                    policy_version, hard_max_dd_pct, hard_max_risk_per_trade_pct,
                    hard_min_profit_factor, hard_min_oos_pf, max_worker_iterations,
                    daily_token_limit, daily_cost_limit_usd, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                ("RISK-POL-V2.0", 18.0, 2.0, 1.15, 1.03, 3, 500000, 5.00, now),
            )

    def get_active_admin_policy(self) -> AdminRiskPolicy:
        """Loads the immutable Admin Risk Policy from the database."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM risk_policies ORDER BY id DESC LIMIT 1"
            ).fetchone()
            if not row:
                return AdminRiskPolicy()
            return AdminRiskPolicy(
                policy_version=row["policy_version"],
                hard_max_dd_pct=float(row["hard_max_dd_pct"]),
                hard_max_risk_per_trade_pct=float(row["hard_max_risk_per_trade_pct"]),
                hard_min_profit_factor=float(row["hard_min_profit_factor"]),
                hard_min_oos_pf=float(row["hard_min_oos_pf"]),
                max_worker_iterations=int(row["max_worker_iterations"]),
                daily_token_limit=int(row["daily_token_limit"]),
                daily_cost_limit_usd=float(row["daily_cost_limit_usd"]),
            )

    def get_daily_token_and_cost_usage(self) -> Tuple[int, float]:
        today_prefix = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT COALESCE(SUM(tokens_used), 0) AS tot_tokens,
                       COALESCE(SUM(estimated_cost_usd), 0.0) AS tot_cost
                FROM workflow_audit_logs
                WHERE executed_at LIKE ?
                """,
                (f"{today_prefix}%",),
            ).fetchone()
            return int(row["tot_tokens"]), round(float(row["tot_cost"]), 4)

    def check_circuit_breaker(self, policy: AdminRiskPolicy, additional_tokens: int = 0, additional_cost: float = 0.0) -> Tuple[bool, str]:
        """
        Section 4.3: API Token & Cost Limit Circuit Breaker.
        Returns `(tripped: bool, reason: str)`.
        """
        used_tokens, used_cost = self.get_daily_token_and_cost_usage()
        proj_tokens = used_tokens + additional_tokens
        proj_cost = used_cost + additional_cost

        if proj_tokens > policy.daily_token_limit:
            return (
                True,
                f"CIRCUIT BREAKER TRIPPED: Daily token usage ({proj_tokens}) exceeds limit ({policy.daily_token_limit}).",
            )
        if proj_cost > policy.daily_cost_limit_usd:
            return (
                True,
                f"CIRCUIT BREAKER TRIPPED: Daily API cost (${proj_cost:.2f}) exceeds limit (${policy.daily_cost_limit_usd:.2f}).",
            )
        return False, "OK"

    def log_node_execution(
        self,
        node_name: str,
        agent_model: str,
        prompt_version: str,
        policy_version: str,
        input_payload: Dict[str, Any],
        output_payload: Dict[str, Any],
        tokens_used: int = 0,
        estimated_cost_usd: float = 0.0,
        verdict: str = "INFO",
        verdict_reasons: Optional[List[str]] = None,
        hypothesis_id: Optional[str] = None,
        strategy_version_id: Optional[str] = None,
    ) -> int:
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO workflow_audit_logs (
                    hypothesis_id, strategy_version_id, node_name, agent_model,
                    prompt_version, policy_version, input_payload, output_payload,
                    tokens_used, estimated_cost_usd, verdict, verdict_reasons, executed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    hypothesis_id,
                    strategy_version_id,
                    node_name,
                    agent_model,
                    prompt_version,
                    policy_version,
                    json.dumps(input_payload, default=str, ensure_ascii=False),
                    json.dumps(output_payload, default=str, ensure_ascii=False),
                    tokens_used,
                    estimated_cost_usd,
                    verdict,
                    json.dumps(verdict_reasons or [], ensure_ascii=False),
                    now,
                ),
            )
            row_id = int(cur.lastrowid)

        # Sync to Supabase PostgreSQL V2 table if deployed
        self._post_supabase_lab(
            "qf-v2",
            {
                "table": "workflow_audit_logs",
                "record": {
                    "hypothesis_id": hypothesis_id,
                    "strategy_version_id": strategy_version_id,
                    "node_name": node_name,
                    "agent_model": agent_model,
                    "prompt_version": prompt_version,
                    "policy_version": policy_version,
                    "input_payload": input_payload,
                    "output_payload": output_payload,
                    "tokens_used": tokens_used,
                    "estimated_cost_usd": estimated_cost_usd,
                    "verdict": verdict,
                    "verdict_reasons": verdict_reasons or [],
                    "executed_at": now,
                },
            },
            timeout=3,
        )
        return row_id

    def record_strategy_version(
        self,
        hypothesis_id: str,
        strategy_code: str,
        symbol: str,
        iteration_num: int,
        csharp_class_name: str,
        source_code_sha256: str,
        dataset_sha256: str,
        parameters: Dict[str, Any],
        compile_passed: bool,
    ) -> str:
        version_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO strategy_versions (
                    id, hypothesis_id, strategy_code, symbol, iteration_num,
                    csharp_class_name, source_code_sha256, dataset_sha256,
                    parameters_json, compile_passed, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    version_id,
                    hypothesis_id,
                    strategy_code,
                    symbol,
                    iteration_num,
                    csharp_class_name,
                    source_code_sha256,
                    dataset_sha256,
                    json.dumps(parameters, ensure_ascii=False),
                    1 if compile_passed else 0,
                    now,
                ),
            )

        self._post_supabase_lab(
            "qf-v2",
            {
                "table": "strategy_versions",
                "record": {
                    "id": version_id,
                    "hypothesis_id": hypothesis_id,
                    "strategy_code": strategy_code,
                    "symbol": symbol,
                    "iteration_num": iteration_num,
                    "csharp_class_name": csharp_class_name,
                    "source_code_sha256": source_code_sha256,
                    "dataset_sha256": dataset_sha256,
                    "parameters_json": parameters,
                    "compile_passed": compile_passed,
                    "created_at": now,
                },
            },
            timeout=3,
        )
        return version_id

    def sync_validated_strategy_to_supabase_postgres(
        self,
        strategy_code: str,
        symbol: str,
        source_code_sha256: str,
        dataset_sha256: str,
        parameters: Dict[str, Any],
        full_metrics: Dict[str, Any],
        oos_metrics: Dict[str, Any],
        checklist_passed: bool,
        empirical_facts: Dict[str, Any],
        ai_postmortem_notes: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """
        Directly persists the V2 validated strategy, SHA-256 hashes, 9/9 checklist status,
        IS/VAL/OOS math reports, and quarantined AI postmortem notes into the live
        Supabase PostgreSQL (`strategies` + `backtest_runs` + Google Drive archive).
        """
        ingest_payload = {
            "strategy": {
                "code": strategy_code,
                "version": 2,
                "name": f"Antigravity V2 Institutional Equilibrium ({strategy_code})",
                "theory": (
                    f"[V2 Build->Prove->Protect] Dataset SHA256={dataset_sha256[:16]} | "
                    f"Code SHA256={source_code_sha256[:16]} | "
                    f"OOS PF={oos_metrics.get('profit_factor')} | "
                    f"9/9 Boolean Checklist={'PASS' if checklist_passed else 'VETO'}"
                ),
                "entryRules": [
                    "13:00-17:00 UTC New York Session",
                    "Anchored VWAP Stretch >= 4.2 SD + 15-bar extreme",
                    "News Void Gate: Bar range <= 2.0x ATR",
                ],
                "exitRules": [
                    "Equilibrium Target: Session VWAP Touch",
                    "Hard Structural Stop Loss: 2.0x ATR clamped to <= 0.70% risk/trade",
                    "Time Stop: 60 minutes",
                ],
                "paramNames": list(parameters.keys()),
            },
            "run": {
                "symbol": symbol,
                "timeframe": "m1",
                "dateFrom": "2022-01-03T00:00:00Z",
                "dateTo": "2026-09-30T23:59:00Z",
                "params": {
                    **parameters,
                    "source_code_sha256": source_code_sha256[:16],
                    "dataset_sha256": dataset_sha256[:16],
                    "checklist_9_of_9": checklist_passed,
                },
                "runningMode": "QuantFundV2_Deterministic_Math",
                "startBalance": 100.0,
                "endBalance": round(100.0 + float(full_metrics.get("net_pnl_usd", 0.0)), 2),
                "netProfit": float(full_metrics.get("net_pnl_usd", 0.0)),
                "totalTrades": int(full_metrics.get("trades", 0)),
                "winRate": float(full_metrics.get("win_rate_pct", 0.0)),
                "profitFactor": float(full_metrics.get("profit_factor", 0.0)),
                "maxDdPct": float(full_metrics.get("max_dd_pct", 0.0)),
                "machine": os.environ.get("COMPUTERNAME", "ANTIGRAVITY-V2"),
                "note": (
                    f"[QuantFund V2 Supabase Sync] 9/9 Checklist={'PASS' if checklist_passed else 'VETO'} | "
                    f"OOS PF={oos_metrics.get('profit_factor')} (${oos_metrics.get('net_pnl_usd', 0.0):+.2f}) | "
                    f"1oz Unscaled=+${full_metrics.get('unscaled_1oz_net_pnl_usd', 0.0):.2f} | "
                    f"AI Notes: Quarantined (verified_by_human=False)"
                ),
            },
            "trades": [],
            "equity": [
                {
                    "v2_empirical_facts": empirical_facts,
                    "v2_quarantined_ai_postmortem_notes": ai_postmortem_notes,
                }
            ],
        }
        return self._post_supabase_lab("ingest", ingest_payload, timeout=12)

    def record_strategy_memory(
        self,
        strategy_version_id: str,
        symbol: str,
        market_regime: str,
        empirical_facts: Dict[str, Any],
        ai_postmortem_notes: Dict[str, Any],
        verified_by_human: bool = False,
        verified_by: Optional[str] = None,
        strategy_code: str = "QF_V2_VWAP_EQUILIBRIUM",
        parameters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Section 4.6: Stores Strategy Memory with strict separation between
        `empirical_facts_json` (math facts) and `ai_postmortem_notes` (LLM suggestions)
        into Supabase PostgreSQL (primary) and local mirror.
        """
        mem_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()

        # 1. Sync to live Supabase PostgreSQL (`strategies` + `backtest_runs` + `/qf-v2` table)
        sb_res = self.sync_validated_strategy_to_supabase_postgres(
            strategy_code=strategy_code,
            symbol=symbol,
            source_code_sha256=str(empirical_facts.get("source_code_sha256") or ""),
            dataset_sha256=str(empirical_facts.get("dataset_sha256") or ""),
            parameters=parameters or {},
            full_metrics=empirical_facts.get("full_period_metrics") or {},
            oos_metrics=empirical_facts.get("out_of_sample_metrics") or {},
            checklist_passed=bool(empirical_facts.get("checklist_passed", False)),
            empirical_facts=empirical_facts,
            ai_postmortem_notes=ai_postmortem_notes,
        )
        supabase_run_id = int(sb_res["runId"]) if (sb_res and sb_res.get("runId")) else None

        self._post_supabase_lab(
            "qf-v2",
            {
                "table": "strategy_memory",
                "record": {
                    "id": mem_id,
                    "strategy_version_id": strategy_version_id,
                    "symbol": symbol,
                    "market_regime": market_regime,
                    "empirical_facts_json": empirical_facts,
                    "ai_postmortem_notes": ai_postmortem_notes,
                    "verified_by_human": verified_by_human,
                    "verified_by": verified_by,
                    "created_at": now,
                },
            },
            timeout=4,
        )

        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO strategy_memory (
                    id, strategy_version_id, symbol, market_regime,
                    empirical_facts_json, ai_postmortem_notes,
                    verified_by_human, verified_by, supabase_run_id, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    mem_id,
                    strategy_version_id,
                    symbol,
                    market_regime,
                    json.dumps(empirical_facts, ensure_ascii=False),
                    json.dumps(ai_postmortem_notes, ensure_ascii=False),
                    1 if verified_by_human else 0,
                    verified_by,
                    supabase_run_id,
                    now,
                ),
            )
        return {
            "memory_id": mem_id,
            "supabase_run_id": supabase_run_id,
            "supabase_synced": bool(supabase_run_id),
            "strategy_version_id": strategy_version_id,
            "symbol": symbol,
            "empirical_facts": empirical_facts,
            "ai_postmortem_notes": ai_postmortem_notes,
            "verified_by_human": verified_by_human,
            "auto_apply_blocked": not verified_by_human,
            "created_at": now,
        }

    def get_usable_strategy_learnings(self, symbol: str) -> List[Dict[str, Any]]:
        """
        Only returns AI postmortem notes that have been explicitly verified by a human (`verified_by_human = 1`).
        Empirical facts are always returned.
        """
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM strategy_memory WHERE symbol = ? ORDER BY created_at DESC",
                (symbol,),
            ).fetchall()
            results = []
            for r in rows:
                is_verified = bool(r["verified_by_human"])
                results.append({
                    "memory_id": r["id"],
                    "supabase_run_id": r["supabase_run_id"],
                    "empirical_facts": json.loads(r["empirical_facts_json"]),
                    "ai_postmortem_notes": json.loads(r["ai_postmortem_notes"]) if is_verified else {"status": "UNVERIFIED_BLOCKED_FROM_AUTO_USE"},
                    "verified_by_human": is_verified,
                })
            return results

    def export_local_backup(self, custom_backup_dir: Optional[str] = None) -> Dict[str, Any]:
        """
        On-Demand / Periodic Local Backup ("สำรองเข้าเครื่องนาน ๆ ที ครั้งได้"):
        Exports all V2 tables + live Supabase runs summary into a timestamped `.json.gz` archive
        in `d:\\cbot-atgvt\\quant_fund_v2\\backups\\` and updates `docs/data/supabase_v2_backup_latest.json`
        for one-click download from the Web Dashboard.
        """
        target_dir = custom_backup_dir or BACKUP_DIR
        os.makedirs(target_dir, exist_ok=True)
        now_utc = datetime.now(timezone.utc)
        stamp = now_utc.strftime("%Y%m%d_%H%M%S")

        tables_dump: Dict[str, List[Dict[str, Any]]] = {}
        with self._connect() as conn:
            for tbl in ("risk_policies", "strategy_versions", "workflow_audit_logs", "deployment_approvals", "strategy_memory"):
                rows = conn.execute(f"SELECT * FROM {tbl} ORDER BY rowid DESC LIMIT 500").fetchall()
                tables_dump[tbl] = [dict(r) for r in rows]

        # Also fetch recent Supabase PostgreSQL runs metadata if available
        supabase_runs: List[Dict[str, Any]] = []
        sb_cfg = _load_supabase_lab_config()
        if sb_cfg and not os.environ.get("QF_V2_DB_PATH"):
            try:
                req = urllib.request.Request(
                    f"{sb_cfg['apiUrl']}/runs?limit=25",
                    headers={"x-ingest-key": sb_cfg["ingestKey"]},
                    method="GET",
                )
                with urllib.request.urlopen(req, timeout=6) as resp:
                    supabase_runs = json.loads(resp.read().decode("utf-8"))
            except Exception:
                supabase_runs = []

        backup_payload = {
            "backup_created_at_utc": now_utc.isoformat(),
            "primary_database": "SUPABASE_POSTGRESQL (https://wmaoopzqgutzxoxiqqgs.supabase.co)",
            "backup_mode": "ON_DEMAND_LOCAL_SNAPSHOT",
            "supabase_recent_runs_count": len(supabase_runs),
            "supabase_recent_runs": supabase_runs[:10],
            "v2_tables": tables_dump,
        }

        gz_path = os.path.join(target_dir, f"supabase_v2_backup_{stamp}.json.gz")
        raw_bytes = json.dumps(backup_payload, indent=2, ensure_ascii=False).encode("utf-8")
        with gzip.open(gz_path, "wb") as gz_file:
            gz_file.write(raw_bytes)

        # Also write uncompressed latest JSON in `docs/data/supabase_v2_backup_latest.json` for Web Dashboard 1-click download
        try:
            os.makedirs(os.path.dirname(WEB_BACKUP_LATEST), exist_ok=True)
            with open(WEB_BACKUP_LATEST, "w", encoding="utf-8") as wf:
                wf.write(raw_bytes.decode("utf-8"))
        except Exception:
            pass

        return {
            "backup_file_gz": gz_path,
            "web_download_json": WEB_BACKUP_LATEST,
            "size_bytes": len(raw_bytes),
            "supabase_runs_included": len(supabase_runs),
            "v2_versions_included": len(tables_dump.get("strategy_versions", [])),
            "v2_memories_included": len(tables_dump.get("strategy_memory", [])),
            "created_at_utc": now_utc.isoformat(),
        }
