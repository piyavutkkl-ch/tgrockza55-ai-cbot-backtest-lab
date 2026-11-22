# 🗺️ CURRENT STATE MAP (`cbot-atgvt` — อัปเดต 22 พ.ย. 2026)

> เอกสารนี้คือ **"ภาพความจริง ณ ปัจจุบัน"** ที่บันทึกอยู่ใน Git Repo เพื่อใช้เป็นจุดตั้งต้นเดียวกันของ AI ทุกตัวและ Human (อ้างอิงกฎจาก [`GEMINI.md`](GEMINI.md))

---

## 1. สภาพแวดล้อมและบัญชีปฏิบัติการ (Execution & Automation)
* **GitHub Repository หลัก:** `https://github.com/piyavutkkl-ch/tgrockza55-ai-cbot-backtest-lab` (`origin/main` · `gh` active account = `piyavutkkl-ch`)
* **หน้าเว็บแดชบอร์ด (Live 8-Page Read-Only Portal):** `https://piyavutkkl-ch.github.io/tgrockza55-ai-cbot-backtest-lab/index.html`
  * ยกเลิก Supabase Auth / Edge Function `lab` / Google Login / Google Drive แล้ว 100%
  * ใช้ธีมมาตรฐานของ 8-Page Shell + `lightweight-charts` บนหน้า Data Center (ไม่บังคับ White Theme / `tv.js`)
* **บัญชีเทรดที่ใช้ (ถาวร):** Pepperstone Demo `#5258778` (`Account.IsLive == false` เท่านั้น ไม่มีเงื่อนไขสวิตช์ไปบัญชีเงินจริง)
* **cTrader Desktop MCP:** เชื่อมต่ออยู่ที่ `http://127.0.0.1:9876/mcp/` ([`.mcp.json`](.mcp.json) · ตรวจด้วย [`tools/test_ctrader_mcp.py`](tools/test_ctrader_mcp.py))
* **Background Automation ที่รันอยู่:**
  1. `research/live_recorder_daemon.py` — 24/7 Watchdog คุม cTrader CLI เก็บตลาดสด (ตั้ง Autostart บน Windows Task Scheduler ชื่อ `AntigravityLiveRecorderWatchdog`)
  2. `research/live_status_sync.py --daemon` — รวมสถิติเทรด/ข้อมูลสด อัปเดต JSON ใน `docs/data/` และ Auto-commit/push ขึ้น GitHub Pages

---

## 2. คลังข้อมูลที่มีอยู่จริง (Data Asset Inventory)

| ประเภทข้อมูล | ที่จัดเก็บ | ปริมาณข้อมูลปัจจุบัน (16 พ.ย. 2026) | แหล่ง & สถานะ |
| :--- | :--- | :--- | :--- |
| **Live L2 DOM 25 ชั้น, Tick, Real Spread, Order Flow, Trades** | `%LOCALAPPDATA%\BacktestLab\live\<SYMBOL>\` *(Local Only ~95+ MB)* | • **BTCUSD:** ~13,084 แท่ง M1<br/>• **ETHUSD:** ~13,012 แท่ง M1<br/>• **XAUUSD:** ~11,184 แท่ง M1<br/>• **GOLD-PERP:** 7,171 แท่ง (Standby) | อัดสดต่อเนื่อง 24/7 ด้วย `LiveRecorder.cs` (ไม่ขึ้น Git ไฟล์ใหญ่, ซิงก์สรุปเข้า `data/live/` และ `docs/data/dc_*.json`) |
| **cTrader Historical Bars & Sessions** | ดึงผ่าน [`research/ctrader_mcp_client.py`](research/ctrader_mcp_client.py) + แคชใน `%LOCALAPPDATA%\BacktestLab\ctrader_cache\` | ย้อนหลัง M1 + Sessions จริง (`XAU 42,307` / `BTC 22,911` / `ETH 22,908` แท่งเมื่อ Merge แล้ว) | **เชื่อมต่อ Phase 1 แล้ว (`hybrid_data_merger.py`):** Merge บน UTC Timestamp + คัดกรองแถวเสีย/ซ้ำอัตโนมัติ (กรองแถวผี XAU `ticks=0` ออก 1,028 แถวแล้ว) |
| **ตลาดทองย้อนหลัง (Historical CSV)** | [`data/XAUUSD_2022_2026_Minute.csv`](data/) *(Local Only ~96.5 MB)* | 2022–2026 M1 | เก็บไว้เป็น Reference เท่านั้น (ไม่มี L2 DOM/Real Spread) |

### ตารางเปิด-ปิดตลาดจริงจาก cTrader (`get_symbol_sessions`)
* **XAUUSD (EST UTC-5 / EDT UTC-4):** หน้าหนาวเปิด `23:01 UTC` – ปิด `21:59 UTC` (พักเบรก Rollover 1 ชม. ช่วง `22:00–23:00 UTC` และสเปรดจริงพุ่ง ~2x จาก `0.093` ➔ `0.173` หลัง `21:00 UTC`); หน้าร้อนเร็วขึ้น 1 ชม. (`22:01`–`20:59 UTC`)
* **BTCUSD / ETHUSD:** เทรดต่อเนื่อง 24 ชม. มีพักระบบแค่ **2 นาที/วัน** (`21:59–22:01 UTC` หน้าหนาว)

---

## 3. สถานะผลงานพอร์ต Demo & โค้ดกลยุทธ์ปัจจุบัน
* **สถานะเทรดสดสะสม (`docs/data/truth_guard.json` ณ `19 Nov 2026 08:34 UTC`):**
  * **จำนวนไม้ปิดจริง:** `N = 412` ไม้ (ชนะ 168 / แพ้ 244 · Win Rate **40.8%**)
  * **Cumulative Net PnL / Balance:** Net **-\$129.26 USD** · Balance บัญชี cTrader จริง **\$115.67 USD** (Profit Factor **0.79**)
* **cBot Strategy & A/B Evaluation บน Demo `#5258778`:**
  * **Challenger `REGIME_ADAPTIVE_V5 v3`:** วิ่งทดสอบจริง 208 ไม้ (ชนะ 89 / แพ้ 119 · Net **-\$100.48 USD**, PF 0.68) ติด Emergency Bleed Guard ➔ **Auto-Rollback กลับไปใช้ Baseline `DOM_ABSORPTION v2` อัตโนมัติ** เรียบร้อยตามกฎ System Rules V5
  * **Baseline `DOM_ABSORPTION v2`:** 109 ไม้ (ชนะ 45 / แพ้ 64 · Net **+\$4.70 USD**, PF **1.04**)
* **บันทึกการตัดสินใจ & A/B Audit:** [`DECISION_LOG.md`](DECISION_LOG.md) + [`docs/data/v5_pipeline_state.json`](docs/data/v5_pipeline_state.json) + [`docs/data/demo_deployment_state.json`](docs/data/demo_deployment_state.json)
* **ผลวิจัย XAUUSD ล่าสุดบนข้อมูลสด (`tools/backtest_dom_live_grid.py` บน 7,295 แท่ง):**
  * `DOM_ABSORPTION_V2 + London/NY (08:00–21:00 UTC) + News Gate`: 78 ไม้ · WR 48.7% · PF **1.25** · Net **+\$35.48 USD** · Daily Win Rate **83.3%** (5/6 วัน)
  * `QuantExtremeReversal` (แชมป์ข้อมูลย้อนหลังเก่า): แพ้บนข้อมูลสด (**-\$16.30 USD**, PF 0.32) — เป็นหลักฐานชัดเจนเรื่อง Overfitting ของข้อมูลสังเคราะห์

---

## 4. โครงสร้างระบบเว็บและสคริปต์ (8-Page Portal & Codebase)
* **เว็บ 8 หน้า (`docs/`):**
  1. `index.html` (Overview) 2. `data-center.html` (Data Center) 3. `research-lab.html` (193 Papers + Quant Engines + Foundry + **Tab 5: Trading Condition Library V5 R2**) 4. `experiment-lab.html` (Backtest Comparator) 5. `intelligence.html` (Regime Matrix & Heatmap) 6. `improvement-audit.html` (Audit & Evolution Log) 7. `archive-system.html` (Transcript, Legacy Snapshot, Feedback Studio, Governance) 8. `database.html` (Unified Catalog)
* **Pattern Discovery Engine V5 Round 2 (`research/pattern_discovery/`):** สกัดจาก Tier 1 Live Microstructure + Tier 2 cTrader MTF (`m5/m15/h1/h4`) รวม `1,630` เงื่อนไข (`XAUUSD 565 · BTCUSD 646 · ETHUSD 419`) ผ่าน `VALIDATED_OOS` รวม **`165`** รูปแบบ (`XAU 66 · BTC 93 · ETH 6`) ซิงก์ลง [`trading_condition_library.json`](docs/data/trading_condition_library.json), [`pattern_discovery_state.json`](docs/data/pattern_discovery_state.json), [`TRADING_CONDITION_LIBRARY_REPORT.md`](TRADING_CONDITION_LIBRARY_REPORT.md) และหน้าเว็บ Page 3 `#patterns` แล้ว
* **ชุดตรวจสอบสุขภาพ:** `tools/verify_8page_ui.py` (ผ่าน 100%), `research/pattern_discovery/test_pattern_discovery.py` (8/8 ผ่าน), และ `research/run_institutional_v4_test_suite.py` (รวม Phase 1, Phase 2 & Phase 3 Unit Tests ผ่าน; เหลือ Bug Windows file lock ใน `tearDown` ของ `test_attribution_matrix_feedback.py`)

---

## 5. แผนที่วิวัฒนาการระบบ V5 (Phase 1–4 Completed)
1. **✅ [Phase 1 เสร็จแล้ว]** เชื่อม [`ctrader_mcp_client.py`](research/ctrader_mcp_client.py) + [`hybrid_data_merger.py`](research/hybrid_data_merger.py) พร้อม V5 Data Sanitizer (ตัดแถวผี `ticks=0` / `NaN` อัตโนมัติ และแก้ไข `build_data_center.py` + `live_status_sync.py` แล้ว)
2. **✅ [Phase 2 เสร็จแล้ว]** [`session_regime_forensics.py`](research/session_regime_forensics.py) + [`regime_strategy_matrix.json`](docs/data/regime_strategy_matrix.json) แยกวิเคราะห์ 7 โซน (`ASIA`, `ASIA_TO_LONDON`, `LONDON`, `LONDON_TO_NY`, `NY`, `NY_TO_CLOSE`, `OVERNIGHT`) + ตรวจ OOS (60/40) แบบไม่ล็อกเลขตายตัว + รัน Blowup Forensics (`FORENSIC_ZERO_SL`) บันทึกจุดแตกหักแทนการแบนถาวร
3. **✅ [Phase 3 เสร็จแล้ว]** [`v5_multi_agent_pipeline.py`](research/v5_multi_agent_pipeline.py) + [`demo_deployment_manager.py`](research/demo_deployment_manager.py) + [`DECISION_LOG.md`](DECISION_LOG.md) ขับเคลื่อน 4 Agents ส่งงานต่อกัน พร้อม Deploy `REGIME_ADAPTIVE_V5 v3` บน Demo `#5258778` และ Auto-Rollback Guard กลับ V2 อัตโนมัติ
4. **✅ [Phase 4 เสร็จแล้ว]** เว็บ 8 หน้าโหมด **4 ขั้นตอนหลัก V5** ([`index.html`](docs/index.html) / [`shell.js`](docs/assets/shell.js)), ตาราง **7-Zone Situational Matrix, Zero-SL Blowup Forensics & Non-Banning Memory** บน [`intelligence.html`](docs/intelligence.html), และ **Demo A/B Rollback + Truth Guard V5** บน [`improvement-audit.html`](docs/improvement-audit.html) ซิงก์ครบ 100%
