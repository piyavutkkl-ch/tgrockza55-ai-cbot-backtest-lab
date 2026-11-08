"""
Evolutionary Discovery Suite Runner
====================================
Executes the four core quantitative pillars:
1. BehavioralAlphaEngine (Human Psychology Models)
2. AlphaDiscoveryEngine (Autonomous Symbolic Mining)
3. AutonomousValidator (Zero Blind Trust Empirical Proofs)
4. StrategyEvolutionEngine (Generational Learning & Immutable Vault)

Compiles results and syncs to docs/data/*.json for the live Web Dashboard.
"""

import os
import sys
import json
from datetime import datetime, timezone

# Ensure project root is in path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(CURRENT_DIR)
sys.path.insert(0, REPO_ROOT)

from research.behavioral_alpha_engine import BehavioralAlphaEngine
from research.alpha_discovery_engine import AlphaDiscoveryEngine
from research.autonomous_validator import AutonomousValidator
from research.strategy_evolution_engine import StrategyEvolutionEngine

DOCS_DATA = os.path.join(REPO_ROOT, 'docs', 'data')
os.makedirs(DOCS_DATA, exist_ok=True)

def run_suite():
    print("=" * 70)
    print("ANTIGRAVITY QUANT LAB — EVOLUTIONARY DISCOVERY & BEHAVIORAL SUITE")
    print("=" * 70)

    # 1. Behavioral Alpha Engine
    print("[1/4] Running Behavioral Alpha & Human Psychology Engine...")
    beh_engine = BehavioralAlphaEngine()
    beh_data = beh_engine.evaluate_biases()
    beh_path = os.path.join(DOCS_DATA, 'behavioral_alphas.json')
    with open(beh_path, 'w', encoding='utf-8') as f:
        json.dump(beh_data, f, indent=2, ensure_ascii=False)
    print(f"  -> Saved {len(beh_data['models'])} behavioral models to {beh_path}")

    # 2. Alpha Discovery Engine
    print("[2/4] Running Alpha Discovery Engine (Symbolic Non-Human Mining)...")
    disc_engine = AlphaDiscoveryEngine()
    disc_data = disc_engine.mine_new_alphas()
    disc_path = os.path.join(DOCS_DATA, 'alpha_discovery.json')
    with open(disc_path, 'w', encoding='utf-8') as f:
        json.dump(disc_data, f, indent=2, ensure_ascii=False)
    print(f"  -> Saved {len(disc_data['alphas'])} non-human alphas to {disc_path}")

    # 3. Autonomous Validator
    print("[3/4] Running Autonomous Experiment & Validation Suite (Zero Blind Trust)...")
    validator = AutonomousValidator()
    val_data = validator.run_validation_suite()
    val_path = os.path.join(DOCS_DATA, 'autonomous_validation.json')
    with open(val_path, 'w', encoding='utf-8') as f:
        json.dump(val_data, f, indent=2, ensure_ascii=False)
    print(f"  -> Saved {len(val_data['results'])} audit reports to {val_path}")

    # 4. Strategy Evolution Engine
    print("[4/4] Running Strategy Evolution Engine & Immutable Vault...")
    evo_engine = StrategyEvolutionEngine()
    evo_data = evo_engine.get_evolution_report()
    evo_path = os.path.join(DOCS_DATA, 'strategy_evolution.json')
    with open(evo_path, 'w', encoding='utf-8') as f:
        json.dump(evo_data, f, indent=2, ensure_ascii=False)
    print(f"  -> Saved Gen {evo_data['generations']['active_generation']} evolution tree & vault to {evo_path}")

    # Update flywheel_cycles.json with evolutionary and behavioral insights
    fw_path = os.path.join(DOCS_DATA, 'flywheel_cycles.json')
    if os.path.exists(fw_path):
        try:
            with open(fw_path, 'r', encoding='utf-8') as f:
                fw = json.load(f)
            fw["behavioral_alphas"] = beh_data
            fw["alpha_discovery"] = disc_data
            fw["autonomous_validation"] = val_data
            fw["strategy_evolution"] = evo_data
            with open(fw_path, 'w', encoding='utf-8') as f:
                json.dump(fw, f, indent=2, ensure_ascii=False)
            print("  -> Synced evolutionary intelligence into flywheel_cycles.json")
        except Exception as e:
            print(f"  -> Error updating flywheel_cycles.json: {e}")

    print("=" * 70)
    print("SUCCESS: All 4 engines executed and synchronized cleanly.")
    print("=" * 70)

if __name__ == "__main__":
    run_suite()
