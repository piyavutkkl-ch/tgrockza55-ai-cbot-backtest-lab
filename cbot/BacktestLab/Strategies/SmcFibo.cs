using System;
using System.Globalization;
using System.IO;
using System.Linq;
using cAlgo.API;
using File = System.IO.File;

namespace cAlgo.Robots
{
    public class SmcFibo : StrategyBase
    {
        public override string Code => "CH_SMC_FIBO";
        public override string Name => "SMC โครงสร้างตลาด + Fibo Golden Zone (5 สเต็ป) + VWAP";
        public override string Theory =>
            "กลยุทธ์ตามโครงสร้างตลาด Smart Money Concepts รวมกับ Fibonacci Golden Zone (0.50-0.65) และ VWAP: " +
            "1) รอเกิด Break of Structure (BOS) ยืนยันแนวโน้มขาขึ้นหรือขาลง " +
            "2) กาง Fibonacci จากจุด Low/High ของขา BOS แล้วรอราคาย่อตัวเข้าสู่ Golden Zone (0.50 - 0.65) " +
            "3) กรองด้วยเส้น VWAP (Buy เมื่อราคายืนเหนือ VWAP, Sell เมื่อราคาอยู่ใต้ VWAP และไม่เทรดตอนตลาด Chop) " +
            "4) ยืนยันสัญญาณด้วยแท่งเทียนกลับตัว (Reversal Candle / Rejection) " +
            "5) หลีกเลี่ยงช่วงข่าวแรง (High Impact News) ตามข้อมูล events.csv และจำกัดเทรดช่วง London & NY Core (07:00 - 16:00 UTC) " +
            "6) วาง Stop Loss ตามโครงสร้างราคา (ใต้ Low หรือเหนือ High ของขา BOS) และตั้ง Take Profit {RR} เท่า " +
            "7) ปล่อยให้รันจนถึง TP หรือ SL (ไม่ปิดออเดอร์ด้วยสัญญาณย่อยตรงข้าม) และเลื่อน SL กันทุนเมื่อกำไรถึง 1R";

        public override string[] ParamNames => new[] { "SwingK", "FibMin", "FibMax", "RR" };

        public override string[] EntryRules => new[]
        {
            "1. ขาขึ้น: ราคาปิดทะลุ Swing High ล่าสุด (BOS ขาขึ้น) บันทึก Low ของขาและ High ใหม่",
            "2. ราคาย่อตัวลงมาแตะ Fibonacci Golden Zone ({FibMin} - {FibMax}) ระหว่าง Low และ High ของขา",
            "3. แท่งเทียนกลับตัวเขียว (Reversal/Rejection) ปิดเหนือโซน และราคายืนเหนือเส้น VWAP (ฝั่งซื้อคุมตลาด) → Buy",
            "4. ขาลง: ราคาปิดหลุด Swing Low ล่าสุด (BOS ขาลง) แล้วเด้งทดสอบ Golden Zone + แท่งกลับตัวแดงใต้ VWAP → Sell",
            "5. เข้าเทรดเฉพาะช่วงที่มีสภาพคล่องสูง (07:00 - 16:00 UTC) และไม่เข้า 30 นาทีก่อนข่าวแรง หรือ 60 นาทีหลังข่าว",
        };

        public override string[] ExitRules => new[]
        {
            "SL: วางใต้ Low ล่าสุดของขา (สำหรับ Buy) หรือเหนือ High ล่าสุด (สำหรับ Sell)",
            "TP: {RR} เท่าของระยะ SL (ตามแนวคิด Risk:Reward 1:2.5 ถึง 1:3)",
            "Breakeven: เมื่อกำไรถึง 1.0R เลื่อน SL มาที่ราคาเข้าเพื่อคุ้มครองทุน",
            "ไม่ปิดออเดอร์ก่อนเวลาเมื่อมีสัญญาณตรงข้าม เพื่อปล่อยให้ R:R ทำงานเต็มที่",
        };

        public override bool ExitOnOppositeSignal => false;
        public override double RewardRisk => P[3];
        public override double BreakevenAtR => 1.0;
        public override double? StopDistance(TradeType side) => _lastStopDistance;

        private SwingTracker _swings;
        private readonly FlowTracker _flow = new FlowTracker();
        private long[] _events = new long[0];

        private double _lastStopDistance;
        private int _bullishBosHighIndex = -1;
        private int _bearishBosLowIndex = -1;
        private int _bullishBosBar = -1;
        private int _bearishBosBar = -1;
        private double _bullishLow, _bullishHigh;
        private double _bearishHigh, _bearishLow;
        private bool _waitingBullishRetrace, _bullishRetraceTouched;
        private bool _waitingBearishRetrace, _bearishRetraceTouched;

        private static long Unix(DateTime t) =>
            new DateTimeOffset(DateTime.SpecifyKind(t, DateTimeKind.Utc)).ToUnixTimeSeconds();

        protected override void OnInit()
        {
            // P1: SwingK (default 5 bars)
            // P2: FibMin (default 0.50)
            // P3: FibMax (default 0.65)
            // P4: RR (default 3.0)
            Defaults(5, 0.50, 0.65, 3.0);
            _swings = new SwingTracker(Bot.Bars, (int)P[0]);

            // โหลดประวัติข่าวเพื่อกรองจังหวะผันผวนรุนแรง
            var eventFile = Path.Combine(Reporter.Folder, "data", "news", "events.csv");
            if (File.Exists(eventFile))
            {
                try
                {
                    _events = File.ReadAllLines(eventFile).Skip(1).Select(l => l.Split(','))
                        .Where(p => p.Length >= 3 && (p[2] == "HIGH" || p[2] == "EXTREME"))
                        .Select(p => long.Parse(p[0], CultureInfo.InvariantCulture)).OrderBy(t => t).ToArray();
                }
                catch { }
            }
        }

        public override void OnTick()
        {
            _flow.Feed(Unix(Bot.Server.Time), Bot.Symbol.Bid, Bot.Symbol.Ask);
        }

        private bool NearNews(long now)
        {
            if (_events.Length == 0) return false;
            int k = Array.BinarySearch(_events, now);
            if (k < 0) k = ~k;
            if (k < _events.Length && _events[k] - now <= 30 * 60) return true;
            return k > 0 && now - _events[k - 1] < 60 * 60;
        }

        private double GetVwap()
        {
            if (!double.IsNaN(_flow.DayVwap) && _flow.DayVwap > 0)
                return _flow.DayVwap;

            var today = TradingDay(Bot.Bars.OpenTimes.Last(1));
            double sumPV = 0;
            double sumV = 0;
            for (int i = 1; i < Bot.Bars.Count - 1 && i < 600; i++)
            {
                if (TradingDay(Bot.Bars.OpenTimes.Last(i)) != today) break;
                double tp = (H(i) + L(i) + C(i)) / 3.0;
                double vol = Bot.Bars.TickVolumes.Last(i);
                if (vol <= 0) vol = 1;
                sumPV += tp * vol;
                sumV += vol;
            }
            return sumV > 0 ? (sumPV / sumV) : double.NaN;
        }

        private bool IsChoppy(double vwap)
        {
            if (double.IsNaN(vwap)) return false;
            int crosses = 0;
            for (int i = 1; i <= 8 && i < Bot.Bars.Count - 2; i++)
            {
                bool abovePrev = C(i + 1) > vwap;
                bool aboveCurr = C(i) > vwap;
                if (abovePrev != aboveCurr) crosses++;
            }
            return crosses >= 3;
        }

        public override TradeType? Signal()
        {
            if (!HasBars(30)) return null;

            _swings.Update();
            var now = _swings.LastClosedIndex;
            var time = Bot.Bars.OpenTimes.Last(1);

            // กรองเวลา: 07:00 - 16:00 UTC (London & early NY - ช่วงที่เทรนด์คุณภาพสูงสุด)
            bool inSession = (time.Hour >= 7 && time.Hour < 16);
            if (NearNews(Unix(time) + 60)) return null;

            var tol = C(1) * 0.0003;
            double vwap = GetVwap();
            bool choppy = IsChoppy(vwap);

            // 1. ตรวจสอบ Bullish BOS
            if (_swings.Highs.Count > 0)
            {
                var lastHigh = _swings.Highs[_swings.Highs.Count - 1];
                if (lastHigh.Index != _bullishBosHighIndex && C(1) > lastHigh.Price + tol)
                {
                    _bullishBosHighIndex = lastHigh.Index;
                    _bullishBosBar = now;
                    _bullishHigh = H(1);

                    double legLow = lastHigh.Price;
                    if (_swings.Lows.Count > 0)
                    {
                        var lastLow = _swings.Lows[_swings.Lows.Count - 1];
                        legLow = _swings.LowestBetween(Math.Max(0, lastLow.Index), now);
                    }
                    else
                    {
                        legLow = LowestLow(1, 15);
                    }
                    _bullishLow = legLow;
                    _waitingBullishRetrace = true;
                    _bullishRetraceTouched = false;
                }
            }

            // 2. ตรวจสอบ Bearish BOS
            if (_swings.Lows.Count > 0)
            {
                var lastLow = _swings.Lows[_swings.Lows.Count - 1];
                if (lastLow.Index != _bearishBosLowIndex && C(1) < lastLow.Price - tol)
                {
                    _bearishBosLowIndex = lastLow.Index;
                    _bearishBosBar = now;
                    _bearishLow = L(1);

                    double legHigh = lastLow.Price;
                    if (_swings.Highs.Count > 0)
                    {
                        var lastHigh = _swings.Highs[_swings.Highs.Count - 1];
                        legHigh = _swings.HighestBetween(Math.Max(0, lastHigh.Index), now);
                    }
                    else
                    {
                        legHigh = HighestHigh(1, 15);
                    }
                    _bearishHigh = legHigh;
                    _waitingBearishRetrace = true;
                    _bearishRetraceTouched = false;
                }
            }

            // 3. รอ Retracement ฝั่ง Buy
            if (_waitingBullishRetrace)
            {
                if (H(1) > _bullishHigh && !_bullishRetraceTouched)
                {
                    _bullishHigh = H(1);
                }

                double legRange = _bullishHigh - _bullishLow;
                if (legRange > tol * 3)
                {
                    double fib50 = _bullishHigh - P[1] * legRange;
                    double fibMax = _bullishHigh - P[2] * legRange;

                    if (C(1) < _bullishLow || (now - _bullishBosBar) > 60)
                    {
                        _waitingBullishRetrace = false;
                    }
                    else
                    {
                        if (L(1) <= fib50 && L(1) >= _bullishLow - tol)
                        {
                            _bullishRetraceTouched = true;
                        }

                        if (_bullishRetraceTouched && inSession)
                        {
                            bool isGreen = C(1) > O(1);
                            bool holdsZone = C(1) >= fibMax;
                            double lowerWick = Math.Min(O(1), C(1)) - L(1);
                            bool rejection = lowerWick >= Body(1) * 0.5 || C(1) > H(2);

                            bool vwapOk = double.IsNaN(vwap) || C(1) >= vwap - tol;

                            if (isGreen && holdsZone && rejection && vwapOk && !choppy)
                            {
                                _waitingBullishRetrace = false;
                                double stopPrice = _bullishLow - tol;
                                double dist = C(1) - stopPrice;
                                if (dist > 0)
                                {
                                    _lastStopDistance = dist;
                                    return TradeType.Buy;
                                }
                            }
                        }
                    }
                }
            }

            // 4. รอ Retracement ฝั่ง Sell
            if (_waitingBearishRetrace)
            {
                if (L(1) < _bearishLow && !_bearishRetraceTouched)
                {
                    _bearishLow = L(1);
                }

                double legRange = _bearishHigh - _bearishLow;
                if (legRange > tol * 3)
                {
                    double fib50 = _bearishLow + P[1] * legRange;
                    double fibMax = _bearishLow + P[2] * legRange;

                    if (C(1) > _bearishHigh || (now - _bearishBosBar) > 60)
                    {
                        _waitingBearishRetrace = false;
                    }
                    else
                    {
                        if (H(1) >= fib50 && H(1) <= _bearishHigh + tol)
                        {
                            _bearishRetraceTouched = true;
                        }

                        if (_bearishRetraceTouched && inSession)
                        {
                            bool isRed = C(1) < O(1);
                            bool holdsZone = C(1) <= fibMax;
                            double upperWick = H(1) - Math.Max(O(1), C(1));
                            bool rejection = upperWick >= Body(1) * 0.5 || C(1) < L(2);

                            bool vwapOk = double.IsNaN(vwap) || C(1) <= vwap + tol;

                            if (isRed && holdsZone && rejection && vwapOk && !choppy)
                            {
                                _waitingBearishRetrace = false;
                                double stopPrice = _bearishHigh + tol;
                                double dist = stopPrice - C(1);
                                if (dist > 0)
                                {
                                    _lastStopDistance = dist;
                                    return TradeType.Sell;
                                }
                            }
                        }
                    }
                }
            }

            return null;
        }
    }
}
