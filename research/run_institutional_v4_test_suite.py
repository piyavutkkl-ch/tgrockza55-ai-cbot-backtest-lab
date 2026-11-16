"""
Institutional Master Test Suite Runner V4
=========================================
Runs all comprehensive unit & integration tests for Architecture V4:
1. Rule Classification Matrix V4 (research/rule_classification.py)
2. Risk Governor V4 (research/risk_governor.py)
3. Market Intelligence Engine V4 (research/test_market_intelligence.py)
4. Adaptive Strategy Library V4 (research/test_strategy_library.py)
5. Adaptive Strategy Selector V4 (research/test_adaptive_strategy_selector.py)
6. Statistical Validation Engine V4 (research/test_statistical_validation.py)
7. Performance Attribution & AI Critic V4 (research/performance_attribution_engine.py)
8. Experiment Registry V4 (research/experiment_registry.py)
9. 8-Page Quant Research Portal Verification (tools/verify_8page_ui.py)
"""

import sys, os, subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PYTHON_EXE = sys.executable

TEST_STEPS = [
    ("Tier 1-3: Rule Classification Matrix", [PYTHON_EXE, "research/rule_classification.py"]),
    ("Risk Governor V4 & Daily Flat", [PYTHON_EXE, "research/risk_governor.py"]),
    ("Market Intelligence & Fingerprinting", [PYTHON_EXE, "-m", "unittest", "research/test_market_intelligence.py"]),
    ("Adaptive Strategy Library (STR-001 - STR-009)", [PYTHON_EXE, "-m", "unittest", "research/test_strategy_library.py"]),
    ("Adaptive Strategy Selector & Switching", [PYTHON_EXE, "-m", "unittest", "research/test_adaptive_strategy_selector.py"]),
    ("Attribution Matrix & Dynamic Feedback Loop", [PYTHON_EXE, "-m", "unittest", "research/test_attribution_matrix_feedback.py"]),
    ("Multi-Objective Statistical Validation", [PYTHON_EXE, "-m", "unittest", "research/test_statistical_validation.py"]),
    ("Performance Attribution & AI Critic", [PYTHON_EXE, "research/performance_attribution_engine.py"]),
    ("Knowledge Memory & Experiment Registry", [PYTHON_EXE, "research/experiment_registry.py"]),
    ("Chronological Market Replay Engine", [PYTHON_EXE, "research/market_replay_engine.py"]),
    ("Event-Driven Market Intelligence Daemon", [PYTHON_EXE, "research/event_driven_intelligence_daemon.py", "--single"]),
    ("Phase 1 Hybrid cTrader+Live Merger & Sanitizer", [PYTHON_EXE, "-m", "unittest", "research/test_hybrid_data_merger.py"]),
    ("Phase 2 Session Regime Engine & Blowup Forensics", [PYTHON_EXE, "-m", "unittest", "research/test_session_regime_forensics.py"]),
    ("Phase 3 V5 4-Agent Pipeline & Demo Rollback", [PYTHON_EXE, "-m", "unittest", "research/test_v5_multi_agent_pipeline.py"]),
    ("8-Page Web Portal Verification", [PYTHON_EXE, "tools/verify_8page_ui.py"])
]

def main():
    print("="*80)
    print("🏛️ INSTITUTIONAL QUANT PLATFORM V4: COMPREHENSIVE TEST RUNNER")
    print("="*80)
    
    passed_count = 0
    total_count = len(TEST_STEPS)
    
    for name, cmd in TEST_STEPS:
        print(f"\n▶ Running: {name}...")
        res = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        if res.returncode == 0:
            print(f"  ✅ [PASS] {name}")
            passed_count += 1
        else:
            print(f"  ❌ [FAIL] {name}")
            print(res.stderr or res.stdout)
            
    print("\n" + "="*80)
    print(f"🏁 TEST SUMMARY: {passed_count}/{total_count} SUITES PASSED ({passed_count/total_count*100:.1f}%)")
    print("="*80)
    
    if passed_count == total_count:
        print("🎉 ALL INSTITUTIONAL V4 ARCHITECTURE SUITES PASSED FLAWLESSLY!")
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == '__main__':
    main()
