# 🧠 หมวดที่ 1: โครงสร้าง Limit Order Book (LOB/DOM) และโมเดล Deep Learning
### Limit Order Book Structure & Deep Learning Architectures

**ภาพรวมเนื้อหา:** การนำข้อมูล Level 2 (Bid/Ask Price & Depth) มาสร้างฟีเจอร์เชิงพื้นที่และลำดับเวลา ป้อนเข้าโมเดล CNN/LSTM/Transformers/T-KAN เพื่อพยากรณ์การเคลื่อนที่ของราคา Mid-Price

**ความสำคัญต่อการพัฒนา Bot Trade:** แกนหลักในการสกัดฟีเจอร์จาก DOM scraping เพื่อเทรน Machine Learning Robot ทำนายทิศทางราคาระยะสั้น (Scalping M1/M5) และตรวจจับคำสั่งหลอก (Spoofing Triaging)

---

## 📚 รายการงานวิจัยในหมวดนี้ (Curated Research Papers)

| ลำดับ | รหัส arXiv | ชื่องานวิจัย | ผู้แต่ง | ปี | ลิงก์อ่าน |
| :---: | :---: | :--- | :--- | :---: | :---: |
| 1 | [`1808.03668`](1808.03668_DeepLOB_ Deep Convolutional Neural Networks f.md) | DeepLOB: Deep Convolutional Neural Networks for Limit Order Books | Zihao Zhang, Stefan Zohren et al. | 2018 | [HTML](https://arxiv.org/html/1808.03668v6) / [PDF](https://arxiv.org/pdf/1808.03668v6.pdf) |
| 2 | [`2003.00130`](2003.00130_Transformers for Limit Order Books.md) | Transformers for Limit Order Books | James Wallbridge | 2020 | [HTML](https://arxiv.org/html/2003.00130v1) / [PDF](https://arxiv.org/pdf/2003.00130v1.pdf) |
| 3 | [`2405.18938`](2405.18938_HLOB -- Information Persistence and Structure.md) | HLOB -- Information Persistence and Structure in Limit Order Books | Antonio Briola, Silvia Bartolucci et al. | 2024 | [HTML](https://arxiv.org/html/2405.18938v3) / [PDF](https://arxiv.org/pdf/2405.18938v3.pdf) |
| 4 | [`2403.09267`](2403.09267_Deep Limit Order Book Forecasting.md) | Deep Limit Order Book Forecasting | Antonio Briola, Silvia Bartolucci et al. | 2024 | [HTML](https://arxiv.org/html/2403.09267v4) / [PDF](https://arxiv.org/pdf/2403.09267v4.pdf) |
| 5 | [`2003.00803`](2003.00803_Ascertaining price formation in cryptocurrenc.md) | Ascertaining price formation in cryptocurrency markets with DeepLearning | Fan Fang, Waichung Chung et al. | 2020 | [HTML](https://arxiv.org/html/2003.00803v1) / [PDF](https://arxiv.org/pdf/2003.00803v1.pdf) |
| 6 | [`2004.01499`](2004.01499_Deep Recurrent Modelling of Stationary Bitcoi.md) | Deep Recurrent Modelling of Stationary Bitcoin Price Formation Using the Order Flow | Ye-Sheen Lim, Denise Gorse | 2020 | [HTML](https://arxiv.org/html/2004.01499v1) / [PDF](https://arxiv.org/pdf/2004.01499v1.pdf) |
| 7 | [`1803.06917`](1803.06917_Universal features of price formation in fina.md) | Universal features of price formation in financial markets: perspectives from Deep Learning | Justin Sirignano, Rama Cont | 2018 | [HTML](https://arxiv.org/html/1803.06917v1) / [PDF](https://arxiv.org/pdf/1803.06917v1.pdf) |
| 8 | [`2112.09015`](2112.09015_Multivariate Realized Volatility Forecasting.md) | Multivariate Realized Volatility Forecasting with Graph Neural Network | Qinkai Chen, Christian-Yann Robert | 2021 | [HTML](https://arxiv.org/html/2112.09015v2) / [PDF](https://arxiv.org/pdf/2112.09015v2.pdf) |
| 9 | [`2403.13429`](2403.13429_Detecting and Triaging Spoofing using Tempora.md) | Detecting and Triaging Spoofing using Temporal Convolutional Networks | Kaushalya Kularatnam, Tania Stathaki | 2024 | [HTML](https://arxiv.org/html/2403.13429v1) / [PDF](https://arxiv.org/pdf/2403.13429v1.pdf) |
| 10 | [`2309.11400`](2309.11400_Transformers versus LSTMs for electronic trad.md) | Transformers versus LSTMs for electronic trading | Paul Bilokon, Yitao Qiu | 2023 | [HTML](https://arxiv.org/html/2309.11400v1) / [PDF](https://arxiv.org/pdf/2309.11400v1.pdf) |

---
*สารบัญนี้จัดทำขึ้นสำหรับการค้นคว้าวิจัยเชิงลึกของโปรเจกต์ cbot-atgvt*