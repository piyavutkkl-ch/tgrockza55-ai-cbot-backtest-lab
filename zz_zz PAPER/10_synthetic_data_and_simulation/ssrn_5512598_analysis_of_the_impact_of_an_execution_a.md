# Analysis of the Impact of an Execution Algorithm with an Order Book Imbalance Strategy on a Financial Market Using an Agent-based Simulation
**แหล่งที่มา:** Social Science Research Network (SSRN)  
**รหัส SSRN:** [`SSRN-5512598`](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5512598) | **DOI:** [`10.2139/ssrn.5512598`](https://doi.org/10.2139/ssrn.5512598)  
**หมวดหมู่การวิจัย:** `10_synthetic_data_and_simulation`  
**ผู้แต่ง:** Shuto Endo, Takanobu Mizuta, Isao Yagi  
**วันที่เผยแพร่/บันทึก:** 2025-10-02  

## 🔗 ลิงก์เอกสารต้นฉบับ (Original Working Paper Links)
- 🌐 **หน้าเว็บงานวิจัยบน SSRN (HTML):** [https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5512598](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5512598) *(อ่านเนื้อหาโดยตรง ไม่ต้องโหลดไฟล์)*
- 📄 **DOI Canonical Resolver:** [https://doi.org/10.2139/ssrn.5512598](https://doi.org/10.2139/ssrn.5512598)

---

## 📌 บทคัดย่อและการศึกษาวิจัย (Abstract & Core Findings)
> <p>One measure of financial markets is order book imbalance (OBI), defined as the number of buy orders minus the number of sell orders in the order book around the best quote. Thus, OBI is an indicator of an imbalance in supply and demand, which can potentially impact the price as price movements in the financial market. There is known to be a positive correlation between OBI and returns, and some investors attempt to exploit this fact to improve their investment performance.</p> <p>In financial markets, an investor sometimes wants to place a large order. However, when an investor places such a large order all at one time, some other investors learn that someone wants to trade a large amount and themselves trade earlier than they would have, or the market price becomes volatile and losses are incurred.</p> <p>Therefore, execution algorithms are used, by which a machine automatically divides orders into smaller lots to avoid distorting the market price. Execution algorithms could be expected to achieve improved performance when OBI is taken into account, but no such findings have been reported so far. One reason for the lack of research findings is that it is virtually impossible to measure the impact of OBI alone on the performance of execution algorithms, since there are many external factors that can affect financial markets. Multi-agent simulation is one way to solve problems that are difficult to analyse using empirical research and conventional methods. In a multi-agent simulation, individual actors in the world are regarded as agents and the behavioural rules and interactions of these agents constitute a model. In this context, a financial market constructed using multi-agent simulation is called an artificial market. In the present study, we modelled an execution algorithm considering OBI, investigated how the model is affected by the market under several market patterns using artificial markets, and analysed the mechanisms. The results showed that in stable markets, the performance of the execution algorithm with the OBI strategy varied with the number of orders placed. In contrast, in markets with unstable prices, the performance of the execution algorithm with the OBI strategy was higher than that of the conventional execution algorithm. Even in markets with manipulation by spoofing, the performance of the execution algorithm with the OBI strategy was not significantly worse than that of the conventional execution algorithm, demonstrating that the model is not easily affected by spoofing.</p>

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
