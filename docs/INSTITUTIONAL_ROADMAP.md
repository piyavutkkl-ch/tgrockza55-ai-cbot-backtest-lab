# 🏛️ INSTITUTIONAL GOVERNANCE & PHASED EXECUTION ROADMAP

**Project:** Unified Multi-Agent Quant Platform (`cbot-atgvt`)  
**Target Environment:** Pepperstone Demo Account `#5258778` (Phase 0–2) & Verified Live Transition (Phase 3)  
**Status:** In Active Execution  

---

## 📌 สรุปแผนผังยุทธศาสตร์ 4 ระยะ (Executive Phased Roadmap)

```
[ Phase 0: ตอนนี้ ] ──► [ Phase 1: สัปดาห์ 1–2 ] ──► [ Phase 2: สัปดาห์ 3–8 ] ──► [ Phase 3: หลังจากนั้น ]
• ซ่อม LiveRecorder      • ลูปเทรนทุกคืน (Nightly)   • รันเดโม 100% อิสระ         • ตรวจเกณฑ์ Audit Checklist
• ระบบ Heartbeat 15s     • Champion / Challenger     • ปลอดความเสี่ยงเงินจริง      • เริ่มเงินจริงล็อตเล็ก (0.01 lot)
• แจ้งเตือนค้าง >180s    • Institutional Risk Governor • สะสม N >= 500 ไม้        • Stealth RAM SL + Hard Stop
```

---

## 🛠️ Phase 0: ตอนนี้ (Active) — ซ่อม LiveRecorder & ระบบแจ้งเตือนการหยุดเก็บ

### 1. การแก้ไขในตัวบันทึกข้อมูล C# cBot ([LiveRecorder.cs](file:///home/antigravity/cbot/BacktestLab/LiveRecorder.cs))
- **Live Heartbeat Pulse (ทุก 15 วินาที):**
  เขียนไฟล์ `heartbeat.json` แสดงสถานะ `RECORDING_ACTIVE`, เวลาที่ได้รับ tick ล่าสุด, และสเปรดปัจจุบัน
- **Stall Alert & Auto-Healing (หยุดนิ่ง > 120 วินาที):**
  หากตลาดเปิดอยู่ (Crypto 24/7, XAUUSD อาทิตย์ 22:00 ถึง ศุกร์ 21:55 UTC) แล้วไม่มี tick เข้ามาเกิน 120 วินาที ระบบจะ:
  1. พิมพ์คำเตือนระดับวิกฤตลงใน cTrader Log ทันที
  2. เขียนไฟล์บันทึกอุบัติการณ์ `stall_alert.json`
  3. ส่งการแจ้งเตือนอัตโนมัติผ่าน Webhook (Discord / Telegram / Line) หากตั้งค่า URL ไว้
  4. สั่ง Flush บัฟเฟอร์และกู้คืนการเชื่อมต่อ Stream อัตโนมัติ

### 2. ตัวตรวจจับอิสระระดับระบบ ([live_recorder_watchdog.py](file:///home/antigravity/research/live_recorder_watchdog.py))
- ตรวจจับความสดของข้อมูลใน `data/live/` และ `%LOCALAPPDATA%/BacktestLab/live/` ทุกสินทรัพย์ (`BTCUSD`, `ETHUSD`, `XAUUSD`, `GOLD-PERP`)
- หากพบการหยุดเก็บข้อมูลเกิน 180 วินาที จะอัปเดตสถานะขึ้นแดชบอร์ด [`docs/data/watchdog_status.json`](file:///home/antigravity/docs/data/watchdog_status.json) และแสดงป้ายเตือนสีแดงทันที

---

## 🌙 Phase 1: สัปดาห์ 1–2 — ลูปเทรนทุกคืน, Champion/Challenger & Risk Governor

### 1. ลูปเทรนอัตโนมัติทุกคืน ([nightly_evolution_daemon.py](file:///home/antigravity/research/nightly_evolution_daemon.py))
- รันเวลา 23:00 UTC (หรือหลังจบวันเทรด) เพื่อนำข้อมูล Tick, DOM Imbalance, และ Order Flow สดล่าสุด 7 วันย้อนหลังมาเทรนโมเดลรอบใหม่

### 2. ระบบประลองโมเดล Champion vs Challenger ([champion_challenger_engine.py](file:///home/antigravity/research/champion_challenger_engine.py))
- **Champion:** โมเดลที่กำลังรันในปัจจุบันบนเซิร์ฟเวอร์
- **Challengers:** โมเดลกลายพันธุ์ที่ถูกสร้างขึ้นจากการปรับจูนพารามิเตอร์รอบกลางคืน
- **เกณฑ์การเลื่อนขั้น (Promotion Rules):**
  1. Daily Win Rate ต้อง $\ge 80\% - 100\%$ (ห้ามแพ้เละเทะในวันใดวันหนึ่ง)
  2. Profit Factor ของ Challenger ต้องสูงกว่า Champion อย่างน้อย $+5\%$
  3. Max Drawdown ต้องไม่แย่ไปกว่า Champion
  4. ผ่านการทดสอบ Out-of-Sample (OOS) บนข้อมูลสดจริงไม่น้อยกว่า 10–20 ไม้

### 3. ผู้คุมกฎความเสี่ยงสถาบัน ([risk_governor.py](file:///home/antigravity/research/risk_governor.py))
- **Portfolio Daily Loss Limit:** หากพอร์ตรวมติดลบแตะ -$10.00 USD ในวันเดียว ระบบจะตัดการเทรดทุกตัวทันที
- **Max Consecutive Losses:** หากสินทรัพย์ใดแพ้ติดกัน 2 ไม้ในวันนั้น จะสั่งหยุดสินทรัพย์นั้นทันที
- **Daily Profit Target Guard:** ล็อกกำไรและหยุดเทรดเมื่อบวกแตะ +$10 ถึง +$15 USD
- **Spread Ceiling:** สเปรดถ่างเกินเกณฑ์ห้ามเข้าออเดอร์เด็ดขาด (XAU > 0.25p, BTC > $35, ETH > $3.5, GOLD-PERP > $2.2)
- **News Void Gate:** หยุดรับออเดอร์ 30 นาทีก่อนข่าว และ 60 นาทีหลังข่าวระดับ HIGH / EXTREME

---

## 🧪 Phase 2: สัปดาห์ 3–8 — การพัฒนาตัวเองบนบัญชีเดโมเท่านั้น (Demo-Only Sandbox)

- **กักบริเวณความปลอดภัย 100%:** รันบนบัญชีเดโม **Pepperstone Demo `#5258778`** เท่านั้น
- **Security Assert:** ระบบมีโค้ดตรวจสอบ `Account.IsLive == false` เสมอในเฟสนี้ หากตรวจพบว่าเป็นเงินจริง ระบบจะปฏิเสธการเทรดทันที
- **เป้าหมายหลัก:**
  - สะสมจำนวนไม้เทรดจริงจากตลาดสดให้ครบ **$N \ge 500$ ถึง $1,200$ ไม้** เพื่อให้เกิดความน่าเชื่อถือทางสถิติ (Statistical Power)
  - วัดค่า Slippage จริง, Latency ในการส่งคำสั่ง, และความแม่นยำของคำสั่ง Take Profit / Stop Loss ในหน่วยความจำ (Quantum Stealth RAM SL)

---

## 💎 Phase 3: หลังจากนั้น — เริ่มเงินจริงด้วยล็อตเล็กเมื่อผ่านเกณฑ์ (Live Micro-Lot Gate)

### เกณฑ์การตรวจสอบขั้นเด็ดขาด (Fail-Closed Checklist):
1. [ ] จำนวนไม้เทรดสะสมบนเดโม $N \ge 500$ ไม้
2. [ ] ค่า Sharpe Ratio สะสม $\ge 1.50$ (SE $\le \pm 0.15$)
3. [ ] Profit Factor รวม $\ge 1.60$
4. [ ] Daily Win Rate $\ge 80.0\%$
5. [ ] Drawdown สูงสุดของพอร์ต $\le 8.0\%$
6. [ ] ไม่มีเหตุการณ์ Unhandled Slippage หรือข้อผิดพลาดทางเทคนิคข้ามคืน

### ข้อกำหนดเมื่อเริ่มเงินจริง (Live Execution Protocol):
- **ขนาดคำสั่งเริ่มต้น:** เริ่มต้นที่ **0.01 lot** เท่านั้น
- **การอนุมัติ:** ต้องได้รับการยืนยันรหัส OTP / Supabase Owner Auth จากเจ้าของพอร์ตก่อนสวิตช์
- **Emergency Circuit Breaker:** ติดตั้ง Hard Broker Disaster SL เสมอ ควบคู่กับ Stealth RAM SL
