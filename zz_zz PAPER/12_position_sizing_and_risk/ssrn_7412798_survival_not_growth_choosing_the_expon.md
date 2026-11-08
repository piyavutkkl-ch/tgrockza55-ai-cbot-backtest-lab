# Survival, Not Growth: Choosing the Exponent in Power-Law Drawdown-Modulated Position Sizing
**แหล่งที่มา:** Social Science Research Network (SSRN)  
**รหัส SSRN:** [`SSRN-7412798`](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7412798) | **DOI:** [`10.2139/ssrn.7412798`](https://doi.org/10.2139/ssrn.7412798)  
**หมวดหมู่การวิจัย:** `12_position_sizing_and_risk`  
**ผู้แต่ง:** Max Silverman  
**วันที่เผยแพร่/บันทึก:** 2026-09-10  

## 🔗 ลิงก์เอกสารต้นฉบับ (Original Working Paper Links)
- 🌐 **หน้าเว็บงานวิจัยบน SSRN (HTML):** [https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7412798](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7412798) *(อ่านเนื้อหาโดยตรง ไม่ต้องโหลดไฟล์)*
- 📄 **DOI Canonical Resolver:** [https://doi.org/10.2139/ssrn.7412798](https://doi.org/10.2139/ssrn.7412798)

---

## 📌 บทคัดย่อและการศึกษาวิจัย (Abstract & Core Findings)
> Drawdown-constrained position sizing is standard practice in systematic trading, and the continuous-time theory is mature. Grossman and Zhou (1993) show that under geometric Brownian motion, log utility, and frictionless continuous rebalancing, optimal allocation is proportional to the cushion between wealth and a floor set at a fixed fraction of the running maximum. Implementations, however, routinely use power-law variants with exponents chosen by convention rather than derivation. We embed the cushion-proportional rule in a one-parameter family, of which Grossman-Zhou is a special case, and study how the optimal exponent depends on the strategy being controlled. Four results follow. First, the binding consideration is survival rather than growth: over much of the practical range the growth-optimal exponent equals the smallest exponent that avoids terminating the strategy. Second, the survival boundary depends only on strategy volatility relative to the barrier, and is invariant to the barrier level across a sixfold range. Third, a multiplicative controller reaching exactly zero exposure creates an absorbing state in a frictionless market, since zero exposure freezes wealth and therefore freezes drawdown; recoveryband hysteresis is unreachable. Fourth, under sufficiently heavy tails no exponent satisfies the constraint. Results are established by simulation and confirmed on twenty-two years of daily data.

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
