# [STRAT-001] DeepLOB: Deep Convolutional Neural Networks for Limit Order Books
**หมวดหมู่:** 📊 01_lob_and_deep_learning | **ประเภทกลยุทธ์:** `LOB Spatial Feature & Deep Learning Prediction`
**อ้างอิงเปเปอร์:** [`1808.03668v6`](https://arxiv.org/html/1808.03668v6) | **ผู้แต่ง:** Zihao Zhang, Stefan Zohren, Stephen Roberts (2018-08-10)

## 🔗 ลิงก์เอกสารต้นฉบับ
- 🌐 **อ่านเวอร์ชัน HTML เต็ม:** [https://arxiv.org/html/1808.03668v6](https://arxiv.org/html/1808.03668v6) *(ไม่ต้องดาวน์โหลด ไม่ติด Limit)*
- 📥 **ดาวน์โหลด PDF:** [https://arxiv.org/pdf/1808.03668v6.pdf](https://arxiv.org/pdf/1808.03668v6.pdf)

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
> We develop a large-scale deep learning model to predict price movements from limit order book (LOB) data of cash equities. The architecture utilises convolutional filters to capture the spatial structure of the limit order books as well as LSTM modules to capture longer time dependencies. The proposed network outperforms all existing state-of-the-art algorithms on the benchmark LOB dataset [1]. In a more realistic setting, we test our model by using one year market quotes from the London Stock Exchange and the model delivers a remarkably stable out-of-sample prediction accuracy for a variety of instruments. Importantly, our model translates well to instruments which were not part of the training set, indicating the model's ability to extract universal features. In order to better understand these features and to go beyond a "black box" model, we perform a sensitivity analysis to understand the rationale behind the model predictions and reveal the components of LOBs that are most relevant. The ability to extract robust features which translate well to other instruments is an important property of our model which has many other applications.

---
*จัดทำเป็นฐานข้อมูลกลยุทธ์เชิงปริมาณสำหรับ cbot-atgvt พร้อมสำหรับการแปลงเป็นระบบเทรดและเผยแพร่บนเว็บ*