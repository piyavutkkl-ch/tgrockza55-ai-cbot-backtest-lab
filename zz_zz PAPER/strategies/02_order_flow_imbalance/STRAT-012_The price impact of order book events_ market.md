# [STRAT-012] The price impact of order book events: market orders, limit orders and cancellations
**หมวดหมู่:** 📊 02_order_flow_imbalance | **ประเภทกลยุทธ์:** `Order Flow Imbalance (OFI) & Price Impact`
**อ้างอิงเปเปอร์:** [`0904.0900v3`](https://arxiv.org/html/0904.0900v3) | **ผู้แต่ง:** Zoltan Eisler, Jean-Philippe Bouchaud, Julien Kockelkoren (2009-04-06)

## 🔗 ลิงก์เอกสารต้นฉบับ
- 🌐 **อ่านเวอร์ชัน HTML เต็ม:** [https://arxiv.org/html/0904.0900v3](https://arxiv.org/html/0904.0900v3) *(ไม่ต้องดาวน์โหลด ไม่ติด Limit)*
- 📥 **ดาวน์โหลด PDF:** [https://arxiv.org/pdf/0904.0900v3.pdf](https://arxiv.org/pdf/0904.0900v3.pdf)

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
> While the long-ranged correlation of market orders and their impact on prices has been relatively well studied in the literature, the corresponding studies of limit orders and cancellations are scarce. We provide here an empirical study of the cross-correlation between all these different events, and their respective impact on future price changes. We define and extract from the data the "bare" impact these events would have, if they were to happen in isolation. For large tick stocks, we show that a model where the bare impact of all events is permanent and non-fluctuating is in good agreement with the data. For small tick stocks, however, bare impacts must contain a history dependent part, reflecting the internal fluctuations of the order book. We show that this effect can be accurately described by an autoregressive model on the past order flow. This framework allows us to decompose the impact of an event into three parts: an instantaneous jump component, the modification of the future rates of the different events, and the modification of the future gaps behind the best quotes. We compare in detail the present formalism with the temporary impact model that was proposed earlier to describe the impact of market orders when other types of events are not observed. Finally, we extend the model to describe the dynamics of the bid-ask spread.

---
*จัดทำเป็นฐานข้อมูลกลยุทธ์เชิงปริมาณสำหรับ cbot-atgvt พร้อมสำหรับการแปลงเป็นระบบเทรดและเผยแพร่บนเว็บ*