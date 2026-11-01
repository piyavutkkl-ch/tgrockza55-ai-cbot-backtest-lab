# [STRAT-027] Deep Hawkes Process for High-Frequency Market Making
**หมวดหมู่:** 📊 03_market_making_and_spread | **ประเภทกลยุทธ์:** `Optimal Market Making & Inventory Skewing`
**อ้างอิงเปเปอร์:** [`2109.15110v1`](https://arxiv.org/html/2109.15110v1) | **ผู้แต่ง:** Pankaj Kumar (2021-09-30)

## 🔗 ลิงก์เอกสารต้นฉบับ
- 🌐 **อ่านเวอร์ชัน HTML เต็ม:** [https://arxiv.org/html/2109.15110v1](https://arxiv.org/html/2109.15110v1) *(ไม่ต้องดาวน์โหลด ไม่ติด Limit)*
- 📥 **ดาวน์โหลด PDF:** [https://arxiv.org/pdf/2109.15110v1.pdf](https://arxiv.org/pdf/2109.15110v1.pdf)

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
> High-frequency market making is a liquidity-providing trading strategy that simultaneously generates many bids and asks for a security at ultra-low latency while maintaining a relatively neutral position. The strategy makes a profit from the bid-ask spread for every buy and sell transaction, against the risk of adverse selection, uncertain execution and inventory risk. We design realistic simulations of limit order markets and develop a high-frequency market making strategy in which agents process order book information to post the optimal price, order type and execution time. By introducing the Deep Hawkes process to the high-frequency market making strategy, we allow a feedback loop to be created between order arrival and the state of the limit order book, together with self- and cross-excitation effects. Our high-frequency market making strategy accounts for the cancellation of orders that influence order queue position, profitability, bid-ask spread and the value of the order. The experimental results show that our trading agent outperforms the baseline strategy, which uses a probability density estimate of the fundamental price. We investigate the effect of cancellations on market quality and the agent's profitability. We validate how closely the simulation framework approximates reality by reproducing stylised facts from the empirical analysis of the simulated order book data.

---
*จัดทำเป็นฐานข้อมูลกลยุทธ์เชิงปริมาณสำหรับ cbot-atgvt พร้อมสำหรับการแปลงเป็นระบบเทรดและเผยแพร่บนเว็บ*