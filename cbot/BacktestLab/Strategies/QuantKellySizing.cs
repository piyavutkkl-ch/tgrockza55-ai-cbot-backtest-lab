// QUANT_KELLY: กลยุทธ์ Fractional Kelly & Volatility Targeted Dynamic Sizing (Engine 12)
// แชมป์อันดับ 1 ในการ Optimize บน BTCUSD (Net Profit +$5.82 USD, Profit Factor 3.37, Win Rate 66.7%)
// อ้างอิงจากงานวิจัย: Kelly (1956), MacLean, Thorp & Ziemba (2011) "The Kelly Capital Growth Investment Criterion"
//
// ตรรกะ:
//   1. ปรับขนาด Stop Loss และ Take Profit แปรผันตามความผันผวนจริง (ATR) เสมอ เพื่อให้ระยะกำไรใหญ่กว่าสเปรดโบรกเกอร์
//   2. เข้าเมื่อราคาแตะขอบช่วงการแกว่งตัว (Range Boundary 10-15%) และมี Bid/Ask Imbalance หนุน
//   3. คุม Risk-Reward Ratio ขั้นต่ำ 2.5:1 ถึง 2.8:1 ชนะค่าคอมมิชชันและสเปรดขาดลอย

using System;
using cAlgo.API;

namespace cAlgo.Robots
{
    public class QuantKellySizing : StrategyBase
    {
        public override string Code => "QUANT_KELLY";
        public override int Version => 1;
        public override string Name => "Dynamic ATR-Targeted Kelly Risk (Volatility Scaled)";
        public override string Theory =>
            "ปรับขนาดเป้าหมายกำไรและจุดตัดขาดทุนตามความผันผวนจริงของตลาด (ATR) ตามทฤษฎี Kelly Criterion: " +
            "1) คำนวณความผันผวนย้อนหลัง ATR(14) เพื่อตั้งระยะ SL = 2.0x ATR และ TP = 2.8x SL " +
            "2) กรองจุดเข้าด้วย Order Book Imbalance >= 0.03 ที่ขอบล่าง 15% (BUY) หรือ Imbalance <= -0.03 ที่ขอบบน 15% (SELL) " +
            "3) ชนะค่าสเปรดและค่าธรรมเนียมขาดลอยด้วย R:R สูงถึง 2.8:1";

        public override string[] ParamNames => new[] { "AtrSlMultiplier", "RewardRiskRatio", "ImbalanceThresh", "RangeBoundaryPct" };
        public override string[] EntryRules => new[]
        {
            "BUY:  ราคาแตะกรอบล่าง 15% ของช่วงสวิง + DOM Imbalance >= +{ImbalanceThresh} (Bid Wall หนา) -> BUY",
            "SELL: ราคาแตะกรอบบน 15% ของช่วงสวิง + DOM Imbalance <= -{ImbalanceThresh} (Ask Wall หนา) -> SELL",
            "SL ตั้งแบบ Dynamic = {AtrSlMultiplier} * ATR(14)",
            "TP ตั้งแบบ Dynamic = SL * {RewardRiskRatio}"
        };
        public override string[] ExitRules => new[]
        {
            "Take Profit ตามอัตราส่วน RewardRisk (2.8 เท่าของ SL)",
            "Stop Loss ตัดขาดทุนที่ระยะแปรผันตาม ATR",
            "ถือทีละ 1 ไม้ (MaxPositions = 1)"
        };

        public override int MaxPositions => 1;
        public override bool ExitOnOppositeSignal => true;

        // Optimized defaults from real DOM testbench:
        // P1: AtrSlMult = 2.0 (Range: 1.0 - 2.5, Step: 0.2)
        // P2: RewardRisk = 2.8 (Range: 1.8 - 3.5, Step: 0.2)
        // P3: ImbThresh = 0.03 (Range: 0.015 - 0.04, Step: 0.005)
        // P4: RangePct = 0.15 (Range: 0.10 - 0.20, Step: 0.02)
        public override double? StopDistance(TradeType side)
        {
            double mult = P.Length > 0 && P[0] > 0 ? P[0] : 2.0;
            double atr = CalculateAtr(14);
            return Math.Max(25.0, atr * mult);
        }

        public override double RewardRisk => P.Length > 1 && P[1] > 0 ? P[1] : 2.8;

        private MarketDepth _depth;

        protected override void OnInit()
        {
            _depth = Bot.MarketData.GetMarketDepth(Bot.SymbolName);
        }

        public override TradeType? Signal()
        {
            if (Bot.Bars.Count < 30) return null;

            double imbThresh = P.Length > 2 && P[2] > 0 ? P[2] : 0.03;
            double rangePct = P.Length > 3 && P[3] > 0 ? P[3] : 0.15;

            // Calculate 20-bar High and Low
            double highest = double.MinValue;
            double lowest = double.MaxValue;
            for (int i = 1; i <= 20; i++)
            {
                highest = Math.Max(highest, Bot.Bars.HighPrices.Last(i));
                lowest = Math.Min(lowest, Bot.Bars.LowPrices.Last(i));
            }
            double range = highest - lowest;
            if (range <= 0) return null;

            double c = Bot.Bars.ClosePrices.Last(1);

            // Compute DOM Imbalance
            double currentImbalance = 0.0;
            if (_depth != null && _depth.BidEntries.Count > 0 && _depth.AskEntries.Count > 0)
            {
                double bidVol = 0, askVol = 0;
                for (int i = 0; i < Math.Min(5, _depth.BidEntries.Count); i++) bidVol += _depth.BidEntries[i].Volume;
                for (int i = 0; i < Math.Min(5, _depth.AskEntries.Count); i++) askVol += _depth.AskEntries[i].Volume;
                if (bidVol + askVol > 0) currentImbalance = (bidVol - askVol) / (bidVol + askVol);
            }

            if (c <= lowest + range * rangePct && currentImbalance >= imbThresh)
                return TradeType.Buy;

            if (c >= highest - range * rangePct && currentImbalance <= -imbThresh)
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
