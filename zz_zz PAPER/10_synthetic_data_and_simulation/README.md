# 🧪 หมวดที่ 10: ข้อมูลตลาดสังเคราะห์ (Synthetic Market Data) และ Diffusion Models
### Synthetic LOB, Diffusion Models & Market Simulation

**ภาพรวมเนื้อหา:** การสร้างข้อมูลจำลอง Order Book และ Tick Data นับล้านฉากทัศน์ที่มีความสมจริงทางสถิติ เพื่อแก้ปัญหา Overfitting และทดสอบภาวะวิกฤติ

**ความสำคัญต่อการพัฒนา Bot Trade:** ใช้ Stress-test บอทก่อนลงเงินจริง เพื่อทดสอบว่าบอทจะรอดหรือไม่หากเกิดเหตุการณ์ Black Swan ที่ไม่เคยเกิดขึ้นในประวัติศาสตร์ 5 ปีหลัง

---

## 📚 รายการงานวิจัยในหมวดนี้ (Curated Research Papers)

| ลำดับ | รหัส arXiv | ชื่องานวิจัย | ผู้แต่ง | ปี | ลิงก์อ่าน |
| :---: | :---: | :--- | :--- | :---: | :---: |
| 1 | [`2610.12537`](2610.12537_Market Impact Estimation via Causal Foundatio.md) | Market Impact Estimation via Causal Foundation Models |  | 2026 | [HTML](https://arxiv.org/html/2610.12537) / [PDF](https://arxiv.org/pdf/2610.12537.pdf) |
| 2 | [`2602.03776`](2602.03776_DiffLOB_ Diffusion Models for Counterfactual.md) | DiffLOB: Diffusion Models for Counterfactual Generation in Limit Order Books |  | 2026 | [HTML](https://arxiv.org/html/2602.03776) / [PDF](https://arxiv.org/pdf/2602.03776.pdf) |
| 3 | [`2601.17247`](2601.17247_Learning Optimal Liquidation with Closing Auc.md) | Learning Optimal Liquidation with Closing Auctions |  | 2026 | [HTML](https://arxiv.org/html/2601.17247) / [PDF](https://arxiv.org/pdf/2601.17247.pdf) |
| 4 | [`2510.22685`](2510.22685_TABL-ABM_ A Hybrid Framework for Synthetic LO.md) | TABL-ABM: A Hybrid Framework for Synthetic LOB Generation |  | 2026 | [HTML](https://arxiv.org/html/2510.22685) / [PDF](https://arxiv.org/pdf/2510.22685.pdf) |
| 5 | [`2509.00982`](2509.00982_Prospects of Imitating Trading Agents in the.md) | Prospects of Imitating Trading Agents in the Stock Market |  | 2026 | [HTML](https://arxiv.org/html/2509.00982) / [PDF](https://arxiv.org/pdf/2509.00982.pdf) |
| 6 | [`2610.26358`](2610.26358_SHADE_ Shrinkage via Halted Alpha-stable Deno.md) | SHADE: Shrinkage via Halted Alpha-stable Denoising for Heavy-Tailed Probabilistic Time Series Forecasting |  | 2026 | [HTML](https://arxiv.org/html/2610.26358) / [PDF](https://arxiv.org/pdf/2610.26358.pdf) |
| 7 | [`2610.25495`](2610.25495_Probabilistic Limit Order Book Forecasting wi.md) | Probabilistic Limit Order Book Forecasting with Conditional Diffusion Models |  | 2026 | [HTML](https://arxiv.org/html/2610.25495) / [PDF](https://arxiv.org/pdf/2610.25495.pdf) |
| 8 | [`2610.13606`](2610.13606_CorrFlow_ Exact and Permutation-Equivariant F.md) | CorrFlow: Exact and Permutation-Equivariant Flow Matching on the Correlation Elliptope |  | 2026 | [HTML](https://arxiv.org/html/2610.13606) / [PDF](https://arxiv.org/pdf/2610.13606.pdf) |
| 9 | [`2609.37741`](2609.37741_Dyson-Schwinger Effective-Action Methods for.md) | Dyson-Schwinger Effective-Action Methods for Rough Volatility: A Correlation-Response Architecture for Calibration, Exotics and Risk |  | 2026 | [HTML](https://arxiv.org/html/2609.37741) / [PDF](https://arxiv.org/pdf/2609.37741.pdf) |
| 10 | [`2609.22893`](2609.22893_Universal Diffusion Models for Implied Volati.md) | Universal Diffusion Models for Implied Volatility Surfaces: Learning Shared Dynamics Across Stocks |  | 2026 | [HTML](https://arxiv.org/html/2609.22893) / [PDF](https://arxiv.org/pdf/2609.22893.pdf) |
| 11 | [`2610.28753`](2610.28753_Understanding the Inner Workings of a State-S.md) | Understanding the Inner Workings of a State-Space Foundation Model for Limit Order Books |  | 2026 | [HTML](https://arxiv.org/html/2610.28753) / [PDF](https://arxiv.org/pdf/2610.28753.pdf) |
| 12 | [`2610.27100`](2610.27100_LOB-Impact Benchmark_ Emergent Market Impact.md) | LOB-Impact Benchmark: Emergent Market Impact in Generative Limit Order Book Models |  | 2026 | [HTML](https://arxiv.org/html/2610.27100) / [PDF](https://arxiv.org/pdf/2610.27100.pdf) |
| 13 | [`2610.15973`](2610.15973_Requested_ Executed and Recoverable Credit_ S.md) | Requested, Executed and Recoverable Credit: Shared Action Ordering among LLM Borrowers in a Simulated Lending Market |  | 2026 | [HTML](https://arxiv.org/html/2610.15973) / [PDF](https://arxiv.org/pdf/2610.15973.pdf) |
| 14 | [`2610.07162`](2610.07162_Adversarial Training for Deep Hedging in Nons.md) | Adversarial Training for Deep Hedging in Nonstationary Markets |  | 2026 | [HTML](https://arxiv.org/html/2610.07162) / [PDF](https://arxiv.org/pdf/2610.07162.pdf) |
| 15 | [`2609.33767`](2609.33767_Taming the Greeks_ Option Portfolios with Ind.md) | Taming the Greeks: Option Portfolios with Inductive Biases |  | 2026 | [HTML](https://arxiv.org/html/2609.33767) / [PDF](https://arxiv.org/pdf/2609.33767.pdf) |

---
*สารบัญนี้จัดทำขึ้นสำหรับการค้นคว้าวิจัยเชิงลึกของโปรเจกต์ cbot-atgvt*