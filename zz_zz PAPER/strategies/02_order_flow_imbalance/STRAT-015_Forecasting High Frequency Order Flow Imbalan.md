# [STRAT-015] Forecasting High Frequency Order Flow Imbalance
**หมวดหมู่:** 📊 02_order_flow_imbalance | **ประเภทกลยุทธ์:** `Order Flow Imbalance (OFI) & Price Impact`
**อ้างอิงเปเปอร์:** [`2408.03594v1`](https://arxiv.org/html/2408.03594v1) | **ผู้แต่ง:** Aditya Nittur Anantha, Shashi Jain (2024-08-07)

## 🔗 ลิงก์เอกสารต้นฉบับ
- 🌐 **อ่านเวอร์ชัน HTML เต็ม:** [https://arxiv.org/html/2408.03594v1](https://arxiv.org/html/2408.03594v1) *(ไม่ต้องดาวน์โหลด ไม่ติด Limit)*
- 📥 **ดาวน์โหลด PDF:** [https://arxiv.org/pdf/2408.03594v1.pdf](https://arxiv.org/pdf/2408.03594v1.pdf)

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
> Market information events are generated intermittently and disseminated at high speeds in real-time. Market participants consume this high-frequency data to build limit order books, representing the current bids and offers for a given asset. The arrival processes, or the order flow of bid and offer events, are asymmetric and possibly dependent on each other. The quantum and direction of this asymmetry are often associated with the direction of the traded price movement. The Order Flow Imbalance (OFI) is an indicator commonly used to estimate this asymmetry. This paper uses Hawkes processes to estimate the OFI while accounting for the lagged dependence in the order flow between bids and offers. Secondly, we develop a method to forecast the near-term distribution of the OFI, which can then be used to compare models for forecasting OFI. Thirdly, we propose a method to compare the forecasts of OFI for an arbitrarily large number of models. We apply the approach developed to tick data from the National Stock Exchange and observe that the Hawkes process modeled with a Sum of Exponential's kernel gives the best forecast among all competing models.

---
*จัดทำเป็นฐานข้อมูลกลยุทธ์เชิงปริมาณสำหรับ cbot-atgvt พร้อมสำหรับการแปลงเป็นระบบเทรดและเผยแพร่บนเว็บ*