# ระเบียบและกฎเหล็กการบริหารจัดการระบบ (System Governance V5.0)
> **แหล่งกฎหลัก (Single Source of Truth):** [`GEMINI.md`](../GEMINI.md) · [`AGENTS.md`](../AGENTS.md)  
> **แผนที่ระบบ:** [`CURRENT_STATE_MAP.md`](../CURRENT_STATE_MAP.md) · [`FUTURE_STATE_MAP.md`](../FUTURE_STATE_MAP.md)  
> **วันที่มีผลบังคับใช้:** 16 พฤศจิกายน 2026 · **สถานะ:** บังคับใช้แบบ Repo-First (อ่านก่อนแก้ไขทุกครั้ง)

---

## สรุปโครงสร้างกฎ 5 หมวด (V5 Architecture)

### หมวดที่ 1: ความจริงแท้, ความปลอดภัย & สภาพแวดล้อม (Core Truth & Environment)
1. **100% Pure Live / Hybrid Real Data (Truth Reset):** ใช้ข้อมูลสด L2 DOM 25 ชั้น / Real Spread / Order Flow ร่วมกับข้อมูลจริงจาก cTrader เท่านั้น ห้ามแต่งหรือสมมติตัวเลขผลกำไรบนเว็บ
2. **Zero Lookahead & Zero Data Leakage:** ใช้แท่งที่ปิดแล้ว (`.Last(1)` / `Count - 2`) และแยกช่วง Train ออกจาก Out-of-Sample ชัดเจน
3. **Permanent Demo Quarantine (`#5258778`):** พัฒนาและเทรดบนบัญชี Pepperstone Demo เท่านั้น ไม่มีเงื่อนไขสวิตช์ไปบัญชีเงินจริงโดยเด็ดขาด
4. **Adaptive Risk, SL & Session Flat Time:** ไม่มีตัวเลขตายตัวสำหรับระยะ SL, RR, % ความเสี่ยงต่อไม้, เพดานขาดทุน/วัน, จำนวนออเดอร์ หรือเวลา Daily Flat (ให้ปรับตามกลยุทธ์, สถานการณ์, และตารางตลาดจริงของแต่ละสินทรัพย์ เช่น XAUUSD ปิดก่อนตลาดเบรกหนาว `21:59 UTC` / ร้อน `20:59 UTC` และช่วงสเปรดพุ่ง `21:00 UTC` — ไม่ปิดที่ `23:50 UTC`)
   * **Backtest Research:** เปิดอิสระให้ทดสอบแม้กระทั่งกลยุทธ์ที่ไม่มี SL หรือปล่อยจำลองพอร์ตแตกได้ แต่ต้องบันทึกสาเหตุอย่างละเอียดว่าพังเพราะสถานการณ์ใด และวิธีแก้ไข
   * **Demo Execution:** ควรมีกลไกหยุดขาดทุน/กันพอร์ตแตกในโค้ดเพื่อให้ Demo เก็บสถิติได้ต่อเนื่อง
5. **Data Sanitization ใน Demo (ไม่สั่งหยุดเก็บ/หยุดเทรด):** ในโหมด Demo หากเจอข้อมูลเสีย/`NaN` ให้ตัดเฉพาะจุดที่เสียออกแล้วเอาข้อมูลที่สมบูรณ์มารันต่อ (ส่วนกฎหยุดเปิดไม้ใหม่เมื่อ Recorder ค้าง เก็บไว้เป็น Reference เฉพาะกรณีบัญชีจริงในอนาคต)

### หมวดที่ 2: การเก็บข้อมูล 24/7, cTrader Audit & Watchdog (Smart Collection)
1. **เช็ก cTrader API/MCP ก่อนเก็บเสมอ:** ดึงแท่ง OHLCV (`get_trendbars`) และ Sessions (`get_symbol_sessions`) จาก cTrader; ส่วนที่ cTrader ไม่มีประวัติย้อนหลัง (`L2 DOM 25 ชั้น`, `Bid/Ask Real Spreads`, `Order Flow Delta/CVD`, `Execution Slippage/Latency`, `Multi-month Ticks`) ต้องบันทึกสด 24/7 เอง แล้ว **Merge เข้าด้วยกัน** ตอนรันวิจัย
2. **24/7 Watchdog Supervisor:** ตรวจความสดของไฟล์ทุก 15 วินาที; ค้างเกิน **120 วินาที** บันทึกเวลาหยุดและรีสตาร์ตต่อทันที (XAUUSD เข้า `WEEKEND_STANDBY` ช่วงตลาดปิดสุดสัปดาห์)

### หมวดที่ 3: วิวัฒนาการตามสถานการณ์ & เว็บ 4 ขั้นตอน
1. **Regime-Matched Memory (ไม่คัดทิ้ง 98% / ไม่แบนถาวร):** เก็บทุกกลยุทธ์พร้อมระบุว่า *"เหมาะกับสถานการณ์ใด / แพ้ในสถานการณ์ใด"* เพื่อใช้ Regime Detection สลับกลยุทธ์และพารามิเตอร์ให้ถูกสถานการณ์
2. **Anti-Overfitting:** ต้องผ่านการทดสอบความทนทานบน Out-of-Sample (Unseen Data) ในสถานการณ์นั้น ไม่เลือกจากกำไรสูงสุดใน Train อย่างเดียว
3. **รายงานผลจริงตรงไปตรงมา (ยกเลิกเกณฑ์รอ `N >= 500`):** รายงานความแม่นยำตามจำนวนครั้งที่เกิดสถานการณ์จริง (เช่น *"เจอสถานการณ์ A 3 ครั้ง ชนะ 2/3 ครั้ง กำไรรวม +$X"*)
4. **4 ขั้นตอนหลักบนเว็บ 8 หน้า:** `1. Data & Market Sync` ➔ `2. Research & Matching` ➔ `3. Test & Anti-Overfit` ➔ `4. Learn, Audit & Evolve`

### หมวดที่ 4: ตระกูลกลยุทธ์ & การพัฒนาแยกตาม Session
1. **ยกเลิกการจำกัดแค่ 4 เสาหลัก:** ใช้ 4 ตระกูลเริ่มต้นเป็น Seed และขยายกลยุทธ์ตระกูลใหม่ได้ไม่จำกัด
2. **แยกโซนพัฒนาตาม Session & รอยต่อข้าม Session:** แยกวิจัยและค้นหาสถานการณ์เป็นราย `ASIA`, `LONDON`, `NY`, `OVERNIGHT` และช่วงรอยต่อ (`Asia→London`, `London→NY`, `NY→Close`)

### หมวดที่ 5: เว็บ, โค้ด cBot, Multi-Agent Pipeline & Git Workflow
1. **Repo-First Context & Pre-Edit Check:** AI ต้องอ่าน `GEMINI.md`, `CURRENT_STATE_MAP.md`, `FUTURE_STATE_MAP.md` ก่อนแก้ไขทุกครั้ง — หากขัดกฎหลัก 5 หมวด ต้องขอให้ **Human Decide** เพื่ออัปเดตกฎก่อนแก้โค้ด
2. **Demo Logic Update vs Core Rule Authority:** AI แก้/Deploy ตรรกะบน Demo ได้เลยโดยต้องขยับ `Version` + บันทึก Change Log + รันเทียบของเดิม และ **Rollback ได้เองทันที** หากของเดิมดีกว่า; แต่ห้ามแก้กฎหลัก 5 หมวดเองโดยไม่ได้รับอนุญาต
3. **Web Freshness & 8-Page Portal (`piyavutkkl-ch`):** ซิงก์ผลวิจัยและสถิติจริงขึ้น GitHub Pages เสมอ (ยกเลิก Supabase Auth/Edge/Drive, ไม่บังคับ White Theme/TradingView `tv.js`)
4. **Multi-Agent + Human-in-the-Loop:** พัฒนาสู่สายพาน 4 Agents ส่งต่อข้อมูลกัน พร้อมจุด Human Decision Gate สำหรับงานใหญ่หรือการเปลี่ยนกฎ
5. **มาตรฐาน cBot & Git:** ใช้ `CultureInfo.InvariantCulture` ใน C# เสมอ, AI commit/push ขึ้น `piyavutkkl-ch` ได้อัตโนมัติ, ห้ามเก็บ Secret ลง Git เด็ดขาด
