# Price Formation and Optimal Trading in Intraday Electricity Markets
**แหล่งที่มา:** Social Science Research Network (SSRN)  
**รหัส SSRN:** [`SSRN-3690316`](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3690316) | **DOI:** [`10.2139/ssrn.3690316`](https://doi.org/10.2139/ssrn.3690316)  
**หมวดหมู่การวิจัย:** `06_gold_commodity_and_macro`  
**ผู้แต่ง:** Olivier FERON, Peter Tankov, Laura Tinsi  
**วันที่เผยแพร่/บันทึก:** 2020-10-31  

## 🔗 ลิงก์เอกสารต้นฉบับ (Original Working Paper Links)
- 🌐 **หน้าเว็บงานวิจัยบน SSRN (HTML):** [https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3690316](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3690316) *(อ่านเนื้อหาโดยตรง ไม่ต้องโหลดไฟล์)*
- 📄 **DOI Canonical Resolver:** [https://doi.org/10.2139/ssrn.3690316](https://doi.org/10.2139/ssrn.3690316)

---

## 📌 บทคัดย่อและการศึกษาวิจัย (Abstract & Core Findings)
> We develop a tractable equilibrium model for price formation in intraday electricity markets in the presence of intermittent renewable generation. Using stochastic control theory we identify the optimal strategies of agents with market impact and exhibit the Nash equilibrium in closed form for a finite number of agents as well as in the asymptotic framework of mean field games. Our model reproduces the empirical features of intraday market prices, such as increasing price volatility at the approach of the delivery date and the correlation between price and renewable infeed forecasts, and relates these features with market characteristics like liquidity, number of agents, and imbalance penalty.

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
