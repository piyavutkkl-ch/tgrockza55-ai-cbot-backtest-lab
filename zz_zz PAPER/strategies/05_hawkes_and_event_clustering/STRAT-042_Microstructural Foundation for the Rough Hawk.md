# [STRAT-042] Microstructural Foundation for the Rough Hawkes--Heston Model
**หมวดหมู่:** 📊 05_hawkes_and_event_clustering | **ประเภทกลยุทธ์:** `Hawkes Process & Trade Burst Detection`
**อ้างอิงเปเปอร์:** [`2608.07709v1`](https://arxiv.org/html/2608.07709v1) | **ผู้แต่ง:** Yingli Wang, Yinhao Wu, Lingjiong Zhu (2026-08-07)

## 🔗 ลิงก์เอกสารต้นฉบับ
- 🌐 **อ่านเวอร์ชัน HTML เต็ม:** [https://arxiv.org/html/2608.07709v1](https://arxiv.org/html/2608.07709v1) *(ไม่ต้องดาวน์โหลด ไม่ติด Limit)*
- 📥 **ดาวน์โหลด PDF:** [https://arxiv.org/pdf/2608.07709v1.pdf](https://arxiv.org/pdf/2608.07709v1.pdf)

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
> Hawkes-based microstructural foundations for rough volatility, leverage, and rough Heston-type limits were developed by El Euch et al. (2018, Finance Stoch., 22(2), 241--280) and connected to the affine rough Heston framework of El Euch and Rosenbaum (2019, Math. Finance, 29(1), 3--38). The rough Hawkes--Heston model with common price--volatility jumps of Bondi et al. (2024, Math. Finance, 34(4), 1197--1241) extends this framework by adding state-dependent common jumps to rough affine volatility. We provide a microstructural foundation for its variance and common-jump mechanism by constructing a Poisson-embedded marked Hawkes order-flow model. Ordinary arrivals generate rough continuous volatility and leverage through a nearly unstable heavy-tailed Hawkes mechanism, while rare marked arrivals represent common shock events that produce simultaneous price jumps and volatility excitation. Under the nearly unstable scaling and the reduced-form admissibility conditions, the complete rescaled price/variance/jump system converges along the full sequence to the unique complete canonical rough Hawkes--Heston weak solution. The Hawkes renewal structure yields a Mittag--Leffler Volterra representation, which is then rewritten in Riemann--Liouville fractional form. The limiting coefficients are expressed explicitly in terms of the microscopic parameters. The construction provides a microstructural foundation for the variance and common-jump mechanism of the rough Hawkes--Heston model. Numerical experiments illustrate the convergence of our microstructural foundation to the rough Hawkes-Heston model.

---
*จัดทำเป็นฐานข้อมูลกลยุทธ์เชิงปริมาณสำหรับ cbot-atgvt พร้อมสำหรับการแปลงเป็นระบบเทรดและเผยแพร่บนเว็บ*