/* ==========================================================================
   ANTIGRAVITY QUANT · Page 2: Data Center Logic
   - TradingView Lightweight Charts v4.2.1 Replay & Indicators
   - Floating QuickTrade Paper Simulator (Buy / Sell / Flatten)
   - Synchronized HiDPI Order Flow & Spread Canvas
   - Pipeline Health Strip (Latency, Tick Freq, Missing Bars Sparklines)
   - 25-Level DoM Ladder with 100ms Batch DOM Flush Engine
   ========================================================================== */
import { mountShell, updateShellTelemetry } from './shell.js';

const TF_SECONDS = {
  M1: 60,
  M5: 300,
  M15: 900,
  M30: 1800,
  H1: 3600,
  H4: 14400,
  D1: 86400,
};

const SYMBOL_ICONS = {
  XAUUSD: '🥇',
  BTCUSD: '🪙',
  ETHUSD: '⟠',
  'GOLD-PERP': '⚡',
};

const state = {
  meta: null,
  symbolCache: {},
  currentSymbol: 'XAUUSD',
  timeframe: 'M1',
  chartMode: 'candles', // 'candles' | 'area'
  showVwap: true,
  showGaps: true,
  isPlaying: true,
  speed: 1,
  replayIndex: 0,
  activeMicroBar: null,
  currentBid: 0,
  currentAsk: 0,
  currentSpread: 0,
  resampledBars: [],
  paperBalance: 10000.0,
  openPositions: [],
  paperDeals: [],
  nextTicket: 810042,
  activeDrawerTab: 'open',
  // Performance Batch State for 25-Level DoM
  domRows: [],
  domDirty: false,
  pendingDom: null,
  // Timers
  microTimer: null,
  barAdvanceMsAcc: 0,
  batchTimer: null,
  telemetryTimer: null,
  // Chart instances
  lwChart: null,
  candleSeries: null,
  areaSeries: null,
  vwapSeries: null,
  pocSeries: null,
  positionLines: [],
  visibleLogicalRange: null,
};

const $ = (id) => document.getElementById(id);

// ========================================================================
// FORMATTING HELPERS
// ========================================================================
function fmtPrice(val, digits = 2) {
  if (val == null || Number.isNaN(val)) return '--';
  return Number(val).toLocaleString('en-US', {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
}

function fmtInt(val) {
  if (val == null || Number.isNaN(val)) return '--';
  return Math.round(val).toLocaleString('en-US');
}

function fmtUtcShort(epochSec) {
  const d = new Date(epochSec * 1000);
  const y = d.getUTCFullYear();
  const m = String(d.getUTCMonth() + 1).padStart(2, '0');
  const day = String(d.getUTCDate()).padStart(2, '0');
  const hh = String(d.getUTCHours()).padStart(2, '0');
  const mm = String(d.getUTCMinutes()).padStart(2, '0');
  return `${y}-${m}-${day} ${hh}:${mm}`;
}

function showToast(msg, tone = 'info') {
  const stack = $('toast-stack');
  if (!stack) return;
  const item = document.createElement('div');
  item.className = `toast-item mono ${tone}`;
  item.textContent = msg;
  stack.appendChild(item);
  setTimeout(() => {
    item.style.opacity = '0';
    item.style.transition = 'opacity 0.2s ease';
    setTimeout(() => item.remove(), 220);
  }, 3000);
}

// ========================================================================
// THEME & SHARED SHELL TELEMETRY SYNC
// ========================================================================
function isLightTheme() {
  return document.documentElement.getAttribute('data-theme') === 'light';
}

function applyChartTheme() {
  if (!state.lwChart) return;
  const light = isLightTheme();
  state.lwChart.applyOptions({
    layout: {
      background: { type: 'solid', color: light ? '#ffffff' : '#080d17' },
      textColor: light ? '#334155' : '#94a3b8',
    },
    grid: {
      vertLines: { color: light ? '#f1f5f9' : 'rgba(148, 163, 184, 0.07)' },
      horzLines: { color: light ? '#f1f5f9' : 'rgba(148, 163, 184, 0.07)' },
    },
    rightPriceScale: {
      borderColor: light ? '#cbd5e1' : '#1b2438',
    },
    timeScale: {
      borderColor: light ? '#cbd5e1' : '#1b2438',
    },
    crosshair: {
      vertLine: { color: light ? '#94a3b8' : '#334155' },
      horzLine: { color: light ? '#94a3b8' : '#334155' },
    },
  });
  drawOrderFlowCanvas();
  updatePipelineHealth();
}

async function fetchJsonSafe(url) {
  try {
    const res = await fetch(`${url}?t=${Date.now()}`, { cache: 'no-store' });
    if (!res.ok) return null;
    return await res.json();
  } catch (e) {
    return null;
  }
}

async function fetchJsonTracked(url, label, failedSources) {
  try {
    const res = await fetch(`${url}?t=${Date.now()}`, { cache: 'no-store' });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (e) {
    if (Array.isArray(failedSources)) failedSources.push(label);
    return null;
  }
}

async function loadTelemetryFeeds() {
  const failedSources = [];
  const [meta, watchdog, liveStatus, webAlerts, overviewSummary] = await Promise.all([
    fetchJsonTracked('data/dc_meta.json', 'dc_meta', failedSources),
    fetchJsonTracked('data/watchdog_status.json', 'watchdog_status', failedSources),
    fetchJsonTracked('data/live_status.json', 'live_status', failedSources),
    fetchJsonTracked('data/web_alerts.json', 'web_alerts', failedSources),
    fetchJsonTracked('data/overview_summary.json', 'overview_summary', failedSources),
  ]);

  state.meta = meta;

  // Format Watchdog alert objects consistently with overview.js / audit.js for shell.js popover
  const wdForShell = watchdog
    ? {
        ...watchdog,
        active_alerts: (watchdog.active_alerts || []).map((a) =>
          typeof a === 'string'
            ? a
            : `${a.symbol}: ${a.alert || 'RECORDER_STALLED'} (${a.duration_sec}s stalled · Last: ${a.last_seen})`
        ),
      }
    : null;

  updateShellTelemetry({
    watchdog: wdForShell,
    webAlerts,
    liveStatus,
    overviewSummary,
    failedSources,
  });
}

  // ========================================================================
  // SYMBOL LOADING & UNPACKING
  // ========================================================================
  function unpackBars(rawBars) {
    return rawBars.map((b) => ({
      t: b[0],
      o: b[1],
      h: b[2],
      l: b[3],
      c: b[4],
      v: b[5],
      tk: b[6],
      d: b[7],
      cvd: b[8],
      sp: b[9],
      bv: b[10],
      av: b[11],
      imb: b[12],
      du: b[13],
      vw: b[14],
      sd: b[15],
      poc: b[16],
      vah: b[17],
      val: b[18],
      lb: b[19],
      la: b[20],
      gap: b[21] || 0,
    }));
  }

  async function loadSymbol(sym) {
    state.currentSymbol = sym;

    // Update UI selectors
    const sel = $('symbol-select');
    if (sel) sel.value = sym;
    const iconEl = $('symbol-badge-icon');
    if (iconEl) iconEl.textContent = SYMBOL_ICONS[sym] || '📈';
    document.querySelectorAll('.sym-pill').forEach((btn) => {
      btn.classList.toggle('active', btn.dataset.sym === sym);
    });

    if (!state.symbolCache[sym]) {
      const raw = await fetchJsonSafe(`data/dc_${sym}.json`);
      if (!raw || !Array.isArray(raw.bars) || !raw.bars.length) {
        showToast(`ไม่สามารถโหลดข้อมูล ${sym} ได้`, 'warn');
        return;
      }
      state.symbolCache[sym] = {
        ...raw,
        unpackedBars: unpackBars(raw.bars),
      };
    }

    const symData = state.symbolCache[sym];
    const domLabel = $('dom-symbol-label');
    if (domLabel) domLabel.textContent = symData.displayName || sym;

    // Set replay index to defaultReplayIndex
    const maxIdx = symData.unpackedBars.length - 1;
    state.replayIndex = Math.min(maxIdx, Math.max(30, symData.defaultReplayIndex || maxIdx - 120));

    const scrubber = $('replay-scrubber');
    if (scrubber) {
      scrubber.min = 30;
      scrubber.max = maxIdx;
      scrubber.value = state.replayIndex;
    }

    primeActiveBarFromIndex();
    rebuildChartSeries(true);
    updateAllReadouts();
    renderRecordedTradesTab();
  }

  function getActiveSymData() {
    return state.symbolCache[state.currentSymbol] || null;
  }

  function primeActiveBarFromIndex() {
    const symData = getActiveSymData();
    if (!symData) return;
    const bar = symData.unpackedBars[state.replayIndex];
    if (!bar) return;

    state.activeMicroBar = {
      ...bar,
      targetC: bar.c,
      targetH: bar.h,
      targetL: bar.l,
      targetTk: bar.tk,
      // Start forming if playing, or full bar if paused
      c: state.isPlaying ? bar.o : bar.c,
      h: state.isPlaying ? Math.max(bar.o, bar.c) : bar.h,
      l: state.isPlaying ? Math.min(bar.o, bar.c) : bar.l,
    };

    const spread = Math.max(symData.pipSize * 0.2, bar.sp || symData.pipSize);
    state.currentSpread = spread;
    state.currentBid = state.activeMicroBar.c;
    state.currentAsk = Number((state.currentBid + spread).toFixed(symData.digits || 2));
  }

  // ========================================================================
  // TIMEFRAME RESAMPLING & TRADINGVIEW LIGHTWEIGHT CHARTS
  // ========================================================================
  function getResampledSequence() {
    const symData = getActiveSymData();
    if (!symData) return [];

    const bars = symData.unpackedBars.slice(0, state.replayIndex);
    if (state.activeMicroBar) bars.push(state.activeMicroBar);
    if (!bars.length) return [];

    const tfSec = TF_SECONDS[state.timeframe] || 60;
    if (tfSec === 60) {
      return bars.map((b) => {
        const tk = Math.max(1, b.tk);
        const buyRatio = Math.min(1, Math.max(0, (tk + b.d) / (2 * tk)));
        const buyVol = Math.round(b.v * buyRatio);
        const sellVol = Math.max(0, b.v - buyVol);
        return {
          time: b.t,
          open: b.o,
          high: b.h,
          low: b.l,
          close: b.c,
          vw: b.vw,
          poc: b.poc,
          buyVol,
          sellVol,
          spread: b.sp,
          gap: b.gap,
          delta: b.d,
          cvd: b.cvd,
        };
      });
    }

    const out = [];
    let cur = null;
    let curSpSum = 0;
    let curCnt = 0;

    for (let i = 0; i < bars.length; i++) {
      const b = bars[i];
      const bucket = Math.floor(b.t / tfSec) * tfSec;
      const tk = Math.max(1, b.tk);
      const buyRatio = Math.min(1, Math.max(0, (tk + b.d) / (2 * tk)));
      const bv = Math.round(b.v * buyRatio);
      const sv = Math.max(0, b.v - bv);

      if (!cur || cur.time !== bucket) {
        if (cur) {
          cur.spread = curSpSum / Math.max(1, curCnt);
          out.push(cur);
        }
        cur = {
          time: bucket,
          open: b.o,
          high: b.h,
          low: b.l,
          close: b.c,
          vw: b.vw,
          poc: b.poc,
          buyVol: bv,
          sellVol: sv,
          spread: b.sp,
          gap: b.gap,
          delta: b.d,
          cvd: b.cvd,
        };
        curSpSum = b.sp;
        curCnt = 1;
      } else {
        cur.high = Math.max(cur.high, b.h);
        cur.low = Math.min(cur.low, b.l);
        cur.close = b.c;
        cur.vw = b.vw;
        cur.poc = b.poc;
        cur.buyVol += bv;
        cur.sellVol += sv;
        cur.delta += b.d;
        cur.cvd = b.cvd;
        if (b.gap > cur.gap) cur.gap = b.gap;
        curSpSum += b.sp;
        curCnt++;
      }
    }
    if (cur) {
      cur.spread = curSpSum / Math.max(1, curCnt);
      out.push(cur);
    }
    return out;
  }

  function initLightweightChart() {
    const container = $('lw-chart-container');
    if (!container || typeof LightweightCharts === 'undefined') return;

    const light = isLightTheme();
    const chart = LightweightCharts.createChart(container, {
      width: container.clientWidth || 720,
      height: container.clientHeight || 380,
      layout: {
        background: { type: 'solid', color: light ? '#ffffff' : '#080d17' },
        textColor: light ? '#334155' : '#94a3b8',
        fontFamily: "'JetBrains Mono', monospace",
        fontSize: 11,
      },
      grid: {
        vertLines: { color: light ? '#f1f5f9' : 'rgba(148, 163, 184, 0.07)' },
        horzLines: { color: light ? '#f1f5f9' : 'rgba(148, 163, 184, 0.07)' },
      },
      crosshair: {
        mode: LightweightCharts.CrosshairMode.Normal,
      },
      rightPriceScale: {
        borderColor: light ? '#cbd5e1' : '#1b2438',
        scaleMargins: { top: 0.12, bottom: 0.12 },
      },
      timeScale: {
        borderColor: light ? '#cbd5e1' : '#1b2438',
        timeVisible: true,
        secondsVisible: false,
        rightOffset: 6,
      },
    });

    const candleSeries = chart.addCandlestickSeries({
      upColor: '#10b981',
      downColor: '#ef4444',
      borderUpColor: '#10b981',
      borderDownColor: '#ef4444',
      wickUpColor: '#10b981',
      wickDownColor: '#ef4444',
    });

    const areaSeries = chart.addAreaSeries({
      topColor: 'rgba(56, 189, 248, 0.32)',
      bottomColor: 'rgba(56, 189, 248, 0.02)',
      lineColor: '#38bdf8',
      lineWidth: 2,
      visible: false,
    });

    const vwapSeries = chart.addLineSeries({
      color: '#38bdf8',
      lineWidth: 1.5,
      priceLineVisible: false,
      lastValueVisible: true,
      title: 'VWAP',
    });

    const pocSeries = chart.addLineSeries({
      color: '#f5b301',
      lineWidth: 1.2,
      lineStyle: LightweightCharts.LineStyle.Dashed,
      priceLineVisible: false,
      lastValueVisible: false,
      title: 'POC',
    });

    chart.subscribeCrosshairMove((param) => {
      if (!param || !param.time) {
        updateOhlcStrip(null);
        return;
      }
      const cVal = param.seriesData.get(candleSeries);
      if (cVal) {
        updateOhlcStrip(cVal);
        return;
      }
      const matched = state.resampledBars.find((b) => b.time === param.time);
      if (matched) {
        updateOhlcStrip(matched);
      } else {
        updateOhlcStrip(null);
      }
    });

    chart.timeScale().subscribeVisibleLogicalRangeChange((range) => {
      state.visibleLogicalRange = range;
      drawOrderFlowCanvas();
    });

    const ro = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const { width, height } = entry.contentRect;
        if (width > 10 && height > 10) {
          chart.applyOptions({ width: Math.floor(width), height: Math.floor(height) });
        }
      }
      drawOrderFlowCanvas();
    });
    ro.observe(container);

    state.lwChart = chart;
    state.candleSeries = candleSeries;
    state.areaSeries = areaSeries;
    state.vwapSeries = vwapSeries;
    state.pocSeries = pocSeries;
  }

  function getPrimarySeries() {
    return state.chartMode === 'area' ? state.areaSeries : state.candleSeries;
  }

  function rebuildChartSeries(fitRecent = false) {
    if (!state.lwChart || !state.candleSeries) return;
    const seq = getResampledSequence();
    state.resampledBars = seq;
    if (!seq.length) return;

    const symData = getActiveSymData();
    const digits = symData ? symData.digits : 2;
    const minMove = digits === 2 ? 0.01 : 0.001;

    state.candleSeries.applyOptions({
      priceFormat: { type: 'price', precision: digits, minMove },
      visible: state.chartMode === 'candles',
    });
    state.areaSeries.applyOptions({
      priceFormat: { type: 'price', precision: digits, minMove },
      visible: state.chartMode === 'area',
    });

    state.candleSeries.setData(seq.map((b) => ({
      time: b.time,
      open: b.open,
      high: b.high,
      low: b.low,
      close: b.close,
    })));

    state.areaSeries.setData(seq.map((b) => ({
      time: b.time,
      value: b.close,
    })));

    if (state.showVwap) {
      state.vwapSeries.applyOptions({ visible: true });
      state.pocSeries.applyOptions({ visible: true });
      state.vwapSeries.setData(seq.filter((b) => b.vw > 0).map((b) => ({ time: b.time, value: b.vw })));
      state.pocSeries.setData(seq.filter((b) => b.poc > 0).map((b) => ({ time: b.time, value: b.poc })));
    } else {
      state.vwapSeries.applyOptions({ visible: false });
      state.pocSeries.applyOptions({ visible: false });
    }

    syncChartMarkers();
    syncPositionPriceLines();

    if (fitRecent) {
      const total = seq.length;
      const from = Math.max(0, total - 90);
      state.lwChart.timeScale().setVisibleLogicalRange({ from, to: total + 4 });
    }

    drawOrderFlowCanvas();
  }

  function updateLatestChartBar() {
    if (!state.candleSeries || !state.resampledBars.length) return;
    const seq = getResampledSequence();
    state.resampledBars = seq;
    const last = seq[seq.length - 1];
    if (!last) return;

    state.candleSeries.update({
      time: last.time,
      open: last.open,
      high: last.high,
      low: last.low,
      close: last.close,
    });
    state.areaSeries.update({
      time: last.time,
      value: last.close,
    });
    if (state.showVwap && last.vw > 0) {
      state.vwapSeries.update({ time: last.time, value: last.vw });
    }
    if (state.showVwap && last.poc > 0) {
      state.pocSeries.update({ time: last.time, value: last.poc });
    }
  }

  function syncChartMarkers() {
    if (!state.candleSeries || !state.areaSeries) return;
    const activeSeries = getPrimarySeries();
    const inactiveSeries = state.chartMode === 'area' ? state.candleSeries : state.areaSeries;
    inactiveSeries.setMarkers([]);

    const markers = [];
    const seq = state.resampledBars;
    if (!seq.length) {
      activeSeries.setMarkers([]);
      return;
    }
    const minT = seq[0].time;
    const maxT = seq[seq.length - 1].time;

    // 1. Missing-Bar Gap Warnings
    if (state.showGaps) {
      for (let i = 0; i < seq.length; i++) {
        if (seq[i].gap > 0) {
          markers.push({
            time: seq[i].time,
            position: 'aboveBar',
            color: '#f59e0b',
            shape: 'circle',
            text: `-${seq[i].gap}m`,
          });
        }
      }
    }

    // 2. Recorded Bot Trades in visible history
    const symData = getActiveSymData();
    if (symData && Array.isArray(symData.trades)) {
      const tfSec = TF_SECONDS[state.timeframe] || 60;
      for (const tr of symData.trades) {
        if (tr.event !== 'OPEN') continue;
        const bucket = Math.floor(tr.t / tfSec) * tfSec;
        if (bucket >= minT && bucket <= maxT) {
          const isBuy = tr.side.toLowerCase() === 'buy';
          markers.push({
            time: bucket,
            position: isBuy ? 'belowBar' : 'aboveBar',
            color: isBuy ? '#22c55e' : '#ef4444',
            shape: isBuy ? 'arrowUp' : 'arrowDown',
            text: isBuy ? 'BOT B' : 'BOT S',
          });
        }
      }
    }

    markers.sort((a, b) => a.time - b.time);
    activeSeries.setMarkers(markers);
  }

  function syncPositionPriceLines() {
    if (!state.candleSeries || !state.areaSeries) return;
    for (const item of state.positionLines) {
      try {
        item.series.removePriceLine(item.line);
      } catch (e) {}
    }
    state.positionLines = [];

    const activeSeries = getPrimarySeries();
    const symPositions = state.openPositions.filter((p) => p.symbol === state.currentSymbol);
    for (const pos of symPositions) {
      const line = activeSeries.createPriceLine({
        price: pos.entryPrice,
        color: pos.side === 'BUY' ? '#22c55e' : '#ef4444',
        lineWidth: 1,
        lineStyle: LightweightCharts.LineStyle.Dotted,
        axisLabelVisible: true,
        title: `${pos.side} ${pos.lot.toFixed(2)}`,
      });
      state.positionLines.push({ series: activeSeries, line });
    }
  }

  // ========================================================================
  // ORDER FLOW & SPREAD CANVAS (SYNCHRONIZED WITH LIGHTWEIGHT CHARTS)
  // ========================================================================
  function drawOrderFlowCanvas() {
    const canvas = $('orderflow-canvas');
    if (!canvas) return;
    const parent = canvas.parentElement;
    if (!parent) return;

    const w = parent.clientWidth;
    const h = parent.clientHeight;
    if (w < 20 || h < 20) return;

    const dpr = window.devicePixelRatio || 1;
    if (canvas.width !== Math.floor(w * dpr) || canvas.height !== Math.floor(h * dpr)) {
      canvas.width = Math.floor(w * dpr);
      canvas.height = Math.floor(h * dpr);
    }

    const ctx = canvas.getContext('2d');
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, w, h);

    const bars = state.resampledBars;
    if (!bars.length) return;

    const symData = getActiveSymData();
    const pipSize = symData ? symData.pipSize : 0.1;

    let fromIdx = Math.max(0, bars.length - 80);
    let toIdx = bars.length - 1;
    if (state.visibleLogicalRange) {
      fromIdx = Math.max(0, Math.floor(state.visibleLogicalRange.from));
      toIdx = Math.min(bars.length - 1, Math.ceil(state.visibleLogicalRange.to));
    }
    if (toIdx < fromIdx) return;

    const slice = bars.slice(fromIdx, toIdx + 1);
    const padL = 8;
    const padR = 46;
    const padT = 12;
    const padB = 20;
    const plotW = Math.max(10, w - padL - padR);
    const plotH = Math.max(10, h - padT - padB);

    const light = isLightTheme();
    const gridColor = light ? '#e2e8f0' : 'rgba(148, 163, 184, 0.08)';
    const textColor = light ? '#475569' : '#64748b';

    let maxVol = 10;
    let maxSp = 0.5;
    for (const b of slice) {
      maxVol = Math.max(maxVol, b.buyVol, b.sellVol);
      const spPips = b.spread / pipSize;
      if (spPips > maxSp) maxSp = spPips;
    }
    maxVol *= 1.15;
    maxSp *= 1.25;

    // Grid lines + right volume labels
    ctx.strokeStyle = gridColor;
    ctx.lineWidth = 1;
    ctx.font = '10px "JetBrains Mono", monospace';
    ctx.fillStyle = textColor;
    ctx.textAlign = 'left';

    for (let g = 0; g <= 2; g++) {
      const y = padT + (plotH * g) / 2;
      ctx.beginPath();
      ctx.moveTo(padL, y);
      ctx.lineTo(w - padR, y);
      ctx.stroke();
      const volLbl = Math.round(maxVol * (1 - g / 2));
      ctx.fillText(volLbl >= 1000 ? `${(volLbl / 1000).toFixed(1)}K` : String(volLbl), w - padR + 5, y + 3);
    }

    const n = slice.length;
    const stepW = plotW / Math.max(1, n);
    const pairW = Math.max(2, stepW * 0.72);
    const barW = Math.max(1, pairW / 2 - 0.5);

    // Draw paired Buy Volume (green) & Sell Volume (red) bars
    for (let i = 0; i < n; i++) {
      const b = slice[i];
      const cx = padL + (i + 0.5) * stepW;
      const buyH = (b.buyVol / maxVol) * plotH;
      const sellH = (b.sellVol / maxVol) * plotH;

      ctx.fillStyle = 'rgba(16, 185, 129, 0.85)';
      ctx.fillRect(cx - barW - 0.5, padT + plotH - buyH, barW, buyH);

      ctx.fillStyle = 'rgba(239, 68, 68, 0.85)';
      ctx.fillRect(cx + 0.5, padT + plotH - sellH, barW, sellH);
    }

    // Draw Spread (pips) line overlay
    ctx.beginPath();
    ctx.strokeStyle = '#38bdf8';
    ctx.lineWidth = 1.6;
    for (let i = 0; i < n; i++) {
      const b = slice[i];
      const cx = padL + (i + 0.5) * stepW;
      const spPips = b.spread / pipSize;
      const y = padT + plotH - Math.min(1, spPips / maxSp) * plotH;
      if (i === 0) ctx.moveTo(cx, y);
      else ctx.lineTo(cx, y);
    }
    ctx.stroke();

    // Time ticks along bottom
    ctx.fillStyle = textColor;
    ctx.textAlign = 'center';
    const labelCount = Math.min(5, n);
    for (let k = 0; k < labelCount; k++) {
      const idx = Math.min(n - 1, Math.round((k * (n - 1)) / Math.max(1, labelCount - 1)));
      const b = slice[idx];
      const cx = padL + (idx + 0.5) * stepW;
      const d = new Date(b.time * 1000);
      const hm = `${String(d.getUTCHours()).padStart(2, '0')}:${String(d.getUTCMinutes()).padStart(2, '0')}`;
      ctx.fillText(hm, cx, h - 5);
    }

    canvas._ofSlice = slice;
    canvas._ofGeom = { padL, padT, plotW, plotH, stepW, pipSize };
  }

  function setupOrderFlowTooltip() {
    const canvas = $('orderflow-canvas');
    const tip = $('of-tooltip');
    if (!canvas || !tip) return;

    canvas.addEventListener('mousemove', (e) => {
      const slice = canvas._ofSlice;
      const geom = canvas._ofGeom;
      if (!slice || !geom || !slice.length) return;
      const rect = canvas.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const idx = Math.floor((x - geom.padL) / geom.stepW);
      if (idx < 0 || idx >= slice.length) {
        tip.style.display = 'none';
        return;
      }
      const b = slice[idx];
      const spPips = (b.spread / geom.pipSize).toFixed(1);
      tip.style.display = 'block';
      tip.innerHTML = `
        <div style="color:var(--dc-sky);font-weight:700;margin-bottom:2px">${fmtUtcShort(b.time)} UTC</div>
        <div style="color:var(--dc-green)">Buy Vol: ${fmtInt(b.buyVol)}</div>
        <div style="color:var(--dc-red)">Sell Vol: ${fmtInt(b.sellVol)}</div>
        <div>Delta: ${b.delta >= 0 ? '+' : ''}${b.delta} · Spread: ${spPips}p</div>
      `;
    });

    canvas.addEventListener('mouseleave', () => {
      tip.style.display = 'none';
    });
  }

  // ========================================================================
  // PIPELINE HEALTH STRIP & SPARKLINES
  // ========================================================================
  function renderSvgSparkline(svgId, values, color, fillAlpha = 0.16) {
    const svg = $(svgId);
    if (!svg) return;
    if (!values.length) {
      svg.innerHTML = '';
      return;
    }
    const min = Math.min(...values);
    const max = Math.max(...values);
    const span = max - min || 1;
    const w = 100;
    const h = 24;
    const pts = values.map((v, i) => {
      const x = (i / Math.max(1, values.length - 1)) * w;
      const y = h - 2 - ((v - min) / span) * (h - 5);
      return [x.toFixed(1), y.toFixed(1)];
    });
    const linePath = pts.map((p, i) => `${i === 0 ? 'M' : 'L'}${p[0]},${p[1]}`).join(' ');
    const areaPath = `${linePath} L${w},${h} L0,${h} Z`;

    svg.innerHTML = `
      <path d="${areaPath}" fill="${color}" fill-opacity="${fillAlpha}"></path>
      <path d="${linePath}" fill="none" stroke="${color}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"></path>
    `;
  }

  function updatePipelineHealth() {
    const symData = getActiveSymData();
    if (!symData) return;

    const winEnd = state.replayIndex;
    const winStart = Math.max(0, winEnd - 29);
    const windowBars = symData.unpackedBars.slice(winStart, winEnd + 1);
    const curBar = windowBars[windowBars.length - 1];
    if (!curBar) return;

    const light = isLightTheme();

    // 1. Latency (prefer real trade latency near/before curBar.t, fallback to cadence)
    const cadences = windowBars.map((b) => (b.du > 0 ? Math.round(60000 / b.du) : 300));
    const curCadence = cadences[cadences.length - 1] || 300;
    const tradesBefore = (symData.trades || []).filter((tr) => tr.latencyMs != null && tr.t <= curBar.t);
    const latSeries = tradesBefore.length >= 4
      ? tradesBefore.slice(-24).map((tr) => tr.latencyMs)
      : cadences;
    const latestLat = tradesBefore.length ? Math.round(tradesBefore[tradesBefore.length - 1].latencyMs) : curCadence;
    const latColor = latestLat > 900 ? 'var(--dc-amber)' : 'var(--dc-green)';
    const latSpark = latestLat > 900 ? (light ? '#d97706' : '#f59e0b') : (light ? '#15803d' : '#22c55e');

    const hmLatVal = $('hm-latency-val');
    const hmLatSub = $('hm-latency-sub');
    if (hmLatVal) {
      hmLatVal.textContent = `${latestLat}ms`;
      hmLatVal.style.color = latColor;
    }
    if (hmLatSub) {
      hmLatSub.textContent = tradesBefore.length
        ? `Exec · Cad ${curCadence}ms`
        : `Cadence ${curCadence}ms/upd`;
    }
    renderSvgSparkline('spark-latency', latSeries, latSpark);

    // 2. Tick Frequency (ticks / sec)
    const tickFreqs = windowBars.map((b) => Number((b.tk / 60).toFixed(2)));
    const curTickFreq = tickFreqs[tickFreqs.length - 1] || 0;
    const hmTickVal = $('hm-tick-val');
    const hmTickSub = $('hm-tick-sub');
    if (hmTickVal) hmTickVal.textContent = `${curTickFreq.toFixed(1)}/s`;
    if (hmTickSub) hmTickSub.textContent = `${curBar.tk} ticks/m`;
    renderSvgSparkline('spark-tickfreq', tickFreqs, light ? '#15803d' : '#22c55e');

    // 3. Missing Bars in rolling 30m window
    const gapsWindow = windowBars.map((b) => b.gap || 0);
    const missingInWin = gapsWindow.reduce((acc, g) => acc + g, 0);
    const totalGapEvents = (symData.gaps || []).length;

    const hmMissVal = $('hm-missing-val');
    const hmMissSub = $('hm-missing-sub');
    const hmMissIcon = $('hm-missing-icon');
    const hdrIcon = $('health-status-icon');
    const missColor = missingInWin === 0 ? 'var(--dc-green)' : (missingInWin <= 5 ? 'var(--dc-amber)' : 'var(--dc-red)');
    const missSpark = missingInWin === 0
      ? (light ? '#15803d' : '#22c55e')
      : (missingInWin <= 5 ? (light ? '#d97706' : '#f59e0b') : (light ? '#dc2626' : '#ef4444'));

    if (hmMissVal) {
      hmMissVal.textContent = fmtInt(missingInWin);
      hmMissVal.style.color = missColor;
    }
    if (hmMissSub) {
      hmMissSub.textContent = `${totalGapEvents} events total`;
    }
    if (hmMissIcon) hmMissIcon.style.color = missColor;
    if (hdrIcon) hdrIcon.style.stroke = missSpark;
    renderSvgSparkline('spark-missing', gapsWindow, missSpark);
  }

  // ========================================================================
  // 25-LEVEL DoM LADDER + 100ms BATCH ENGINE
  // ========================================================================
  function initDomTable() {
    const tbody = $('dom-tbody');
    if (!tbody) return;
    tbody.innerHTML = '';
    state.domRows = [];

    for (let i = 0; i < 25; i++) {
      const tr = document.createElement('tr');

      const tdLvl = document.createElement('td');
      tdLvl.className = 'dom-col-lvl';
      tdLvl.textContent = String(i + 1);

      const tdBVol = document.createElement('td');
      tdBVol.className = 'dom-col-bvol';
      const bidBar = document.createElement('div');
      bidBar.className = 'dom-bar-bg dom-bar-bid';
      const bidVolSpan = document.createElement('span');
      bidVolSpan.className = 'dom-vol-text';
      tdBVol.append(bidBar, bidVolSpan);

      const tdBid = document.createElement('td');
      tdBid.className = 'dom-col-bid';
      tdBid.title = 'คลิกเพื่อดูข้อมูลระดับราคา Bid';

      const tdAsk = document.createElement('td');
      tdAsk.className = 'dom-col-ask';
      tdAsk.title = 'คลิกเพื่อดูข้อมูลระดับราคา Ask';

      const tdAVol = document.createElement('td');
      tdAVol.className = 'dom-col-avol';
      const askBar = document.createElement('div');
      askBar.className = 'dom-bar-bg dom-bar-ask';
      const askVolSpan = document.createElement('span');
      askVolSpan.className = 'dom-vol-text';
      tdAVol.append(askBar, askVolSpan);

      tdBid.addEventListener('click', () => {
        showToast(`Bid L${i + 1}: ${tdBid.textContent} · Vol ${bidVolSpan.textContent}`, 'buy');
      });
      tdAsk.addEventListener('click', () => {
        showToast(`Ask L${i + 1}: ${tdAsk.textContent} · Vol ${askVolSpan.textContent}`, 'sell');
      });

      tr.append(tdLvl, tdBVol, tdBid, tdAsk, tdAVol);
      tbody.appendChild(tr);

      state.domRows.push({
        bidBar,
        bidVolSpan,
        tdBid,
        tdAsk,
        askBar,
        askVolSpan,
      });
    }
  }

  function scheduleDomBatch() {
    const symData = getActiveSymData();
    const bar = state.activeMicroBar;
    if (!symData || !bar) return;

    const digits = symData.digits || 2;
    const baseStep = Math.max(symData.domStep || 0.1, (bar.lb || 0.3) / 10);
    const step = Number(baseStep.toFixed(digits)) || symData.domStep || 0.1;

    // Anchor total Bid & Ask liquidity around real recorded bidVol/askVol + imbalance
    const rawBidTotal = Math.max(100, bar.bv > 50 ? bar.bv * 18 : bar.bv * 2500 || 35000);
    const rawAskTotal = Math.max(100, bar.av > 50 ? bar.av * 18 : bar.av * 2500 || 35000);
    const imbBias = bar.imb || 0;

    const bids = [];
    const asks = [];
    let maxLvlVol = 1;
    let totalBidVol = 0;
    let totalAskVol = 0;

    const poc = bar.poc || state.currentBid;
    const vah = bar.vah || state.currentAsk + step * 12;
    const val = bar.val || state.currentBid - step * 12;
    const phase = (state.currentBid * 3.7 + Date.now() * 0.002) % (Math.PI * 2);

    for (let i = 0; i < 25; i++) {
      const bPrice = Number((state.currentBid - i * step).toFixed(digits));
      const aPrice = Number((state.currentAsk + i * step).toFixed(digits));

      // Depth increases slightly away from top of book + peaks near POC/VAL/VAH liquidity walls
      const depthSlope = 0.55 + (i / 24) * 1.15;
      const bDistPoc = Math.abs(bPrice - poc);
      const bDistVal = Math.abs(bPrice - val);
      const bWallBoost = (bDistPoc < step * 2.2 || bDistVal < step * 2.2) ? 1.65 : 1.0;

      const aDistPoc = Math.abs(aPrice - poc);
      const aDistVah = Math.abs(aPrice - vah);
      const aWallBoost = (aDistPoc < step * 2.2 || aDistVah < step * 2.2) ? 1.65 : 1.0;

      const bNoise = 0.85 + 0.3 * Math.abs(Math.sin(phase + i * 0.73));
      const aNoise = 0.85 + 0.3 * Math.abs(Math.cos(phase + i * 0.67));

      const bVol = Math.max(10, Math.round((rawBidTotal / 25) * depthSlope * bWallBoost * bNoise * (1 + imbBias * 0.6)));
      const aVol = Math.max(10, Math.round((rawAskTotal / 25) * depthSlope * aWallBoost * aNoise * (1 - imbBias * 0.6)));

      totalBidVol += bVol;
      totalAskVol += aVol;
      if (bVol > maxLvlVol) maxLvlVol = bVol;
      if (aVol > maxLvlVol) maxLvlVol = aVol;

      bids.push({ price: bPrice, vol: bVol, isWall: bWallBoost > 1.2 });
      asks.push({ price: aPrice, vol: aVol, isWall: aWallBoost > 1.2 });
    }

    // Also flag top 2 largest volumes per side as structural walls
    const sortedB = [...bids].sort((a, b) => b.vol - a.vol);
    const sortedA = [...asks].sort((a, b) => b.vol - a.vol);
    if (sortedB[0]) sortedB[0].isWall = true;
    if (sortedB[1]) sortedB[1].isWall = true;
    if (sortedA[0]) sortedA[0].isWall = true;
    if (sortedA[1]) sortedA[1].isWall = true;

    state.pendingDom = {
      digits,
      bids,
      asks,
      maxLvlVol,
      totalBidVol,
      totalAskVol,
      spread: state.currentSpread,
      ladderBid: bar.lb || 0,
      ladderAsk: bar.la || 0,
    };
    state.domDirty = true;
  }

  function flushDomBatch() {
    if (!state.domDirty || !state.pendingDom || !state.domRows.length) return;
    const d = state.pendingDom;
    state.domDirty = false;

    for (let i = 0; i < 25; i++) {
      const row = state.domRows[i];
      const b = d.bids[i];
      const a = d.asks[i];

      row.bidVolSpan.textContent = fmtInt(b.vol);
      row.tdBid.textContent = fmtPrice(b.price, d.digits);
      row.bidBar.style.transform = `scaleX(${Math.max(0.04, b.vol / d.maxLvlVol).toFixed(3)})`;
      row.bidBar.classList.toggle('wall', Boolean(b.isWall));

      row.tdAsk.textContent = fmtPrice(a.price, d.digits);
      row.askVolSpan.textContent = fmtInt(a.vol);
      row.askBar.style.transform = `scaleX(${Math.max(0.04, a.vol / d.maxLvlVol).toFixed(3)})`;
      row.askBar.classList.toggle('wall', Boolean(a.isWall));
    }

    const total = Math.max(1, d.totalBidVol + d.totalAskVol);
    const bPct = ((d.totalBidVol / total) * 100).toFixed(1);
    const aPct = (100 - Number(bPct)).toFixed(1);
    const symData = getActiveSymData();
    const pipSize = symData ? symData.pipSize : 0.1;

    const bLbl = $('dom-imb-bid-lbl');
    const aLbl = $('dom-imb-ask-lbl');
    const mLbl = $('dom-imb-mid-lbl');
    const bBar = $('dom-imb-bid-bar');
    const aBar = $('dom-imb-ask-bar');
    const spanNote = $('dom-span-note');

    if (bLbl) bLbl.textContent = `Bids ${bPct}%`;
    if (aLbl) aLbl.textContent = `${aPct}% Asks`;
    if (mLbl) mLbl.textContent = `Spread: ${(d.spread / pipSize).toFixed(1)}p`;
    if (bBar) bBar.style.width = `${bPct}%`;
    if (aBar) aBar.style.width = `${aPct}%`;
    if (spanNote) spanNote.textContent = `Span: B ${d.ladderBid.toFixed(3)} / A ${d.ladderAsk.toFixed(3)}`;
  }

  // ========================================================================
  // READOUTS: OHLC STRIP, ORDER FLOW STATS, QUICKTRADE, PAPER PNL
  // ========================================================================
  function updateOhlcStrip(hoveredCandle) {
    const symData = getActiveSymData();
    const bar = state.activeMicroBar;
    if (!symData || !bar) return;
    const digits = symData.digits || 2;

    const o = hoveredCandle ? hoveredCandle.open : bar.o;
    const h = hoveredCandle ? hoveredCandle.high : bar.h;
    const l = hoveredCandle ? hoveredCandle.low : bar.l;
    const c = hoveredCandle ? hoveredCandle.close : bar.c;
    const diff = c - o;
    const pct = o ? (diff / o) * 100 : 0;

    if ($('ohlc-o')) $('ohlc-o').textContent = fmtPrice(o, digits);
    if ($('ohlc-h')) $('ohlc-h').textContent = fmtPrice(h, digits);
    if ($('ohlc-l')) $('ohlc-l').textContent = fmtPrice(l, digits);
    if ($('ohlc-c')) $('ohlc-c').textContent = fmtPrice(c, digits);

    const chgEl = $('ohlc-chg');
    if (chgEl) {
      const sign = diff >= 0 ? '+' : '';
      chgEl.textContent = `${sign}${diff.toFixed(digits)} (${sign}${pct.toFixed(2)}%)`;
      chgEl.className = `ohlc-change ${diff >= 0 ? 'up' : 'down'}`;
    }

    if ($('ctx-vwap')) $('ctx-vwap').textContent = fmtPrice(bar.vw, digits);
    if ($('ctx-poc')) $('ctx-poc').textContent = fmtPrice(bar.poc, digits);
    if ($('ctx-time')) $('ctx-time').textContent = `${fmtUtcShort(bar.t)} UTC`;
  }

  function updateOrderFlowStats() {
    const symData = getActiveSymData();
    const bar = state.activeMicroBar;
    if (!symData || !bar) return;

    const pipSize = symData.pipSize || 0.1;
    const spPips = state.currentSpread / pipSize;
    if ($('stat-spread-pips')) $('stat-spread-pips').textContent = `${spPips.toFixed(1)} pips`;
    if ($('stat-spread-raw')) $('stat-spread-raw').textContent = `Quote: ${state.currentSpread.toFixed(symData.digits)}`;

    // Calculate 14-bar M1 True Range ATR up to replayIndex
    const start = Math.max(1, state.replayIndex - 14);
    const bars = symData.unpackedBars;
    let trSum = 0;
    let trCnt = 0;
    for (let i = start; i <= state.replayIndex; i++) {
      const prevClose = bars[i - 1].c;
      const cur = bars[i];
      const tr = Math.max(cur.h - cur.l, Math.abs(cur.h - prevClose), Math.abs(cur.l - prevClose));
      trSum += tr;
      trCnt++;
    }
    const atr = trCnt ? trSum / trCnt : bar.h - bar.l;
    const atrPips = atr / pipSize;
    if ($('stat-atr-pips')) $('stat-atr-pips').textContent = `${atrPips.toFixed(1)} pips`;
    if ($('stat-cvd-val')) $('stat-cvd-val').textContent = `CVD: ${bar.cvd >= 0 ? '+' : ''}${fmtInt(bar.cvd)}`;
  }

  function updateQuickTradeAndPaperPnL() {
    const symData = getActiveSymData();
    const digits = symData ? symData.digits : 2;
    if ($('qt-ask-price')) $('qt-ask-price').textContent = fmtPrice(state.currentAsk, digits);
    if ($('qt-bid-price')) $('qt-bid-price').textContent = fmtPrice(state.currentBid, digits);

    let totalUnrealized = 0;
    let curSymOpen = 0;

    for (const pos of state.openPositions) {
      if (pos.symbol === state.currentSymbol) {
        curSymOpen++;
        const exitPx = pos.side === 'BUY' ? state.currentBid : state.currentAsk;
        pos.currentPrice = exitPx;
        const diff = pos.side === 'BUY' ? (exitPx - pos.entryPrice) : (pos.entryPrice - exitPx);
        pos.pnl = Number((diff * pos.lot * pos.contractSize).toFixed(2));
      }
      totalUnrealized += pos.pnl;
    }

    const equity = state.paperBalance + totalUnrealized;
    const eqEl = $('top-paper-equity');
    if (eqEl) {
      eqEl.textContent = `$${fmtPrice(equity, 2)}`;
      eqEl.style.color = equity >= 10000 ? 'var(--dc-green)' : 'var(--dc-red)';
    }
    if ($('top-open-badge')) $('top-open-badge').textContent = String(state.openPositions.length);
    if ($('qt-flatten-btn')) $('qt-flatten-btn').disabled = curSymOpen === 0;

    const sumEl = $('qt-pos-summary');
    const pnlEl = $('qt-pos-pnl');
    if (sumEl) {
      sumEl.textContent = state.openPositions.length
        ? `${state.openPositions.length} open position(s)`
        : '0 open · Paper Sim';
      sumEl.style.color = state.openPositions.length ? 'var(--text-primary)' : 'var(--text-muted)';
    }
    if (pnlEl) {
      const sign = totalUnrealized >= 0 ? '+' : '';
      pnlEl.textContent = `${sign}$${totalUnrealized.toFixed(2)}`;
      pnlEl.style.color = totalUnrealized >= 0 ? 'var(--dc-green)' : 'var(--dc-red)';
    }

    if ($('paper-drawer') && $('paper-drawer').classList.contains('open')) {
      renderPaperDrawer();
    }
  }

  function updateAllReadouts() {
    const symData = getActiveSymData();
    if (!symData) return;

    updateOhlcStrip(null);
    updateOrderFlowStats();
    updatePipelineHealth();
    scheduleDomBatch();
    updateQuickTradeAndPaperPnL();

    const scrubber = $('replay-scrubber');
    if (scrubber) scrubber.value = state.replayIndex;
    const counter = $('replay-bar-counter');
    if (counter) counter.textContent = `${state.replayIndex + 1} / ${symData.unpackedBars.length}`;
  }

  // ========================================================================
  // REPLAY ENGINE (PLAY / PAUSE / 1x–5x / SCRUB / STEP)
  // ========================================================================
  function stepForwardOneBar() {
    const symData = getActiveSymData();
    if (!symData || !state.activeMicroBar) return;

    // Finalize current micro bar into historical state
    const orig = symData.unpackedBars[state.replayIndex];
    if (orig) {
      state.activeMicroBar.h = orig.h;
      state.activeMicroBar.l = orig.l;
      state.activeMicroBar.c = orig.c;
      state.activeMicroBar.tk = orig.tk;
      updateLatestChartBar();
    }

    if (state.replayIndex < symData.unpackedBars.length - 1) {
      state.replayIndex++;
    } else {
      // Loop cleanly back to default replay window
      state.replayIndex = Math.max(60, symData.defaultReplayIndex || 60);
      primeActiveBarFromIndex();
      rebuildChartSeries(true);
      updateAllReadouts();
      return;
    }

    primeActiveBarFromIndex();
    updateLatestChartBar();
    syncChartMarkers();
    updateAllReadouts();
    drawOrderFlowCanvas();
  }

  function stepBackwardOneBar() {
    const symData = getActiveSymData();
    if (!symData) return;
    if (state.replayIndex > 30) {
      state.replayIndex--;
      primeActiveBarFromIndex();
      rebuildChartSeries(false);
      updateAllReadouts();
    }
  }

  function startReplayLoop() {
    if (state.microTimer) clearInterval(state.microTimer);
    state.barAdvanceMsAcc = 0;

    state.microTimer = setInterval(() => {
      if (!state.isPlaying || !state.activeMicroBar) return;
      const symData = getActiveSymData();
      if (!symData) return;

      const bar = state.activeMicroBar;
      const barIntervalMs = Math.max(400, Math.round(2000 / state.speed));
      state.barAdvanceMsAcc += 200;

      if (state.barAdvanceMsAcc >= barIntervalMs) {
        state.barAdvanceMsAcc = 0;
        stepForwardOneBar();
        return;
      }

      // Smooth intra-bar micro tick converging toward bar.targetC
      const progress = Math.min(1, state.barAdvanceMsAcc / barIntervalMs);
      const jitter = (Math.random() - 0.5) * state.currentSpread * 0.9;
      const rawPx = bar.o + (bar.targetC - bar.o) * progress + jitter * (1 - progress * 0.6);
      const digits = symData.digits || 2;
      bar.c = Number(rawPx.toFixed(digits));
      bar.h = Math.max(bar.h, bar.c);
      bar.l = Math.min(bar.l, bar.c);

      state.currentBid = bar.c;
      state.currentAsk = Number((state.currentBid + state.currentSpread).toFixed(digits));

      updateLatestChartBar();
      updateOhlcStrip(null);
      scheduleDomBatch();
      updateQuickTradeAndPaperPnL();
    }, 200);
  }

  function setPlaying(playing) {
    state.isPlaying = playing;
    if ($('btn-play')) $('btn-play').classList.toggle('active', playing);
    if ($('btn-pause')) $('btn-pause').classList.toggle('active', !playing);
  }

  function setSpeed(spd) {
    state.speed = spd;
    document.querySelectorAll('[data-speed]').forEach((btn) => {
      btn.classList.toggle('active', Number(btn.dataset.speed) === spd);
    });
    if ($('replay-speed-label')) $('replay-speed-label').textContent = `Speed: ${spd}.0x`;
  }

  // ========================================================================
  // PAPER TRADING SIMULATOR (BUY / SELL / FLATTEN + DRAWER)
  // ========================================================================
  function placePaperOrder(side) {
    const symData = getActiveSymData();
    if (!symData) return;
    const lotInput = $('qt-lot-input');
    const lot = Math.max(0.01, Math.min(10, Number(lotInput ? lotInput.value : 0.01) || 0.01));
    const entryPrice = side === 'BUY' ? state.currentAsk : state.currentBid;
    const ticket = state.nextTicket++;

    state.openPositions.push({
      ticket,
      symbol: state.currentSymbol,
      side,
      lot,
      contractSize: symData.contractSize || 100,
      digits: symData.digits || 2,
      entryPrice,
      currentPrice: entryPrice,
      pnl: 0,
      time: fmtUtcShort(state.activeMicroBar ? state.activeMicroBar.t : Math.floor(Date.now() / 1000)),
    });

    syncPositionPriceLines();
    updateQuickTradeAndPaperPnL();
    showToast(`Paper ${side} ${lot.toFixed(2)} ${symData.displayName} @ ${fmtPrice(entryPrice, symData.digits)}`, side === 'BUY' ? 'buy' : 'sell');
  }

  function closePaperPosition(ticket) {
    const idx = state.openPositions.findIndex((p) => p.ticket === ticket);
    if (idx === -1) return;
    const pos = state.openPositions[idx];
    state.paperBalance = Number((state.paperBalance + pos.pnl).toFixed(2));
    state.paperDeals.unshift({
      time: fmtUtcShort(state.activeMicroBar ? state.activeMicroBar.t : Math.floor(Date.now() / 1000)),
      symbol: pos.symbol,
      side: pos.side,
      lot: pos.lot,
      digits: pos.digits,
      entryPrice: pos.entryPrice,
      exitPrice: pos.currentPrice,
      pnl: pos.pnl,
    });
    state.openPositions.splice(idx, 1);
    syncPositionPriceLines();
    updateQuickTradeAndPaperPnL();
    showToast(`Closed #${ticket} (${pos.pnl >= 0 ? '+' : ''}$${pos.pnl.toFixed(2)})`, pos.pnl >= 0 ? 'buy' : 'sell');
  }

  function flattenCurrentSymbol() {
    const targets = state.openPositions.filter((p) => p.symbol === state.currentSymbol);
    if (!targets.length) return;
    let sumPnl = 0;
    const curTime = fmtUtcShort(state.activeMicroBar ? state.activeMicroBar.t : Math.floor(Date.now() / 1000));
    for (const pos of targets) {
      sumPnl += pos.pnl;
      state.paperBalance = Number((state.paperBalance + pos.pnl).toFixed(2));
      state.paperDeals.unshift({
        time: curTime,
        symbol: pos.symbol,
        side: pos.side,
        lot: pos.lot,
        digits: pos.digits,
        entryPrice: pos.entryPrice,
        exitPrice: pos.currentPrice,
        pnl: pos.pnl,
      });
    }
    state.openPositions = state.openPositions.filter((p) => p.symbol !== state.currentSymbol);
    syncPositionPriceLines();
    updateQuickTradeAndPaperPnL();
    showToast(`Flattened ${targets.length} pos (${sumPnl >= 0 ? '+' : ''}$${sumPnl.toFixed(2)})`, sumPnl >= 0 ? 'buy' : 'warn');
  }

  function renderPaperDrawer() {
    if ($('drawer-open-cnt')) $('drawer-open-cnt').textContent = String(state.openPositions.length);
    if ($('drawer-deals-cnt')) $('drawer-deals-cnt').textContent = String(state.paperDeals.length);
    if ($('drawer-balance')) $('drawer-balance').textContent = `$${fmtPrice(state.paperBalance, 2)}`;

    const totalUpnl = state.openPositions.reduce((s, p) => s + p.pnl, 0);
    const upnlEl = $('drawer-upnl');
    if (upnlEl) {
      upnlEl.textContent = `${totalUpnl >= 0 ? '+' : ''}$${totalUpnl.toFixed(2)}`;
      upnlEl.style.color = totalUpnl >= 0 ? 'var(--dc-green)' : 'var(--dc-red)';
    }

    const openTbody = $('drawer-open-tbody');
    if (openTbody) {
      if (!state.openPositions.length) {
        openTbody.innerHTML = '<tr><td colspan="8" style="text-align:center;padding:16px;color:var(--text-muted)">ไม่มีออเดอร์เปิดอยู่ · กด BUY หรือ SELL ใน QuickTrade เพื่อทดสอบ</td></tr>';
      } else {
        openTbody.innerHTML = state.openPositions.map((p) => `
          <tr>
            <td>#${p.ticket}</td>
            <td><strong>${p.symbol}</strong></td>
            <td style="color:${p.side === 'BUY' ? 'var(--dc-green)' : 'var(--dc-red)'};font-weight:700">${p.side}</td>
            <td>${p.lot.toFixed(2)}</td>
            <td>${fmtPrice(p.entryPrice, p.digits)}</td>
            <td>${fmtPrice(p.currentPrice, p.digits)}</td>
            <td style="color:${p.pnl >= 0 ? 'var(--dc-green)' : 'var(--dc-red)'};font-weight:700">${p.pnl >= 0 ? '+' : ''}$${p.pnl.toFixed(2)}</td>
            <td><button type="button" class="r-btn" data-close-ticket="${p.ticket}">Close ×</button></td>
          </tr>
        `).join('');
        openTbody.querySelectorAll('[data-close-ticket]').forEach((btn) => {
          btn.addEventListener('click', () => closePaperPosition(Number(btn.dataset.closeTicket)));
        });
      }
    }

    const dealsTbody = $('drawer-deals-tbody');
    if (dealsTbody) {
      if (!state.paperDeals.length) {
        dealsTbody.innerHTML = '<tr><td colspan="7" style="text-align:center;padding:16px;color:var(--text-muted)">ยังไม่มีประวัติการปิดออเดอร์จำลอง</td></tr>';
      } else {
        dealsTbody.innerHTML = state.paperDeals.slice(0, 30).map((d) => `
          <tr>
            <td>${d.time}</td>
            <td><strong>${d.symbol}</strong></td>
            <td style="color:${d.side === 'BUY' ? 'var(--dc-green)' : 'var(--dc-red)'};font-weight:700">${d.side}</td>
            <td>${d.lot.toFixed(2)}</td>
            <td>${fmtPrice(d.entryPrice, d.digits)}</td>
            <td>${fmtPrice(d.exitPrice, d.digits)}</td>
            <td style="color:${d.pnl >= 0 ? 'var(--dc-green)' : 'var(--dc-red)'};font-weight:700">${d.pnl >= 0 ? '+' : ''}$${d.pnl.toFixed(2)}</td>
          </tr>
        `).join('');
      }
    }
  }

  function renderRecordedTradesTab() {
    const symData = getActiveSymData();
    const recCnt = $('drawer-rec-cnt');
    const recTbody = $('drawer-rec-tbody');
    const trades = (symData && symData.trades) ? symData.trades : [];
    if (recCnt) recCnt.textContent = String(trades.length);
    if (!recTbody) return;
    if (!trades.length) {
      recTbody.innerHTML = '<tr><td colspan="7" style="text-align:center;padding:16px;color:var(--text-muted)">ไม่มีประวัติการเทรดจริงในสัญลักษณ์นี้</td></tr>';
      return;
    }
    recTbody.innerHTML = trades.slice().reverse().slice(0, 30).map((tr) => `
      <tr>
        <td>${tr.time}</td>
        <td>${tr.event}</td>
        <td style="color:${tr.side.toLowerCase() === 'buy' ? 'var(--dc-green)' : 'var(--dc-red)'};font-weight:700">${tr.side}</td>
        <td>${fmtPrice(tr.price, symData.digits || 2)}</td>
        <td>${tr.slippage != null ? tr.slippage : '--'}</td>
        <td>${tr.latencyMs != null ? `${Math.round(tr.latencyMs)}ms` : '--'}</td>
        <td style="color:${(tr.net || 0) >= 0 ? 'var(--dc-green)' : 'var(--dc-red)'};font-weight:700">${tr.net != null ? `${tr.net >= 0 ? '+' : ''}$${tr.net.toFixed(2)}` : '--'}</td>
      </tr>
    `).join('');
  }

  // ========================================================================
  // MODALS (MISSING BARS / WATCHDOG / ALERTS / HELP)
  // ========================================================================
  function openModal(title, htmlContent) {
    const bd = $('dc-modal-backdrop');
    if ($('dc-modal-title')) $('dc-modal-title').textContent = title;
    if ($('dc-modal-body')) $('dc-modal-body').innerHTML = htmlContent;
    if (bd) bd.classList.add('open');
  }

  function closeModal() {
    const bd = $('dc-modal-backdrop');
    if (bd) bd.classList.remove('open');
  }

  function showMissingBarsModal() {
    const symData = getActiveSymData();
    if (!symData) return;
    const gaps = symData.gaps || [];
    const rowsHtml = gaps.length
      ? gaps.slice(0, 40).map((g) => `
          <tr>
            <td style="padding:5px 6px">${g.from}</td>
            <td style="padding:5px 6px">${g.to}</td>
            <td style="padding:5px 6px;color:var(--dc-amber);font-weight:700">${g.missingBars} bars</td>
            <td style="padding:5px 6px"><button type="button" class="r-btn" data-jump-idx="${Math.min(symData.unpackedBars.length - 1, g.afterIndex + 1)}">Jump</button></td>
          </tr>
        `).join('')
      : '<tr><td colspan="4" style="padding:12px;text-align:center">ไม่พบ Missing Bars</td></tr>';

    openModal(`Missing Bars Audit · ${symData.displayName}`, `
      <p style="margin-top:0">ตรวจพบช่วงเวลาขาดหายทั้งหมด <strong class="mono">${gaps.length}</strong> เหตุการณ์ (รวม ${fmtInt(symData.stats.totalMissingBars)} แท่ง M1) จากการตรวจสอบ timestamp ต่อเนื่องของ <code>data/live/${symData.symbol}/min-*.csv</code></p>
      <table class="drawer-table" style="width:100%">
        <thead><tr><th>From (UTC)</th><th>To (UTC)</th><th>Missing</th><th>Inspect</th></tr></thead>
        <tbody>${rowsHtml}</tbody>
      </table>
    `);

    const body = $('dc-modal-body');
    if (body) {
      body.querySelectorAll('[data-jump-idx]').forEach((btn) => {
        btn.addEventListener('click', () => {
          const idx = Math.max(30, Number(btn.dataset.jumpIdx));
          state.replayIndex = idx;
          setPlaying(false);
          primeActiveBarFromIndex();
          rebuildChartSeries(true);
          updateAllReadouts();
          closeModal();
        });
      });
    }
  }

  function showHelpModal() {
    openModal('คู่มือใช้งาน Data Center (Page 2)', `
      <ul style="padding-left:18px;line-height:1.7;margin:0">
        <li><strong>TradingView Lightweight Charts &amp; Replay:</strong> เลือกคู่เทรด (<code>XAU/USD</code>, <code>BTC/USD</code>, <code>ETH/USD</code>, <code>GOLD-PERP</code>) และกรอบเวลา <code>M1–D1</code> ปรับสปีด <code>1x–5x</code> หรือลากแถบเวลาเพื่อย้อนดูพฤติกรรมราคาจริง</li>
        <li><strong>QuickTrade Paper Simulator:</strong> ส่งคำสั่งจำลอง <code>BUY</code>, <code>SELL</code>, <code>FLATTEN</code> ด้วย Lot Size ที่ต้องการ พร้อมดูเส้น Entry บนกราฟและ PnL แบบเรียลไทม์ (ไม่ส่งคำสั่งเข้าบัญชีจริง)</li>
        <li><strong>25-Level DoM Ladder (100ms Batch):</strong> แสดง Bid/Ask 25 ชั้นและแถบความหนาแน่นสภาพคล่อง (Depth Heatmap) อ้างอิงจาก <code>bidVol</code>, <code>askVol</code>, <code>ladderBid/Ask</code> และระดับ <code>POC/VAH/VAL</code> โดยอัปเดตแบบ Batch ทุก 100ms</li>
        <li><strong>Pipeline Health Strip:</strong> วัดค่า Execution Latency / Feed Cadence, Tick Frequency (ticks/sec) และตรวจจับ Missing Bars อัตโนมัติพร้อมกราฟ Sparkline</li>
      </ul>
    `);
  }

  // ========================================================================
  // EVENT WIRING & INITIALIZATION
  // ========================================================================
  function bindEvents() {
    $('btn-dc-help')?.addEventListener('click', showHelpModal);
    $('hm-card-missing')?.addEventListener('click', showMissingBarsModal);
    $('hm-card-missing')?.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        showMissingBarsModal();
      }
    });

    $('dc-modal-close')?.addEventListener('click', closeModal);
    $('dc-modal-backdrop')?.addEventListener('click', (e) => {
      if (e.target === $('dc-modal-backdrop')) closeModal();
    });
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') closeModal();
    });

    // React cleanly when Shared Shell toggles data-theme="dark" | "light"
    const themeObserver = new MutationObserver(() => {
      applyChartTheme();
    });
    themeObserver.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ['data-theme'],
    });

    // Symbol Switchers
    $('symbol-select')?.addEventListener('change', (e) => loadSymbol(e.target.value));
    document.querySelectorAll('.sym-pill').forEach((btn) => {
      btn.addEventListener('click', () => loadSymbol(btn.dataset.sym));
    });

    // Timeframe Switchers
    document.querySelectorAll('.tf-btn').forEach((btn) => {
      btn.addEventListener('click', () => {
        state.timeframe = btn.dataset.tf;
        document.querySelectorAll('.tf-btn').forEach((b) => b.classList.toggle('active', b === btn));
        rebuildChartSeries(true);
      });
    });

    // Chart Toolbar Actions
    $('btn-chart-mode')?.addEventListener('click', (e) => {
      state.chartMode = state.chartMode === 'candles' ? 'area' : 'candles';
      const label = state.chartMode === 'candles'
        ? '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M9 5v14"/><rect x="7" y="8" width="4" height="8" rx="0.5"/><path d="M17 3v18"/><rect x="15" y="7" width="4" height="7" rx="0.5"/></svg> <span>Candles</span>'
        : '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><polyline points="3 17 9 11 13 15 21 7"/><polyline points="16 7 21 7 21 12"/></svg> <span>Area</span>';
      e.currentTarget.innerHTML = label;
      rebuildChartSeries(false);
    });

    $('btn-vwap-toggle')?.addEventListener('click', (e) => {
      state.showVwap = !state.showVwap;
      e.currentTarget.classList.toggle('active', state.showVwap);
      rebuildChartSeries(false);
    });

    $('btn-gaps-toggle')?.addEventListener('click', (e) => {
      state.showGaps = !state.showGaps;
      e.currentTarget.classList.toggle('active', state.showGaps);
      syncChartMarkers();
    });

    $('btn-chart-fit')?.addEventListener('click', () => {
      if (!state.lwChart || !state.resampledBars.length) return;
      const n = state.resampledBars.length;
      state.lwChart.timeScale().setVisibleLogicalRange({ from: Math.max(0, n - 90), to: n + 4 });
    });

    $('btn-fullscreen')?.addEventListener('click', () => {
      const card = $('chart-card');
      if (!card) return;
      if (!document.fullscreenElement) {
        card.requestFullscreen?.().catch(() => {});
      } else {
        document.exitFullscreen?.().catch(() => {});
      }
    });

    // QuickTrade Controls
    $('qt-close-btn')?.addEventListener('click', () => {
      $('quicktrade-card')?.classList.add('collapsed');
      $('quicktrade-reopen')?.classList.add('visible');
    });
    $('quicktrade-reopen')?.addEventListener('click', () => {
      $('quicktrade-card')?.classList.remove('collapsed');
      $('quicktrade-reopen')?.classList.remove('visible');
    });
    $('qt-buy-btn')?.addEventListener('click', () => placePaperOrder('BUY'));
    $('qt-sell-btn')?.addEventListener('click', () => placePaperOrder('SELL'));
    $('qt-flatten-btn')?.addEventListener('click', flattenCurrentSymbol);

    $('qt-lot-minus')?.addEventListener('click', () => {
      const inp = $('qt-lot-input');
      if (!inp) return;
      const cur = Number(inp.value) || 0.01;
      inp.value = Math.max(0.01, cur - 0.01).toFixed(2);
    });
    $('qt-lot-plus')?.addEventListener('click', () => {
      const inp = $('qt-lot-input');
      if (!inp) return;
      const cur = Number(inp.value) || 0.01;
      inp.value = Math.min(10, cur + 0.01).toFixed(2);
    });

    // Paper Drawer Controls
    const toggleDrawer = (forceOpen) => {
      const dr = $('paper-drawer');
      if (!dr) return;
      const open = typeof forceOpen === 'boolean' ? forceOpen : !dr.classList.contains('open');
      dr.classList.toggle('open', open);
      if (open) renderPaperDrawer();
    };
    $('btn-paper-drawer')?.addEventListener('click', () => toggleDrawer());
    $('qt-pos-mini')?.addEventListener('click', () => toggleDrawer(true));
    $('btn-close-drawer')?.addEventListener('click', () => toggleDrawer(false));

    $('btn-reset-paper')?.addEventListener('click', () => {
      state.paperBalance = 10000.0;
      state.openPositions = [];
      state.paperDeals = [];
      syncPositionPriceLines();
      updateQuickTradeAndPaperPnL();
      renderPaperDrawer();
      showToast('รีเซ็ตพอร์ตจำลองกลับเป็น $10,000.00 แล้ว', 'info');
    });

    const switchDrawerTab = (tab) => {
      state.activeDrawerTab = tab;
      $('tab-open-pos')?.classList.toggle('active', tab === 'open');
      $('tab-deals-hist')?.classList.toggle('active', tab === 'deals');
      $('tab-rec-trades')?.classList.toggle('active', tab === 'rec');
      if ($('view-open-pos')) $('view-open-pos').style.display = tab === 'open' ? 'block' : 'none';
      if ($('view-deals-hist')) $('view-deals-hist').style.display = tab === 'deals' ? 'block' : 'none';
      if ($('view-rec-trades')) $('view-rec-trades').style.display = tab === 'rec' ? 'block' : 'none';
    };
    $('tab-open-pos')?.addEventListener('click', () => switchDrawerTab('open'));
    $('tab-deals-hist')?.addEventListener('click', () => switchDrawerTab('deals'));
    $('tab-rec-trades')?.addEventListener('click', () => switchDrawerTab('rec'));

    // Replay Transport Controls
    $('btn-play')?.addEventListener('click', () => setPlaying(true));
    $('btn-pause')?.addEventListener('click', () => setPlaying(false));
    $('btn-step-back')?.addEventListener('click', () => {
      setPlaying(false);
      stepBackwardOneBar();
    });
    $('btn-step-fwd')?.addEventListener('click', () => {
      setPlaying(false);
      stepForwardOneBar();
    });
    $('btn-reset-replay')?.addEventListener('click', () => {
      const symData = getActiveSymData();
      if (!symData) return;
      state.replayIndex = Math.max(30, symData.defaultReplayIndex || 120);
      primeActiveBarFromIndex();
      rebuildChartSeries(true);
      updateAllReadouts();
      showToast('รีเซ็ตตำแหน่งเวลา Replay แล้ว', 'info');
    });

    document.querySelectorAll('[data-speed]').forEach((btn) => {
      btn.addEventListener('click', () => setSpeed(Number(btn.dataset.speed)));
    });

    $('replay-scrubber')?.addEventListener('input', (e) => {
      const idx = Number(e.target.value);
      const symData = getActiveSymData();
      if (!symData || Number.isNaN(idx)) return;
      state.replayIndex = Math.max(30, Math.min(symData.unpackedBars.length - 1, idx));
      primeActiveBarFromIndex();
      rebuildChartSeries(true);
      updateAllReadouts();
    });

    $('btn-snapshot')?.addEventListener('click', () => {
      if (!state.lwChart) return;
      try {
        const snap = state.lwChart.takeScreenshot();
        const a = document.createElement('a');
        a.download = `antigravity_${state.currentSymbol}_${state.timeframe}.png`;
        a.href = snap.toDataURL('image/png');
        a.click();
        showToast('บันทึกภาพกราฟ PNG เรียบร้อย', 'info');
      } catch (e) {
        showToast('ไม่สามารถบันทึกภาพได้', 'warn');
      }
    });
  }

  async function init() {
    mountShell({ activePage: 'data-center.html', onRetry: loadTelemetryFeeds });
    initDomTable();
    initLightweightChart();
    setupOrderFlowTooltip();
    bindEvents();

    // Strictly batch DoM DOM writes every 100ms to keep CPU idle
    state.batchTimer = setInterval(flushDomBatch, 100);
    state.telemetryTimer = setInterval(loadTelemetryFeeds, 60000);

    await loadTelemetryFeeds();
    await loadSymbol('XAUUSD');
    startReplayLoop();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
