# [STRAT-029] Macroscopic Market Making
**หมวดหมู่:** 📊 03_market_making_and_spread | **ประเภทกลยุทธ์:** `Optimal Market Making & Inventory Skewing`
**อ้างอิงเปเปอร์:** [`2307.14129v3`](https://arxiv.org/html/2307.14129v3) | **ผู้แต่ง:** Ivan Guo, Shijia Jin, Kihun Nam (2023-07-26)

## 🔗 ลิงก์เอกสารต้นฉบับ
- 🌐 **อ่านเวอร์ชัน HTML เต็ม:** [https://arxiv.org/html/2307.14129v3](https://arxiv.org/html/2307.14129v3) *(ไม่ต้องดาวน์โหลด ไม่ติด Limit)*
- 📥 **ดาวน์โหลด PDF:** [https://arxiv.org/pdf/2307.14129v3.pdf](https://arxiv.org/pdf/2307.14129v3.pdf)

---

## 💰 1. ทำไมถึงได้กำไร? (Alpha & Profit Mechanism)
เก็บกำไรจาก Bid-Ask Spread ซ้ำๆ ต่อเนื่องตลอดวันโดยอาศัย Law of Large Numbers และสถิติ Mean-Reversion ของสภาพคล่องระยะสั้น

## 🟢 2. เงื่อนไขจุดเข้า (Entry Trigger)
คำนวณราคาจอง (Reservation Price) r(s,q,t) = s - q*gamma*sigma^2*(T-t) วางคำสั่ง Limit Order สองฝั่ง Bid/Ask รอบราคาจอง พร้อมเอียงราคา (Quote Skewing) ตามสัญญาณโมเมนตัมระดับสั้น

## 🔴 3. เงื่อนไขจุดออก (Exit Trigger / TP / SL)
คำสั่งฝั่งหนึ่งถูก Match ทำกำไรจากสเปรดทันที หากสถานะคงค้าง (Inventory q) เกินเพดานที่กำหนด ให้หยุดวางฝั่งเดิมและเร่งระบายออกฝั่งตรงข้ามด้วยส่วนลดราคา

## 💎 4. จุดเด่น (Strengths)
- สร้างผลกำไรสะสมเป็นเส้นตรง (High Sharpe Ratio) ในตลาด Sideway หรือช่วงที่มีวอลุ่มหมุนเวียนคงที่

## ⚠️ 5. จุดอ่อน (Weaknesses)
- กลืนกินการขาดทุนหนักเมื่อเกิดเทรนด์รุนแรงทิศทางเดียว (Adverse Selection Risk) หรือเมื่อถือของผิดฝั่ง

## 🚨 6. สิ่งที่ต้องเฝ้าระวังอย่างยิ่ง (Risk Factors & Cautions)
- การคุม Inventory ต้องเฉียบขาด หากถือของสะสมเกินลิมิตต้องตัดทิ้งทันทีโดยไม่ลังเล

## 🧩 7. การทำงานร่วมกับกลยุทธ์อื่น (Compatibility & Synergy)
- สามารถทำงานร่วมกับหมวด: 05_hawkes_and_event_clustering, 07_regime_detection_and_hmm, 12_position_sizing_and_risk, 13_rough_volatility_and_jumps

---
## 📌 บทคัดย่อของงานวิจัยต้นฉบับ
> We propose a macroscopic market making model à la Avellaneda-Stoikov, using continuous processes for orders instead of discrete point processes. The model intends to bridge the gap between market making and optimal execution problems, while shedding light on the influence of order flows on the optimal strategies. We demonstrate our model through three problems. The study provides a comprehensive analysis from Markovian to non-Markovian noises and from linear to non-linear intensity functions, encompassing both bounded and unbounded coefficients. Mathematically, the contribution lies in the existence and uniqueness of the optimal control, guaranteed by the well-posedness of the strong solution to the Hamilton-Jacobi-Bellman equation and the (non-)Lipschitz forward-backward stochastic differential equation. Finally, the model's applications to price impact and optimal execution are discussed.

---
*จัดทำเป็นฐานข้อมูลกลยุทธ์เชิงปริมาณสำหรับ cbot-atgvt พร้อมสำหรับการแปลงเป็นระบบเทรดและเผยแพร่บนเว็บ*