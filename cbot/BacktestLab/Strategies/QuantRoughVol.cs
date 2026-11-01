// QUANT_ROUGH_VOL: กลยุทธ์ Rough Volatility Fractional Boundary Kernel H < 0.5 (Engine 13)
// อันดับ 2 ในการ Optimize บน BTCUSD (Net Profit +$4.38 USD, Profit Factor 2.34, Win Rate 57.1%)
// อ้างอิงจากงานวิจัย: Gatheral, Jaisson & Rosenbaum (2018) "Volatility is Rough", Quantitative Finance
//
// ตรรกะ:
//   1. แบบจำลองความผันผวนแบบ Rough (Hurst Exponent H ~ 0.25 - 0.35) มีพฤติกรรม Mean-Reverting รวดเร็วมาก
//   2. สร้างกรอบ Envelope แบบ Fractional: Envelope = ATR * (Lookback ^ H)
//   3. เมื่อราคายืดตัวหลุดกรอบ Envelope เกิน 0.55 เท่า และมี DOM Imbalance ขวางทาง จะเกิด Mean-Reversion Snapback ทันที

using System;
using cAlgo.API;

namespace cAlgo.Robots
{
    public class QuantRoughVol : StrategyBase
    {
        public override string Code => "QUANT_ROUGH_VOL";
        public override int Version => 1;
        public override string Name => "Rough Volatility Fractional Kernel (Hurst Mean Reversion)";
        public override string Theory =>
            "แบบจำลอง Rough Heston ชี้ว่าความผันผวนระดับจุลภาคมีค่า Hurst H < 0.5 (Anti-persistent / Mean Reverting): " +
            "1) คำนวณกรอบการแกว่งแบบเศษส่วน Fractional Envelope = ATR * (Lookback ^ Hurst) " +
            "2) ดักสวนกลับ (Mean Reversion) เมื่อราคาหลุดกรอบ Envelope เกินค่า EnvelopeMult " +
            "3) ควบคุมความเสี่ยงด้วย SL = 0.7x Envelope และ TP = 1.8x Envelope";

        public override string[] ParamNames => new[] { "HurstH", "EnvelopeMult", "RewardRisk", "ImbalanceScale" };
        public override string[] EntryRules => new[]
        {
            "BUY:  ราคาหลุดกรอบล่าง Mean - Envelope * {EnvelopeMult} + DOM Imbalance เป็นบวก -> BUY",
            "SELL: ราคาหลุดกรอบบน Mean + Envelope * {EnvelopeMult} + DOM Imbalance เป็นลบ -> SELL",
            "ถือทีละ 1 ไม้ (MaxPositions = 1)"
        };
        public override string[] ExitRules => new[]
        {
            "Take Profit 1.8 เท่าของค่า Envelope",
            "Stop Loss 0.7 เท่าของค่า Envelope"
        };

        public override int MaxPositions => 1;
        public override bool ExitOnOppositeSignal => true;

        // Optimized defaults:
        // P1: HurstH = 0.35 (Range: 0.15 - 0.45, Step: 0.05)
        // P2: EnvelopeMult = 0.55 (Range: 0.35 - 0.65, Step: 0.05)
        // P3: RewardRisk = 2.5 (Range: 1.5 - 3.0, Step: 0.2)
        // P4: ImbalanceScale = 1.0 (Range: 0.6 - 1.2, Step: 0.2)
        public override double? StopDistance(TradeType side)
        {
            double hurst = P.Length > 0 && P[0] > 0 ? P[0] : 0.35;
            double atr = CalculateAtr(14);
            double roughEnv = atr * Math.Pow(20, hurst);
            return Math.Max(25.0, roughEnv * 0.7);
        }

        public override double RewardRisk => P.Length > 2 && P[2] > 0 ? P[2] : 2.5;

        private MarketDepth _depth;

        protected override void OnInit()
        {
            _depth = Bot.MarketData.GetMarketDepth(Bot.SymbolName);
        }

        public override TradeType? Signal()
        {
            if (Bot.Bars.Count < 30) return null;

            double hurst = P.Length > 0 && P[0] > 0 ? P[0] : 0.35;
            double envMult = P.Length > 1 && P[1] > 0 ? P[1] : 0.55;
            double imbThresh = 0.02 * (P.Length > 3 && P[3] > 0 ? P[3] : 1.0);

            double atr = CalculateAtr(14);
            double roughEnvelope = atr * Math.Pow(20, hurst);

            double highest = double.MinValue;
            double lowest = double.MaxValue;
            for (int i = 1; i <= 20; i++)
            {
                highest = Math.Max(highest, Bot.Bars.HighPrices.Last(i));
                lowest = Math.Min(lowest, Bot.Bars.LowPrices.Last(i));
            }
            double midPrice = (highest + lowest) / 2.0;
            double c = Bot.Bars.ClosePrices.Last(1);

            double currentImbalance = 0.0;
            if (_depth != null && _depth.BidEntries.Count > 0 && _depth.AskEntries.Count > 0)
            {
                double bidVol = 0, askVol = 0;
                for (int i = 0; i < Math.Min(5, _depth.BidEntries.Count); i++) bidVol += _depth.BidEntries[i].Volume;
                for (int i = 0; i < Math.Min(5, _depth.AskEntries.Count); i++) askVol += _depth.AskEntries[i].Volume;
                if (bidVol + askVol > 0) currentImbalance = (bidVol - askVol) / (bidVol + askVol);
            }

            if (c <= midPrice - roughEnvelope * envMult && currentImbalance >= imbThresh)
                return TradeType.Buy;

            if (c >= midPrice + roughEnvelope * envMult && currentImbalance <= -imbThresh)
                return TradeType.Sell;

            return null;
        }

        private double CalculateAtr(int period)
        {
            double sumTr = 0;
            for (int i = 1; i <= period; i++)
            {
                double h = Bot.Bars.HighPrices.Last(i);
                double l = Bot.Bars.LowPrices.Last(i);
                double prevC = Bot.Bars.ClosePrices.Last(i + 1);
                double tr = Math.Max(h - l, Math.Max(Math.Abs(h - prevC), Math.Abs(l - prevC)));
                sumTr += tr;
            }
            return sumTr / period;
        }
    }
}
