# 🏛️ คู่มือและคลังงานวิจัยทางการเงินฉบับสมบูรณ์สำหรับพัฒนา Trading Bot
## (Quantitative Finance & Microstructure Master Research Repository)

> **เป้าหมายโครงการ:** สกัดทฤษฎีทางคณิตศาสตร์ โครงสร้างตลาดจุลภาค (Market Microstructure), สัญญาณดิจิทัล, และโมเดล Machine Learning/Deep Learning จากงานวิจัยระดับโลก **รวม 141 งานวิจัย ครอบคลุม 13 เสาหลัก** เพื่อนำมาแปลงเป็นอัลกอริทึมเทรดอัตโนมัติ (cTrader C# Robot & Python BacktestLab) สำหรับสินทรัพย์ **XAUUSD (Gold), BTCUSD และ ETHUSD**

---

## ⚡ สรุปแนวทางการเข้าถึงเอกสาร (HTML Full-Text Standard)

เพื่อความรวดเร็วและป้องกันปัญหา **Rate Limit (HTTP 429)**:
1. **อ่านผ่าน HTML ทันที:** arXiv มีหน้าเว็บ HTML เต็มรูปแบบที่ [https://arxiv.org/html/<id>](https://arxiv.org/html/1808.03668) แสดงสูตรคณิตศาสตร์ (LaTeX) และแผนผังโมเดลครบถ้วน
2. **คลังบทสรุปในโฟลเดอร์:** มีเอกสารสรุป (`.md`) ในแต่ละหมวดหมู่พร้อมลิงก์ตรงและข้อพิจารณาในการเขียนโค้ด
3. **ไฟล์ฐานข้อมูล:** จัดเก็บ Metadata ครบ 141 งานวิจัยไว้ใน [`papers_database.json`](file:///d:/cbot-atgvt/zz_zz%20PAPER/papers_database.json)

---

## 🗺️ แผนผัง 13 เสาหลักของงานวิจัย (The 13 Pillars for Quantitative Bot Trading)

| หมวดหมู่ | โฟลเดอร์ | ประโยชน์ต่อ Bot Trade | งานวิจัยเด่น |
| :--- | :--- | :--- | :--- |
| **1. LOB & Deep Learning** 🧠 | [`01_lob_and_deep_learning/`](file:///d:/cbot-atgvt/zz_zz%20PAPER/01_lob_and_deep_learning/) | นำข้อมูล DOM Level 2 (Bid/Ask Depth) ป้อน CNN/LSTM เพื่อทำนายทิศทาง 5 แท่ง M1 | `1808.03668` (DeepLOB)<br>`2403.13429` (Spoofing TCN) |
| **2. Order Flow Imbalance** ⚡ | [`02_order_flow_imbalance/`](file:///d:/cbot-atgvt/zz_zz%20PAPER/02_order_flow_imbalance/) | คำนวณแรงซื้อขายสุทธิ (OFI) จับจังหวะ Absorption และวัด Price Impact | `1011.6402` (Cont & Stoikov)<br>`2112.02947` (Multi-level OFI) |
| **3. Market Making & Spread** ⚖️ | [`03_market_making_and_spread/`](file:///d:/cbot-atgvt/zz_zz%20PAPER/03_market_making_and_spread/) | วางคำสั่ง Bid/Ask แบบ Passive, ปรับสเปรดตาม Volatility และคุม Inventory | `1605.01862` (Guéant Master MM)<br>`1105.3115` (Inventory Risk) |
| **4. Optimal Execution & VWAP** 🎯 | [`04_optimal_execution_and_vwap/`](file:///d:/cbot-atgvt/zz_zz%20PAPER/04_optimal_execution_and_vwap/) | ซอยคำสั่ง (Slicing) ลด Slippage และยิงตามเส้น VWAP สถาบัน | `1409.2618` (Dynamic OFI Slicing)<br>`1306.2832` (Guaranteed VWAP) |
| **5. Hawkes Event Clustering** 🌊 | [`05_hawkes_and_event_clustering/`](file:///d:/cbot-atgvt/zz_zz%20PAPER/05_hawkes_and_event_clustering/) | ตรวจจับการกระชากของคำสั่งที่เป็นลูกโซ่ (Point Process) หลบข่าวหรือ Scalp ด่วน | `1301.1135` (Bacry Hawkes Model)<br>`1809.08060` (State-dependent LOB) |
| **6. Gold Microstructure & Alpha** 🥇 | [`06_gold_commodity_and_macro/`](file:///d:/cbot-atgvt/zz_zz%20PAPER/06_gold_commodity_and_macro/) | จุลภาคสภาพคล่องของทองคำ (XAUUSD), จังหวะ Forecast-to-Fill และ Regime Alpha | `2511.08571` (Forecast-to-Fill Alpha)<br>`2609.07946` (Stock/Bond/Gold) |
| **7. Market Regime Detection** 🎛️ | [`07_regime_detection_and_hmm/`](file:///d:/cbot-atgvt/zz_zz%20PAPER/07_regime_detection_and_hmm/) | ใช้ Hidden Markov Models (HMM) จำแนกสภาวะตลาดอัตโนมัติ เพื่อเป็นสวิตช์เปิด/ปิดบอท | `2605.27848` (HMM + RL Regime)<br>`2606.23492` (Continuous HMM) |
| **8. Lead-Lag & Latency** 🏎️ | [`08_lead_lag_and_latency/`](file:///d:/cbot-atgvt/zz_zz%20PAPER/08_lead_lag_and_latency/) | ตรวจจับความหน่วงระหว่างตลาด (เช่น Binance นำ cTrader, หรือ Bond Yield นำ Gold) เพื่อยิงดักหน้า | `1906.10388` (Lead-lag in FX)<br>`2608.24703` (Lead-lag Estimators) |
| **9. Signal Processing & Kalman** 🎯 | [`09_signal_processing_and_kalman/`](file:///d:/cbot-atgvt/zz_zz%20PAPER/09_signal_processing_and_kalman/) | กรอง Noise ตลาดแบบ Zero-Lag แทน Moving Average ดั้งเดิม ตัดปัญหาความหน่วงและสัญญาณหลอก | `1808.03297` (Trend without Hiccups)<br>`2609.14205` (CAST State-Space) |
| **10. Synthetic Data & Simulation** 🧪 | [`10_synthetic_data_and_simulation/`](file:///d:/cbot-atgvt/zz_zz%20PAPER/10_synthetic_data_and_simulation/) | ใช้ Diffusion Models / GANs สร้างข้อมูล LOB สังเคราะห์นับล้านฉากทัศน์สำหรับ Stress-test บอท | `2602.03776` (DiffLOB Diffusion)<br>`2510.22685` (TABL-ABM Synthetic) |
| **11. Financial LLMs & Sentiment** 🤖 | [`11_financial_llm_and_sentiment/`](file:///d:/cbot-atgvt/zz_zz%20PAPER/11_financial_llm_and_sentiment/) | สกัด Sentiment ข่าว Macro (FOMC, CPI, NFP) แปลงเป็นคะแนนทิศทางตลาดภายในเสี้ยววินาที | `2412.19245` (LLM Sentiment Trading)<br>`2607.28127` (FinSMART NLP) |
| **12. Position Sizing & Risk** 📐 | [`12_position_sizing_and_risk/`](file:///d:/cbot-atgvt/zz_zz%20PAPER/12_position_sizing_and_risk/) | บริหารขนาดไม้ด้วย Kelly Criterion และ Volatility Targeting ปรับลด Lot อัตโนมัติเมื่อผันผวนสูง | `2508.16598` (Kelly & VIX Hybrid)<br>`2609.13825` (ViperQ Auction Theory) |
| **13. Rough Volatility & Jumps** 🌊 | [`13_rough_volatility_and_jumps/`](file:///d:/cbot-atgvt/zz_zz%20PAPER/13_rough_volatility_and_jumps/) | แบบจำลองความขรุขระของราคา (Hurst < 0.5) สำหรับคำนวณระยะ SL/TP เชิงฟิสิกส์แท้จริง | `2609.31570` (Deep Rough Volatility)<br>`2606.27932` (Inefficient States) |

---

## 📊 การเข้าถึงสารบัญฉบับเต็ม

- 👉 **เปิดสารบัญงานวิจัยทั้ง 141 เรื่อง พร้อมลิงก์ HTML / PDF / สรุป:** [`PAPERS_INDEX.md`](file:///d:/cbot-atgvt/zz_zz%20PAPER/PAPERS_INDEX.md)
- 👉 **ไฟล์ฐานข้อมูล JSON:** [`papers_database.json`](file:///d:/cbot-atgvt/zz_zz%20PAPER/papers_database.json)

---

## 🚀 แผนการดำเนินการขั้นถัดไป (Next Steps)

เมื่อคลังความรู้เชิงทฤษฎีจาก **arXiv (`q-fin`)** สมบูรณ์ครบถ้วนทั้ง 13 มิติแล้ว แหล่งข้อมูลถัดไปคือ:
1. **SSRN (https://www.ssrn.com/ssrn/):** Working Papers ของกองทุนและสถาบัน (AQR, Two Sigma, Man AHL) เน้นเรื่อง Practitioner Backtesting, Real-world Execution และ Factor Alpha
2. **World Gold Council (https://www.gold.org/):** รายงานความต้องการทองคำจริงของธนาคารกลาง, โครงสร้างสภาพคล่อง OTC และ LBMA Fixing สำหรับ XAUUSD โดยตรง
