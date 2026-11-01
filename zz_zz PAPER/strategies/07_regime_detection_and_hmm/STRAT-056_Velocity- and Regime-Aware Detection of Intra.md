# [STRAT-056] Velocity- and Regime-Aware Detection of Intraday Options Market Manipulation, with Explainable Attribution
**หมวดหมู่:** 🎛️ หมวดที่ 7: การจำแนกสภาวะตลาด (Market Regime Detection) และแบบจำลอง HMM | **ประเภทกลยุทธ์:** `Hidden Markov Model (HMM) Regime Switching`
**อ้างอิงเปเปอร์:** [`2608.05373`](https://arxiv.org/html/2608.05373) | **ผู้แต่ง:**  (5 August, )

## 🔗 ลิงก์เอกสารต้นฉบับ
- 🌐 **อ่านเวอร์ชัน HTML เต็ม:** [https://arxiv.org/html/2608.05373](https://arxiv.org/html/2608.05373) *(ไม่ต้องดาวน์โหลด ไม่ติด Limit)*
- 📥 **ดาวน์โหลด PDF:** [https://arxiv.org/pdf/2608.05373.pdf](https://arxiv.org/pdf/2608.05373.pdf)

---

## 💰 1. ทำไมถึงได้กำไร? (Alpha & Profit Mechanism)
ป้องกันการขาดทุนแบบ Drawdown ลึกจากการรันบอทผิดสภาวะตลาด (Eliminating Regime Misalignment)

## 🟢 2. เงื่อนไขจุดเข้า (Entry Trigger)
โมเดล HMM จำแนกสภาวะตลาดเป็น 4 โหมด: (1) Low-Vol Trend -> อนุญาตให้บอท Momentum ทำงาน (2) High-Vol Trend -> ลดขนาด Lot และรัน Trend Follow (3) Range-Bound -> อนุญาตให้บอท Mean-Reversion/Market Making ทำงาน (4) Crisis/Turbulent -> ปิดระบบทั้งหมด

## 🔴 3. เงื่อนไขจุดออก (Exit Trigger / TP / SL)
เมื่อโมเดลตรวจพบความน่าจะเป็นของ Regime เปลี่ยนแปลง (Regime Transition Probability > 0.60) สั่งบังคับปิดออเดอร์ของโหมดเดิมทันที

## 💎 4. จุดเด่น (Strengths)
- เพิ่ม Sharpe Ratio ของพอร์ตรวมอย่างมหาศาล และลด Maximum Drawdown ลงได้มากกว่า 40-60%

## ⚠️ 5. จุดอ่อน (Weaknesses)
- การตรวจจับการเปลี่ยนสภาวะอาจมีความล่าช้าเล็กน้อย (Lagging in Transition Phase)

## 🚨 6. สิ่งที่ต้องเฝ้าระวังอย่างยิ่ง (Risk Factors & Cautions)
- ต้องระวังการ Overfit จำนวน State ในขั้นตอนการเทรน HMM (แนะนำ 3 หรือ 4 State กำลังดี)

## 🧩 7. การทำงานร่วมกับกลยุทธ์อื่น (Compatibility & Synergy)
- สามารถทำงานร่วมกับหมวด: 01_lob_and_deep_learning, 03_market_making_and_spread, 04_optimal_execution_and_vwap, 12_position_sizing_and_risk

---
## 📌 บทคัดย่อของงานวิจัยต้นฉบับ
> 

---
*จัดทำเป็นฐานข้อมูลกลยุทธ์เชิงปริมาณสำหรับ cbot-atgvt พร้อมสำหรับการแปลงเป็นระบบเทรดและเผยแพร่บนเว็บ*