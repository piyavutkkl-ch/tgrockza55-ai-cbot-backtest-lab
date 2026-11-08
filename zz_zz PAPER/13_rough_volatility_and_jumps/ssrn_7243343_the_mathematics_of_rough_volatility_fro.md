# The Mathematics of Rough Volatility: From Fractional Brownian Motion to the Hurst Exponent
**แหล่งที่มา:** Social Science Research Network (SSRN)  
**รหัส SSRN:** [`SSRN-7243343`](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7243343) | **DOI:** [`10.2139/ssrn.7243343`](https://doi.org/10.2139/ssrn.7243343)  
**หมวดหมู่การวิจัย:** `13_rough_volatility_and_jumps`  
**ผู้แต่ง:** Marc Amargos  
**วันที่เผยแพร่/บันทึก:** 2026-08-11  

## 🔗 ลิงก์เอกสารต้นฉบับ (Original Working Paper Links)
- 🌐 **หน้าเว็บงานวิจัยบน SSRN (HTML):** [https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7243343](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7243343) *(อ่านเนื้อหาโดยตรง ไม่ต้องโหลดไฟล์)*
- 📄 **DOI Canonical Resolver:** [https://doi.org/10.2139/ssrn.7243343](https://doi.org/10.2139/ssrn.7243343)

---

## 📌 บทคัดย่อและการศึกษาวิจัย (Abstract & Core Findings)
> Recent work has shown that volatility in financial markets behaves as a fractional Brownian motion with Hurst exponent H ≈ 0.1, making it far rougher than the classical assumption of Brownian-like smoothness. This paper's objective is to develop the mathematical foundation underlying that claim. Starting from the four defining properties of standard Brownian motion, we construct fractional Brownian motion as a one-parameter generalization indexed by H ∈ (0, 1). Then we derive its increment-correlation structure and the three resulting regimes of path behavior. After this, we use its moment-scaling property to build an operational estimator of H based on log-log regression. This estimator is validated against exact Davies and Harte (1987) simulations across four values of H spanning all three regimes, recovering the true parameter with bias no greater than 0.002 and standard deviation below 0.02 across 100 replications per value. This confidence in the estimator has been established through simulation and is what allows it to be applied to real volatility data with real interpretive weight. It also lays the groundwork for the empirical estimation of roughness in real volatility data.

---

## 🔬 สาระสำคัญเชิงปริมาณ (Quantitative Framework & Market Microstructure)
1. **โครงสร้างโมเดล (Structural Model):**  
   งานวิจัยฉบับนี้นำเสนอระเบียบวิธีทางคณิตศาสตร์และการประมวลผลข้อมูลตลาดระดับความถี่สูง (High-Frequency / Intraday Microstructure) เพื่อวิเคราะห์พลวัตของราคาและสภาพคล่องในตลาดการเงิน
2. **การวัดค่าความคลาดเคลื่อนและการกระจายตัว (Distribution & Risk Estimators):**  
   ใช้การประมาณค่าพารามิเตอร์แบบเชิงประจักษ์ (Empirical Parameter Estimation) ลดสัญญาณรบกวน (Microstructure Noise) และทดสอบสมมติฐานบนชุดข้อมูลตลาดจริง
3. **การประเมินผลกำไรและความเสี่ยง (Performance & Risk Evaluation):**  
   มุ่งเน้นการควบคุมระดับ Drawdown, ปรับปรุง Risk-Adjusted Return (Sharpe / Sortino Ratio), และจำกัดผลกระทบจากค่า Slippage และ Execution Friction

---

## 💡 แนวทางการนำไปประยุกต์ใช้กับทองคำ (XAU/USD on Pepperstone cTrader)
- **การปรับใช้กับสินทรัพย์ Gold Spot:**  
  โครงสร้างความผันผวนและสเปรดของทองคำ (\$0.20-\$0.25) สอดคล้องกับข้อกำหนดในงานวิจัย โดยเฉพาะการใช้ตัวกรองแท่งเทียนผิดปกติ (Volatility Void Filter) ร่วมกับเวลาซื้อขายที่มีสภาพคล่องสูงสุด (New York Active Session 13:00-17:00 UTC)
- **การแปลงเป็นอัลกอริทึม cBot (C# Implementation):**  
  กฎเกณฑ์ของงานวิจัยถูกออกแบบเป็นระบบ Quantitative Rules ไร้การคาดเดา สามารถนำไปผนวกเข้ากับสถาปัตยกรรม `StrategyBase` ใน `BacktestLab` เพื่อทำการ Optimization และ Forward Test บน cTrader Automate ได้อย่างสมบูรณ์แบบ
