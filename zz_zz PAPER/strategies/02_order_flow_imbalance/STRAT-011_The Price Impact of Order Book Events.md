# [STRAT-011] The Price Impact of Order Book Events
**หมวดหมู่:** 📊 02_order_flow_imbalance | **ประเภทกลยุทธ์:** `Order Flow Imbalance (OFI) & Price Impact`
**อ้างอิงเปเปอร์:** [`1011.6402v3`](https://arxiv.org/html/1011.6402v3) | **ผู้แต่ง:** Rama Cont, Arseniy Kukanov, Sasha Stoikov (2010-11-29)

## 🔗 ลิงก์เอกสารต้นฉบับ
- 🌐 **อ่านเวอร์ชัน HTML เต็ม:** [https://arxiv.org/html/1011.6402v3](https://arxiv.org/html/1011.6402v3) *(ไม่ต้องดาวน์โหลด ไม่ติด Limit)*
- 📥 **ดาวน์โหลด PDF:** [https://arxiv.org/pdf/1011.6402v3.pdf](https://arxiv.org/pdf/1011.6402v3.pdf)

---

## 💰 1. ทำไมถึงได้กำไร? (Alpha & Profit Mechanism)
เป็นดัชนีวัดปริมาณเงินจริงที่กำลังซัดเข้ามาในตลาด (Linear Price Impact) ราคาจำเป็นต้องเคลื่อนที่ตามแรงซื้อขายสุทธิเพื่อหาสมดุลใหม่ตามกฎสภาพคล่อง

## 🟢 2. เงื่อนไขจุดเข้า (Entry Trigger)
เมื่อค่าแรงกดดันคำสั่งซื้อขายสุทธิ (Cumulative OFI) พุ่งทะลุ +2.0 Standard Deviations (สำหรับ Buy) หรือต่ำกว่า -2.0 SD (สำหรับ Sell) ควบคู่กับสัดส่วน Bid/Ask Volume Imbalance ที่ระดับ Top of Book > 2.5:1 ส่งคำสั่ง Aggressive Market Order หรือ Ioc Limit Order ตามทิศทางแรงกดดัน

## 🔴 3. เงื่อนไขจุดออก (Exit Trigger / TP / SL)
ปิดสถานะเมื่อค่า OFI เริ่มชะลอตัวและเกิดสัญญาณ Liquidity Replenishment (มีคำสั่งฝั่งตรงข้ามเข้ามาเติมใน Queue) หรือเมื่อกำไรถึงระยะ 2.0x Spread หรือครบ 30 วินาที

## 💎 4. จุดเด่น (Strengths)
- ให้สัญญาณแม่นยำสูงมากในระดับเสี้ยววินาที ไม่มีอาการ Lag เหมือนแท่งเทียน จับจังหวะสถาบันเข้ากวาดสภาพคล่องได้อย่างชัดเจน

## ⚠️ 5. จุดอ่อน (Weaknesses)
- ระยะเวลาถือสั้นมาก (Ultra High Frequency) หากโบรกเกอร์คิดคอมมิชชันแพงจะกินกำไร

## 🚨 6. สิ่งที่ต้องเฝ้าระวังอย่างยิ่ง (Risk Factors & Cautions)
- ต้องระวังการเกิด Absorption เมื่อราคาชนแนวรับ/ต้านที่มีสภาพคล่องหนาแน่นดักอยู่

## 🧩 7. การทำงานร่วมกับกลยุทธ์อื่น (Compatibility & Synergy)
- สามารถทำงานร่วมกับหมวด: 01_lob_and_deep_learning, 04_optimal_execution_and_vwap, 08_lead_lag_and_latency, 12_position_sizing_and_risk

---
## 📌 บทคัดย่อของงานวิจัยต้นฉบับ
> We study the price impact of order book events - limit orders, market orders and cancelations - using the NYSE TAQ data for 50 U.S. stocks. We show that, over short time intervals, price changes are mainly driven by the order flow imbalance, defined as the imbalance between supply and demand at the best bid and ask prices. Our study reveals a linear relation between order flow imbalance and price changes, with a slope inversely proportional to the market depth. These results are shown to be robust to seasonality effects, and stable across time scales and across stocks. We argue that this linear price impact model, together with a scaling argument, implies the empirically observed "square-root" relation between price changes and trading volume. However, the relation between price changes and trade volume is found to be noisy and less robust than the one based on order flow imbalance.

---
*จัดทำเป็นฐานข้อมูลกลยุทธ์เชิงปริมาณสำหรับ cbot-atgvt พร้อมสำหรับการแปลงเป็นระบบเทรดและเผยแพร่บนเว็บ*