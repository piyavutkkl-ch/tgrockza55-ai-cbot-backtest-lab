# Bid-Ask Spread Formula and Liquidity Cost: Risk and Reward of a Market Maker
**แหล่งที่มา:** Social Science Research Network (SSRN)  
**รหัส SSRN:** [`SSRN-229830`](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=229830) | **DOI:** [`10.2139/ssrn.229830`](https://doi.org/10.2139/ssrn.229830)  
**หมวดหมู่การวิจัย:** `03_market_making_and_spread`  
**ผู้แต่ง:** Sergei Esipov, Alex Morozovsky  
**วันที่เผยแพร่/บันทึก:** 2005-08-19  

## 🔗 ลิงก์เอกสารต้นฉบับ (Original Working Paper Links)
- 🌐 **หน้าเว็บงานวิจัยบน SSRN (HTML):** [https://papers.ssrn.com/sol3/papers.cfm?abstract_id=229830](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=229830) *(อ่านเนื้อหาโดยตรง ไม่ต้องโหลดไฟล์)*
- 📄 **DOI Canonical Resolver:** [https://doi.org/10.2139/ssrn.229830](https://doi.org/10.2139/ssrn.229830)

---

## 📌 บทคัดย่อและการศึกษาวิจัย (Abstract & Core Findings)
> One of the fundamental properties of most markets is the existence of more than one asset price or distribution of prices for a given asset. In many markets this distribution is clearly bi-modal, and can be related to the so-called "bid" and "ask" positions. The underlying detailed "microscopic" kinetics of bids, offers, and their matches can be complex and includes information flow along with capital and inventory balances. The reduction of a micro-model to the observed bid-ask spread determines the parameters of interest. We study a dynamic modification of the Garman model without inventory shortages, and obtain a relationship between the bid-ask spread, Value-at-Risk of the market maker, required returns, and the rate of arrivals of orders (measure of liquidity). Our formula for the bid-ask spread can be parametrized by historical data and used as a key ingredient in the information systems and/or automatic trading systems. The formula is derived in the risk-premium pricing framework suggested earlier by one of us and Guo. The bid-ask spread and liquidity costs are computed theoretically and compared with estimates for the most traded equity stocks. The remainder of the paper explores the benefits of dynamic bid-ask trading strategies.

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
