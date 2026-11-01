# [STRAT-016] Non-average price impact in order-driven markets
**หมวดหมู่:** 📊 02_order_flow_imbalance | **ประเภทกลยุทธ์:** `Order Flow Imbalance (OFI) & Price Impact`
**อ้างอิงเปเปอร์:** [`2110.00771v2`](https://arxiv.org/html/2110.00771v2) | **ผู้แต่ง:** Claudio Bellani, Damiano Brigo, Mikko Pakkanen, Leandro Sanchez-Betancourt (2021-10-02)

## 🔗 ลิงก์เอกสารต้นฉบับ
- 🌐 **อ่านเวอร์ชัน HTML เต็ม:** [https://arxiv.org/html/2110.00771v2](https://arxiv.org/html/2110.00771v2) *(ไม่ต้องดาวน์โหลด ไม่ติด Limit)*
- 📥 **ดาวน์โหลด PDF:** [https://arxiv.org/pdf/2110.00771v2.pdf](https://arxiv.org/pdf/2110.00771v2.pdf)

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
> We present a measurement of price impact in order-driven markets that does not require averages across executions or scenarios. Given the order book data associated with one single execution of a sell metaorder, we measure its contribution to price decrease during the trade. We do so by modelling the limit order book using state-dependent Hawkes processes, and by defining the price impact profile of the execution as a function of the compensator of a stochastic process in our model. We apply our measurement to a data set from NASDAQ, and we conclude that the clustering of sell child orders has a bigger impact on price than their sizes.

---
*จัดทำเป็นฐานข้อมูลกลยุทธ์เชิงปริมาณสำหรับ cbot-atgvt พร้อมสำหรับการแปลงเป็นระบบเทรดและเผยแพร่บนเว็บ*