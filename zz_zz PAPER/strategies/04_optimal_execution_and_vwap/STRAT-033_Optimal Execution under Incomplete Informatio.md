# [STRAT-033] Optimal Execution under Incomplete Information
**หมวดหมู่:** 📊 04_optimal_execution_and_vwap | **ประเภทกลยุทธ์:** `Optimal Execution & Dynamic VWAP Slicing`
**อ้างอิงเปเปอร์:** [`2411.04616v2`](https://arxiv.org/html/2411.04616v2) | **ผู้แต่ง:** Etienne Chevalier, Yadh Hafsi, Vathana Ly Vath (2024-11-07)

## 🔗 ลิงก์เอกสารต้นฉบับ
- 🌐 **อ่านเวอร์ชัน HTML เต็ม:** [https://arxiv.org/html/2411.04616v2](https://arxiv.org/html/2411.04616v2) *(ไม่ต้องดาวน์โหลด ไม่ติด Limit)*
- 📥 **ดาวน์โหลด PDF:** [https://arxiv.org/pdf/2411.04616v2.pdf](https://arxiv.org/pdf/2411.04616v2.pdf)

---

## 💰 1. ทำไมถึงได้กำไร? (Alpha & Profit Mechanism)
ลดต้นทุนการส่งคำสั่ง (Execution Cost Minimization) ได้ราคาเฉลี่ยที่ดีกว่าราคากลางของตลาด และหลีกเลี่ยงการดันราคาตัวเอง (Self-Impact)

## 🟢 2. เงื่อนไขจุดเข้า (Entry Trigger)
เมื่อมีคำสั่งขนาดใหญ่หรือต้องการเข้าสะสมสถานะตามแนวโน้มวัน ให้คำนวณเส้นโค้ง Volume Profile และเส้น VWAP สถาบัน ส่งคำสั่งแบ่งไม้ซอย (Slicing) แบบ Almgren-Chriss เมื่อราคาดึงกลับมาสัมผัสเส้น VWAP +/- 1.0 Band

## 🔴 3. เงื่อนไขจุดออก (Exit Trigger / TP / SL)
ปิดสถานะเมื่อราคาทะลุออกนอกกรอบ VWAP 2.5 Band หรือเมื่อครบกำหนดตารางเวลาการเทรดของ Session (London/NY Close)

## 💎 4. จุดเด่น (Strengths)
- สามารถรองรับพอร์ตขนาดใหญ่ได้โดยไม่เกิด Slippage มหาศาล สอดคล้องกับพฤติกรรมการเทรดของสถาบันการเงิน

## ⚠️ 5. จุดอ่อน (Weaknesses)
- ไม่เหมาะกับการเทรดเก็งกำไรระยะสั้นแบบ Scalping เสี้ยววินาที

## 🚨 6. สิ่งที่ต้องเฝ้าระวังอย่างยิ่ง (Risk Factors & Cautions)
- ต้องระวังการหลุดของ Volume Profile ในวันที่เกิดข่าวเซอร์ไพรส์นอกตาราง

## 🧩 7. การทำงานร่วมกับกลยุทธ์อื่น (Compatibility & Synergy)
- สามารถทำงานร่วมกับหมวด: 02_order_flow_imbalance, 06_gold_commodity_and_macro, 07_regime_detection_and_hmm, 12_position_sizing_and_risk

---
## 📌 บทคัดย่อของงานวิจัยต้นฉบับ
> We study optimal liquidation strategies under partial information for a single asset within a finite time horizon. We propose a model tailored for high-frequency trading, capturing price formation driven solely by order flow through mutually stimulating marked Hawkes processes. The model assumes a limit order book framework, accounting for both permanent price impact and transient market impact. Importantly, we incorporate liquidity as a hidden Markov process, influencing the intensities of the point processes governing bid and ask prices. Within this setting, we formulate the optimal liquidation problem as an impulse control problem. We elucidate the dynamics of the hidden Markov chain's filter and determine the related normalized filtering equations. We then express the value function as the limit of a sequence of auxiliary continuous functions, defined recursively. This characterization enables the use of a dynamic programming principle for optimal stopping problems and the determination of an optimal strategy. It also facilitates the development of an implementable algorithm to approximate the original liquidation problem. We enrich our analysis with numerical results and visualizations of candidate optimal strategies.

---
*จัดทำเป็นฐานข้อมูลกลยุทธ์เชิงปริมาณสำหรับ cbot-atgvt พร้อมสำหรับการแปลงเป็นระบบเทรดและเผยแพร่บนเว็บ*