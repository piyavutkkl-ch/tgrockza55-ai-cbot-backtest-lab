// DOM_WALL_ABSORPTION: กลยุทธ์ตรวจจับกำแพงสมุดคำสั่งซื้อขาย (Order Book Imbalance Wall Absorption)
// ดักทางจุดกลับตัวเมื่อราคาแตะขอบสวิงแล้วมีผู้เล่นรายใหญ่ตั้งกำแพงรับของ (Absorption)
//
// ตรรกะ:
//   1. เฝ้าติดตาม Order Book (Level 2 MarketDepth) คำนวณ Imbalance: (BidVol - AskVol) / (BidVol + AskVol)
//   2. ตรวจจับการแตะขอบ Rolling High / Low ในรอบ 15-20 นาที
//   3. ขา SELL: เมื่อราคาพุ่งทดสอบ High แต่ในสมุดคำสั่งมีกำแพง Ask กองหนาแน่น (Imbalance <= -0.03) -> สั่ง SELL
//   4. ขา BUY:  เมื่อราคาดิ่งทดสอบ Low แต่ในสมุดคำสั่งมีกำแพง Bid กองหนาแน่น (Imbalance >= +0.03) -> สั่ง BUY
//   5. คุมความเสี่ยงเข้มงวด: ถือทีละ 1 ไม้ (MaxPositions = 1), SL ตามโครงสร้าง, TP ชนะค่าสเปรดขาดลอย

using System;
using System.Collections.Generic;
using System.Linq;
using cAlgo.API;

namespace cAlgo.Robots
{
    public class DomWallAbsorption : StrategyBase
    {
        public override string Code => "DOM_ABSORPTION";
        public override int Version => 1;
        public override string Name => "DOM Wall Absorption (Order Book Exhaustion)";
        public override string Theory =>
            "ตรวจจับการดูดซับแรงซื้อขาย (Liquidity Absorption) ในสมุดคำสั่ง Level 2: " +
            "1) เมื่อราคาแตะแนวต้านสวิง High แต่เจอ Ask Wall หนาแน่นขวางไว้ (Imbalance ติดลบ) ราคาจะทุบกลับทันที -> SELL " +
            "2) เมื่อราคาแตะแนวรับสวิง Low แต่เจอ Bid Wall หนาแน่นหนุนรับ (Imbalance เป็นบวก) ราคาจะเด้งกลับทันที -> BUY " +
            "3) ระบบปิดทำกำไรอัตโนมัติ (TP) และคุมความเสี่ยงด้วย SL สั้น (RR 1:2 ถึง 1:3.5) ชนะค่าสเปรดขาดลอย";

        public override string[] ParamNames => new[] { "LookbackMin", "ImbalanceThresh", "StopLossUsd", "RewardRisk" };
        public override string[] EntryRules => new[]
        {
            "ขาขึ้น (BUY): ราคาแตะโซน Low ในรอบ {LookbackMin} นาที + DOM Imbalance >= +{ImbalanceThresh} (Bid Wall หนา) -> BUY",
            "ขาลง (SELL): ราคาแตะโซน High ในรอบ {LookbackMin} นาที + DOM Imbalance <= -{ImbalanceThresh} (Ask Wall หนา) -> SELL",
            "จำกัดการเข้า: ถือทีละ 1 ไม้เท่านั้น (MaxPositions = 1) และสเปรดต้องอยู่ในเกณฑ์ปกติ",
        };
        public override string[] ExitRules => new[]
        {
            "Take Profit ตามอัตราส่วน RewardRisk (เช่น 2.0 เท่าของ SL)",
            "Stop Loss ตัดขาดทุนที่ {StopLossUsd} USD",
            "Smart DOM Exit: หากมีกำไรแล้วตรวจพบกำแพงฝั่งตรงข้ามตั้งขวาง จะปิดล็อกกำไรทันที",
        };

        public override int MaxPositions => 1;
        public override bool ExitOnOppositeSignal => true;

        private MarketDepth _depth;
        private double _currentImbalance;
        private double _lastStopDistance;
        private double _rewardRisk = 2.0;

        // พารามิเตอร์เริ่มต้นตามสินทรัพย์
        private int _lookback = 15;
        private double _imbThresh = 0.03;
        private double _defaultSl = 25.0;
        private double _defaultRr = 2.0;

        protected override void OnInit()
        {
            // ปรับค่าเริ่มต้นตามคู่เงิน
            string sym = Bot.SymbolName.ToUpperInvariant();
            if (sym.Contains("BTC"))
            {
                _lookback = 15;
                _imbThresh = 0.03;
                _defaultSl = 25.0;
                _defaultRr = 2.0; // TP $50.0
            }
            else if (sym.Contains("ETH"))
            {
                _lookback = 20;
                _imbThresh = 0.03;
                _defaultSl = 1.0;
                _defaultRr = 3.5; // TP $3.5
            }
            else if (sym.Contains("GOLD") || sym.Contains("XAU"))
            {
                _lookback = 15;
                _imbThresh = 0.03;
                _defaultSl = 1.0;
                _defaultRr = 2.0; // TP $2.0
            }

            // โอเวอร์ไรด์ด้วยพารามิเตอร์ P ถ้าผู้ใช้กำหนดมา
            if (P.Length > 0 && P[0] > 0) _lookback = (int)P[0];
            if (P.Length > 1 && P[1] > 0) _imbThresh = P[1];
            if (P.Length > 2 && P[2] > 0) _defaultSl = P[2];
            if (P.Length > 3 && P[3] > 0) _defaultRr = P[3];

            _lastStopDistance = _defaultSl;
            _rewardRisk = _defaultRr;

            // เชื่อมต่อ Event Market Depth
            if (Bot.RunningMode == RunningMode.RealTime)
            {
                try
                {
                    _depth = Bot.MarketData.GetMarketDepth(Bot.SymbolName);
                    if (_depth != null)
                    {
                        _depth.Updated += OnDepthUpdated;
                        Bot.Print("DOM_ABSORPTION: MarketDepth connected for {0}. Lookback={1}m, ImbThresh={2}, SL={3}, RR={4}",
                            Bot.SymbolName, _lookback, _imbThresh, _defaultSl, _defaultRr);
                    }
                }
                catch (Exception e)
                {
                    Bot.Print("DOM_ABSORPTION: MarketDepth warning: {0}", e.Message);
                }
            }
        }

        private void OnDepthUpdated()
        {
            if (_depth == null) return;
            try
            {
                var bids = _depth.BidEntries.Take(10).ToList();
                var asks = _depth.AskEntries.Take(10).ToList();
                if (bids.Count == 0 && asks.Count == 0) return;

                double bidVol = bids.Sum(e => e.VolumeInUnits);
                double askVol = asks.Sum(e => e.VolumeInUnits);

                if (bidVol + askVol > 0)
                {
                    _currentImbalance = (bidVol - askVol) / (bidVol + askVol);
                }
            }
            catch { }
        }

        public override TradeType? Signal()
        {
            int count = Bot.Bars.Count;
            if (count < _lookback + 5) return null;

            // คำนวณ High และ Low ในช่วง Lookback แท่งล่าสุด
            double rollingHigh = double.MinValue;
            double rollingLow = double.MaxValue;

            for (int i = 1; i <= _lookback; i++)
            {
                double h = Bot.Bars.HighPrices.Last(i);
                double l = Bot.Bars.LowPrices.Last(i);
                if (h > rollingHigh) rollingHigh = h;
                if (l < rollingLow) rollingLow = l;
            }

            double currentBid = Bot.Symbol.Bid;
            double currentAsk = Bot.Symbol.Ask;
            double tol = (rollingHigh - rollingLow) * 0.08; // อยู่ในโซน 8% ขอบบน/ล่าง

            // ขา SELL: ราคาแตะโซน High + มีกำแพงคนตั้งขายหนาแน่น (Imbalance <= -ImbalanceThresh)
            if (currentBid >= rollingHigh - tol && _currentImbalance <= -_imbThresh)
            {
                _lastStopDistance = _defaultSl;
                _rewardRisk = _defaultRr;
                Bot.Print("DOM_ABSORPTION: SELL Trigger! Price={0:F2} near High={1:F2}, Imbalance={2:F3}",
                    currentBid, rollingHigh, _currentImbalance);
                return TradeType.Sell;
            }

            // ขา BUY: ราคาแตะโซน Low + มีกำแพงคนตั้งซื้อหนาแน่น (Imbalance >= +ImbalanceThresh)
            if (currentAsk <= rollingLow + tol && _currentImbalance >= _imbThresh)
            {
                _lastStopDistance = _defaultSl;
                _rewardRisk = _defaultRr;
                Bot.Print("DOM_ABSORPTION: BUY Trigger! Price={0:F2} near Low={1:F2}, Imbalance={2:F3}",
                    currentAsk, rollingLow, _currentImbalance);
                return TradeType.Buy;
            }

            return null;
        }

        public override double? StopDistance(TradeType side) => _lastStopDistance;
        public override double RewardRisk => _rewardRisk;

        public override bool ShouldExit(Position pos)
        {
            if (pos == null) return false;

            double currentPrice = pos.TradeType == TradeType.Buy ? Bot.Symbol.Bid : Bot.Symbol.Ask;
            double profitDist = pos.TradeType == TradeType.Buy
                ? (currentPrice - pos.EntryPrice)
                : (pos.EntryPrice - currentPrice);

            // ถ้ากำไรเกิน 50% ของเป้าหมาย แล้วพบกำแพงฝั่งตรงข้ามตั้งขวางชัดเจน -> ชิงปิดล็อกกำไร
            double halfTarget = (_lastStopDistance * _rewardRisk) * 0.5;
            if (profitDist >= halfTarget)
            {
                if (pos.TradeType == TradeType.Buy && _currentImbalance <= -(_imbThresh * 1.5))
                {
                    Bot.Print("DOM_ABSORPTION: Smart Exit BUY at profit +{0:F2} (Opposite Ask Wall detected)", profitDist);
                    return true;
                }
                if (pos.TradeType == TradeType.Sell && _currentImbalance >= (_imbThresh * 1.5))
                {
                    Bot.Print("DOM_ABSORPTION: Smart Exit SELL at profit +{0:F2} (Opposite Bid Wall detected)", profitDist);
                    return true;
                }
            }

            return false;
        }

        public override void OnStop()
        {
            if (_depth != null)
                _depth.Updated -= OnDepthUpdated;
        }
    }
}
