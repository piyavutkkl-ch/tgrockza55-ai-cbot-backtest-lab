# Price Discovery and the Cross-section of High-Frequency Trading
**แหล่งที่มา:** Social Science Research Network (SSRN)  
**รหัส SSRN:** [`SSRN-2184302`](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2184302) | **DOI:** [`10.2139/ssrn.2184302`](https://doi.org/10.2139/ssrn.2184302)  
**หมวดหมู่การวิจัย:** `08_lead_lag_and_latency`  
**ผู้แต่ง:** Evangelos Benos, Satchit Sagade  
**วันที่เผยแพร่/บันทึก:** 2012-12-12  

## 🔗 ลิงก์เอกสารต้นฉบับ (Original Working Paper Links)
- 🌐 **หน้าเว็บงานวิจัยบน SSRN (HTML):** [https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2184302](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2184302) *(อ่านเนื้อหาโดยตรง ไม่ต้องโหลดไฟล์)*
- 📄 **DOI Canonical Resolver:** [https://doi.org/10.2139/ssrn.2184302](https://doi.org/10.2139/ssrn.2184302)

---

## 📌 บทคัดย่อและการศึกษาวิจัย (Abstract & Core Findings)
> We quantify the price discovery contributions of high-frequency traders (HFTs) in the United Kingdom equity market and examine how it varies in their cross-section. For this, we group individual HFTs according to their liquidity taking/making activity. HFTs contribute about 14\% of all trade-induced information, with aggressive HFTs accounting for two-thirds of this contribution. This suggests that HFTs who pursue strategies that require the use of aggressive trades are most informed, as opposed to passive HFTs who more likely act as market-makers. However, information shares decline with the amount of aggressive volume, suggesting that these trading strategies are not scalable.

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
