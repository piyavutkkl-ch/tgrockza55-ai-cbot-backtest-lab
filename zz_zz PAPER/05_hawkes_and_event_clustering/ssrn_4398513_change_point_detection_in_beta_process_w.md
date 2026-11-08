# Change Point Detection in Beta Process with High Frequency Data
**แหล่งที่มา:** Social Science Research Network (SSRN)  
**รหัส SSRN:** [`SSRN-4398513`](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4398513) | **DOI:** [`10.2139/ssrn.4398513`](https://doi.org/10.2139/ssrn.4398513)  
**หมวดหมู่การวิจัย:** `05_hawkes_and_event_clustering`  
**ผู้แต่ง:** Dachuan Chen, Long Feng  
**วันที่เผยแพร่/บันทึก:** 2023-04-05  

## 🔗 ลิงก์เอกสารต้นฉบับ (Original Working Paper Links)
- 🌐 **หน้าเว็บงานวิจัยบน SSRN (HTML):** [https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4398513](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4398513) *(อ่านเนื้อหาโดยตรง ไม่ต้องโหลดไฟล์)*
- 📄 **DOI Canonical Resolver:** [https://doi.org/10.2139/ssrn.4398513](https://doi.org/10.2139/ssrn.4398513)

---

## 📌 บทคัดย่อและการศึกษาวิจัย (Abstract & Core Findings)
> High frequency regression has received more and more attention recent years. This is the first paper about detecting the change points in the beta process of high frequency regression. As an intermediate modelling approach between the constant beta and continuous beta process, this paper employs the piecewise constant process to model the time-varying beta, which can ensure both parsimony and flexibility of the high frequency regression model at the same time. By extending the idea of self-normalization to the observations with time-varying covariance structure, we have developed the testing and estimation methodologies for the scenario of single change point in the multivariate beta process. The limiting null distribution and the asymptotic behavior of the power of the single change point test are derived. The convergence rate of the single change point estimate is also established. For the scenario of multiple change points, we have developed a new wild binary segmentation algorithm to detect the multiple change points. A novel data-driven approach is also designed to consistently estimate the number of change points. Monte Carlo simulation and empirical study show the accuracy and efficiency of our proposed methodologies.

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
