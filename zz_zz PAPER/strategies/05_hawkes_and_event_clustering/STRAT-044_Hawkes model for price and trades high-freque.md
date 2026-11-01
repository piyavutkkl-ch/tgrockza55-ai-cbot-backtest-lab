# [STRAT-044] Hawkes model for price and trades high-frequency dynamics
**หมวดหมู่:** 📊 05_hawkes_and_event_clustering | **ประเภทกลยุทธ์:** `Hawkes Process & Trade Burst Detection`
**อ้างอิงเปเปอร์:** [`1301.1135v1`](https://arxiv.org/html/1301.1135v1) | **ผู้แต่ง:** E. Bacry, J. F Muzy (2013-01-07)

## 🔗 ลิงก์เอกสารต้นฉบับ
- 🌐 **อ่านเวอร์ชัน HTML เต็ม:** [https://arxiv.org/html/1301.1135v1](https://arxiv.org/html/1301.1135v1) *(ไม่ต้องดาวน์โหลด ไม่ติด Limit)*
- 📥 **ดาวน์โหลด PDF:** [https://arxiv.org/pdf/1301.1135v1.pdf](https://arxiv.org/pdf/1301.1135v1.pdf)

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
> We introduce a multivariate Hawkes process that accounts for the dynamics of market prices through the impact of market order arrivals at microstructural level. Our model is a point process mainly characterized by 4 kernels associated with respectively the trade arrival self-excitation, the price changes mean reversion the impact of trade arrivals on price variations and the feedback of price changes on trading activity. It allows one to account for both stylized facts of market prices microstructure (including random time arrival of price moves, discrete price grid, high frequency mean reversion, correlation functions behavior at various time scales) and the stylized facts of market impact (mainly the concave-square-root-like/relaxation characteristic shape of the market impact of a meta-order). Moreover, it allows one to estimate the entire market impact profile from anonymous market data. We show that these kernels can be estimated from the empirical conditional mean intensities. We provide numerical examples, application to real data and comparisons to former approaches.

---
*จัดทำเป็นฐานข้อมูลกลยุทธ์เชิงปริมาณสำหรับ cbot-atgvt พร้อมสำหรับการแปลงเป็นระบบเทรดและเผยแพร่บนเว็บ*