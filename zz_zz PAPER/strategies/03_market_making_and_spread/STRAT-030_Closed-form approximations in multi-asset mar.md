# [STRAT-030] Closed-form approximations in multi-asset market making
**หมวดหมู่:** 📊 03_market_making_and_spread | **ประเภทกลยุทธ์:** `Optimal Market Making & Inventory Skewing`
**อ้างอิงเปเปอร์:** [`1810.04383v5`](https://arxiv.org/html/1810.04383v5) | **ผู้แต่ง:** Philippe Bergault, David Evangelista, Olivier Guéant, Douglas Vieira (2018-10-10)

## 🔗 ลิงก์เอกสารต้นฉบับ
- 🌐 **อ่านเวอร์ชัน HTML เต็ม:** [https://arxiv.org/html/1810.04383v5](https://arxiv.org/html/1810.04383v5) *(ไม่ต้องดาวน์โหลด ไม่ติด Limit)*
- 📥 **ดาวน์โหลด PDF:** [https://arxiv.org/pdf/1810.04383v5.pdf](https://arxiv.org/pdf/1810.04383v5.pdf)

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
> A large proportion of market making models derive from the seminal model of Avellaneda and Stoikov. The numerical approximation of the value function and the optimal quotes in these models remains a challenge when the number of assets is large. In this article, we propose closed-form approximations for the value functions of many multi-asset extensions of the Avellaneda-Stoikov model. These approximations or proxies can be used (i) as heuristic evaluation functions, (ii) as initial value functions in reinforcement learning algorithms, and/or (iii) directly to design quoting strategies through a greedy approach. Regarding the latter, our results lead to new and easily interpretable closed-form approximations for the optimal quotes, both in the finite-horizon case and in the asymptotic (ergodic) regime.

---
*จัดทำเป็นฐานข้อมูลกลยุทธ์เชิงปริมาณสำหรับ cbot-atgvt พร้อมสำหรับการแปลงเป็นระบบเทรดและเผยแพร่บนเว็บ*