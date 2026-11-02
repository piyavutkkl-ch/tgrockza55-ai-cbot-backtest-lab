// QUANT_EXTREME_REVERSAL: Extreme Deviation Reversal cBot Strategy
// รวบรวมองค์ความรู้จากงานวิจัยและผลการทดสอบ Multi-Year 2022 - 2026 (1,675,835 แท่ง M1 ทองคำ XAUUSD):
//   - Strategy A: Extreme Deviation Reversal (Anchored VWAP + Microstructure Rejection)
//   - arXiv:2412.19245 (News & Volatility Void Gate: กรองแท่งกระจายตัวผิดปกติ)
//   - Parameter Optimization (SD >= 3.5 - 4.2, NY Session 13:00-17:00 UTC)
//   - Mean Reversion Target: ออกเมื่อราคาวกกลับมาแตะ Session VWAP หรือหมดเวลา 60 นาที

using System;
using System.Globalization;
using cAlgo.API;
using cAlgo.API.Internals;

namespace cAlgo.Robots
{
    public class QuantExtremeReversal : StrategyBase
    {
        public override string Code => "QUANT_EXTREME_REVERSAL";
        public override int Version => 1;
        public override string Name => "Quant Extreme Deviation Reversal (Anchored VWAP Mean Reversion)";
        public override string Theory =>
            "กลยุทธ์ Mean Reversion ทางสถิติขั้นสูงสำหรับทองคำ (XAUUSD): " +
            "1) คำนวณ Session Anchored VWAP และ Dynamic Standard Deviation Band แบบสะสมในแต่ละวัน " +
            "2) เมื่อราคาถูกดึงยืดออกนอกกรอบอย่างรุนแรง (Deviation >= {SdMultiplier} SD) ในช่วงตลาด New York (13:00-17:00 UTC) " +
            "3) กรองแท่งผิดปกติช่วงข่าวแรง (News Void Filter: ขนาดแท่งไม่เกิน {MaxAtrBar}x ATR) " +
            "4) จุดทำกำไรหลัก (Target): ปิดทันทีเมื่อราคาวกกลับมาสัมผัสเส้น Anchored VWAP หรือครบ {MaxHoldMinutes} นาที";

        public override string[] ParamNames => new[] { "SdMultiplier", "SlAtrMultiplier", "MaxHoldMinutes", "MaxAtrBar" };
        public override string[] EntryRules => new[]
        {
            "เวลา 13:00 - 17:00 UTC (New York Liquidity Session):",
            "ราคาปิดต่ำกว่า Anchored VWAP เกิน {SdMultiplier} SD และแท่งเทียนมีการปฏิเสธราคา (Wick Rejection) -> BUY",
            "ราคาปิดสูงกว่า Anchored VWAP เกิน {SdMultiplier} SD และแท่งเทียนมีการปฏิเสธราคา (Wick Rejection) -> SELL",
            "กรองข่าว/ความผันผวนผิดปกติ: ขนาดแท่ง (High - Low) ต้องไม่เกิน {MaxAtrBar}x ATR",
            "ไม่เข้าออเดอร์ซ้อน (MaxPositions = 1)"
        };
        public override string[] ExitRules => new[]
        {
            "ทำกำไรสมบูรณ์ (Mean Reversion Target): ราคาข้ามกลับมาสัมผัส Session VWAP สั่งปิดทันที",
            "Stop Loss ป้องกันความเสี่ยงตามโครงสร้าง: {SlAtrMultiplier}x ATR",
            "Time Stop: หากถือครองเกิน {MaxHoldMinutes} นาทีแล้วยังไม่ถึงเป้า ให้สั่งปิดทันที"
        };

        public override int MaxPositions => 1;
        public override bool ExitOnOppositeSignal => true;
        public override double RewardRisk => 2.5; // สำรองกรณีไม่แตะ VWAP

        // Parameters
        private double _sdMultiplier = 3.5;
        private double _slAtrMultiplier = 2.0;
        private int _maxHoldMinutes = 60;
        private double _maxAtrBar = 2.0;

        // State Tracking
        private DateTime _currentDay = DateTime.MinValue;
        private double _sumPv = 0.0;
        private double _sumP2v = 0.0;
        private double _sumV = 0.0;
        private double _currentVwap = 0.0;
        private double _currentSd = 1.0;
        private double _currentAtr = 1.5;

        private TradeType? _pendingSignal = null;
        private double _lastStopDistance = 3.0;

        protected override void OnInit()
        {
            Defaults(3.5, 2.0, 60.0, 2.0);
            _sdMultiplier = P[0] > 0 ? P[0] : 3.5;
            _slAtrMultiplier = P.Length > 1 && P[1] > 0 ? P[1] : 2.0;
            _maxHoldMinutes = P.Length > 2 && P[2] > 0 ? (int)P[2] : 60;
            _maxAtrBar = P.Length > 3 && P[3] > 0 ? P[3] : 2.0;

            ResetDailyVwap(Bot.Server.Time.Date);
        }

        private void ResetDailyVwap(DateTime day)
        {
            _currentDay = day;
            _sumPv = 0.0;
            _sumP2v = 0.0;
            _sumV = 0.0;
            _currentVwap = 0.0;
            _currentSd = 1.0;
        }

        public override double? StopDistance(TradeType side)
        {
            return _lastStopDistance > 0 ? _lastStopDistance : 3.0;
        }

        public override TradeType? Signal()
        {
            if (Bot.Bars.Count < 50) return null;

            int lastIdx = Bot.Bars.Count - 2; // แท่งที่เพิ่งปิดสมบูรณ์
            var barTime = Bot.Bars.OpenTimes[lastIdx];
            double c = Bot.Bars.ClosePrices[lastIdx];
            double h = Bot.Bars.HighPrices[lastIdx];
            double l = Bot.Bars.LowPrices[lastIdx];
            double v = Math.Max(Bot.Bars.TickVolumes[lastIdx], 1.0);

            // 1. Reset VWAP เมื่อขึ้นวันใหม่
            if (barTime.Date != _currentDay)
            {
                ResetDailyVwap(barTime.Date);
            }

            // 2. ปรับปรุง Anchored VWAP & SD
            double p = (h + l + c) / 3.0;
            _sumPv += p * v;
            _sumP2v += (p * p) * v;
            _sumV += v;

            if (_sumV > 0)
            {
                _currentVwap = _sumPv / _sumV;
                double variance = Math.Max((_sumP2v / _sumV) - (_currentVwap * _currentVwap), 0.01);
                _currentSd = Math.Sqrt(variance);
            }

            // 3. ปรับปรุง ATR แบบ Exponential Smoothed
            double prevClose = Bot.Bars.ClosePrices[Math.Max(0, lastIdx - 1)];
            double tr = Math.Max(h - l, Math.Max(Math.Abs(h - prevClose), Math.Abs(l - prevClose)));
            _currentAtr = 0.95 * _currentAtr + 0.05 * tr;

            // 4. ตรวจสอบชั่วโมงตลาด New York Active (13:00 - 17:00 UTC = 20:00 - 00:00 น. เวลาไทย)
            int hourUtc = barTime.Hour;
            bool isNySession = (hourUtc >= 13 && hourUtc <= 17);
            if (!isNySession) return null;

            // 5. ข่าว & Volatility Void Gate: กรองแท่งข่าวที่มีขนาดใหญ่ผิดปกติ
            if ((h - l) > _maxAtrBar * _currentAtr)
            {
                return null;
            }

            // 6. ตรวจจับการยืดออกทางสถิติขั้นรุนแรง (Extreme Deviation)
            double deviation = c - _currentVwap;
            double threshold = _sdMultiplier * Math.Max(_currentSd, 1.0);

            _lastStopDistance = _slAtrMultiplier * Math.Max(_currentAtr, 1.2);

            // BUY Signal: ราคาหลุดล่างรุนแรง + แท่งเทียนปิดมีไส้ล่าง (Buyers Absorbing)
            if (deviation <= -threshold)
            {
                bool lowerRejection = (c > l + 0.25 * (h - l));
                if (lowerRejection)
                {
                    _pendingSignal = TradeType.Buy;
                    return TradeType.Buy;
                }
            }
            // SELL Signal: ราคาหลุดบนรุนแรง + แท่งเทียนปิดมีไส้บน (Sellers Absorbing)
            else if (deviation >= threshold)
            {
                bool upperRejection = (c < h - 0.25 * (h - l));
                if (upperRejection)
                {
                    _pendingSignal = TradeType.Sell;
                    return TradeType.Sell;
                }
            }

            return null;
        }

        public override bool ShouldExit(Position position)
        {
            if (position == null) return false;

            double currentPrice = position.TradeType == TradeType.Buy ? Bot.Symbol.Bid : Bot.Symbol.Ask;

            // 1. Mean Reversion Target: ถ้าราคาวกกลับมาสัมผัสเส้น Anchored Session VWAP ให้ปิดทำกำไรทันที
            if (_currentVwap > 0)
            {
                if (position.TradeType == TradeType.Buy && currentPrice >= _currentVwap)
                {
                    Bot.Print("QUANT_EXTREME_REVERSAL: BUY target reached at Anchored VWAP {0:F2}. Closing position.", _currentVwap);
                    return true;
                }
                if (position.TradeType == TradeType.Sell && currentPrice <= _currentVwap)
                {
                    Bot.Print("QUANT_EXTREME_REVERSAL: SELL target reached at Anchored VWAP {0:F2}. Closing position.", _currentVwap);
                    return true;
                }
            }

            // 2. Time-Based Exit: หากถือครองเกินกำหนด ให้ปิดออเดอร์เพื่อจำกัดความเสี่ยง
            var duration = Bot.Server.Time - position.EntryTime;
            if (duration.TotalMinutes >= _maxHoldMinutes)
            {
                Bot.Print("QUANT_EXTREME_REVERSAL: Max hold time {0} mins exceeded. Closing position.", _maxHoldMinutes);
                return true;
            }

            return false;
        }
    }
}
