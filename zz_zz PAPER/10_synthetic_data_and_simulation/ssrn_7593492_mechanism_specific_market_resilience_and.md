# Mechanism-specific market resilience and size-dependent nonlinear response in a unified limit-order-book agent-based model ​
**แหล่งที่มา:** Social Science Research Network (SSRN)  
**รหัส SSRN:** [`SSRN-7593492`](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7593492) | **DOI:** [`10.2139/ssrn.7593492`](https://doi.org/10.2139/ssrn.7593492)  
**หมวดหมู่การวิจัย:** `10_synthetic_data_and_simulation`  
**ผู้แต่ง:** Arina Ravilova, Igor Goncharov, Elizaveta Kantemirova, Petr Lukianchenko  
**วันที่เผยแพร่/บันทึก:** 2026-10-10  

## 🔗 ลิงก์เอกสารต้นฉบับ (Original Working Paper Links)
- 🌐 **หน้าเว็บงานวิจัยบน SSRN (HTML):** [https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7593492](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7593492) *(อ่านเนื้อหาโดยตรง ไม่ต้องโหลดไฟล์)*
- 📄 **DOI Canonical Resolver:** [https://doi.org/10.2139/ssrn.7593492](https://doi.org/10.2139/ssrn.7593492)

---

## 📌 บทคัดย่อและการศึกษาวิจัย (Abstract & Core Findings)
> Instability in electronic markets is usually attributed to a single local cause: a news event, a speed advantage, a liquidity shortage or an operational outage. In a limit-order-book market populated by interacting heterogeneous traders, however, the response to any of these disturbances is a collective property that depends jointly on the composition of the population, on the timing of information and execution, and on the state of the book. We study this collective response in a single continuous double-auction agent-based model with noise traders, fundamentalists, trend-following chartists with Lux–Marchesi-type opinion dynamics, strategy-switching agents and an inventory-constrained market maker. The same engine is subjected to eight distinct frictions and shocks: an execution-speed advantage for a share φ of chartists, event-time versus calendar-time measurement, delayed observation of the book combined with thin or deep initial liquidity, server-side execution latency, temporary loss of participation, belief (news) shocks, shifts of the fundamental value, and changes in trader aggressiveness. The campaign comprises 11 250 Monte Carlo runs plus 660 runs at larger population sizes. All comparisons are reported as effect sizes with bootstrap confidence intervals and Monte Carlo precision diagnostics, and the baseline dynamics are checked against the empirical stylised facts. The model reproduces heavy-tailed returns and positive dependence of volatility proxies; a pure power-law tail is not supported by a Clauset–Shalizi–Newman test, and the tail index lies above the empirical cubic law, which we relate to the finite population and to the bounded order-size rules. The joint effect of stale information and thin liquidity on post-shock drawdown, the volatility increase under recurrent news, and the lengthening of recovery after large fundamental shifts are large and stable; the event-time and latency contrasts are not resolved at the planned sample sizes. The execution-speed response is nonlinear in φ and its threshold location moves from φ∗ = 0.2 at N = 26 to 0.5 at N = 51 and 0.6 at N = 76, while the fluctuation peak does not track the threshold and the response does not sharpen with size. We therefore read the speed response as a size-dependent nonlinear crossover rather than as evidence of a critical point, and we spell out the finite-size scaling programme that would be required to decide the question. Market resilience emerges as mechanism-specific and must be assessed jointly across price, liquidity, tail, recovery and size-scaling measures. ​

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
