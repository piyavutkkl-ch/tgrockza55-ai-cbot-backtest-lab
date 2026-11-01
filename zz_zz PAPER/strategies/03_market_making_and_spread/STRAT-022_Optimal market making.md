# [STRAT-022] Optimal market making
**หมวดหมู่:** 📊 03_market_making_and_spread | **ประเภทกลยุทธ์:** `Optimal Market Making & Inventory Skewing`
**อ้างอิงเปเปอร์:** [`1605.01862v5`](https://arxiv.org/html/1605.01862v5) | **ผู้แต่ง:** Olivier Guéant (2016-05-06)

## 🔗 ลิงก์เอกสารต้นฉบับ
- 🌐 **อ่านเวอร์ชัน HTML เต็ม:** [https://arxiv.org/html/1605.01862v5](https://arxiv.org/html/1605.01862v5) *(ไม่ต้องดาวน์โหลด ไม่ติด Limit)*
- 📥 **ดาวน์โหลด PDF:** [https://arxiv.org/pdf/1605.01862v5.pdf](https://arxiv.org/pdf/1605.01862v5.pdf)

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
> Market makers provide liquidity to other market participants: they propose prices at which they stand ready to buy and sell a wide variety of assets. They face a complex optimization problem with both static and dynamic components. They need indeed to propose bid and offer/ask prices in an optimal way for making money out of the difference between these two prices (their bid-ask spread). Since they seldom buy and sell simultaneously, and therefore hold long and/or short inventories, they also need to mitigate the risk associated with price changes, and subsequently skew their quotes dynamically. In this paper, (i) we propose a general modeling framework which generalizes (and reconciles) the various modeling approaches proposed in the literature since the publication of the seminal paper "High-frequency trading in a limit order book" by Avellaneda and Stoikov, (ii) we prove new general results on the existence and the characterization of optimal market making strategies, (iii) we obtain new closed-form approximations for the optimal quotes, (iv) we extend the modeling framework to the case of multi-asset market making and we obtain general closed-form approximations for the optimal quotes of a multi-asset market maker, and (v) we show how the model can be used in practice in the specific (and original) case of two credit indices.

---
*จัดทำเป็นฐานข้อมูลกลยุทธ์เชิงปริมาณสำหรับ cbot-atgvt พร้อมสำหรับการแปลงเป็นระบบเทรดและเผยแพร่บนเว็บ*