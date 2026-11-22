# 📚 TRADING CONDITION LIBRARY REPORT (V5 Scalping & Intraday Pattern Discovery)

> **Generated (UTC):** `2026-11-22T07:04:41.939304+00:00` · **Data Scope:** Tier 1 Pure Live L2 DOM/Order Flow/Real Spread + Tier 2 cTrader Real Multi-TF OHLCV (Strict Zero-Lookahead, Next-Bar Open + Friction, Chronological 60/40 IS/OOS + 3-Fold Walk-Forward)

---

## 1. Data Provenance & Portfolio Validation Summary

| Symbol | M1 Total Bars | Live DOM+Spread Bars | Order Flow Bars | Range (UTC) | Tested | `VALIDATED_OOS` | `REGIME_SPECIFIC` | `RARE_HIGH_EDGE` | `IS_ONLY_OVERFIT` | `NO_EDGE` | `INSUFFICIENT` |
| :--- | :---: | :---: | :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **XAUUSD** | 48,165 | 15,197 | 15,183 | `2026-10-04 22:43 -> 2026-11-20 21:54` | 565 | **66** | 131 | 20 | 92 | 108 | 148 |
| **BTCUSD** | 30,962 | 18,134 | 18,077 | `2026-10-31 17:02 -> 2026-11-22 07:03` | 646 | **93** | 97 | 28 | 74 | 169 | 185 |
| **ETHUSD** | 30,959 | 18,069 | 18,013 | `2026-10-31 17:05 -> 2026-11-22 07:03` | 419 | **6** | 26 | 6 | 18 | 221 | 142 |

## 1B. Iteration Round 1 vs Round 2 Yield Comparison

| Symbol | Round | Tested | `VALIDATED_OOS` | `REGIME_SPECIFIC` | `RARE_HIGH_EDGE` | `IS_ONLY_OVERFIT` | `NO_EDGE` | Total Edge Rate |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **XAUUSD** | Round 1 (Base) | 316 | **35** | 98 | 7 | 33 | 54 | `44.3%` |
| **XAUUSD** | Round 2 (OB + Session) | 249 | **31** | 33 | 13 | 59 | 54 | `30.9%` |
| **BTCUSD** | Round 1 (Base) | 366 | **35** | 68 | 4 | 26 | 97 | `29.2%` |
| **BTCUSD** | Round 2 (OB + Session) | 280 | **58** | 29 | 24 | 48 | 72 | `39.6%` |
| **ETHUSD** | Round 1 (Base) | 241 | **0** | 13 | 2 | 4 | 143 | `6.2%` |
| **ETHUSD** | Round 2 (OB + Session) | 178 | **6** | 13 | 4 | 14 | 78 | `12.9%` |

## 2. Empirical Multi-Timeframe Confluence Proof (`1 TF` vs `2 TF` vs `3+ TF`)

| Symbol | Tier | Patterns | Avg OOS N | Avg OOS P(Dir) | Avg OOS Win Rate | Avg OOS Expectancy (USD) | Avg OOS PF | Verdict |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **XAUUSD** | `1_TF` | 10 | 258.2 | 43.3% | 41.4% | -0.1797 | 0.97 | `-` |
| **XAUUSD** | `2_TF` | 10 | 166.9 | 42.2% | 36.0% | -0.4766 | 0.88 | `-` |
| **XAUUSD** | `3_PLUS_TF` | 9 | 131.1 | 42.8% | 39.1% | -0.2195 | 0.98 | `CONFLUENCE_NOT_MONOTONIC_OVER_SINGLE_TF` |
| **BTCUSD** | `1_TF` | 10 | 327.9 | 40.6% | 37.0% | -0.2274 | 0.79 | `-` |
| **BTCUSD** | `2_TF` | 10 | 244.6 | 42.4% | 37.6% | -0.1816 | 0.81 | `-` |
| **BTCUSD** | `3_PLUS_TF` | 9 | 174.4 | 42.3% | 37.5% | -0.1581 | 0.85 | `CONFLUENCE_IMPROVES_PROB_AND_EXP` |
| **ETHUSD** | `1_TF` | 10 | 350.1 | 36.0% | 26.8% | -0.0360 | 0.39 | `-` |
| **ETHUSD** | `2_TF` | 10 | 278.0 | 37.5% | 26.9% | -0.0325 | 0.39 | `-` |
| **ETHUSD** | `3_PLUS_TF` | 9 | 209.4 | 37.8% | 29.0% | -0.0304 | 0.44 | `CONFLUENCE_IMPROVES_PROB_AND_EXP` |

---

## 3. XAUUSD — Top Discovered Conditions & 20-Field Trading Condition Library

| Rank | Condition Name | Type | TFs | Dir | OOS P(Dir) / Lift | OOS WR (Wilson LB) | OOS Exp (USD) | OOS PF | MFE / MAE | Horizon | Freq/Day | N (IS/OOS) | SL/TP (ATR) | WF Folds | Jitter ±15% | Status / Reliability |
| :---: | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| #1 | `SEQ: COMPRESSION -> BREAKOUT_UP` | Sequential | `M1` | **BUY** | 100.0% (+69.5%) | 80.0% (37.5%) | +4.0396 | 6.82 | 1.41 / 1.32 | `+5b` | 2.2/d | 23 (18/5) | 1.2 / 2.0 | 3/3 | PASS | `VALIDATED_OOS` (`MEDIUM`) |
| #2 | `SES[ASIA]: MTF: M15_SWEEP_HIGH -> M1_VA_REJECT_VAH` | Session-Micro | `M1+M15` | **SELL** | 100.0% (+54.6%) | 88.9% (56.5%) | +2.0846 | 9.04 | 2.85 / 1.96 | `+15b` | 2.4/d | 25 (16/9) | 1.0 / 1.5 | 1/3 | PASS | `VALIDATED_OOS` (`MEDIUM`) |
| #3 | `SES[LONDON]: SPREAD_EXPANSION` | Session-Micro | `M1` | **BUY** | 60.0% (+27.0%) | 71.4% (35.9%) | +2.8763 | 4.57 | 1.54 / 0.67 | `+5b` | 3.5/d | 37 (27/10) | 1.2 / 2.0 | 2/3 | FRAGILE | `VALIDATED_OOS` (`MEDIUM`) |
| #4 | `SEQ: DOM_STACK_BEAR -> LADDER_THIN_BID` | Sequential | `M1` | **SELL** | 60.0% (+16.3%) | 68.4% (46.0%) | +4.2011 | 2.75 | 2.64 / 1.69 | `+15b` | 4.6/d | 49 (29/20) | 2.0 / 3.0 | 3/3 | PASS | `VALIDATED_OOS` (`MEDIUM`) |
| #5 | `FLOW_SWEEP_HIGH` | Single | `M1` | **SELL** | 58.8% (+14.1%) | 52.9% (31.0%) | +2.7271 | 2.72 | 2.31 / 1.73 | `+15b` | 5.5/d | 58 (41/17) | 1.5 / 2.5 | 2/3 | PASS | `VALIDATED_OOS` (`MEDIUM`) |
| #6 | `SEQ: VA_REJECT_VAL -> BOS_BULL` | Sequential | `M1` | **BUY** | 61.5% (+20.8%) | 61.5% (35.5%) | +1.6291 | 2.34 | 3.24 / 2.37 | `+30b` | 2.8/d | 30 (16/14) | 1.5 / 2.0 | 2/3 | PASS | `VALIDATED_OOS` (`MEDIUM`) |
| #7 | `SEQ: FLOW_SWEEP_HIGH -> DEPTH_ICEBERG_BATTLE` | Sequential | `M1` | **SELL** | 57.1% (+20.8%) | 57.1% (25.1%) | +2.5447 | 2.59 | 1.39 / 1.02 | `+5b` | 2.0/d | 21 (14/7) | 1.0 / 1.5 | 1/3 | FRAGILE | `VALIDATED_OOS` (`MEDIUM`) |
| #8 | `SES[ASIA]: MTF: DEV_H1_REJECTION_BULL -> M1_DOM_ABSORPTION_BUY` | Session-Micro | `H1+M1` | **BUY** | 60.0% (+21.1%) | 66.7% (35.4%) | +3.0218 | 1.89 | 5.51 / 2.98 | `+60b` | 2.2/d | 23 (13/10) | 2.0 / 3.0 | 2/3 | FRAGILE | `VALIDATED_OOS` (`MEDIUM`) |
| #9 | `SEQ: DEPTH_ICEBERG_BATTLE -> CVD_SURGE_BEAR` | Sequential | `M1` | **SELL** | 62.0% (+26.2%) | 54.4% (40.2%) | +1.3347 | 1.59 | 1.28 / 0.75 | `+5b` | 9.9/d | 105 (55/50) | 1.2 / 2.0 | 2/3 | PASS | `VALIDATED_OOS` (`HIGH`) |
| #10 | `SES[ASIA]: SEQ: SWEEP_HIGH -> RECLAIM_HIGH+DOM_ABSORPTION_SELL` | Session-Micro | `M1` | **SELL** | 64.3% (+17.4%) | 53.8% (29.1%) | +1.4417 | 1.65 | 3.40 / 2.78 | `+30b` | 5.1/d | 54 (40/14) | 2.0 / 3.0 | 3/3 | PASS | `VALIDATED_OOS` (`MEDIUM`) |
| #11 | `MTF: H1_RANGE -> M1_BOS_BEAR` | Multi-TF | `H1+M1` | **SELL** | 48.3% (-0.6%) | 62.5% (38.6%) | +2.1000 | 2.54 | 3.29 / 2.74 | `+30b` | 9.5/d | 100 (71/29) | 2.0 / 3.0 | 2/3 | PASS | `VALIDATED_OOS` (`MEDIUM`) |
| #12 | `MTF: H1_NEAR_SUPPORT -> M15_FAILED_RETEST_BOT -> M1_DISPLACEMENT_BULL` | Multi-TF | `H1+M1+M15` | **BUY** | 56.8% (+15.4%) | 50.0% (34.5%) | +1.2373 | 1.72 | 5.00 / 3.82 | `+60b` | 8.4/d | 89 (52/37) | 1.5 / 2.5 | 2/3 | PASS | `VALIDATED_OOS` (`MEDIUM`) |
| #13 | `SES[NY]: SPREAD_SNAPBACK` | Session-Micro | `M1` | **SELL** | 43.6% (+7.0%) | 61.9% (46.8%) | +2.6885 | 2.10 | 1.28 / 1.00 | `+5b` | 12.9/d | 136 (81/55) | 2.0 / 3.0 | 2/3 | PASS | `VALIDATED_OOS` (`HIGH`) |
| #14 | `MTF: H1_NEAR_RESIST -> M15_FAILED_RETEST_TOP -> M1_DISPLACEMENT_BEAR` | Multi-TF | `H1+M1+M15` | **SELL** | 55.6% (+11.8%) | 57.1% (25.1%) | +1.9381 | 2.09 | 2.58 / 1.81 | `+15b` | 5.0/d | 53 (44/9) | 2.0 / 3.0 | 1/3 | PASS | `VALIDATED_OOS` (`MEDIUM`) |
| #15 | `MTF: H1_RANGE -> M5_FALSE_BREAK_DOWN -> M1_REJECTION_BULL` | Multi-TF | `H1+M1+M5` | **BUY** | 54.2% (+14.3%) | 52.4% (32.4%) | +1.1669 | 1.57 | 3.06 / 2.92 | `+30b` | 11.1/d | 117 (93/24) | 2.0 / 3.0 | 2/3 | PASS | `VALIDATED_OOS` (`MEDIUM`) |
| #16 | `SEQ: VWAP_EXTREME_HIGH -> DOM_ABSORPTION_SELL -> RECLAIM_HIGH` | Sequential | `M1` | **SELL** | 57.1% (+20.2%) | 83.3% (43.6%) | +2.6599 | 4.05 | 1.51 / 1.82 | `+15b` | 2.8/d | 30 (23/7) | 2.0 / 3.0 | 1/3 | PASS | `REGIME_SPECIFIC_EDGE` (`LOW`) |
| #17 | `SES[NY]: SEQ: DEPTH_ICEBERG_BATTLE -> VOL_SPIKE_SESSION` | Session-Micro | `M1` | **BUY** | 35.3% (-1.0%) | 50.0% (26.8%) | +1.8437 | 1.75 | 2.13 / 2.15 | `+15b` | 3.1/d | 33 (16/17) | 1.5 / 2.5 | 3/3 | FRAGILE | `VALIDATED_OOS` (`MEDIUM`) |
| #18 | `SEQ: DEPTH_ICEBERG_BATTLE -> VWAP_EXTREME_LOW` | Sequential | `M1` | **BUY** | 60.0% (+20.5%) | 50.0% (28.0%) | +1.6288 | 1.42 | 2.97 / 3.02 | `+30b` | 1.9/d | 20 (3/17) | 2.0 / 3.0 | 1/3 | FRAGILE | `VALIDATED_OOS` (`MEDIUM`) |
| #19 | `SEQ: LIQUIDITY_PULL_SHOCK -> SPREAD_SNAPBACK -> RECLAIM_HIGH` | Sequential | `M1` | **SELL** | 42.9% (+7.2%) | 57.1% (36.5%) | +1.5724 | 1.71 | 1.15 / 1.00 | `+5b` | 7.3/d | 77 (56/21) | 1.5 / 2.5 | 2/3 | PASS | `VALIDATED_OOS` (`HIGH`) |
| #20 | `BREAKOUT_DOWN` | Single | `M1` | **SELL** | 48.6% (+12.6%) | 53.7% (44.9%) | +0.8252 | 1.43 | 1.38 / 1.01 | `+5b` | 31.8/d | 336 (194/142) | 1.5 / 2.0 | 2/3 | PASS | `VALIDATED_OOS` (`HIGH`) |

### XAUUSD — Structured Event Sequences (`HTF Context → MTF Setup → LTF Trigger → Entry → Outcome`)

- **#1 `SEQ: COMPRESSION -> BREAKOUT_UP`** (VALIDATED_OOS): `M1 Sequence [COMPRESSION -> BREAKOUT_UP] -> Next-Bar Open Entry -> Expected Outcome` · BUY over next 5 M1 bars (~5m): OOS P(BUY)=100.0% (vs baseline 30.5%, lift +69.5%), avg move +1.673 ATR, MFE before MAE 45.5% | Ablation Lift vs prev: ΔP=`+68.5%`, ΔExp=`+5.2045 USD`
- **#2 `SES[ASIA]: MTF: M15_SWEEP_HIGH -> M1_VA_REJECT_VAH`** (VALIDATED_OOS): `[ASIA] M15_SWEEP_HIGH -> M1 [VA_REJECT_VAH] -> Next-Bar Open Entry -> Expected Outcome` · SELL over next 15 M1 bars (~15m): OOS P(SELL)=100.0% (vs baseline 45.4%, lift +54.6%), avg move -3.846 ATR, MFE before MAE 68.0%
- **#3 `SES[LONDON]: SPREAD_EXPANSION`** (VALIDATED_OOS): `[LONDON] M1 Trigger [SPREAD_EXPANSION] -> Next-Bar Open Entry -> Expected Outcome` · BUY over next 5 M1 bars (~5m): OOS P(BUY)=60.0% (vs baseline 33.0%, lift +27.0%), avg move +1.111 ATR, MFE before MAE 67.6%
- **#4 `SEQ: DOM_STACK_BEAR -> LADDER_THIN_BID`** (VALIDATED_OOS): `M1 OrderBook Sequence [DOM_STACK_BEAR -> LADDER_THIN_BID] -> Next-Bar Open Entry -> Expected Outcome` · SELL over next 15 M1 bars (~15m): OOS P(SELL)=60.0% (vs baseline 43.7%, lift +16.3%), avg move -1.115 ATR, MFE before MAE 62.5% | Ablation Lift vs prev: ΔP=`-2.5%`, ΔExp=`+3.2463 USD`
- **#5 `FLOW_SWEEP_HIGH`** (VALIDATED_OOS): `M1 Trigger [FLOW_SWEEP_HIGH] -> Next-Bar Open Entry -> Expected Outcome` · SELL over next 15 M1 bars (~15m): OOS P(SELL)=58.8% (vs baseline 44.8%, lift +14.1%), avg move -0.823 ATR, MFE before MAE 47.4%
- **#6 `SEQ: VA_REJECT_VAL -> BOS_BULL`** (VALIDATED_OOS): `M1 OrderBook Sequence [VA_REJECT_VAL -> BOS_BULL] -> Next-Bar Open Entry -> Expected Outcome` · BUY over next 30 M1 bars (~30m): OOS P(BUY)=61.5% (vs baseline 40.7%, lift +20.8%), avg move +1.085 ATR, MFE before MAE 34.5% | Ablation Lift vs prev: ΔP=`+23.6%`, ΔExp=`+3.1736 USD`
- **#7 `SEQ: FLOW_SWEEP_HIGH -> DEPTH_ICEBERG_BATTLE`** (VALIDATED_OOS): `M1 Sequence [FLOW_SWEEP_HIGH -> DEPTH_ICEBERG_BATTLE] -> Next-Bar Open Entry -> Expected Outcome` · SELL over next 5 M1 bars (~5m): OOS P(SELL)=57.1% (vs baseline 36.4%, lift +20.8%), avg move -0.625 ATR, MFE before MAE 57.1% | Ablation Lift vs prev: ΔP=`-1.7%`, ΔExp=`-0.1824 USD`
- **#8 `SES[ASIA]: MTF: DEV_H1_REJECTION_BULL -> M1_DOM_ABSORPTION_BUY`** (VALIDATED_OOS): `[ASIA] DEV_H1_REJECTION_BULL -> M1 [DOM_ABSORPTION_BUY] -> Next-Bar Open Entry -> Expected Outcome` · BUY over next 60 M1 bars (~60m): OOS P(BUY)=60.0% (vs baseline 38.9%, lift +21.1%), avg move +0.945 ATR, MFE before MAE 65.2%

### XAUUSD — Branching Patterns (Same Prefix Diverging by Next Step)

- Prefix `SWEEP_LOW`: `RECLAIM_LOW+DOM_ABSORPTION_BUY` ➔ **BUY** (N=153, OOS P=44.6%, Exp=-0.489) ; `HIGHER_LOW` ➔ **BUY** (N=428, OOS P=30.2%, Exp=-0.552) ; `RECLAIM_LOW` ➔ **BUY** (N=938, OOS P=37.8%, Exp=-0.639) ; `RETEST_SUPPORT_2X` ➔ **BUY** (N=863, OOS P=34.5%, Exp=-1.354)
- Prefix `SWEEP_HIGH`: `RECLAIM_HIGH` ➔ **SELL** (N=891, OOS P=48.5%, Exp=+1.909) ; `LOWER_HIGH` ➔ **SELL** (N=462, OOS P=46.3%, Exp=+0.878) ; `RETEST_RESIST_2X` ➔ **SELL** (N=832, OOS P=36.8%, Exp=+0.637) ; `RECLAIM_HIGH+DOM_ABSORPTION_SELL` ➔ **SELL** (N=158, OOS P=40.4%, Exp=-0.649)
- Prefix `EXHAUSTION_BOT`: `POC_RECLAIM_BULL` ➔ **BUY** (N=14, OOS P=40.0%, Exp=+2.263) ; `SWEEP_LOW` ➔ **BUY** (N=197, OOS P=27.4%, Exp=-0.296) ; `DEPTH_ICEBERG_BATTLE` ➔ **BUY** (N=55, OOS P=37.8%, Exp=-0.371) ; `REJECTION_BULL` ➔ **BUY** (N=106, OOS P=33.9%, Exp=-0.444)
- Prefix `FLOW_SWEEP_LOW`: `VOL_SPIKE_SESSION` ➔ **BUY** (N=28, OOS P=37.5%, Exp=-0.143) ; `EXHAUSTION_BOT` ➔ **BUY** (N=34, OOS P=50.0%, Exp=-0.418) ; `DEPTH_ICEBERG_BATTLE` ➔ **BUY** (N=21, OOS P=27.3%, Exp=-1.614) ; `REJECTION_BULL` ➔ **BUY** (N=45, OOS P=33.3%, Exp=-1.699)

---

## 3. BTCUSD — Top Discovered Conditions & 20-Field Trading Condition Library

| Rank | Condition Name | Type | TFs | Dir | OOS P(Dir) / Lift | OOS WR (Wilson LB) | OOS Exp (USD) | OOS PF | MFE / MAE | Horizon | Freq/Day | N (IS/OOS) | SL/TP (ATR) | WF Folds | Jitter ±15% | Status / Reliability |
| :---: | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| #1 | `SEQ: VA_REJECT_VAH -> DELTA_DIVERGENCE_BEAR` | Sequential | `M1` | **SELL** | 76.5% (+42.7%) | 64.7% (41.3%) | +1.2308 | 4.34 | 1.38 / 0.70 | `+5b` | 4.9/d | 62 (45/17) | 1.5 / 2.5 | 3/3 | PASS | `VALIDATED_OOS` (`MEDIUM`) |
| #2 | `MTF: M15_SWEEP_HIGH -> M1_VA_REJECT_VAH` | Multi-TF | `M1+M15` | **SELL** | 78.4% (+25.2%) | 68.0% (48.4%) | +1.1518 | 3.49 | 3.56 / 2.60 | `+60b` | 8.2/d | 103 (66/37) | 2.0 / 3.0 | 3/3 | PASS | `VALIDATED_OOS` (`HIGH`) |
| #3 | `MTF: H1_RANGE -> M1_VWAP_EXTREME_HIGH` | Multi-TF | `H1+M1` | **SELL** | 83.3% (+21.4%) | 66.7% (30.0%) | +1.3121 | 4.82 | 3.85 / 3.37 | `+60b` | 2.2/d | 28 (22/6) | 1.2 / 2.0 | 3/3 | PASS | `VALIDATED_OOS` (`MEDIUM`) |
| #4 | `SEQ: FLOW_SWEEP_HIGH -> DELTA_DIVERGENCE_BEAR` | Sequential | `M1` | **SELL** | 57.1% (+22.9%) | 57.1% (36.5%) | +1.0514 | 2.57 | 1.27 / 0.77 | `+5b` | 3.0/d | 38 (17/21) | 2.0 / 3.0 | 3/3 | PASS | `VALIDATED_OOS` (`HIGH`) |
| #5 | `SEQ: FLOW_SWEEP_HIGH -> SPREAD_SNAPBACK` | Sequential | `M1` | **SELL** | 65.6% (+16.1%) | 61.3% (43.8%) | +0.9081 | 2.32 | 2.70 / 1.70 | `+30b` | 5.9/d | 74 (41/33) | 2.0 / 3.0 | 3/3 | PASS | `VALIDATED_OOS` (`HIGH`) |
| #6 | `SEQ: DOM_FLIP_BEAR -> DELTA_DIVERGENCE_BEAR` | Sequential | `M1` | **SELL** | 78.6% (+30.2%) | 76.9% (49.7%) | +1.9931 | 4.79 | 4.16 / 2.25 | `+60b` | 2.6/d | 33 (19/14) | 2.0 / 3.0 | 2/3 | PASS | `REGIME_SPECIFIC_EDGE` (`MEDIUM`) |
| #7 | `SES[ASIA]: MTF: M15_SWEEP_HIGH -> M1_DELTA_DIVERGENCE_BEAR` | Session-Micro | `M15+M1` | **SELL** | 52.2% (+9.6%) | 61.1% (38.6%) | +0.9869 | 2.82 | 1.83 / 1.34 | `+15b` | 5.6/d | 71 (47/24) | 2.0 / 3.0 | 3/3 | PASS | `VALIDATED_OOS` (`MEDIUM`) |
| #8 | `SEQ: POC_RECLAIM_BEAR -> CVD_SURGE_BEAR` | Sequential | `M1` | **SELL** | 48.1% (+2.6%) | 66.7% (45.4%) | +1.0599 | 2.99 | 3.00 / 2.04 | `+30b` | 4.5/d | 56 (29/27) | 2.0 / 3.0 | 2/3 | PASS | `VALIDATED_OOS` (`HIGH`) |
| #9 | `MTF: M15_SWEEP_HIGH -> M1_EXHAUSTION_TOP` | Multi-TF | `M15+M1` | **SELL** | 37.5% (+2.5%) | 68.8% (44.4%) | +1.1723 | 3.32 | 1.15 / 1.04 | `+5b` | 2.9/d | 36 (20/16) | 2.0 / 3.0 | 2/3 | PASS | `VALIDATED_OOS` (`MEDIUM`) |
| #10 | `SES[NY]: MTF: H1_TREND_BEAR -> M1_SPREAD_SNAPBACK` | Session-Micro | `H1+M1` | **SELL** | 65.6% (+12.9%) | 50.0% (28.0%) | +0.9288 | 1.87 | 4.05 / 2.65 | `+60b` | 10.4/d | 131 (99/32) | 2.0 / 3.0 | 3/3 | PASS | `VALIDATED_OOS` (`MEDIUM`) |
| #11 | `SEQ: FLOW_SWEEP_HIGH -> RETEST_RESIST_2X -> DOM_IMBALANCE_BEAR` | Sequential | `M1` | **SELL** | 100.0% (+43.2%) | 66.7% (35.4%) | +0.7828 | 2.39 | 5.75 / 2.12 | `+60b` | 1.8/d | 22 (13/9) | 2.0 / 3.0 | 3/3 | PASS | `VALIDATED_OOS` (`MEDIUM`) |
| #12 | `MTF: M15_SWEEP_HIGH -> M1_DELTA_DIVERGENCE_BEAR` | Multi-TF | `M15+M1` | **SELL** | 56.0% (+13.3%) | 53.3% (40.9%) | +0.6625 | 1.83 | 1.97 / 1.43 | `+15b` | 16.1/d | 203 (127/76) | 2.0 / 3.0 | 2/3 | PASS | `VALIDATED_OOS` (`HIGH`) |
| #13 | `SES[NY]: MTF: M15_SWEEP_HIGH -> M1_DELTA_DIVERGENCE_BEAR` | Session-Micro | `M15+M1` | **SELL** | 52.2% (+16.2%) | 50.0% (29.0%) | +0.9322 | 1.93 | 1.25 / 0.96 | `+5b` | 5.0/d | 63 (40/23) | 2.0 / 3.0 | 3/3 | PASS | `VALIDATED_OOS` (`MEDIUM`) |
| #14 | `SEQ: BREAKOUT_DOWN -> DOM_IMBALANCE_BEAR -> BREAKOUT_DOWN` | Sequential | `M1` | **SELL** | 60.0% (+27.6%) | 57.1% (32.6%) | +0.9340 | 2.24 | 1.48 / 1.60 | `+5b` | 2.1/d | 26 (11/15) | 2.0 / 3.0 | 2/3 | PASS | `VALIDATED_OOS` (`MEDIUM`) |
| #15 | `SEQ: FLOW_SWEEP_HIGH -> RSI_OVERBOUGHT` | Sequential | `M1` | **SELL** | 66.7% (+19.3%) | 66.7% (35.4%) | +1.0936 | 2.51 | 2.31 / 1.56 | `+30b` | 1.8/d | 22 (13/9) | 2.0 / 3.0 | 3/3 | PASS | `VALIDATED_OOS` (`MEDIUM`) |
| #16 | `SEQ: DELTA_DIVERGENCE_BEAR -> DOM_ABSORPTION_SELL` | Sequential | `M1` | **SELL** | 65.0% (+18.1%) | 66.7% (45.4%) | +0.6148 | 2.84 | 2.57 / 2.14 | `+30b` | 4.0/d | 51 (30/21) | 1.0 / 1.5 | 3/3 | PASS | `VALIDATED_OOS` (`HIGH`) |
| #17 | `SEQ: VA_REJECT_VAH -> DOM_IMBALANCE_BEAR` | Sequential | `M1` | **SELL** | 70.0% (+22.1%) | 80.0% (49.0%) | +1.4912 | 4.73 | 3.03 / 1.67 | `+30b` | 2.3/d | 29 (19/10) | 2.0 / 3.0 | 2/3 | PASS | `REGIME_SPECIFIC_EDGE` (`LOW`) |
| #18 | `SES[NY]: VA_REJECT_VAH` | Session-Micro | `M1` | **SELL** | 100.0% (+41.7%) | 70.0% (39.7%) | +1.4070 | 2.71 | 4.25 / 2.46 | `+60b` | 2.6/d | 33 (22/11) | 2.0 / 3.0 | 2/3 | PASS | `REGIME_SPECIFIC_EDGE` (`LOW`) |
| #19 | `SEQ: FLOW_SWEEP_HIGH -> RETEST_RESIST_2X -> SPREAD_SNAPBACK` | Sequential | `M1` | **SELL** | 59.3% (+9.1%) | 63.0% (44.2%) | +0.7752 | 2.21 | 2.78 / 1.78 | `+30b` | 5.2/d | 65 (37/28) | 2.0 / 3.0 | 2/3 | PASS | `VALIDATED_OOS` (`HIGH`) |
| #20 | `MTF: M15_SWEEP_HIGH -> M1_RSI_OVERBOUGHT` | Multi-TF | `M15+M1` | **SELL** | 61.9% (+11.0%) | 60.0% (38.7%) | +0.8448 | 2.16 | 4.15 / 2.24 | `+60b` | 3.3/d | 42 (21/21) | 2.0 / 3.0 | 2/3 | PASS | `VALIDATED_OOS` (`HIGH`) |

### BTCUSD — Structured Event Sequences (`HTF Context → MTF Setup → LTF Trigger → Entry → Outcome`)

- **#1 `SEQ: VA_REJECT_VAH -> DELTA_DIVERGENCE_BEAR`** (VALIDATED_OOS): `M1 OrderBook Sequence [VA_REJECT_VAH -> DELTA_DIVERGENCE_BEAR] -> Next-Bar Open Entry -> Expected Outcome` · SELL over next 5 M1 bars (~5m): OOS P(SELL)=76.5% (vs baseline 33.8%, lift +42.7%), avg move -0.916 ATR, MFE before MAE 69.3% | Ablation Lift vs prev: ΔP=`+2.6%`, ΔExp=`+0.8711 USD`
- **#2 `MTF: M15_SWEEP_HIGH -> M1_VA_REJECT_VAH`** (VALIDATED_OOS): `M15_SWEEP_HIGH -> M1 [VA_REJECT_VAH] -> Next-Bar Open Entry -> Expected Outcome` · SELL over next 60 M1 bars (~60m): OOS P(SELL)=78.4% (vs baseline 53.2%, lift +25.2%), avg move -1.867 ATR, MFE before MAE 47.6%
- **#3 `MTF: H1_RANGE -> M1_VWAP_EXTREME_HIGH`** (VALIDATED_OOS): `H1_RANGE -> M1 [VWAP_EXTREME_HIGH] -> Next-Bar Open Entry -> Expected Outcome` · SELL over next 60 M1 bars (~60m): OOS P(SELL)=83.3% (vs baseline 61.9%, lift +21.4%), avg move -2.688 ATR, MFE before MAE 60.7%
- **#4 `SEQ: FLOW_SWEEP_HIGH -> DELTA_DIVERGENCE_BEAR`** (VALIDATED_OOS): `M1 Sequence [FLOW_SWEEP_HIGH -> DELTA_DIVERGENCE_BEAR] -> Next-Bar Open Entry -> Expected Outcome` · SELL over next 5 M1 bars (~5m): OOS P(SELL)=57.1% (vs baseline 34.2%, lift +22.9%), avg move -0.586 ATR, MFE before MAE 52.6% | Ablation Lift vs prev: ΔP=`-11.4%`, ΔExp=`+1.1016 USD`
- **#5 `SEQ: FLOW_SWEEP_HIGH -> SPREAD_SNAPBACK`** (VALIDATED_OOS): `M1 Sequence [FLOW_SWEEP_HIGH -> SPREAD_SNAPBACK] -> Next-Bar Open Entry -> Expected Outcome` · SELL over next 30 M1 bars (~30m): OOS P(SELL)=65.6% (vs baseline 49.5%, lift +16.1%), avg move -1.106 ATR, MFE before MAE 60.3% | Ablation Lift vs prev: ΔP=`-2.9%`, ΔExp=`+0.9583 USD`
- **#6 `SEQ: DOM_FLIP_BEAR -> DELTA_DIVERGENCE_BEAR`** (REGIME_SPECIFIC_EDGE): `M1 OrderBook Sequence [DOM_FLIP_BEAR -> DELTA_DIVERGENCE_BEAR] -> Next-Bar Open Entry -> Expected Outcome` · SELL over next 60 M1 bars (~60m): OOS P(SELL)=78.6% (vs baseline 48.4%, lift +30.2%), avg move -2.173 ATR, MFE before MAE 57.6% | Ablation Lift vs prev: ΔP=`+20.5%`, ΔExp=`+1.7864 USD`
- **#7 `SES[ASIA]: MTF: M15_SWEEP_HIGH -> M1_DELTA_DIVERGENCE_BEAR`** (VALIDATED_OOS): `[ASIA] M15_SWEEP_HIGH -> M1 [DELTA_DIVERGENCE_BEAR] -> Next-Bar Open Entry -> Expected Outcome` · SELL over next 15 M1 bars (~15m): OOS P(SELL)=52.2% (vs baseline 42.6%, lift +9.6%), avg move -0.486 ATR, MFE before MAE 65.7%
- **#8 `SEQ: POC_RECLAIM_BEAR -> CVD_SURGE_BEAR`** (VALIDATED_OOS): `M1 Sequence [POC_RECLAIM_BEAR -> CVD_SURGE_BEAR] -> Next-Bar Open Entry -> Expected Outcome` · SELL over next 30 M1 bars (~30m): OOS P(SELL)=48.1% (vs baseline 45.6%, lift +2.6%), avg move -0.857 ATR, MFE before MAE 66.1% | Ablation Lift vs prev: ΔP=`-10.2%`, ΔExp=`+1.1870 USD`

### BTCUSD — Branching Patterns (Same Prefix Diverging by Next Step)

- Prefix `BREAKOUT_DOWN`: `DOM_IMBALANCE_BEAR` ➔ **SELL** (N=77, OOS P=46.9%, Exp=+0.507) ; `DELTA_DIVERGENCE_BEAR` ➔ **SELL** (N=74, OOS P=57.7%, Exp=+0.488) ; `POC_RECLAIM_BEAR` ➔ **SELL** (N=15, OOS P=42.9%, Exp=+0.290) ; `FALSE_BREAKOUT_DOWN` ➔ **BUY** (N=305, OOS P=46.5%, Exp=+0.017)
- Prefix `BREAKOUT_UP`: `FALSE_BREAKOUT_UP` ➔ **SELL** (N=257, OOS P=44.8%, Exp=+0.186) ; `SPREAD_SNAPBACK` ➔ **BUY** (N=235, OOS P=32.4%, Exp=-0.421) ; `COMPRESSION` ➔ **BUY** (N=26, OOS P=33.3%, Exp=-0.485) ; `DEPTH_ICEBERG_BATTLE` ➔ **BUY** (N=44, OOS P=17.4%, Exp=-0.713)
- Prefix `EXHAUSTION_TOP`: `DEPTH_ICEBERG_BATTLE` ➔ **SELL** (N=26, OOS P=55.6%, Exp=+0.529) ; `BREAKOUT_DOWN` ➔ **SELL** (N=11, OOS P=50.0%, Exp=+0.300) ; `SPREAD_SNAPBACK` ➔ **SELL** (N=104, OOS P=59.5%, Exp=+0.239) ; `DELTA_DIVERGENCE_BEAR` ➔ **SELL** (N=51, OOS P=55.0%, Exp=+0.120)
- Prefix `COMPRESSION`: `DELTA_DIVERGENCE_BEAR` ➔ **SELL** (N=20, OOS P=57.1%, Exp=+0.281) ; `DOM_IMBALANCE_BEAR` ➔ **SELL** (N=18, OOS P=62.5%, Exp=+0.230) ; `SPREAD_SNAPBACK` ➔ **BUY** (N=103, OOS P=36.1%, Exp=-0.032) ; `BREAKOUT_UP` ➔ **BUY** (N=33, OOS P=30.8%, Exp=-0.096)

---

## 3. ETHUSD — Top Discovered Conditions & 20-Field Trading Condition Library

| Rank | Condition Name | Type | TFs | Dir | OOS P(Dir) / Lift | OOS WR (Wilson LB) | OOS Exp (USD) | OOS PF | MFE / MAE | Horizon | Freq/Day | N (IS/OOS) | SL/TP (ATR) | WF Folds | Jitter ±15% | Status / Reliability |
| :---: | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| #1 | `SES[NY]: VA_REJECT_VAH` | Session-Micro | `M1` | **SELL** | 66.7% (+34.8%) | 66.7% (35.4%) | +0.0628 | 2.66 | 1.27 / 0.75 | `+5b` | 1.8/d | 23 (11/12) | 2.0 / 3.0 | 3/3 | PASS | `VALIDATED_OOS` (`MEDIUM`) |
| #2 | `SES[NY]: SEQ: SPREAD_SNAPBACK -> DELTA_DIVERGENCE_BEAR` | Session-Micro | `M1` | **SELL** | 54.5% (+2.2%) | 44.4% (18.9%) | +0.0520 | 2.34 | 3.70 / 1.48 | `+60b` | 2.9/d | 36 (25/11) | 2.0 / 3.0 | 3/3 | PASS | `VALIDATED_OOS` (`MEDIUM`) |
| #3 | `SES[NY]: MTF: H1_TREND_BEAR -> M1_DELTA_DIVERGENCE_BEAR` | Session-Micro | `H1+M1` | **SELL** | 42.9% (+11.6%) | 60.0% (31.3%) | +0.0388 | 1.88 | 1.02 / 0.74 | `+5b` | 2.7/d | 34 (20/14) | 2.0 / 3.0 | 1/3 | PASS | `VALIDATED_OOS` (`MEDIUM`) |
| #4 | `SES[NY]: SEQ: DOM_FLIP_BEAR -> LADDER_THIN_BID` | Session-Micro | `M1` | **SELL** | 63.2% (+17.7%) | 50.0% (28.0%) | +0.0151 | 1.23 | 2.82 / 1.69 | `+30b` | 3.0/d | 37 (18/19) | 2.0 / 3.0 | 2/3 | FRAGILE | `VALIDATED_OOS` (`MEDIUM`) |
| #5 | `SES[NY]: MTF: M15_SWEEP_HIGH -> M1_DELTA_DIVERGENCE_BEAR` | Session-Micro | `M15+M1` | **SELL** | 68.4% (+17.8%) | 43.8% (23.1%) | +0.0094 | 1.16 | 4.35 / 1.63 | `+60b` | 3.8/d | 48 (29/19) | 2.0 / 3.0 | 2/3 | FRAGILE | `VALIDATED_OOS` (`MEDIUM`) |
| #6 | `SES[NY]: SEQ: SPREAD_SNAPBACK -> DOM_IMBALANCE_BEAR` | Session-Micro | `M1` | **SELL** | 27.3% (-13.7%) | 44.4% (18.9%) | +0.0220 | 1.41 | 1.89 / 1.33 | `+15b` | 4.1/d | 52 (41/11) | 2.0 / 3.0 | 2/3 | FRAGILE | `VALIDATED_OOS` (`MEDIUM`) |
| #7 | `RSI_OVERBOUGHT` | Single | `M1` | **SELL** | 64.7% (+16.1%) | 56.7% (39.2%) | +0.0176 | 1.49 | 3.06 / 1.93 | `+60b` | 5.7/d | 72 (38/34) | 2.0 / 3.0 | 2/3 | PASS | `REGIME_SPECIFIC_EDGE` (`MEDIUM`) |
| #8 | `MTF: M15_PULLBACK_BEAR -> M1_RSI_OVERBOUGHT` | Multi-TF | `M15+M1` | **SELL** | 85.7% (+40.6%) | 57.1% (25.1%) | +0.0066 | 1.24 | 2.26 / 1.30 | `+30b` | 1.2/d | 15 (8/7) | 1.2 / 2.0 | 2/3 | FRAGILE | `RARE_HIGH_EDGE` (`RARE_PRELIMINARY`) |
| #9 | `SES[NY]: DOM_IMBALANCE_BEAR` | Session-Micro | `M1` | **SELL** | 45.1% (+13.7%) | 44.7% (30.1%) | +0.0118 | 1.22 | 1.08 / 0.88 | `+5b` | 10.6/d | 133 (82/51) | 2.0 / 3.0 | 2/3 | PASS | `REGIME_SPECIFIC_EDGE` (`MEDIUM`) |
| #10 | `SEQ: FLOW_SWEEP_HIGH -> DELTA_DIVERGENCE_BEAR` | Sequential | `M1` | **SELL** | 56.2% (+16.1%) | 56.2% (33.2%) | +0.0117 | 1.29 | 1.59 / 1.31 | `+15b` | 2.1/d | 27 (11/16) | 2.0 / 3.0 | 1/3 | FRAGILE | `REGIME_SPECIFIC_EDGE` (`MEDIUM`) |
| #11 | `SES[LONDON]: VA_REJECT_VAH` | Session-Micro | `M1` | **SELL** | 83.3% (+33.4%) | 80.0% (37.5%) | +0.0292 | 4.02 | 2.93 / 1.67 | `+60b` | 1.8/d | 23 (17/6) | 2.0 / 3.0 | 1/3 | PASS | `NO_EDGE` (`LOW`) |
| #12 | `MTF: H1_TREND_BEAR -> M1_RSI_OVERBOUGHT` | Multi-TF | `H1+M1` | **SELL** | 55.0% (+11.7%) | 55.0% (34.2%) | -0.0008 | 0.98 | 1.94 / 1.86 | `+30b` | 2.5/d | 32 (12/20) | 2.0 / 3.0 | 2/3 | PASS | `REGIME_SPECIFIC_EDGE` (`MEDIUM`) |
| #13 | `SES[NY]: FLOW_SWEEP_HIGH` | Session-Micro | `M1` | **SELL** | 83.3% (+28.9%) | 50.0% (18.8%) | +0.0129 | 1.22 | 4.72 / 1.35 | `+60b` | 1.4/d | 17 (11/6) | 2.0 / 3.0 | 2/3 | PASS | `RARE_HIGH_EDGE` (`RARE_PRELIMINARY`) |
| #14 | `MTF: H1_RANGE -> M1_RSI_OVERSOLD` | Multi-TF | `H1+M1` | **BUY** | 44.8% (+14.6%) | 51.7% (34.4%) | +0.0018 | 1.05 | 1.51 / 0.81 | `+5b` | 3.8/d | 47 (18/29) | 1.5 / 2.0 | 1/3 | FRAGILE | `REGIME_SPECIFIC_EDGE` (`MEDIUM`) |
| #15 | `SES[NY]: DELTA_DIVERGENCE_BEAR` | Session-Micro | `M1` | **SELL** | 56.4% (+6.1%) | 41.4% (25.5%) | +0.0015 | 1.03 | 3.84 / 1.77 | `+60b` | 7.2/d | 91 (52/39) | 2.0 / 3.0 | 2/3 | FRAGILE | `REGIME_SPECIFIC_EDGE` (`MEDIUM`) |
| #16 | `MTF: M15_SWEEP_HIGH -> M1_DELTA_DIVERGENCE_BEAR` | Multi-TF | `M15+M1` | **SELL** | 59.3% (+12.8%) | 48.0% (34.8%) | -0.0019 | 0.96 | 3.49 / 2.00 | `+60b` | 10.0/d | 126 (70/56) | 2.0 / 3.0 | 1/3 | PASS | `REGIME_SPECIFIC_EDGE` (`MEDIUM`) |
| #17 | `VA_REJECT_VAH` | Single | `M1` | **SELL** | 52.4% (+6.4%) | 46.2% (31.6%) | +0.0002 | 1.00 | 2.91 / 2.32 | `+60b` | 15.5/d | 194 (131/63) | 2.0 / 3.0 | 1/3 | FRAGILE | `REGIME_SPECIFIC_EDGE` (`MEDIUM`) |
| #18 | `SES[NY]: DOM_ABSORPTION_SELL` | Session-Micro | `M1` | **SELL** | 61.3% (+17.2%) | 34.6% (19.4%) | -0.0081 | 0.87 | 2.12 / 1.95 | `+30b` | 6.5/d | 81 (50/31) | 2.0 / 3.0 | 0/3 | PASS | `REGIME_SPECIFIC_EDGE` (`MEDIUM`) |
| #19 | `MTF: H1_RANGE -> M1_RSI_OVERBOUGHT` | Multi-TF | `H1+M1` | **SELL** | 70.0% (+38.8%) | 68.4% (46.0%) | +0.0330 | 2.53 | 1.19 / 0.70 | `+5b` | 3.2/d | 40 (20/20) | 1.2 / 2.0 | 2/3 | PASS | `NO_EDGE` (`LOW`) |
| #20 | `SES[NY]: LADDER_THIN_BID` | Session-Micro | `M1` | **SELL** | 26.7% (-4.9%) | 40.9% (27.7%) | -0.0028 | 0.96 | 1.01 / 0.97 | `+5b` | 14.8/d | 186 (111/75) | 2.0 / 3.0 | 2/3 | PASS | `REGIME_SPECIFIC_EDGE` (`MEDIUM`) |

### ETHUSD — Structured Event Sequences (`HTF Context → MTF Setup → LTF Trigger → Entry → Outcome`)

- **#1 `SES[NY]: VA_REJECT_VAH`** (VALIDATED_OOS): `[NY] M1 Trigger [VA_REJECT_VAH] -> Next-Bar Open Entry -> Expected Outcome` · SELL over next 5 M1 bars (~5m): OOS P(SELL)=66.7% (vs baseline 31.9%, lift +34.8%), avg move -0.648 ATR, MFE before MAE 69.6%
- **#2 `SES[NY]: SEQ: SPREAD_SNAPBACK -> DELTA_DIVERGENCE_BEAR`** (VALIDATED_OOS): `[NY] M1 OrderBook Sequence [SPREAD_SNAPBACK -> DELTA_DIVERGENCE_BEAR] -> Next-Bar Open Entry -> Expected Outcome` · SELL over next 60 M1 bars (~60m): OOS P(SELL)=54.5% (vs baseline 52.4%, lift +2.2%), avg move -1.521 ATR, MFE before MAE 69.4%
- **#3 `SES[NY]: MTF: H1_TREND_BEAR -> M1_DELTA_DIVERGENCE_BEAR`** (VALIDATED_OOS): `[NY] H1_TREND_BEAR -> M1 [DELTA_DIVERGENCE_BEAR] -> Next-Bar Open Entry -> Expected Outcome` · SELL over next 5 M1 bars (~5m): OOS P(SELL)=42.9% (vs baseline 31.3%, lift +11.6%), avg move -0.146 ATR, MFE before MAE 61.8%
- **#4 `SES[NY]: SEQ: DOM_FLIP_BEAR -> LADDER_THIN_BID`** (VALIDATED_OOS): `[NY] M1 OrderBook Sequence [DOM_FLIP_BEAR -> LADDER_THIN_BID] -> Next-Bar Open Entry -> Expected Outcome` · SELL over next 30 M1 bars (~30m): OOS P(SELL)=63.2% (vs baseline 45.4%, lift +17.7%), avg move -1.669 ATR, MFE before MAE 56.8%
- **#5 `SES[NY]: MTF: M15_SWEEP_HIGH -> M1_DELTA_DIVERGENCE_BEAR`** (VALIDATED_OOS): `[NY] M15_SWEEP_HIGH -> M1 [DELTA_DIVERGENCE_BEAR] -> Next-Bar Open Entry -> Expected Outcome` · SELL over next 60 M1 bars (~60m): OOS P(SELL)=68.4% (vs baseline 50.6%, lift +17.8%), avg move -3.498 ATR, MFE before MAE 66.7%
- **#6 `SES[NY]: SEQ: SPREAD_SNAPBACK -> DOM_IMBALANCE_BEAR`** (VALIDATED_OOS): `[NY] M1 OrderBook Sequence [SPREAD_SNAPBACK -> DOM_IMBALANCE_BEAR] -> Next-Bar Open Entry -> Expected Outcome` · SELL over next 15 M1 bars (~15m): OOS P(SELL)=27.3% (vs baseline 41.0%, lift -13.7%), avg move -0.017 ATR, MFE before MAE 53.8%
- **#7 `RSI_OVERBOUGHT`** (REGIME_SPECIFIC_EDGE): `M1 Trigger [RSI_OVERBOUGHT] -> Next-Bar Open Entry -> Expected Outcome` · SELL over next 60 M1 bars (~60m): OOS P(SELL)=64.7% (vs baseline 48.6%, lift +16.1%), avg move -1.341 ATR, MFE before MAE 65.3%
- **#8 `MTF: M15_PULLBACK_BEAR -> M1_RSI_OVERBOUGHT`** (RARE_HIGH_EDGE): `M15_PULLBACK_BEAR -> M1 [RSI_OVERBOUGHT] -> Next-Bar Open Entry -> Expected Outcome` · SELL over next 30 M1 bars (~30m): OOS P(SELL)=85.7% (vs baseline 45.1%, lift +40.6%), avg move -1.245 ATR, MFE before MAE 73.3%

### ETHUSD — Branching Patterns (Same Prefix Diverging by Next Step)

- Prefix `COMPRESSION`: `BREAKOUT_DOWN` ➔ **SELL** (N=10, OOS P=50.0%, Exp=+0.013) ; `DISPLACEMENT_BEAR` ➔ **SELL** (N=13, OOS P=0.0%, Exp=-0.008) ; `BREAKOUT_UP` ➔ **BUY** (N=12, OOS P=0.0%, Exp=-0.055) ; `BOS_BULL` ➔ **BUY** (N=14, OOS P=33.3%, Exp=-0.069)
- Prefix `BREAKOUT_DOWN`: `DOM_STACK_BEAR` ➔ **SELL** (N=14, OOS P=40.0%, Exp=-0.018) ; `DISPLACEMENT_BEAR` ➔ **SELL** (N=46, OOS P=40.0%, Exp=-0.033) ; `FALSE_BREAKOUT_DOWN` ➔ **BUY** (N=257, OOS P=50.0%, Exp=-0.036)
- Prefix `BREAKOUT_UP`: `BOS_BULL` ➔ **BUY** (N=40, OOS P=46.7%, Exp=-0.021) ; `FALSE_BREAKOUT_UP` ➔ **SELL** (N=231, OOS P=44.8%, Exp=-0.028)

---

## 4. Round 2 Deep Dive — Order Book Imbalance, Liquidity Ladder & Microstructure Sequences (`XAUUSD` & `BTCUSD`)

### XAUUSD — Top Order Book Imbalance & Microstructure Patterns (Round 2)

| Rank | Condition Name | Type | Dir | OOS P(Dir) / Lift | OOS WR | OOS Exp (USD) | OOS PF | N (IS/OOS) | Ablation ΔP / ΔExp | WF Folds | Jitter ±15% | Status |
| :---: | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| #4 | `SEQ: DOM_STACK_BEAR -> LADDER_THIN_BID` | Sequential | **SELL** | 60.0% (+16.3%) | 68.4% | +4.2011 | 2.75 | 49 (29/20) | `-2.5%` / `+3.246` | 3/3 | PASS | `VALIDATED_OOS` |
| #6 | `SEQ: VA_REJECT_VAL -> BOS_BULL` | Sequential | **BUY** | 61.5% (+20.8%) | 61.5% | +1.6291 | 2.34 | 30 (16/14) | `+23.6%` / `+3.174` | 2/3 | PASS | `VALIDATED_OOS` |
| #9 | `SEQ: DEPTH_ICEBERG_BATTLE -> CVD_SURGE_BEAR` | Sequential | **SELL** | 62.0% (+26.2%) | 54.4% | +1.3347 | 1.59 | 105 (55/50) | `+25.6%` / `+1.750` | 2/3 | PASS | `VALIDATED_OOS` |
| #19 | `SEQ: LIQUIDITY_PULL_SHOCK -> SPREAD_SNAPBACK -> RECLAIM_HIGH` | Sequential | **SELL** | 42.9% (+7.2%) | 57.1% | +1.5724 | 1.71 | 77 (56/21) | `+6.2%` / `+2.672` | 2/3 | PASS | `VALIDATED_OOS` |
| #25 | `SEQ: FLOW_SWEEP_HIGH -> SWEEP_HIGH` | Sequential | **SELL** | 47.1% (+2.3%) | 52.9% | +1.3386 | 2.05 | 50 (33/17) | `-11.8%` / `-1.389` | 2/3 | PASS | `VALIDATED_OOS` |
| #27 | `SEQ: DEPTH_ICEBERG_BATTLE -> DOM_IMBALANCE_BULL -> DISPLACEMENT_BULL` | Sequential | **BUY** | 66.7% (+22.5%) | 66.7% | +3.0162 | 5.17 | 13 (7/6) | `+31.7%` / `+2.304` | 3/3 | PASS | `RARE_HIGH_EDGE` |
| #28 | `SEQ: DOM_FLIP_BULL -> BOS_BULL` | Sequential | **BUY** | 44.0% (+5.9%) | 52.4% | +1.2277 | 1.44 | 70 (45/25) | `+11.8%` / `+3.224` | 2/3 | FRAGILE | `VALIDATED_OOS` |
| #32 | `MTF: H1_TREND_BEAR -> M15_PULLBACK_BEAR -> M1_DOM_FLIP_BEAR` | Multi-TF | **SELL** | 42.1% (+5.1%) | 46.7% | +1.8767 | 1.72 | 22 (3/19) | - | 1/3 | PASS | `VALIDATED_OOS` |
| #36 | `SEQ: DEPTH_ICEBERG_BATTLE -> BOS_BULL` | Sequential | **BUY** | 50.0% (+8.9%) | 45.5% | +1.3954 | 1.44 | 32 (20/12) | `+13.6%` / `+1.810` | 3/3 | - | `VALIDATED_OOS` |
| #40 | `SEQ: DEPTH_ICEBERG_BATTLE -> SWEEP_HIGH` | Sequential | **SELL** | 46.4% (+11.1%) | 50.8% | +0.7069 | 1.25 | 154 (85/69) | `+10.0%` / `+1.122` | 1/3 | - | `VALIDATED_OOS` |
| #41 | `SEQ: VA_REJECT_VAH -> DOM_IMBALANCE_BEAR` | Sequential | **SELL** | 66.7% (+30.0%) | 66.7% | +2.0837 | 2.58 | 29 (20/9) | `+9.5%` / `+1.827` | 1/3 | - | `REGIME_SPECIFIC_EDGE` |
| #43 | `SEQ: FLOW_SWEEP_LOW -> RECLAIM_LOW+DOM_IMBALANCE_BULL` | Sequential | **BUY** | 75.0% (+33.1%) | 62.5% | +4.8878 | 6.28 | 11 (3/8) | `+28.8%` / `+6.698` | 0/0 | - | `RARE_HIGH_EDGE` |
| #61 | `MTF: M15_SWEEP_HIGH -> M1_VA_REJECT_VAH` | Multi-TF | **SELL** | 52.9% (+15.8%) | 64.7% | +0.7192 | 1.59 | 52 (35/17) | - | 1/3 | - | `VALIDATED_OOS` |
| #68 | `SEQ: SWEEP_LOW -> DOM_FLIP_BULL -> DISPLACEMENT_BULL` | Sequential | **BUY** | 50.0% (+18.0%) | 48.0% | +0.5606 | 1.20 | 75 (49/26) | `+16.0%` / `+1.505` | 1/3 | - | `VALIDATED_OOS` |
| #83 | `SEQ: DOM_STACK_BEAR -> BREAKOUT_DOWN` | Sequential | **SELL** | 35.7% (-0.2%) | 53.8% | +1.9264 | 1.94 | 25 (11/14) | `-26.8%` / `+0.972` | 1/3 | - | `REGIME_SPECIFIC_EDGE` |

**XAUUSD Order Book Branching Divergences:**

- Prefix `DOM_FLIP_BULL`: `BOS_BULL` ➔ **BUY** (N=70, Exp=+1.228) ; `SPREAD_EXPANSION` ➔ **BUY** (N=86, Exp=-0.170) ; `DEPTH_ICEBERG_BATTLE` ➔ **BUY** (N=98, Exp=-0.204) ; `LADDER_THIN_ASK` ➔ **BUY** (N=238, Exp=-0.344)
- Prefix `DEPTH_ICEBERG_BATTLE`: `BOS_BULL` ➔ **BUY** (N=32, Exp=+1.395) ; `CVD_SURGE_BEAR` ➔ **SELL** (N=105, Exp=+1.335) ; `DOM_IMBALANCE_BULL` ➔ **BUY** (N=82, Exp=+0.712) ; `SWEEP_HIGH` ➔ **SELL** (N=154, Exp=+0.707)
- Prefix `SPREAD_EXPANSION`: `FLOW_SWEEP_LOW` ➔ **BUY** (N=9, Exp=+11.597) ; `VA_REJECT_VAL` ➔ **BUY** (N=33, Exp=+0.497) ; `SWEEP_HIGH` ➔ **SELL** (N=148, Exp=+0.389) ; `BOS_BULL` ➔ **BUY** (N=30, Exp=+0.120)

### BTCUSD — Top Order Book Imbalance & Microstructure Patterns (Round 2)

| Rank | Condition Name | Type | Dir | OOS P(Dir) / Lift | OOS WR | OOS Exp (USD) | OOS PF | N (IS/OOS) | Ablation ΔP / ΔExp | WF Folds | Jitter ±15% | Status |
| :---: | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| #1 | `SEQ: VA_REJECT_VAH -> DELTA_DIVERGENCE_BEAR` | Sequential | **SELL** | 76.5% (+42.7%) | 64.7% | +1.2308 | 4.34 | 62 (45/17) | `+2.6%` / `+0.871` | 3/3 | PASS | `VALIDATED_OOS` |
| #2 | `MTF: M15_SWEEP_HIGH -> M1_VA_REJECT_VAH` | Multi-TF | **SELL** | 78.4% (+25.2%) | 68.0% | +1.1518 | 3.49 | 103 (66/37) | - | 3/3 | PASS | `VALIDATED_OOS` |
| #6 | `SEQ: DOM_FLIP_BEAR -> DELTA_DIVERGENCE_BEAR` | Sequential | **SELL** | 78.6% (+30.2%) | 76.9% | +1.9931 | 4.79 | 33 (19/14) | `+20.5%` / `+1.786` | 2/3 | PASS | `REGIME_SPECIFIC_EDGE` |
| #11 | `SEQ: FLOW_SWEEP_HIGH -> RETEST_RESIST_2X -> DOM_IMBALANCE_BEAR` | Sequential | **SELL** | 100.0% (+43.2%) | 66.7% | +0.7828 | 2.39 | 22 (13/9) | `+62.9%` / `+0.537` | 3/3 | PASS | `VALIDATED_OOS` |
| #16 | `SEQ: DELTA_DIVERGENCE_BEAR -> DOM_ABSORPTION_SELL` | Sequential | **SELL** | 65.0% (+18.1%) | 66.7% | +0.6148 | 2.84 | 51 (30/21) | `+22.5%` / `+0.248` | 3/3 | PASS | `VALIDATED_OOS` |
| #17 | `SEQ: VA_REJECT_VAH -> DOM_IMBALANCE_BEAR` | Sequential | **SELL** | 70.0% (+22.1%) | 80.0% | +1.4912 | 4.73 | 29 (19/10) | `-3.9%` / `+1.131` | 2/3 | PASS | `REGIME_SPECIFIC_EDGE` |
| #19 | `SEQ: FLOW_SWEEP_HIGH -> RETEST_RESIST_2X -> SPREAD_SNAPBACK` | Sequential | **SELL** | 59.3% (+9.1%) | 63.0% | +0.7752 | 2.21 | 65 (37/28) | `+22.1%` / `+0.529` | 2/3 | PASS | `VALIDATED_OOS` |
| #24 | `SEQ: DOM_ABSORPTION_SELL -> DELTA_DIVERGENCE_BEAR -> SPREAD_SNAPBACK` | Sequential | **SELL** | 68.4% (+18.2%) | 60.0% | +0.5866 | 1.78 | 42 (22/20) | `+3.4%` / `+0.318` | 3/3 | PASS | `VALIDATED_OOS` |
| #29 | `SEQ: FLOW_SWEEP_HIGH -> RETEST_RESIST_2X -> DELTA_DIVERGENCE_BEAR` | Sequential | **SELL** | 62.5% (+12.9%) | 52.9% | +0.6239 | 1.90 | 30 (13/17) | `+25.4%` / `+0.378` | 3/3 | PASS | `VALIDATED_OOS` |
| #32 | `SEQ: DOM_FLIP_BEAR -> SPREAD_SNAPBACK` | Sequential | **SELL** | 55.6% (+6.2%) | 53.8% | +0.6456 | 1.84 | 70 (43/27) | `-2.5%` / `+0.439` | 2/3 | PASS | `VALIDATED_OOS` |
| #36 | `SEQ: DELTA_DIVERGENCE_BEAR -> FLOW_SWEEP_HIGH -> DELTA_DIVERGENCE_BEAR` | Sequential | **SELL** | 100.0% (+40.6%) | 80.0% | +1.7077 | 83.25 | 11 (6/5) | `+37.5%` / `+1.406` | 0/0 | - | `RARE_HIGH_EDGE` |
| #37 | `SEQ: SPREAD_SNAPBACK -> EXHAUSTION_TOP` | Sequential | **SELL** | 80.0% (+32.2%) | 50.0% | +0.4646 | 1.65 | 52 (42/10) | `+35.3%` / `+0.633` | 2/3 | - | `VALIDATED_OOS` |
| #38 | `SEQ: DOM_IMBALANCE_BEAR -> DELTA_DIVERGENCE_BEAR` | Sequential | **SELL** | 41.3% (+7.5%) | 50.0% | +0.4789 | 1.51 | 114 (68/46) | `-10.4%` / `+0.596` | 2/3 | - | `VALIDATED_OOS` |
| #39 | `SEQ: DOM_IMBALANCE_BEAR -> CVD_SURGE_BEAR -> DELTA_DIVERGENCE_BEAR` | Sequential | **SELL** | 47.1% (+13.3%) | 52.9% | +0.4122 | 1.92 | 44 (27/17) | `+9.3%` / `+0.939` | 3/3 | - | `VALIDATED_OOS` |
| #40 | `SEQ: SPREAD_SNAPBACK -> DELTA_DIVERGENCE_BEAR` | Sequential | **SELL** | 45.3% (+11.8%) | 49.5% | +0.3612 | 1.40 | 320 (192/128) | `+0.6%` / `+0.529` | 2/3 | - | `VALIDATED_OOS` |

**BTCUSD Order Book Branching Divergences:**

- Prefix `DOM_STACK_BEAR`: `SPREAD_SNAPBACK` ➔ **SELL** (N=17, Exp=+0.070) ; `RETEST_RESIST_2X` ➔ **SELL** (N=16, Exp=+0.046) ; `CVD_SURGE_BEAR` ➔ **SELL** (N=10, Exp=-0.244) ; `DELTA_DIVERGENCE_BEAR` ➔ **SELL** (N=11, Exp=-0.594)
- Prefix `DOM_FLIP_BEAR`: `DELTA_DIVERGENCE_BEAR` ➔ **SELL** (N=33, Exp=+1.993) ; `DOM_IMBALANCE_BEAR` ➔ **SELL** (N=29, Exp=+0.954) ; `SPREAD_SNAPBACK` ➔ **SELL** (N=70, Exp=+0.646) ; `DOM_ABSORPTION_SELL` ➔ **SELL** (N=11, Exp=+0.544)
- Prefix `DOM_IMBALANCE_BEAR`: `DELTA_DIVERGENCE_BEAR` ➔ **SELL** (N=114, Exp=+0.479) ; `SPREAD_SNAPBACK` ➔ **SELL** (N=288, Exp=+0.241) ; `RETEST_RESIST_2X` ➔ **SELL** (N=258, Exp=+0.185) ; `FLOW_SWEEP_HIGH` ➔ **SELL** (N=18, Exp=+0.085)

---

## 5. 7-Zone Session-Specific Scalping Playbooks (`XAUUSD` & `BTCUSD`)

### XAUUSD — Winning Pattern & Session Lift per Session Zone

| Session Zone | Winning Condition | Type | Dir | N (IS/OOS) | Session OOS WR | Session OOS Exp (USD) | Session OOS PF | All-Day Exp (USD) | Session Lift | SL/TP (ATR) | Status |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **`ASIA`** | `SES[ASIA]: MTF: DEV_H1_REJECTION_BULL -> M1_DOM_ABSORPTION_BUY` | Session-Micro | **BUY** | 23 (13/10) | 66.7% | +3.0218 | 1.89 | +0.9437 | **`+2.0781`** | 2.0 / 3.0 | `VALIDATED_OOS` |
| **`ASIA_TO_LONDON`** | `SES[ASIA_TO_LONDON]: DOM_FLIP_BULL` | Session-Micro | **BUY** | 27 (16/11) | 40.0% | -0.7232 | 0.74 | -1.9963 | **`+1.2731`** | 1.5 / 2.0 | `IS_ONLY_OVERFIT` |
| **`LONDON`** | `SES[LONDON]: SPREAD_EXPANSION` | Session-Micro | **BUY** | 37 (27/10) | 71.4% | +2.8763 | 4.57 | -0.8593 | **`+3.7356`** | 1.2 / 2.0 | `VALIDATED_OOS` |
| **`LONDON_TO_NY`** | `SES[LONDON_TO_NY]: DOM_FLIP_BULL` | Session-Micro | **BUY** | 30 (15/15) | 50.0% | +0.5551 | 1.24 | -1.9963 | **`+2.5514`** | 1.5 / 2.5 | `REGIME_SPECIFIC_EDGE` |
| **`NY`** | `SES[NY]: SPREAD_SNAPBACK` | Session-Micro | **SELL** | 136 (81/55) | 61.9% | +2.6885 | 2.10 | +0.3829 | **`+2.3056`** | 2.0 / 3.0 | `VALIDATED_OOS` |
| **`NY_TO_CLOSE`** | `SES[NY_TO_CLOSE]: DOM_FLIP_BULL` | Session-Micro | **BUY** | 33 (19/14) | 44.4% | +0.1013 | 1.06 | -1.9963 | **`+2.0976`** | 2.0 / 3.0 | `VALIDATED_OOS` |

### BTCUSD — Winning Pattern & Session Lift per Session Zone

| Session Zone | Winning Condition | Type | Dir | N (IS/OOS) | Session OOS WR | Session OOS Exp (USD) | Session OOS PF | All-Day Exp (USD) | Session Lift | SL/TP (ATR) | Status |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **`ASIA`** | `SES[ASIA]: MTF: M15_SWEEP_HIGH -> M1_DELTA_DIVERGENCE_BEAR` | Session-Micro | **SELL** | 71 (47/24) | 61.1% | +0.9869 | 2.82 | +0.6625 | **`+0.3244`** | 2.0 / 3.0 | `VALIDATED_OOS` |
| **`LONDON`** | `SES[LONDON]: MTF: M15_SWEEP_HIGH -> M1_DELTA_DIVERGENCE_BEAR` | Session-Micro | **SELL** | 36 (21/15) | 50.0% | +0.3765 | 1.65 | +0.6625 | **`-0.2860`** | 1.5 / 2.5 | `VALIDATED_OOS` |
| **`LONDON_TO_NY`** | `SES[LONDON_TO_NY]: CVD_SURGE_BEAR` | Session-Micro | **SELL** | 26 (16/10) | 42.9% | +0.2594 | 1.27 | -0.1389 | **`+0.3983`** | 2.0 / 3.0 | `VALIDATED_OOS` |
| **`NY`** | `SES[NY]: SPREAD_SNAPBACK` | Session-Micro | **SELL** | 347 (213/134) | 45.3% | +0.4825 | 1.42 | -0.1681 | **`+0.6506`** | 2.0 / 3.0 | `VALIDATED_OOS` |
| **`OVERNIGHT`** | `SES[OVERNIGHT]: POC_RECLAIM_BULL` | Session-Micro | **BUY** | 31 (14/17) | 45.5% | +0.1298 | 1.18 | -0.4816 | **`+0.6114`** | 1.5 / 2.5 | `VALIDATED_OOS` |

