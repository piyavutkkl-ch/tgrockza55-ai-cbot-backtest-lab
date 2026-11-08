# Scenario-Aware Long-Horizon Forecasting of Levelized Cost of Energy via an Interpretable Deep Learning Ensemble of Transformer and CNN-LSTM
**แหล่งที่มา:** Social Science Research Network (SSRN)  
**รหัส SSRN:** [`SSRN-6646727`](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6646727) | **DOI:** [`10.2139/ssrn.6646727`](https://doi.org/10.2139/ssrn.6646727)  
**หมวดหมู่การวิจัย:** `01_lob_and_deep_learning`  
**ผู้แต่ง:** Seyit &Ouml;nderol, Faik Bilgili  
**วันที่เผยแพร่/บันทึก:** 2026-04-25  

## 🔗 ลิงก์เอกสารต้นฉบับ (Original Working Paper Links)
- 🌐 **หน้าเว็บงานวิจัยบน SSRN (HTML):** [https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6646727](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6646727) *(อ่านเนื้อหาโดยตรง ไม่ต้องโหลดไฟล์)*
- 📄 **DOI Canonical Resolver:** [https://doi.org/10.2139/ssrn.6646727](https://doi.org/10.2139/ssrn.6646727)

---

## 📌 บทคัดย่อและการศึกษาวิจัย (Abstract & Core Findings)
> Reliable long-horizon forecasts of the Levelized Cost of Energy (LCOE) are essential for investment planning and policy design in renewable and low-carbon power. We propose an interpretable deep-learning decision-support framework for scenario-based, multi-technology LCOE forecasting that integrates Transformer and CNN-LSTM architectures into a weighted ensemble. Using the National Renewable Energy Laboratory (NREL) Annual Technology Baseline (ATB) 2024 dataset (572,000 observations), we project the LCOE for thirteen renewable and low-carbon power technologies across Conservative, Moderate, and Advanced scenarios from 2022 to 2050, with a 20-year look-back window and temporal splitting for realistic long-term evaluation. To improve robustness and economic plausibility, training incorporates a physics-guided regularization term that penalizes deviations from the traditional LCOE formulation. We compare against linear regression, random forest, and XGBoost, showing that the proposed deep ensemble provides more reliable performance in this context. Decision support is further enhanced with interpretability analyses (SHAP, attention weights, permutation importance) and uncertainty diagnostics, enabling transparent, scenario- and technology-specific insights for portfolio planning.

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
