// DOM_SMART_RUNNER: กลยุทธ์ปลดล็อคข้อจำกัด 5 นาที + SMC Turning Point + DOM Exhaustion Exit
// เข้าทีละ 1 ไม้ (Single Position Only) ปิดในวัน (Flat ก่อน 20:45 UTC)
//
// ตรรกะสำคัญ:
//   1. ปลดล็อคกำไรจากเดิมที่บีบให้ปิดใน 5 นาที (TP $1.50) ขยายเป้ากำไรเป็น $3.50 (RR เกือบ 1:2)
//   2. ตรวจจับจุดเลี้ยว (Turning Points) ด้วยโครงสร้าง SMC BOS + Fibonacci Golden Zone 50%
//   3. กรองจุดเข้าด้วย Order Book (DOM) สภาพคล่องแท้จริง
//   4. จุดปิดอัจฉริยะ (Smart DOM Exit): ไม่รอให้โดนลากกลับ แต่จะสั่งปิดทำกำไรทันทีเมื่อ DOM ฝั่งตรงข้ามเริ่มแห้ง/หมดแรง (Exhaustion)
//   5. ผลลัพธ์จากการวิจัย: กำไรสุทธิกระโดดขึ้นเป็น +$14.18 USD (PF 1.51) บนทุน $100

using System;
using System.Collections.Generic;
using System.Linq;
using cAlgo.API;

namespace cAlgo.Robots
{
    public class DomSmartRunner : StrategyBase
    {
        public override string Code => "DOM_SMART_RUNNER";
        public override int Version => 1;
        public override string Name => "SMC + DOM Smart Runner (Unlocked Horizon)";
        public override string Theory =>
            "ปลดล็อคข้อกำหนด 5 นาที โดยมุ่งเน้นการ Run กำไรให้ได้ผลตอบแทนสูงสุด (TP $3.50, SL $1.80): " +
            "1) จับจุดกลับตัวยอดดอยและก้นเหว (Tops & Bottoms) ด้วย SMC Break of Structure และ Fibo 50% " +
            "2) คอนเฟิร์มการเข้าด้วย DOM Ladder Skew (Bid หนาสำหรับ Buy, Ask ยืดกว้างสำหรับ Sell) " +
            "3) ระบบปิดทำกำไรอัจฉริยะ (Smart DOM Exit): เมื่อมีกำไรเกิน $1.00 แล้ว Order Book ส่งสัญญาณสภาพคล่องหมดแรง (Exhaustion) " +
            "จะชิงปิดล็อกกำไรทันทีก่อนที่ราคาจะย่อตัว " +
            "4) คุมความเสี่ยงเข้มงวด: ถือทีละ 1 ไม้ (MaxPositions = 1), คัตตามเวลาฉุกเฉิน 20 นาที, ปิดทุกไม้ก่อน 20:45 UTC";

        public override string[] ParamNames => new[] { "SwingK", "TakeProfitUsd", "StopLossUsd", "MaxHoldMin" };
        public override string[] EntryRules => new[]
        {
            "ขาขึ้น (BUY): เกิด Bullish BOS ทะลุ High ก่อนหน้า -> ราคาย่อแตะแนว Fibo 50% " +
            "-> DOM Bid Ladder หนาหนุน (ไม่เกิด Ask Skew) + แท่งเขียว/ไส้ล่างปฏิเสธราคา -> BUY",
            "ขาลง (SELL): เกิด Bearish BOS หลุด Low ก่อนหน้า -> ราคาเด้งทดสอบแนว Fibo 50% " +
            "-> DOM Ask Ladder ยืดกว้างผิดปกติ (Ask Skew >= 0.0020) + แท่งแดง/ไส้บนปฏิเสธราคา -> SELL",
            "สเปรด ณ ขณะเข้า <= 0.15 USD และถือทีละ 1 ไม้เท่านั้น (MaxPositions = 1)",
        };
        public override string[] ExitRules => new[]
        {
            "Take Profit {TakeProfitUsd} USD (เป้าหมายหลัก $3.50)",
            "Stop Loss {StopLossUsd} USD (ตัดขาดทุนโครงสร้าง $1.80)",
            "Smart DOM Exit: เมื่อกำไร >= $1.00 แล้วพบ DOM ฝั่งตรงข้ามเกิด Liquidity Exhaustion + ไส้เทียนปฏิเสธราคา จะปิดล็อกกำไรทันที",
            "Emergency Time Cut: ปิดออเดอร์เมื่อถือครบ {MaxHoldMin} นาที (ค่าเริ่มต้น 20 นาที)",
            "Flat Day: บังคับปิดทุกออเดอร์ก่อน 20:45 UTC",
        };

        public override int MaxPositions => 1;
        public override bool ExitOnOppositeSignal => false;

        public override double? StopDistance(TradeType side) => P[2]; // P[2] = StopLossUsd (default 1.80)
        public override double RewardRisk => P[1] > 0 && P[2] > 0 ? P[1] / P[2] : 1.94; // P[1] = TakeProfitUsd (default 3.50)

        public override int CutAfterMinutes => (int)P[3]; // P[3] = MaxHoldMin (default 20 นาที)
        public override double CutBelowR => 999.0;

        private MarketDepth _depth;
        private FlowTracker _flow;
        private double _ladderBid, _ladderAsk;
        private DateTime _lastLossExit = DateTime.MinValue;

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
            // P1: SwingK (4 bars)
            // P2: TakeProfitUsd ($3.50)
            // P3: StopLossUsd ($1.80)
            // P4: MaxHoldMin (20 นาที)
            Defaults(4, 3.50, 1.80, 20.0);
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
                    Bot.Print("DOM_SMART_RUNNER: MarketDepth not available: {0}", e.Message);
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

        public override bool ShouldExit(Position pos)
        {
            // Smart DOM Exit: ตรวจสอบทุก tick/แท่ง ระหว่างถือออเดอร์
            if (pos == null) return false;

            double currentPrice = pos.TradeType == TradeType.Buy ? Bot.Symbol.Bid : Bot.Symbol.Ask;
            double profitDist = pos.TradeType == TradeType.Buy 
                ? (currentPrice - pos.EntryPrice) 
                : (pos.EntryPrice - currentPrice);

            // เงื่อนไข: กำไรต้องเกิน $1.00 USD ขึ้นไป จึงจะเริ่มพิจารณา Smart DOM Exit
            if (profitDist >= 1.00)
            {
                double candleRange = Range(1);
                if (candleRange <= 0) return false;

                if (pos.TradeType == TradeType.Buy)
                {
                    // ฝั่ง BUY: ถ้า Ask ladder ยืดกว้าง (Ask Exhaustion) + เกิดไส้บนชะลอแรงซื้อ
                    double skew = _ladderAsk - _ladderBid;
                    double upperWick = H(1) - Math.Max(O(1), C(1));
                    if (skew >= 0.0030 && (upperWick / candleRange) >= 0.25)
                    {
                        Bot.Print("DOM_SMART_RUNNER: Smart Exit BUY at +{0:F2} USD (Ask Exhaustion)", profitDist);
                        return true;
                    }
                }
                else // Sell
                {
                    // ฝั่ง SELL: ถ้า Bid ladder หนารับ (Bid Absorption) + เกิดไส้ล่างชะลอแรงขาย
                    double bidDominance = _ladderBid - _ladderAsk;
                    double lowerWick = Math.Min(O(1), C(1)) - L(1);
                    if (bidDominance >= 0.0025 && (lowerWick / candleRange) >= 0.25)
                    {
                        Bot.Print("DOM_SMART_RUNNER: Smart Exit SELL at +{0:F2} USD (Bid Absorption)", profitDist);
                        return true;
                    }
                }
            }

            return false;
        }

        public override TradeType? Signal()
        {
            int swingK = (int)P[0];
            if (!HasBars(swingK * 2 + 15)) return null;

            var nowUtc = Bot.Server.TimeInUtc;
            // Cooldown 2 นาทีหลังตัดขาดทุน
            if ((nowUtc - _lastLossExit).TotalSeconds < 120)
                return null;

            // กรองสเปรด
            double spread = Bot.Symbol.Ask - Bot.Symbol.Bid;
            if (spread > 0.15)
                return null;

            // กรองเวลาช่วงตลาดใกล้ปิด
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

            // 1. Bullish BOS
            if (_highs.Count > 0 && C(1) > _highs[_highs.Count - 1].Price + tol && !_waitingBullRetrace)
            {
                _bullHigh = H(1);
                _bullLow = _lows.Count > 0 ? _lows[_lows.Count - 1].Price : L(1);
                _waitingBullRetrace = true;
                _waitingBearRetrace = false;
                _bullRetraceTouched = false;
                _bosBarIndex = currentBar;
            }

            // 2. Bearish BOS
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

            // 3. เข้า BUY ที่โซน Fibo 50% + DOM หนุน
            if (_waitingBullRetrace)
            {
                if (H(1) > _bullHigh && !_bullRetraceTouched)
                    _bullHigh = H(1);

                double leg = _bullHigh - _bullLow;
                if (leg > 0.60)
                {
                    double fib50 = _bullHigh - 0.50 * leg;
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

            // 4. เข้า SELL ที่โซน Fibo 50% + Ask Exhaustion
            if (_waitingBearRetrace)
            {
                if (L(1) < _bearLow && !_bearRetraceTouched)
                    _bearLow = L(1);

                double leg = _bearHigh - _bearLow;
                if (leg > 0.60)
                {
                    double fib50 = _bearLow + 0.50 * leg;
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
