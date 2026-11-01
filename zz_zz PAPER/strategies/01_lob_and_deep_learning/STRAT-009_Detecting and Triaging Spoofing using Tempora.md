# [STRAT-009] Detecting and Triaging Spoofing using Temporal Convolutional Networks
**หมวดหมู่:** 📊 01_lob_and_deep_learning | **ประเภทกลยุทธ์:** `LOB Spatial Feature & Deep Learning Prediction`
**อ้างอิงเปเปอร์:** [`2403.13429v1`](https://arxiv.org/html/2403.13429v1) | **ผู้แต่ง:** Kaushalya Kularatnam, Tania Stathaki (2024-03-20)

## 🔗 ลิงก์เอกสารต้นฉบับ
- 🌐 **อ่านเวอร์ชัน HTML เต็ม:** [https://arxiv.org/html/2403.13429v1](https://arxiv.org/html/2403.13429v1) *(ไม่ต้องดาวน์โหลด ไม่ติด Limit)*
- 📥 **ดาวน์โหลด PDF:** [https://arxiv.org/pdf/2403.13429v1.pdf](https://arxiv.org/pdf/2403.13429v1.pdf)

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
> As algorithmic trading and electronic markets continue to transform the landscape of financial markets, detecting and deterring rogue agents to maintain a fair and efficient marketplace is crucial. The explosion of large datasets and the continually changing tricks of the trade make it difficult to adapt to new market conditions and detect bad actors. To that end, we propose a framework that can be adapted easily to various problems in the space of detecting market manipulation. Our approach entails initially employing a labelling algorithm which we use to create a training set to learn a weakly supervised model to identify potentially suspicious sequences of order book states. The main goal here is to learn a representation of the order book that can be used to easily compare future events. Subsequently, we posit the incorporation of expert assessment to scrutinize specific flagged order book states. In the event of an expert's unavailability, recourse is taken to the application of a more complex algorithm on the identified suspicious order book states. We then conduct a similarity search between any new representation of the order book against the expert labelled representations to rank the results of the weak learner. We show some preliminary results that are promising to explore further in this direction

---
*จัดทำเป็นฐานข้อมูลกลยุทธ์เชิงปริมาณสำหรับ cbot-atgvt พร้อมสำหรับการแปลงเป็นระบบเทรดและเผยแพร่บนเว็บ*