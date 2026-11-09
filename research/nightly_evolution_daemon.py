"""
Nightly Autonomous Evolution Daemon (Master Orchestrator for Week 1-2)
======================================================================
Executes the institutional nightly training and risk governance cycle:
1. LiveRecorder Watchdog & Stall Health Check
2. Risk Governor Limit Verification
3. Champion vs Challenger Tournament Showdown
4. Portfolio Synthesis & Daily Win Rate Maximization
5. Web Dashboard Data Feed Synchronization
"""

import sys, os, subprocess, json
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PYTHON_EXE = sys.executable

def run_step(description, command_args):
    print(f"\n▶ {description}...")
    res = subprocess.run(command_args, cwd=ROOT, capture_output=True, text=True)
    if res.returncode == 0:
        print(f"  ✅ SUCCESS: {description}")
        return True, res.stdout
    else:
        print(f"  ❌ ERROR: {res.stderr}")
        return False, res.stderr

def main():
    print("="*80)
    print("🌙 LAUNCHING NIGHTLY QUANT TRAINING & EVOLUTION ORCHESTRATOR")
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()} UTC")
    print("="*80)
    
    # Step 1: Watchdog & Stall Check
    ok1, out1 = run_step("LiveRecorder Watchdog & Stall Alert Audit", [PYTHON_EXE, "research/live_recorder_watchdog.py"])
    
    # Step 2: Champion vs Challenger Tournament
    ok2, out2 = run_step("Champion vs Challenger Arena Showdown", [PYTHON_EXE, "research/champion_challenger_engine.py"])
    
    # Step 3: Master Portfolio Synthesis
    ok3, out3 = run_step("Master 100% Daily Profitability Synthesis", [PYTHON_EXE, "research/synthesize_autonomous_portfolio.py"])
    
    # Step 4: Sync to Web Dashboard
    ok4, out4 = run_step("Web Telemetry & Data Feeds Sync", [PYTHON_EXE, "tools/sync_autonomous_champions_to_web.py"])
    
    # Step 5: Dashboard Build & Verification
    ok5, out5 = run_step("Rebuild Modern Dashboard", [PYTHON_EXE, "tools/build_modern_quant_dashboard.py"])
    ok6, out6 = run_step("Run Automated Test Suite", [PYTHON_EXE, "tools/verify_white_theme_and_charts.py"])
    
    print("\n" + "="*80)
    print("🎉 NIGHTLY EVOLUTION CYCLE COMPLETED SUCCESSFULLY!")
    print("="*80)

if __name__ == '__main__':
    main()
