// ==================================================================================================
// QuantExtremeReversal (Standalone cBot for cTrader Automate)
// Target Asset: XAU/USD (Gold) on Pepperstone cTrader
// Developed from Deep Quantitative Research & Multi-Year Backtest (2022 - 2026, 1,675,835 M1 Bars)
// ==================================================================================================

using System;
using System.Linq;
using cAlgo.API;
using cAlgo.API.Internals;

namespace cAlgo.Robots
{
    [Robot(TimeZone = TimeZones.UTC, AccessRights = AccessRights.None)]
    public class QuantExtremeReversalStandalone : Robot
    {
        [Parameter("Strategy Name", Group = "System Info", DefaultValue = "Extreme Deviation Reversal (Gold)")]
        public string StrategyInfo { get; set; }

        [Parameter("Volume (Lots)", Group = "Risk Management", DefaultValue = 0.01, MinValue = 0.01, Step = 0.01)]
        public double VolumeLots { get; set; }

        [Parameter("SD Stretch Multiplier", Group = "Strategy A Parameters", DefaultValue = 3.8, MinValue = 2.0, MaxValue = 5.0, Step = 0.2)]
        public double SdMultiplier { get; set; }

        [Parameter("Stop Loss ATR Multiplier", Group = "Strategy A Parameters", DefaultValue = 2.0, MinValue = 1.0, MaxValue = 4.0, Step = 0.5)]
        public double SlAtrMultiplier { get; set; }

        [Parameter("Max Hold Minutes", Group = "Strategy A Parameters", DefaultValue = 60, MinValue = 15, MaxValue = 180, Step = 15)]
        public int MaxHoldMinutes { get; set; }

        [Parameter("Max Bar ATR (News Gate)", Group = "Filters", DefaultValue = 2.0, MinValue = 1.0, MaxValue = 4.0, Step = 0.5)]
        public double MaxBarAtr { get; set; }

        [Parameter("Start Hour UTC", Group = "Session Window", DefaultValue = 13, MinValue = 0, MaxValue = 23)]
        public int StartHourUtc { get; set; }

        [Parameter("End Hour UTC", Group = "Session Window", DefaultValue = 17, MinValue = 0, MaxValue = 23)]
        public int EndHourUtc { get; set; }

        // VWAP Accumulator State
        private DateTime _currentDay = DateTime.MinValue;
        private double _sumPv = 0.0;
        private double _sumP2v = 0.0;
        private double _sumV = 0.0;
        private double _currentVwap = 0.0;
        private double _currentSd = 1.0;
        private double _currentAtr = 1.5;

        protected override void OnStart()
        {
            Print("QuantExtremeReversal cBot Started successfully on {0}", SymbolName);
            ResetDailyVwap(Server.Time.Date);
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

        protected override void OnBar()
        {
            if (Bars.Count < 50) return;

            int lastIdx = Bars.Count - 2; // Previous completed bar
            var barTime = Bars.OpenTimes[lastIdx];
            double c = Bars.ClosePrices[lastIdx];
            double h = Bars.HighPrices[lastIdx];
            double l = Bars.LowPrices[lastIdx];
            double v = Math.Max(Bars.TickVolumes[lastIdx], 1.0);

            // 1. Daily Reset for Session Anchored VWAP
            if (barTime.Date != _currentDay)
            {
                ResetDailyVwap(barTime.Date);
            }

            // 2. Accumulate Volume-Weighted Price
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

            // 3. Update ATR (True Range Exponential Smoothing)
            double prevClose = Bars.ClosePrices[Math.Max(0, lastIdx - 1)];
            double tr = Math.Max(h - l, Math.Max(Math.Abs(h - prevClose), Math.Abs(l - prevClose)));
            _currentAtr = 0.95 * _currentAtr + 0.05 * tr;

            // 4. Session Filter: New York Active Liquidity Window (13:00 - 17:00 UTC)
            int hourUtc = barTime.Hour;
            bool inSession = (hourUtc >= StartHourUtc && hourUtc <= EndHourUtc);
            if (!inSession) return;

            // 5. News & Volatility Void Gate: Filter out erratic slippage bars
            if ((h - l) > MaxBarAtr * _currentAtr)
            {
                return;
            }

            // 6. Check Positions (Only 1 active position at a time)
            var currentPos = Positions.Find("QuantExtremeReversal", SymbolName);
            if (currentPos != null) return;

            // 7. Extreme Statistical Deviation Calculation
            double deviation = c - _currentVwap;
            double threshold = SdMultiplier * Math.Max(_currentSd, 1.0);
            double slDistance = SlAtrMultiplier * Math.Max(_currentAtr, 1.2);

            // BUY Signal: Price stretched far below VWAP + Absorption wick rejection
            if (deviation <= -threshold)
            {
                bool lowerRejection = (c > l + 0.25 * (h - l));
                if (lowerRejection)
                {
                    double slPrice = Symbol.Ask - slDistance;
                    ExecuteOrder(TradeType.Buy, slPrice);
                }
            }
            // SELL Signal: Price stretched far above VWAP + Absorption wick rejection
            else if (deviation >= threshold)
            {
                bool upperRejection = (c < h - 0.25 * (h - l));
                if (upperRejection)
                {
                    double slPrice = Symbol.Bid + slDistance;
                    ExecuteOrder(TradeType.Sell, slPrice);
                }
            }
        }

        private void ExecuteOrder(TradeType tradeType, double stopLossPrice)
        {
            var volumeInUnits = Symbol.QuantityToVolumeInUnits(VolumeLots);
            var result = ExecuteMarketOrder(tradeType, SymbolName, volumeInUnits, "QuantExtremeReversal", stopLossPrice, null);

            if (result.IsSuccessful)
            {
                Print("ORDER EXECUTED: {0} {1} Lots at {2:F2}, SL={3:F2}, VWAP={4:F2}",
                    tradeType, VolumeLots, result.Position.EntryPrice, stopLossPrice, _currentVwap);
            }
        }

        protected override void OnTick()
        {
            var position = Positions.Find("QuantExtremeReversal", SymbolName);
            if (position == null) return;

            double currentPrice = position.TradeType == TradeType.Buy ? Symbol.Bid : Symbol.Ask;

            // 1. Mean Reversion Target: Exit immediately when price touches Anchored VWAP equilibrium
            if (_currentVwap > 0)
            {
                if (position.TradeType == TradeType.Buy && currentPrice >= _currentVwap)
                {
                    Print("TARGET REACHED: BUY closed at Anchored VWAP {0:F2}", _currentVwap);
                    ClosePosition(position);
                    return;
                }
                if (position.TradeType == TradeType.Sell && currentPrice <= _currentVwap)
                {
                    Print("TARGET REACHED: SELL closed at Anchored VWAP {0:F2}", _currentVwap);
                    ClosePosition(position);
                    return;
                }
            }

            // 2. Time-Based Stop: Max hold duration reached
            var holdTime = Server.Time - position.EntryTime;
            if (holdTime.TotalMinutes >= MaxHoldMinutes)
            {
                Print("TIME STOP: Max hold duration {0} mins reached. Closing position.", MaxHoldMinutes);
                ClosePosition(position);
            }
        }
    }
}
