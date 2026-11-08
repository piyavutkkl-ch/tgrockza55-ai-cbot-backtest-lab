# 🏛️ MISSION BRIEF: UPGRADE & MODERNIZE UNIFIED CBOT QUANT PLATFORM (WEB & CLOUD ARCHITECTURE)

**Role:** Lead Quant Developer & Senior Full-Stack Architect on Google Antigravity
**Project:** Unified Multi-Agent Institutional Trading & Research Platform (`cbot-atgvt`)
**Target Surface:** Web Dashboard (`docs/`) & Cloud-Native Execution Engine

---

## 1. Executive Context & System Architecture

This project is the culmination and consolidation of four distinct core pillars:
1. **cbot_Data PAPER:** Deep research across 141+ quant papers, producing the 13 C# Strategy Engines in `cbot/BacktestLab/Strategies/` (such as `DomWallAbsorption.cs`, `QuantAuctionValue.cs`, `QuantRoughVol.cs`, `QuantHawkesBurst.cs`).
2. **cbot_Multi-Agent:** The enterprise architecture blueprint specified in `ARCHITECTURE.md`, Supabase PostgreSQL data layer, and Quant Fund multi-agent execution structure.
3. **cbot_Front-end UI:** The interactive web dashboard in `docs/` (`index.html`, `pro.html`, `research.html`, `chart.html`, `daystudy.html`) hosted on GitHub Pages (`https://tgrockza55-ai.github.io/tgrockza55-ai-cbot-backtest-lab/`).
4. **cbot-atgvt (Live Trading & Microstructure Research):** Real-time tick & Level 2 Depth-of-Market (DOM) recording on Pepperstone Demo `#5258778` in `data/live/`, leading to the empirical discovery of the Champion Model: **VWAP Extended Absorption + Macro Trend Shield** (Profit Factor 3.00, Net +$96.00 USD, Max Drawdown $12.00 USD on 3,345 M1 bars).

---

## 2. Immediate Core Deliverables (Web Dashboard Upgrade)

Your immediate mission is to upgrade and modernize the web dashboard inside the `docs/` folder:

### Deliverable A: Modernize the Strategy Backtest Lab (`docs/pro.html`, `docs/index.html`)
- **Replace Outdated Mock Tabs:**
  - Decommission the previous legacy/mock tabs.
  - Elevate the newly discovered Champion Models:
    - `🔥 VWAP_ABSORPTION (XAU)` -> Net +$96.00 USD, Profit Factor 3.00, Max DD $12.00 USD, Win Rate 50-62%, 24 trades.
    - `⚡ DOM_ABSORPTION (BTC)`
    - `🛡️ DOM_ABSORPTION (ETH)`
- **Synchronize JSON Data Feeds:**
  - Update `docs/data/backtest_data.json` with the exact verified trade logs, equity curves, and performance metrics from `research/exhaustive_extrema_quant_search.py` and `research/optimize_vwap_extrema_all_assets.py`.

### Deliverable B: Clear Visual Zone Separation
- **Zone 1: Strategy Backtest Lab (ห้องทดลองย้อนหลัง)**
  - Clearly labeled with historical research badges, equity charts, parameter inspectors, and trade logs.
- **Zone 2: Bot Fleet Live Monitor (ระบบมอนิเตอร์บอทสด)**
  - Connected to `docs/data/live_status.json`.
  - Shows real-time telemetry from Pepperstone Demo `#5258778`: Heartbeat pulses, active prices, live imbalance, and current net PnL.

### Deliverable C: Secure Controller Architecture (Public vs Admin Mode)
Since the dashboard is hosted on public GitHub Pages:
- **Public Visitor Mode (View-Only):**
  - Visitors can browse performance charts, backtest statistics, and live telemetry in read-only mode.
  - All interactive controls (start/stop/kill/lot size) are strictly hidden or disabled.
- **Owner Admin Mode (Authenticated via Supabase):**
  - Sign-in gateway for the portfolio owner (`piyavut.ch@gmail.com`) using Supabase Auth.
  - Unlocks sensitive controls (Emergency Kill Switch, Pause/Resume, Lot Size Adjustment) with signed JWT tokens.
  - **Zero Secrets in Frontend:** Never hardcode `Client Secret` or sensitive API keys in client-side HTML/JavaScript.

### Deliverable D: cTrader Open API OAuth2 Callback
- Ensure `docs/auth.html` exists and handles OAuth2 redirects from `https://openapiconsole.spotware.com` cleanly, parsing the authorization code and passing it securely to Supabase without exposing credentials.

---

## 3. Key Reference Files in Workspace
- `ARCHITECTURE.md` - Master enterprise architecture blueprint (30.6 KB).
- `docs/index.html` & `docs/pro.html` - Primary web dashboard templates.
- `docs/data/backtest_data.json` - Strategy backtest data feed.
- `docs/data/live_status.json` - Live bot fleet telemetry feed.
- `research/find_high_profit_strategy.py` - Core empirical simulation harness.
- `research/exhaustive_extrema_quant_search.py` - Turning point optimization search.
- `data/live/` - Portable recorded M1, tick flow, and DOM data for XAUUSD, GOLD-PERP, BTCUSD, ETHUSD.

Proceed with reviewing `ARCHITECTURE.md` and upgrading the `docs/` web platform immediately.
