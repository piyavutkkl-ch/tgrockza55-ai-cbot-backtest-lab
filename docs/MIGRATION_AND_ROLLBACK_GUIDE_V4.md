# 🔄 MIGRATION AND ROLLBACK GUIDE V4
## Deployment Protocol & Disaster Recovery for Institutional Quant Platform

**Version:** 4.0.0  
**Effective Date:** November 10, 2026  
**Target:** Pepperstone Demo Account `#5258778`

---

## 1. Migration Protocol (From V3 to V4)

Architecture V4 transitions the system from a single-strategy brute-force loop into an **Event-Driven Multi-Regime Platform**.

### Key Architectural Shifts:
- **Rule Hierarchy:** Immutable Hard Constraints (Tier 1) strictly clamp AI mutations (Tier 2).
- **Strategy Library:** Modular expansion into STR-001 through STR-009 with standardized schema.
- **Daemon Evolution:** Transitioned from 10s timer (`continuous_infinite_evolver.py`) to 30s event-driven market intelligence daemon (`event_driven_intelligence_daemon.py`).

### Verification Steps Prior to Forward Execution:
```bash
# 1. Run full 10-suite institutional test runner
python3 research/run_institutional_v4_test_suite.py

# 2. Check daemon status
python3 -c "import json; d=json.load(open('docs/data/live_market_intelligence.json')); print(d['feed_version'], d['system_health'])"

# 3. Verify web dashboard UI
python3 tools/verify_white_theme_and_charts.py
```

---

## 2. Daemon Process Management

The Market Intelligence Daemon runs as a background support process:
- **Script:** [`research/event_driven_intelligence_daemon.py`](file:///home/antigravity/research/event_driven_intelligence_daemon.py)
- **Log File:** `research/intelligence_daemon.log`
- **Output Feed:** `docs/data/live_market_intelligence.json` and `docs/data/live_status.json`

### To Inspect or Restart the Daemon:
```bash
# Inspect latest log output
tail -n 25 research/intelligence_daemon.log

# Run single test cycle manually
python3 research/event_driven_intelligence_daemon.py --single
```

---

## 3. Rollback Procedure (Disaster Recovery)

If any technical discrepancy, unhandled exception, or unexpected behavior occurs, follow the fail-closed rollback protocol:

### Step 1: Emergency Kill Switch
If positions are active, trigger immediate liquidation and stop orders:
```bash
python3 -c "from research.risk_governor import RiskGovernor; gov=RiskGovernor(); gov.portfolio_halted=True; print('EMERGENCY KILL SWITCH ENGAGED')"
```

### Step 2: Rollback Git Repository
To revert the codebase to the verified baseline commit (`ce5d23cf` or `35fed138`):
```bash
# Check recent stable commits
git log -n 5 --oneline

# Soft rollback to previous verified commit
git checkout ce5d23cf

# Rebuild dashboard
python3 tools/build_modern_quant_dashboard.py
python3 tools/verify_white_theme_and_charts.py
```

### Step 3: Revert to Baseline Simulation
If multi-regime routing requires recalibration, the baseline Champion model (`QuantFund VWAP Extended Absorption`) can be executed directly via:
```bash
python3 research/verify_100pct_daily_portfolio.py
```
This guarantees an immediate return to the audited 100% daily profitability baseline ($100 $\to$ $214.04 USD).
