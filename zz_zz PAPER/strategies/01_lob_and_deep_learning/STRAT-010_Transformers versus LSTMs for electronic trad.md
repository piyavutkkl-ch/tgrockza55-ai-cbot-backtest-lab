# [STRAT-010] Transformers versus LSTMs for electronic trading
**หมวดหมู่:** 📊 01_lob_and_deep_learning | **ประเภทกลยุทธ์:** `LOB Spatial Feature & Deep Learning Prediction`
**อ้างอิงเปเปอร์:** [`2309.11400v1`](https://arxiv.org/html/2309.11400v1) | **ผู้แต่ง:** Paul Bilokon, Yitao Qiu (2023-09-20)

## 🔗 ลิงก์เอกสารต้นฉบับ
- 🌐 **อ่านเวอร์ชัน HTML เต็ม:** [https://arxiv.org/html/2309.11400v1](https://arxiv.org/html/2309.11400v1) *(ไม่ต้องดาวน์โหลด ไม่ติด Limit)*
- 📥 **ดาวน์โหลด PDF:** [https://arxiv.org/pdf/2309.11400v1.pdf](https://arxiv.org/pdf/2309.11400v1.pdf)

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
> With the rapid development of artificial intelligence, long short term memory (LSTM), one kind of recurrent neural network (RNN), has been widely applied in time series prediction.   Like RNN, Transformer is designed to handle the sequential data. As Transformer achieved great success in Natural Language Processing (NLP), researchers got interested in Transformer's performance on time series prediction, and plenty of Transformer-based solutions on long time series forecasting have come out recently. However, when it comes to financial time series prediction, LSTM is still a dominant architecture. Therefore, the question this study wants to answer is: whether the Transformer-based model can be applied in financial time series prediction and beat LSTM.   To answer this question, various LSTM-based and Transformer-based models are compared on multiple financial prediction tasks based on high-frequency limit order book data. A new LSTM-based model called DLSTM is built and new architecture for the Transformer-based model is designed to adapt for financial prediction. The experiment result reflects that the Transformer-based model only has the limited advantage in absolute price sequence prediction. The LSTM-based models show better and more robust performance on difference sequence prediction, such as price difference and price movement.

---
*จัดทำเป็นฐานข้อมูลกลยุทธ์เชิงปริมาณสำหรับ cbot-atgvt พร้อมสำหรับการแปลงเป็นระบบเทรดและเผยแพร่บนเว็บ*