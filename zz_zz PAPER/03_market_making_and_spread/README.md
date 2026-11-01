# ⚖️ หมวดที่ 3: กลยุทธ์ Market Making, Bid/Ask Spreads และการคุม Inventory Risk
### Market Making Algorithms, Spread Dynamics & Inventory Control

**ภาพรวมเนื้อหา:** แบบจำลองคณิตศาสตร์สำหรับการวางคำสั่ง Bid/Ask แบบ Passive (Avellaneda-Stoikov & Guéant models), การคำนวณ Reservation Price และการคุมความเสี่ยงเมื่อพอร์ตถือสถานะไม่สมดุล

**ความสำคัญต่อการพัฒนา Bot Trade:** ใช้กำหนดระยะกางของสเปรดและจุดตั้ง Limit Order / Take Profit ตามความผันผวน และใช้เอียงราคาเสนอซื้อขาย (Quote Skewing) ตามทิศทางโมเมนตัม

---

## 📚 รายการงานวิจัยในหมวดนี้ (Curated Research Papers)

| ลำดับ | รหัส arXiv | ชื่องานวิจัย | ผู้แต่ง | ปี | ลิงก์อ่าน |
| :---: | :---: | :--- | :--- | :---: | :---: |
| 1 | [`1605.01862`](1605.01862_Optimal market making.md) | Optimal market making | Olivier Guéant | 2016 | [HTML](https://arxiv.org/html/1605.01862v5) / [PDF](https://arxiv.org/pdf/1605.01862v5.pdf) |
| 2 | [`2607.17991`](2607.17991_Optimal Market Making in Prediction Markets.md) | Optimal Market Making in Prediction Markets | Dominik Feil, Max Nendel | 2026 | [HTML](https://arxiv.org/html/2607.17991v1) / [PDF](https://arxiv.org/pdf/2607.17991v1.pdf) |
| 3 | [`1502.02863`](1502.02863_Dark-Pool Perspective of Optimal Market Makin.md) | Dark-Pool Perspective of Optimal Market Making | M. Alessandra Crisafi, Andrea Macrina | 2015 | [HTML](https://arxiv.org/html/1502.02863v1) / [PDF](https://arxiv.org/pdf/1502.02863v1.pdf) |
| 4 | [`1105.3115`](1105.3115_Dealing with the Inventory Risk. A solution t.md) | Dealing with the Inventory Risk. A solution to the market making problem | Olivier Guéant, Charles-Albert Lehalle et al. | 2011 | [HTML](https://arxiv.org/html/1105.3115v5) / [PDF](https://arxiv.org/pdf/1105.3115v5.pdf) |
| 5 | [`2306.17179`](2306.17179_Integrating Tick-level Data and Periodical Si.md) | Integrating Tick-level Data and Periodical Signal for High-frequency Market Making | Jiafa He, Cong Zheng et al. | 2023 | [HTML](https://arxiv.org/html/2306.17179v1) / [PDF](https://arxiv.org/pdf/2306.17179v1.pdf) |
| 6 | [`2109.15110`](2109.15110_Deep Hawkes Process for High-Frequency Market.md) | Deep Hawkes Process for High-Frequency Market Making | Pankaj Kumar | 2021 | [HTML](https://arxiv.org/html/2109.15110v1) / [PDF](https://arxiv.org/pdf/2109.15110v1.pdf) |
| 7 | [`2407.21025`](2407.21025_Reinforcement Learning in High-frequency Mark.md) | Reinforcement Learning in High-frequency Market Making | Yuheng Zheng, Zihan Ding | 2024 | [HTML](https://arxiv.org/html/2407.21025v2) / [PDF](https://arxiv.org/pdf/2407.21025v2.pdf) |
| 8 | [`2307.14129`](2307.14129_Macroscopic Market Making.md) | Macroscopic Market Making | Ivan Guo, Shijia Jin et al. | 2023 | [HTML](https://arxiv.org/html/2307.14129v3) / [PDF](https://arxiv.org/pdf/2307.14129v3.pdf) |
| 9 | [`1810.04383`](1810.04383_Closed-form approximations in multi-asset mar.md) | Closed-form approximations in multi-asset market making | Philippe Bergault, David Evangelista et al. | 2018 | [HTML](https://arxiv.org/html/1810.04383v5) / [PDF](https://arxiv.org/pdf/1810.04383v5.pdf) |

---
*สารบัญนี้จัดทำขึ้นสำหรับการค้นคว้าวิจัยเชิงลึกของโปรเจกต์ cbot-atgvt*