# [STRAT-028] Reinforcement Learning in High-frequency Market Making
**หมวดหมู่:** 📊 03_market_making_and_spread | **ประเภทกลยุทธ์:** `Optimal Market Making & Inventory Skewing`
**อ้างอิงเปเปอร์:** [`2407.21025v2`](https://arxiv.org/html/2407.21025v2) | **ผู้แต่ง:** Yuheng Zheng, Zihan Ding (2024-07-14)

## 🔗 ลิงก์เอกสารต้นฉบับ
- 🌐 **อ่านเวอร์ชัน HTML เต็ม:** [https://arxiv.org/html/2407.21025v2](https://arxiv.org/html/2407.21025v2) *(ไม่ต้องดาวน์โหลด ไม่ติด Limit)*
- 📥 **ดาวน์โหลด PDF:** [https://arxiv.org/pdf/2407.21025v2.pdf](https://arxiv.org/pdf/2407.21025v2.pdf)

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
> This paper establishes a new and comprehensive theoretical analysis for the application of reinforcement learning (RL) in high-frequency market making. We bridge the modern RL theory and the continuous-time statistical models in high-frequency financial economics. Different with most existing literature on methodological research about developing various RL methods for market making problem, our work is a pilot to provide the theoretical analysis. We target the effects of sampling frequency, and find an interesting tradeoff between error and complexity of RL algorithm when tweaking the values of the time increment $Δ$ $-$ as $Δ$ becomes smaller, the error will be smaller but the complexity will be larger. We also study the two-player case under the general-sum game framework and establish the convergence of Nash equilibrium to the continuous-time game equilibrium as $Δ\rightarrow0$. The Nash Q-learning algorithm, which is an online multi-agent RL method, is applied to solve the equilibrium. Our theories are not only useful for practitioners to choose the sampling frequency, but also very general and applicable to other high-frequency financial decision making problems, e.g., optimal executions, as long as the time-discretization of a continuous-time markov decision process is adopted. Monte Carlo simulation evidence support all of our theories.

---
*จัดทำเป็นฐานข้อมูลกลยุทธ์เชิงปริมาณสำหรับ cbot-atgvt พร้อมสำหรับการแปลงเป็นระบบเทรดและเผยแพร่บนเว็บ*