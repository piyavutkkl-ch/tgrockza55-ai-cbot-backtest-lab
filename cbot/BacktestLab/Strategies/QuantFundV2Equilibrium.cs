// Antigravity Trading Platform V2 — Auto-Generated Strategy
// Code: QF_V2_VWAP_EQUILIBRIUM | Class: QuantFundV2Equilibrium
using System;
using cAlgo.API;

namespace cAlgo.Robots
{
    public class QuantFundV2Equilibrium : StrategyBase
    {
        public override string Code => "QF_V2_VWAP_EQUILIBRIUM";
        public override int Version => 2;
        public override string Name => "Antigravity V2 Institutional VWAP Equilibrium (QF_V2_VWAP_EQUILIBRIUM)";
        public override string Theory =>
            "Build (AI) -> Prove (Math) -> Protect (Rules): Session Anchored VWAP Extreme Reversion " +
            "(>= 4.2 SD) in NY Window (13:00-17:00 UTC) with News Void Gate (2.0x ATR).";

        public override string[] ParamNames => new[] { "SdMultiplier", "SlAtrMultiplier", "MaxHoldMinutes", "MaxAtrBar" };
        public override string[] EntryRules => new[]
        {
            "13:00 - 17:00 UTC New York Session",
            "Anchored VWAP Stretch >= 4.2 SD + 15-bar extreme",
            "News Void Gate: Bar range <= 2.0x ATR"
        };
        public override string[] ExitRules => new[]
        {
            "Equilibrium Target: VWAP_TOUCH at Session VWAP",
            "Hard Structural Stop Loss: 2.0x ATR clamped to risk policy",
            "Time Stop: 60 minutes"
        };

        public override int MaxPositions => 1;
        public override bool ExitOnOppositeSignal => true;
        public override double RewardRisk => 2.5;

        private double _sdMultiplier = 4.2;
        private double _slAtrMultiplier = 2.0;
        private int _maxHoldMinutes = 60;
        private double _maxAtrBar = 2.0;

        private DateTime _currentDay = DateTime.MinValue;
        private double _sumPv = 0.0;
        private double _sumP2v = 0.0;
        private double _sumV = 0.0;
        private double _currentVwap = 0.0;
        private double _currentSd = 1.0;
        private double _currentAtr = 1.5;
        private double _lastStopDistance = 3.0;

        protected override void OnInit()
        {
            if (P != null && P.Length > 0 && P[0] > 0) _sdMultiplier = P[0];
            if (P != null && P.Length > 1 && P[1] > 0) _slAtrMultiplier = P[1];
            if (P != null && P.Length > 2 && P[2] > 0) _maxHoldMinutes = (int)P[2];
            if (P != null && P.Length > 3 && P[3] > 0) _maxAtrBar = P[3];
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
            return _lastStopDistance > 0 ? Math.Clamp(_lastStopDistance, 1.5, 4.5) : 3.0;
        }

        public override TradeType? Signal()
        {
            if (Bot.Bars.Count < 50) return null;

            int lastIdx = Bot.Bars.Count - 2;
            DateTime barTime = Bot.Bars.OpenTimes[lastIdx];
            double c = Bot.Bars.ClosePrices.Last(1);
            double h = Bot.Bars.HighPrices.Last(1);
            double l = Bot.Bars.LowPrices.Last(1);
            double v = Math.Max(Bot.Bars.TickVolumes.Last(1), 1.0);

            if (barTime.Date != _currentDay)
                ResetDailyVwap(barTime.Date);

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

            double prevClose = Bot.Bars.ClosePrices[Math.Max(0, lastIdx - 1)];
            double tr = Math.Max(h - l, Math.Max(Math.Abs(h - prevClose), Math.Abs(l - prevClose)));
            _currentAtr = 0.95 * _currentAtr + 0.05 * tr;

            if (barTime.Hour < 13 || barTime.Hour > 17)
                return null;

            if ((h - l) > _maxAtrBar * Math.Max(_currentAtr, 1.2))
                return null;

            double dev = c - _currentVwap;
            double thresh = _sdMultiplier * Math.Max(_currentSd, 1.0);
            _lastStopDistance = _slAtrMultiplier * Math.Max(_currentAtr, 1.2);

            double minLow15 = double.MaxValue;
            double maxHigh15 = double.MinValue;
            for (int k = lastIdx - 15; k < lastIdx; k++)
            {
                if (Bot.Bars.LowPrices[k] < minLow15) minLow15 = Bot.Bars.LowPrices[k];
                if (Bot.Bars.HighPrices[k] > maxHigh15) maxHigh15 = Bot.Bars.HighPrices[k];
            }

            if (dev <= -thresh && c <= minLow15)
                return TradeType.Buy;
            if (dev >= thresh && c >= maxHigh15)
                return TradeType.Sell;

            return null;
        }

        public override bool ShouldExit(Position position)
        {
            if (position == null) return false;
            double currentPrice = position.TradeType == TradeType.Buy ? Bot.Symbol.Bid : Bot.Symbol.Ask;

            if (_currentVwap > 0)
            {
                if (position.TradeType == TradeType.Buy && currentPrice >= _currentVwap)
                    return true;
                if (position.TradeType == TradeType.Sell && currentPrice <= _currentVwap)
                    return true;
            }
            if ((Bot.Server.Time - position.EntryTime).TotalMinutes >= _maxHoldMinutes)
                return true;
            return false;
        }
    }
}
