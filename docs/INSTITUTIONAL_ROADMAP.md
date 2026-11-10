# 🏛️ INSTITUTIONAL GOVERNANCE & PHASED EXECUTION ROADMAP (ARCHITECTURE V4)

**Project:** Unified Multi-Agent Quant Platform (`cbot-atgvt`)  
**Target Environment:** Pepperstone Demo Account `#5258778` (Phase 0–2 Sandbox) & Verified Live Transition (Phase 3)  
**Execution Paradigm:**  
```
Observe ➔ Understand ➔ Research ➔ Build ➔ Prove ➔ Select ➔ Execute ➔ Analyze ➔ Learn ➔ Evolve
```
*"One Market, Multiple Regimes, Multiple Strategies, One Intelligent Decision System."*

---

## 📌 สรุปแผนผังยุทธศาสตร์ 4 ระยะ (Phased Phased Roadmap V4)

```
[ Phase 0: ตอนนี้ ] ──► [ Phase 1: สัปดาห์ 1–2 ] ──► [ Phase 2: สัปดาห์ 3–8 ] ──► [ Phase 3: หลังจากนั้น ]
• ซ่อม LiveRecorder      • Market Intelligence V4    • Adaptive Strategy Library  • ตรวจเกณฑ์ Audit Checklist
• ระบบ Heartbeat 15s     • Rule Classification (1-3) • Dynamic Switching Engine   • เริ่มเงินจริงล็อตเล็ก (0.01 lot)
• แจ้งเตือนค้าง >180s    • Risk Governor V4          • Demo Quarantine (#5258778) • Stealth RAM SL + Hard Stop
• Watchdog Multi-Market  • Daily Flat (21:45 UTC)    • สะสม N >= 500 ไม้        • Supabase Owner Auth OTP
```

---

## 🛠️ Phase 0: ตอนนี้ (Active) — ซ่อม LiveRecorder & ระบบแจ้งเตือนการหยุดเก็บ

### 1. การแก้ไขในตัวบันทึกข้อมูล C# cBot ([LiveRecorder.cs](file:///home/antigravity/cbot/BacktestLab/LiveRecorder.cs))
- **Live Heartbeat Pulse (ทุก 15 วินาที):** เขียนไฟล์ `heartbeat.json` แสดงสถานะ `RECORDING_ACTIVE`, เวลาที่ได้รับ tick ล่าสุด, และสเปรดปัจจุบัน
- **Stall Alert & Auto-Healing (หยุดนิ่ง > 120 วินาที):**
  หากตลาดเปิดอยู่ (Crypto 24/7, XAUUSD อาทิตย์ 22:00 ถึง ศุกร์ 21:55 UTC) แล้วไม่มี tick เข้ามาเกิน 120 วินาที ระบบจะ:
  1. พิมพ์คำเตือนระดับวิกฤตลงใน cTrader Log ทันที
  2. เขียนไฟล์บันทึกอุบัติการณ์ `stall_alert.json`
  3. ส่งการแจ้งเตือนอัตโนมัติผ่าน Webhook หากตั้งค่าไว้
  4. สั่ง Flush บัฟเฟอร์และกู้คืนการเชื่อมต่อ Stream อัตโนมัติ

### 2. ตัวตรวจจับอิสระระดับระบบ ([live_recorder_watchdog.py](file:///home/antigravity/research/live_recorder_watchdog.py))
- ตรวจสอบความสดของข้อมูลใน `data/live/` ทุกสินทรัพย์ (`BTCUSD`, `ETHUSD`, `XAUUSD`, `GOLD-PERP`)
- อัปเดตสถานะขึ้นแดชบอร์ด [`docs/data/watchdog_status.json`](file:///home/antigravity/docs/data/watchdog_status.json)

---

## 🌙 Phase 1: สัปดาห์ 1–2 — สถาปัตยกรรม V4, Market Intelligence & Risk Governor V4

### 1. กฎเหล็กและการจัดหมวดหมู่ 3 ระดับ ([rule_classification.py](file:///home/antigravity/research/rule_classification.py))
- **Tier 1 (Immutable Hard):** ห้าม Lookahead, ห้าม Data Leakage, บังคับ Stop Loss ทุกไม้, ห้าม Martingale/Grid, บังคับ **Daily Flat ที่ 21:45 UTC**, กักบริเวณในเดโม
- **Tier 2 (Adaptive Rules):** พารามิเตอร์ที่ AI เสนอและปรับจูนได้ภายใต้กรอบที่กำหนด (SL, RR, Dynamic Spread, News Blackout, Session Filter)
- **Tier 3 (Open Research Hypotheses):** คลังวิจัยเปิดกว้างสำหรับทุกตระกูลกลยุทธ์ บันทึกทุกการทดลองอย่างเป็นระบบ

### 2. Market Intelligence Engine ([market_intelligence_engine.py](file:///home/antigravity/research/market_intelligence_engine.py))
- วิเคราะห์ 6 แกนสำคัญ: Time Context, News Proximity, 13 Market Regimes, Microstructure (DOM Imbalance, Delta, CVD, Absorption), Price Behavior (Swing points, Rejection), และ **Context Fingerprint**

### 3. Institutional Risk Governor V4 ([risk_governor.py](file:///home/antigravity/research/risk_governor.py))
- **Portfolio Daily Loss Limit:** ตัดการเทรดทั้งพอร์ตเมื่อแตะ -$10.00 USD
- **Symbol Consecutive Loss Cutoff:** หยุดสินทรัพย์นั้นเมื่อแพ้ติดกัน 2 ไม้
- **Central Daily Flat Mandate:** บังคับปิดทุกสถานะก่อน 21:45 UTC ห้ามถือข้ามคืนเด็ดขาด
- **Spread Ceiling:** สเปรดถ่างเกินเกณฑ์ห้ามเข้าออเดอร์

---

## 🧪 Phase 2: สัปดาห์ 3–8 — การพัฒนาตัวเองบนบัญชีเดโมเท่านั้น (Demo-Only Sandbox)

### 1. คลังกลยุทธ์ปรับตัวได้ (Adaptive Strategy Library)
- **STR-001:** Multi-Timeframe Trend Following
- **STR-002:** Session VWAP Mean Reversion
- **STR-003:** Liquidity Sweep & Stop Hunt Reversal
- **STR-004:** Volatility Expansion Breakout
- **STR-005:** Post-News Directional Reaction
- **STR-006:** L2 DOM Order Flow Imbalance
- **STR-007:** Extreme Volatility Stretch Reversal
- **STR-008:** Session Opening Range Expansion
- **STR-009:** Capital Defense & No-Trade Mode

### 2. ระบบคัดเลือกและสลับกลยุทธ์พลวัต ([adaptive_strategy_selector.py](file:///home/antigravity/research/adaptive_strategy_selector.py))
- คำนวณ Suitability Score (0–100) และใช้ **Hysteresis (หน่วงเวลาขั้นต่ำ 15 แท่ง)** เพื่อป้องกัน Whipsaw
- มีกลไก **Position Preservation** รักษาออเดอร์เดิมที่กำลังเปิดอยู่ ไม่ทอดทิ้งสถานะกลางคัน

### 3. แดมอนวิเคราะห์ตลาดสดและพัฒนาต่อเนื่อง 24/7 ([event_driven_intelligence_daemon.py](file:///home/antigravity/research/event_driven_intelligence_daemon.py))
- รันในเบื้องหลังแบบ Event-Driven อัปเดตข้อมูลสดทุก 30 วินาทีเข้าสู่ [`docs/data/live_market_intelligence.json`](file:///home/antigravity/docs/data/live_market_intelligence.json)

### 4. การสะสมสถิติบนเดโม
- รันบน **Pepperstone Demo `#5258778`** เท่านั้น (`Account.IsLive == false`)
- สะสมจำนวนไม้เทรดจริงให้ครบ **$N \ge 500$ ถึง $1,200$ ไม้**

---

## 💎 Phase 3: หลังจากนั้น — เริ่มเงินจริงด้วยล็อตเล็กเมื่อผ่านเกณฑ์ (Live Micro-Lot Gate)

### เกณฑ์การตรวจสอบขั้นเด็ดขาด (Fail-Closed Checklist):
1. [ ] จำนวนไม้เทรดสะสมบนเดโม $N \ge 500$ ไม้
2. [ ] ค่า Sharpe Ratio สะสม $\ge 1.50$ (SE $\le \pm 0.15$)
3. [ ] Profit Factor รวม $\ge 1.60$
4. [ ] Daily Win Rate $\ge 80.0\%$
5. [ ] Drawdown สูงสุดของพอร์ต $\le 8.0\%$
6. [ ] ผ่าน Monte Carlo 1,000 รอบ โอกาสล้างพอร์ต $\le 0.5\%$
7. [ ] ไม่มีเหตุการณ์ Unhandled Slippage หรือข้อผิดพลาดทางเทคนิคข้ามคืน

### ข้อกำหนดเมื่อเริ่มเงินจริง (Live Execution Protocol):
- **ขนาดคำสั่งเริ่มต้น:** เริ่มต้นที่ **0.01 lot** เท่านั้น
- **การอนุมัติ:** ต้องได้รับการยืนยันรหัส OTP / Supabase Owner Auth จากเจ้าของพอร์ตก่อนสวิตช์
- **Emergency Circuit Breaker:** ติดตั้ง Hard Broker Disaster SL เสมอ ควบคู่กับ Stealth RAM SL
