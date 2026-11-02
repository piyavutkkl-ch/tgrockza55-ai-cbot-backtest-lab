import re

path = r'd:\cbot-atgvt\cbot\BacktestLab\BacktestLab.cs'
with open(path, 'r', encoding='utf-8') as f:
    c = f.read()

# 1. Add parameters after BookSeconds
param_marker = '[Parameter("Book snapshot every (s)", DefaultValue = 2, MinValue = 1, Group = "Live")]\n        public int BookSeconds { get; set; }'
new_params = '''[Parameter("Book snapshot every (s)", DefaultValue = 2, MinValue = 1, Group = "Live")]
        public int BookSeconds { get; set; }

        // --- QUANTUM STEALTH & ANTI-STOP-HUNT DEFENSE ---
        [Parameter("Stealth stops (SL/TP in RAM)", DefaultValue = true, Group = "Risk")]
        public bool StealthStops { get; set; } = true;

        [Parameter("Jitter noise (+/- % on SL)", DefaultValue = 5.0, MinValue = 0.0, MaxValue = 20.0, Group = "Risk")]
        public double JitterNoisePct { get; set; } = 5.0;

        [Parameter("Emergency disaster SL (x SL)", DefaultValue = 3.5, MinValue = 0.0, Group = "Risk")]
        public double EmergencySlMult { get; set; } = 3.5;'''

c = c.replace(param_marker, new_params)

# 2. Add StealthPosition class and dictionary
state_marker = 'private readonly Dictionary<int, double> _expectedClose = new Dictionary<int, double>();'
new_state = '''// Stealth Position Tracking (ซ่อน SL/TP จากโบรกเกอร์และเจ้าตลาด)
        private class StealthPosition
        {
            public int Id;
            public TradeType Side;
            public double EntryPrice;
            public double VirtualSl;
            public double VirtualTp;
            public double JitterFactor;
            public DateTime OpenTime;
        }
        private readonly Dictionary<int, StealthPosition> _stealthPositions = new Dictionary<int, StealthPosition>();
        private readonly Random _rng = new Random();

        // ราคาที่เห็นตอนสั่งปิด ของแต่ละ position — ไว้เทียบกับราคาที่ได้จริง (ใช้เฉพาะตอนบันทึกตลาดสด)
        private readonly Dictionary<int, double> _expectedClose = new Dictionary<int, double>();'''

c = c.replace(state_marker, new_state)

# 3. Add to ApplyLiveSettings
live_marker = 'if (root.TryGetProperty("p4", out v)) P4 = v.GetDouble();'
new_live = '''if (root.TryGetProperty("p4", out v)) P4 = v.GetDouble();
                    if (root.TryGetProperty("stealthStops", out v)) StealthStops = v.GetBoolean();
                    if (root.TryGetProperty("jitterNoisePct", out v)) JitterNoisePct = v.GetDouble();
                    if (root.TryGetProperty("emergencySlMult", out v)) EmergencySlMult = v.GetDouble();'''

c = c.replace(live_marker, new_live, 1)

live_sym_marker = 'if (symObj.TryGetProperty("p4", out v)) P4 = v.GetDouble();'
new_sym_live = '''if (symObj.TryGetProperty("p4", out v)) P4 = v.GetDouble();
                        if (symObj.TryGetProperty("stealthStops", out v)) StealthStops = v.GetBoolean();
                        if (symObj.TryGetProperty("jitterNoisePct", out v)) JitterNoisePct = v.GetDouble();
                        if (symObj.TryGetProperty("emergencySlMult", out v)) EmergencySlMult = v.GetDouble();'''

c = c.replace(live_sym_marker, new_sym_live, 1)

# 4. Update OnTick to call CheckStealthStops
ontick_marker = '''        protected override void OnTick()
        {
            _strategy.OnTick();
            if (_recorder != null) _recorder.OnTick();
        }'''

new_ontick = '''        protected override void OnTick()
        {
            _strategy.OnTick();
            if (_recorder != null) _recorder.OnTick();

            if (StealthStops && _stealthPositions.Count > 0)
                CheckStealthStops();
        }

        private void CheckStealthStops()
        {
            foreach (var pos in Positions.FindAll(Label, SymbolName))
            {
                StealthPosition sp;
                if (!_stealthPositions.TryGetValue(pos.Id, out sp)) continue;

                double currentPrice = pos.TradeType == TradeType.Buy ? Symbol.Bid : Symbol.Ask;
                bool isSl = pos.TradeType == TradeType.Buy ? (currentPrice <= sp.VirtualSl) : (currentPrice >= sp.VirtualSl);
                bool isTp = pos.TradeType == TradeType.Buy ? (currentPrice >= sp.VirtualTp) : (currentPrice <= sp.VirtualTp);
                bool isCustomExit = _strategy.ShouldExit(pos);

                if (isSl || isTp || isCustomExit)
                {
                    string reason = isSl ? "STEALTH_SL" : (isTp ? "STEALTH_TP" : "SMART_DOM_EXIT");
                    Print("🛡️ STEALTH TRIGGERED: {0} for {1} #{2} at Price {3:F2} (VirtualSL={4:F2}, VirtualTP={5:F2})",
                        reason, SymbolName, pos.Id, currentPrice, sp.VirtualSl, sp.VirtualTp);
                    Close(pos);
                    _stealthPositions.Remove(pos.Id);
                }
            }
        }'''

c = c.replace(ontick_marker, new_ontick)

# 5. Order execution logic in OnBar
exec_old = '''            var volume = Symbol.NormalizeVolumeInUnits(Symbol.QuantityToVolumeInUnits(Lots));
            double? sl = StopLossPips > 0 ? StopLossPips : (double?)null;
            double? tp = TakeProfitPips > 0 ? TakeProfitPips : (double?)null;

            var distance = _strategy.StopDistance(signal.Value);
            if (distance.HasValue)
            {
                var price = Symbol.Bid;
                var d = Math.Max(distance.Value, price * MinStopPct / 100);
                if (MaxStopPct > 0) d = Math.Min(d, price * MaxStopPct / 100);
                sl = Math.Round(d / Symbol.PipSize, 1);
                tp = _strategy.RewardRisk > 0 ? Math.Round(sl.Value * _strategy.RewardRisk, 1) : (double?)null;   // RewardRisk <= 0 = ไม่มี TP
                _structureStops = true;
            }
            var expected = signal.Value == TradeType.Buy ? Symbol.Ask : Symbol.Bid;
            var clock = System.Diagnostics.Stopwatch.StartNew();
            var result = ExecuteMarketOrder(signal.Value, SymbolName, volume, Label, sl, tp, _strategy.SignalTag);
            clock.Stop();
            if (_recorder != null)
            {
                if (result.IsSuccessful && result.Position != null)
                    _recorder.OrderOpened(result.Position, expected, clock.Elapsed.TotalMilliseconds, _strategy.Prediction);
                else
                    _recorder.OrderFailed(signal.Value, result.Error.HasValue ? result.Error.Value.ToString() : "unknown");
            }
            if (result.IsSuccessful && result.Position != null)
            {
                var p = result.Position;
                _stops[p.Id] = new[] { p.StopLoss, p.TakeProfit };
                if (p.StopLoss.HasValue && (_strategy.BreakevenAtR > 0 || _strategy.CutAfterMinutes > 0))
                    _plans[p.Id] = new TradePlan
                    {
                        R = Math.Abs(p.EntryPrice - p.StopLoss.Value),
                        BreakevenAtR = _strategy.BreakevenAtR,
                        CutAfterMinutes = _strategy.CutAfterMinutes,
                        CutBelowR = _strategy.CutBelowR,
                    };
            }'''

exec_new = '''            var volume = Symbol.NormalizeVolumeInUnits(Symbol.QuantityToVolumeInUnits(Lots));
            double? sl = StopLossPips > 0 ? StopLossPips : (double?)null;
            double? tp = TakeProfitPips > 0 ? TakeProfitPips : (double?)null;

            var distance = _strategy.StopDistance(signal.Value);
            double baseDistance = 0;
            if (distance.HasValue)
            {
                var price = Symbol.Bid;
                var d = Math.Max(distance.Value, price * MinStopPct / 100);
                if (MaxStopPct > 0) d = Math.Min(d, price * MaxStopPct / 100);
                baseDistance = d;
                sl = Math.Round(d / Symbol.PipSize, 1);
                tp = _strategy.RewardRisk > 0 ? Math.Round(sl.Value * _strategy.RewardRisk, 1) : (double?)null;   // RewardRisk <= 0 = ไม่มี TP
                _structureStops = true;
            }
            var expected = signal.Value == TradeType.Buy ? Symbol.Ask : Symbol.Bid;

            // --- QUANTUM STEALTH & STOCHASTIC JITTER DEFENSE ---
            double? brokerSl = sl;
            double? brokerTp = tp;
            double virtualSlPrice = 0;
            double virtualTpPrice = 0;
            double jitter = 1.0;

            if (StealthStops && baseDistance > 0)
            {
                // Jitter +/- JitterNoisePct %
                if (JitterNoisePct > 0)
                {
                    double noise = (_rng.NextDouble() * 2.0 - 1.0) * (JitterNoisePct / 100.0);
                    jitter = 1.0 + noise;
                }
                double actualSlDist = baseDistance * jitter;
                double actualTpDist = actualSlDist * (_strategy.RewardRisk > 0 ? _strategy.RewardRisk : 2.0);

                virtualSlPrice = signal.Value == TradeType.Buy ? (expected - actualSlDist) : (expected + actualSlDist);
                virtualTpPrice = signal.Value == TradeType.Buy ? (expected + actualTpDist) : (expected - actualTpDist);

                // Send emergency catastrophic stop to broker if configured, hide TP completely
                brokerSl = EmergencySlMult > 0 ? Math.Round((baseDistance * EmergencySlMult) / Symbol.PipSize, 1) : (double?)null;
                brokerTp = null;
            }

            var clock = System.Diagnostics.Stopwatch.StartNew();
            var result = ExecuteMarketOrder(signal.Value, SymbolName, volume, Label, brokerSl, brokerTp, _strategy.SignalTag);
            clock.Stop();
            if (_recorder != null)
            {
                if (result.IsSuccessful && result.Position != null)
                    _recorder.OrderOpened(result.Position, expected, clock.Elapsed.TotalMilliseconds, _strategy.Prediction);
                else
                    _recorder.OrderFailed(signal.Value, result.Error.HasValue ? result.Error.Value.ToString() : "unknown");
            }
            if (result.IsSuccessful && result.Position != null)
            {
                var p = result.Position;
                _stops[p.Id] = new[] { p.StopLoss, p.TakeProfit };

                if (StealthStops && baseDistance > 0)
                {
                    _stealthPositions[p.Id] = new StealthPosition
                    {
                        Id = p.Id,
                        Side = signal.Value,
                        EntryPrice = p.EntryPrice,
                        VirtualSl = virtualSlPrice,
                        VirtualTp = virtualTpPrice,
                        JitterFactor = jitter,
                        OpenTime = Server.Time
                    };
                    Print("🛡️ STEALTH ARMED for #{0} {1}: Entry={2:F2} | VirtualSL={3:F2} | VirtualTP={4:F2} | Jitter={5:+0.00%} | BrokerEmergencySL={6}",
                        p.Id, signal.Value, p.EntryPrice, virtualSlPrice, virtualTpPrice, (jitter - 1.0) * 100.0, brokerSl.HasValue ? brokerSl.Value.ToString() : "NONE");
                }

                if (p.StopLoss.HasValue && (_strategy.BreakevenAtR > 0 || _strategy.CutAfterMinutes > 0))
                    _plans[p.Id] = new TradePlan
                    {
                        R = Math.Abs(p.EntryPrice - p.StopLoss.Value),
                        BreakevenAtR = _strategy.BreakevenAtR,
                        CutAfterMinutes = _strategy.CutAfterMinutes,
                        CutBelowR = _strategy.CutBelowR,
                    };
            }'''

c = c.replace(exec_old, exec_new)

# 6. Cleanup in OnPositionClosed
pos_closed_marker = 'var p = args.Position;\n            if (_recorder == null || p.Label != Label || p.SymbolName != SymbolName) return;'
new_pos_closed = 'var p = args.Position;\n            _stealthPositions.Remove(p.Id);\n            if (_recorder == null || p.Label != Label || p.SymbolName != SymbolName) return;'

c = c.replace(pos_closed_marker, new_pos_closed)

with open(path, 'w', encoding='utf-8') as f:
    f.write(c)

print('Patch applied successfully!')
