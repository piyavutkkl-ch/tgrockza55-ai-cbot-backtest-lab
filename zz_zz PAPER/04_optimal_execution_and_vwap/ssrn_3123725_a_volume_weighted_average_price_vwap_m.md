# A Volume-Weighted-Average-Price (VWAP) Method for Estimating Beta in the Context of Reference-Day Risk.
**แหล่งที่มา:** Social Science Research Network (SSRN)  
**รหัส SSRN:** [`SSRN-3123725`](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3123725) | **DOI:** [`10.2139/ssrn.3123725`](https://doi.org/10.2139/ssrn.3123725)  
**หมวดหมู่การวิจัย:** `04_optimal_execution_and_vwap`  
**ผู้แต่ง:** Keshav Sahadev, Mike Ward, Chris Muller  
**วันที่เผยแพร่/บันทึก:** 2018-03-07  

## 🔗 ลิงก์เอกสารต้นฉบับ (Original Working Paper Links)
- 🌐 **หน้าเว็บงานวิจัยบน SSRN (HTML):** [https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3123725](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3123725) *(อ่านเนื้อหาโดยตรง ไม่ต้องโหลดไฟล์)*
- 📄 **DOI Canonical Resolver:** [https://doi.org/10.2139/ssrn.3123725](https://doi.org/10.2139/ssrn.3123725)

---

## 📌 บทคัดย่อและการศึกษาวิจัย (Abstract & Core Findings)
> The ability to accurately estimate systematic risk (or beta) in the presence of reference-day risk is an ineluctable requirement for all applications of the capital asset pricing model (CAPM). This research documents evidence of reference-day risk for shares on the Johannesburg All Share Index. In response to the need for greater accuracy when estimating systematic risk, this paper contributes a volume-weighted-average-price (VWAP) method for estimating beta when reference-day risk is exhibited in share betas. Furthermore, this research applies a graphical time-series approach to test the underlying risk-reward tenet postulated by the CAPM. Using beta as a measure of systematic risk, this research finds that the CAPM appears to imperfectly specify the risk-reward trade-off.

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
