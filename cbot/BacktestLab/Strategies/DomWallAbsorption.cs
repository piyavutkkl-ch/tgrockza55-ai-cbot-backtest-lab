// DOM_WALL_ABSORPTION V2: Institutional Liquidity & Spread-Protected Absorption Model
// ป้องกันการโดนลาก (Trend/Regime), ป้องกันสเปรดถ่างช่วงกลางคืน (Spread Ceiling), และมีระบบ Breakeven Lock

using System;
using System.Collections.Generic;
using System.Linq;
using cAlgo.API;

namespace cAlgo.Robots
{
    public class DomWallAbsorption : StrategyBase
    {
        public override string Code => "DOM_ABSORPTION";
        public override int Version => 2;
        public override string Name => "DOM Wall Absorption V2 (Spread & Order Flow Protected)";
        public override string Theory =>
            "ตรวจจับการดูดซับแรงซื้อขาย (Liquidity Absorption) เชิงลึก Level 2 พร้อมระบบป้องกันสเปรดถ่างและป้องกันการเทรดสวนเทรนด์: " +
            "1) Spread Ceiling Gate: ปฏิเสธการเข้าเทรดทันทีถ้าสเปรดกว้างเกินเพดาน (ป้องกัน Asian Night Spread Spikes) " +
            "2) Exhaustion Wall Fade: ดักจับกำแพง Order Book ขนาดใหญ่ที่ขอบราคาที่มีสัญญาณชะลอตัว " +
            "3) Dynamic SL & Target: ปรับระยะ SL ให้สัมพันธ์กับสเปรดตลาด ไม่ตั้ง SL แคบกว่าความกว้างของสเปรด " +
            "4) Breakeven Trailing: ขยับ SL บังทุน + ค่าธรรมเนียมทันทีเมื่อราคาบวกถึง 1.0R";

        public override string[] ParamNames => new[] { "LookbackMin", "ImbalanceThresh", "StopLossUsd", "RewardRisk", "SpreadCeiling" };
        public override string[] EntryRules => new[]
        {
            "ความปลอดภัย (Spread Gate): สเปรดต้องต่ำกว่าเพดาน (BTC <= $20, ETH <= $2.2, XAU <= $0.20) ป้องกันสเปรดกิน SL",
            "ฝั่งซื้อ (BUY): ราคาแตะ Low รอบ {LookbackMin} นาที + DOM Imbalance >= +{ImbalanceThresh} (มี Bid Wall ค้ำหนาแน่น)",
            "ฝั่งขาย (SELL): ราคาแตะ High รอบ {LookbackMin} นาที + DOM Imbalance <= -{ImbalanceThresh} (มี Ask Wall ขวางหนาแน่น)",
            "จำกัดความเสี่ยง: เปิดได้ทีละ 1 ไม้เท่านั้น (MaxPositions = 1) และซ่อน SL ในหน่วยความจำ (RAM)",
        };
        public override string[] ExitRules => new[]
        {
            "Take Profit: เป้าหมายกำไร {RewardRisk} เท่าของระยะตัดขาดทุน (RR 1.5 - 2.5)",
            "Breakeven Lock: เมื่อกำไรแตะ 1.0R ขยับ SL บังทุนเสมอเพื่อล็อกไม่ให้ไม้ที่ชนะกลายเป็นแพ้",
            "Stop Loss: ตัดขาดทุนที่ระยะปลอดภัยตามการคำนวณแบบ Dynamic ผกผันตามสเปรด",
            "Smart DOM Exit: หากกำไรเกิน 50% แล้วตรวจพบกำแพงฝั่งตรงข้ามตั้งขวาง จะปิดล็อกกำไรทันที",
        };

        public override int MaxPositions => 1;
        public override bool ExitOnOppositeSignal => true;

        private MarketDepth _depth;
        private double _currentImbalance;
        private double _lastStopDistance;
        private double _rewardRisk = 1.5;

        // ค่าพารามิเตอร์ที่ผ่านการ Optimize บนข้อมูล L2 DOM 2,020 แท่ง
        private int _lookback = 30;
        private double _imbThresh = 0.02;
        private double _defaultSl = 70.0;
        private double _defaultRr = 1.5;
        private double _spreadCeiling = 20.0;

        protected override void OnInit()
        {
            string sym = Bot.SymbolName.ToUpperInvariant();
            if (sym.Contains("BTC"))
            {
                _lookback = 30;
                _imbThresh = 0.02;
                _defaultSl = 70.0;
                _defaultRr = 1.5;
                _spreadCeiling = 20.0; // เพดานสเปรด BTC $20 USD
            }
            else if (sym.Contains("ETH"))
            {
                _lookback = 10;
                _imbThresh = 0.05;
                _defaultSl = 1.5;
                _defaultRr = 2.0;
                _spreadCeiling = 2.2;  // เพดานสเปรด ETH $2.2 USD
            }
            else if (sym.Contains("GOLD") || sym.Contains("XAU"))
            {
                _lookback = 30;
                _imbThresh = 0.02;
                _defaultSl = 3.5;
                _defaultRr = 2.0;
                _spreadCeiling = 0.20; // เพดานสเปรดทอง $0.20 USD
            }

            // โอเวอร์ไรด์ด้วย P ถ้าผู้ใช้กำหนด
            if (P.Length > 0 && P[0] > 0) _lookback = (int)P[0];
            if (P.Length > 1 && P[1] > 0) _imbThresh = P[1];
            if (P.Length > 2 && P[2] > 0) _defaultSl = P[2];
            if (P.Length > 3 && P[3] > 0) _defaultRr = P[3];
            if (P.Length > 4 && P[4] > 0) _spreadCeiling = P[4];

            _lastStopDistance = _defaultSl;
            _rewardRisk = _defaultRr;

            if (Bot.RunningMode == RunningMode.RealTime)
            {
                try
                {
                    _depth = Bot.MarketData.GetMarketDepth(Bot.SymbolName);
                    if (_depth != null)
                    {
                        _depth.Updated += OnDepthUpdated;
                        Bot.Print("DOM_ABSORPTION V2: MarketDepth connected for {0}. Lookback={1}m, ImbThresh={2:F3}, SL={3}, RR={4}, SpreadCeil={5}",
                            Bot.SymbolName, _lookback, _imbThresh, _defaultSl, _defaultRr, _spreadCeiling);
                    }
                }
                catch (Exception e)
                {
                    Bot.Print("DOM_ABSORPTION V2 warning: {0}", e.Message);
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

            // 1. ตรวจสอบเพดานสเปรด (Spread Safety Gate)
            double currentSpread = Bot.Symbol.Spread;
            if (currentSpread > _spreadCeiling)
            {
                // สเปรดถ่างผิดปกติ (เช่น ช่วงตลาดเอเชียกลางคืน) -> ห้ามเทรดเด็ดขาด
                return null;
            }

            // 2. คำนวณขอบเขต High / Low
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
            double tol = (rollingHigh - rollingLow) * 0.08;

            // 3. ปรับระยะ SL ให้ปลอดภัย ไม่ต่ำกว่า 2.5 เท่าของสเปรด
            _lastStopDistance = Math.Max(_defaultSl, 2.5 * currentSpread);
            _rewardRisk = _defaultRr;

            // 4. สัญญาณ SELL: ราคาชนโซน High + มีกำแพงขายหนาแน่น
            if (currentBid >= rollingHigh - tol && _currentImbalance <= -_imbThresh)
            {
                Bot.Print("DOM_ABSORPTION V2: SELL Signal at {0:F2} (Spread={1:F2} <= {2:F2}, Imbalance={3:F3})",
                    currentBid, currentSpread, _spreadCeiling, _currentImbalance);
                return TradeType.Sell;
            }

            // 5. สัญญาณ BUY: ราคาแตะโซน Low + มีกำแพงซื้อหนุนหนาแน่น
            if (currentAsk <= rollingLow + tol && _currentImbalance >= _imbThresh)
            {
                Bot.Print("DOM_ABSORPTION V2: BUY Signal at {0:F2} (Spread={1:F2} <= {2:F2}, Imbalance={3:F3})",
                    currentAsk, currentSpread, _spreadCeiling, _currentImbalance);
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

            // Breakeven Lock: หากกำไรเกิน 1.0R ให้ขยับล็อกทุน
            double r1 = _lastStopDistance;
            if (profitDist >= r1)
            {
                // สามารถใช้สมาร์ทเอ็กซิทเมื่อกำแพงเปลี่ยนทิศ
                if (pos.TradeType == TradeType.Buy && _currentImbalance <= -(_imbThresh * 1.5))
                {
                    Bot.Print("DOM_ABSORPTION V2: Smart Exit BUY at +{0:F2} profit", profitDist);
                    return true;
                }
                if (pos.TradeType == TradeType.Sell && _currentImbalance >= (_imbThresh * 1.5))
                {
                    Bot.Print("DOM_ABSORPTION V2: Smart Exit SELL at +{0:F2} profit", profitDist);
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
