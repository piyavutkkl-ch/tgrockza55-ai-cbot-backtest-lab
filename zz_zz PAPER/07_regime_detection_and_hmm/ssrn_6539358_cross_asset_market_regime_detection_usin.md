# Cross-Asset Market Regime Detection Using Hidden Markov Models: A Framework for Real-Time Regime-Aware Risk Management
**แหล่งที่มา:** Social Science Research Network (SSRN)  
**รหัส SSRN:** [`SSRN-6539358`](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6539358) | **DOI:** [`10.2139/ssrn.6539358`](https://doi.org/10.2139/ssrn.6539358)  
**หมวดหมู่การวิจัย:** `07_regime_detection_and_hmm`  
**ผู้แต่ง:** Sumanth Polavarapu  
**วันที่เผยแพร่/บันทึก:** 2026-07-29  

## 🔗 ลิงก์เอกสารต้นฉบับ (Original Working Paper Links)
- 🌐 **หน้าเว็บงานวิจัยบน SSRN (HTML):** [https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6539358](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6539358) *(อ่านเนื้อหาโดยตรง ไม่ต้องโหลดไฟล์)*
- 📄 **DOI Canonical Resolver:** [https://doi.org/10.2139/ssrn.6539358](https://doi.org/10.2139/ssrn.6539358)

---

## 📌 บทคัดย่อและการศึกษาวิจัย (Abstract & Core Findings)
> <p>Standard quantitative risk models assume financial returns follow a normal distribution with constant volatility. This paper demonstrates empirically that this assumption fails during regime shifts, producing an 11.58 percentage point underestimation of annual tail risk for S&amp;P 500 returns spanning the 2020 COVID crisis and 2022 Federal Reserve rate shock (January 2020 – December 2024).</p> <p>We implement a cross-asset Gaussian Hidden Markov Model (HMM) — the Kroniq Regime Radar — using nine features across five asset classes: SPY, VIX, TLT, GLD, and ICE BofA US High Yield credit spreads (FRED: BAMLH0A0HYM2). A rigorous BIC model selection sweep across K=3 through K=9, with 5 independent random seeds per K and minimum state-size stability validation, confirms K=5 as the optimal and production-ready state count. Models at K=6, K=7, and K=8 produce unstable micro-states (as few as 9 days), inconsistent with reliable live regime routing.</p> <p>The five-state model produces a two-stage early warning for the March 2020 COVID crash: a Macro stress signal on October 1, 2019 — 141 calendar days before the February 19, 2020 SPY price peak — followed by full Crisis classification on February 28, 2020, before 79% of the total drawdown materialised. This 141-day lead time substantially extended early warning capability relative to the seven-feature baseline (23 days), attributable to the credit spread features; it is event-specific and not assumed to generalise as a consistent predictive horizon. Static out-of-sample performance (2021–2024): Sharpe 1.107, maximum drawdown -8.37%, CAGR 7.94%. Walk-forward OOS with quarterly retraining: Sharpe 0.881, MaxDD -17.46%, CAGR 9.97% — all exceeding buy-and-hold Sharpe of 0.859.</p> <p>The five-state transition probability matrix confirms regime persistence (Low-Vol: 95.5%, Bull: 92.7%, Neutral: 92.5%, Macro: 81.7%, Crisis: 73.0%) with no direct transitions from calm states to crisis within the observed training sample — consistent with how market dislocations actually unfold. Regime persistence is consistent with macro intuition, with states typically lasting multiple weeks to months rather than exhibiting high-frequency switching. The model demonstrates cross-event generalization across structurally distinct regime types: correctly classifying the fast COVID-2020 dislocation (Crisis state, VIX &gt; 48) and the prolonged 2022 Federal Reserve rate shock (Macro state, 99.2% classification purity) without structural modification. All three historical sanity checks pass. The objective is not to predict markets, but to dynamically adapt risk exposure to evolving regimes. These findings motivate the Kroniq framework: a cross-asset HMM regime detection API targeting institutional systematic funds.</p>

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
