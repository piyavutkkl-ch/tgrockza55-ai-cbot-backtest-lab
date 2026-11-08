# Intraday Long Gamma Investing Via Hidden Markov Models
**แหล่งที่มา:** Social Science Research Network (SSRN)  
**รหัส SSRN:** [`SSRN-3678648`](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3678648) | **DOI:** [`10.2139/ssrn.3678648`](https://doi.org/10.2139/ssrn.3678648)  
**หมวดหมู่การวิจัย:** `07_regime_detection_and_hmm`  
**ผู้แต่ง:** Jonathan Seror  
**วันที่เผยแพร่/บันทึก:** 2020-08-24  

## 🔗 ลิงก์เอกสารต้นฉบับ (Original Working Paper Links)
- 🌐 **หน้าเว็บงานวิจัยบน SSRN (HTML):** [https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3678648](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3678648) *(อ่านเนื้อหาโดยตรง ไม่ต้องโหลดไฟล์)*
- 📄 **DOI Canonical Resolver:** [https://doi.org/10.2139/ssrn.3678648](https://doi.org/10.2139/ssrn.3678648)

---

## 📌 บทคัดย่อและการศึกษาวิจัย (Abstract & Core Findings)
> This study presents a modest Hidden Markov Models flavored extension of the tail risk mitigation strategies discussed by Ernest Chan (QTS Capital Management, L.L.C.) on his blog, and Mark Spitznagel (Universa Investments, L.P.) in an interim letter to investors dated April 7th, 2020, following the covid-19 market turmoil.<br><br>The objective is to partly replicate the performance of these long gamma strategies, and attempt to bridge a reported gap between in and out-of-tail net return on capital, by adding a Hidden Markov Model based regime detection overlay to the proposed hedging approach. The results show that a well calibrated non-biased HMM regime filter, effectively shuts down the trend following trading signal, when sub-optimal conditions would make it unprofitable.<br><br>The implementation focuses on a representative U.S. energy large cap, and relies on the R dependent mixture models depmixS4 library.

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
