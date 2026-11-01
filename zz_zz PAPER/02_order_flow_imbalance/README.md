# ⚡ หมวดที่ 2: แรงกดดันคำสั่งซื้อขาย (Order Flow Imbalance - OFI) และ Price Impact
### Order Flow Imbalance (OFI) & Price Impact Dynamics

**ภาพรวมเนื้อหา:** ทฤษฎีการคำนวณแรงซื้อขายสุทธิ (Order Flow Imbalance) จากการเปลี่ยนแปลงของ Best Bid/Ask, Limit Orders, Market Orders และ Cancellations รวมถึง Multi-Level OFI และ Cross-Asset Impact

**ความสำคัญต่อการพัฒนา Bot Trade:** ดัชนีตรวจจับแรงซื้อขายสถาบันที่เกิดขึ้นจริง แม่นยำกว่าแท่งเทียน ช่วยจับจังหวะการถูกดูดซับสภาพคล่อง (Absorption) หรือการหมดแรงของฝั่งตรงข้ามก่อนสไนเปอร์เข้าออเดอร์

---

## 📚 รายการงานวิจัยในหมวดนี้ (Curated Research Papers)

| ลำดับ | รหัส arXiv | ชื่องานวิจัย | ผู้แต่ง | ปี | ลิงก์อ่าน |
| :---: | :---: | :--- | :--- | :---: | :---: |
| 1 | [`1011.6402`](1011.6402_The Price Impact of Order Book Events.md) | The Price Impact of Order Book Events | Rama Cont, Arseniy Kukanov et al. | 2010 | [HTML](https://arxiv.org/html/1011.6402v3) / [PDF](https://arxiv.org/pdf/1011.6402v3.pdf) |
| 2 | [`0904.0900`](0904.0900_The price impact of order book events_ market.md) | The price impact of order book events: market orders, limit orders and cancellations | Zoltan Eisler, Jean-Philippe Bouchaud et al. | 2009 | [HTML](https://arxiv.org/html/0904.0900v3) / [PDF](https://arxiv.org/pdf/0904.0900v3.pdf) |
| 3 | [`2112.02947`](2112.02947_The Price Impact of Generalized Order Flow Im.md) | The Price Impact of Generalized Order Flow Imbalance | Yuhan Su, Zeyu Sun et al. | 2021 | [HTML](https://arxiv.org/html/2112.02947v1) / [PDF](https://arxiv.org/pdf/2112.02947v1.pdf) |
| 4 | [`2505.17388`](2505.17388_Stochastic Price Dynamics in Response to Orde.md) | Stochastic Price Dynamics in Response to Order Flow Imbalance: Evidence from CSI 300 Index Futures | Chen Hu, Kouxiao Zhang | 2025 | [HTML](https://arxiv.org/html/2505.17388v1) / [PDF](https://arxiv.org/pdf/2505.17388v1.pdf) |
| 5 | [`2408.03594`](2408.03594_Forecasting High Frequency Order Flow Imbalan.md) | Forecasting High Frequency Order Flow Imbalance | Aditya Nittur Anantha, Shashi Jain | 2024 | [HTML](https://arxiv.org/html/2408.03594v1) / [PDF](https://arxiv.org/pdf/2408.03594v1.pdf) |
| 6 | [`2110.00771`](2110.00771_Non-average price impact in order-driven mark.md) | Non-average price impact in order-driven markets | Claudio Bellani, Damiano Brigo et al. | 2021 | [HTML](https://arxiv.org/html/2110.00771v2) / [PDF](https://arxiv.org/pdf/2110.00771v2.pdf) |
| 7 | [`2609.36257`](2609.36257_When Hedging Changes the Payoff_ Option Repli.md) | When Hedging Changes the Payoff: Option Replication with Price Impact and Execution Costs | David Itkin, Leandro Sánchez-Betancourt | 2026 | [HTML](https://arxiv.org/html/2609.36257v1) / [PDF](https://arxiv.org/pdf/2609.36257v1.pdf) |
| 8 | [`2112.03789`](2112.03789_Self-exciting price impact via negative resil.md) | Self-exciting price impact via negative resilience in stochastic order books | Julia Ackermann, Thomas Kruse et al. | 2021 | [HTML](https://arxiv.org/html/2112.03789v2) / [PDF](https://arxiv.org/pdf/2112.03789v2.pdf) |
| 9 | [`2107.08684`](2107.08684_A characterisation of cross-impact kernels.md) | A characterisation of cross-impact kernels | Mathieu Rosenbaum, Mehdi Tomas | 2021 | [HTML](https://arxiv.org/html/2107.08684v1) / [PDF](https://arxiv.org/pdf/2107.08684v1.pdf) |
| 10 | [`2510.06879`](2510.06879_Nonparametric Estimation of Self- and Cross-I.md) | Nonparametric Estimation of Self- and Cross-Impact | Natascha Hey, Eyal Neuman et al. | 2025 | [HTML](https://arxiv.org/html/2510.06879v1) / [PDF](https://arxiv.org/pdf/2510.06879v1.pdf) |
| 11 | [`2112.13213`](2112.13213_Cross-Impact of Order Flow Imbalance in Equit.md) | Cross-Impact of Order Flow Imbalance in Equity Markets | Rama Cont, Mihai Cucuringu et al. | 2021 | [HTML](https://arxiv.org/html/2112.13213v4) / [PDF](https://arxiv.org/pdf/2112.13213v4.pdf) |

---
*สารบัญนี้จัดทำขึ้นสำหรับการค้นคว้าวิจัยเชิงลึกของโปรเจกต์ cbot-atgvt*