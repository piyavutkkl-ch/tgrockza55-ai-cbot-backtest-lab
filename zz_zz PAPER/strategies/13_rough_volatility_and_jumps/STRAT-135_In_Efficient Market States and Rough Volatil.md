# [STRAT-135] (In)Efficient Market States and Rough Volatility Detected via Grunwald-Letnikov Fractional Derivative
**หมวดหมู่:** 🌊 หมวดที่ 13: ฟิสิกส์ความขรุขระของราคา (Rough Volatility) และการกระโดดของราคา (Jumps) | **ประเภทกลยุทธ์:** `Rough Volatility & Fractal Boundary Strategy`
**อ้างอิงเปเปอร์:** [`2606.27932`](https://arxiv.org/html/2606.27932) | **ผู้แต่ง:**  (26 June, 2)

## 🔗 ลิงก์เอกสารต้นฉบับ
- 🌐 **อ่านเวอร์ชัน HTML เต็ม:** [https://arxiv.org/html/2606.27932](https://arxiv.org/html/2606.27932) *(ไม่ต้องดาวน์โหลด ไม่ติด Limit)*
- 📥 **ดาวน์โหลด PDF:** [https://arxiv.org/pdf/2606.27932.pdf](https://arxiv.org/pdf/2606.27932.pdf)

---

## 💰 1. ทำไมถึงได้กำไร? (Alpha & Profit Mechanism)
สอดคล้องกับพฤติกรรมความขรุขระจริงของสินทรัพย์การเงิน ซึ่งโมเดลเกาส์เซียนทั่วไปมองข้าม

## 🟢 2. เงื่อนไขจุดเข้า (Entry Trigger)
คำนวณค่า Hurst Exponent H และค่า Roughness ของ Time-series (H < 0.5) เข้าเทรด Mean-reversion เมื่อราคาเหวี่ยงแตะขอบเขต Fractional Boundary ที่คำนวณจาก Rough Heston Kernel

## 🔴 3. เงื่อนไขจุดออก (Exit Trigger / TP / SL)
ปิดสถานะเมื่อราคากลับเข้าสู่เส้นแกนกลาง หรือเมื่อเวลาผ่านไปเกินกรอบความทรงจำของคลื่นขรุขระ (Memory Persistence Horizon)

## 💎 4. จุดเด่น (Strengths)
- ตั้ง Stop Loss และ Take Profit ได้อย่างแม่นยำในจุดที่พ้นจากระยะการสะบัดหลอกของตลาด

## ⚠️ 5. จุดอ่อน (Weaknesses)
- คณิตศาสตร์มีความซับซ้อนสูง ต้องใช้การแก้สมการอนุพันธ์ย่อยเชิงเศษส่วน

## 🚨 6. สิ่งที่ต้องเฝ้าระวังอย่างยิ่ง (Risk Factors & Cautions)
- ต้องตรวจวัดค่า Hurst Exponent ใหม่เป็นระยะเนื่องจากพฤติกรรมความขรุขระสามารถเปลี่ยนแปลงได้

## 🧩 7. การทำงานร่วมกับกลยุทธ์อื่น (Compatibility & Synergy)
- สามารถทำงานร่วมกับหมวด: 01_lob_and_deep_learning, 03_market_making_and_spread, 07_regime_detection_and_hmm, 12_position_sizing_and_risk

---
## 📌 บทคัดย่อของงานวิจัยต้นฉบับ
> 

---
*จัดทำเป็นฐานข้อมูลกลยุทธ์เชิงปริมาณสำหรับ cbot-atgvt พร้อมสำหรับการแปลงเป็นระบบเทรดและเผยแพร่บนเว็บ*