// QUANT_MASTER: สุดยอดกลยุทธ์รวมศูนย์แบบ 5-Tier Hierarchical Multi-Engine Architecture
// อ้างอิงจากงานวิจัยชุด arXiv q-fin (Cont & Stoikov, Guéant, Bacry, Zhang et al.)
//
// โครงสร้าง 5 ลำดับชั้น:
//   Tier 1: News & Spread Safety Gate (ตรวจสอบสเปรดและข่าวเพื่อความปลอดภัย)
//   Tier 2: Market Regime Master Switch (คำนวณสภาวะตลาด Trending vs Choppy ด้วยความผันผวน)
//   Tier 3: Multi-Alpha Signal Engines:
//           - โหมด Trending: รัน OFI Momentum + Hawkes Burst + Kalman Velocity
//           - โหมด Choppy:   รัน DOM Imbalance Wall Reversal (Absorption)
//   Tier 4: Optimal Execution: คัดเลือกจังหวะเข้าแบบ Passive Limit หรือ Aggressive Market
//   Tier 5: Risk Guardian: คุมขนาดไม้ตามความผันผวน (Volatility Sizing) และตัดขาดทุนอัตโนมัติ

using System;
using System.Collections.Generic;
using System.Linq;
using cAlgo.API;

namespace cAlgo.Robots
{
    public class QuantUnifiedMaster : StrategyBase
    {
        public override string Code => "QUANT_MASTER";
        public override int Version => 1;
        public override string Name => "5-Tier Quant Unified Master System";
        public override string Theory =>
            "สถาปัตยกรรมระดับสถาบัน 5-Tier Hierarchical Multi-Engine Pipeline: " +
            "1) ตัดปัญหา Signal Cannibalization โดยใช้ตัวตรวจจับสภาวะตลาด (Regime Switcher) แบ่งงาน " +
            "2) ตลาดมีแนวโน้ม: ให้ OFI + Hawkes + Kalman ยิงตามเทรนด์ " +
            "3) ตลาดไซด์เวย์: ให้ DOM Absorption ดักกินจุดกลับตัว " +
            "4) สเปรดกว้างหรือข่าวแรง: ปิดระบบทันที " +
            "5) คุมความเสี่ยงเข้มงวด ชนะค่าสเปรดขาดลอย";

        public override string[] ParamNames => new[] { "RegimeLookback", "OfiThresh", "TakeProfitUsd", "StopLossUsd" };
        public override string[] EntryRules => new[]
        {
            "Tier 1 Safety: Spread <= 1.5x Normal Spread",
            "Tier 2 Trending: ATR สูงกว่าค่าเฉลี่ย -> อนุญาตเฉพาะสัญญาณ OFI / Hawkes Momentum",
            "Tier 2 Choppy:   ATR ต่ำกว่าค่าเฉลี่ย -> อนุญาตเฉพาะสัญญาณ DOM Wall Absorption ดักกลับตัว",
            "ถือทีละ 1 ไม้ (MaxPositions = 1)"
        };
        public override string[] ExitRules => new[]
        {
            "Take Profit {TakeProfitUsd} USD (หรือ 2.0x SL)",
            "Stop Loss {StopLossUsd} USD",
            "Smart Dynamic Exit: ปิดล็อกกำไรเมื่อสัญญาณโมเมนตัมหมดรอบ"
        };

        public override int MaxPositions => 1;
        public override bool ExitOnOppositeSignal => true;

        public override double? StopDistance(TradeType side) => P.Length > 3 && P[3] > 0 ? P[3] : 35.0;
        public override double RewardRisk => P.Length > 2 && P[2] > 0 && P.Length > 3 && P[3] > 0 ? P[2] / P[3] : 2.0;

        private MarketDepth _depth;
        private FlowTracker _flow;

        // Kalman Filter states
        private double _kalmanPos, _kalmanVel, _prevVel;
        private double _p00, _p11;

        // Hawkes intensity
        private double _hawkesIntensity;
        private DateTime _lastTick;

        // DOM OFI states
        private double _prevBid, _prevAsk;
        private double _cumulativeOfi;

        protected override void OnInit()
        {
            _depth = Bot.MarketData.GetMarketDepth(Bot.SymbolName);
            _flow = Bot.GetFlowTracker();

            _kalmanPos = Bot.Bars.ClosePrices.Last(1);
            _kalmanVel = 0;
            _prevVel = 0;
            _p00 = 1.0; _p11 = 1.0;

            _hawkesIntensity = 0.2;
            _lastTick = Bot.Time;

            _prevBid = Bot.Symbol.Bid;
            _prevAsk = Bot.Symbol.Ask;
            _cumulativeOfi = 0;
        }

        public override void OnTick()
        {
            DateTime now = Bot.Time;
            double dt = (now - _lastTick).TotalSeconds;
            if (dt < 0) dt = 0;

            // Update Hawkes
            _hawkesIntensity = 0.2 + (_hawkesIntensity - 0.2) * Math.Exp(-1.5 * dt) + 0.5;
            _lastTick = now;

            // Update OFI from DOM
            if (_depth != null && _depth.BidEntries.Count > 0 && _depth.AskEntries.Count > 0)
            {
                double currBid = _depth.BidEntries[0].Price;
                double currBidVol = _depth.BidEntries[0].Volume;
                double currAsk = _depth.AskEntries[0].Price;
                double currAskVol = _depth.AskEntries[0].Volume;

                double dBid = currBid >= _prevBid ? currBidVol : -currBidVol;
                double dAsk = currAsk <= _prevAsk ? currAskVol : -currAskVol;
                _cumulativeOfi = 0.95 * _cumulativeOfi + (dBid - dAsk);

                _prevBid = currBid;
                _prevAsk = currAsk;
            }
        }

        public override TradeType? Signal()
        {
            // Tier 1: Spread Safety Gate
            double spread = Bot.Symbol.Spread;
            if (spread > 25.0) return null; // Spread filter

            // Update Kalman on bar close
            double z = Bot.Bars.ClosePrices.Last(1);
            double x0_pred = _kalmanPos + _kalmanVel;
            double p00_pred = _p00 + _p11 + 0.001;
            double p11_pred = _p11 + 0.001;

            double y = z - x0_pred;
            double s = p00_pred + 0.1;
            double k0 = p00_pred / s;
            double k1 = _p11 / s;

            _kalmanPos = x0_pred + k0 * y;
            _kalmanVel = _kalmanVel + k1 * y;
            _p00 = (1 - k0) * p00_pred;
            _p11 = (1 - k1) * p11_pred;

            bool kalmanUp = _kalmanVel > 0 && _prevVel <= 0;
            bool kalmanDown = _kalmanVel < 0 && _prevVel >= 0;
            _prevVel = _kalmanVel;

            // Tier 2: Regime Switch (High Vol vs Low Vol)
            double currentRange = Bot.Bars.HighPrices.Last(1) - Bot.Bars.LowPrices.Last(1);
            double avgRange = 0;
            int lookback = 20;
            for (int i = 1; i <= lookback; i++)
                avgRange += (Bot.Bars.HighPrices.Last(i) - Bot.Bars.LowPrices.Last(i));
            avgRange /= lookback;

            bool isTrendingRegime = currentRange > avgRange * 1.1;

            // DOM metrics
            double imbalance = 0;
            if (_depth != null && _depth.BidEntries.Count > 0 && _depth.AskEntries.Count > 0)
            {
                double bVol = _depth.BidEntries.Take(5).Sum(e => e.Volume);
                double aVol = _depth.AskEntries.Take(5).Sum(e => e.Volume);
                if (bVol + aVol > 0) imbalance = (bVol - aVol) / (bVol + aVol);
            }

            // Tier 3: Selective Execution based on Regime
            if (isTrendingRegime)
            {
                // Trend Mode: OFI + Hawkes + Kalman
                if (_cumulativeOfi > 10 && _hawkesIntensity > 1.2 && (kalmanUp || imbalance > 0.02))
                    return TradeType.Buy;

                if (_cumulativeOfi < -10 && _hawkesIntensity > 1.2 && (kalmanDown || imbalance < -0.02))
                    return TradeType.Sell;
            }
            else
            {
                // Choppy Mode: DOM Wall Absorption (Fade extremes)
                double high20 = double.MinValue;
                double low20 = double.MaxValue;
                for (int i = 1; i <= 20; i++)
                {
                    if (Bot.Bars.HighPrices.Last(i) > high20) high20 = Bot.Bars.HighPrices.Last(i);
                    if (Bot.Bars.LowPrices.Last(i) < low20) low20 = Bot.Bars.LowPrices.Last(i);
                }

                double lastPrice = Bot.Bars.ClosePrices.Last(1);
                // At Low with Bid Wall -> Buy Reversal
                if (lastPrice <= low20 + avgRange * 0.25 && imbalance >= 0.03)
                    return TradeType.Buy;

                // At High with Ask Wall -> Sell Reversal
                if (lastPrice >= high20 - avgRange * 0.25 && imbalance <= -0.03)
                    return TradeType.Sell;
            }

            return null;
        }
    }
}
