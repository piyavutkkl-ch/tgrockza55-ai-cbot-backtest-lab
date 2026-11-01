# [STRAT-021] Cross-Impact of Order Flow Imbalance in Equity Markets
**หมวดหมู่:** 📊 02_order_flow_imbalance | **ประเภทกลยุทธ์:** `Order Flow Imbalance (OFI) & Price Impact`
**อ้างอิงเปเปอร์:** [`2112.13213v4`](https://arxiv.org/html/2112.13213v4) | **ผู้แต่ง:** Rama Cont, Mihai Cucuringu, Chao Zhang (2021-12-25)

## 🔗 ลิงก์เอกสารต้นฉบับ
- 🌐 **อ่านเวอร์ชัน HTML เต็ม:** [https://arxiv.org/html/2112.13213v4](https://arxiv.org/html/2112.13213v4) *(ไม่ต้องดาวน์โหลด ไม่ติด Limit)*
- 📥 **ดาวน์โหลด PDF:** [https://arxiv.org/pdf/2112.13213v4.pdf](https://arxiv.org/pdf/2112.13213v4.pdf)

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
> We investigate the impact of order flow imbalance (OFI) on price movements in equity markets in a multi-asset setting. First, we propose a systematic approach for combining OFIs at the top levels of the limit order book into an integrated OFI variable which better explains price impact, compared to the best-level OFI. We show that once the information from multiple levels is integrated into OFI, multi-asset models with cross-impact do not provide additional explanatory power for contemporaneous impact compared to a sparse model without cross-impact terms. On the other hand, we show that lagged cross-asset OFIs do improve the forecasting of future returns. We also establish that this lagged cross-impact mainly manifests at short-term horizons and decays rapidly in time.

---
*จัดทำเป็นฐานข้อมูลกลยุทธ์เชิงปริมาณสำหรับ cbot-atgvt พร้อมสำหรับการแปลงเป็นระบบเทรดและเผยแพร่บนเว็บ*