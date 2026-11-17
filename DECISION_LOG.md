# 🧭 DECISION LOG & HUMAN DECISION GATE (`cbot-atgvt` V5)

> เอกสารนี้จัดทำและอัปเดตอัตโนมัติโดย **Agent 4 (`Audit, Demo Deploy & Reporter Agent`)** 
> ตามกฎกลาง [`GEMINI.md`](GEMINI.md) เพื่อบันทึกประวัติการปรับกลยุทธ์บน Demo (`#5258778`), เกณฑ์ A/B Rollback อัตโนมัติ, และประเด็นที่รอ **Human Decide**

---

## 1. Human-in-the-Loop Decision Gate (รายการรอ/สรุปให้ Human พิจารณา)

| ID | หัวข้อ / จุดตัดสินใจ | สถานะ | เหตุผล & Trade-Off (ตัวเลขจริง) | คำสั่ง Human / ทางเลือก |
| :--- | :--- | :--- | :--- | :--- |
| **DEC-V5-001** | ใช้กฎกลาง System Rules V5 (`GEMINI.md`) แทน V4 | ✅ APPROVED | ปลดล็อก Demo Sanitizer, ยกเลิกรอ N>=500, เพิ่ม 7-Zone & Zero-SL Forensics | ใช้งานแล้ว (ห้าม AI แก้กฎ 5 หมวดโดยพลการ) |
| **DEC-V5-002** | Phase 3 Autonomous Upgrade บน Demo `#5258778`: `DOM_ABSORPTION v2` ➔ `REGIME_ADAPTIVE_V5 v3` | 🟢 DEPLOYED (AUTO-ROLLBACK ARMED) | ผล Phase 2 OOS ผ่าน `52/91` ช่อง across XAU/BTC/ETH และแก้จุดตาย Spread Spike ช่วง Transition (`475` Forensic cases) | AI ทดสอบเดินหน้าอัตโนมัติบน Demo และจะ **Rollback กลับ V2 ทันที** หาก Expectancy/PF ต่ำกว่า Baseline หลังครบ N>=8 ไม้ (หรือแพ้หนัก >= -12 USD) |
| **DEC-V5-003** | ก้าวเข้าสู่ **Phase 4** (ปรับเว็บ 8 หน้าเป็น 4 ขั้นตอนหลัก & แสดงตาราง 7-Zone Situational Transparency เต็มรูปแบบ) | ✅ COMPLETED | อัปเกรด Shell 7-Zone Header, Overview 4-Stage Loop, Intelligence 7-Zone & Zero-SL Forensics, และ Audit Demo A/B + Truth Guard V5 เรียบร้อย | ใช้งานแล้ว (พร้อมรันเก็บผลเทียบ V3 vs V2 บน Demo `#5258778`) |

---

## 2. Parallel Demo A/B Comparison (`#5258778` Live Forward)

* **Updated (UTC):** `2026-11-17T05:42:35.667541+00:00`
* **Active C# Strategy on Demo `#5258778`:** `DOM_ABSORPTION` (Version `2`) · **Last Action:** `NONE`
* **A/B Verdict:** `AUTO_ROLLBACK` — REGIME_ADAPTIVE_V5 underperformed DOM_ABSORPTION over 61 Demo trades (Exp -0.128 vs +0.043, PF 0.89 vs 1.04) -> Auto-Rollback to V2.
* **Cumulative Demo Account (`truth_guard.json`):** Balance `$106.16 USD` · Closed `N=213` · Net `+6.16 USD` · PF `1.02`

| Model Variant | Status on Demo `#5258778` | Closed Trades | Win Rate | Profit Factor | Expectancy / Trade | Net PnL (USD) | Max DD (USD) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Baseline: `DOM_ABSORPTION v2`** | Rollback Snapshot Saved | 109 | 41.3% | 1.04 | +0.0431 | +4.70 | 31.66 |
| **Challenger: `REGIME_ADAPTIVE_V5 v3`** | Active Forward Candidate | 61 | 47.5% | 0.89 | -0.1275 | -7.78 | 23.45 |

---

## 3. Demo Deployment & Rollback History Log

| Timestamp (UTC) | Action | From ➔ To | Rationale / Hypothesis |
| :--- | :--- | :--- | :--- |
| `2026-11-16T16:38:36` | `DEPLOY_V3_ON_DEMO` | `DOM_ABSORPTION v2` ➔ `REGIME_ADAPTIVE_V5 v3` | Phase 2 OOS Matrix proved 7-zone Regime/ATR/Zone-End adaptation reduces rollover & transition losses vs static DOM_ABSORPTION V2. |
| `2026-11-16T18:50:30` | `AUTO_ROLLBACK_TO_V2` | `REGIME_ADAPTIVE_V5 v3` ➔ `DOM_ABSORPTION v2` | REGIME_ADAPTIVE_V5 underperformed DOM_ABSORPTION over 10 Demo trades (Exp -0.605 vs +0.043, PF 0.53 vs 1.04) -> Auto-Rollback to V2. |
