# [STRAT-075] Statistically validated lead-lag networks and inventory prediction in the foreign exchange market
**หมวดหมู่:** 🏎️ หมวดที่ 8: ความสัมพันธ์ตัวนำ-ตัวตาม (Lead-Lag Microstructure) และ Latency Arbitrage | **ประเภทกลยุทธ์:** `Cross-Market Lead-Lag & Preemptive Arbitrage`
**อ้างอิงเปเปอร์:** [`1609.04640`](https://arxiv.org/html/1609.04640) | **ผู้แต่ง:**  (26 July, 2)

## 🔗 ลิงก์เอกสารต้นฉบับ
- 🌐 **อ่านเวอร์ชัน HTML เต็ม:** [https://arxiv.org/html/1609.04640](https://arxiv.org/html/1609.04640) *(ไม่ต้องดาวน์โหลด ไม่ติด Limit)*
- 📥 **ดาวน์โหลด PDF:** [https://arxiv.org/pdf/1609.04640.pdf](https://arxiv.org/pdf/1609.04640.pdf)

---

## 💰 1. ทำไมถึงได้กำไร? (Alpha & Profit Mechanism)
เก็บเกี่ยวผลประโยชน์จากความหน่วงของการกระจายข้อมูลระหว่างเซิร์ฟเวอร์ (Information Propagation Latency)

## 🟢 2. เงื่อนไขจุดเข้า (Entry Trigger)
ติดตามข้อมูล Tick จากตลาดผู้นำ (Leader เช่น Binance Futures หรือ CME Gold) เทียบกับตลาดผู้ตาม (Laggard เช่น โบรกเกอร์ cTrader) หาก Leader ขยับเกินเกณฑ์ Threshold และยืนยันด้วย Hayashi-Yoshida Correlation > 0.8 ยิง Market Order ในตลาด Laggard ดักหน้าทันที

## 🔴 3. เงื่อนไขจุดออก (Exit Trigger / TP / SL)
ปิดสถานะทันทีเมื่อราคาตลาด Laggard ขยับตามมาทัน (Catch-up completed ภายใน 500ms ถึง 3 วินาที) หรือเมื่อพ้นเวลา 5 วินาที

## 💎 4. จุดเด่น (Strengths)
- อัตราการชนะ (Win Rate) สูงที่สุดในบรรดากลยุทธ์ทั้งหมด (มักสูงกว่า 70-85%) หากสามารถทำความเร็วได้

## ⚠️ 5. จุดอ่อน (Weaknesses)
- ต้องการโครงสร้างพื้นฐานระดับสูง (VPS ใกล้ Server โบรกเกอร์, C# Low Latency API)

## 🚨 6. สิ่งที่ต้องเฝ้าระวังอย่างยิ่ง (Risk Factors & Cautions)
- โบรกเกอร์อาจมีมาตรการ Anti-Arbitrage หรือปฏิเสธคำสั่ง (Requote / Slippage)

## 🧩 7. การทำงานร่วมกับกลยุทธ์อื่น (Compatibility & Synergy)
- สามารถทำงานร่วมกับหมวด: 02_order_flow_imbalance, 05_hawkes_and_event_clustering, 12_position_sizing_and_risk

---
## 📌 บทคัดย่อของงานวิจัยต้นฉบับ
> 

---
*จัดทำเป็นฐานข้อมูลกลยุทธ์เชิงปริมาณสำหรับ cbot-atgvt พร้อมสำหรับการแปลงเป็นระบบเทรดและเผยแพร่บนเว็บ*