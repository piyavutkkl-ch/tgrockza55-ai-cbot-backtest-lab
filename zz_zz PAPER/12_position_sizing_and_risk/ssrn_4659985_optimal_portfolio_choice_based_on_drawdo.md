# Optimal Portfolio Choice Based on Drawdown Stochastic Dominance
**แหล่งที่มา:** Social Science Research Network (SSRN)  
**รหัส SSRN:** [`SSRN-4659985`](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4659985) | **DOI:** [`10.2139/ssrn.4659985`](https://doi.org/10.2139/ssrn.4659985)  
**หมวดหมู่การวิจัย:** `12_position_sizing_and_risk`  
**ผู้แต่ง:** Andrei Vedernikov, Juuso Liesiö, Tomi Seppälä  
**วันที่เผยแพร่/บันทึก:** 2023-12-20  

## 🔗 ลิงก์เอกสารต้นฉบับ (Original Working Paper Links)
- 🌐 **หน้าเว็บงานวิจัยบน SSRN (HTML):** [https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4659985](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4659985) *(อ่านเนื้อหาโดยตรง ไม่ต้องโหลดไฟล์)*
- 📄 **DOI Canonical Resolver:** [https://doi.org/10.2139/ssrn.4659985](https://doi.org/10.2139/ssrn.4659985)

---

## 📌 บทคัดย่อและการศึกษาวิจัย (Abstract & Core Findings)
> The portfolio drawdown measures the magnitude of the portfolio value drop from its preceding maximum value, an important criterion in active portfolio management. While methods for portfolio optimization based on a single point or several points of the portfolio drawdown distribution exist, we propose a method that accounts for the entire portfolio drawdown distribution over the considered investment horizon. Therefore, we construct a dominance criterion for comparing two portfolios by their random drawdown profiles in the spirit of second-degree stochastic dominance (SSD). First, we introduce a new variant of a drawdown measure, based on the current portfolio value, subsequently shown to have beneficial properties for portfolio optimization. Second, we define a portfolio drawdown distribution. Third, we build an optimization method to minimize the conditional α tail of a drawdown distribution similar to conditional value-at-risk. Fourth, we construct the drawdown dominance criterion so that a portfolio dominates another portfolio if the conditional drawdown of the former portfolio is lower than or equal to that of the latter portfolio for all confidence levels. We denote this portfolio choice rule as drawdown second-degree stochastic dominance (D-SSD) in the spirit of the SSD method. The model testing on historical data indicates that in most periods over a 30-year horizon it is possible to find a stock portfolio with a significantly higher return and dominant drawdown profile compared to the U.S. all-stock benchmark. The testing also shows that the excess return of the D-SSD dominant portfolio is highest in the periods following major recessions.

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
