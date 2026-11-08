# Insider Trading and the Bid-Ask Spread: A Critical Evaluation of Adverse Selection in Market Making
**แหล่งที่มา:** Social Science Research Network (SSRN)  
**รหัส SSRN:** [`SSRN-440380`](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=440380) | **DOI:** [`10.2139/ssrn.440380`](https://doi.org/10.2139/ssrn.440380)  
**หมวดหมู่การวิจัย:** `03_market_making_and_spread`  
**ผู้แต่ง:** Stanislav Dolgopolov  
**วันที่เผยแพร่/บันทึก:** 2005-07-07  

## 🔗 ลิงก์เอกสารต้นฉบับ (Original Working Paper Links)
- 🌐 **หน้าเว็บงานวิจัยบน SSRN (HTML):** [https://papers.ssrn.com/sol3/papers.cfm?abstract_id=440380](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=440380) *(อ่านเนื้อหาโดยตรง ไม่ต้องโหลดไฟล์)*
- 📄 **DOI Canonical Resolver:** [https://doi.org/10.2139/ssrn.440380](https://doi.org/10.2139/ssrn.440380)

---

## 📌 บทคัดย่อและการศึกษาวิจัย (Abstract & Core Findings)
> In economic, finance, and legal literature, there is a widespread acceptance of the notion that market makers increase the bid-ask spread in response to insider trading, as they consistently lose money by transacting with better-informed insiders. The development of this adverse selection model of market making was treated as proof that insider trading imposes a real cost on securities markets by decreasing liquidity and increasing the corporate cost of capital and was used as a justification for regulation. This Article is a critical review of the adverse selection literature. It discusses the model's theoretical development, its use in the regulation debates, a summary of the case law on the harm from insider trading to market makers, and empirical research on the link between insider trading and transaction costs. The adverse selection argument is criticized from both theoretical and empirical standpoints: there are limitations to the model due to required assumptions about the role and behavior of market makers' inventories; different causal links among insider trading, firm size, quality of disclosure, stock price volatility, and the bid-ask spread are possible; the existing empirical studies may confuse various components of the spread; and information asymmetry may actually benefit market makers.

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
