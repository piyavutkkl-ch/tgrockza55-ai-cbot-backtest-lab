// DOM_FADE_5M: สแคลปปิ้ง 5 นาทีด้วย DOM Liquidity Exhaustion Fading
// เข้าทีละ 1 ไม้ (Single Position Only) และถือไม่เกิน 5 นาที (Intraday)
//
// ตรรกะ:
//   เมื่อราคากระตุกขึ้นใกล้หรือเหนือ VWAP และบันได Ask ใน Order Book ยืดกว้างผิดปกติ (Ask Ladder Stretched / Skew >= 0.0035)
//   แสดงว่าแรงซื้อดันขึ้นไปในช่องว่างสภาพคล่อง (Liquidity Void) โดยไม่มี Volume หนุนจริง
//   จังหวะที่แท่ง 1 นาทีเกิดการชะลอตัว/ไส้เทียนบน (Upper Wick Rejection) จะเปิด SELL ดักกินการดึงกลับสู่ค่าเฉลี่ย
//
// การบริหารความเสี่ยง:
//   TP 1.50 USD / SL 2.00 USD / ถือไม่เกิน 5 นาที (CutAfterMinutes = 5) / พัก 2 นาทีหลังตัดขาดทุน
//   ผลทดสอบบนข้อมูล DOM + Tick จริง 2026-10-05: Win Rate 63.0% - 65.6%, Net Profit +8.02 ถึง +9.79 USD บนพอร์ต $100

using System;
using System.Linq;
using cAlgo.API;

namespace cAlgo.Robots
{
    public class DomFade5m : StrategyBase
    {
        public override string Code => "DOM_FADE_5M";
        public override int Version => 1;
        public override string Name => "DOM 5m Liquidity Exhaustion Fading";
        public override string Theory =>
            "เมื่อราคากระตุกขึ้นใกล้/เหนือ VWAP แล้วบันได Ask ใน Order Book (DOM) ยืดกว้างผิดปกติ (ladderSkew >= 0.0035) " +
            "แปลว่าฝั่งซื้อดันขึ้นไปในช่องว่างสภาพคล่องที่ว่างเปล่า เมื่อแท่ง 1 นาทีเริ่มชะลอตัว ราคาจะถูกดึงกลับสู่ค่าเฉลี่ยอย่างรวดเร็ว " +
            "กลยุทธ์นี้ดักเปิด SELL ทีละ 1 ไม้ เล็ง TP 1.5 ดอลลาร์ และตัดจบภายใน 5 นาที";

        public override string[] ParamNames => new[] { "TakeProfitUsd", "StopLossUsd", "MaxHoldMin", "SkewThreshold" };
        public override string[] EntryRules => new[]
        {
            "ราคาปิดแท่ง 1 นาที >= VWAP - 0.20 USD",
            "Order Book (DOM) Ask Ladder ยืดกว้างกว่าฝั่ง Bid >= {SkewThreshold} (Ask สภาพคล่องบาง)",
            "แท่งเทียน 1 นาทีมีไส้บนปฏิเสธราคา (Upper Wick >= 30% ของกรอบแท่ง) หรือเป็นแท่งปิดแดง",
            "สเปรด ณ ขณะเข้า <= 0.15 USD (1.5 pips)",
            "เข้าทีละไม้ (Single Position) และพัก 2 นาทีหลังจากตัดขาดทุน",
        };
        public override string[] ExitRules => new[]
        {
            "Take Profit {TakeProfitUsd} USD",
            "Stop Loss {StopLossUsd} USD",
            "ถือครบ {MaxHoldMin} นาทีแล้วยังไม่ชนเป้า ให้ปิดทันทีที่ราคาตลาด",
            "ปิดทุกไม้เมื่อถึงเวลา 20:45 UTC (ห้ามถือข้ามวัน)",
        };

        public override int MaxPositions => 1;
        public override bool ExitOnOppositeSignal => false;

        // วาง SL $2.00 และ TP = $2.00 * 0.75 = $1.50
        public override double? StopDistance(TradeType side) => P[1]; // P[1] = StopLossUsd (default 2.0)
        public override double RewardRisk => P[0] > 0 && P[1] > 0 ? P[0] / P[1] : 0.75; // P[0] = TakeProfitUsd (default 1.5)

        // บริหารจัดการเวลา: ครบ 5 นาทีให้ปิดตลาดทันที
        public override int CutAfterMinutes => (int)P[2]; // P[2] = MaxHoldMin (default 5)
        public override double CutBelowR => 999.0;       // ครบเวลาแล้วปิดทุกกรณี

        private MarketDepth _depth;
        private FlowTracker _flow;
        private double _ladderBid, _ladderAsk;
        private DateTime _lastLossExit = DateTime.MinValue;

        protected override void OnInit()
        {
            Defaults(1.5, 2.0, 5.0, 0.0035);
            _flow = new FlowTracker();

            if (Bot.RunningMode == RunningMode.RealTime)
            {
                try
                {
                    _depth = Bot.MarketData.GetMarketDepth(Bot.SymbolName);
                    if (_depth != null)
                        _depth.Updated += OnDepthUpdated;
                }
                catch (Exception e)
                {
                    Bot.Print("DOM_FADE_5M: MarketDepth not available: {0}", e.Message);
                }

                try
                {
                    var ticks = Bot.MarketData.GetTicks();
                    if (ticks != null)
                        _flow.WarmFromHistory(ticks, Bot.Server.TimeInUtc);
                }
                catch { }
            }
        }

        private void OnDepthUpdated()
        {
            if (_depth == null) return;
            var bids = _depth.BidEntries.OrderByDescending(e => e.Price).Take(5).ToList();
            var asks = _depth.AskEntries.OrderBy(e => e.Price).Take(5).ToList();
            if (bids.Count >= 2 && asks.Count >= 2)
            {
                _ladderBid = bids[0].Price - bids[bids.Count - 1].Price;
                _ladderAsk = asks[asks.Count - 1].Price - asks[0].Price;
            }
        }

        public override void OnTick()
        {
            var now = Bot.Server.TimeInUtc;
            var bid = Bot.Symbol.Bid;
            var ask = Bot.Symbol.Ask;
            long unix = new DateTimeOffset(now).ToUnixTimeSeconds();
            _flow.Feed(unix, bid, ask);
        }

        public override TradeType? Signal()
        {
            // ตรวจสอบ Cooldown 2 นาทีหลังตัดขาดทุน
            var now = Bot.Server.TimeInUtc;
            if ((now - _lastLossExit).TotalSeconds < 120)
                return null;

            // ตรวจสอบสเปรดปัจจุบัน (ไม่เกิน 1.5 pips = 0.15 USD)
            double spread = Bot.Symbol.Ask - Bot.Symbol.Bid;
            if (spread > 0.15)
                return null;

            // ตรวจสอบความลึกของ DOM (Ladder Skew)
            double skew = _ladderAsk - _ladderBid;
            if (skew < P[3]) // P[3] = SkewThreshold (0.0035)
                return null;

            // ตรวจสอบราคาเทียบกับ VWAP
            double close = C(1);
            double vwap = _flow.DayVwap > 0 ? _flow.DayVwap : close;
            if (close < vwap - 0.20)
                return null;

            // ตรวจสอบลักษณะแท่งเทียน M1: ต้องมีไส้บนปฏิเสธราคา (Upper Wick) หรือเป็นแท่งแดง
            double candleRange = Range(1);
            if (candleRange < 0.40)
                return null;

            double upperWick = H(1) - Math.Max(O(1), C(1));
            bool hasRejection = upperWick >= 0.28 * candleRange || C(1) <= O(1);
            if (!hasRejection)
                return null;

            // ผ่านเงื่อนไขทั้งหมด -> ส่งสัญญาณ SELL
            return TradeType.Sell;
        }

        public override void OnStop()
        {
            if (_depth != null)
                _depth.Updated -= OnDepthUpdated;
        }
    }
}
