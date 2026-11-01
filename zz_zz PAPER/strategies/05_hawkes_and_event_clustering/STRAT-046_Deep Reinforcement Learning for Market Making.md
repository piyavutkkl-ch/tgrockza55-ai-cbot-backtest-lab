# [STRAT-046] Deep Reinforcement Learning for Market Making Under a Hawkes Process-Based Limit Order Book Model
**หมวดหมู่:** 📊 05_hawkes_and_event_clustering | **ประเภทกลยุทธ์:** `Hawkes Process & Trade Burst Detection`
**อ้างอิงเปเปอร์:** [`2207.09951v1`](https://arxiv.org/html/2207.09951v1) | **ผู้แต่ง:** Bruno Gašperov, Zvonko Kostanjčar (2022-07-20)

## 🔗 ลิงก์เอกสารต้นฉบับ
- 🌐 **อ่านเวอร์ชัน HTML เต็ม:** [https://arxiv.org/html/2207.09951v1](https://arxiv.org/html/2207.09951v1) *(ไม่ต้องดาวน์โหลด ไม่ติด Limit)*
- 📥 **ดาวน์โหลด PDF:** [https://arxiv.org/pdf/2207.09951v1.pdf](https://arxiv.org/pdf/2207.09951v1.pdf)

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
> The stochastic control problem of optimal market making is among the central problems in quantitative finance. In this paper, a deep reinforcement learning-based controller is trained on a weakly consistent, multivariate Hawkes process-based limit order book simulator to obtain market making controls. The proposed approach leverages the advantages of Monte Carlo backtesting and contributes to the line of research on market making under weakly consistent limit order book models. The ensuing deep reinforcement learning controller is compared to multiple market making benchmarks, with the results indicating its superior performance with respect to various risk-reward metrics, even under significant transaction costs.

---
*จัดทำเป็นฐานข้อมูลกลยุทธ์เชิงปริมาณสำหรับ cbot-atgvt พร้อมสำหรับการแปลงเป็นระบบเทรดและเผยแพร่บนเว็บ*