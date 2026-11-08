# Modeling High Frequency Market Order Dynamics Using Self-Excited Point Process
**แหล่งที่มา:** Social Science Research Network (SSRN)  
**รหัส SSRN:** [`SSRN-1668160`](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1668160) | **DOI:** [`10.2139/ssrn.1668160`](https://doi.org/10.2139/ssrn.1668160)  
**หมวดหมู่การวิจัย:** `05_hawkes_and_event_clustering`  
**ผู้แต่ง:** Howard Howan Stephen Shek  
**วันที่เผยแพร่/บันทึก:** 2012-01-05  

## 🔗 ลิงก์เอกสารต้นฉบับ (Original Working Paper Links)
- 🌐 **หน้าเว็บงานวิจัยบน SSRN (HTML):** [https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1668160](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1668160) *(อ่านเนื้อหาโดยตรง ไม่ต้องโหลดไฟล์)*
- 📄 **DOI Canonical Resolver:** [https://doi.org/10.2139/ssrn.1668160](https://doi.org/10.2139/ssrn.1668160)

---

## 📌 บทคัดย่อและการศึกษาวิจัย (Abstract & Core Findings)
> This paper extends the self-excited point process framework to model conditional arrival intensities of buy and sell orders of listed stocks. The cross-excitation of market orders is modeled explicitly such that buy size and buy side order book cumulative volume can affect the sell order intensity, and vice versa. Different variations of the framework are estimated by using method of maximum likelihood estimation, using a recursive application of the log-likelihood functions derived in this paper. Results indicate that by incorporating an order imbalance measure related to the probability weighted cumulative queue volume at the bid and ask sides of the market, one can improve the overall model goodness-of-fit significantly.

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
