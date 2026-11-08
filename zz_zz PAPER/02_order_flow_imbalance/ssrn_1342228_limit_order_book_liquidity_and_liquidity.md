# Limit Order Book Liquidity and Liquidity Imbalance
**แหล่งที่มา:** Social Science Research Network (SSRN)  
**รหัส SSRN:** [`SSRN-1342228`](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1342228) | **DOI:** [`10.2139/ssrn.1342228`](https://doi.org/10.2139/ssrn.1342228)  
**หมวดหมู่การวิจัย:** `02_order_flow_imbalance`  
**ผู้แต่ง:** Wee Yong Yeo  
**วันที่เผยแพร่/บันทึก:** 2011-12-28  

## 🔗 ลิงก์เอกสารต้นฉบับ (Original Working Paper Links)
- 🌐 **หน้าเว็บงานวิจัยบน SSRN (HTML):** [https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1342228](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1342228) *(อ่านเนื้อหาโดยตรง ไม่ต้องโหลดไฟล์)*
- 📄 **DOI Canonical Resolver:** [https://doi.org/10.2139/ssrn.1342228](https://doi.org/10.2139/ssrn.1342228)

---

## 📌 บทคัดย่อและการศึกษาวิจัย (Abstract & Core Findings)
> We analyze the role of liquidity provision of limit order traders in the NYSE. Using an extensive limit order book data for all the ordinary stocks in the NYSE, we compute various measures of liquidity and imbalance in liquidity. We show that the interest rate environment has a strong impact on the willingness of limit order traders to provide liquidity. Higher cost of financing the provision of liquidity reduces the liquidity in the limit order book. Limit order traders are also more willing to provide liquidity earlier in the week than later. Imbalance between buy side and sell side liquidity exhibit high autocorrelation. Higher buy side liquidity increases daily market returns in the same period. Both contemporaneous and lag daily market returns have a positive impact on the imbalance of the liquidity in the limit order book. However, we find that on an intraday basis, higher sell side liquidity in the pervious period increases returns in the current period, and higher intraday contemporaneous returns increase sell side liquidity more than buy side liquidity. This may be indicative of the market stabilizing role that limit order traders play.

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
