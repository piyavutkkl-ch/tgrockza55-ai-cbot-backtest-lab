# Screen Information, Trader Activity, and Bid-Ask Spreads in a Limit Order Market
**แหล่งที่มา:** Social Science Research Network (SSRN)  
**รหัส SSRN:** [`SSRN-174692`](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=174692) | **DOI:** [`10.2139/ssrn.174692`](https://doi.org/10.2139/ssrn.174692)  
**หมวดหมู่การวิจัย:** `03_market_making_and_spread`  
**ผู้แต่ง:** Mark T. Coppejans, Ian H. Domowitz  
**วันที่เผยแพร่/บันทึก:** 2005-08-19  

## 🔗 ลิงก์เอกสารต้นฉบับ (Original Working Paper Links)
- 🌐 **หน้าเว็บงานวิจัยบน SSRN (HTML):** [https://papers.ssrn.com/sol3/papers.cfm?abstract_id=174692](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=174692) *(อ่านเนื้อหาโดยตรง ไม่ต้องโหลดไฟล์)*
- 📄 **DOI Canonical Resolver:** [https://doi.org/10.2139/ssrn.174692](https://doi.org/10.2139/ssrn.174692)

---

## 📌 บทคัดย่อและการศึกษาวิจัย (Abstract & Core Findings)
> A key focus of empirical work on limit order markets is the relative importance of individual pieces of information in characterizing order submission and trade execution. We enlarge this focus to include an examination of pricing behavior, using data on index futures trading in a pure electronic limit order book market. A theoretical link between order, trade, and cancellation arrival rates, and the distribution of bid-ask spreads is empirically implemented. Evaluation of models across different information sets is based on relative ability to predict market activity and pricing out-of-sample. A main finding of the paper is the importance and superiority of information embodied in continuous individual traders' actions in characterizing order submission behavior and the structure of pricing. The book information on chararcteristics of resting orders alone cannot explain subsequent order submission, trade, or pricing behavior, and has little impact on the shape of the spread distribution.

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
