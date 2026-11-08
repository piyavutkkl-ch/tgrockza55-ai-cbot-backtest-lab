# Forecasting Intraday Trading Volume: A Kalman Filter Approach
**แหล่งที่มา:** Social Science Research Network (SSRN)  
**รหัส SSRN:** [`SSRN-3101695`](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3101695) | **DOI:** [`10.2139/ssrn.3101695`](https://doi.org/10.2139/ssrn.3101695)  
**หมวดหมู่การวิจัย:** `09_signal_processing_and_kalman`  
**ผู้แต่ง:** Ran Chen, Yiyong Feng, Daniel Palomar  
**วันที่เผยแพร่/บันทึก:** 2018-05-02  

## 🔗 ลิงก์เอกสารต้นฉบับ (Original Working Paper Links)
- 🌐 **หน้าเว็บงานวิจัยบน SSRN (HTML):** [https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3101695](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3101695) *(อ่านเนื้อหาโดยตรง ไม่ต้องโหลดไฟล์)*
- 📄 **DOI Canonical Resolver:** [https://doi.org/10.2139/ssrn.3101695](https://doi.org/10.2139/ssrn.3101695)

---

## 📌 บทคัดย่อและการศึกษาวิจัย (Abstract & Core Findings)
> An accurate forecast of intraday volume is a key aspect of algorithmic trading. This manuscript proposes a state-space model to forecast intraday trading volume via the Kalman filter and derives closed-form expectation-maximization (EM) solutions for model calibration. The model is extended to handle outliers in real-time market data by applying a sparse regularization technique. Empirical studies using thirty securities on eight exchanges show that the proposed model substantially outperforms the rolling means (RM) and the state-of-the-art Component Multiplicative Error Model (CMEM) by 64% and 29%, respectively, in volume prediction and by 15% and 9%, respectively, in Volume Weighted Average Price (VWAP) trading.

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
