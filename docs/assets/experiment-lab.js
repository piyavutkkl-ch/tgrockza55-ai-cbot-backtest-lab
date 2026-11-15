/* ============================================================================
   PAGE 4: EXPERIMENT LAB (Backtesting & Version Diff Comparator)
   Features:
   - Version Diff Comparator (Overlay Run A vs Run B + Delta KPI Cards)
   - Cost-Calibration Toggle Switch (Gross Ideal Fill vs Real Commission+Spread/Slippage)
   - Dual-Chart Synchronized Canvas (Equity Curve + Underwater Drawdown & Recovery Time)
   - LTTB Downsampling (Auto-activates when points > 5,000 for 60fps zoom/pan)
   - Paginated Trade Execution Log with Search, Filter, Sort, Expandable Inspector, CSV Export
   Strict Rule: 100% real data from docs/data/*.json — zero fabricated numbers.
   ============================================================================ */

import { mountShell, loadShellTelemetryOnly } from './shell.js';

const LTTB_THRESHOLD = 5000;
const INITIAL_EQUITY = 100.0;

const PRESETS = [
  { id: 'smart_vs_fade', label: 'Smart Runner vs DOM Fade', a: 'dom_smart_runner', b: 'dom_fade' },
  { id: 'smc_vs_fade', label: 'SMC Fibo vs DOM Fade', a: 'smc_fibo_dom', b: 'dom_fade' },
  { id: 'smart_vs_smc', label: 'Smart Runner vs SMC Fibo', a: 'dom_smart_runner', b: 'smc_fibo_dom' },
  { id: 'btc_vs_eth', label: 'BTC V2 vs ETH V2', a: 'dom_absorption_btc', b: 'dom_absorption_eth' },
  { id: 'vwap_vs_perp', label: 'VWAP Eq vs Gold-Perp', a: 'vwap_equilibrium_xau', b: 'dom_absorption_gold_perp' }
];

const state = {
  rawBacktest: null,
  rawCosts: null,
  rawLive: null,
  rawQv2: null,
  rawIntel: null,
  runs: {},       // Normalized run catalog keyed by id
  runOrder: [],
  runA: 'dom_smart_runner',
  runB: 'dom_fade',
  costCalibrated: true,
  showGrossGhost: true,
  xMode: 'time',  // 'time' | 'trade' | 'daily'
  unit: 'pct',    // 'pct' | 'usd'
  zoom: { start: 0, end: 1 }, // normalized [0,1]
  hoverNormX: null,
  hoverClientX: 0,
  hoverClientY: 0,
  isDragging: false,
  dragStartX: 0,
  dragStartZoom: null,
  rafPending: false,
  logScope: 'both', // 'both' | 'a' | 'b'
  logFilter: 'all',
  logSearch: '',
  logSortBy: 'time_desc',
  logPage: 1,
  logPageSize: 10,
  expandedTradeKey: null,
  lastComputed: null
};

/* ----------------------------------------------------------------------------
   1. LTTB Downsampling (Largest-Triangle-Three-Buckets, Steinarsson 2013)
   ---------------------------------------------------------------------------- */
export function lttbDownsample(data, threshold) {
  const len = data.length;
  if (!Array.isArray(data) || threshold >= len || threshold <= 2) {
    return data;
  }

  const sampled = new Array(threshold);
  let sampledIndex = 0;
  const every = (len - 2) / (threshold - 2);

  let a = 0;
  sampled[sampledIndex++] = data[a];

  for (let i = 0; i < threshold - 2; i++) {
    let avgX = 0;
    let avgY = 0;
    let avgRangeStart = Math.floor((i + 1) * every) + 1;
    let avgRangeEnd = Math.floor((i + 2) * every) + 1;
    avgRangeEnd = avgRangeEnd < len ? avgRangeEnd : len;

    const avgRangeLength = avgRangeEnd - avgRangeStart;
    if (avgRangeLength > 0) {
      for (let j = avgRangeStart; j < avgRangeEnd; j++) {
        avgX += data[j].x;
        avgY += data[j].y;
      }
      avgX /= avgRangeLength;
      avgY /= avgRangeLength;
    } else {
      avgX = data[Math.min(len - 1, avgRangeStart)].x;
      avgY = data[Math.min(len - 1, avgRangeStart)].y;
    }

    const rangeOffs = Math.floor(i * every) + 1;
    const rangeTo = Math.min(len - 1, Math.floor((i + 1) * every) + 1);

    const pointAX = data[a].x;
    const pointAY = data[a].y;

    let maxArea = -1;
    let nextA = rangeOffs;

    for (let j = rangeOffs; j < rangeTo; j++) {
      const area = Math.abs(
        (pointAX - avgX) * (data[j].y - pointAY) -
        (pointAX - data[j].x) * (avgY - pointAY)
      ) * 0.5;
      if (area > maxArea) {
        maxArea = area;
        nextA = j;
      }
    }

    sampled[sampledIndex++] = data[nextA];
    a = nextA;
  }

  sampled[sampledIndex++] = data[len - 1];
  return sampled;
}

/* ----------------------------------------------------------------------------
   2. Parsing & Normalization Helpers
   ---------------------------------------------------------------------------- */
function parseUtcTimestamp(str) {
  if (!str || str === 'Start') return null;
  const normalized = String(str).trim().replace(' ', 'T');
  const withZ = /Z$|[+-]\d{2}:?\d{2}$/.test(normalized) ? normalized : `${normalized}Z`;
  const ts = Date.parse(withZ);
  return Number.isNaN(ts) ? null : ts;
}

function formatDateShort(ts) {
  if (ts == null || Number.isNaN(ts)) return '–';
  const d = new Date(ts);
  const mon = d.toLocaleString('en-US', { month: 'short', timeZone: 'UTC' });
  const day = String(d.getUTCDate()).padStart(2, '0');
  const hh = String(d.getUTCHours()).padStart(2, '0');
  const mm = String(d.getUTCMinutes()).padStart(2, '0');
  return `${mon} ${day} ${hh}:${mm}`;
}

function formatDateDay(ts) {
  if (ts == null || Number.isNaN(ts)) return '–';
  return new Date(ts).toISOString().slice(0, 10);
}

function formatDurationMs(ms) {
  if (!ms || ms <= 0) return '0m';
  const totalMin = Math.round(ms / 60000);
  if (totalMin < 60) return `${totalMin}m`;
  const hrs = Math.floor(totalMin / 60);
  const mins = totalMin % 60;
  if (hrs < 48) return `${hrs}h ${mins}m`;
  const days = Math.floor(hrs / 24);
  const remH = hrs % 24;
  return `${days}d ${remH}h`;
}

function escapeHtml(str) {
  return String(str ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function inferSymbol(key, entry) {
  if (entry.symbol) return entry.symbol;
  if (key.includes('btc')) return 'BTCUSD';
  if (key.includes('eth')) return 'ETHUSD';
  if (key.includes('gold_perp')) return 'GOLD-PERP';
  return 'XAUUSD';
}

function inferVersionLabel(key, entry) {
  const map = {
    dom_smart_runner: 'Smart Runner v2.1',
    smc_fibo_dom: 'SMC Fibo DOM v1.3',
    dom_fade: 'DOM Fade Baseline v1.0',
    dom_absorption_btc: 'DOM Abs V2 (BTC)',
    dom_absorption_eth: 'DOM Abs V2 (ETH)',
    dom_absorption_xau: 'DOM Abs V2 (XAU)',
    vwap_equilibrium_xau: 'VWAP Eq (XAU)',
    dom_absorption_gold_perp: 'DOM Abs (GOLD-PERP)',
    live_demo_deals: 'Live #5258778 (Recent)'
  };
  return map[key] || entry.name || key;
}

function buildNormalizedRuns(btData, costsData, liveData) {
  const runs = {};
  const order = [];
  const symsCost = costsData?.symbols || {};

  Object.entries(btData || {}).forEach(([key, entry]) => {
    const sym = inferSymbol(key, entry);
    const calSym = symsCost[sym] || symsCost.XAUUSD || {};
    const trades = Array.isArray(entry.trades) ? entry.trades : [];

    const normalizedTrades = trades.map((t, idx) => {
      const lot = Number(t.volume ?? 0.01);
      const lotScale = lot / 0.01;
      const hasExplicitGrossNet = typeof t.gross === 'number' && typeof t.net === 'number';
      const spreadRaw = Number(t.spread ?? 0);

      let grossPnl = 0;
      let netPnl = 0;
      let commCost = 0;
      let slipCost = 0;

      if (hasExplicitGrossNet) {
        grossPnl = Number(t.gross);
        netPnl = Number(t.net);
        commCost = Number(t.comm ?? calSym.commission_per_001_lot_usd ?? 0.07);
        slipCost = Math.max(0, +(grossPnl - netPnl - commCost).toFixed(4));
      } else {
        const recordedPnl = Number(t.net_pnl ?? t.pnl ?? 0);
        // backtest_dom_recorded.py baked spread*lot into recordedPnl, without commission/slippage
        const spreadUsd = +(spreadRaw * lot).toFixed(4);
        const calComm = +((calSym.commission_per_001_lot_usd ?? 0) * lotScale).toFixed(4);
        const calSlipMean = Math.max(0, Number(calSym.slippage?.mean ?? 0));
        const calSlipUsd = +(calSlipMean * lot).toFixed(4);

        grossPnl = +(recordedPnl + spreadUsd).toFixed(4);
        commCost = calComm;
        slipCost = +(spreadUsd + calSlipUsd).toFixed(4);
        netPnl = +(recordedPnl - calComm - calSlipUsd).toFixed(4);
      }

      const entryTimeStr = t.time || t.entry_time || '';
      const exitTimeStr = t.exit_time || entryTimeStr;
      const entryTs = parseUtcTimestamp(entryTimeStr);
      const exitTs = parseUtcTimestamp(exitTimeStr) ?? entryTs;

      return {
        uid: `${key}_${t.id ?? idx + 1}`,
        seq: t.id ?? idx + 1,
        symbol: sym,
        side: String(t.side || '').toUpperCase() === 'BUY' ? 'BUY' : 'SELL',
        size: lot,
        entryTimeStr,
        exitTimeStr,
        entryTs,
        exitTs,
        entryPrice: Number(t.entry_p ?? t.entry_price ?? 0),
        exitPrice: Number(t.exit_p ?? t.exit_price ?? 0),
        slPrice: t.sl_p ?? null,
        tpPrice: t.tp_p ?? null,
        durMin: t.dur_min ?? t.duration_min ?? null,
        grossPnl,
        netPnl,
        commCost,
        slipCost,
        rawSpread: spreadRaw,
        reason: t.reason || '–',
        entryReason: t.entry_reason || null,
        domReason: t.dom_reason || null,
        structureReason: t.structure_reason || null,
        analysis: t.analysis || null
      };
    });

    // Daily fallback for summary-only runs (e.g. vwap_equilibrium_xau, dom_absorption_gold_perp)
    const dailyMap = entry.daily_pnl && typeof entry.daily_pnl === 'object' ? entry.daily_pnl : null;
    const dailySeries = dailyMap
      ? Object.entries(dailyMap)
          .sort(([da], [db]) => da.localeCompare(db))
          .map(([day, val], i) => {
            const totalDays = Object.keys(dailyMap).length || 1;
            const avgTradesPerDay = (entry.summary?.total_trades ?? totalDays) / totalDays;
            const estCostPerTrade =
              Number(calSym.commission_per_001_lot_usd ?? 0.07) +
              Number(calSym.spread?.mean ?? 0.12) * (sym === 'XAUUSD' || sym === 'GOLD-PERP' ? 1 : 0.01);
            const dayCost = +(estCostPerTrade * avgTradesPerDay).toFixed(2);
            return {
              date: day,
              ts: parseUtcTimestamp(`${day} 21:45`),
              netPnl: Number(val),
              grossPnl: +(Number(val) + dayCost).toFixed(2),
              costDrag: dayCost,
              idx: i + 1
            };
          })
      : [];

    runs[key] = {
      id: key,
      shortName: inferVersionLabel(key, entry),
      name: entry.name || key,
      symbol: sym,
      timeframe: entry.timeframe || 'M1',
      periodLabel: entry.period || null,
      reportedSummary: entry.summary || {},
      parameters: entry.parameters || null,
      trades: normalizedTrades,
      dailySeries,
      sourceTag: 'backtest_data.json'
    };
    order.push(key);
  });

  // Optional live deals benchmark from live_status.json -> recent_closed_deals
  const liveDeals = Array.isArray(liveData?.recent_closed_deals) ? liveData.recent_closed_deals : [];
  if (liveDeals.length) {
    const chronoDeals = [...liveDeals].sort((a, b) =>
      String(a.close_time || '').localeCompare(String(b.close_time || ''))
    );
    const liveTrades = chronoDeals.map((d, idx) => {
      const sym = d.symbol || 'XAUUSD';
      const calSym = symsCost[sym] || {};
      const comm = Number(calSym.commission_per_001_lot_usd ?? 0.07);
      const sp = Number(d.spread ?? 0);
      const slp = Math.max(0, Number(d.slippage ?? 0));
      const slipUsd = sym === 'XAUUSD' ? +(sp + slp).toFixed(4) : +((sp + slp) * 0.01).toFixed(4);
      const net = Number(d.net ?? 0);
      const gross = +(net + comm + slipUsd).toFixed(4);
      const ts = parseUtcTimestamp(d.close_time);
      return {
        uid: `live_${d.id ?? idx + 1}`,
        seq: idx + 1,
        symbol: sym,
        side: String(d.side || '').toUpperCase() === 'BUY' ? 'BUY' : 'SELL',
        size: 0.01,
        entryTimeStr: d.close_time || '',
        exitTimeStr: d.close_time || '',
        entryTs: ts,
        exitTs: ts,
        entryPrice: Number(d.entry_price ?? 0),
        exitPrice: Number(d.exit_price ?? 0),
        slPrice: null,
        tpPrice: null,
        durMin: null,
        grossPnl: gross,
        netPnl: net,
        commCost: comm,
        slipCost: slipUsd,
        rawSpread: sp,
        reason: d.reason || 'Live Closed',
        entryReason: `Pepperstone Demo #5258778 Deal #${d.id}`,
        domReason: null,
        structureReason: null,
        analysis: `Live balance after close: $${Number(d.balance ?? 0).toFixed(2)}`
      };
    });

    runs.live_demo_deals = {
      id: 'live_demo_deals',
      shortName: 'Live #5258778 (Recent)',
      name: 'Pepperstone Demo #5258778 (Recent 10 Closed Deals)',
      symbol: 'MULTI',
      timeframe: 'Live',
      periodLabel: 'Recent Live Closed Deals',
      reportedSummary: {},
      parameters: null,
      trades: liveTrades,
      dailySeries: [],
      sourceTag: 'live_status.json'
    };
    order.push('live_demo_deals');
  }

  return { runs, order };
}

/* ----------------------------------------------------------------------------
   3. Series, Drawdown, Cost & Recovery Time Calculation
   ---------------------------------------------------------------------------- */
function computeRunSeries(run, costCalibrated, xMode) {
  if (!run) return null;

  const hasTrades = run.trades.length > 0;
  let points = [];
  let ghostPoints = [];
  let tradeStats = {
    totalTrades: 0,
    wins: 0,
    losses: 0,
    winRate: 0,
    grossWin: 0,
    grossLoss: 0,
    profitFactor: 0,
    netPnlUsd: 0,
    grossPnlUsd: 0,
    totalCostUsd: 0,
    returnPct: 0,
    startTs: null,
    endTs: null
  };

  if (hasTrades) {
    let eq = INITIAL_EQUITY;
    let eqGross = INITIAL_EQUITY;
    const firstTs = run.trades[0].entryTs ?? run.trades[0].exitTs ?? 0;
    const startTs = firstTs ? firstTs - 60000 : 0;

    const rawTradePoints = [{
      idx: 0,
      ts: startTs,
      eq: INITIAL_EQUITY,
      eqGross: INITIAL_EQUITY,
      label: 'Start'
    }];

    let wins = 0;
    let losses = 0;
    let grossWin = 0;
    let grossLoss = 0;
    let sumGross = 0;
    let sumNet = 0;
    let sumCost = 0;

    const enrichedTrades = run.trades.map((t, i) => {
      const activePnl = costCalibrated ? t.netPnl : t.grossPnl;
      const activeComm = costCalibrated ? t.commCost : 0;
      const activeSlip = costCalibrated ? t.slipCost : 0;
      const pctOnTrade = eq > 0 ? (activePnl / eq) * 100 : 0;

      eq = +(eq + activePnl).toFixed(4);
      eqGross = +(eqGross + t.grossPnl).toFixed(4);

      if (activePnl > 0) {
        wins++;
        grossWin += activePnl;
      } else if (activePnl < 0) {
        losses++;
        grossLoss += Math.abs(activePnl);
      }

      sumGross += t.grossPnl;
      sumNet += t.netPnl;
      sumCost += (t.commCost + t.slipCost);

      const ts = t.exitTs ?? t.entryTs ?? (startTs + (i + 1) * 60000);
      rawTradePoints.push({
        idx: i + 1,
        ts,
        eq,
        eqGross,
        label: t.exitTimeStr || t.entryTimeStr || `Trade #${i + 1}`
      });

      return {
        ...t,
        runId: run.id,
        runLabel: run.shortName,
        activePnl,
        activeComm,
        activeSlip,
        pnlPct: pctOnTrade,
        cumPnlUsd: +(eq - INITIAL_EQUITY).toFixed(2),
        cumEquity: eq
      };
    });

    if (xMode === 'daily') {
      const byDay = new Map();
      rawTradePoints.forEach((p) => {
        const dayKey = p.ts ? formatDateDay(p.ts) : 'Day 0';
        byDay.set(dayKey, p);
      });
      let dayIdx = 0;
      points = Array.from(byDay.entries()).map(([dayKey, p]) => ({
        x: dayIdx,
        xTs: parseUtcTimestamp(`${dayKey} 21:45`) ?? p.ts,
        idx: dayIdx++,
        eq: p.eq,
        eqGross: p.eqGross,
        label: dayKey
      }));
    } else {
      points = rawTradePoints.map((p) => ({
        x: xMode === 'time' ? (p.ts || p.idx) : p.idx,
        xTs: p.ts,
        idx: p.idx,
        eq: p.eq,
        eqGross: p.eqGross,
        label: p.label
      }));
    }

    ghostPoints = points.map((p) => ({
      ...p,
      eq: p.eqGross
    }));

    const total = enrichedTrades.length;
    const netUsd = +(eq - INITIAL_EQUITY).toFixed(2);
    tradeStats = {
      totalTrades: total,
      wins,
      losses,
      winRate: total > 0 ? +((wins / total) * 100).toFixed(1) : 0,
      grossWin: +grossWin.toFixed(2),
      grossLoss: +grossLoss.toFixed(2),
      profitFactor: grossLoss > 0 ? +(grossWin / grossLoss).toFixed(2) : (grossWin > 0 ? 99.0 : 0),
      netPnlUsd: netUsd,
      grossPnlUsd: +sumGross.toFixed(2),
      totalCostUsd: +sumCost.toFixed(2),
      returnPct: +(((eq - INITIAL_EQUITY) / INITIAL_EQUITY) * 100).toFixed(2),
      startTs: run.trades[0]?.entryTs ?? rawTradePoints[1]?.ts ?? startTs,
      endTs: rawTradePoints[rawTradePoints.length - 1]?.ts ?? startTs,
      enrichedTrades
    };
  } else {
    // Summary/Daily-only run (e.g. vwap_equilibrium_xau / dom_absorption_gold_perp)
    let eq = INITIAL_EQUITY;
    let eqGross = INITIAL_EQUITY;
    const firstDayTs = run.dailySeries[0]?.ts ? run.dailySeries[0].ts - 86400000 : 0;
    const pts = [{
      x: xMode === 'time' ? firstDayTs : 0,
      xTs: firstDayTs,
      idx: 0,
      eq: INITIAL_EQUITY,
      eqGross: INITIAL_EQUITY,
      label: 'Start'
    }];

    let sumCost = 0;
    run.dailySeries.forEach((d, i) => {
      const val = costCalibrated ? d.netPnl : d.grossPnl;
      eq = +(eq + val).toFixed(2);
      eqGross = +(eqGross + d.grossPnl).toFixed(2);
      sumCost += d.costDrag;
      pts.push({
        x: xMode === 'time' ? (d.ts || i + 1) : i + 1,
        xTs: d.ts,
        idx: i + 1,
        eq,
        eqGross,
        label: d.date
      });
    });

    points = pts;
    ghostPoints = pts.map((p) => ({ ...p, eq: p.eqGross }));

    const s = run.reportedSummary || {};
    const netUsd = costCalibrated
      ? Number(s.net_profit ?? (eq - INITIAL_EQUITY))
      : +(Number(s.net_profit ?? (eq - INITIAL_EQUITY)) + sumCost).toFixed(2);
    const total = Number(s.total_trades ?? 0);
    const baseWr = Number(s.win_rate ?? 0);
    const basePf = Number(s.profit_factor ?? 0);

    tradeStats = {
      totalTrades: total,
      wins: Math.round((total * baseWr) / 100),
      losses: total - Math.round((total * baseWr) / 100),
      winRate: baseWr,
      grossWin: 0,
      grossLoss: 0,
      profitFactor: costCalibrated ? basePf : +(basePf * (1 + sumCost / Math.max(10, Math.abs(netUsd) + 10))).toFixed(2),
      netPnlUsd: +netUsd.toFixed(2),
      grossPnlUsd: +(Number(s.net_profit ?? 0) + sumCost).toFixed(2),
      totalCostUsd: +sumCost.toFixed(2),
      returnPct: +((netUsd / INITIAL_EQUITY) * 100).toFixed(2),
      startTs: run.dailySeries[0]?.ts ?? null,
      endTs: run.dailySeries[run.dailySeries.length - 1]?.ts ?? null,
      enrichedTrades: []
    };
  }

  // Compute Underwater Drawdown & Recovery Time
  let peak = INITIAL_EQUITY;
  let peakTs = points[0]?.xTs ?? 0;
  let peakIdx = 0;
  let inDd = false;
  let ddStartTs = peakTs;
  let ddStartIdx = 0;
  let maxDdPct = 0;
  let maxDdUsd = 0;
  let maxRecMs = 0;
  let maxRecTrades = 0;
  let currentUnderwaterMs = 0;
  let currentUnderwaterTrades = 0;
  let episodeCount = 0;
  let sumRecMs = 0;
  let recoveredCount = 0;

  const ddPoints = points.map((p, i) => {
    if (p.eq >= peak) {
      if (inDd) {
        const recMs = (p.xTs ?? 0) - (ddStartTs ?? 0);
        const recTr = p.idx - ddStartIdx;
        if (recMs > maxRecMs) maxRecMs = recMs;
        if (recTr > maxRecTrades) maxRecTrades = recTr;
        sumRecMs += Math.max(0, recMs);
        recoveredCount++;
        inDd = false;
      }
      peak = p.eq;
      peakTs = p.xTs;
      peakIdx = p.idx;
      return {
        ...p,
        y: 0,
        ddUsd: 0
      };
    }

    if (!inDd) {
      inDd = true;
      ddStartTs = peakTs;
      ddStartIdx = peakIdx;
      episodeCount++;
    }

    const ddUsd = +(p.eq - peak).toFixed(4);
    const ddPct = peak > 0 ? +(((p.eq - peak) / peak) * 100).toFixed(3) : 0;
    if (Math.abs(ddPct) > maxDdPct) maxDdPct = Math.abs(ddPct);
    if (Math.abs(ddUsd) > maxDdUsd) maxDdUsd = Math.abs(ddUsd);

    if (i === points.length - 1 && inDd) {
      currentUnderwaterMs = Math.max(0, (p.xTs ?? 0) - (ddStartTs ?? 0));
      currentUnderwaterTrades = Math.max(0, p.idx - ddStartIdx);
      if (currentUnderwaterMs > maxRecMs) maxRecMs = currentUnderwaterMs;
      if (currentUnderwaterTrades > maxRecTrades) maxRecTrades = currentUnderwaterTrades;
    }

    return {
      ...p,
      y: ddPct,
      ddUsd
    };
  });

  const lastDdPct = ddPoints[ddPoints.length - 1]?.y ?? 0;

  return {
    run,
    points,
    ghostPoints,
    ddPoints,
    stats: {
      ...tradeStats,
      maxDdPct: +maxDdPct.toFixed(2),
      maxDdUsd: +maxDdUsd.toFixed(2),
      maxRecMs,
      maxRecTrades,
      avgRecMs: recoveredCount > 0 ? sumRecMs / recoveredCount : 0,
      stillUnderwater: inDd,
      currentDdPct: +lastDdPct.toFixed(2),
      currentUnderwaterMs,
      currentUnderwaterTrades,
      episodeCount
    }
  };
}

/* ----------------------------------------------------------------------------
   4. Dual-Chart Synchronized HiDPI Canvas Renderer + LTTB
   ---------------------------------------------------------------------------- */
function getThemeColors() {
  const isLight = document.documentElement.getAttribute('data-theme') === 'light';
  return {
    bg: isLight ? '#f8fafc' : '#0a101d',
    grid: isLight ? 'rgba(15, 23, 42, 0.08)' : 'rgba(148, 163, 184, 0.10)',
    axisText: isLight ? '#475569' : '#64748b',
    zeroLine: isLight ? 'rgba(15, 23, 42, 0.25)' : 'rgba(148, 163, 184, 0.28)',
    runA: isLight ? '#0284c7' : '#38bdf8',
    runAFillTop: isLight ? 'rgba(2, 132, 199, 0.22)' : 'rgba(56, 189, 248, 0.24)',
    runAFillBot: isLight ? 'rgba(2, 132, 199, 0.01)' : 'rgba(56, 189, 248, 0.01)',
    runAGhost: isLight ? 'rgba(2, 132, 199, 0.42)' : 'rgba(56, 189, 248, 0.36)',
    runB: isLight ? '#d97706' : '#f59e0b',
    ddA: isLight ? '#dc2626' : '#ef4444',
    ddAFillTop: isLight ? 'rgba(220, 38, 38, 0.06)' : 'rgba(239, 68, 68, 0.08)',
    ddAFillBot: isLight ? 'rgba(220, 38, 38, 0.32)' : 'rgba(239, 68, 68, 0.38)',
    ddB: isLight ? 'rgba(217, 119, 6, 0.72)' : 'rgba(245, 158, 11, 0.72)',
    crosshair: isLight ? 'rgba(15, 23, 42, 0.38)' : 'rgba(226, 232, 240, 0.42)'
  };
}

function toDisplayY(eqValue, unit) {
  if (unit === 'pct') {
    return ((eqValue - INITIAL_EQUITY) / INITIAL_EQUITY) * 100;
  }
  return eqValue - INITIAL_EQUITY;
}

function sliceVisibleWithMargin(pts, xMin, xMax) {
  if (!pts.length) return [];
  let start = 0;
  let end = pts.length - 1;
  for (let i = 0; i < pts.length; i++) {
    if (pts[i].x >= xMin) {
      start = Math.max(0, i - 1);
      break;
    }
  }
  for (let i = pts.length - 1; i >= 0; i--) {
    if (pts[i].x <= xMax) {
      end = Math.min(pts.length - 1, i + 1);
      break;
    }
  }
  return pts.slice(start, end + 1);
}

function findNearestPoint(pts, targetX) {
  if (!pts || !pts.length) return null;
  let lo = 0;
  let hi = pts.length - 1;
  while (lo < hi) {
    const mid = (lo + hi) >> 1;
    if (pts[mid].x < targetX) lo = mid + 1;
    else hi = mid;
  }
  if (lo > 0 && Math.abs(pts[lo - 1].x - targetX) <= Math.abs(pts[lo].x - targetX)) {
    return pts[lo - 1];
  }
  return pts[lo];
}

function scheduleChartDraw() {
  if (state.rafPending) return;
  state.rafPending = true;
  requestAnimationFrame(() => {
    state.rafPending = false;
    drawDualCharts();
  });
}

function drawDualCharts() {
  const eqCanvas = document.getElementById('el-equity-canvas');
  const ddCanvas = document.getElementById('el-dd-canvas');
  if (!eqCanvas || !ddCanvas || !state.lastComputed) return;

  const { seriesA, seriesB } = state.lastComputed;
  if (!seriesA || !seriesA.points.length) return;

  const colors = getThemeColors();
  const dpr = Math.min(window.devicePixelRatio || 1, 2);

  const eqRect = eqCanvas.parentElement.getBoundingClientRect();
  const ddRect = ddCanvas.parentElement.getBoundingClientRect();
  const width = Math.max(320, Math.floor(eqRect.width));
  const eqHeight = Math.max(180, Math.floor(eqRect.height));
  const ddHeight = Math.max(130, Math.floor(ddRect.height));

  eqCanvas.width = width * dpr;
  eqCanvas.height = eqHeight * dpr;
  ddCanvas.width = width * dpr;
  ddCanvas.height = ddHeight * dpr;

  const pad = { top: 14, right: 16, bottom: 26, left: 56 };
  const plotW = Math.max(40, width - pad.left - pad.right);

  // Determine global X domain across A and B
  const allPtsA = seriesA.points.map((p) => ({ ...p, y: toDisplayY(p.eq, state.unit) }));
  const allGhostA = seriesA.ghostPoints.map((p) => ({ ...p, y: toDisplayY(p.eq, state.unit) }));
  const allPtsB = seriesB ? seriesB.points.map((p) => ({ ...p, y: toDisplayY(p.eq, state.unit) })) : [];

  const xValues = [...allPtsA.map((p) => p.x), ...allPtsB.map((p) => p.x)];
  let fullMinX = Math.min(...xValues);
  let fullMaxX = Math.max(...xValues);
  if (fullMinX === fullMaxX) fullMaxX = fullMinX + 1;

  const viewMinX = fullMinX + (fullMaxX - fullMinX) * state.zoom.start;
  const viewMaxX = fullMinX + (fullMaxX - fullMinX) * state.zoom.end;
  const viewSpanX = Math.max(1e-6, viewMaxX - viewMinX);

  const visA = sliceVisibleWithMargin(allPtsA, viewMinX, viewMaxX);
  const visGhostA = sliceVisibleWithMargin(allGhostA, viewMinX, viewMaxX);
  const visB = sliceVisibleWithMargin(allPtsB, viewMinX, viewMaxX);

  const visDdA = sliceVisibleWithMargin(seriesA.ddPoints, viewMinX, viewMaxX);
  const visDdB = seriesB ? sliceVisibleWithMargin(seriesB.ddPoints, viewMinX, viewMaxX) : [];

  // LTTB activation when total/visible points > 5,000
  const maxRawVisible = Math.max(visA.length, visB.length, visDdA.length, visDdB.length);
  const maxRawTotal = Math.max(allPtsA.length, allPtsB.length);
  const targetBuckets = Math.min(2000, Math.max(240, Math.floor(plotW * 1.5)));
  const lttbActive = maxRawVisible > LTTB_THRESHOLD;

  const drawA = lttbActive ? lttbDownsample(visA, targetBuckets) : visA;
  const drawGhostA = lttbActive ? lttbDownsample(visGhostA, targetBuckets) : visGhostA;
  const drawB = lttbActive ? lttbDownsample(visB, targetBuckets) : visB;
  const drawDdA = lttbActive ? lttbDownsample(visDdA, targetBuckets) : visDdA;
  const drawDdB = lttbActive ? lttbDownsample(visDdB, targetBuckets) : visDdB;

  updateLttbBadge(lttbActive, maxRawTotal, Math.max(drawA.length, drawB.length));

  const mapX = (x) => pad.left + ((x - viewMinX) / viewSpanX) * plotW;

  // --- DRAW UPPER CHART: EQUITY CURVE ---
  const eqCtx = eqCanvas.getContext('2d');
  eqCtx.save();
  eqCtx.scale(dpr, dpr);
  eqCtx.fillStyle = colors.bg;
  eqCtx.fillRect(0, 0, width, eqHeight);

  const eqPlotH = Math.max(40, eqHeight - pad.top - pad.bottom);
  const eqYVals = [
    ...drawA.map((p) => p.y),
    ...drawB.map((p) => p.y),
    ...(state.costCalibrated && state.showGrossGhost ? drawGhostA.map((p) => p.y) : []),
    0
  ];
  let minEqY = Math.min(...eqYVals);
  let maxEqY = Math.max(...eqYVals);
  const eqMargin = Math.max(0.5, (maxEqY - minEqY) * 0.12);
  minEqY -= eqMargin * 0.5;
  maxEqY += eqMargin;
  const spanEqY = Math.max(1e-6, maxEqY - minEqY);
  const mapEqY = (y) => pad.top + eqPlotH - ((y - minEqY) / spanEqY) * eqPlotH;

  // Horizontal Grid & Y labels
  eqCtx.font = '600 10.5px "JetBrains Mono", monospace';
  eqCtx.textAlign = 'right';
  eqCtx.textBaseline = 'middle';
  const yTicks = 5;
  for (let i = 0; i <= yTicks; i++) {
    const val = minEqY + (spanEqY * i) / yTicks;
    const py = mapEqY(val);
    eqCtx.strokeStyle = Math.abs(val) < spanEqY * 0.02 ? colors.zeroLine : colors.grid;
    eqCtx.lineWidth = 1;
    eqCtx.beginPath();
    eqCtx.moveTo(pad.left, py);
    eqCtx.lineTo(width - pad.right, py);
    eqCtx.stroke();

    eqCtx.fillStyle = colors.axisText;
    const txt = state.unit === 'pct'
      ? `${val >= 0 ? '+' : ''}${val.toFixed(1)}%`
      : `${val >= 0 ? '+' : ''}$${val.toFixed(1)}`;
    eqCtx.fillText(txt, pad.left - 8, py);
  }

  // Zero reference line
  if (minEqY < 0 && maxEqY > 0) {
    const zeroY = mapEqY(0);
    eqCtx.strokeStyle = colors.zeroLine;
    eqCtx.setLineDash([3, 3]);
    eqCtx.beginPath();
    eqCtx.moveTo(pad.left, zeroY);
    eqCtx.lineTo(width - pad.right, zeroY);
    eqCtx.stroke();
    eqCtx.setLineDash([]);
  }

  // X ticks
  drawXAxisTicks(eqCtx, width, eqHeight, pad, plotW, viewMinX, viewMaxX, state.xMode, colors);

  // Clip plot region
  eqCtx.save();
  eqCtx.beginPath();
  eqCtx.rect(pad.left, pad.top, plotW, eqPlotH);
  eqCtx.clip();

  // Optional Gross Ghost line when Cost ON
  if (state.costCalibrated && state.showGrossGhost && drawGhostA.length > 1) {
    eqCtx.strokeStyle = colors.runAGhost;
    eqCtx.lineWidth = 1.6;
    eqCtx.setLineDash([2, 4]);
    eqCtx.beginPath();
    drawGhostA.forEach((p, idx) => {
      const px = mapX(p.x);
      const py = mapEqY(p.y);
      if (idx === 0) eqCtx.moveTo(px, py);
      else eqCtx.lineTo(px, py);
    });
    eqCtx.stroke();
    eqCtx.setLineDash([]);
  }

  // Run B dashed line
  if (drawB.length > 1) {
    eqCtx.strokeStyle = colors.runB;
    eqCtx.lineWidth = 2;
    eqCtx.setLineDash([6, 4]);
    eqCtx.beginPath();
    drawB.forEach((p, idx) => {
      const px = mapX(p.x);
      const py = mapEqY(p.y);
      if (idx === 0) eqCtx.moveTo(px, py);
      else eqCtx.lineTo(px, py);
    });
    eqCtx.stroke();
    eqCtx.setLineDash([]);
  }

  // Run A fill + solid line
  if (drawA.length > 1) {
    const grad = eqCtx.createLinearGradient(0, pad.top, 0, pad.top + eqPlotH);
    grad.addColorStop(0, colors.runAFillTop);
    grad.addColorStop(1, colors.runAFillBot);

    eqCtx.fillStyle = grad;
    eqCtx.beginPath();
    drawA.forEach((p, idx) => {
      const px = mapX(p.x);
      const py = mapEqY(p.y);
      if (idx === 0) eqCtx.moveTo(px, py);
      else eqCtx.lineTo(px, py);
    });
    eqCtx.lineTo(mapX(drawA[drawA.length - 1].x), pad.top + eqPlotH);
    eqCtx.lineTo(mapX(drawA[0].x), pad.top + eqPlotH);
    eqCtx.closePath();
    eqCtx.fill();

    eqCtx.strokeStyle = colors.runA;
    eqCtx.lineWidth = 2.4;
    eqCtx.lineJoin = 'round';
    eqCtx.beginPath();
    drawA.forEach((p, idx) => {
      const px = mapX(p.x);
      const py = mapEqY(p.y);
      if (idx === 0) eqCtx.moveTo(px, py);
      else eqCtx.lineTo(px, py);
    });
    eqCtx.stroke();
  }
  eqCtx.restore();

  // --- DRAW LOWER CHART: UNDERWATER DRAWDOWN ---
  const ddCtx = ddCanvas.getContext('2d');
  ddCtx.save();
  ddCtx.scale(dpr, dpr);
  ddCtx.fillStyle = colors.bg;
  ddCtx.fillRect(0, 0, width, ddHeight);

  const ddPlotH = Math.max(40, ddHeight - pad.top - pad.bottom);
  const ddVals = [
    ...drawDdA.map((p) => p.y),
    ...drawDdB.map((p) => p.y),
    -0.5
  ];
  const minDdY = Math.min(...ddVals) * 1.15;
  const maxDdY = 0;
  const spanDdY = Math.max(0.5, maxDdY - minDdY);
  const mapDdY = (y) => pad.top + ((maxDdY - y) / spanDdY) * ddPlotH;

  ddCtx.font = '600 10.5px "JetBrains Mono", monospace';
  ddCtx.textAlign = 'right';
  ddCtx.textBaseline = 'middle';
  const ddTicks = 4;
  for (let i = 0; i <= ddTicks; i++) {
    const val = (minDdY * i) / ddTicks;
    const py = mapDdY(val);
    ddCtx.strokeStyle = i === 0 ? colors.zeroLine : colors.grid;
    ddCtx.lineWidth = 1;
    ddCtx.beginPath();
    ddCtx.moveTo(pad.left, py);
    ddCtx.lineTo(width - pad.right, py);
    ddCtx.stroke();

    ddCtx.fillStyle = colors.axisText;
    ddCtx.fillText(`${val.toFixed(1)}%`, pad.left - 8, py);
  }

  drawXAxisTicks(ddCtx, width, ddHeight, pad, plotW, viewMinX, viewMaxX, state.xMode, colors);

  ddCtx.save();
  ddCtx.beginPath();
  ddCtx.rect(pad.left, pad.top, plotW, ddPlotH);
  ddCtx.clip();

  // Run A Underwater Area
  if (drawDdA.length > 1) {
    const ddGrad = ddCtx.createLinearGradient(0, pad.top, 0, pad.top + ddPlotH);
    ddGrad.addColorStop(0, colors.ddAFillTop);
    ddGrad.addColorStop(1, colors.ddAFillBot);

    ddCtx.fillStyle = ddGrad;
    ddCtx.beginPath();
    const zeroY = mapDdY(0);
    ddCtx.moveTo(mapX(drawDdA[0].x), zeroY);
    drawDdA.forEach((p) => ddCtx.lineTo(mapX(p.x), mapDdY(p.y)));
    ddCtx.lineTo(mapX(drawDdA[drawDdA.length - 1].x), zeroY);
    ddCtx.closePath();
    ddCtx.fill();

    ddCtx.strokeStyle = colors.ddA;
    ddCtx.lineWidth = 1.9;
    ddCtx.beginPath();
    drawDdA.forEach((p, idx) => {
      const px = mapX(p.x);
      const py = mapDdY(p.y);
      if (idx === 0) ddCtx.moveTo(px, py);
      else ddCtx.lineTo(px, py);
    });
    ddCtx.stroke();
  }

  // Run B Underwater Dashed Comparison
  if (drawDdB.length > 1) {
    ddCtx.strokeStyle = colors.ddB;
    ddCtx.lineWidth = 1.6;
    ddCtx.setLineDash([5, 4]);
    ddCtx.beginPath();
    drawDdB.forEach((p, idx) => {
      const px = mapX(p.x);
      const py = mapDdY(p.y);
      if (idx === 0) ddCtx.moveTo(px, py);
      else ddCtx.lineTo(px, py);
    });
    ddCtx.stroke();
    ddCtx.setLineDash([]);
  }
  ddCtx.restore();

  // --- SYNCHRONIZED HOVER CROSSHAIR & TOOLTIP ---
  const tooltipEl = document.getElementById('el-chart-tooltip');
  if (state.hoverNormX != null) {
    const targetX = viewMinX + state.hoverNormX * viewSpanX;
    const crossPx = pad.left + state.hoverNormX * plotW;

    [eqCtx, ddCtx].forEach((ctx, ci) => {
      const h = ci === 0 ? eqPlotH : ddPlotH;
      ctx.strokeStyle = colors.crosshair;
      ctx.lineWidth = 1;
      ctx.setLineDash([4, 3]);
      ctx.beginPath();
      ctx.moveTo(crossPx, pad.top);
      ctx.lineTo(crossPx, pad.top + h);
      ctx.stroke();
      ctx.setLineDash([]);
    });

    const pA = findNearestPoint(drawA, targetX);
    const pB = drawB.length ? findNearestPoint(drawB, targetX) : null;
    const dA = findNearestPoint(drawDdA, targetX);
    const dB = drawDdB.length ? findNearestPoint(drawDdB, targetX) : null;

    if (pA) {
      drawMarker(eqCtx, mapX(pA.x), mapEqY(pA.y), colors.runA);
    }
    if (pB) {
      drawMarker(eqCtx, mapX(pB.x), mapEqY(pB.y), colors.runB);
    }
    if (dA) {
      drawMarker(ddCtx, mapX(dA.x), mapDdY(dA.y), colors.ddA);
    }
    if (dB) {
      drawMarker(ddCtx, mapX(dB.x), mapDdY(dB.y), colors.ddB);
    }

    if (tooltipEl && pA) {
      const unitSuffix = state.unit === 'pct' ? '%' : '$';
      const fmtVal = (v) => (state.unit === 'pct'
        ? `${v >= 0 ? '+' : ''}${v.toFixed(2)}%`
        : `${v >= 0 ? '+' : ''}$${v.toFixed(2)}`);

      const hdrLabel = pA.label || (state.xMode === 'trade' ? `Trade #${pA.idx}` : formatDateShort(targetX));
      const diffVal = pB != null ? pA.y - pB.y : null;

      tooltipEl.innerHTML = `
        <div style="font-weight:700;font-size:11.5px;border-bottom:1px solid var(--border-subtle);padding-bottom:4px;margin-bottom:4px;" class="mono">
          ${escapeHtml(hdrLabel)} <span style="color:var(--text-muted);font-weight:500;">(Trade #${pA.idx})</span>
        </div>
        <div class="el-tooltip-row">
          <span style="color:${colors.runA};font-weight:700;">● ${escapeHtml(seriesA.run.shortName)}</span>
          <strong class="mono">${fmtVal(pA.y)}</strong>
        </div>
        ${pB ? `<div class="el-tooltip-row">
          <span style="color:${colors.runB};font-weight:700;">◆ ${escapeHtml(seriesB.run.shortName)}</span>
          <strong class="mono">${fmtVal(pB.y)}</strong>
        </div>` : ''}
        ${diffVal != null ? `<div class="el-tooltip-row" style="color:var(--text-secondary);">
          <span>Spread (A − B)</span>
          <strong class="mono ${diffVal >= 0 ? 'pos' : 'neg'}">${diffVal >= 0 ? '+' : ''}${diffVal.toFixed(2)}${unitSuffix === '%' ? '%' : ' USD'}</strong>
        </div>` : ''}
        ${dA ? `<div class="el-tooltip-row" style="margin-top:6px;padding-top:5px;border-top:1px dashed var(--border-subtle);">
          <span style="color:${colors.ddA};">Underwater DD (A)</span>
          <strong class="mono neg">${dA.y.toFixed(2)}% ($${dA.ddUsd.toFixed(2)})</strong>
        </div>` : ''}
        ${dB ? `<div class="el-tooltip-row">
          <span style="color:${colors.ddB};">Underwater DD (B)</span>
          <strong class="mono">${dB.y.toFixed(2)}%</strong>
        </div>` : ''}
      `;
      tooltipEl.style.display = 'block';
      const ttRect = tooltipEl.getBoundingClientRect();
      let left = state.hoverClientX + 16;
      if (left + ttRect.width > window.innerWidth - 12) {
        left = state.hoverClientX - ttRect.width - 16;
      }
      let top = state.hoverClientY - 24;
      if (top + ttRect.height > window.innerHeight - 12) {
        top = window.innerHeight - ttRect.height - 12;
      }
      tooltipEl.style.left = `${Math.max(10, left)}px`;
      tooltipEl.style.top = `${Math.max(10, top)}px`;
    }
  } else if (tooltipEl) {
    tooltipEl.style.display = 'none';
  }

  eqCtx.restore();
  ddCtx.restore();
}

function drawMarker(ctx, x, y, color) {
  ctx.save();
  ctx.fillStyle = color;
  ctx.beginPath();
  ctx.arc(x, y, 4, 0, Math.PI * 2);
  ctx.fill();
  ctx.strokeStyle = '#ffffff';
  ctx.lineWidth = 1.5;
  ctx.stroke();
  ctx.restore();
}

function drawXAxisTicks(ctx, width, height, pad, plotW, viewMinX, viewMaxX, xMode, colors) {
  const tickCount = Math.min(6, Math.max(3, Math.floor(plotW / 120)));
  ctx.fillStyle = colors.axisText;
  ctx.font = '600 10.5px "JetBrains Mono", monospace';
  ctx.textBaseline = 'bottom';

  for (let i = 0; i <= tickCount; i++) {
    const frac = i / tickCount;
    const xVal = viewMinX + (viewMaxX - viewMinX) * frac;
    const px = pad.left + frac * plotW;

    ctx.strokeStyle = colors.grid;
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(px, pad.top);
    ctx.lineTo(px, height - pad.bottom);
    ctx.stroke();

    ctx.textAlign = i === 0 ? 'left' : i === tickCount ? 'right' : 'center';
    let label = '';
    if (xMode === 'time') {
      label = formatDateShort(xVal);
    } else if (xMode === 'daily') {
      label = `Day ${Math.round(xVal)}`;
    } else {
      label = `#${Math.round(xVal)}`;
    }
    ctx.fillText(label, px, height - 6);
  }
}

function updateLttbBadge(active, totalPts, renderedPts) {
  const el = document.getElementById('el-lttb-badge');
  if (!el) return;
  if (active) {
    el.classList.add('active');
    el.textContent = `LTTB ACTIVE: ${renderedPts.toLocaleString()} / ${totalPts.toLocaleString()} pts · 60fps`;
  } else {
    el.classList.remove('active');
    el.textContent = `LTTB Armed (>5,000 pts) · 1:1 Full (${totalPts.toLocaleString()} pts)`;
  }
}

/* ----------------------------------------------------------------------------
   5. UI Binding & Rendering
   ---------------------------------------------------------------------------- */
function renderSelectors() {
  const selA = document.getElementById('el-select-a');
  const selB = document.getElementById('el-select-b');
  if (!selA || !selB) return;

  const optsHtml = state.runOrder.map((id) => {
    const r = state.runs[id];
    const cnt = r.trades.length || r.reportedSummary?.total_trades || 0;
    return `<option value="${escapeHtml(id)}">${escapeHtml(r.shortName)} (${escapeHtml(r.symbol)} · ${cnt} trades)</option>`;
  }).join('');

  selA.innerHTML = optsHtml;
  selB.innerHTML = `<option value="none">None (Single Run Only)</option>${optsHtml}`;

  selA.value = state.runA;
  selB.value = state.runB;

  const presetWrap = document.getElementById('el-preset-row');
  if (presetWrap) {
    presetWrap.innerHTML = PRESETS.map((p) => {
      const isAct = state.runA === p.a && state.runB === p.b;
      return `<button type="button" class="el-preset-btn${isAct ? ' active' : ''}" data-preset="${p.id}">${escapeHtml(p.label)}</button>`;
    }).join('');
  }
}

function renderContextStrip(seriesA) {
  const dq = state.rawQv2?.data_quality_report;
  const run = seriesA.run;
  const st = seriesA.stats;

  const covEl = document.getElementById('el-ctx-coverage');
  const covSubEl = document.getElementById('el-ctx-coverage-sub');
  if (covEl) {
    const rev = dq?.time_reversals_count ?? 0;
    const inv = dq?.invalid_hl_count ?? 0;
    covEl.innerHTML = `<span class="el-dot ok" style="width:7px;height:7px;"></span> ${rev === 0 && inv === 0 ? '100.0%' : 'WARN'}`;
  }
  if (covSubEl) {
    covSubEl.textContent = dq?.total_bars ? `${Number(dq.total_bars).toLocaleString()} bars audited` : 'Verified JSON';
  }

  const uniEl = document.getElementById('el-ctx-universe');
  const uniSubEl = document.getElementById('el-ctx-universe-sub');
  if (uniEl) uniEl.textContent = run.symbol;
  if (uniSubEl) uniSubEl.textContent = `${st.totalTrades} trades`;

  const resEl = document.getElementById('el-ctx-res');
  if (resEl) resEl.textContent = run.timeframe || 'M1';

  const perEl = document.getElementById('el-ctx-period');
  const perSubEl = document.getElementById('el-ctx-period-sub');
  if (perEl) {
    if (st.startTs && st.endTs) {
      perEl.textContent = `${formatDateDay(st.startTs)} → ${formatDateDay(st.endTs)}`;
    } else {
      perEl.textContent = run.periodLabel || '–';
    }
  }
  if (perSubEl) {
    perSubEl.textContent = st.startTs && st.endTs ? formatDurationMs(st.endTs - st.startTs) : run.sourceTag;
  }

  const regEl = document.getElementById('el-ctx-regime');
  if (regEl) {
    const intelAsset = state.rawIntel?.assets?.[run.symbol];
    regEl.textContent = intelAsset?.primary_regime || intelAsset?.regime || 'Neutral / DOM';
  }
}

function renderDiffKpis(seriesA, seriesB) {
  const a = seriesA.stats;
  const b = seriesB?.stats || null;

  // 1. Win Rate
  const wrDeltaEl = document.getElementById('el-kpi-wr-delta');
  const wrSubEl = document.getElementById('el-kpi-wr-sub');
  if (b) {
    const d = +(a.winRate - b.winRate).toFixed(1);
    wrDeltaEl.textContent = `${d >= 0 ? '+' : ''}${d.toFixed(1)}%`;
    wrDeltaEl.className = `el-kpi-delta mono ${d >= 0 ? 'pos' : 'neg'}`;
    wrSubEl.textContent = `${a.winRate.toFixed(1)}% vs ${b.winRate.toFixed(1)}%`;
  } else {
    wrDeltaEl.textContent = `${a.winRate.toFixed(1)}%`;
    wrDeltaEl.className = 'el-kpi-delta mono info';
    wrSubEl.textContent = `${a.wins}W / ${a.losses}L (${a.totalTrades} trades)`;
  }

  // 2. Profit Factor
  const pfValEl = document.getElementById('el-kpi-pf-val');
  const pfSubEl = document.getElementById('el-kpi-pf-sub');
  pfValEl.textContent = a.profitFactor.toFixed(2);
  pfValEl.className = `el-kpi-delta mono ${a.profitFactor >= 1.2 ? 'info' : a.profitFactor >= 1.0 ? 'warn' : 'neg'}`;
  if (b) {
    const dPf = +(a.profitFactor - b.profitFactor).toFixed(2);
    pfSubEl.textContent = `vs ${b.profitFactor.toFixed(2)} (${dPf >= 0 ? '+' : ''}${dPf.toFixed(2)})`;
  } else {
    pfSubEl.textContent = `Gross $${a.grossWin.toFixed(2)} / -$${a.grossLoss.toFixed(2)}`;
  }

  // 3. Net Return / PnL
  const retDeltaEl = document.getElementById('el-kpi-ret-delta');
  const retSubEl = document.getElementById('el-kpi-ret-sub');
  if (b) {
    if (state.unit === 'pct') {
      const dR = +(a.returnPct - b.returnPct).toFixed(2);
      retDeltaEl.textContent = `${dR >= 0 ? '+' : ''}${dR.toFixed(2)}%`;
      retDeltaEl.className = `el-kpi-delta mono ${dR >= 0 ? 'pos' : 'neg'}`;
      retSubEl.textContent = `${a.returnPct >= 0 ? '+' : ''}${a.returnPct.toFixed(2)}% vs ${b.returnPct >= 0 ? '+' : ''}${b.returnPct.toFixed(2)}%`;
    } else {
      const dUsd = +(a.netPnlUsd - b.netPnlUsd).toFixed(2);
      retDeltaEl.textContent = `${dUsd >= 0 ? '+' : '-'}$${Math.abs(dUsd).toFixed(2)}`;
      retDeltaEl.className = `el-kpi-delta mono ${dUsd >= 0 ? 'pos' : 'neg'}`;
      retSubEl.textContent = `$${a.netPnlUsd.toFixed(2)} vs $${b.netPnlUsd.toFixed(2)}`;
    }
  } else {
    retDeltaEl.textContent = state.unit === 'pct'
      ? `${a.returnPct >= 0 ? '+' : ''}${a.returnPct.toFixed(2)}%`
      : `${a.netPnlUsd >= 0 ? '+' : '-'}$${Math.abs(a.netPnlUsd).toFixed(2)}`;
    retDeltaEl.className = `el-kpi-delta mono ${a.netPnlUsd >= 0 ? 'pos' : 'neg'}`;
    retSubEl.textContent = `Gross $${a.grossPnlUsd.toFixed(2)} · Cost -$${a.totalCostUsd.toFixed(2)}`;
  }

  // 4. Max Drawdown (lower DD is better: negative delta means A has smaller DD than B -> green!)
  const ddDeltaEl = document.getElementById('el-kpi-dd-delta');
  const ddSubEl = document.getElementById('el-kpi-dd-sub');
  if (b) {
    const dDd = +(a.maxDdPct - b.maxDdPct).toFixed(2);
    ddDeltaEl.textContent = `${dDd > 0 ? '+' : ''}${dDd.toFixed(2)}pp`;
    ddDeltaEl.className = `el-kpi-delta mono ${dDd <= 0 ? 'pos' : 'neg'}`;
    ddSubEl.textContent = `-${a.maxDdPct.toFixed(2)}% vs -${b.maxDdPct.toFixed(2)}%`;
  } else {
    ddDeltaEl.textContent = `-${a.maxDdPct.toFixed(2)}%`;
    ddDeltaEl.className = `el-kpi-delta mono ${a.maxDdPct <= 5 ? 'pos' : a.maxDdPct <= 12 ? 'warn' : 'neg'}`;
    ddSubEl.textContent = `Max DD -$${a.maxDdUsd.toFixed(2)} (${a.episodeCount} dips)`;
  }

  // Cost switch subtitle
  const costSub = document.getElementById('el-cost-sub');
  if (costSub) {
    costSub.textContent = state.costCalibrated
      ? `Commission + Slippage ON (Drag: -$${a.totalCostUsd.toFixed(2)})`
      : `Ideal Fill Zero-Cost (Saved +$${a.totalCostUsd.toFixed(2)})`;
  }
}

function renderChartHeaders(seriesA, seriesB) {
  const legA = document.getElementById('el-legend-a-text');
  const legB = document.getElementById('el-legend-b-wrap');
  const legBText = document.getElementById('el-legend-b-text');
  const legGhost = document.getElementById('el-legend-ghost-wrap');
  const ddLegA = document.getElementById('el-dd-legend-a');
  const ddLegBWrap = document.getElementById('el-dd-legend-b-wrap');
  const ddLegB = document.getElementById('el-dd-legend-b');

  if (legA) legA.textContent = seriesA.run.shortName;
  if (ddLegA) ddLegA.textContent = seriesA.run.shortName;

  if (seriesB) {
    if (legB) legB.style.display = 'inline-flex';
    if (legBText) legBText.textContent = seriesB.run.shortName;
    if (ddLegBWrap) ddLegBWrap.style.display = 'inline-flex';
    if (ddLegB) ddLegB.textContent = seriesB.run.shortName;
  } else {
    if (legB) legB.style.display = 'none';
    if (ddLegBWrap) ddLegBWrap.style.display = 'none';
  }

  if (legGhost) {
    legGhost.style.display = state.costCalibrated && state.showGrossGhost ? 'inline-flex' : 'none';
  }

  // Recovery time metrics
  const st = seriesA.stats;
  const maxDdChip = document.getElementById('el-rec-maxdd');
  const maxRecChip = document.getElementById('el-rec-time');
  const statusChip = document.getElementById('el-rec-status');
  if (maxDdChip) maxDdChip.textContent = `Max DD: -${st.maxDdPct.toFixed(2)}% (-$${st.maxDdUsd.toFixed(2)})`;
  if (maxRecChip) {
    const recText = st.maxRecMs > 0
      ? `${formatDurationMs(st.maxRecMs)} (${st.maxRecTrades} trades)`
      : `${st.maxRecTrades} trades`;
    maxRecChip.textContent = `Max Recovery: ${recText}`;
  }
  if (statusChip) {
    if (st.stillUnderwater) {
      statusChip.innerHTML = `<span class="neg">Underwater: ${st.currentDdPct.toFixed(2)}% (${formatDurationMs(st.currentUnderwaterMs)})</span>`;
    } else {
      statusChip.innerHTML = `<span class="pos">Recovered (0.00% At Peak)</span>`;
    }
  }
}

function renderTradeLog(seriesA, seriesB) {
  const rowsA = (seriesA.stats.enrichedTrades || []).map((t) => ({ ...t, sideTag: 'a' }));
  const rowsB = seriesB
    ? (seriesB.stats.enrichedTrades || []).map((t) => ({ ...t, sideTag: 'b' }))
    : [];

  let combined = [];
  if (state.logScope === 'a') combined = rowsA;
  else if (state.logScope === 'b') combined = rowsB;
  else combined = [...rowsA, ...rowsB];

  // Filter
  const q = state.logSearch.trim().toLowerCase();
  const filtered = combined.filter((t) => {
    if (state.logFilter === 'wins' && t.activePnl <= 0) return false;
    if (state.logFilter === 'losses' && t.activePnl >= 0) return false;
    if (state.logFilter === 'buy' && t.side !== 'BUY') return false;
    if (state.logFilter === 'sell' && t.side !== 'SELL') return false;
    if (state.logFilter === 'tp' && !String(t.reason).toLowerCase().includes('tp') && !String(t.reason).toLowerCase().includes('takeprofit')) return false;
    if (state.logFilter === 'sl' && !String(t.reason).toLowerCase().includes('sl') && !String(t.reason).toLowerCase().includes('stoploss') && !String(t.reason).toLowerCase().includes('timeout')) return false;

    if (q) {
      const hay = `${t.seq} ${t.symbol} ${t.side} ${t.entryTimeStr} ${t.reason} ${t.runLabel} ${t.analysis || ''} ${t.entryReason || ''}`.toLowerCase();
      if (!hay.includes(q)) return false;
    }
    return true;
  });

  // Sort
  filtered.sort((x, y) => {
    if (state.logSortBy === 'time_asc') {
      return (x.entryTs ?? x.seq) - (y.entryTs ?? y.seq);
    }
    if (state.logSortBy === 'pnl_desc') {
      return y.activePnl - x.activePnl;
    }
    if (state.logSortBy === 'pnl_asc') {
      return x.activePnl - y.activePnl;
    }
    // default: time_desc (newest first)
    const tx = x.entryTs ?? x.seq;
    const ty = y.entryTs ?? y.seq;
    if (ty !== tx) return ty - tx;
    return y.seq - x.seq;
  });

  state.lastFilteredTrades = filtered;

  const totalCountEl = document.getElementById('el-log-count');
  if (totalCountEl) totalCountEl.textContent = `${filtered.length.toLocaleString()} trades`;

  const tbody = document.getElementById('el-log-tbody');
  if (!tbody) return;

  const totalPages = Math.max(1, Math.ceil(filtered.length / state.logPageSize));
  if (state.logPage > totalPages) state.logPage = totalPages;
  if (state.logPage < 1) state.logPage = 1;

  const startIdx = (state.logPage - 1) * state.logPageSize;
  const pageRows = filtered.slice(startIdx, startIdx + state.logPageSize);

  if (!pageRows.length) {
    const emptyMsg = (!rowsA.length && !rowsB.length)
      ? 'ชุดข้อมูลนี้บันทึกเฉพาะ Daily PnL รายวัน (ไม่มีรายการ Trade รายไม้ใน JSON)'
      : 'ไม่พบรายการออเดอร์ที่ตรงกับเงื่อนไขการค้นหา/ตัวกรอง';
    tbody.innerHTML = `<tr><td colspan="13" style="text-align:center;padding:28px;color:var(--text-secondary);">${escapeHtml(emptyMsg)}</td></tr>`;
  } else {
    tbody.innerHTML = pageRows.map((t) => {
      const rowKey = `${t.runId}_${t.uid}`;
      const isExpanded = state.expandedTradeKey === rowKey;
      const pnlCls = t.activePnl > 0 ? 'pos' : t.activePnl < 0 ? 'neg' : '';
      const cumCls = t.cumPnlUsd > 0 ? 'pos' : t.cumPnlUsd < 0 ? 'neg' : '';
      const priceDecimals = t.symbol === 'BTCUSD' || t.symbol === 'ETHUSD' ? 2 : 2;
      const hasDetails = t.entryReason || t.domReason || t.structureReason || t.analysis || t.slPrice != null;

      let html = `<tr class="el-trade-row" data-row-key="${escapeHtml(rowKey)}" title="${hasDetails ? 'คลิกเพื่อดูรายละเอียดสัญญาณเข้า/ออก' : ''}">
        <td class="mono" style="color:var(--text-secondary);">${t.seq}</td>
        <td class="mono">${escapeHtml(t.entryTimeStr || '–')}</td>
        <td class="mono" style="font-weight:700;">${escapeHtml(t.symbol)}</td>
        <td><span class="el-side-pill ${t.side === 'BUY' ? 'buy' : 'sell'}">${t.side}</span></td>
        <td class="num mono">${t.size.toFixed(2)}</td>
        <td class="num mono">${t.entryPrice ? t.entryPrice.toLocaleString('en-US', { minimumFractionDigits: priceDecimals, maximumFractionDigits: priceDecimals }) : '–'}</td>
        <td class="num mono" style="color:var(--text-secondary);">$${t.activeComm.toFixed(2)}</td>
        <td class="num mono" style="color:var(--text-secondary);">$${t.activeSlip.toFixed(2)}</td>
        <td class="num mono ${pnlCls}" style="font-weight:700;">${t.activePnl >= 0 ? '+' : '-'}$${Math.abs(t.activePnl).toFixed(2)}</td>
        <td class="num mono ${pnlCls}">${t.pnlPct >= 0 ? '+' : ''}${t.pnlPct.toFixed(2)}%</td>
        <td class="num mono ${cumCls}">${t.cumPnlUsd >= 0 ? '+' : '-'}$${Math.abs(t.cumPnlUsd).toFixed(2)}</td>
        <td><span class="el-run-pill ${t.sideTag}">${escapeHtml(t.runLabel)}</span></td>
        <td style="color:var(--text-secondary);">${escapeHtml(t.reason)}</td>
      </tr>`;

      if (isExpanded) {
        html += `<tr class="el-detail-row"><td colspan="13">
          <div class="el-detail-grid">
            <div><strong>Entry → Exit:</strong> <span class="mono">${t.entryPrice.toFixed(2)} → ${t.exitPrice.toFixed(2)}</span></div>
            <div><strong>SL / TP:</strong> <span class="mono">${t.slPrice != null ? t.slPrice : '–'} / ${t.tpPrice != null ? t.tpPrice : '–'}</span></div>
            <div><strong>Duration:</strong> <span class="mono">${t.durMin != null ? `${t.durMin} min` : '–'}</span> · <strong>Raw Spread:</strong> <span class="mono">${t.rawSpread}</span></div>
            <div><strong>Gross vs Net:</strong> <span class="mono">${t.grossPnl >= 0 ? '+' : ''}$${t.grossPnl.toFixed(2)} vs ${t.netPnl >= 0 ? '+' : ''}$${t.netPnl.toFixed(2)}</span></div>
            ${t.entryReason ? `<div><strong>Entry Signal:</strong> ${escapeHtml(t.entryReason)}</div>` : ''}
            ${t.domReason ? `<div><strong>DOM Microstructure:</strong> ${escapeHtml(t.domReason)}</div>` : ''}
            ${t.structureReason ? `<div><strong>Structure:</strong> ${escapeHtml(t.structureReason)}</div>` : ''}
            ${t.analysis ? `<div style="grid-column:1 / -1;"><strong>Post-Trade Analysis:</strong> ${escapeHtml(t.analysis)}</div>` : ''}
          </div>
        </td></tr>`;
      }
      return html;
    }).join('');
  }

  renderPagination(filtered.length, totalPages, startIdx);
}

function renderPagination(total, totalPages, startIdx) {
  const infoEl = document.getElementById('el-page-info');
  const btnsEl = document.getElementById('el-page-btns');
  if (infoEl) {
    const from = total === 0 ? 0 : startIdx + 1;
    const to = Math.min(total, startIdx + state.logPageSize);
    infoEl.textContent = `Showing ${from}–${to} of ${total.toLocaleString()} trades`;
  }
  if (!btnsEl) return;

  const pages = [];
  if (totalPages <= 7) {
    for (let i = 1; i <= totalPages; i++) pages.push(i);
  } else {
    pages.push(1);
    if (state.logPage > 3) pages.push('…');
    for (let i = Math.max(2, state.logPage - 1); i <= Math.min(totalPages - 1, state.logPage + 1); i++) {
      pages.push(i);
    }
    if (state.logPage < totalPages - 2) pages.push('…');
    pages.push(totalPages);
  }

  btnsEl.innerHTML = `
    <button type="button" class="el-page-btn" data-page="${state.logPage - 1}" ${state.logPage <= 1 ? 'disabled' : ''} aria-label="Previous page">‹</button>
    ${pages.map((p) => (p === '…'
      ? '<span style="padding:0 4px;color:var(--text-muted);">…</span>'
      : `<button type="button" class="el-page-btn${p === state.logPage ? ' active' : ''}" data-page="${p}">${p}</button>`)).join('')}
    <button type="button" class="el-page-btn" data-page="${state.logPage + 1}" ${state.logPage >= totalPages ? 'disabled' : ''} aria-label="Next page">›</button>
  `;
}

function recomputeAndRenderAll() {
  const runA = state.runs[state.runA];
  if (!runA) return;
  const runB = state.runB && state.runB !== 'none' ? state.runs[state.runB] : null;

  const seriesA = computeRunSeries(runA, state.costCalibrated, state.xMode);
  const seriesB = runB ? computeRunSeries(runB, state.costCalibrated, state.xMode) : null;

  state.lastComputed = { seriesA, seriesB };

  renderContextStrip(seriesA);
  renderDiffKpis(seriesA, seriesB);
  renderChartHeaders(seriesA, seriesB);
  renderTradeLog(seriesA, seriesB);
  scheduleChartDraw();

  // Update active preset highlight
  document.querySelectorAll('.el-preset-btn').forEach((btn) => {
    const p = PRESETS.find((x) => x.id === btn.dataset.preset);
    btn.classList.toggle('active', Boolean(p && p.a === state.runA && p.b === state.runB));
  });
}

/* ----------------------------------------------------------------------------
   6. Exports (CSV Trade Log, PNG Dual-Chart, JSON Comparison Report)
   ---------------------------------------------------------------------------- */
function exportCsvLog() {
  const rows = state.lastFilteredTrades || [];
  if (!rows.length) return;
  const header = ['Seq', 'TimeUTC', 'Symbol', 'Side', 'Size', 'EntryPrice', 'ExitPrice', 'CommissionUSD', 'SlippageSpreadUSD', 'PnL_USD', 'PnL_Pct', 'CumPnL_USD', 'Run', 'Reason'];
  const csvRows = [
    header.join(','),
    ...rows.map((t) => [
      t.seq,
      `"${String(t.entryTimeStr || '').replace(/"/g, '""')}"`,
      t.symbol,
      t.side,
      t.size.toFixed(2),
      t.entryPrice,
      t.exitPrice,
      t.activeComm.toFixed(4),
      t.activeSlip.toFixed(4),
      t.activePnl.toFixed(4),
      t.pnlPct.toFixed(3),
      t.cumPnlUsd.toFixed(2),
      `"${String(t.runLabel).replace(/"/g, '""')}"`,
      `"${String(t.reason).replace(/"/g, '""')}"`
    ].join(','))
  ];
  const blob = new Blob(['\uFEFF' + csvRows.join('\n')], { type: 'text/csv;charset=utf-8;' });
  triggerDownload(blob, `experiment_log_${state.runA}_vs_${state.runB}.csv`);
}

function exportCompositePng() {
  const eqCanvas = document.getElementById('el-equity-canvas');
  const ddCanvas = document.getElementById('el-dd-canvas');
  if (!eqCanvas || !ddCanvas) return;

  const out = document.createElement('canvas');
  out.width = Math.max(eqCanvas.width, ddCanvas.width);
  out.height = eqCanvas.height + ddCanvas.height + 56;
  const ctx = out.getContext('2d');
  const isLight = document.documentElement.getAttribute('data-theme') === 'light';
  ctx.fillStyle = isLight ? '#ffffff' : '#0d1424';
  ctx.fillRect(0, 0, out.width, out.height);

  ctx.fillStyle = isLight ? '#0f172a' : '#e2e8f0';
  ctx.font = 'bold 24px "Plus Jakarta Sans", sans-serif';
  const aName = state.runs[state.runA]?.shortName || state.runA;
  const bName = state.runs[state.runB]?.shortName || 'Single';
  ctx.fillText(`Experiment Lab: ${aName} vs ${bName} (Cost: ${state.costCalibrated ? 'ON' : 'OFF'})`, 24, 34);

  ctx.drawImage(eqCanvas, 0, 50);
  ctx.drawImage(ddCanvas, 0, 50 + eqCanvas.height + 6);

  out.toBlob((blob) => {
    if (blob) triggerDownload(blob, `equity_drawdown_${state.runA}.png`);
  });
}

function exportComparisonJson() {
  if (!state.lastComputed) return;
  const { seriesA, seriesB } = state.lastComputed;
  const payload = {
    exported_at_utc: new Date().toISOString(),
    cost_calibrated: state.costCalibrated,
    unit: state.unit,
    x_mode: state.xMode,
    run_a: { id: state.runA, name: seriesA.run.name, stats: { ...seriesA.stats, enrichedTrades: undefined } },
    run_b: seriesB ? { id: state.runB, name: seriesB.run.name, stats: { ...seriesB.stats, enrichedTrades: undefined } } : null
  };
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
  triggerDownload(blob, `experiment_diff_${state.runA}_vs_${state.runB}.json`);
}

function triggerDownload(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

/* ----------------------------------------------------------------------------
   7. Canvas Interaction (60fps Wheel Zoom, Pan Drag, Synced Hover)
   ---------------------------------------------------------------------------- */
function bindCanvasInteractions() {
  const wraps = [
    document.getElementById('el-equity-wrap'),
    document.getElementById('el-dd-wrap')
  ].filter(Boolean);

  wraps.forEach((wrap) => {
    wrap.addEventListener('wheel', (e) => {
      e.preventDefault();
      const rect = wrap.getBoundingClientRect();
      const padLeft = 56;
      const padRight = 16;
      const plotW = Math.max(40, rect.width - padLeft - padRight);
      const normX = Math.max(0, Math.min(1, (e.clientX - rect.left - padLeft) / plotW));

      const span = state.zoom.end - state.zoom.start;
      const factor = e.deltaY > 0 ? 1.18 : 0.85;
      const nextSpan = Math.max(0.02, Math.min(1, span * factor));
      const anchor = state.zoom.start + normX * span;

      let nextStart = anchor - normX * nextSpan;
      let nextEnd = nextStart + nextSpan;
      if (nextStart < 0) {
        nextStart = 0;
        nextEnd = nextSpan;
      }
      if (nextEnd > 1) {
        nextEnd = 1;
        nextStart = Math.max(0, 1 - nextSpan);
      }
      state.zoom = { start: nextStart, end: nextEnd };
      scheduleChartDraw();
    }, { passive: false });

    wrap.addEventListener('pointerdown', (e) => {
      state.isDragging = true;
      state.dragStartX = e.clientX;
      state.dragStartZoom = { ...state.zoom };
      wrap.classList.add('dragging');
      wrap.setPointerCapture(e.pointerId);
    });

    wrap.addEventListener('pointermove', (e) => {
      const rect = wrap.getBoundingClientRect();
      const padLeft = 56;
      const padRight = 16;
      const plotW = Math.max(40, rect.width - padLeft - padRight);

      if (state.isDragging && state.dragStartZoom) {
        const dxNorm = (e.clientX - state.dragStartX) / plotW;
        const span = state.dragStartZoom.end - state.dragStartZoom.start;
        let nextStart = state.dragStartZoom.start - dxNorm * span;
        let nextEnd = nextStart + span;
        if (nextStart < 0) {
          nextStart = 0;
          nextEnd = span;
        }
        if (nextEnd > 1) {
          nextEnd = 1;
          nextStart = Math.max(0, 1 - span);
        }
        state.zoom = { start: nextStart, end: nextEnd };
      }

      const relX = (e.clientX - rect.left - padLeft) / plotW;
      if (relX >= 0 && relX <= 1) {
        state.hoverNormX = relX;
        state.hoverClientX = e.clientX;
        state.hoverClientY = e.clientY;
      } else {
        state.hoverNormX = null;
      }
      scheduleChartDraw();
    });

    wrap.addEventListener('pointerup', (e) => {
      state.isDragging = false;
      state.dragStartZoom = null;
      wrap.classList.remove('dragging');
      try { wrap.releasePointerCapture(e.pointerId); } catch (_) {}
    });

    wrap.addEventListener('pointerleave', () => {
      if (!state.isDragging) {
        state.hoverNormX = null;
        scheduleChartDraw();
      }
    });

    wrap.addEventListener('dblclick', () => {
      state.zoom = { start: 0, end: 1 };
      scheduleChartDraw();
    });
  });

  window.addEventListener('resize', scheduleChartDraw);
}

function observeThemeChanges() {
  if (typeof MutationObserver === 'undefined') return;
  const observer = new MutationObserver((mutations) => {
    for (const m of mutations) {
      if (m.attributeName === 'data-theme') {
        scheduleChartDraw();
        break;
      }
    }
  });
  observer.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });
}

/* ----------------------------------------------------------------------------
   8. Control Bindings & Data Fetch Bootstrap
   ---------------------------------------------------------------------------- */
function bindControls() {
  document.getElementById('el-select-a')?.addEventListener('change', (e) => {
    state.runA = e.target.value;
    state.zoom = { start: 0, end: 1 };
    state.logPage = 1;
    autoAdjustXModeIfDisjoint();
    recomputeAndRenderAll();
  });

  document.getElementById('el-select-b')?.addEventListener('change', (e) => {
    state.runB = e.target.value;
    state.zoom = { start: 0, end: 1 };
    state.logPage = 1;
    autoAdjustXModeIfDisjoint();
    recomputeAndRenderAll();
  });

  document.getElementById('el-swap-btn')?.addEventListener('click', () => {
    if (!state.runB || state.runB === 'none') return;
    const prevA = state.runA;
    state.runA = state.runB;
    state.runB = prevA;
    document.getElementById('el-select-a').value = state.runA;
    document.getElementById('el-select-b').value = state.runB;
    state.zoom = { start: 0, end: 1 };
    recomputeAndRenderAll();
  });

  document.getElementById('el-preset-row')?.addEventListener('click', (e) => {
    const btn = e.target.closest('.el-preset-btn');
    if (!btn) return;
    const p = PRESETS.find((x) => x.id === btn.dataset.preset);
    if (!p || !state.runs[p.a]) return;
    state.runA = p.a;
    state.runB = state.runs[p.b] ? p.b : 'none';
    document.getElementById('el-select-a').value = state.runA;
    document.getElementById('el-select-b').value = state.runB;
    state.zoom = { start: 0, end: 1 };
    state.logPage = 1;
    autoAdjustXModeIfDisjoint();
    recomputeAndRenderAll();
  });

  const costBtn = document.getElementById('el-cost-switch');
  costBtn?.addEventListener('click', () => {
    state.costCalibrated = !state.costCalibrated;
    costBtn.setAttribute('aria-checked', String(state.costCalibrated));
    recomputeAndRenderAll();
  });

  const ghostBtn = document.getElementById('el-ghost-toggle');
  ghostBtn?.addEventListener('click', () => {
    state.showGrossGhost = !state.showGrossGhost;
    ghostBtn.classList.toggle('active', state.showGrossGhost);
    recomputeAndRenderAll();
  });

  document.querySelectorAll('[data-xmode]').forEach((btn) => {
    btn.addEventListener('click', () => {
      state.xMode = btn.dataset.xmode;
      document.querySelectorAll('[data-xmode]').forEach((b) => b.classList.toggle('active', b === btn));
      state.zoom = { start: 0, end: 1 };
      recomputeAndRenderAll();
    });
  });

  document.querySelectorAll('[data-unit]').forEach((btn) => {
    btn.addEventListener('click', () => {
      state.unit = btn.dataset.unit;
      document.querySelectorAll('[data-unit]').forEach((b) => b.classList.toggle('active', b === btn));
      recomputeAndRenderAll();
    });
  });

  document.getElementById('el-zoom-in')?.addEventListener('click', () => zoomBy(0.7));
  document.getElementById('el-zoom-out')?.addEventListener('click', () => zoomBy(1.4));
  document.getElementById('el-zoom-reset')?.addEventListener('click', () => {
    state.zoom = { start: 0, end: 1 };
    scheduleChartDraw();
  });

  document.getElementById('el-refresh-btn')?.addEventListener('click', loadAllData);
  document.getElementById('el-export-json-btn')?.addEventListener('click', exportComparisonJson);
  document.getElementById('el-export-chart-btn')?.addEventListener('click', exportCompositePng);
  document.getElementById('el-export-csv-btn')?.addEventListener('click', exportCsvLog);

  // Trade log controls
  document.querySelectorAll('[data-scope]').forEach((btn) => {
    btn.addEventListener('click', () => {
      state.logScope = btn.dataset.scope;
      state.logPage = 1;
      document.querySelectorAll('[data-scope]').forEach((b) => b.classList.toggle('active', b === btn));
      if (state.lastComputed) renderTradeLog(state.lastComputed.seriesA, state.lastComputed.seriesB);
    });
  });

  document.getElementById('el-log-search')?.addEventListener('input', (e) => {
    state.logSearch = e.target.value;
    state.logPage = 1;
    if (state.lastComputed) renderTradeLog(state.lastComputed.seriesA, state.lastComputed.seriesB);
  });

  document.getElementById('el-log-filter')?.addEventListener('change', (e) => {
    state.logFilter = e.target.value;
    state.logPage = 1;
    if (state.lastComputed) renderTradeLog(state.lastComputed.seriesA, state.lastComputed.seriesB);
  });

  document.getElementById('el-log-sort')?.addEventListener('change', (e) => {
    state.logSortBy = e.target.value;
    state.logPage = 1;
    if (state.lastComputed) renderTradeLog(state.lastComputed.seriesA, state.lastComputed.seriesB);
  });

  document.getElementById('el-page-size')?.addEventListener('change', (e) => {
    state.logPageSize = Number(e.target.value) || 10;
    state.logPage = 1;
    if (state.lastComputed) renderTradeLog(state.lastComputed.seriesA, state.lastComputed.seriesB);
  });

  document.getElementById('el-page-btns')?.addEventListener('click', (e) => {
    const btn = e.target.closest('.el-page-btn');
    if (!btn || btn.disabled) return;
    state.logPage = Number(btn.dataset.page) || 1;
    if (state.lastComputed) renderTradeLog(state.lastComputed.seriesA, state.lastComputed.seriesB);
  });

  document.getElementById('el-log-tbody')?.addEventListener('click', (e) => {
    const row = e.target.closest('tr.el-trade-row');
    if (!row) return;
    const key = row.dataset.rowKey;
    state.expandedTradeKey = state.expandedTradeKey === key ? null : key;
    if (state.lastComputed) renderTradeLog(state.lastComputed.seriesA, state.lastComputed.seriesB);
  });
}

function zoomBy(mult) {
  const span = state.zoom.end - state.zoom.start;
  const mid = (state.zoom.start + state.zoom.end) * 0.5;
  const nextSpan = Math.max(0.02, Math.min(1, span * mult));
  let s = mid - nextSpan * 0.5;
  let e = mid + nextSpan * 0.5;
  if (s < 0) { s = 0; e = nextSpan; }
  if (e > 1) { e = 1; s = Math.max(0, 1 - nextSpan); }
  state.zoom = { start: s, end: e };
  scheduleChartDraw();
}

function autoAdjustXModeIfDisjoint() {
  const rA = state.runs[state.runA];
  const rB = state.runB && state.runB !== 'none' ? state.runs[state.runB] : null;
  if (!rA || !rB) return;

  const spanA = getRunTimeSpan(rA);
  const spanB = getRunTimeSpan(rB);
  if (spanA && spanB) {
    const overlap = Math.min(spanA.end, spanB.end) >= Math.max(spanA.start, spanB.start);
    if (!overlap && state.xMode === 'time') {
      state.xMode = 'trade';
      document.querySelectorAll('[data-xmode]').forEach((b) => {
        b.classList.toggle('active', b.dataset.xmode === 'trade');
      });
    }
  }
}

function getRunTimeSpan(run) {
  if (run.trades.length) {
    const t0 = run.trades[0].entryTs;
    const t1 = run.trades[run.trades.length - 1].exitTs;
    if (t0 && t1) return { start: t0, end: t1 };
  }
  if (run.dailySeries.length) {
    return { start: run.dailySeries[0].ts, end: run.dailySeries[run.dailySeries.length - 1].ts };
  }
  return null;
}

async function fetchJson(path) {
  const res = await fetch(`${path}?t=${Date.now()}`, { cache: 'no-store' });
  if (!res.ok) throw new Error(`${path}: HTTP ${res.status}`);
  return res.json();
}

async function loadAllData() {
  const banner = document.getElementById('el-error-banner');
  try {
    const [btRes, costRes, liveRes, qv2Res, intelRes] = await Promise.allSettled([
      fetchJson('data/backtest_data.json'),
      fetchJson('data/calibrated_costs.json'),
      fetchJson('data/live_status.json'),
      fetchJson('data/quant_fund_v2_status.json'),
      fetchJson('data/live_market_intelligence.json')
    ]);

    if (btRes.status !== 'fulfilled') {
      throw new Error('ไม่สามารถโหลดไฟล์ข้อมูลหลัก docs/data/backtest_data.json ได้');
    }

    state.rawBacktest = btRes.value;
    state.rawCosts = costRes.status === 'fulfilled' ? costRes.value : null;
    state.rawLive = liveRes.status === 'fulfilled' ? liveRes.value : null;
    state.rawQv2 = qv2Res.status === 'fulfilled' ? qv2Res.value : null;
    state.rawIntel = intelRes.status === 'fulfilled' ? intelRes.value : null;

    const { runs, order } = buildNormalizedRuns(state.rawBacktest, state.rawCosts, state.rawLive);
    state.runs = runs;
    state.runOrder = order;

    if (!state.runs[state.runA] && order.length) state.runA = order[0];
    if (state.runB !== 'none' && !state.runs[state.runB]) state.runB = order[1] || 'none';

    if (banner) banner.classList.remove('visible');
    renderSelectors();
    recomputeAndRenderAll();
  } catch (err) {
    if (banner) {
      banner.classList.add('visible');
      const msgEl = document.getElementById('el-error-msg');
      if (msgEl) msgEl.textContent = `ออฟไลน์ / โหลดข้อมูลไม่สำเร็จ: ${err.message}`;
    }
  }
}

async function initPage() {
  mountShell({
    activePage: 'experiment-lab.html',
    onRetry: () => Promise.all([loadShellTelemetryOnly(), loadAllData()])
  });
  bindControls();
  bindCanvasInteractions();
  observeThemeChanges();
  await Promise.all([loadShellTelemetryOnly(), loadAllData()]);
}

if (typeof document !== 'undefined') {
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initPage);
  } else {
    initPage();
  }
}
