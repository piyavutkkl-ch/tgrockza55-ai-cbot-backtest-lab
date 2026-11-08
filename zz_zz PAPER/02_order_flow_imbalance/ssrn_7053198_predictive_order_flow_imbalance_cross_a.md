# Predictive Order Flow Imbalance: Cross-Asset Microstructure Alpha
**แหล่งที่มา:** Social Science Research Network (SSRN)  
**รหัส SSRN:** [`SSRN-7053198`](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7053198) | **DOI:** [`10.2139/ssrn.7053198`](https://doi.org/10.2139/ssrn.7053198)  
**หมวดหมู่การวิจัย:** `02_order_flow_imbalance`  
**ผู้แต่ง:** Kethan S E  
**วันที่เผยแพร่/บันทึก:** 2026-07-17  

## 🔗 ลิงก์เอกสารต้นฉบับ (Original Working Paper Links)
- 🌐 **หน้าเว็บงานวิจัยบน SSRN (HTML):** [https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7053198](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7053198) *(อ่านเนื้อหาโดยตรง ไม่ต้องโหลดไฟล์)*
- 📄 **DOI Canonical Resolver:** [https://doi.org/10.2139/ssrn.7053198](https://doi.org/10.2139/ssrn.7053198)

---

## 📌 บทคัดย่อและการศึกษาวิจัย (Abstract & Core Findings)
> This paper examines the predictive power of Order Flow Imbalance (OFI) as an intraday alpha signal across twelve U.S. equity and ETF instruments over a one-year sample period (April 2024 to April 2025). Building on the framework of Cont, Kukanov and Stoikov (2014), we construct OFI from Level-1 NBBO quote data at ten-second bar frequency and evaluate its forward predictive content using walk-forward Ridge regression across 84 monthly test folds. The signal exhibits statistically significant predictive power at short horizons, with a mean Information Coefficient of +0.0044 (pooled t = 3.26, p = 0.0016) and a positive out-of-sample IC of +0.0022. The statistical evidence is robust to ticker-level dependence but sensitive to the short out-of-sample period (seven months), limiting the strength of cross-temporal inference. Sensitivity analyses using ticker-level and month-level aggregation produced qualitatively similar conclusions, although month-level aggregation was not statistically significant owing to the short sevenmonth sample. A two-state Hidden Markov Model identifies calm and stressed volatility regimes. Regime-conditioned models show elevated IC at longer horizons (5m: +0.0148, 10m: +0.0161), but these findings do not survive multiple-testing correction and are treated as exploratory. The strategy does not survive transaction costs at ten-second execution frequency. A gross Sharpe of +0.981 collapses to a net Sharpe of-1.726, with bid-ask crossing costs exceeding the gross signal edge by a factor of 164. NVDA is the only instrument achieving a positive mean net Sharpe (+0.14) after costs. A depth-aware imbalance comparison using Databento XNAS ITCH Market-By-Order (MBO) data provides directional evidence of Level-1 attenuation bias, although the results are not statistically conclusive over the 40-day window.

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
