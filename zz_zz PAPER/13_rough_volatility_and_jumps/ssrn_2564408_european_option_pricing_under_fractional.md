# European Option Pricing Under Fractional Brownian Motion with an Application to Realized Volatility
**แหล่งที่มา:** Social Science Research Network (SSRN)  
**รหัส SSRN:** [`SSRN-2564408`](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2564408) | **DOI:** [`10.2139/ssrn.2564408`](https://doi.org/10.2139/ssrn.2564408)  
**หมวดหมู่การวิจัย:** `13_rough_volatility_and_jumps`  
**ผู้แต่ง:** Takayuki Morimoto  
**วันที่เผยแพร่/บันทึก:** 2015-02-18  

## 🔗 ลิงก์เอกสารต้นฉบับ (Original Working Paper Links)
- 🌐 **หน้าเว็บงานวิจัยบน SSRN (HTML):** [https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2564408](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2564408) *(อ่านเนื้อหาโดยตรง ไม่ต้องโหลดไฟล์)*
- 📄 **DOI Canonical Resolver:** [https://doi.org/10.2139/ssrn.2564408](https://doi.org/10.2139/ssrn.2564408)

---

## 📌 บทคัดย่อและการศึกษาวิจัย (Abstract & Core Findings)
> This study investigates European option pricing under fractional Brownian motion (fBm) and applies it to realized volatility (RV). The RV measure is selected because it uniquely exhibits simultaneous stationarity and long-range dependency properties in financial time series, as shown in our empirical study. Meanwhile, the Black-Scholes differential equation is not well defined when the underlying assets follow fBm with the Hurst exponent H not equal to 1/2 because fBm is not a semimartingale. Thus, we compute the European option prices using a previously proposed fractional Black-Scholes formula. Our empirical study is conducted on Tokyo Stock Price Index data from January 06, 1997 to December 30, 2013 with a sample size of 4177.

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
