# [STRAT-006] Deep Recurrent Modelling of Stationary Bitcoin Price Formation Using the Order Flow
**หมวดหมู่:** 📊 01_lob_and_deep_learning | **ประเภทกลยุทธ์:** `LOB Spatial Feature & Deep Learning Prediction`
**อ้างอิงเปเปอร์:** [`2004.01499v1`](https://arxiv.org/html/2004.01499v1) | **ผู้แต่ง:** Ye-Sheen Lim, Denise Gorse (2020-03-31)

## 🔗 ลิงก์เอกสารต้นฉบับ
- 🌐 **อ่านเวอร์ชัน HTML เต็ม:** [https://arxiv.org/html/2004.01499v1](https://arxiv.org/html/2004.01499v1) *(ไม่ต้องดาวน์โหลด ไม่ติด Limit)*
- 📥 **ดาวน์โหลด PDF:** [https://arxiv.org/pdf/2004.01499v1.pdf](https://arxiv.org/pdf/2004.01499v1.pdf)

---

## 💰 1. ทำไมถึงได้กำไร? (Alpha & Profit Mechanism)
สกัดเจตนาของตลาดจากความหนาแน่นของสภาพคล่องจริง (Order Depth) ล่วงหน้าก่อนราคาในแท่งเทียนจะขยับ และเก็บส่วนต่างค่าสเปรด (Capture Half-Spread) จากการเข้าแบบ Passive

## 🟢 2. เงื่อนไขจุดเข้า (Entry Trigger)
เมื่อโมเดลประมวลผลข้อมูล DOM Level 2 (10 ระดับความลึก) ย้อนหลัง 100 Ticks แล้วค่าความน่าจะเป็นเชิงทิศทาง P(Direction) >= 0.72 พร้อมทั้งระยะการเคลื่อนที่ของราคาคาดการณ์สูงกว่าค่าสเปรดอย่างน้อย 1.5 เท่า ส่งคำสั่งแบบ Passive Limit Order ที่ Best Bid/Ask

## 🔴 3. เงื่อนไขจุดออก (Exit Trigger / TP / SL)
ปิดสถานะเมื่อ (1) โมเดลพลิกส่งสัญญาณตรงข้าม (P >= 0.65) (2) ถือครบกำหนด Time-horizon k ticks (50-100 ticks หรือ 1-3 นาที) หรือ (3) โดน Volatility SL ที่ 1.5x ATR(M1)

## 💎 4. จุดเด่น (Strengths)
- ความเร็วในการจับสัญญาณเหนือกว่าอินดิเคเตอร์ทุกชนิด เรียนรู้ความสัมพันธ์แบบ Non-linear ข้ามระดับราคาได้แม่นยำ

## ⚠️ 5. จุดอ่อน (Weaknesses)
- ต้องการพลังประมวลผลสูง (Inference GPU/ONNX) และแพ้ตลาดที่สเปรดถ่างกว้าง

## 🚨 6. สิ่งที่ต้องเฝ้าระวังอย่างยิ่ง (Risk Factors & Cautions)
- ระวังการถูกหลอกด้วยคำสั่งปลอม (Spoofing) และความหน่วงการส่งคำสั่ง (Execution Latency) ต้องเผื่อ Buffer t+5 ticks

## 🧩 7. การทำงานร่วมกับกลยุทธ์อื่น (Compatibility & Synergy)
- สามารถทำงานร่วมกับหมวด: 02_order_flow_imbalance, 07_regime_detection_and_hmm, 09_signal_processing_and_kalman, 12_position_sizing_and_risk

---
## 📌 บทคัดย่อของงานวิจัยต้นฉบับ
> In this paper we propose a deep recurrent model based on the order flow for the stationary modelling of the high-frequency directional prices movements. The order flow is the microsecond stream of orders arriving at the exchange, driving the formation of prices seen on the price chart of a stock or currency. To test the stationarity of our proposed model we train our model on data before the 2017 Bitcoin bubble period and test our model during and after the bubble. We show that without any retraining, the proposed model is temporally stable even as Bitcoin trading shifts into an extremely volatile "bubble trouble" period. The significance of the result is shown by benchmarking against existing state-of-the-art models in the literature for modelling price formation using deep learning.

---
*จัดทำเป็นฐานข้อมูลกลยุทธ์เชิงปริมาณสำหรับ cbot-atgvt พร้อมสำหรับการแปลงเป็นระบบเทรดและเผยแพร่บนเว็บ*