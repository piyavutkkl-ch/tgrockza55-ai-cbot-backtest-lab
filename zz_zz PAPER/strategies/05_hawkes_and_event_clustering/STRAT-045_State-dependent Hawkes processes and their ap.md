# [STRAT-045] State-dependent Hawkes processes and their application to limit order book modelling
**หมวดหมู่:** 📊 05_hawkes_and_event_clustering | **ประเภทกลยุทธ์:** `Hawkes Process & Trade Burst Detection`
**อ้างอิงเปเปอร์:** [`1809.08060v3`](https://arxiv.org/html/1809.08060v3) | **ผู้แต่ง:** Maxime Morariu-Patrichi, Mikko S. Pakkanen (2018-09-21)

## 🔗 ลิงก์เอกสารต้นฉบับ
- 🌐 **อ่านเวอร์ชัน HTML เต็ม:** [https://arxiv.org/html/1809.08060v3](https://arxiv.org/html/1809.08060v3) *(ไม่ต้องดาวน์โหลด ไม่ติด Limit)*
- 📥 **ดาวน์โหลด PDF:** [https://arxiv.org/pdf/1809.08060v3.pdf](https://arxiv.org/pdf/1809.08060v3.pdf)

---

## 💰 1. ทำไมถึงได้กำไร? (Alpha & Profit Mechanism)
จับจังหวะการเกิดลูกโซ่ของออเดอร์ (Herding & Order Cascades) ที่มักนำไปสู่การทะลุแนวรับแนวต้านแบบเฉียบพลัน

## 🟢 2. เงื่อนไขจุดเข้า (Entry Trigger)
คำนวณค่า Intensity Lambda(t) ของการเกิดออเดอร์ หากค่าความถี่พุ่งขึ้นแบบยกกำลัง (Self-Exciting Burst) เกินเกณฑ์วิกฤติ Lambda > Lambda_thresh พร้อมทิศทางออเดอร์ฝั่งใดฝั่งหนึ่งเกิน 75% ให้ยิง Momentum Follow ตามฝั่งนั้นทันที

## 🔴 3. เงื่อนไขจุดออก (Exit Trigger / TP / SL)
ปิดสถานะทันทีเมื่อค่า Intensity เริ่มสลายตัว (Exponential Decay) ต่ำกว่าระดับครึ่งหนึ่งของจุดสูงสุด หรือเมื่อเกิดการกระชากครบ 15-45 วินาที

## 💎 4. จุดเด่น (Strengths)
- ดักจับจังหวะการระเบิดของราคา (Volatility Breakout) ได้เร็วที่สุดก่อนที่กราฟแท่งเทียนจะฟอร์มตัวเสร็จ

## ⚠️ 5. จุดอ่อน (Weaknesses)
- มีจังหวะ False Alarm หากการระเบิดของคำสั่งเกิดจากการชนกันของบอทสองฝั่งโดยไม่มีทิศทางชัดเจน

## 🚨 6. สิ่งที่ต้องเฝ้าระวังอย่างยิ่ง (Risk Factors & Cautions)
- ต้องมีระบบคุ้มกันกรณีเกิด Flash Crash สวนทิศทาง ต้องใช้ Hard SL เสมอ

## 🧩 7. การทำงานร่วมกับกลยุทธ์อื่น (Compatibility & Synergy)
- สามารถทำงานร่วมกับหมวด: 01_lob_and_deep_learning, 02_order_flow_imbalance, 03_market_making_and_spread, 08_lead_lag_and_latency

---
## 📌 บทคัดย่อของงานวิจัยต้นฉบับ
> We study statistical aspects of state-dependent Hawkes processes, which are an extension of Hawkes processes where a self- and cross-exciting counting process and a state process are fully coupled, interacting with each other. The excitation kernel of the counting process depends on the state process that, reciprocally, switches state when there is an event in the counting process. We first establish the existence and uniqueness of state-dependent Hawkes processes and explain how they can be simulated. Then we develop maximum likelihood estimation methodology for parametric specifications of the process. We apply state-dependent Hawkes processes to high-frequency limit order book data, allowing us to build a novel model that captures the feedback loop between the order flow and the shape of the limit order book. We estimate two specifications of the model, using the bid-ask spread and the queue imbalance as state variables, and find that excitation effects in the order flow are strongly state-dependent. Additionally, we find that the endogeneity of the order flow, measured by the magnitude of excitation, is also state-dependent, being more pronounced in disequilibrium states of the limit order book.

---
*จัดทำเป็นฐานข้อมูลกลยุทธ์เชิงปริมาณสำหรับ cbot-atgvt พร้อมสำหรับการแปลงเป็นระบบเทรดและเผยแพร่บนเว็บ*