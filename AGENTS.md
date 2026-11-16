# 🤖 Agent Operating Instructions (`cbot-atgvt`)

AI Agents ทุกตัว (Antigravity, Gemini, Claude, Subagents และ Swarms) ที่ทำงานใน Repository นี้ **ต้องอ่านเอกสารหลัก 3 ไฟล์นี้ก่อนแก้ไขโค้ดหรือกลยุทธ์ทุกครั้ง**:

1. **[`GEMINI.md`](GEMINI.md)** — **กฎกลางของโปรเจกต์ 5 หมวด (System Rules V5)** และโปรโตคอลการตรวจสอบความขัดแย้งก่อนแก้ไข *(ห้าม AI แก้ไขกฎหลัก 5 หมวดเองโดยไม่ได้รับการอนุมัติจาก Human)*
2. **[`CURRENT_STATE_MAP.md`](CURRENT_STATE_MAP.md)** — **แผนที่สถานะระบบปัจจุบัน**: บัญชี Demo, คลังข้อมูลสดเทียบ cTrader API, ผลงานจริง, บอท/Daemon ที่กำลังรัน, และโครงสร้างเว็บ 8 หน้าบน `piyavutkkl-ch`
3. **[`FUTURE_STATE_MAP.md`](FUTURE_STATE_MAP.md)** — **แผนที่สถาปัตยกรรมเป้าหมาย**: Hybrid cTrader+Live Merger, Regime-Matched Library, Session/Transition R&D และ Multi-Agent Pipeline + Human Decision Gate

> **Repository Context Rule:** ความจำ ข้อค้นพบ และการตัดสินใจต้องบันทึกไว้ใน Repo เสมอ (ดูบันทึกการตัดสินใจ & Demo A/B Log ที่ [`DECISION_LOG.md`](DECISION_LOG.md)) · สำหรับกฎการเขียนโค้ด C# cBot และ `ctrader-cli` ดูเพิ่มเติมใน [`CLAUDE.md`](CLAUDE.md)
