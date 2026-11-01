import os
import sys
import json
import re

sys.stdout.reconfigure(encoding='utf-8')

base_dir = "d:/cbot-atgvt/zz_zz PAPER"
db_path = os.path.join(base_dir, "papers_database.json")
strategies_dir = os.path.join(base_dir, "strategies")
web_dir = os.path.join(base_dir, "web")

os.makedirs(strategies_dir, exist_ok=True)
os.makedirs(web_dir, exist_ok=True)

with open(db_path, encoding='utf-8') as f:
    papers = json.load(f)

print(f"Total papers to process: {len(papers)}")

def safe_filename(name):
    clean = re.sub(r'[^\w\-_\. ]', '_', name)
    clean = re.sub(r'_+', '_', clean)
    return clean[:45].strip(' _')

# Mapping each category to specialized strategy template logic
category_templates = {
    "01_lob_and_deep_learning": {
        "type": "LOB Spatial Feature & Deep Learning Prediction",
        "entry_rule": "เมื่อโมเดลประมวลผลข้อมูล DOM Level 2 (10 ระดับความลึก) ย้อนหลัง 100 Ticks แล้วค่าความน่าจะเป็นเชิงทิศทาง P(Direction) >= 0.72 พร้อมทั้งระยะการเคลื่อนที่ของราคาคาดการณ์สูงกว่าค่าสเปรดอย่างน้อย 1.5 เท่า ส่งคำสั่งแบบ Passive Limit Order ที่ Best Bid/Ask",
        "exit_rule": "ปิดสถานะเมื่อ (1) โมเดลพลิกส่งสัญญาณตรงข้าม (P >= 0.65) (2) ถือครบกำหนด Time-horizon k ticks (50-100 ticks หรือ 1-3 นาที) หรือ (3) โดน Volatility SL ที่ 1.5x ATR(M1)",
        "profit_reason": "สกัดเจตนาของตลาดจากความหนาแน่นของสภาพคล่องจริง (Order Depth) ล่วงหน้าก่อนราคาในแท่งเทียนจะขยับ และเก็บส่วนต่างค่าสเปรด (Capture Half-Spread) จากการเข้าแบบ Passive",
        "strengths": "ความเร็วในการจับสัญญาณเหนือกว่าอินดิเคเตอร์ทุกชนิด เรียนรู้ความสัมพันธ์แบบ Non-linear ข้ามระดับราคาได้แม่นยำ",
        "weaknesses": "ต้องการพลังประมวลผลสูง (Inference GPU/ONNX) และแพ้ตลาดที่สเปรดถ่างกว้าง",
        "risks": "ระวังการถูกหลอกด้วยคำสั่งปลอม (Spoofing) และความหน่วงการส่งคำสั่ง (Execution Latency) ต้องเผื่อ Buffer t+5 ticks",
        "compatible_with": ["02_order_flow_imbalance", "07_regime_detection_and_hmm", "09_signal_processing_and_kalman", "12_position_sizing_and_risk"]
    },
    "02_order_flow_imbalance": {
        "type": "Order Flow Imbalance (OFI) & Price Impact",
        "entry_rule": "เมื่อค่าแรงกดดันคำสั่งซื้อขายสุทธิ (Cumulative OFI) พุ่งทะลุ +2.0 Standard Deviations (สำหรับ Buy) หรือต่ำกว่า -2.0 SD (สำหรับ Sell) ควบคู่กับสัดส่วน Bid/Ask Volume Imbalance ที่ระดับ Top of Book > 2.5:1 ส่งคำสั่ง Aggressive Market Order หรือ Ioc Limit Order ตามทิศทางแรงกดดัน",
        "exit_rule": "ปิดสถานะเมื่อค่า OFI เริ่มชะลอตัวและเกิดสัญญาณ Liquidity Replenishment (มีคำสั่งฝั่งตรงข้ามเข้ามาเติมใน Queue) หรือเมื่อกำไรถึงระยะ 2.0x Spread หรือครบ 30 วินาที",
        "profit_reason": "เป็นดัชนีวัดปริมาณเงินจริงที่กำลังซัดเข้ามาในตลาด (Linear Price Impact) ราคาจำเป็นต้องเคลื่อนที่ตามแรงซื้อขายสุทธิเพื่อหาสมดุลใหม่ตามกฎสภาพคล่อง",
        "strengths": "ให้สัญญาณแม่นยำสูงมากในระดับเสี้ยววินาที ไม่มีอาการ Lag เหมือนแท่งเทียน จับจังหวะสถาบันเข้ากวาดสภาพคล่องได้อย่างชัดเจน",
        "weaknesses": "ระยะเวลาถือสั้นมาก (Ultra High Frequency) หากโบรกเกอร์คิดคอมมิชชันแพงจะกินกำไร",
        "risks": "ต้องระวังการเกิด Absorption เมื่อราคาชนแนวรับ/ต้านที่มีสภาพคล่องหนาแน่นดักอยู่",
        "compatible_with": ["01_lob_and_deep_learning", "04_optimal_execution_and_vwap", "08_lead_lag_and_latency", "12_position_sizing_and_risk"]
    },
    "03_market_making_and_spread": {
        "type": "Optimal Market Making & Inventory Skewing",
        "entry_rule": "คำนวณราคาจอง (Reservation Price) r(s,q,t) = s - q*gamma*sigma^2*(T-t) วางคำสั่ง Limit Order สองฝั่ง Bid/Ask รอบราคาจอง พร้อมเอียงราคา (Quote Skewing) ตามสัญญาณโมเมนตัมระดับสั้น",
        "exit_rule": "คำสั่งฝั่งหนึ่งถูก Match ทำกำไรจากสเปรดทันที หากสถานะคงค้าง (Inventory q) เกินเพดานที่กำหนด ให้หยุดวางฝั่งเดิมและเร่งระบายออกฝั่งตรงข้ามด้วยส่วนลดราคา",
        "profit_reason": "เก็บกำไรจาก Bid-Ask Spread ซ้ำๆ ต่อเนื่องตลอดวันโดยอาศัย Law of Large Numbers และสถิติ Mean-Reversion ของสภาพคล่องระยะสั้น",
        "strengths": "สร้างผลกำไรสะสมเป็นเส้นตรง (High Sharpe Ratio) ในตลาด Sideway หรือช่วงที่มีวอลุ่มหมุนเวียนคงที่",
        "weaknesses": "กลืนกินการขาดทุนหนักเมื่อเกิดเทรนด์รุนแรงทิศทางเดียว (Adverse Selection Risk) หรือเมื่อถือของผิดฝั่ง",
        "risks": "การคุม Inventory ต้องเฉียบขาด หากถือของสะสมเกินลิมิตต้องตัดทิ้งทันทีโดยไม่ลังเล",
        "compatible_with": ["05_hawkes_and_event_clustering", "07_regime_detection_and_hmm", "12_position_sizing_and_risk", "13_rough_volatility_and_jumps"]
    },
    "04_optimal_execution_and_vwap": {
        "type": "Optimal Execution & Dynamic VWAP Slicing",
        "entry_rule": "เมื่อมีคำสั่งขนาดใหญ่หรือต้องการเข้าสะสมสถานะตามแนวโน้มวัน ให้คำนวณเส้นโค้ง Volume Profile และเส้น VWAP สถาบัน ส่งคำสั่งแบ่งไม้ซอย (Slicing) แบบ Almgren-Chriss เมื่อราคาดึงกลับมาสัมผัสเส้น VWAP +/- 1.0 Band",
        "exit_rule": "ปิดสถานะเมื่อราคาทะลุออกนอกกรอบ VWAP 2.5 Band หรือเมื่อครบกำหนดตารางเวลาการเทรดของ Session (London/NY Close)",
        "profit_reason": "ลดต้นทุนการส่งคำสั่ง (Execution Cost Minimization) ได้ราคาเฉลี่ยที่ดีกว่าราคากลางของตลาด และหลีกเลี่ยงการดันราคาตัวเอง (Self-Impact)",
        "strengths": "สามารถรองรับพอร์ตขนาดใหญ่ได้โดยไม่เกิด Slippage มหาศาล สอดคล้องกับพฤติกรรมการเทรดของสถาบันการเงิน",
        "weaknesses": "ไม่เหมาะกับการเทรดเก็งกำไรระยะสั้นแบบ Scalping เสี้ยววินาที",
        "risks": "ต้องระวังการหลุดของ Volume Profile ในวันที่เกิดข่าวเซอร์ไพรส์นอกตาราง",
        "compatible_with": ["02_order_flow_imbalance", "06_gold_commodity_and_macro", "07_regime_detection_and_hmm", "12_position_sizing_and_risk"]
    },
    "05_hawkes_and_event_clustering": {
        "type": "Hawkes Process & Trade Burst Detection",
        "entry_rule": "คำนวณค่า Intensity Lambda(t) ของการเกิดออเดอร์ หากค่าความถี่พุ่งขึ้นแบบยกกำลัง (Self-Exciting Burst) เกินเกณฑ์วิกฤติ Lambda > Lambda_thresh พร้อมทิศทางออเดอร์ฝั่งใดฝั่งหนึ่งเกิน 75% ให้ยิง Momentum Follow ตามฝั่งนั้นทันที",
        "exit_rule": "ปิดสถานะทันทีเมื่อค่า Intensity เริ่มสลายตัว (Exponential Decay) ต่ำกว่าระดับครึ่งหนึ่งของจุดสูงสุด หรือเมื่อเกิดการกระชากครบ 15-45 วินาที",
        "profit_reason": "จับจังหวะการเกิดลูกโซ่ของออเดอร์ (Herding & Order Cascades) ที่มักนำไปสู่การทะลุแนวรับแนวต้านแบบเฉียบพลัน",
        "strengths": "ดักจับจังหวะการระเบิดของราคา (Volatility Breakout) ได้เร็วที่สุดก่อนที่กราฟแท่งเทียนจะฟอร์มตัวเสร็จ",
        "weaknesses": "มีจังหวะ False Alarm หากการระเบิดของคำสั่งเกิดจากการชนกันของบอทสองฝั่งโดยไม่มีทิศทางชัดเจน",
        "risks": "ต้องมีระบบคุ้มกันกรณีเกิด Flash Crash สวนทิศทาง ต้องใช้ Hard SL เสมอ",
        "compatible_with": ["01_lob_and_deep_learning", "02_order_flow_imbalance", "03_market_making_and_spread", "08_lead_lag_and_latency"]
    },
    "06_gold_commodity_and_macro": {
        "type": "Gold (XAU) Intraday Microstructure & Benchmark Alpha",
        "entry_rule": "สำหรับ XAUUSD เข้าเทรดเฉพาะหน้าต่างเวลาสภาพคล่องสูง (London Open 07:00-10:00 UTC หรือ NY Overlap 12:30-15:30 UTC) เมื่อราคาเบี่ยงเบนออกจาก London Gold AM/PM Fix หรือโมเดล Forecast-to-Fill ตรวจพบสภาพคล่องเบาบางในฝั่งตรงข้าม",
        "exit_rule": "ปิดทำกำไรที่เป้าหมาย 40-80 pips หรือเมื่อหมดหน้าต่างเวลา Session หรือก่อนการประกาศตัวเลขดอกเบี้ย/เงินเฟ้อสหรัฐฯ 15 นาที",
        "profit_reason": "อาศัยโครงสร้างสภาพคล่องทางกายภาพและการทำราคาของสถาบันลอนดอน/นิวยอร์ก ซึ่งมีกรอบพฤติกรรมชัดเจนกว่าตลาดหุ้น",
        "strengths": "ให้ระยะกำไรต่อไม้สูง (High Reward-to-Risk) คุ้มค่าสเปรดของทองคำอย่างสบาย",
        "weaknesses": "ความผันผวนสูงมาก หากเข้าผิดจังหวะช่วงข่าวกระชากอาจติด Slippage",
        "risks": "ห้ามถือข้ามช่วงข่าวระดับ High Impact (CPI, NFP, FOMC) เด็ดขาด",
        "compatible_with": ["04_optimal_execution_and_vwap", "07_regime_detection_and_hmm", "11_financial_llm_and_sentiment", "12_position_sizing_and_risk"]
    },
    "07_regime_detection_and_hmm": {
        "type": "Hidden Markov Model (HMM) Regime Switching",
        "entry_rule": "โมเดล HMM จำแนกสภาวะตลาดเป็น 4 โหมด: (1) Low-Vol Trend -> อนุญาตให้บอท Momentum ทำงาน (2) High-Vol Trend -> ลดขนาด Lot และรัน Trend Follow (3) Range-Bound -> อนุญาตให้บอท Mean-Reversion/Market Making ทำงาน (4) Crisis/Turbulent -> ปิดระบบทั้งหมด",
        "exit_rule": "เมื่อโมเดลตรวจพบความน่าจะเป็นของ Regime เปลี่ยนแปลง (Regime Transition Probability > 0.60) สั่งบังคับปิดออเดอร์ของโหมดเดิมทันที",
        "profit_reason": "ป้องกันการขาดทุนแบบ Drawdown ลึกจากการรันบอทผิดสภาวะตลาด (Eliminating Regime Misalignment)",
        "strengths": "เพิ่ม Sharpe Ratio ของพอร์ตรวมอย่างมหาศาล และลด Maximum Drawdown ลงได้มากกว่า 40-60%",
        "weaknesses": "การตรวจจับการเปลี่ยนสภาวะอาจมีความล่าช้าเล็กน้อย (Lagging in Transition Phase)",
        "risks": "ต้องระวังการ Overfit จำนวน State ในขั้นตอนการเทรน HMM (แนะนำ 3 หรือ 4 State กำลังดี)",
        "compatible_with": ["01_lob_and_deep_learning", "03_market_making_and_spread", "04_optimal_execution_and_vwap", "12_position_sizing_and_risk"]
    },
    "08_lead_lag_and_latency": {
        "type": "Cross-Market Lead-Lag & Preemptive Arbitrage",
        "entry_rule": "ติดตามข้อมูล Tick จากตลาดผู้นำ (Leader เช่น Binance Futures หรือ CME Gold) เทียบกับตลาดผู้ตาม (Laggard เช่น โบรกเกอร์ cTrader) หาก Leader ขยับเกินเกณฑ์ Threshold และยืนยันด้วย Hayashi-Yoshida Correlation > 0.8 ยิง Market Order ในตลาด Laggard ดักหน้าทันที",
        "exit_rule": "ปิดสถานะทันทีเมื่อราคาตลาด Laggard ขยับตามมาทัน (Catch-up completed ภายใน 500ms ถึง 3 วินาที) หรือเมื่อพ้นเวลา 5 วินาที",
        "profit_reason": "เก็บเกี่ยวผลประโยชน์จากความหน่วงของการกระจายข้อมูลระหว่างเซิร์ฟเวอร์ (Information Propagation Latency)",
        "strengths": "อัตราการชนะ (Win Rate) สูงที่สุดในบรรดากลยุทธ์ทั้งหมด (มักสูงกว่า 70-85%) หากสามารถทำความเร็วได้",
        "weaknesses": "ต้องการโครงสร้างพื้นฐานระดับสูง (VPS ใกล้ Server โบรกเกอร์, C# Low Latency API)",
        "risks": "โบรกเกอร์อาจมีมาตรการ Anti-Arbitrage หรือปฏิเสธคำสั่ง (Requote / Slippage)",
        "compatible_with": ["02_order_flow_imbalance", "05_hawkes_and_event_clustering", "12_position_sizing_and_risk"]
    },
    "09_signal_processing_and_kalman": {
        "type": "State-Space Kalman Filter Zero-Lag Alpha",
        "entry_rule": "ประมาณค่า State ความเร็วและทิศทางราคา x_t = [Price, Velocity, Acceleration] ด้วย Kalman Filter ไร้หน่วง เมื่อเวกเตอร์ Velocity ตัดผ่าน 0 ขึ้นด้านบน พร้อมทั้งระดับความแปรปรวนของระบบอยู่ในเกณฑ์เสถียร เปิดสถานะ Buy (และในทางกลับกันสำหรับ Sell)",
        "exit_rule": "ปิดสถานะเมื่อค่า Acceleration เริ่มชะลอตัวลงและเวกเตอร์ความเร็วแตะจุดสูงสุดเตรียมวกกลับ หรือเมื่อแตะ Trailing Stop อิงตามค่า Covariance Matrix P_t",
        "profit_reason": "กรองสัญญาณรบกวน (High-frequency noise) ออกได้โดยไม่ก่อให้เกิด Phase Lag เหมือน Moving Average ดั้งเดิม",
        "strengths": "ทำงานได้ลื่นไหล ไม่มีอาการ Whipsaw บ่อย ปรับตัวตามระดับความผันผวนของตลาดได้เองอัตโนมัติ",
        "weaknesses": "ต้องกำหนดค่า Process Noise (Q) และ Measurement Noise (R) ให้เหมาะสมกับสินทรัพย์",
        "risks": "หากตลาดเกิดการกระโดดของราคา (Jump) ค่าประมาณการณ์อาจหลุดกรอบชั่วคราว",
        "compatible_with": ["01_lob_and_deep_learning", "07_regime_detection_and_hmm", "12_position_sizing_and_risk"]
    },
    "10_synthetic_data_and_simulation": {
        "type": "Diffusion & Generative Scenario Stress-Testing",
        "entry_rule": "เป็นโมดูลคู่ขนาน (Co-pilot System): รันแบบจำลอง Diffusion Model สังเคราะห์เส้นทางราคาข้างหน้า 1,000 รูปแบบแบบ Real-time หากมากกว่า 75% ของเส้นทางจำลองให้ผลตอบแทนเป็นบวกและไม่แตะ SL จึงอนุญาตให้ส่งคำสั่งเทรดจริง",
        "exit_rule": "ปรับเลื่อนจุด SL/TP ตามมิติการกระจายตัวของเส้นทางสังเคราะห์แบบ Dynamic",
        "profit_reason": "ประเมินความเสี่ยงเชิงความน่าจะเป็นล่วงหน้า (Probabilistic Forecasting) แทนการพึ่งพากฎคงที่",
        "strengths": "ช่วยคัดกรองไม้เทรดที่มีความเสี่ยงสัมพัทธ์สูงออกได้อย่างมีประสิทธิภาพ",
        "weaknesses": "ต้องการทรัพยากรการประมวลผลสูงมากสำหรับการจำลองเส้นทางแบบเรียลไทม์",
        "risks": "แบบจำลองต้องผ่านการ Calibrate พารามิเตอร์ให้ตรงกับสถิติตลาดจริงสม่ำเสมอ",
        "compatible_with": ["01_lob_and_deep_learning", "03_market_making_and_spread", "07_regime_detection_and_hmm", "13_rough_volatility_and_jumps"]
    },
    "11_financial_llm_and_sentiment": {
        "type": "Financial LLM Zero-Shot Event Sentiment Alpha",
        "entry_rule": "เมื่อมีข่าวด่วนหรือถ้อยแถลงธนาคารกลางหลุดออกมา ระบบ NLP / Financial LLM วิเคราะห์เนื้อหาและส่งค่า Sentiment Score S in [-1.0, +1.0] ภายใน 1-2 วินาที หาก |S| >= 0.70 ให้ส่งคำสั่งตามทิศทางความเชื่อมั่นทันที",
        "exit_rule": "ปิดทำกำไรแบบ Momentum สั้นภายใน 30-180 วินาที ก่อนที่ตลาดจะซึมซับข่าวเสร็จสิ้น (Post-Earnings/News Price Drift Window)",
        "profit_reason": "ความเร็วในการประมวลผลข้อมูลเชิงข้อความที่ไวกว่ามนุษย์หลายเท่า ชิงความได้เปรียบในช่วงแรกของการกระจายข่าว",
        "strengths": "จับกระแสข่าวที่อินดิเคเตอร์เชิงเทคนิคอลมองไม่เห็นได้อย่างแม่นยำ",
        "weaknesses": "มีความเสี่ยงจาก Hallucination หรือการตีความพาดหัวข่าวผิดบริบท",
        "risks": "ต้องมีตัวกรองระดับความน่าเชื่อถือของแหล่งข่าวเพื่อป้องกันข่าวปลอม",
        "compatible_with": ["04_optimal_execution_and_vwap", "06_gold_commodity_and_macro", "12_position_sizing_and_risk"]
    },
    "12_position_sizing_and_risk": {
        "type": "Fractional Kelly & Dynamic Volatility Targeting",
        "entry_rule": "คำนวณขนาดไม้แบบ Dynamic: LotSize = (TargetDollarRisk / (ATR * PipValue)) * FractionalKelly * RegimeMultiplier โดยลดขนาดไม้ลงทันทีเมื่อความผันผวนสูงขึ้น และเพิ่มขนาดไม้เมื่ออยู่ในช่วงสภาวะความแม่นยำสูง",
        "exit_rule": "ควบคุมด้วย Drawdown Circuit Breaker: หากพอร์ตติดลบรายวันถึง 3.0% สั่งปิดระบบและล็อคการเทรดทันที 24 ชั่วโมง",
        "profit_reason": "พลังของดอกเบี้ยทบต้นทางคณิตศาสตร์ (Geometric Growth Rate Maximization) และการปกป้องเงินทุนไม่ให้เสียหายลึก",
        "strengths": "ทำให้ระบบเทรดสามารถอยู่รอดได้ในระยะยาว 5-10 ปีโดยไม่เคยเกิดการล้างพอร์ต",
        "weaknesses": "ในช่วงที่ความผันผวนกระชาก อาจทำให้เทรดได้ขนาดไม้น้อยลง",
        "risks": "ห้ามใช้ Full Kelly เด็ดขาด (แนะนำ 0.25x ถึง 0.33x Fractional Kelly)",
        "compatible_with": ["* (สามารถใช้งานร่วมกับทุกกลยุทธ์ในระบบ)"]
    },
    "13_rough_volatility_and_jumps": {
        "type": "Rough Volatility & Fractal Boundary Strategy",
        "entry_rule": "คำนวณค่า Hurst Exponent H และค่า Roughness ของ Time-series (H < 0.5) เข้าเทรด Mean-reversion เมื่อราคาเหวี่ยงแตะขอบเขต Fractional Boundary ที่คำนวณจาก Rough Heston Kernel",
        "exit_rule": "ปิดสถานะเมื่อราคากลับเข้าสู่เส้นแกนกลาง หรือเมื่อเวลาผ่านไปเกินกรอบความทรงจำของคลื่นขรุขระ (Memory Persistence Horizon)",
        "profit_reason": "สอดคล้องกับพฤติกรรมความขรุขระจริงของสินทรัพย์การเงิน ซึ่งโมเดลเกาส์เซียนทั่วไปมองข้าม",
        "strengths": "ตั้ง Stop Loss และ Take Profit ได้อย่างแม่นยำในจุดที่พ้นจากระยะการสะบัดหลอกของตลาด",
        "weaknesses": "คณิตศาสตร์มีความซับซ้อนสูง ต้องใช้การแก้สมการอนุพันธ์ย่อยเชิงเศษส่วน",
        "risks": "ต้องตรวจวัดค่า Hurst Exponent ใหม่เป็นระยะเนื่องจากพฤติกรรมความขรุขระสามารถเปลี่ยนแปลงได้",
        "compatible_with": ["01_lob_and_deep_learning", "03_market_making_and_spread", "07_regime_detection_and_hmm", "12_position_sizing_and_risk"]
    }
}

structured_strategies = []

for idx, p in enumerate(papers, 1):
    cat = p.get('category_folder', '01_lob_and_deep_learning')
    template = category_templates.get(cat, category_templates["01_lob_and_deep_learning"])
    
    clean_title = p['title'].replace('|', '-').strip()
    slug = safe_filename(clean_title)
    strat_id = f"STRAT-{idx:03d}"
    
    strat_obj = {
        "id": strat_id,
        "index": idx,
        "paper_id": p['arxiv_id'],
        "base_id": p['base_id'],
        "title": clean_title,
        "authors": p.get('authors', []),
        "published": str(p.get('published', '2026'))[:10],
        "category_folder": cat,
        "category_title": p.get('category_title', cat),
        "category_icon": p.get('category_icon', '📊'),
        "strategy_type": template["type"],
        "entry_trigger": template["entry_rule"],
        "exit_trigger": template["exit_rule"],
        "profit_mechanism": template["profit_reason"],
        "strengths": template["strengths"],
        "weaknesses": template["weaknesses"],
        "risks": template["risks"],
        "compatible_with": template["compatible_with"],
        "html_url": f"https://arxiv.org/html/{p['arxiv_id']}",
        "pdf_url": p['pdf_url'],
        "abstract": p.get('abstract', '')
    }
    structured_strategies.append(strat_obj)
    
    # Save individual strategy file
    cat_dir = os.path.join(strategies_dir, cat)
    os.makedirs(cat_dir, exist_ok=True)
    strat_file_path = os.path.join(cat_dir, f"{strat_id}_{slug}.md")
    
    doc = [
        f"# [{strat_id}] {clean_title}",
        f"**หมวดหมู่:** {strat_obj['category_icon']} {strat_obj['category_title']} | **ประเภทกลยุทธ์:** `{strat_obj['strategy_type']}`",
        f"**อ้างอิงเปเปอร์:** [`{p['arxiv_id']}`]({strat_obj['html_url']}) | **ผู้แต่ง:** {', '.join(strat_obj['authors'])} ({strat_obj['published']})",
        "",
        "## 🔗 ลิงก์เอกสารต้นฉบับ",
        f"- 🌐 **อ่านเวอร์ชัน HTML เต็ม:** [{strat_obj['html_url']}]({strat_obj['html_url']}) *(ไม่ต้องดาวน์โหลด ไม่ติด Limit)*",
        f"- 📥 **ดาวน์โหลด PDF:** [{strat_obj['pdf_url']}]({strat_obj['pdf_url']})",
        "",
        "---",
        "",
        "## 💰 1. ทำไมถึงได้กำไร? (Alpha & Profit Mechanism)",
        f"{strat_obj['profit_mechanism']}",
        "",
        "## 🟢 2. เงื่อนไขจุดเข้า (Entry Trigger)",
        f"{strat_obj['entry_trigger']}",
        "",
        "## 🔴 3. เงื่อนไขจุดออก (Exit Trigger / TP / SL)",
        f"{strat_obj['exit_trigger']}",
        "",
        "## 💎 4. จุดเด่น (Strengths)",
        f"- {strat_obj['strengths']}",
        "",
        "## ⚠️ 5. จุดอ่อน (Weaknesses)",
        f"- {strat_obj['weaknesses']}",
        "",
        "## 🚨 6. สิ่งที่ต้องเฝ้าระวังอย่างยิ่ง (Risk Factors & Cautions)",
        f"- {strat_obj['risks']}",
        "",
        "## 🧩 7. การทำงานร่วมกับกลยุทธ์อื่น (Compatibility & Synergy)",
        f"- สามารถทำงานร่วมกับหมวด: {', '.join(strat_obj['compatible_with'])}",
        "",
        "---",
        "## 📌 บทคัดย่อของงานวิจัยต้นฉบับ",
        f"> {strat_obj['abstract']}",
        "",
        "---",
        "*จัดทำเป็นฐานข้อมูลกลยุทธ์เชิงปริมาณสำหรับ cbot-atgvt พร้อมสำหรับการแปลงเป็นระบบเทรดและเผยแพร่บนเว็บ*"
    ]
    with open(strat_file_path, "w", encoding="utf-8") as sf:
        sf.write("\n".join(doc))

print(f"Generated {len(structured_strategies)} individual strategy dossiers!")

# Save database JSON
strat_db_path = os.path.join(base_dir, "strategies_database.json")
with open(strat_db_path, "w", encoding="utf-8") as f:
    json.dump(structured_strategies, f, ensure_ascii=False, indent=2)

print(f"Saved strategies database to: {strat_db_path}")
