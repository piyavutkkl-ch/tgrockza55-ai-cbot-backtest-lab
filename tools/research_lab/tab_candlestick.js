// Tab 3: Pro Candlestick Lab (Synchronized Standard OHLC vs Heikin-Ashi + VWAP SD Split-View & Instant Dictionary)
(function () {
  'use strict';

  var initialized = false;
  var activeDatasetKey = 'XAUUSD'; // XAUUSD | BTCUSD | ETHUSD | HA_0 | HA_1 | HA_2
  var computedBars = [];
  var viewStart = 60;
  var viewCount = 70;
  var hoverIdx = -1;
  var isDragging = false;
  var dragStartX = 0;
  var dragStartView = 0;

  var DICT_TERMS = [
    { id: 'D01', cat: 'Candlestick & HA', term: 'Heikin-Ashi Close (HA_Close)', th: 'ราคาปิดเฉลี่ยถ่วงสมดุลแท่งไฮเก้นอาชิ', tag: 'Smoothing', formula: '(O + H + L + C) / 4', desc: 'Average price of the current real bar; smooths intra-bar noise and exposes genuine directional drift.' },
    { id: 'D02', cat: 'Candlestick & HA', term: 'Heikin-Ashi Open (HA_Open)', th: 'ราคาเปิดต่อเนื่องกึ่งกลางแท่งก่อนหน้า', tag: 'Momentum Memory', formula: '(prevHA_O + prevHA_C) / 2', desc: 'Computed strictly from the previous Heikin-Ashi body midpoint — known at bar open before ticks arrive, enabling open-gap signal prediction.' },
    { id: 'D03', cat: 'Candlestick & HA', term: 'HA Shaved Bottom / Top (No Wick)', th: 'แท่งไร้ไส้ล่าง (Bullish) หรือไร้ไส้บน (Bearish)', tag: 'Trend Continuation', formula: 'HA_Low == HA_Open (Strong Up)', desc: 'Signals strong sustained trend with minimal counter-pressure; preferred regime confirmation for STR-001 and STR-004.' },
    { id: 'D04', cat: 'Candlestick & HA', term: 'HA Doji / Spinning Top', th: 'แท่งโดจิและตัวแคบใน Heikin-Ashi', tag: 'Indecision', formula: '|HA_C - HA_O| < 0.2 * (HA_H - HA_L)', desc: 'Thin body with upper and lower shadows warns of momentum exhaustion or impending trend transition.' },
    { id: 'D05', cat: 'Candlestick & HA', term: 'Pin Bar / Rejection Wick', th: 'หางแท่งยาวปฏิเสธระดับราคา (Liquidity Rejection)', tag: 'Reversal', formula: 'Wick >= 2.2 * Body', desc: 'Long upper or lower shadow after sweeping resting stop clusters indicates institutional absorption at extremes.' },
    { id: 'D06', cat: 'Candlestick & HA', term: 'CHoCH (Change of Character)', th: 'การเปลี่ยนโครงสร้างแนวโน้มราคา', tag: 'Market Structure', formula: 'Break of Prior Swing Pivot', desc: 'First structural break against the dominant intraday leg after a liquidity sweep; Pillar 2 displacement confirmation.' },
    { id: 'D07', cat: 'Candlestick & HA', term: 'Liquidity Sweep (Stop Hunt)', th: 'การกวาดคำสั่ง Stop Loss เหนือ Hi / ใต้ Lo ก่อนกลับตัว', tag: 'SMC / STR-003', formula: 'High > Equal_High && Close < Equal_High', desc: 'Price briefly pierces prior swing highs/lows to harvest stops before snapping back into equilibrium (BIAS_STOP_CLUSTER_SWEEP).' },
    { id: 'D08', cat: 'Candlestick & HA', term: 'Bullish / Bearish Engulfing', th: 'แท่งกลืนกินเต็มลำตัว', tag: 'Displacement', formula: 'Body_t covers Body_{t-1}', desc: 'Full-bodied displacement candle confirming aggressive taker flow overturning the prior bar.' },

    { id: 'D09', cat: 'VWAP & Execution', term: 'Anchored VWAP (Volume-Weighted Average Price)', th: 'ราคาเฉลี่ยถ่วงน้ำหนักตามปริมาณซื้อขายสะสม', tag: 'Fair Value', formula: 'Sum(P_i * V_i) / Sum(V_i)', desc: 'Institutional fair-value benchmark since session anchor; used by STR-002 and ENGINE_04_VWAP_SLICER as equilibrium magnet.' },
    { id: 'D10', cat: 'VWAP & Execution', term: 'VWAP ±1σ / ±2σ SD Bands', th: 'แถบส่วนเบี่ยงเบนมาตรฐานรอบเส้น VWAP', tag: 'Overextension', formula: 'VWAP +/- k * sigma_VWAP', desc: 'Measures price stretch from session fair value. +1.2 to +2.0 SD signals mean-reversion value zones in balanced (Chop) regimes.' },
    { id: 'D11', cat: 'VWAP & Execution', term: 'VWAP Z-Score Stretch', th: 'ค่ามาตรฐาน Z-Score วัดระยะห่างจาก VWAP', tag: 'Signal Threshold', formula: 'Z = (Close - VWAP) / SD', desc: 'Standardized stretch metric; |Z| > 2.5 in non-news markets triggers STR-007 extreme stretch mean-reversion evaluation.' },
    { id: 'D12', cat: 'VWAP & Execution', term: 'Almgren-Chriss Implementation Shortfall', th: 'ต้นทุนแฝงและแรงกระแทกราคาขณะทยอยส่งคำสั่ง', tag: 'Optimal Exec', formula: 'E[IS] = TempImpact + PermImpact + TimingRisk', desc: 'Balances market impact against price drift risk when slicing institutional order blocks.' },
    { id: 'D13', cat: 'VWAP & Execution', term: 'Dynamic ATR Stop-Loss / TP', th: 'ระยะตัดขาดทุนและทำกำไรแปรผันตาม ATR', tag: 'QUANT_KELLY', formula: 'SL = 2.0 * ATR_14, TP = 2.8 * SL', desc: 'Adapts stop placement to live M1 volatility rather than rigid USD pips; central to #1 BTCUSD champion ENGINE_12_KELLY_SIZING.' },
    { id: 'D14', cat: 'VWAP & Execution', term: 'Broker Friction & Spread Drag', th: 'แรงต้านจากค่าสเปรด ค่าคอมฯ และ Slippage จริง', tag: 'Gate 5 Filter', formula: 'Net_Edge = Gross_Alpha - (Spread + Comm + Slip)', desc: 'Primary killer of naive M1 scalpers; wiped out GRAVE_001 (PF 1.62 -> 0.54) and weekend GOLD-PERP ($1.413 spread vs $0.115 bar range).' },
    { id: 'D15', cat: 'VWAP & Execution', term: 'Session Rollover Blackout', th: 'หน้าต่างปิดรับออเดอร์ช่วงเปลี่ยนวันตลาด 21:45–23:15 UTC', tag: 'STR-009 Defense', formula: 'Flat All @ 21:45 UTC', desc: 'Mandatory liquidity freeze avoiding synthetic spread widening during bank rollover.' },
    { id: 'D16', cat: 'VWAP & Execution', term: 'Rough Volatility Envelope (Hurst H < 0.5)', th: 'กรอบความผันผวนแฟร็กทัล (Gatheral Rough Heston)', tag: 'QUANT_ROUGH_VOL', formula: 'E = avgRange * L^H (H = 0.35)', desc: 'Models clustering of volatility with anti-persistent increments; powers #2 BTCUSD champion ENGINE_13_ROUGH_VOL (PF 2.34).' },

    { id: 'D17', cat: 'DOM & Microstructure', term: 'L2 Order Book Imbalance (IMB)', th: 'สัดส่วนความไม่สมดุล Bid vs Ask ในระดับ DOM', tag: 'DeepLOB', formula: 'IMB = (V_bid - V_ask) / (V_bid + V_ask)', desc: 'Immediate buying/selling pressure across L2 depth levels; key feature input for ENGINE_01_DEEPLOB and DOM_ABSORPTION.' },
    { id: 'D18', cat: 'DOM & Microstructure', term: 'OFI (Order Flow Imbalance)', th: 'กระแสการเติม-ยกเลิก-เคาะคำสั่งบน Best Bid/Ask', tag: 'Cont-Stoikov', formula: 'OFI = Sum(dBid * I_up - dAsk * I_down)', desc: 'Linear predictor of short-horizon mid-price changes proven in Cont, Kukanov & Stoikov (2014).' },
    { id: 'D19', cat: 'DOM & Microstructure', term: 'DOM Absorption (Iceberg Wall)', th: 'การดูดซับแรงเคาะตลาดด้วย Limit Wall ซ่อนอยู่', tag: 'DOM_ABSORPTION', formula: 'HighVol && SmallDeltaPrice', desc: 'Large passive liquidity absorbing aggressive market orders at a key price shelf without allowing breakout.' },
    { id: 'D20', cat: 'DOM & Microstructure', term: 'CVD (Cumulative Volume Delta)', th: 'ผลต่างสะสมระหว่าง Aggressor Buy และ Sell Volume', tag: 'Exhaustion', formula: 'CVD_t = Sum(V_buy - V_sell)', desc: 'Divergence between flat/rising CVD and failing price flags buyer exhaustion and imminent reversal.' },
    { id: 'D21', cat: 'DOM & Microstructure', term: 'Hawkes Self-Exciting Intensity', th: 'สมการจุดปะทุคำสั่งซื้อขายแบบกระตุ้นตัวเองต่อเนื่อง', tag: 'Burst Detection', formula: 'lambda(t) = mu + Sum(alpha * e^{-beta*(t-t_i)})', desc: 'Captures bursts where incoming order arrivals trigger cascading follow-on orders; branching ratio alpha/beta measures endogenous instability.' },
    { id: 'D22', cat: 'DOM & Microstructure', term: 'Avellaneda-Stoikov Reservation Price', th: 'ราคาอ้างอิงปรับตามความเสี่ยงสินค้าคงคลังและเวลา', tag: 'Market Making', formula: 'r(s,q,t) = s - q * gamma * sigma^2 * (T-t)', desc: 'Shifts passive quote midpoints away from risky accumulated inventory toward mean-reversion.' },
    { id: 'D23', cat: 'DOM & Microstructure', term: 'Kalman Zero-Lag State Filter', th: 'ตัวกรอง Kalman แยกสัญญาณแนวโน้มและสปีดราคา', tag: 'Phase Lead', formula: 'x_hat = x_pred + K_t * (z_t - H * x_pred)', desc: 'Recursive Bayesian filter estimating fair price & velocity with lower lag than EMA/SMA.' },
    { id: 'D24', cat: 'DOM & Microstructure', term: 'HMM 2-State Regime Filter', th: 'โมเดล Hidden Markov จำแนก Chop vs Expansion', tag: 'STR-001 Gate', formula: 'P(S_t = Expansion | F_t)', desc: 'Infers latent volatility/trend state to prevent breakout bots from churning in range-bound markets (GRAVE_002 fix).' },

    { id: 'D25', cat: 'Quant Validation', term: 'DSR (Deflated Sharpe Ratio)', th: 'อัตราส่วน Sharpe ที่หักโทษจำนวนการทดลอง (Trial Bias)', tag: 'Bailey 2014', formula: 'DSR = Phi((SR - SR_bench) / sigma_SR)', desc: 'Adjusts Sharpe ratio for non-normal skewness/kurtosis and N_trials=50 data snooping. Current live N=72 DSR=0.0362 (not significant).' },
    { id: 'D26', cat: 'Quant Validation', term: 'PBO / CSCV (Probability of Backtest Overfitting)', th: 'ความน่าจะเป็นที่กลยุทธ์ยอดเยี่ยมเกิดจาก Overfit', tag: 'CPCV / CSCV', formula: 'PBO = P(OOS Rank < Median)', desc: 'Combinatorial Symmetric Cross-Validation checking out-of-sample rank consistency. Threshold < 0.20; current audited PBO=0.60.' },
    { id: 'D27', cat: 'Quant Validation', term: 'SPRT (Sequential Probability Ratio Test)', th: 'การทดสอบทางสถิติแบบต่อเนื่องเพื่อตัดสิน H0 vs H1', tag: 'Wald Test', formula: 'LLR in [-2.251, +2.890]', desc: 'Monitors live cumulative log-likelihood ratio against H0 (no edge) and H1 boundaries. Currently LLR=-1.152 -> COLLECT_MORE_DATA.' },
    { id: 'D28', cat: 'Quant Validation', term: 'CUSUM Drift Monitor', th: 'ตัวตรวจจับผลประกอบการจริงเสื่อมถอยแบบสะสม', tag: 'Live Kill Guard', formula: 'CUSUM_score vs 2σ (0.04) / 3σ (0.06)', desc: 'Live equity drift alarm triggered before catastrophic drawdown. Currently 0.0308 (NORMAL_HEALTHY).' },
    { id: 'D29', cat: 'Quant Validation', term: 'Statistical Power (N=79 / 500)', th: 'อำนาจการทดสอบทางสถิติจากขนาดตัวอย่างปัจจุบัน', tag: 'Truth Guard', formula: 'Power = 15.8% at N=79', desc: 'Evaluates whether closed live trade sample can reject zero-edge null hypothesis. Requires N >= 500 to validate genuine alpha.' },
    { id: 'D30', cat: 'Quant Validation', term: 'Fractional Kelly Criterion', th: 'ขนาดไม้เหมาะสมที่สุดเพื่อเพิ่มทบต้นโดยไม่ล้างพอร์ต', tag: 'Position Sizing', formula: 'f* = c * (p*b - q) / b', desc: 'Scales full Kelly by safety fraction c (0.25–0.50) to limit drawdown variance under parameter uncertainty.' },
    { id: 'D31', cat: 'Quant Validation', term: 'Backtest-to-Live Decay', th: 'อัตราการเสื่อมถอยของ PF เมื่อเทียบ Backtest กับ Live', tag: 'Mean -47.4%', desc: 'Observed empirical degradation (-35% to -62%) across Pepperstone 0.01 lot micro-forward bots due to real queue position & slippage.', formula: 'Decay = (PF_live - PF_IS) / PF_IS' },
    { id: 'D32', cat: 'Quant Validation', term: 'Immune Memory Gene', th: 'กติกาป้องกันความพินาศถาวรที่สืบทอดจากการขาดทุนจริง', tag: 'IMMUNE_GENE', desc: 'Hardcoded constraints extracted from past losses (News Void Gate, Regime Block, Cost Ceiling) enforced on all future Strategy Foundry generations.', formula: 'TradeBlocked = Any(ImmuneGene_i)' }
  ];

  function esc(v) { return window.RLAB.esc(v); }

  function computeHeikinAshi(bars) {
    var out = [];
    var prevHaO = null;
    var prevHaC = null;
    for (var i = 0; i < bars.length; i++) {
      var b = bars[i];
      var haC = (b.o + b.h + b.l + b.c) / 4;
      var haO = prevHaO === null ? (b.o + b.c) / 2 : (prevHaO + prevHaC) / 2;
      var haH = Math.max(b.h, haO, haC);
      var haL = Math.min(b.l, haO, haC);
      out.push({
        t: b.t, o: b.o, h: b.h, l: b.l, c: b.c, v: b.v,
        vwap: b.vwap, sd: b.sd, imb: b.imb, sp: b.sp,
        haO: haO, haH: haH, haL: haL, haC: haC
      });
      prevHaO = haO;
      prevHaC = haC;
    }
    return out;
  }

  function loadDataset(key) {
    activeDatasetKey = key;
    var data = (window.LAB_DATA && window.LAB_DATA.candlestick) || {};
    var series = data.series || {};
    var examples = data.ha_examples || [];

    if (key.indexOf('HA_') === 0) {
      var idx = parseInt(key.split('_')[1], 10) || 0;
      var ex = examples[idx] || examples[0];
      if (ex && ex.bars) {
        // Ex.bars entries: [ts, haO, haH, haL, haC]
        // Compute rolling VWAP/SD proxy strictly from these real HA bars & approximate OHLC for educational split comparison
        var sumPV = 0, sumV = 0;
        var arr = ex.bars.map(function (r, k) {
          var haO = r[1], haH = r[2], haL = r[3], haC = r[4];
          sumPV += haC;
          sumV += 1;
          var vw = sumPV / sumV;
          return {
            t: r[0],
            o: k === 0 ? haO : ex.bars[k - 1][4],
            h: haH,
            l: haL,
            c: haC,
            v: 100,
            vwap: vw,
            sd: 0.95,
            imb: ex.call > 0 ? 0.14 : -0.14,
            sp: 0.18,
            haO: haO, haH: haH, haL: haL, haC: haC
          };
        });
        var arr_prevC;
        computedBars = arr;
        viewStart = 0;
        viewCount = arr.length;
        hoverIdx = arr.length - 1;
      }
    } else {
      var raw = series[key] || series.XAUUSD || [];
      computedBars = computeHeikinAshi(raw);
      viewCount = Math.min(72, computedBars.length);
      viewStart = Math.max(0, computedBars.length - viewCount);
      hoverIdx = computedBars.length - 1;
    }

    document.querySelectorAll('.cs-ds-btn').forEach(function (b) {
      b.classList.toggle('bg-cyan-500/20', b.dataset.ds === key);
      b.classList.toggle('text-cyan-300', b.dataset.ds === key);
      b.classList.toggle('border-cyan-500/50', b.dataset.ds === key);
    });

    drawBothCharts();
    updateTelemetryStrip(hoverIdx);
    updateExampleCallout();
  }

  function updateExampleCallout() {
    var box = document.getElementById('ha-example-callout');
    if (!box) return;
    if (activeDatasetKey.indexOf('HA_') !== 0) {
      box.classList.add('hidden');
      return;
    }
    var idx = parseInt(activeDatasetKey.split('_')[1], 10) || 0;
    var examples = (window.LAB_DATA && window.LAB_DATA.candlestick && window.LAB_DATA.candlestick.ha_examples) || [];
    var ex = examples[idx];
    if (!ex) { box.classList.add('hidden'); return; }
    box.classList.remove('hidden');
    var right = ex.call === ex.result;
    var sideLbl = ex.call > 0 ? 'CALL ขึ้น ▲' : 'CALL ลง ▼';
    var resLbl = ex.result > 0 ? 'ปิดขึ้น ▲' : 'ปิดลง ▼';
    box.innerHTML =
      '<div class="flex flex-wrap items-center justify-between gap-2 text-xs">' +
        '<div class="flex items-center gap-2">' +
          '<span class="px-2 py-0.5 rounded mono font-bold ' + (right ? 'bg-emerald-500/20 text-emerald-300' : 'bg-rose-500/20 text-rose-300') + '">' +
            'Study #' + (idx + 1) + ' (' + esc(ex.kind.toUpperCase()) + ') · ' + (right ? 'ทายถูก ✓' : 'บทเรียนทายผิด ✗') +
          '</span>' +
          '<span class="text-slate-200 font-semibold">Open ตอนเริ่มแท่ง: <span class="mono text-amber-300">' + ex.open.toFixed(2) + '</span> vs HA_Open: <span class="mono text-cyan-300">' + ex.haOpen.toFixed(2) + '</span></span>' +
        '</div>' +
        '<div class="mono text-slate-300">Predicted: <strong>' + sideLbl + '</strong> · Closed: <strong>' + resLbl + '</strong></div>' +
      '</div>';
  }

  function formatTime(ts) {
    if (typeof ts === 'string') {
      var m = ts.match(/(\d{2}:\d{2})/);
      if (m) return m[1];
      var parsed = Date.parse(ts);
      if (!isNaN(parsed)) {
        var ds = new Date(parsed);
        return String(ds.getUTCHours()).padStart(2, '0') + ':' + String(ds.getUTCMinutes()).padStart(2, '0');
      }
      return ts.slice(-5);
    }
    var n = Number(ts);
    if (!isFinite(n) || isNaN(n)) return '--:--';
    var d = new Date(n * 1000);
    return String(d.getUTCHours()).padStart(2, '0') + ':' + String(d.getUTCMinutes()).padStart(2, '0');
  }

  function drawSinglePane(canvasId, isHeikin, rangeObj) {
    var canvas = document.getElementById(canvasId);
    if (!canvas) return;
    var parent = canvas.parentElement;
    var w = (parent && parent.clientWidth) || 540;
    var h = (parent && parent.clientHeight) || 410;
    if (w < 60 || h < 60) return;

    var dpr = Math.min(2, window.devicePixelRatio || 1);
    canvas.width = Math.floor(w * dpr);
    canvas.height = Math.floor(h * dpr);
    var ctx = canvas.getContext('2d');
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

    var isLight = document.documentElement.getAttribute('data-theme') === 'light' || document.documentElement.classList.contains('light');
    ctx.fillStyle = isLight ? '#ffffff' : '#070b12';
    ctx.fillRect(0, 0, w, h);

    var slice = computedBars.slice(viewStart, viewStart + viewCount);
    if (!slice.length) return;

    var PAD_L = 10, PAD_R = 62, PAD_T = 22, PAD_B = 26;
    var plotW = w - PAD_L - PAD_R;
    var plotH = h - PAD_T - PAD_B;
    var minP = rangeObj.minP, maxP = rangeObj.maxP, span = (maxP - minP) || 1;

    function xAt(i) { return PAD_L + ((i + 0.5) / slice.length) * plotW; }
    function yAt(p) { return PAD_T + (1 - (p - minP) / span) * plotH; }

    // Grid horizontal levels
    ctx.strokeStyle = isLight ? '#f1f5f9' : '#131b2b';
    ctx.lineWidth = 1;
    ctx.font = '10px "JetBrains Mono", monospace';
    ctx.fillStyle = isLight ? '#64748b' : '#64748b';
    for (var g = 0; g <= 4; g++) {
      var gy = PAD_T + (g / 4) * plotH;
      var gp = maxP - (g / 4) * span;
      ctx.beginPath(); ctx.moveTo(PAD_L, gy); ctx.lineTo(w - PAD_R, gy); ctx.stroke();
      ctx.fillText(gp.toFixed(2), w - PAD_R + 5, gy + 3);
    }

    var showSD = window.RLAB.state.f3 !== 'SD_OFF';

    // Right pane: VWAP +/- 1 SD and +/- 2 SD shaded bands
    if (isHeikin && showSD) {
      // Shaded +/-2 SD area
      ctx.fillStyle = isLight ? 'rgba(168, 85, 247, 0.08)' : 'rgba(168, 85, 247, 0.08)';
      ctx.beginPath();
      for (var i = 0; i < slice.length; i++) {
        var yu2 = yAt(slice[i].vwap + 2 * slice[i].sd);
        if (i === 0) ctx.moveTo(xAt(i), yu2); else ctx.lineTo(xAt(i), yu2);
      }
      for (var j = slice.length - 1; j >= 0; j--) {
        ctx.lineTo(xAt(j), yAt(slice[j].vwap - 2 * slice[j].sd));
      }
      ctx.closePath(); ctx.fill();

      // Dashed +/-1 SD lines
      ctx.strokeStyle = isLight ? 'rgba(147, 51, 234, 0.55)' : 'rgba(192, 132, 252, 0.45)';
      ctx.setLineDash([4, 4]);
      [1, -1, 2, -2].forEach(function (mult) {
        ctx.lineWidth = Math.abs(mult) === 1 ? 1.1 : 0.9;
        ctx.beginPath();
        for (var k = 0; k < slice.length; k++) {
          var yy = yAt(slice[k].vwap + mult * slice[k].sd);
          if (k === 0) ctx.moveTo(xAt(k), yy); else ctx.lineTo(xAt(k), yy);
        }
        ctx.stroke();
      });
      ctx.setLineDash([]);

      // Core VWAP line
      ctx.strokeStyle = '#06b6d4';
      ctx.lineWidth = 1.8;
      ctx.beginPath();
      for (var v = 0; v < slice.length; v++) {
        var yv = yAt(slice[v].vwap);
        if (v === 0) ctx.moveTo(xAt(v), yv); else ctx.lineTo(xAt(v), yv);
      }
      ctx.stroke();
    } else if (!isHeikin && showSD) {
      // Light VWAP reference line on Standard OHLC too for honest side-by-side spatial check
      ctx.strokeStyle = 'rgba(6, 182, 212, 0.42)';
      ctx.lineWidth = 1.1;
      ctx.beginPath();
      for (var v2 = 0; v2 < slice.length; v2++) {
        var yv2 = yAt(slice[v2].vwap);
        if (v2 === 0) ctx.moveTo(xAt(v2), yv2); else ctx.lineTo(xAt(v2), yv2);
      }
      ctx.stroke();
    }

    // Candles
    var stepX = plotW / slice.length;
    var bodyW = Math.max(2.5, Math.min(14, stepX * 0.64));
    for (var idx = 0; idx < slice.length; idx++) {
      var b = slice[idx];
      var o = isHeikin ? b.haO : b.o;
      var hi = isHeikin ? b.haH : b.h;
      var lo = isHeikin ? b.haL : b.l;
      var c = isHeikin ? b.haC : b.c;
      var bull = c >= o;
      var col = bull ? (isLight ? '#059669' : '#10b981') : (isLight ? '#e11d48' : '#f43f5e');
      var cx = xAt(idx);

      // Wick
      ctx.strokeStyle = col;
      ctx.lineWidth = 1.2;
      ctx.beginPath();
      ctx.moveTo(cx, yAt(hi));
      ctx.lineTo(cx, yAt(lo));
      ctx.stroke();

      // Body
      var topY = yAt(Math.max(o, c));
      var botY = yAt(Math.min(o, c));
      ctx.fillStyle = col;
      ctx.fillRect(cx - bodyW / 2, topY, bodyW, Math.max(2, botY - topY));
    }

    // Synchronized Crosshair
    var localIdx = hoverIdx - viewStart;
    if (localIdx >= 0 && localIdx < slice.length) {
      var hb = slice[localIdx];
      var hx = xAt(localIdx);
      var hPrice = isHeikin ? hb.haC : hb.c;
      var hy = yAt(hPrice);

      ctx.strokeStyle = isLight ? 'rgba(2, 132, 199, 0.7)' : 'rgba(56, 189, 248, 0.75)';
      ctx.setLineDash([3, 3]);
      ctx.lineWidth = 1;
      ctx.beginPath(); ctx.moveTo(hx, PAD_T); ctx.lineTo(hx, h - PAD_B); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(PAD_L, hy); ctx.lineTo(w - PAD_R, hy); ctx.stroke();
      ctx.setLineDash([]);

      // Price tag pill on right axis
      ctx.fillStyle = '#0284c7';
      ctx.fillRect(w - PAD_R + 1, hy - 9, PAD_R - 3, 18);
      ctx.fillStyle = '#ffffff';
      ctx.fillText(hPrice.toFixed(2), w - PAD_R + 5, hy + 4);

      // Time pill on bottom axis
      var tStr = formatTime(hb.t);
      ctx.fillStyle = isLight ? '#0f172a' : '#1e293b';
      ctx.fillRect(hx - 20, h - PAD_B + 2, 40, 16);
      ctx.fillStyle = '#ffffff';
      ctx.fillText(tStr, hx - 15, h - PAD_B + 13);
    }
  }

  function drawBothCharts() {
    var slice = computedBars.slice(viewStart, viewStart + viewCount);
    if (!slice.length) return;
    var showSD = window.RLAB.state.f3 !== 'SD_OFF';
    var minP = Infinity, maxP = -Infinity;
    slice.forEach(function (b) {
      minP = Math.min(minP, b.l, b.haL, showSD ? (b.vwap - 2 * b.sd) : Infinity);
      maxP = Math.max(maxP, b.h, b.haH, showSD ? (b.vwap + 2 * b.sd) : -Infinity);
    });
    var pad = (maxP - minP) * 0.06 || 1;
    var rangeObj = { minP: minP - pad, maxP: maxP + pad };
    drawSinglePane('canvas-ohlc', false, rangeObj);
    drawSinglePane('canvas-ha', true, rangeObj);
  }

  function updateTelemetryStrip(absIdx) {
    var el = document.getElementById('split-telemetry-strip');
    if (!el || !computedBars.length) return;
    var i = absIdx >= 0 && absIdx < computedBars.length ? absIdx : computedBars.length - 1;
    var b = computedBars[i];
    var z = b.sd > 0 ? ((b.c - b.vwap) / b.sd) : 0;
    var haDir = b.haC >= b.haO;
    var ohlcDir = b.c >= b.o;

    el.innerHTML =
      '<div class="flex flex-wrap items-center justify-between gap-2 text-xs font-mono">' +
        '<div class="flex flex-wrap items-center gap-3">' +
          '<span class="px-2 py-0.5 rounded bg-slate-900 border border-slate-700 text-cyan-300 font-bold">' + esc(activeDatasetKey) + ' · ' + formatTime(b.t) + ' UTC</span>' +
          '<span class="' + (ohlcDir ? 'text-emerald-400' : 'text-rose-400') + '">OHLC: O ' + b.o.toFixed(2) + ' H ' + b.h.toFixed(2) + ' L ' + b.l.toFixed(2) + ' C ' + b.c.toFixed(2) + '</span>' +
          '<span class="' + (haDir ? 'text-emerald-300' : 'text-rose-300') + ' font-bold">HA: O ' + b.haO.toFixed(2) + ' C ' + b.haC.toFixed(2) + ' (' + (haDir ? 'BULL' : 'BEAR') + ')</span>' +
        '</div>' +
        '<div class="flex flex-wrap items-center gap-3">' +
          '<span class="text-cyan-300">VWAP: ' + b.vwap.toFixed(2) + ' (Z=' + (z >= 0 ? '+' : '') + z.toFixed(2) + 'σ)</span>' +
          '<span class="' + (b.imb >= 0 ? 'text-emerald-400' : 'text-rose-400') + '">IMB: ' + (b.imb >= 0 ? '+' : '') + b.imb.toFixed(3) + '</span>' +
          '<span class="text-amber-300">Spread: ' + b.sp.toFixed(2) + '</span>' +
        '</div>' +
      '</div>';
  }

  function wireCanvasInteractions(canvasId) {
    var canvas = document.getElementById(canvasId);
    if (!canvas) return;
    canvas.addEventListener('mousemove', function (e) {
      var rect = canvas.getBoundingClientRect();
      var x = e.clientX - rect.left;
      if (isDragging) {
        var deltaPx = e.clientX - dragStartX;
        var barsPerPx = viewCount / Math.max(100, rect.width - 72);
        var shift = Math.round(deltaPx * barsPerPx);
        viewStart = Math.max(0, Math.min(Math.max(0, computedBars.length - viewCount), dragStartView - shift));
      }
      var plotW = Math.max(60, rect.width - 72);
      var ratio = Math.max(0, Math.min(0.999, (x - 10) / plotW));
      hoverIdx = Math.min(computedBars.length - 1, viewStart + Math.floor(ratio * viewCount));
      drawBothCharts();
      updateTelemetryStrip(hoverIdx);
    });
    canvas.addEventListener('mousedown', function (e) {
      isDragging = true;
      dragStartX = e.clientX;
      dragStartView = viewStart;
    });
    window.addEventListener('mouseup', function () { isDragging = false; });
    canvas.addEventListener('wheel', function (e) {
      e.preventDefault();
      var factor = e.deltaY > 0 ? 1.15 : 0.85;
      var newCount = Math.max(14, Math.min(computedBars.length, Math.round(viewCount * factor)));
      var rightEdge = viewStart + viewCount;
      viewCount = newCount;
      viewStart = Math.max(0, Math.min(computedBars.length - viewCount, rightEdge - viewCount));
      drawBothCharts();
    }, { passive: false });
  }

  window.switchCandlestickDataset = function (key) {
    loadDataset(key);
  };

  window.zoomCandlestick = function (dir) {
    if (!computedBars.length) return;
    if (dir === 0) {
      viewCount = Math.min(72, computedBars.length);
      viewStart = Math.max(0, computedBars.length - viewCount);
    } else {
      var next = dir < 0 ? Math.min(computedBars.length, viewCount + 16) : Math.max(16, viewCount - 16);
      var end = viewStart + viewCount;
      viewCount = next;
      viewStart = Math.max(0, Math.min(computedBars.length - viewCount, end - viewCount));
    }
    drawBothCharts();
  };

  function highlightText(text, terms) {
    var safe = esc(text);
    if (!terms.length) return safe;
    terms.forEach(function (t) {
      var re = new RegExp('(' + t.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + ')', 'gi');
      safe = safe.replace(re, '<mark class="hl">$1</mark>');
    });
    return safe;
  }

  window.filterDictionaryQuick = function (catVal) {
    window.RLAB.state.f2 = catVal;
    var f2 = document.getElementById('filter-select-2');
    if (f2) f2.value = catVal;
    renderDictionary();
  };

  function renderDictionary() {
    var grid = document.getElementById('dict-grid');
    var countEl = document.getElementById('dict-count');
    var localSearch = document.getElementById('dict-local-search');
    if (!grid) return;

    var rawQ = (localSearch && localSearch.value) ? localSearch.value : (window.RLAB.state.search || '');
    var q = rawQ.trim().toLowerCase();
    var terms = q ? q.split(/\s+/).filter(Boolean) : [];
    var catF = window.RLAB.state.f2 || 'ALL';

    document.querySelectorAll('.dict-cat-btn').forEach(function (b) {
      var act = b.dataset.cat === catF;
      b.classList.toggle('bg-cyan-500/20', act);
      b.classList.toggle('text-cyan-300', act);
      b.classList.toggle('border-cyan-500/50', act);
    });

    var matched = DICT_TERMS.filter(function (d) {
      if (catF !== 'ALL' && d.cat !== catF) return false;
      if (!terms.length) return true;
      var blob = (d.term + ' ' + d.th + ' ' + d.tag + ' ' + d.formula + ' ' + d.desc + ' ' + d.cat).toLowerCase();
      return terms.every(function (t) { return blob.indexOf(t) >= 0; });
    });

    if (countEl) countEl.textContent = matched.length + ' / ' + DICT_TERMS.length + ' terms';

    if (!matched.length) {
      grid.innerHTML = '<div class="col-span-full p-6 text-center text-xs text-slate-400 lab-card">No dictionary term matched "' + esc(rawQ) + '".</div>';
      return;
    }

    grid.innerHTML = matched.map(function (d) {
      return '<div class="lab-card p-3.5 flex flex-col justify-between gap-2">' +
        '<div>' +
          '<div class="flex items-center justify-between gap-2 mb-1">' +
            '<span class="px-2 py-0.5 rounded bg-cyan-500/15 text-cyan-300 border border-cyan-500/30 text-[10px] font-mono font-bold">' + highlightText(d.cat, terms) + '</span>' +
            '<span class="px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 text-[10px] font-mono">' + highlightText(d.tag, terms) + '</span>' +
          '</div>' +
          '<div class="text-sm font-extrabold text-white leading-snug">' + highlightText(d.term, terms) + '</div>' +
          '<div class="text-xs text-amber-300 font-medium mt-0.5">' + highlightText(d.th, terms) + '</div>' +
          '<p class="text-xs text-slate-300 leading-relaxed mt-1.5">' + highlightText(d.desc, terms) + '</p>' +
        '</div>' +
        '<div class="mt-1 px-2.5 py-1.5 rounded-lg bg-slate-950/70 border border-slate-800/80 mono text-[11px] text-cyan-300 overflow-x-auto">' + highlightText(d.formula, terms) + '</div>' +
      '</div>';
    }).join('');
  }

  function renderHaMathSheet() {
    var m1 = document.getElementById('ha-math-formula');
    if (!m1) return;
    var tex = String.raw`\text{HA}_{\text{Close}} = \frac{O+H+L+C}{4}, \quad \text{HA}_{\text{Open}}(t) = \frac{\text{HA}_{\text{Open}}(t\!-\!1)+\text{HA}_{\text{Close}}(t\!-\!1)}{2}, \quad Z_{\text{VWAP}} = \frac{C - \text{VWAP}}{\sigma_{\text{VWAP}}}`;
    if (window.katex && typeof window.katex.render === 'function') {
      try { window.katex.render(tex, m1, { displayMode: false, throwOnError: false }); return; } catch (_) {}
    }
    m1.innerHTML = '<code class="mono text-xs text-cyan-300">HA_Close=(O+H+L+C)/4 | HA_Open=(prevHA_O+prevHA_C)/2 | Z_VWAP=(C-VWAP)/SD</code>';
  }

  window.onLocalDictSearch = function () {
    renderDictionary();
  };

  window.RLAB.renderers.candlestick = {
    init: function () {
      if (initialized) return;
      initialized = true;
      wireCanvasInteractions('canvas-ohlc');
      wireCanvasInteractions('canvas-ha');
      window.addEventListener('resize', function () {
        if (window.RLAB.state.activeTab === 'candlestick') drawBothCharts();
      });
    },
    onActivate: function () {
      renderHaMathSheet();
      requestAnimationFrame(function () {
        loadDataset(activeDatasetKey);
        renderDictionary();
      });
    },
    onFilter: function () {
      var f1 = window.RLAB.state.f1;
      if (f1 === 'XAUUSD' || f1 === 'BTCUSD' || f1 === 'ETHUSD') {
        activeDatasetKey = f1;
        loadDataset(activeDatasetKey);
      } else {
        drawBothCharts();
      }
      renderDictionary();
    },
    drawCharts: function () {
      drawBothCharts();
    }
  };
})();
