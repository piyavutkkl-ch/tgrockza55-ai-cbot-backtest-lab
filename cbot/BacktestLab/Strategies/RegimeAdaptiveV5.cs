// REGIME_ADAPTIVE_V5 (Version 3): 7-Zone Session/Transition & Regime-Matched OOS Router
// Built from System Rules V5 & Phase 2 Out-of-Sample Matrix (docs/data/regime_strategy_matrix.json)
// Wires FlowTracker (OnTick real tick delta/VWAP/SD/sweep) + MarketDepth L2 DOM
// Zero Lookahead (.Last(1) closed bars only) | Demo Quarantine Safe (#5258778)

using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using cAlgo.API;

namespace cAlgo.Robots
{
    public class RegimeAdaptiveV5 : StrategyBase
    {
        public override string Code => "REGIME_ADAPTIVE_V5";
        public override int Version => 3;
        public override string Name => "V5 7-Zone Session & Regime Adaptive Router";
        public override string Theory =>
            "เลือกกลยุทธ์และพารามิเตอร์ SL/RR/Exit แบบ Adaptive แยกตาม 7 โซนเวลา (Asia/London/NY/Overnight + 3 ช่วงรอยต่อ) " +
            "และสถานการณ์ตลาดจริง (TREND_BULL, TREND_BEAR, BREAKOUT, RANGE) ด้วย Order Flow Delta + Anchored VWAP (FlowTracker) และ L2 DOM Imbalance " +
            "ตามผล Out-of-Sample Phase 2 พร้อมกันพอร์ตช่วงสเปรดถ่าง (THIN_OR_NEWS / NY_TO_CLOSE)";

        public override string[] ParamNames => new[] { "SlAtrScale", "RrScale", "ImbThresh", "DeltaThresh" };
        public override string[] EntryRules => new[]
        {
            "1. จำแนก Session 7 โซน (UTC) + ตรวจภาวะตลาดบนแท่งปิดล่าสุด (.Last(1)) ด้วย EMA50/200, ADX(14), ATR(14), FlowTracker (Delta/VWAP/SD) และ L2 DOM",
            "2. ปฏิเสธการเข้าทันทีเมื่อเกิด THIN_OR_NEWS หรือช่วง XAUUSD NY_TO_CLOSE Spread > 0.19",
            "3. จับคู่กลยุทธ์ที่ผ่าน OOS ของโซนนั้น: TREND ➔ Pullback + Delta (STR-001), BREAKOUT ➔ Expansion + Delta (STR-004), RANGE ➔ VWAP ±1 SD / DOM Fade (STR-002 / STR-006)",
            "4. ระยะ SL ปรับอัตโนมัติตาม ATR(14) คุมเพดานความเสี่ยงพอร์ต Demo + Cooldown 15 นาทีหลังสัญญาณ",
        };
        public override string[] ExitRules => new[]
        {
            "Stealth RAM SL/TP + Breakeven Lock",
            "Zone-End Protection: สำหรับไม้โหมด ZONE_SCALP จะปิดสถานะเมื่อหลุดโซนเวลาที่เข้าและกำไรเป็นบวก หรือเข้าเขต NY_TO_CLOSE Spread Spike",
            "Reverse Flow Smart Exit: ปิดล็อกกำไรหลัง > 0.75R หาก DOM Imbalance สวนทิศรุนแรง",
        };

        public override int MaxPositions => 1;
        public override bool ExitOnOppositeSignal => false;

        private MarketDepth _depth;
        private FlowTracker _flow;
        private double _currentImbalance;
        private double _lastFlowDelta;
        private double _lastVwapDay;
        private double _lastSdDay;
        private string _lastSweep = "";

        private double _lastStopDistance = 4.2;
        private double _rewardRisk = 2.4;
        private string _signalTag = "V5|INIT";
        private string _currentRegime = "ASIA|RANGE";

        private double _slAtrScale = 1.0;
        private double _rrScale = 1.0;
        private double _imbThresh = 0.018;
        private double _deltaThresh = 6.0;
        private double _spreadCeiling = 0.24;
        private double _minAtr = 0.25;
        private double _maxSlDistance = 6.5;

        private DateTime _lastSignalUtc = DateTime.MinValue;
        private string _currentZone = "ASIA";
        private string _currentMacroRegime = "RANGE";
        private bool _exitOnZoneEndPending;
        private readonly Dictionary<int, string> _posEntryZone = new Dictionary<int, string>();
        private readonly Dictionary<int, bool> _posZoneFlatMode = new Dictionary<int, bool>();
        private readonly Dictionary<int, double> _posSlDist = new Dictionary<int, double>();

        public override string SignalTag => _signalTag;
        public override string CurrentRegime => _currentRegime;
        public override double? StopDistance(TradeType side) => _lastStopDistance;
        public override double RewardRisk => _rewardRisk;

        protected override void OnInit()
        {
            _flow = new FlowTracker();
            string sym = Bot.SymbolName.ToUpperInvariant();
            if (sym.Contains("BTC"))
            {
                _imbThresh = 0.020;
                _deltaThresh = 12.0;
                _spreadCeiling = 35.0;
                _minAtr = 12.0;
                _maxSlDistance = 160.0;
                _lastStopDistance = 90.0;
            }
            else if (sym.Contains("ETH"))
            {
                _imbThresh = 0.015;
                _deltaThresh = 5.0;
                _spreadCeiling = 3.8;
                _minAtr = 0.80;
                _maxSlDistance = 8.0;
                _lastStopDistance = 3.0;
            }
            else
            {
                _imbThresh = 0.018;
                _deltaThresh = 6.0;
                _spreadCeiling = 0.24;
                _minAtr = 0.25;
                _maxSlDistance = 6.5;
                _lastStopDistance = 4.2;
            }

            if (P.Length > 0 && P[0] > 0) _slAtrScale = P[0];
            if (P.Length > 1 && P[1] > 0) _rrScale = P[1];
            if (P.Length > 2 && P[2] > 0) _imbThresh = P[2];
            if (P.Length > 3 && P[3] > 0) _deltaThresh = P[3];

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
                    Bot.Print("REGIME_ADAPTIVE_V5 MarketDepth warning: {0}", e.Message);
                }

                try
                {
                    var ticks = Bot.MarketData.GetTicks();
                    if (ticks != null)
                        _flow.WarmFromHistory(ticks, Bot.Server.TimeInUtc);
                }
                catch { }
            }

            Bot.Print(string.Format(
                CultureInfo.InvariantCulture,
                "REGIME_ADAPTIVE_V5 v{0} initialized on {1} | SlAtrScale={2:F2}, RrScale={3:F2}, ImbThresh={4:F3}, DeltaThresh={5:F1}",
                Version, Bot.SymbolName, _slAtrScale, _rrScale, _imbThresh, _deltaThresh));
        }

        public override void OnTick()
        {
            if (_flow == null) return;
            DateTime now = DateTime.SpecifyKind(Bot.Server.TimeInUtc, DateTimeKind.Utc);
            long unix = new DateTimeOffset(now).ToUnixTimeSeconds();
            string row = _flow.Feed(unix, Bot.Symbol.Bid, Bot.Symbol.Ask);
            if (!string.IsNullOrEmpty(row))
            {
                // Format from FlowTracker.CloseMinute():
                // [0]=time,[1]=ticks,[2]=delta,[3]=cvd,[4]=vwapDay,[5]=sdDay,...,[21]=sweep
                string[] parts = row.Split(',');
                if (parts.Length > 21)
                {
                    if (double.TryParse(parts[2], NumberStyles.Float, CultureInfo.InvariantCulture, out double d))
                        _lastFlowDelta = d;
                    if (double.TryParse(parts[4], NumberStyles.Float, CultureInfo.InvariantCulture, out double vw))
                        _lastVwapDay = vw;
                    if (double.TryParse(parts[5], NumberStyles.Float, CultureInfo.InvariantCulture, out double sd))
                        _lastSdDay = sd;
                    _lastSweep = parts[21] ?? "";
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
                    _currentImbalance = (bidVol - askVol) / (bidVol + askVol);
            }
            catch { }
        }

        public static string ClassifySessionZone(DateTime utcTime)
        {
            int hm = utcTime.Hour * 60 + utcTime.Minute;
            if (hm >= 0 && hm < 7 * 60) return "ASIA";
            if (hm >= 7 * 60 && hm < 8 * 60) return "ASIA_TO_LONDON";
            if (hm >= 8 * 60 && hm < 12 * 60 + 30) return "LONDON";
            if (hm >= 12 * 60 + 30 && hm < 14 * 60) return "LONDON_TO_NY";
            if (hm >= 14 * 60 && hm < 20 * 60 + 30) return "NY";
            if (hm >= 20 * 60 + 30 && hm < 22 * 60) return "NY_TO_CLOSE";
            return "OVERNIGHT";
        }

        private void BindLatestPositionMetadata()
        {
            foreach (var pos in Bot.Positions.Where(p => p.SymbolName == Bot.SymbolName && p.Label != null && p.Label.StartsWith(Code, StringComparison.Ordinal)))
            {
                if (!_posEntryZone.ContainsKey(pos.Id))
                {
                    _posEntryZone[pos.Id] = _currentZone;
                    _posZoneFlatMode[pos.Id] = _exitOnZoneEndPending;
                    _posSlDist[pos.Id] = _lastStopDistance;
                }
            }
        }

        public override TradeType? Signal()
        {
            BindLatestPositionMetadata();

            if (Bot.Bars.Count < 210)
            {
                _currentZone = ClassifySessionZone(Bot.Server.TimeInUtc);
                _currentMacroRegime = "WARMUP";
                _currentRegime = _currentZone + "|WARMUP";
                return null;
            }

            DateTime barUtc = DateTime.SpecifyKind(Bot.Bars.OpenTimes.Last(1), DateTimeKind.Utc);
            _currentZone = ClassifySessionZone(barUtc);

            if ((barUtc - _lastSignalUtc).TotalMinutes < 15)
                return null;

            double c = Bot.Bars.ClosePrices.Last(1);
            double o = Bot.Bars.OpenPrices.Last(1);
            double h1 = Bot.Bars.HighPrices.Last(1);
            double l1 = Bot.Bars.LowPrices.Last(1);
            double spread = Bot.Symbol.Spread;

            int start = Math.Min(Bot.Bars.Count - 1, 240);
            double ema20 = Bot.Bars.ClosePrices.Last(start);
            double ema50 = ema20;
            double ema200 = ema20;
            double atr14 = _minAtr;
            double trS = _minAtr, plusDmS = 0.0, minusDmS = 0.0;
            double adx14 = 20.0;
            var dxList = new Queue<double>();

            double k20 = 2.0 / 21.0, k50 = 2.0 / 51.0, k200 = 2.0 / 201.0;
            for (int i = start - 1; i >= 1; i--)
            {
                double ci = Bot.Bars.ClosePrices.Last(i);
                double hi = Bot.Bars.HighPrices.Last(i);
                double li = Bot.Bars.LowPrices.Last(i);
                double pc = Bot.Bars.ClosePrices.Last(i + 1);
                double ph = Bot.Bars.HighPrices.Last(i + 1);
                double pl = Bot.Bars.LowPrices.Last(i + 1);

                ema20 = ci * k20 + ema20 * (1.0 - k20);
                ema50 = ci * k50 + ema50 * (1.0 - k50);
                ema200 = ci * k200 + ema200 * (1.0 - k200);

                double tr = Math.Max(hi - li, Math.Max(Math.Abs(hi - pc), Math.Abs(li - pc)));
                atr14 = ((atr14 * 13.0) + tr) / 14.0;

                double upM = hi - ph;
                double dnM = pl - li;
                double pDm = (upM > dnM && upM > 0) ? upM : 0.0;
                double mDm = (dnM > upM && dnM > 0) ? dnM : 0.0;

                trS = (trS * 13.0 + tr) / 14.0;
                plusDmS = (plusDmS * 13.0 + pDm) / 14.0;
                minusDmS = (minusDmS * 13.0 + mDm) / 14.0;
                double pDi = 100.0 * plusDmS / Math.Max(trS, 1e-6);
                double mDi = 100.0 * minusDmS / Math.Max(trS, 1e-6);
                double dx = 100.0 * Math.Abs(pDi - mDi) / Math.Max(pDi + mDi, 1e-6);
                dxList.Enqueue(dx);
                if (dxList.Count > 14) dxList.Dequeue();
                adx14 = dxList.Average();
            }
            atr14 = Math.Max(atr14, _minAtr);

            double prevHh20 = double.MinValue, prevLl20 = double.MaxValue;
            double hh15 = double.MinValue, ll15 = double.MaxValue;
            for (int i = 2; i <= 21; i++)
            {
                double hi = Bot.Bars.HighPrices.Last(i);
                double li = Bot.Bars.LowPrices.Last(i);
                if (hi > prevHh20) prevHh20 = hi;
                if (li < prevLl20) prevLl20 = li;
                if (i <= 16)
                {
                    if (hi > hh15) hh15 = hi;
                    if (li < ll15) ll15 = li;
                }
            }

            // Use FlowTracker tick VWAP/SD if warmed up, else fallback cleanly to closed intraday bar VWAP
            double vwap = _lastVwapDay > 0 ? _lastVwapDay : c;
            double sdDay = _lastSdDay > 0 ? Math.Max(_lastSdDay, atr14 * 1.2) : atr14 * 1.5;
            if (_lastVwapDay <= 0)
            {
                DateTime dayUtc = barUtc.Date;
                double sumPv = 0.0, sumV = 0.0;
                var dayCloses = new List<double>();
                for (int i = 1; i <= 360 && i < Bot.Bars.Count; i++)
                {
                    DateTime bt = DateTime.SpecifyKind(Bot.Bars.OpenTimes.Last(i), DateTimeKind.Utc);
                    if (bt.Date != dayUtc) break;
                    double tp = (Bot.Bars.HighPrices.Last(i) + Bot.Bars.LowPrices.Last(i) + Bot.Bars.ClosePrices.Last(i)) / 3.0;
                    double v = Math.Max(Bot.Bars.TickVolumes.Last(i), 1.0);
                    sumPv += tp * v;
                    sumV += v;
                    dayCloses.Add(Bot.Bars.ClosePrices.Last(i));
                }
                if (sumV > 0) vwap = sumPv / sumV;
                if (dayCloses.Count >= 10)
                {
                    double varSum = dayCloses.Sum(x => (x - vwap) * (x - vwap)) / dayCloses.Count;
                    sdDay = Math.Max(Math.Sqrt(varSum), atr14 * 1.2);
                }
            }

            bool isSpreadThin = spread > _spreadCeiling;
            string macro;
            if (isSpreadThin)
                macro = "THIN_OR_NEWS";
            else if (adx14 >= 24.0 && ema50 > ema200 && c > ema50)
                macro = "TREND_BULL";
            else if (adx14 >= 24.0 && ema50 < ema200 && c < ema50)
                macro = "TREND_BEAR";
            else if (c > prevHh20 || c < prevLl20)
                macro = "BREAKOUT";
            else
                macro = "RANGE";

            _currentMacroRegime = macro;
            _currentRegime = _currentZone + "|" + macro;

            if (macro == "THIN_OR_NEWS")
                return null;

            string sym = Bot.SymbolName.ToUpperInvariant();
            bool isXau = sym.Contains("XAU") || sym.Contains("GOLD");
            if (isXau && _currentZone == "NY_TO_CLOSE" && spread > 0.19)
                return null;

            double delta = _lastFlowDelta;
            bool hasLiveDom = Bot.RunningMode == RunningMode.RealTime && _depth != null;
            bool isBullMacro = c > ema50 && ema50 > ema200;
            bool isBearMacro = c < ema50 && ema50 < ema200;
            double range15 = Math.Max(hh15 - ll15, atr14);

            TradeType? signal = null;
            string subStrat = "NONE";
            double slMult = 2.0;
            double rr = 2.5;
            bool zoneFlat = false;

            if (macro == "TREND_BULL" || macro == "TREND_BEAR")
            {
                // Exact Phase 2 STR-001 Pullback + Real Tick Order-Flow Delta
                if (macro == "TREND_BULL" && l1 <= ema50 + 0.6 * atr14 && delta >= _deltaThresh && (!hasLiveDom || _currentImbalance >= -0.005))
                {
                    signal = TradeType.Buy;
                    subStrat = "STR001_PULLBACK";
                    if (isXau && _currentZone == "LONDON") { slMult = 1.5; rr = 2.0; zoneFlat = true; }
                    else { slMult = 2.0; rr = 2.5; }
                }
                else if (macro == "TREND_BEAR" && h1 >= ema50 - 0.6 * atr14 && delta <= -_deltaThresh && (!hasLiveDom || _currentImbalance <= 0.005))
                {
                    signal = TradeType.Sell;
                    subStrat = "STR001_PULLBACK";
                    if (isXau && _currentZone == "LONDON") { slMult = 1.5; rr = 2.0; zoneFlat = true; }
                    else { slMult = 2.0; rr = 2.5; }
                }
            }
            else if (macro == "BREAKOUT")
            {
                // Phase 2 Finding: Avoid XAU LONDON breakouts (0/4 OOS), trade ASIA / ASIA_TO_LONDON / NY breakouts + Delta
                bool allowBreakout = !(isXau && _currentZone == "LONDON");
                if (allowBreakout)
                {
                    if (c > prevHh20 && delta >= _deltaThresh * 1.2 && (!hasLiveDom || _currentImbalance >= _imbThresh * 0.4))
                    {
                        signal = TradeType.Buy;
                        subStrat = "STR004_BREAKOUT";
                        slMult = (_currentZone == "ASIA") ? 2.5 : 2.0;
                        rr = 2.5;
                        if (_currentZone == "ASIA_TO_LONDON") zoneFlat = true;
                    }
                    else if (c < prevLl20 && delta <= -_deltaThresh * 1.2 && (!hasLiveDom || _currentImbalance <= -_imbThresh * 0.4))
                    {
                        signal = TradeType.Sell;
                        subStrat = "STR004_BREAKOUT";
                        slMult = (_currentZone == "ASIA") ? 2.5 : 2.0;
                        rr = 2.5;
                        if (_currentZone == "ASIA_TO_LONDON") zoneFlat = true;
                    }
                }
            }
            else // RANGE
            {
                // Phase 2 STR-002 / STR-010 VWAP Mean Reversion + STR-006 DOM Absorption
                bool vwapBuy = (l1 <= vwap - sdDay * 1.0) && delta >= _deltaThresh && !isBearMacro;
                bool vwapSell = (h1 >= vwap + sdDay * 1.0) && delta <= -_deltaThresh && !isBullMacro;
                bool domBuy = hasLiveDom && _currentImbalance >= _imbThresh && c <= ll15 + 0.25 * range15 && delta >= 0 && !isBearMacro;
                bool domSell = hasLiveDom && _currentImbalance <= -_imbThresh && c >= hh15 - 0.25 * range15 && delta <= 0 && !isBullMacro;

                if (vwapBuy || domBuy)
                {
                    signal = TradeType.Buy;
                    subStrat = domBuy ? "STR006_DOM" : "STR002_VWAP";
                }
                else if (vwapSell || domSell)
                {
                    signal = TradeType.Sell;
                    subStrat = domSell ? "STR006_DOM" : "STR002_VWAP";
                }

                if (signal.HasValue)
                {
                    if (isXau && (_currentZone == "LONDON" || _currentZone == "LONDON_TO_NY"))
                    {
                        slMult = 1.5; rr = 2.0; zoneFlat = true;
                    }
                    else
                    {
                        slMult = 2.0; rr = 2.4;
                    }
                }
            }

            if (!signal.HasValue)
                return null;

            double rawSl = Math.Max(atr14 * slMult * _slAtrScale, Math.Max(2.5 * spread, _minAtr));
            _lastStopDistance = Math.Min(rawSl, _maxSlDistance);
            _rewardRisk = rr * _rrScale;
            _exitOnZoneEndPending = zoneFlat;
            _lastSignalUtc = barUtc;
            _signalTag = string.Format(CultureInfo.InvariantCulture, "{0}|{1}|{2}", _currentZone, macro, subStrat);

            Bot.Print(string.Format(
                CultureInfo.InvariantCulture,
                "REGIME_ADAPTIVE_V5 v{0}: {1} Signal [{2}] SL={3:F2} RR={4:F2} Delta={5:F1} VWAP={6:F2} Imb={7:F3}",
                Version, signal.Value, _signalTag, _lastStopDistance, _rewardRisk, delta, vwap, _currentImbalance));

            return signal;
        }

        public override bool ShouldExit(Position pos)
        {
            if (pos == null) return false;

            double currentPrice = pos.TradeType == TradeType.Buy ? Bot.Symbol.Bid : Bot.Symbol.Ask;
            double profitDist = pos.TradeType == TradeType.Buy
                ? (currentPrice - pos.EntryPrice)
                : (pos.EntryPrice - currentPrice);

            double slDist = _posSlDist.TryGetValue(pos.Id, out double savedSl) && savedSl > 0 ? savedSl : _lastStopDistance;
            string entryZone = _posEntryZone.TryGetValue(pos.Id, out string zVal) ? zVal : _currentZone;
            bool zoneFlat = _posZoneFlatMode.TryGetValue(pos.Id, out bool zfVal) && zfVal;

            if (zoneFlat && _currentZone != entryZone && (Bot.Server.TimeInUtc - pos.EntryTime).TotalMinutes >= 3)
            {
                if (profitDist > 0 || _currentZone == "NY_TO_CLOSE")
                    return true;
            }

            if (slDist > 0 && profitDist >= slDist * 0.75)
            {
                if (pos.TradeType == TradeType.Buy && _currentImbalance <= -(_imbThresh * 1.6))
                    return true;
                if (pos.TradeType == TradeType.Sell && _currentImbalance >= (_imbThresh * 1.6))
                    return true;
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
