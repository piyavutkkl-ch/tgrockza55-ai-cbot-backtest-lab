# 🎯 หมวดที่ 4: การส่งคำสั่งอย่างคุ้มค่า (Optimal Execution) และกลยุทธ์ VWAP/TWAP
### Optimal Execution, Market Impact Minimization & VWAP Strategies

**ภาพรวมเนื้อหา:** อัลกอริทึมการซอยคำสั่ง (Order Slicing / TWAP / VWAP) เพื่อลดค่า Slippage และ Market Impact รวมถึงการใช้ Reinforcement Learning ในการเลือกส่ง Market Order เทียบกับ Limit Order

**ความสำคัญต่อการพัฒนา Bot Trade:** แก้ปัญหาบอทกำไรใน Backtest แต่ขาดทุนในตลาดจริงเพราะโดนกินสเปรดและ Slippage โดยช่วยคำนวณเส้นทางการแบ่งไม้เข้า-ออกที่ดีที่สุด

---

## 📚 รายการงานวิจัยในหมวดนี้ (Curated Research Papers)

| ลำดับ | รหัส arXiv | ชื่องานวิจัย | ผู้แต่ง | ปี | ลิงก์อ่าน |
| :---: | :---: | :--- | :--- | :---: | :---: |
| 1 | [`2411.06389`](2411.06389_Optimal Execution with Reinforcement Learning.md) | Optimal Execution with Reinforcement Learning | Yadh Hafsi, Edoardo Vittori | 2024 | [HTML](https://arxiv.org/html/2411.06389v2) / [PDF](https://arxiv.org/pdf/2411.06389v2.pdf) |
| 2 | [`2506.11813`](2506.11813_Optimal Execution under Liquidity Uncertainty.md) | Optimal Execution under Liquidity Uncertainty | Etienne Chevalier, Yadh Hafsi et al. | 2025 | [HTML](https://arxiv.org/html/2506.11813v2) / [PDF](https://arxiv.org/pdf/2506.11813v2.pdf) |
| 3 | [`2411.04616`](2411.04616_Optimal Execution under Incomplete Informatio.md) | Optimal Execution under Incomplete Information | Etienne Chevalier, Yadh Hafsi et al. | 2024 | [HTML](https://arxiv.org/html/2411.04616v2) / [PDF](https://arxiv.org/pdf/2411.04616v2.pdf) |
| 4 | [`1409.2618`](1409.2618_Optimal Execution with Dynamic Order Flow Imb.md) | Optimal Execution with Dynamic Order Flow Imbalance | Kyle Bechler, Mike Ludkovski | 2014 | [HTML](https://arxiv.org/html/1409.2618v2) / [PDF](https://arxiv.org/pdf/1409.2618v2.pdf) |
| 5 | [`2306.00621`](2306.00621_Optimal execution and speculation with trade.md) | Optimal execution and speculation with trade signals | Peter Bank, Álvaro Cartea et al. | 2023 | [HTML](https://arxiv.org/html/2306.00621v3) / [PDF](https://arxiv.org/pdf/2306.00621v3.pdf) |
| 6 | [`1306.2832`](1306.2832_VWAP execution and guaranteed VWAP.md) | VWAP execution and guaranteed VWAP | Olivier Guéant, Guillaume Royer | 2013 | [HTML](https://arxiv.org/html/1306.2832v4) / [PDF](https://arxiv.org/pdf/1306.2832v4.pdf) |
| 7 | [`2212.14670`](2212.14670_Hierarchical Deep Reinforcement Learning for.md) | Hierarchical Deep Reinforcement Learning for VWAP Strategy Optimization | Xiaodong Li, Pangjing Wu et al. | 2022 | [HTML](https://arxiv.org/html/2212.14670v1) / [PDF](https://arxiv.org/pdf/2212.14670v1.pdf) |
| 8 | [`1408.6118`](1408.6118_VWAP Execution as an Optimal Strategy.md) | VWAP Execution as an Optimal Strategy | Takashi Kato | 2014 | [HTML](https://arxiv.org/html/1408.6118v4) / [PDF](https://arxiv.org/pdf/1408.6118v4.pdf) |
| 9 | [`2510.22206`](2510.22206_Right Place_ Right Time_ Market Simulation-ba.md) | Right Place, Right Time: Market Simulation-based RL for Execution Optimisation | Ollie Olby, Andreea Bacalum et al. | 2025 | [HTML](https://arxiv.org/html/2510.22206v1) / [PDF](https://arxiv.org/pdf/2510.22206v1.pdf) |
| 10 | [`2103.10860`](2103.10860_Universal Trading for Order Execution with Or.md) | Universal Trading for Order Execution with Oracle Policy Distillation | Yuchen Fang, Kan Ren et al. | 2021 | [HTML](https://arxiv.org/html/2103.10860v1) / [PDF](https://arxiv.org/pdf/2103.10860v1.pdf) |
| 11 | [`2507.06345`](2507.06345_Reinforcement Learning for Trade Execution wi.md) | Reinforcement Learning for Trade Execution with Market and Limit Orders | Patrick Cheridito, Moritz Weiss | 2025 | [HTML](https://arxiv.org/html/2507.06345v2) / [PDF](https://arxiv.org/pdf/2507.06345v2.pdf) |

---
*สารบัญนี้จัดทำขึ้นสำหรับการค้นคว้าวิจัยเชิงลึกของโปรเจกต์ cbot-atgvt*