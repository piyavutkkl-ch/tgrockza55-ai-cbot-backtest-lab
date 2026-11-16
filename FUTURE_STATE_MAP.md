# 🚀 FUTURE STATE MAP (`cbot-atgvt` — เป้าหมายสถาปัตยกรรม V5)

> เอกสารนี้คือ **"พิมพ์เขียวเป้าหมายในอนาคต"** เพื่อให้ AI ทุกตัวเห็นภาพเดียวกันว่ากำลังพัฒนาระบบไปทางไหน (อ้างอิงกฎจาก [`GEMINI.md`](GEMINI.md))

---

## 🎯 เป้าหมายสูงสุด (North Star)
สร้างระบบ **Regime-Aware Autonomous Trading & Research Ecosystem บนบัญชี Demo** ที่สามารถ:
1. ดึงข้อมูลครบถ้วนทั้งจาก cTrader (OHLCV/Sessions) และ L2 DOM / Order Flow สด 24/7
2. อ่านสถานการณ์ตลาดปัจจุบันและรอยต่อของแต่ละ Session ให้ออก
3. เลือกกลยุทธ์ + พารามิเตอร์ (SL/TP/Sizing/Flat Time) ที่ทนทานต่อ Out-of-Sample เข้ากับสถานการณ์นั้น
4. ทดลองเปลี่ยนตรรกะบน Demo แบบขนานพร้อม Rollback อัตโนมัติเมื่อของเดิมดีกว่า และส่งต่อรายงานสถานการณ์จริงให้ Human ตัดสินใจเมื่อถึงเกณฑ์สำคัญ

---

## 🏗️ 4 เสาหลักของระบบเป้าหมาย (Target Pipeline & Modules)

### ✅ Phase 1: Smart Hybrid Data & Sanitizer Pipeline *(COMPLETED — 16 พ.ย. 2026)*
* **สร้างเสร็จแล้ว:** [`research/ctrader_mcp_client.py`](research/ctrader_mcp_client.py), [`research/hybrid_data_merger.py`](research/hybrid_data_merger.py), [`research/test_hybrid_data_merger.py`](research/test_hybrid_data_merger.py), [`docs/data/hybrid_data_audit.json`](docs/data/hybrid_data_audit.json)
* **cTrader Historical Auto-Checker & Fetcher:** ดึง `get_trendbars` & `get_symbol_sessions` อัตโนมัติผ่าน MCP JSON-RPC และแคชในเครื่อง; Watchdog 24/7 เก็บ L2 DOM 25 ชั้น, Real Spreads, Order Flow และ Slippage
* **Hybrid Data Merger + Demo Sanitizer:** Merge แท่งราคา cTrader เข้ากับ DOM/Flow ตาม UTC Timestamp, คัดกรองแถวเสีย/`NaN`/แถวผี `ticks=0` อัตโนมัติ (อัปเดตเข้า [`live_status_sync.py`](research/live_status_sync.py) & [`build_data_center.py`](tools/build_data_center.py) แล้ว) และติดแท็กครบทั้ง 7 Session/Transition zones (`ASIA`, `ASIA_TO_LONDON`, `LONDON`, `LONDON_TO_NY`, `NY`, `NY_TO_CLOSE`, `OVERNIGHT`)

### ✅ Phase 2: Session-Partitioned Regime & Forensic Strategy Engine *(COMPLETED — 16 พ.ย. 2026)*
* **สร้างเสร็จแล้ว:** [`research/session_regime_forensics.py`](research/session_regime_forensics.py), [`research/test_session_regime_forensics.py`](research/test_session_regime_forensics.py), [`docs/data/regime_strategy_matrix.json`](docs/data/regime_strategy_matrix.json) (เชื่อมเข้า [`market_intelligence_engine.py`](research/market_intelligence_engine.py) & [`build_intelligence_summary.py`](tools/build_intelligence_summary.py))
* **Session & Transition Segmentation Engine:** แยกวิจัยและจำแนกครบทั้ง 7 โซน (`ASIA`, `ASIA_TO_LONDON`, `LONDON`, `LONDON_TO_NY`, `NY`, `NY_TO_CLOSE`, `OVERNIGHT`) บนชุดข้อมูล Hybrid ที่ Clean แล้ว
* **Adaptive Optimization & Out-of-Sample Gate (No Fixed Numbers):** ทดสอบสวีป SL/RR (Tight/Balanced/Wide ATR) + รูปแบบการปิดออเดอร์ (`EXIT_AT_ZONE_END`, `ROLLOVER_GUARD`, `HOLD_THRU`) ผ่านเกณฑ์ Strict Chronological 60/40 IS➔OOS (Next-bar open fill, zero lookahead)
* **Blowup & Failure Forensic Logger (No Permanent Ban):** ทดสอบโหมด `FORENSIC_ZERO_SL` (ไม่มี SL) เพื่อจับจุดแตกหักราย Regime/Transition พร้อมระบุสาเหตุและวิธีแก้ โดยเก็บทุกกลยุทธ์ไว้ใน Regime-Matched Memory (`REGIME_MATCHED_ACTIVE`) แทนการลบ/แบนถาวร

### ✅ Phase 3: Multi-Agent Pipeline & Autonomous Demo Deployment / Rollback *(COMPLETED — 16 พ.ย. 2026)*
* **สร้างเสร็จแล้ว:** [`research/v5_multi_agent_pipeline.py`](research/v5_multi_agent_pipeline.py), [`research/demo_deployment_manager.py`](research/demo_deployment_manager.py), [`research/test_v5_multi_agent_pipeline.py`](research/test_v5_multi_agent_pipeline.py), [`cbot/BacktestLab/Strategies/RegimeAdaptiveV5.cs`](cbot/BacktestLab/Strategies/RegimeAdaptiveV5.cs), [`DECISION_LOG.md`](DECISION_LOG.md)
* **4 Specialized AI Agents ส่งงานต่อกันผ่าน Repo Structured Artifacts:**
  1. **`Data Collector & Merger Agent`**: คุม cTrader API + Watchdog 120s + Hybrid Merge + Sanitization (`hybrid_data_audit.json`)
  2. **`Research & Pattern Hunter Agent`**: สกัด 7-Zone Session Patterns & Blowup Forensics ร่วมกับคลัง 193 เปเปอร์
  3. **`Strategy Evolver & OOS Validator Agent`**: คัดเลือก OOS 60/40 ช่องที่ผ่านเกณฑ์และสร้าง Policy `REGIME_ADAPTIVE_V5 v3`
  4. **`Audit, Demo Deploy & Reporter Agent`**: Deploy `REGIME_ADAPTIVE_V5 v3` ลง Demo `#5258778` (คง Snapshot `DOM_ABSORPTION v2` สำหรับ **Auto-Rollback อัตโนมัติ**), อัปเดต [`DECISION_LOG.md`](DECISION_LOG.md), `agent_handovers.json` และ `v5_pipeline_state.json`
* **Human-in-the-Loop Decision Gate ([`DECISION_LOG.md`](DECISION_LOG.md)):** สรุปรอบพัฒนาใหญ่, กฎหลัก, และผลเทียบ A/B ให้ Human พิจารณาตัดสินใจได้ตลอดเวลา

### ✅ Phase 4: เว็บ 8 หน้าโหมด 4 ขั้นตอนหลัก & Real-Time Situational Transparency *(COMPLETED — 16 พ.ย. 2026)*
* แสดง **วงจร 4 ขั้นตอนหลัก V5** (`Data & Market Sync ➔ Research & Matching ➔ Test & Anti-Overfit ➔ Learn & State Evolution`) บน [`index.html`](docs/index.html), [`shell.js`](docs/assets/shell.js) และ [`improvement-audit.html`](docs/improvement-audit.html) พร้อมตัวบอก **7-Zone UTC Session** แบบเรียลไทม์บน Top Bar
* แสดงตาราง **Accuracy by Situation & 7-Zone Session**, **Zero-SL Blowup Forensics**, และ **Regime-Matched Memory (ไม่แบนกลยุทธ์ถาวร)** บน [`intelligence.html`](docs/intelligence.html) โดยยกเลิกตัวนับรอ `N >= 500` บนเว็บแล้วทั้งหมด
* แสดง **Demo `#5258778` Autonomous A/B (`DOM_ABSORPTION v2` vs `REGIME_ADAPTIVE_V5 v3`) & Human Gate** บน [`improvement-audit.html`](docs/improvement-audit.html) ซิงก์ [`CURRENT_STATE_MAP.md`](CURRENT_STATE_MAP.md) และ `docs/data/*.json` ตลอดเวลา
