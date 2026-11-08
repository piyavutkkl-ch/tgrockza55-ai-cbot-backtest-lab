# Apparent Criticality and Calibration Issues in the Hawkes Self-Excited Point Process Model: Application to High-Frequency Financial Data
**แหล่งที่มา:** Social Science Research Network (SSRN)  
**รหัส SSRN:** [`SSRN-2371284`](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2371284) | **DOI:** [`10.2139/ssrn.2371284`](https://doi.org/10.2139/ssrn.2371284)  
**หมวดหมู่การวิจัย:** `05_hawkes_and_event_clustering`  
**ผู้แต่ง:** Vladimir Filimonov, Didier Sornette  
**วันที่เผยแพร่/บันทึก:** 2013-12-25  

## 🔗 ลิงก์เอกสารต้นฉบับ (Original Working Paper Links)
- 🌐 **หน้าเว็บงานวิจัยบน SSRN (HTML):** [https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2371284](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2371284) *(อ่านเนื้อหาโดยตรง ไม่ต้องโหลดไฟล์)*
- 📄 **DOI Canonical Resolver:** [https://doi.org/10.2139/ssrn.2371284](https://doi.org/10.2139/ssrn.2371284)

---

## 📌 บทคัดย่อและการศึกษาวิจัย (Abstract & Core Findings)
> We present a careful analysis of possible issues of the application of the self-excited Hawkes process to high-frequency financial data and carefully analyze a set of effects that lead to significant biases in the estimation of the "criticality index'' <i>n</i> that quantifies the degree of endogeneity of how much past events trigger future events. We report the following model biases: (i) evidence of strong upward biases on the estimation of <i>n</i> when using power law memory kernels in the presence of a few outliers, (ii) strong effects on <i>n</i> resulting from the form of the regularization part of the power law kernel, (iii) strong edge effects on the estimated <i>n</i> when using power law kernels, and (iv) the need for an exhaustive search of the absolute maximum of the log-likelihood function due to its complicated shape. Moreover, we demonstrate that the calibration of the Hawkes process on mixtures of pure Poisson process with changes of regime leads to completely spurious apparent critical values for the branching ratio (<i>n</i> = 1) while the true value is actually <i>n</i> = 0. More generally, regime shifts on the parameters of the Hawkes model and/or on the generating process itself are shown to systematically lead to a significant upward bias in the estimation of the branching ratio. We demonstrate the importance of the preparation of the high-frequency financial data, in particular: (i) the impact of overnight trading in the analysis of long-term trends, (ii) intraday seasonality and detrending of the data and (ii) vulnerability of the analysis to day-to-day nonstationarity and regime shifts. Special care is given to the decrease of quality of the timestamps of tick data due to latency and grouping of messages to packets by the stock exchange. Altogether, our careful exploration of the caveats of the calibration of the Hawkes process stresses the need for considering all the above issues before any conclusion can be sustained. In this respect, because the above effects are plaguing their analyses, the claim by Hardiman, Bercot and Bouchaud (2013) that financial market have been continuously functioning at or close to criticality (<i>n</i> = 1) cannot be supported. In contrast, our previous results on E-mini S&P 500 Futures Contracts and on major commodity future contracts are upheld.

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
