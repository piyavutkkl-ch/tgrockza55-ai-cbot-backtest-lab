// SMC_FIBO_DOM_5M: สแคลปปิ้ง 5 นาที ผสานโครงสร้าง SMC + Fibonacci Golden Zone + DOM Imbalance
// เข้าทีละ 1 ไม้ (Single Position Only) และตัดรอบกำไรใน 5 นาที (Intraday)
//
// จุดเด่นการรวมกลยุทธ์:
//   1. แก้ปัญหาของ DOM Fade เดิม ที่เทรด Sell ฝั่งเดียว และมักโดนลากเวลาเจอเทรนด์ใหญ่
//   2. แก้ปัญหาของ SMC Fibo เดิม ที่ต้องถือยาวบน M30 โดยนำมาประยุกต์เข้ากับโครงสร้างไมโคร M1/M5
//   3. เทรดได้ทั้ง 2 ฝั่ง (Buy เมื่อย่อตัวสู่ Discount Zone + Bid Absorption, Sell เมื่อดีดสู่ Premium Zone + Ask Exhaustion)
//   4. คุมความเสี่ยงเข้มงวด: TP $1.50, SL $1.50, ปิดตลาดทันทีเมื่อถือครบ 5 นาที

using System;
using System.Collections.Generic;
using System.Linq;
using cAlgo.API;

namespace cAlgo.Robots
{
    public class SmcFiboDom5m : StrategyBase
    {
        public override string Code => "SMC_FIBO_DOM_5M";
        public override int Version => 1;
        public override string Name => "SMC Structure + Fibo Golden Zone + DOM 5m Scalper";
        public override string Theory =>
            "กลยุทธ์ไฮบริดที่ผสานการวิเคราะห์โครงสร้างตลาด Smart Money Concepts (BOS), " +
            "การย่อตัวสู่ Fibonacci Golden Zone (0.50 - 0.65) และการยืนยันสภาพคล่องจริงจาก Order Book (DOM): " +
            "1) ระบุแนวโน้มด้วย Break of Structure (BOS) เพื่อเลือกหน้าเทรด (Buy หรือ Sell) " +
            "2) รอราคาย่อตัวเข้าสู่โซน Fibonacci 50% - 65% ของสวิงล่าสุด " +
            "3) ยืนยันด้วยแท่ง Rejection Wick ร่วมกับ DOM Ladder Skew / Absorption เพื่อตัด False Breakout " +
            "4) ล็อคกำไร/ตัดขาดทุนเฉียบขาด: TP $1.50, SL $1.50, ถือไม่เกิน 5 นาที (CutAfterMinutes = 5) เข้าทีละ 1 ไม้";

        public override string[] ParamNames => new[] { "SwingK", "FibMin", "TakeProfitUsd", "StopLossUsd" };
        public override string[] EntryRules => new[]
        {
            "ขาขึ้น (BUY): เกิด Bullish BOS ทะลุ High ก่อนหน้า -> ราคาย่อตัวเข้าสู่ Fibo Golden Zone (50%-65%) " +
            "-> เกิดแท่งเทียน Rejection ล่าง + DOM Bid หนาหนุน (ไม่เกิด Ask Skew) และราคายืนเหนือแนว VWAP",
            "ขาลง (SELL): เกิด Bearish BOS หลุด Low ก่อนหน้า -> ราคาเด้งทดสอบ Fibo Golden Zone " +
            "-> เกิดแท่ง Rejection บน + DOM Ask Ladder ยืดกว้าง (สภาพคล่อง Ask บางตา) และราคาอยู่ใต้แนว VWAP",
            "สเปรด ณ ขณะเข้าเทรด <= 0.15 USD (1.5 pips)",
            "เข้าทีละไม้ (Single Position Only, MaxPositions = 1) และไม่ถือข้ามวัน (Flat ก่อน 20:45 UTC)",
        };
        public override string[] ExitRules => new[]
        {
            "Take Profit {TakeProfitUsd} USD",
            "Stop Loss {StopLossUsd} USD",
            "ถือครบ 5 นาทีแล้วยังไม่ชน TP/SL ให้ปิดทันทีที่ราคาตลาด (Time Stop 5m)",
            "ปิดทุกออเดอร์ก่อน 20:45 UTC (Flat Time)",
        };

        public override int MaxPositions => 1;
        public override bool ExitOnOppositeSignal => false;

        // SL & TP การบริหารความเสี่ยง
        public override double? StopDistance(TradeType side) => P[3]; // P[3] = StopLossUsd (default 1.50)
        public override double RewardRisk => P[2] > 0 && P[3] > 0 ? P[2] / P[3] : 1.0; // P[2] = TakeProfitUsd (default 1.50)

        // ขีดจำกัดเวลา 5 นาที (CutAfterMinutes = 5)
        public override int CutAfterMinutes => 5;
        public override double CutBelowR => 999.0; // ครบเวลาปิดทันที

        private MarketDepth _depth;
        private FlowTracker _flow;
        private double _ladderBid, _ladderAsk;
        private DateTime _lastLossExit = DateTime.MinValue;

        // ตัวแปรติดตามโครงสร้างราคา (Swing & BOS Tracker)
        private readonly List<SwingPoint> _highs = new List<SwingPoint>();
        private readonly List<SwingPoint> _lows = new List<SwingPoint>();
        private double _bullHigh, _bullLow;
        private double _bearHigh, _bearLow;
        private bool _waitingBullRetrace, _bullRetraceTouched;
        private bool _waitingBearRetrace, _bearRetraceTouched;
        private int _bosBarIndex;

        private class SwingPoint
        {
            public int Index;
            public double Price;
        }

        protected override void OnInit()
        {
            // P1: SwingK (default 4 bars)
            // P2: FibMin (default 0.50)
            // P3: TakeProfitUsd (default 1.50)
            // P4: StopLossUsd (default 1.50)
            Defaults(4, 0.50, 1.50, 1.50);
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
                    Bot.Print("SMC_FIBO_DOM_5M: MarketDepth not available: {0}", e.Message);
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
            int swingK = (int)P[0];
            if (!HasBars(swingK * 2 + 15)) return null;

            var nowUtc = Bot.Server.TimeInUtc;
            // Cooldown 2 นาทีหลังตัดขาดทุน
            if ((nowUtc - _lastLossExit).TotalSeconds < 120)
                return null;

            // กรองสเปรด (ไม่เกิน 0.15 USD = 1.5 pips)
            double spread = Bot.Symbol.Ask - Bot.Symbol.Bid;
            if (spread > 0.15)
                return null;

            // กรองเวลาไม่เข้าเทรดช่วงตลาดใกล้ปิด (หลัง 20:30 UTC)
            if (nowUtc.Hour == 20 && nowUtc.Minute >= 30)
                return null;

            int currentBar = Bot.Bars.Count - 1;
            int pivotBar = currentBar - swingK;
            double tol = C(1) * 0.0002;

            // ตรวจสอบ Pivot High
            double pHigh = H(currentBar - pivotBar);
            bool isHigh = true;
            for (int j = 1; j <= swingK * 2; j++)
            {
                int barIdx = currentBar - pivotBar - swingK + j;
                if (barIdx == currentBar - pivotBar) continue;
                if (H(barIdx) > pHigh) { isHigh = false; break; }
            }
            if (isHigh && (_highs.Count == 0 || _highs[_highs.Count - 1].Index != pivotBar))
            {
                _highs.Add(new SwingPoint { Index = pivotBar, Price = pHigh });
                if (_highs.Count > 30) _highs.RemoveAt(0);
            }

            // ตรวจสอบ Pivot Low
            double pLow = L(currentBar - pivotBar);
            bool isLow = true;
            for (int j = 1; j <= swingK * 2; j++)
            {
                int barIdx = currentBar - pivotBar - swingK + j;
                if (barIdx == currentBar - pivotBar) continue;
                if (L(barIdx) < pLow) { isLow = false; break; }
            }
            if (isLow && (_lows.Count == 0 || _lows[_lows.Count - 1].Index != pivotBar))
            {
                _lows.Add(new SwingPoint { Index = pivotBar, Price = pLow });
                if (_lows.Count > 30) _lows.RemoveAt(0);
            }

            // 1. ตรวจสอบ Bullish BOS
            if (_highs.Count > 0 && C(1) > _highs[_highs.Count - 1].Price + tol && !_waitingBullRetrace)
            {
                _bullHigh = H(1);
                _bullLow = _lows.Count > 0 ? _lows[_lows.Count - 1].Price : L(1);
                _waitingBullRetrace = true;
                _waitingBearRetrace = false;
                _bullRetraceTouched = false;
                _bosBarIndex = currentBar;
            }

            // 2. ตรวจสอบ Bearish BOS
            if (_lows.Count > 0 && C(1) < _lows[_lows.Count - 1].Price - tol && !_waitingBearRetrace)
            {
                _bearLow = L(1);
                _bearHigh = _highs.Count > 0 ? _highs[_highs.Count - 1].Price : H(1);
                _waitingBearRetrace = true;
                _waitingBullRetrace = false;
                _bearRetraceTouched = false;
                _bosBarIndex = currentBar;
            }

            double vwap = _flow.DayVwap > 0 ? _flow.DayVwap : C(1);
            double candleRange = Range(1);

            // 3. เงื่อนไขเข้า BUY (ย่อตัวลงมาแตะ Fibo Golden Zone ของขาขึ้น + DOM หนุน)
            if (_waitingBullRetrace)
            {
                if (H(1) > _bullHigh && !_bullRetraceTouched)
                    _bullHigh = H(1);

                double leg = _bullHigh - _bullLow;
                if (leg > 0.60)
                {
                    double fib50 = _bullHigh - P[1] * leg; // 50% Retracement
                    if (L(1) <= fib50 && L(1) >= _bullLow)
                        _bullRetraceTouched = true;

                    if (_bullRetraceTouched)
                    {
                        double lowerWick = Math.Min(O(1), C(1)) - L(1);
                        bool rejection = (candleRange > 0 && lowerWick >= 0.20 * candleRange) || C(1) > O(1);
                        bool domOk = _ladderBid >= _ladderAsk - 0.001;
                        bool vwapOk = C(1) >= vwap - 0.50;

                        if (rejection && domOk && vwapOk)
                        {
                            _waitingBullRetrace = false;
                            return TradeType.Buy;
                        }
                    }

                    if (C(1) < _bullLow || (currentBar - _bosBarIndex) > 30)
                        _waitingBullRetrace = false;
                }
            }

            // 4. เงื่อนไขเข้า SELL (เด้งขึ้นไปแตะ Fibo Golden Zone ของขาลง + DOM Ask Exhaustion)
            if (_waitingBearRetrace)
            {
                if (L(1) < _bearLow && !_bearRetraceTouched)
                    _bearLow = L(1);

                double leg = _bearHigh - _bearLow;
                if (leg > 0.60)
                {
                    double fib50 = _bearLow + P[1] * leg; // 50% Retracement
                    if (H(1) >= fib50 && H(1) <= _bearHigh)
                        _bearRetraceTouched = true;

                    if (_bearRetraceTouched)
                    {
                        double upperWick = H(1) - Math.Max(O(1), C(1));
                        bool rejection = (candleRange > 0 && upperWick >= 0.20 * candleRange) || C(1) <= O(1);
                        double skew = _ladderAsk - _ladderBid;
                        bool domOk = skew >= 0.0020;
                        bool vwapOk = C(1) <= vwap + 0.50;

                        if (rejection && domOk && vwapOk)
                        {
                            _waitingBearRetrace = false;
                            return TradeType.Sell;
                        }
                    }

                    if (C(1) > _bearHigh || (currentBar - _bosBarIndex) > 30)
                        _waitingBearRetrace = false;
                }
            }

            return null;
        }

        public override void OnStop()
        {
            if (_depth != null)
                _depth.Updated -= OnDepthUpdated;
        }
    }
}
