# 🏛️ INSTITUTIONAL QUANT TRADING PLATFORM — ARCHITECTURE V4
## Adaptive Market Intelligence & Autonomous Strategy Evolution

**Version:** 4.0.0 (Institutional Enterprise)  
**Date:** November 10, 2026  
**Target Environment:** Pepperstone Demo Account `#5258778` (Phases 0–2 Sandbox) & Live Micro-Lot Gate (Phase 3)  
**Execution Paradigm:**  
```
Observe ➔ Understand ➔ Research ➔ Build ➔ Prove ➔ Select ➔ Execute ➔ Analyze ➔ Learn ➔ Evolve
```

---

## 1. Executive Summary & Paradigm Shift

The platform evolves from a single-strategy optimization loop into a **Multi-Regime Adaptive Intelligence Engine**. The system operates on the foundational principle:
> **One Market, Multiple Regimes, Multiple Strategies, One Intelligent Decision System.**

### The 9 Essential Questions the System Answers in Real-Time:
1. **Market State:** ขณะนี้ตลาดมีสภาวะอย่างไร? (Uptrend, Downtrend, Sideway, Breakout, Volatility Expansion/Compression, Thin Liquidity, High Uncertainty)
2. **Regime Transition:** ตลาดกำลังเปลี่ยนแปลงไปในทิศทางใด? (Transitioning from compression to expansion, exhaustion, or liquidity sweep)
3. **Time Context:** วันนี้เป็นวันอะไร และอยู่ใน Trading Session ใด? (Asia, London, New York, Overlap, Rollover proximity, Time to Daily Flat)
4. **Macro & News Context:** มีข่าวเศรษฐกิจอะไรที่เกี่ยวข้อง? (CPI, NFP, FOMC, Fed Speeches, Actual vs Forecast surprise)
5. **Microstructure & Order Flow:** พฤติกรรมของราคาและสภาพคล่องเป็นอย่างไร? (DOM imbalance, Delta, Aggressive Buy/Sell, Absorption, Volume Profile)
6. **Conditional Evidence:** กลยุทธ์ใดมีหลักฐานทางสถิติว่าทำงานได้ดีในสภาวะแบบนี้? (Conditional Expectancy, OOS Profit Factor)
7. **Execution Decision:** ควรเข้าเทรด ออกเทรด หรือไม่ควรเทรด (No Trade)? (Strict selective edge)
8. **Performance Attribution:** หลังจากเทรดแล้ว ผลลัพธ์เกิดจากอะไร? (7 failure categories, AI Critic postmortem)
9. **Evolutionary Prudence:** จะพัฒนาระบบให้ดีขึ้นได้อย่างไรโดยไม่เพิ่มความเสี่ยงเกินจำเป็น? (Event-driven evolution, Overfitting prevention)

---

## 2. Rule Classification Matrix (3 Strict Operational Boundaries)

```
┌────────────────────────────────────────────────────────────────────────┐
│               2.1 IMMUTABLE HARD CONSTRAINTS (Zero AI Authority)       │
│  • No Lookahead Bias (.Last(1) only)    • No Overnight Holding (Daily Flat) │
│  • Mandatory Stop Loss on EVERY order   • Risk Governor Supremacy      │
│  • No Martingale / No Grid Accumulation • Demo Only (#5258778)         │
│  • Hard Risk Limit <= 2.0% per trade    • Tamper-Proof Audit Trail     │
│  • Daily Loss Ceiling (-$10.00 USD)     • Fail-Closed Data Sanity      │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Governs & Constrains
┌───────────────────────────────────▼────────────────────────────────────┐
│                  2.2 ADAPTIVE RULES (Bounded AI Tuning)                │
│  • Take Profit & Stop Loss distances    • Dynamic Spread Thresholds    │
│  • Entry / Exit Microstructure Gates    • Consecutive Loss Cooldown    │
│  • Trading Session Allocation           • Max Daily Orders & Sizing    │
│  • News Blackout Windows                • Strategy Switching Hysteresis│
│  * Requires Multi-Objective Statistical Validation before live usage    │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Explored Across
┌───────────────────────────────────▼────────────────────────────────────┐
│             2.3 OPEN RESEARCH HYPOTHESES (Unbounded AI Formulation)    │
│  • STR-001: Trend Following             • STR-006: Order Flow Imbalance│
│  • STR-002: Mean Reversion              • STR-007: Volatility Reversal │
│  • STR-003: Liquidity Sweep Reversal    • STR-008: Session Open Range  │
│  • STR-004: Momentum Breakout           • STR-009: No Trade            │
│  • STR-005: News Reaction               • STR-010+: Custom Ensembles   │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Current State Audit Report (10 Core Subsystems)

| # | Subsystem | Current State | Code Audit Findings & Reality Check |
|---|---|:---:|---|
| **1** | **ARCHITECTURE.md** | `Partially Implemented` / `Conflicting` | Documents 10-node LangGraph pipeline, but `langgraph` package is not installed and code contained hardcoded Windows paths (`d:\cbot-atgvt`). Standalone Python engines (`verify_100pct_daily_portfolio.py`) actually perform the work. |
| **2** | **Roadmap & Governance** | `Implemented` / `In Progress` | Phase 0 (LiveRecorder Watchdog + Heartbeat 15s) and Phase 1 (Nightly daemon, Champion/Challenger arena, Risk Governor) active. Phase 2 Demo accumulation underway. |
| **3** | **Repository Structure** | `Implemented` (Cluttered) | 570+ quant papers, 13 C# engines in `cbot/`, full frontend in `docs/`, live tick/DOM data in `data/live/`. |
| **4** | **Risk Governor** | `Implemented` (Upgraded to V4) | Enforces Portfolio Daily Loss (-$10), Symbol Consecutive Losses (2), Spread Ceilings, News Void Gate. Upgraded with central Daily Flat (21:45 UTC) and Demo Assertion. |
| **5** | **LiveRecorder** | `Implemented` | `LiveRecorder.cs` writes ticks, book DOM, flow, and M1 bars. Watchdog detects market freeze. |
| **6** | **Evolution Daemon** | `Implemented` (Daemon Active) | Currently executing 24/7 background loop (`task-1005`), but will be upgraded from 10s brute-force to event-driven market intelligence. |
| **7** | **Data Pipeline** | `Partially Implemented` | M1 and Flow CSVs recorded with rich columns, but deterministic Chronological Tick & DOM Replay engine is missing. |
| **8** | **Strategy Engine** | `Partially Implemented` / `Duplicated` | 13 C# strategies in `cbot/`, but Python simulation only tested VWAP and DOM absorption. Needs modular Strategy Library (STR-001 to STR-009+). |
| **9** | **Database & Registry** | `Partially Implemented` | JSON-based storage (`champion_registry.json`, `flywheel_cycles.json`). Needs permanent Knowledge Memory and Experiment Registry to prevent duplicate testing. |
| **10**| **Testing & Deployment**| `Partially Implemented` | UI verification passes 17/17, GitHub Pages deployed. Strategy unit tests need clean self-contained implementation without broken dependencies. |

---

## 4. Master 10-Phase Implementation Plan

- **Phase 1: Architecture Audit and Rule Classification** *(COMPLETED)*
  - Completed comprehensive 10-subsystem audit.
  - Implemented `research/rule_classification.py` and `docs/data/rule_classification_matrix.json`.
  - Upgraded `research/risk_governor.py` with Daily Flat (21:45 UTC) and Demo assert.
- **Phase 2: Market Intelligence and Context Fingerprinting** *(NEXT)*
  - Time & Session Context (Asia, London, NY, Overlap, DST).
  - Economic News Context (Actual vs Forecast surprise, Pre/Post-news price behavior).
  - Multi-Regime Classifier (12 market states + transitions).
  - Microstructure Analyzer (DOM Imbalance, Delta, CVD, Spread, Absorption).
  - Context Fingerprint generator per M1 bar.
- **Phase 3: Strategy Library and Registry**
  - Implement STR-001 through STR-009 with standard strategy schema.
- **Phase 4: Adaptive Strategy Selection and Dynamic Switching**
  - Hybrid intelligence selection engine + Hysteresis anti-whipsaw filter.
- **Phase 5: Statistical Validation Upgrade**
  - Multi-objective validation (Expectancy, PF, Sharpe, Sortino, Max DD, Monte Carlo, Walk-Forward).
- **Phase 6: AI Researcher & AI Critic Workflow**
  - Gemini strategy hypothesis generator vs rigorous empirical critic.
- **Phase 7: Knowledge Memory and Experiment Registry**
  - SQLite/JSON permanent lineage tracking with duplicate experiment prevention.
- **Phase 8: Performance Attribution Engine**
  - Post-trade audit across 7 failure categories.
- **Phase 9: Event-Driven Continuous Evolution**
  - Transition from 10s brute force to event-driven / post-session intelligence loop.
- **Phase 10: Unified Web Dashboard & Final QA**
  - Live display of all 20 required indicators on GitHub Pages.
