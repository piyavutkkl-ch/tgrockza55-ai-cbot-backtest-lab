# A Regime-Filtered Intraday Trading Framework for Gold: Integrating VWAP Microstructure and EMA-Based Dynamic Exit Mechanisms
**แหล่งที่มา:** Social Science Research Network (SSRN)  
**รหัส SSRN:** [`SSRN-6650958`](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6650958) | **DOI:** [`10.2139/ssrn.6650958`](https://doi.org/10.2139/ssrn.6650958)  
**หมวดหมู่การวิจัย:** `06_gold_commodity_and_macro`  
**ผู้แต่ง:** Amaanullah Bhatti  
**วันที่เผยแพร่/บันทึก:** 2026-04-26  

## 🔗 ลิงก์เอกสารต้นฉบับ (Original Working Paper Links)
- 🌐 **หน้าเว็บงานวิจัยบน SSRN (HTML):** [https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6650958](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6650958) *(อ่านเนื้อหาโดยตรง ไม่ต้องโหลดไฟล์)*
- 📄 **DOI Canonical Resolver:** [https://doi.org/10.2139/ssrn.6650958](https://doi.org/10.2139/ssrn.6650958)

---

## 📌 บทคัดย่อและการศึกษาวิจัย (Abstract & Core Findings)
> This paper presents, formalises, and empirically validates a fully rule-based intraday trading strategy for gold spot (XAU/USD) that integrates Volume-Weighted Average Price (VWAP) as a primary structural reference level with Exponential Moving Averages (EMAs) as dynamic trend filters and trailing stop mechanisms. The strategy directly addresses two chronic structural inefficiencies in short-term gold trading: (i) the propensity of gold prices to produce aggressive intrabar wicks that prematurely trigger conventional fixeddistance stop-loss orders, and (ii) the difficulty of managing open profit as price approaches known institutional reference levels. The 200-period EMA serves as a binary regime classifier; entry is conditioned on a precisely defined pullback and rejection signal at the 50-period EMA above (or below) the session VWAP; and the 50-period EMA functions as a dynamic trailing stop activated exclusively on candle closes, not intrabar wick penetrations. All entry conditions are stated as machine-testable quantitative rules, eliminating hidden discretion. A simulated backtest over 247 trades on the XAU/USD 15-minute timeframe (January-December 2024) produces a win rate of 45.3%, mean expectancy of +0.414R per trade, profit factor of 1.76, annualised Sharpe ratio of 3.99, and maximum drawdown of 5.1% on a fixed 1% risk-per-trade model, substantially outperforming a simple EMA crossover benchmark across all evaluated metrics. Risk management incorporates ATR-adjusted position sizing, a hard daily loss limit, and explicit news-event exclusion protocols.

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
