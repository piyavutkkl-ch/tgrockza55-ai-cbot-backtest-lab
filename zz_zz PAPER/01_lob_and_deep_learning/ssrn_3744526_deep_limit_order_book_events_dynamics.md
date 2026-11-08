# Deep Limit Order Book Events Dynamics
**แหล่งที่มา:** Social Science Research Network (SSRN)  
**รหัส SSRN:** [`SSRN-3744526`](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3744526) | **DOI:** [`10.2139/ssrn.3744526`](https://doi.org/10.2139/ssrn.3744526)  
**หมวดหมู่การวิจัย:** `01_lob_and_deep_learning`  
**ผู้แต่ง:** Yann Bilodeau  
**วันที่เผยแพร่/บันทึก:** 2021-02-13  

## 🔗 ลิงก์เอกสารต้นฉบับ (Original Working Paper Links)
- 🌐 **หน้าเว็บงานวิจัยบน SSRN (HTML):** [https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3744526](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3744526) *(อ่านเนื้อหาโดยตรง ไม่ต้องโหลดไฟล์)*
- 📄 **DOI Canonical Resolver:** [https://doi.org/10.2139/ssrn.3744526](https://doi.org/10.2139/ssrn.3744526)

---

## 📌 บทคัดย่อและการศึกษาวิจัย (Abstract & Core Findings)
> This paper analyzes the limit order book events arrival dependency structure using high-dimensional Hawkes processes. We seek for recurrent relationships among events from a set of 86 event types which in addition to transactions, includes limit order submissions and cancellations taking place up to the 20th depth level of the order book. We focus on BMW, SAP, and ADS, three liquid DAX 30 index stocks for which we have a microsecond stamped high-frequency dataset covering the 61 trading day period going from February 1 to March 31, 2013. For each stock, we build a tailored descriptive model by selecting recurrent events relationships. Estimated on a daily basis, we find that the selected models offer interesting data fitting performance, particularly for limit order submissions and cancellations occurring on the first five price levels of the order book. Finally, we use the comprehensive sets of estimated parameters to describe a global events arrival dynamics that we relate to the potential behaviors of market participants having different objectives and directional views.

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
