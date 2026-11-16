# 🧭 DECISION LOG & HUMAN DECISION GATE (`cbot-atgvt` V5)

> เอกสารนี้จัดทำและอัปเดตอัตโนมัติโดย **Agent 4 (`Audit, Demo Deploy & Reporter Agent`)** 
> ตามกฎกลาง [`GEMINI.md`](GEMINI.md) เพื่อบันทึกประวัติการปรับกลยุทธ์บน Demo (`#5258778`), เกณฑ์ A/B Rollback อัตโนมัติ, และประเด็นที่รอ **Human Decide**

---

## 1. Human-in-the-Loop Decision Gate (รายการรอ/สรุปให้ Human พิจารณา)

| ID | หัวข้อ / จุดตัดสินใจ | สถานะ | เหตุผล & Trade-Off (ตัวเลขจริง) | คำสั่ง Human / ทางเลือก |
| :--- | :--- | :--- | :--- | :--- |
| **DEC-V5-001** | ใช้กฎกลาง System Rules V5 (`GEMINI.md`) แทน V4 | ✅ APPROVED | ปลดล็อก Demo Sanitizer, ยกเลิกรอ N>=500, เพิ่ม 7-Zone & Zero-SL Forensics | ใช้งานแล้ว (ห้าม AI แก้กฎ 5 หมวดโดยพลการ) |
| **DEC-V5-002** | Phase 3 Autonomous Upgrade บน Demo `#5258778`: `DOM_ABSORPTION v2` ➔ `REGIME_ADAPTIVE_V5 v3` | 🟢 DEPLOYED (AUTO-ROLLBACK ARMED) | ผล Phase 2 OOS ผ่าน `52/91` ช่อง across XAU/BTC/ETH และแก้จุดตาย Spread Spike ช่วง Transition (`475` Forensic cases) | AI ทดสอบเดินหน้าอัตโนมัติบน Demo และจะ **Rollback กลับ V2 ทันที** หาก Expectancy/PF ต่ำกว่า Baseline หลังครบ N>=8 ไม้ (หรือแพ้หนัก >= -12 USD) |
| **DEC-V5-003** | ก้าวเข้าสู่ **Phase 4** (ปรับเว็บ 8 หน้าเป็น 4 ขั้นตอนหลัก & แสดงตาราง 7-Zone Situational Transparency เต็มรูปแบบ) | ⏳ AWAITING HUMAN GO | โครงสร้าง Backend Phase 1–3 พร้อมครบ (`Hybrid Merger`, `7-Zone OOS + Forensics`, `4-Agent Pipeline + Auto-Rollback`) | สั่ง **"ไปต่อ Phase 4"** เมื่อพร้อมอัปเกรด UI เว็บ 8 หน้า |

---

## 2. Parallel Demo A/B Comparison (`#5258778` Live Forward)

* **Updated (UTC):** `2026-11-16T16:38:36.017423+00:00`
* **Active C# Strategy on Demo `#5258778`:** `REGIME_ADAPTIVE_V5` (Version `3`) · **Last Action:** `DEPLOYED_V3_REGIME_ADAPTIVE_V5`
* **A/B Verdict:** `COLLECTING_PARALLEL_AB` — Forward Demo verification in progress (0/8 closed trades on REGIME_ADAPTIVE_V5). Baseline (DOM_ABSORPTION) N=109, Net=+4.70 USD.
* **Cumulative Demo Account (`truth_guard.json`):** Balance `$120.76 USD` · Closed `N=125` · Net `+20.76 USD` · PF `1.17`

| Model Variant | Status on Demo `#5258778` | Closed Trades | Win Rate | Profit Factor | Expectancy / Trade | Net PnL (USD) | Max DD (USD) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Baseline: `DOM_ABSORPTION v2`** | Rollback Snapshot Saved | 109 | 41.3% | 1.04 | +0.0431 | +4.70 | 31.66 |
| **Challenger: `REGIME_ADAPTIVE_V5 v3`** | Active Forward Candidate | 0 | 0.0% | 0.00 | +0.0000 | +0.00 | 0.00 |

---

## 3. Demo Deployment & Rollback History Log

| Timestamp (UTC) | Action | From ➔ To | Rationale / Hypothesis |
| :--- | :--- | :--- | :--- |
| `2026-11-16T16:38:36` | `DEPLOY_V3_ON_DEMO` | `DOM_ABSORPTION v2` ➔ `REGIME_ADAPTIVE_V5 v3` | Phase 2 OOS Matrix proved 7-zone Regime/ATR/Zone-End adaptation reduces rollover & transition losses vs static DOM_ABSORPTION V2. |
