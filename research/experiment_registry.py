"""
Knowledge Memory & Experiment Registry V4 (Architecture V4)
===========================================================
Permanent repository for all quantitative trading hypotheses and experiments:
- Stores comprehensive experiment metadata, results, and causal attribution
- Tracks lineage (previous related experiments -> next recommendations)
- Strictly prevents duplicate experiments via parameter-dataset hashing
- Searchable by strategy family, market regime, and outcome
"""

import os
import json
import hashlib
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone

class ExperimentRegistry:
    ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    REGISTRY_FILE = os.path.join(ROOT, 'docs', 'data', 'experiment_registry.json')

    def __init__(self):
        self.experiments: List[Dict[str, Any]] = []
        self._load()

    def _load(self):
        if os.path.exists(self.REGISTRY_FILE):
            try:
                with open(self.REGISTRY_FILE, 'r', encoding='utf-8') as f:
                    d = json.load(f)
                    self.experiments = d.get('experiments', [])
            except Exception:
                self.experiments = []

    def save(self):
        os.makedirs(os.path.dirname(self.REGISTRY_FILE), exist_ok=True)
        payload = {
            "registry_version": "V4.0-INSTITUTIONAL",
            "updated_at_utc": datetime.now(timezone.utc).isoformat(),
            "total_experiments_recorded": len(self.experiments),
            "experiments": self.experiments
        }
        with open(self.REGISTRY_FILE, 'w', encoding='utf-8') as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)

    @classmethod
    def compute_experiment_hash(cls, strategy_id: str, parameters: Dict[str, Any], dataset_id: str) -> str:
        """Deterministic fingerprint of an experiment configuration to detect duplicates."""
        param_str = json.dumps(parameters, sort_keys=True)
        raw = f"{strategy_id}::{param_str}::{dataset_id}"
        return hashlib.sha256(raw.encode('utf-8')).hexdigest()[:16]

    def is_duplicate_experiment(self, strategy_id: str, parameters: Dict[str, Any], dataset_id: str) -> Tuple[bool, Optional[str]]:
        """Checks if this exact strategy and parameter combination has already been evaluated."""
        cfg_hash = self.compute_experiment_hash(strategy_id, parameters, dataset_id)
        for exp in self.experiments:
            if exp.get('config_hash') == cfg_hash:
                return True, exp.get('experiment_id')
        return False, None

    def record_experiment(self, strategy_id: str, strategy_version: str, hypothesis: str,
                          parameters: Dict[str, Any], dataset_id: str, market_context: str,
                          test_period: str, results: Dict[str, Any], failure_reasons: List[str],
                          successful_conditions: List[str], research_references: List[str] = None,
                          previous_exp_id: str = None, next_recommended: List[str] = None) -> str:
        """
        Records a new experiment in the permanent knowledge memory.
        """
        is_dup, existing_id = self.is_duplicate_experiment(strategy_id, parameters, dataset_id)
        if is_dup:
            raise ValueError(f"DUPLICATE EXPERIMENT VETO: Configuration already tested in {existing_id}. Re-running identical setups is prohibited.")

        now_utc = datetime.now(timezone.utc)
        exp_num = len(self.experiments) + 1
        exp_id = f"EXP-{now_utc.strftime('%Y%m%d')}-{exp_num:04d}"
        cfg_hash = self.compute_experiment_hash(strategy_id, parameters, dataset_id)
        
        record = {
            "experiment_id": exp_id,
            "config_hash": cfg_hash,
            "created_at_utc": now_utc.isoformat(),
            "strategy_id": strategy_id,
            "strategy_version": strategy_version,
            "hypothesis": hypothesis,
            "parameters": parameters,
            "dataset_id": dataset_id,
            "market_context": market_context,
            "test_period": test_period,
            "results": results,
            "failure_reasons": failure_reasons,
            "successful_conditions": successful_conditions,
            "research_references": research_references or [],
            "previous_related_experiment": previous_exp_id,
            "next_recommended_experiments": next_recommended or []
        }
        
        self.experiments.append(record)
        self.save()
        return exp_id

    def find_experiments_by_strategy(self, strategy_id: str) -> List[Dict[str, Any]]:
        return [e for e in self.experiments if e.get('strategy_id') == strategy_id]

    def find_successful_experiments(self) -> List[Dict[str, Any]]:
        return [e for e in self.experiments if e.get('results', {}).get('validation_passed', False)]

if __name__ == '__main__':
    print("Testing ExperimentRegistry V4...")
    reg = ExperimentRegistry()
    ts = datetime.now(timezone.utc).timestamp()
    test_params = {"sl": 5.0, "rr": 2.5, "delta_th": 10.0, "test_ts": ts}
    
    # Test recording
    exp_id = reg.record_experiment(
        strategy_id="STR-001", strategy_version="1.0.0",
        hypothesis="Trend momentum continuation",
        parameters=test_params,
        dataset_id="XAUUSD_M1_LIVE_NOV2026",
        market_context="STRONG_UPTREND / NY_SESSION",
        test_period="2026-11-01 to 2026-11-06",
        results={"net_pnl": 58.78, "profit_factor": 6.63, "validation_passed": True},
        failure_reasons=[],
        successful_conditions=["High liquidity London/NY overlap", "Order flow delta > 10"]
    )
    print(f"Recorded experiment: {exp_id}")
    
    # Test duplicate detection
    is_dup, existing = reg.is_duplicate_experiment("STR-001", test_params, "XAUUSD_M1_LIVE_NOV2026")
    print(f"Duplicate detected correctly: {is_dup} (Original: {existing})")
    assert is_dup
    print("✅ ExperimentRegistry V4 verified successfully!")
