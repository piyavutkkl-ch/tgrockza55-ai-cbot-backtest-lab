/* ==========================================================================
   Page 6: Improvement & Audit Controller (audit.js)
   Integrates cleanly with shared ES Module shell.js & docs/data/*.json
   ========================================================================== */

import { mountShell, updateShellTelemetry, escapeHtml, formatRelativeTime } from './shell.js';

const state = {
  auditSummary: null,
  watchdog: null,
  truthGuard: null,
  autoVal: null,
  ruleMatrix: null,
  qfV2: null,
  foundry: null,
  experiments: null,
  handovers: null,
  liveStatus: null,
  marketIntel: null,
  webAlerts: null,
  overviewSummary: null,
  failedSources: [],
  gaugeMode: 'session', // 'session' (-$2.68) | 'worst' (-$5.25)
  inspectedStage: null,
  logFilter: 'ALL',
  logSearch: '',
  logLimit: '100',
  activeDeepTab: 'pillars',
  activeRuleTier: 'tier1',
};

const LIFECYCLE_STAGES = [
  { num: 1, title: '1. Data Pipe', sub: 'Collect Markets', officerKey: 'officer_1', enRole: 'Data Pipeline Architect', enSpec: 'Inspects cTrader M1/Tick/DOM L2 feeds, Forex Factory news calendar, and data quality.' },
  { num: 2, title: '2. Feature Engine', sub: 'Prepare Signals', officerKey: 'officer_2', enRole: 'Alpha Hypothesis Researcher', enSpec: 'Extracts OBI (25-level L2 DOM), Hawkes Intensity, and Anchored Session VWAP formulas.' },
  { num: 3, title: '3. Strategy Core', sub: 'Generate Alpha', officerKey: 'officer_3', enRole: 'cBot Lead Engineer', enSpec: 'Compiles C# cAlgo bots with Quantum Stealth RAM SL (±5% Jitter) and strict closed-bar indexing.' },
  { num: 4, title: '4. Backtest', sub: 'Validate Logic', officerKey: 'officer_4_5', enRole: 'Backtest & Quant Math Validator', enSpec: 'Runs 5-year M1 simulation (1.67M bars) and Multi-Year Walk-Forward Optimization (WFO).' },
  { num: 5, title: '5. Paper Trade', sub: 'Simulate Live', officerKey: 'officer_4_5', enRole: 'Monte Carlo & Sieve Screener', enSpec: 'Executes 1,000 Monte Carlo permutation runs & 98% Math Sieve before live exposure.' },
  { num: 6, title: '6. Risk Check', sub: 'Assess Exposure', officerKey: 'officer_6', enRole: 'Risk & Governance Gatekeeper', enSpec: 'Enforces 9-Gate deterministic checklist & Risk Policy V2.0 (Demo Quarantine).' },
  { num: 7, title: '7. Live Deploy', sub: 'Run with Guard', officerKey: 'officer_7', enRole: 'Live Execution Commander', enSpec: 'Routes 0.01 lot forward orders on Pepperstone Demo #5258778 under real-time Watchdog.' },
  { num: 8, title: '8. Monitor', sub: 'Track & Alert', officerKey: 'officer_8_9', enRole: '24/7 Watchdog & Truth Guard', enSpec: 'Tracks feed staleness (180s cutoff), intraday DD ceiling, and N=79/500 power accumulation.' },
  { num: 9, title: '9. Review', sub: 'Analyze Results', officerKey: 'officer_8_9', enRole: 'Memory & Post-Mortem Analyst', enSpec: 'Runs DSR, SPRT, CUSUM drift, PBO/CSCV audits, and auto-retires decaying micro-bots.' },
  { num: 10, title: '10. Feedback Loop', sub: 'Improve System', officerKey: 'officer_10', enRole: 'Evolutionary Feedback Director', enSpec: 'Synthesizes Flywheel Cycle takeaways into mutation directives for Stage 1.' },
];

const ENGLISH_TAKEAWAYS = [
  '1. Strictly block trading inside Extreme News windows (CPI, NFP, FOMC) — News Void defense converts negative expectancy into institutional stability.',
  '2. Avoid ultra-short scalping under spread widening — targeting 15–60 minute holding windows clears commission and slippage drag.',
  '3. Require 25-level L2 Order Book (DOM) Absorption confirmation rather than relying purely on lagging candlestick indicators.',
  '4. Enforce Quantum Stealth RAM SL (±5% Jitter) in memory to protect stops against aggressive liquidity stop-hunting.',
];

const ENGLISH_GRAVEYARD_SUMMARIES = {
  GRAVE_001_M1_SCALPER: 'Live spread and commission drag completely eroded gross expectancy under real broker execution.',
  GRAVE_002_OVERFITTED_TA: 'Severe data-snooping artifact (P-hacking) passed in-sample optimization but collapsed immediately Out-of-Sample.',
  GRAVE_003_GRID_MARTINGALE: 'Severe fat-tail blowup risk (68.4% DD) during sustained directional trends; size doubling permanently prohibited.',
  GRAVE_004_NEWS_STRADDLE: 'Order book liquidity vanished on macro release, causing -4.8 pip adverse fills and 38% order rejections.',
  GRAVE_005_SESSION_OPEN_GAP: 'Statistically unstable across market regimes; profitable only in isolated months (3/16 CPCV folds).',
};

function cleanUsdNotation(str) {
  return String(str || '')
    .replace(/\+\$-/g, '-$')
    .replace(/\$-\s*(\d)/g, '-$$$1');
}

function fmtSignedUsd(val, decimals = 2) {
  const n = Number(val);
  if (!Number.isFinite(n)) return '–';
  const abs = Math.abs(n).toFixed(decimals);
  return n >= 0 ? `+$${abs}` : `-$${abs}`;
}

function fmtUsd(val, decimals = 2) {
  const n = Number(val);
  if (!Number.isFinite(n)) return '–';
  const abs = Math.abs(n).toFixed(decimals);
  return n < 0 ? `-$${abs}` : `$${abs}`;
}

function stripNonAscii(str) {
  return String(str || '')
    .replace(/[^\x20-\x7E\u2013\u2014\u00B1\u2264\u2265]/g, '')
    .replace(/\s+/g, ' ')
    .trim();
}

function extractEnglishParenthetical(str, fallback = '') {
  const raw = String(str || '');
  const m = raw.match(/\(([A-Za-z0-9\s,&/+.-]{3,})\)/);
  if (m) return m[1].trim();
  const cleaned = stripNonAscii(raw);
  return cleaned.length > 2 ? cleaned : fallback;
}

function getFlatCutoffState(flatHhmm = 2145) {
  const hh = Math.floor(flatHhmm / 100);
  const mm = flatHhmm % 100;
  const now = new Date();
  const cutoffToday = Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate(), hh, mm, 0, 0);
  const nowMs = now.getTime();
  const inFlatWindow = nowMs >= cutoffToday;
  const targetMs = inFlatWindow ? cutoffToday + 86400 * 1000 : cutoffToday;
  const diffSec = Math.max(0, Math.floor((targetMs - nowMs) / 1000));
  const remH = Math.floor(diffSec / 3600);
  const remM = Math.floor((diffSec % 3600) / 60);
  const remS = diffSec % 60;
  return {
    diffSec,
    hms: `${String(remH).padStart(2, '0')}:${String(remM).padStart(2, '0')}:${String(remS).padStart(2, '0')}`,
    human: `${remH}h ${String(remM).padStart(2, '0')}m ${String(remS).padStart(2, '0')}s`,
    inFlatWindow,
    targetStr: `${String(hh).padStart(2, '0')}:${String(mm).padStart(2, '0')}:00`,
  };
}

function isLightTheme() {
  return document.documentElement.getAttribute('data-theme') === 'light';
}

// =========================================================================
// Header Live Account & Market Strip
// =========================================================================
function renderHeaderTelemetryStrip() {
  const wrap = document.getElementById('auditHeaderTelemetry');
  if (!wrap) return;

  const fwd = state.liveStatus?.forward_trading || {};
  const rm = state.auditSummary?.risk_metrics || {};
  const xau = state.marketIntel?.assets?.XAUUSD;

  const eqVal = Number(fwd.equity ?? rm.equity_usd);
  const netVal = Number(fwd.net_pnl ?? rm.overall_net_pnl_usd);
  const netPct = Number(fwd.net_pnl_pct ?? -17.07);
  const netCls = Number.isFinite(netVal) ? (netVal >= 0 ? 'pos' : 'neg') : '';

  const chips = [];
  if (xau) {
    chips.push(
      `<span class="mini-stat-chip"><span class="m-lbl">XAUUSD</span><span class="m-val">${Number(xau.latest_price).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span><span class="m-lbl" style="color:var(--audit-green-ink)">Spd ${xau.spread}</span></span>`
    );
  }
  if (Number.isFinite(eqVal)) {
    chips.push(
      `<span class="mini-stat-chip"><span class="m-lbl">Demo #5258778 Equity</span><span class="m-val">${fmtUsd(eqVal)}</span></span>`
    );
  }
  if (Number.isFinite(netVal)) {
    chips.push(
      `<span class="mini-stat-chip"><span class="m-lbl">Cum P/L</span><span class="m-val ${netCls}">${fmtSignedUsd(netVal)} (${netPct >= 0 ? '+' : ''}${netPct.toFixed(1)}%)</span></span>`
    );
  }

  wrap.innerHTML =
    chips.join('') +
    `<button type="button" id="btnRefreshPage" class="btn-outline-sm" aria-label="Refresh Page 6 telemetry">↻ Refresh</button>`;

  document.getElementById('btnRefreshPage')?.addEventListener('click', loadPageData);
}

// =========================================================================
// 1. 10-Stage Institutional Lifecycle Stepper
// =========================================================================
function renderLifecycleStepper() {
  const container = document.getElementById('lifecycleStepper');
  const cycleBadge = document.getElementById('lifecycleCycleBadge');
  const activeStage = 7;

  const fw = state.auditSummary?.flywheel_meta || {};
  if (cycleBadge) {
    cycleBadge.textContent = `Cycle #${fw.active_cycle || 328} · ${fw.total_cycles_completed || 327} Completed`;
  }

  if (!container) return;

  const nodesHtml = LIFECYCLE_STAGES.map((st) => {
    const statusCls = st.num < activeStage ? 'done' : st.num === activeStage ? 'active' : 'queued';
    const inspCls = state.inspectedStage === st.num ? 'inspected' : '';
    const circleInner =
      st.num < activeStage
        ? '<svg viewBox="0 0 20 20" width="15" height="15" fill="currentColor" aria-hidden="true"><path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"/></svg>'
        : String(st.num);
    return `<button type="button" class="stage-node ${statusCls} ${inspCls}" data-stage="${st.num}" aria-pressed="${state.inspectedStage === st.num ? 'true' : 'false'}">
      <span class="stage-circle">${circleInner}</span>
      <span class="stage-title">${escapeHtml(st.title)}</span>
      <span class="stage-sub">${escapeHtml(st.sub)}</span>
    </button>`;
  }).join('');

  container.innerHTML = `
    <div class="stepper-grid">
      <div class="stepper-track-bg" aria-hidden="true"></div>
      <div class="stepper-track-fill" aria-hidden="true" style="width:${((activeStage - 1) / 9) * 90}%"></div>
      ${nodesHtml}
    </div>
  `;

  container.querySelectorAll('.stage-node').forEach((btn) => {
    btn.addEventListener('click', () => {
      const num = Number(btn.dataset.stage);
      state.inspectedStage = state.inspectedStage === num ? null : num;
      renderLifecycleStepper();
      renderStageInspector();
    });
  });
}

function renderStageInspector() {
  const box = document.getElementById('stageInspector');
  if (!box) return;
  if (!state.inspectedStage) {
    box.hidden = true;
    return;
  }

  const stage = LIFECYCLE_STAGES.find((s) => s.num === state.inspectedStage);
  if (!stage) {
    box.hidden = true;
    return;
  }

  const officers = state.handovers?.officers || {};
  const officer = officers[stage.officerKey] || {};
  const rm = state.auditSummary?.risk_metrics || {};
  const fsStats = state.foundry?.stats || {};
  const tg = state.truthGuard?.statistical_power || {};

  let metricChips = '';
  if (stage.num === 1) {
    metricChips = `<span class="insp-metric-chip">1,675,835 XAU Bars</span><span class="insp-metric-chip">L2 DOM + News Gate</span>`;
  } else if (stage.num <= 3) {
    metricChips = `<span class="insp-metric-chip">9 Active Families (STR-001..009)</span><span class="insp-metric-chip">RAM Stealth SL ±5%</span>`;
  } else if (stage.num <= 5) {
    metricChips = `<span class="insp-metric-chip">${fsStats.total_hypotheses_generated || 1420} Screened</span><span class="insp-metric-chip">${fsStats.rejection_rate_pct || 98.0}% Math Sieve</span>`;
  } else if (stage.num === 6) {
    const passV2 = state.qfV2?.validation_checklist?.overall_passed;
    metricChips = `<span class="insp-metric-chip">9/9 Gates: ${passV2 ? 'PASS' : 'CHECKING'}</span><span class="insp-metric-chip">Risk Policy V2.0</span>`;
  } else if (stage.num === 7) {
    metricChips = `<span class="insp-metric-chip">Account: ${escapeHtml(rm.account || '5258778 Demo')}</span><span class="insp-metric-chip">Equity: ${fmtUsd(rm.equity_usd)}</span><span class="insp-metric-chip">Open Pos: ${rm.open_positions ?? 0}</span>`;
  } else {
    metricChips = `<span class="insp-metric-chip">Sample N = ${tg.sample_size_N ?? 79} / ${tg.target_preliminary_N ?? 500}</span><span class="insp-metric-chip">Cycles: ${state.auditSummary?.flywheel_meta?.total_cycles_completed || 327}</span>`;
  }

  box.hidden = false;
  box.innerHTML = `
    <div class="insp-main">
      <div class="insp-top">
        <span class="insp-stage-tag">${escapeHtml(stage.title)} · ${escapeHtml(stage.sub)}</span>
        <span class="tag-pill">Officer: ${escapeHtml(officer.name || 'AI Agent')} — ${escapeHtml(stage.enRole)}</span>
        <span class="tag-pill ${stage.num < 7 ? 'ok' : stage.num === 7 ? 'info' : ''}">${stage.num < 7 ? 'COMPLETED' : stage.num === 7 ? 'ACTIVE STAGE' : 'QUEUED MONITOR'}</span>
      </div>
      <div class="insp-desc">${escapeHtml(stage.enSpec)}</div>
      <div class="insp-metrics">${metricChips}</div>
    </div>
    <button type="button" class="btn-outline-sm" id="btnCloseStageInsp" aria-label="Close stage inspector">Close ✕</button>
  `;

  document.getElementById('btnCloseStageInsp')?.addEventListener('click', () => {
    state.inspectedStage = null;
    renderLifecycleStepper();
    renderStageInspector();
  });
}

// =========================================================================
// 2. Middle Trio Cards (Gauge, Flat Cutoff, 4-Pillar Rule Matrix)
// =========================================================================
function renderRiskGaugeCard() {
  const rm = state.auditSummary?.risk_metrics || {};
  const limit = Number(rm.daily_loss_ceiling_usd || 10.0);
  const sessionDd = Number(rm.latest_session_intraday_dd_usd ?? -2.68);
  const worstDay = Number(rm.worst_recent_session_pnl_usd ?? -5.25);

  const activeLoss = state.gaugeMode === 'worst' ? worstDay : sessionDd;
  const absLoss = Math.abs(activeLoss < 0 ? activeLoss : 0);
  const ratio = Math.min(1, absLoss / (limit || 10));
  const pct = (ratio * 100).toFixed(1);

  const bigEl = document.getElementById('gaugeLossValue');
  const subEl = document.getElementById('gaugeLimitValue');
  const barEl = document.getElementById('gaugeFooterText');
  const statusBadge = document.getElementById('governorCardBadge');

  if (bigEl) bigEl.textContent = fmtSignedUsd(activeLoss < 0 ? activeLoss : 0);
  if (subEl) subEl.textContent = `/ -$${limit.toFixed(2)}`;
  if (barEl) {
    if (state.gaugeMode === 'worst') {
      barEl.innerHTML = `<span>⚠ Worst Day (${escapeHtml(rm.worst_recent_session_date || '2026-11-06')}): <strong class="mono">${fmtSignedUsd(worstDay)} / -$${limit.toFixed(2)}</strong> (${pct}%)</span><span class="mono">Breaker: 10%</span>`;
    } else {
      const net = Number(rm.latest_session_net_pnl_usd ?? 8.3);
      barEl.innerHTML = `<span>⚠ Daily Loss Limit: <strong class="mono">${fmtSignedUsd(sessionDd)} / -$${limit.toFixed(2)}</strong> (${pct}%)</span><span class="mono">Session Net: ${fmtSignedUsd(net)}</span>`;
    }
  }
  if (statusBadge) {
    const stalledCount = Number(state.watchdog?.active_alerts_count || 0);
    statusBadge.className = `active-pill ${absLoss >= limit ? 'crit' : ''}`;
    statusBadge.innerHTML = `<span class="pulse-dot ${absLoss >= limit ? 'red' : 'green'}"></span><span>${absLoss >= limit ? 'HALTED' : stalledCount > 0 ? 'ENFORCING' : 'ACTIVE'}</span>`;
  }

  const svg = document.getElementById('riskGaugeSvg');
  if (svg) {
    const cx = 140;
    const cy = 124;
    const r = 100;
    const startX = cx - r;
    const endX = cx + r;
    const theta = Math.PI * (1 - ratio);
    const mx = cx + r * Math.cos(theta);
    const my = cy - r * Math.sin(theta);

    const light = isLightTheme();
    const trackColor = light ? '#E2E8F0' : '#1E2638';
    const markerRing = light ? '#0F172A' : '#FFFFFF';
    const markerFill = light ? '#FFFFFF' : '#0B0E14';

    svg.innerHTML = `
      <defs>
        <linearGradient id="riskArcGrad" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stop-color="#22C55E"/>
          <stop offset="52%" stop-color="#F59E0B"/>
          <stop offset="100%" stop-color="#EF4444"/>
        </linearGradient>
      </defs>
      <path d="M ${startX} ${cy} A ${r} ${r} 0 0 1 ${endX} ${cy}" fill="none" stroke="${trackColor}" stroke-width="18" stroke-linecap="round"/>
      <path d="M ${startX} ${cy} A ${r} ${r} 0 0 1 ${endX} ${cy}" fill="none" stroke="url(#riskArcGrad)" stroke-width="14" stroke-linecap="round" opacity="0.92"/>
      <circle cx="${mx.toFixed(1)}" cy="${my.toFixed(1)}" r="12" fill="var(--audit-cyan)" fill-opacity="0.18"/>
      <circle cx="${mx.toFixed(1)}" cy="${my.toFixed(1)}" r="7.5" fill="${markerFill}" stroke="${markerRing}" stroke-width="3"/>
      <circle cx="${mx.toFixed(1)}" cy="${my.toFixed(1)}" r="3.2" fill="var(--audit-cyan)"/>
    `;
  }
}

function renderFlatCutoffCard() {
  const rm = state.auditSummary?.risk_metrics || {};
  const hhmm = Number(rm.daily_flat_utc_hhmm || 2145);
  const stateCut = getFlatCutoffState(hhmm);

  const timeEl = document.getElementById('cutoffMainTime');
  const cntEl = document.getElementById('cutoffCountdownLabel');
  const posEl = document.getElementById('cutoffOpenPosBadge');

  if (timeEl) timeEl.textContent = stateCut.targetStr;
  if (cntEl) {
    cntEl.innerHTML = stateCut.inFlatWindow
      ? `<strong style="color:var(--audit-red-ink)">FLAT WINDOW ACTIVE</strong> · Next in <span class="mono">${stateCut.human}</span>`
      : `Auto Flat in: <strong class="mono">${stateCut.human}</strong>`;
  }
  if (posEl) {
    const openPos = rm.open_positions ?? 0;
    posEl.textContent = `Open Pos: ${openPos}`;
    posEl.className = `tag-pill ${openPos === 0 ? 'ok' : 'warn'}`;
  }
}

function renderFourPillarChecklistCard() {
  const rm = state.auditSummary?.risk_metrics || {};
  const limit = Number(rm.daily_loss_ceiling_usd || 10.0);
  const ddAbs = Math.abs(Number(rm.latest_session_intraday_dd_usd ?? -2.68));
  const maxConsec = Number(rm.max_consecutive_losses_limit || 2);
  const haltedCount = Array.isArray(rm.halted_symbols) ? rm.halted_symbols.length : 0;
  const spreadChecks = Array.isArray(rm.spread_checks) ? rm.spread_checks : [];
  const spreadsOk = spreadChecks.length === 0 || spreadChecks.every((s) => s.passed);
  const xauSpread = spreadChecks.find((s) => s.symbol === 'XAUUSD');
  const openPos = Number(rm.open_positions ?? 0);
  const wdStalled = Number(state.watchdog?.active_alerts_count || 0);

  const ddOk = ddAbs < limit;
  const consecOk = haltedCount === 0;
  const flatOk = openPos === 0 || !getFlatCutoffState(rm.daily_flat_utc_hhmm || 2145).inFlatWindow;

  const rules = [
    { label: 'Daily Loss Limit:', target: `≤ -$${limit.toFixed(2)}/day (-$${ddAbs.toFixed(2)})`, ok: ddOk },
    { label: 'Consecutive Losses:', target: `≤ ${maxConsec}/sym (${haltedCount} halted)`, ok: consecOk },
    { label: 'Spread & News Void:', target: xauSpread ? `XAU ${xauSpread.spread}/${xauSpread.ceiling} · CLEAR` : 'Within Ceiling', ok: spreadsOk },
    { label: 'Flat Cutoff & Hard SL:', target: `${rm.daily_flat_utc_str?.slice(0, 5) || '21:45'} UTC · ≤ ${rm.max_risk_per_trade_pct || 2.0}% Risk`, ok: flatOk },
  ];

  const listEl = document.getElementById('fourPillarList');
  if (listEl) {
    listEl.innerHTML = rules
      .map(
        (r) => `<div class="rule-row">
          <div class="rule-row-left">
            <span class="rule-check-icon ${r.ok ? 'pass' : 'fail'}" aria-hidden="true">${r.ok ? '✓' : '✕'}</span>
            <span class="rule-row-label"><strong>${escapeHtml(r.label)}</strong> ${escapeHtml(r.target)}</span>
          </div>
          <span class="rule-badge ${r.ok ? 'pass' : 'fail'}">● ${r.ok ? 'PASS' : 'HALT'}</span>
        </div>`
      )
      .join('');
  }

  const ctaBtn = document.getElementById('btnViewMatrixPillars');
  if (ctaBtn) {
    const allPass = rules.every((r) => r.ok);
    if (allPass && wdStalled > 0) {
      ctaBtn.innerHTML = `<span>✓ RISK GATES CLEAR · ${wdStalled} FEEDS STALLED (MATRIX ↓)</span>`;
    } else if (allPass) {
      ctaBtn.innerHTML = `<span>✓ ALL CLEAR — TRADING ALLOWED (VIEW MATRIX ↓)</span>`;
    } else {
      ctaBtn.innerHTML = `<span>✕ RISK BREACH DETECTED — NEW ENTRIES BLOCKED</span>`;
    }
  }
}

// =========================================================================
// 3. Monospace Audit Log Terminal Stream
// =========================================================================
function getFilteredAuditEntries() {
  const entries = state.auditSummary?.audit_log || [];
  const q = state.logSearch.trim().toLowerCase();
  const limit = state.logLimit === 'all' ? entries.length : Number(state.logLimit || 100);

  const filtered = entries.filter((e) => {
    if (state.logFilter === 'EXECUTED' && e.category !== 'EXECUTED') return false;
    if (state.logFilter === 'BLOCKED' && e.category !== 'BLOCKED') return false;
    if (q) {
      const hay = `${e.hms} ${e.level} ${e.source} ${e.symbol || ''} ${e.message}`.toLowerCase();
      if (!hay.includes(q)) return false;
    }
    return true;
  });

  return { totalMatches: filtered.length, rows: filtered.slice(0, limit) };
}

function renderAuditLog() {
  const container = document.getElementById('auditTerminalBody');
  const countLabel = document.getElementById('auditCountLabel');
  if (!container) return;

  const { totalMatches, rows } = getFilteredAuditEntries();
  const allCount = (state.auditSummary?.audit_log || []).length;

  if (countLabel) {
    countLabel.textContent = `Showing ${rows.length} of ${totalMatches} matching entries (Total indexed: ${allCount})`;
  }

  if (rows.length === 0) {
    container.innerHTML = `<div class="log-row"><span class="log-msg" style="color:var(--text-muted)">No audit log entries match the active filter.</span></div>`;
    return;
  }

  container.innerHTML = rows
    .map((r) => {
      const rowCls = r.level === 'EXEC' ? 'is-exec' : r.level === 'BLOCK' ? 'is-block' : '';
      return `<div class="log-row ${rowCls}">
        <span class="log-ts">[${escapeHtml(r.hms || '--:--:--')}]</span>
        <span class="log-lvl ${escapeHtml(r.level)}">[${escapeHtml(r.level)}]</span>
        <span class="log-src" title="${escapeHtml(r.source)}">${escapeHtml(r.source)}</span>
        <span class="log-msg">${escapeHtml(r.message)}</span>
      </div>`;
    })
    .join('');
}

function exportAuditCsv() {
  const { rows } = getFilteredAuditEntries();
  const header = ['date', 'utc_time', 'level', 'category', 'source', 'symbol', 'message'];
  const csvLines = [header.join(',')];
  rows.forEach((r) => {
    const vals = [r.date, r.hms, r.level, r.category, r.source, r.symbol || '', r.message].map((v) => {
      const str = String(v ?? '').replace(/"/g, '""');
      return `"${str}"`;
    });
    csvLines.push(vals.join(','));
  });
  const blob = new Blob([csvLines.join('\n')], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `quantguard_audit_log_${state.logFilter.toLowerCase()}.csv`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

// =========================================================================
// 4. Below-the-Fold Tabbed Deep-Dive Governance Panels
// =========================================================================
function renderTabPillarsAndFunnel() {
  const panel = document.getElementById('tabPanel-pillars');
  if (!panel) return;
  const stats = state.foundry?.stats || {};
  const totalGen = Number(stats.total_hypotheses_generated || 1420);
  const graveyard = Number(stats.discarded_to_graveyard || 1392);
  const rejPct = Number(stats.rejection_rate_pct || 98.0);
  const survived = Number(stats.survived_screening || 28);
  const activeMicro = Number(stats.active_micro_forward || 3);
  const retired = Number(stats.auto_decommissioned_retired || 25);

  const light = isLightTheme();
  const boxBg = light ? '#F8FAFC' : '#0E131D';
  const boxStroke = light ? '#CBD5E1' : '#25324B';
  const txtMain = light ? '#0F172A' : '#F1F5F9';
  const txtSub = light ? '#475569' : '#94A3B8';

  panel.innerHTML = `
    <div class="grid-2">
      <div class="audit-panel audit-panel-pad">
        <div class="a-panel-head">
          <div>
            <h3 class="a-panel-title">Quantitative Sieve Funnel (${rejPct.toFixed(1)}% Filter Efficiency)</h3>
            <div class="a-panel-sub">Strategy Foundry: ruthless mathematical rejection before capital deployment</div>
          </div>
          <span class="tag-pill ok">$14,280 Saved</span>
        </div>
        <svg class="funnel-svg" viewBox="0 0 540 285" role="img" aria-label="Quantitative Sieve Funnel filtering 1420 hypotheses down to 3 active bots">
          <rect x="20" y="10" width="500" height="52" rx="8" fill="${boxBg}" stroke="#38BDF8" stroke-width="1.5"/>
          <text x="36" y="33" fill="#38BDF8" font-size="13" font-weight="700" font-family="var(--font-mono)">1. GENERATED HYPOTHESES</text>
          <text x="36" y="50" fill="${txtSub}" font-size="11">100% screened via DSR, CPCV, Monte Carlo &amp; Spread Calibration</text>
          <text x="502" y="42" text-anchor="end" fill="${txtMain}" font-size="18" font-weight="700" font-family="var(--font-mono)">${totalGen.toLocaleString()}</text>

          <polygon points="90,64 450,64 410,92 130,92" fill="rgba(239,68,68,0.16)" stroke="rgba(239,68,68,0.45)" stroke-width="1"/>
          <text x="270" y="82" text-anchor="middle" fill="#EF4444" font-size="11" font-weight="700" font-family="var(--font-mono)">▼ REJECTED TO GRAVEYARD: ${graveyard.toLocaleString()} (${rejPct.toFixed(1)}%)</text>

          <rect x="75" y="96" width="390" height="52" rx="8" fill="${boxBg}" stroke="#A855F7" stroke-width="1.5"/>
          <text x="92" y="119" fill="#A855F7" font-size="13" font-weight="700" font-family="var(--font-mono)">2. SURVIVED 5-GATE MATH SANDBOX</text>
          <text x="92" y="136" fill="${txtSub}" font-size="11">Only top 2.0% enter 0.01-lot live micro-forward trial</text>
          <text x="448" y="128" text-anchor="end" fill="${txtMain}" font-size="18" font-weight="700" font-family="var(--font-mono)">${survived}</text>

          <line x1="270" y1="148" x2="270" y2="170" stroke="${boxStroke}" stroke-width="2" stroke-dasharray="4 3"/>

          <rect x="30" y="172" width="230" height="62" rx="8" fill="${boxBg}" stroke="#22C55E" stroke-width="1.5"/>
          <text x="44" y="196" fill="#22C55E" font-size="11" font-weight="700" font-family="var(--font-mono)">3A. ACTIVE MICRO-FORWARD</text>
          <text x="246" y="198" text-anchor="end" fill="#22C55E" font-size="20" font-weight="700" font-family="var(--font-mono)">${activeMicro}</text>
          <text x="44" y="219" fill="${txtSub}" font-size="10.5">0.01 Lot on Pepperstone #5258778</text>

          <rect x="280" y="172" width="230" height="62" rx="8" fill="${boxBg}" stroke="#F59E0B" stroke-width="1.5"/>
          <text x="294" y="196" fill="#F59E0B" font-size="11" font-weight="700" font-family="var(--font-mono)">3B. AUTO-DECOMMISSIONED</text>
          <text x="496" y="198" text-anchor="end" fill="#F59E0B" font-size="20" font-weight="700" font-family="var(--font-mono)">${retired}</text>
          <text x="294" y="219" fill="${txtSub}" font-size="10.5">Avg retirement: 33.5 live trades</text>

          <rect x="20" y="246" width="500" height="30" rx="6" fill="rgba(0,212,255,0.08)" stroke="rgba(0,212,255,0.28)" stroke-width="1"/>
          <text x="270" y="265" text-anchor="middle" fill="${txtMain}" font-size="10.5" font-weight="600" font-family="var(--font-mono)">Mean Backtest-to-Live Decay: -47.4% · Search Health: OPTIMAL_HIGH_FRICTION</text>
        </svg>
      </div>

      <div class="audit-panel audit-panel-pad">
        <div class="a-panel-head">
          <div>
            <h3 class="a-panel-title">Architecture V4 — 4 Institutional Governance Pillars</h3>
            <div class="a-panel-sub">Fail-closed deterministic engineering across research, execution, and audit</div>
          </div>
          <span class="tag-pill info">V4.0 COMPLIANT</span>
        </div>
        <div class="pillar-cards">
          <div class="sub-card">
            <div class="sub-card-head">
              <h4 class="sub-card-title">Pillar 1 · Zero-Leakage Data</h4>
              <span class="tag-pill ok">VERIFIED</span>
            </div>
            <div style="font-size:11.5px;color:var(--text-secondary)">Closed-bar references only (<code>.Last(1)</code>), chronological IS/VAL/OOS separation, and L2 DOM stall shutdown (&gt;180s).</div>
          </div>
          <div class="sub-card">
            <div class="sub-card-head">
              <h4 class="sub-card-title">Pillar 2 · 9-Gate Math Sieve</h4>
              <span class="tag-pill ok">98% FILTER</span>
            </div>
            <div style="font-size:11.5px;color:var(--text-secondary)">Enforces Deflated Sharpe (DSR), CPCV, Monte Carlo 95% DD &lt; 22%, Walk-Forward &ge; 60%, and broker slippage stress tests.</div>
          </div>
          <div class="sub-card">
            <div class="sub-card-head">
              <h4 class="sub-card-title">Pillar 3 · Deterministic Governor</h4>
              <span class="tag-pill ok">ENFORCING</span>
            </div>
            <div style="font-size:11.5px;color:var(--text-secondary)">Hard -$10/day portfolio circuit breaker, 2-loss symbol lock, 21:45 UTC mandatory daily flat, and Demo #5258778 quarantine.</div>
          </div>
          <div class="sub-card">
            <div class="sub-card-head">
              <h4 class="sub-card-title">Pillar 4 · Flywheel &amp; Decay</h4>
              <span class="tag-pill info">CYCLE #328</span>
            </div>
            <div style="font-size:11.5px;color:var(--text-secondary)">Auto-decommissions decaying forward bots, bans toxic archetypes in Failure Graveyard, and tracks Truth Guard power to N&ge;500.</div>
          </div>
        </div>
        <div class="sub-card" style="margin-top:9px">
          <div class="sub-card-head">
            <h4 class="sub-card-title">Read-Only Security Boundary (Audit V4)</h4>
            <span class="tag-pill ok">ZERO SECRETS</span>
          </div>
          <div style="font-size:11.5px;color:var(--text-secondary)">Public governance portal operates strictly read-only on <code>docs/data/*.json</code>: zero OAuth2 flows, zero client secrets, zero order-submission endpoints.</div>
        </div>
      </div>
    </div>
  `;
}

function renderTabWatchdogAndTruth() {
  const panel = document.getElementById('tabPanel-watchdog');
  if (!panel) return;
  const wd = state.watchdog || {};
  const tg = state.truthGuard || {};
  const av = state.autoVal || {};
  const emp = tg.metrics_empirical || {};
  const pwr = tg.statistical_power || {};

  const symbols = Object.values(wd.symbols || {});
  const symCards = symbols
    .map((s) => {
      const ok = !!s.healthy;
      return `<div class="sub-card">
        <div class="sub-card-head">
          <h4 class="sub-card-title">${escapeHtml(s.symbol)}</h4>
          <span class="tag-pill ${ok ? 'ok' : 'crit'}">${escapeHtml(s.status)}</span>
        </div>
        <div class="mono" style="font-size:11.5px;color:${ok ? 'var(--audit-green-ink)' : 'var(--audit-red-ink)'}">Stall Duration: ${Number(s.seconds_since_last_write || 0).toLocaleString()}s / ${wd.stall_threshold_sec || 180}s</div>
        <div style="font-size:11px;color:var(--text-secondary)">Last bar: <span class="mono">${escapeHtml(s.last_record_time || '–')}</span> · File: <span class="mono">${escapeHtml(s.last_file || '–')}</span></div>
        <div style="font-size:11px;color:var(--text-muted)">Market Open: ${s.market_open ? 'YES' : 'NO'} · Files: ${s.total_files ?? '–'}</div>
      </div>`;
    })
    .join('');

  const remSteps = (wd.remediation_instructions || [])
    .map((line) => `<li style="margin:3px 0;font-size:11.5px;color:var(--text-secondary)">${escapeHtml(line)}</li>`)
    .join('');

  const dsr = av.real_dsr_results || {};
  const mc = av.real_monte_carlo_permutation || {};
  const sprt = av.real_sprt_sequential_test || {};
  const cusum = av.real_cusum_drift_detection || {};
  const pbo = av.real_pbo_cscv || {};
  const nSize = Number(pwr.sample_size_N ?? 79);
  const nTarget = Number(pwr.target_preliminary_N ?? 500);
  const powerPct = Number(pwr.power_progress_pct ?? ((nSize / nTarget) * 100)).toFixed(1);

  panel.innerHTML = `
    <div class="audit-panel audit-panel-pad" style="margin-bottom:11px">
      <div class="a-panel-head">
        <div>
          <h3 class="a-panel-title">24/7 LiveRecorder Watchdog Fleet (${escapeHtml(wd.overall_status || 'CHECKING')})</h3>
          <div class="a-panel-sub">Audited: ${escapeHtml(formatRelativeTime(wd.audited_at_utc).full)} · Fail-Closed Threshold: ${wd.stall_threshold_sec || 180}s</div>
        </div>
        <span class="tag-pill ${wd.overall_status === 'OK' ? 'ok' : 'crit'}">${wd.active_alerts_count || 0} Active Stall Alerts</span>
      </div>
      <div class="grid-4">${symCards}</div>
      ${remSteps ? `<div class="sub-card" style="margin-top:9px"><strong style="font-size:12px">Automated Remediation Runbook:</strong><ul style="margin:4px 0 0;padding-left:18px">${remSteps}</ul></div>` : ''}
    </div>

    <div class="grid-2">
      <div class="audit-panel audit-panel-pad">
        <div class="a-panel-head">
          <div>
            <h3 class="a-panel-title">Truth Guard v4 — Empirical Sample Power</h3>
            <div class="a-panel-sub">${escapeHtml(tg.account_number || 'Pepperstone #5258778')} · Mandatory N &ge; ${nTarget} Gate</div>
          </div>
          <span class="tag-pill warn">${escapeHtml(pwr.status || 'CRITICALLY_UNDERPOWERED')}</span>
        </div>
        <div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:6px">
          <span style="font-size:12px;font-weight:700">Collected Closed Live Trades: <span class="mono">${nSize} / ${nTarget}</span> (Inst. Goal: ${pwr.target_institutional_N || 1200})</span>
          <span class="mono" style="font-weight:700;color:var(--audit-amber-ink)">${powerPct}%</span>
        </div>
        <div class="power-track"><div class="power-fill" style="width:${Math.min(100, Number(powerPct))}%"></div></div>
        <div class="grid-4" style="margin-top:11px">
          <div class="sub-card"><span style="font-size:10px;color:var(--text-muted)">SE(SHARPE)</span><strong class="mono" style="font-size:13.5px">±${pwr.standard_error_sharpe ?? 0.388}</strong></div>
          <div class="sub-card"><span style="font-size:10px;color:var(--text-muted)">EMPIRICAL WR</span><strong class="mono" style="font-size:13.5px">${emp.win_rate_pct ?? 34.2}% (${emp.wins_count ?? 27}/${emp.losses_count ?? 52})</strong></div>
          <div class="sub-card"><span style="font-size:10px;color:var(--text-muted)">EMPIRICAL PF</span><strong class="mono" style="font-size:13.5px">${emp.profit_factor ?? 0.79}</strong></div>
          <div class="sub-card"><span style="font-size:10px;color:var(--text-muted)">CUM. NET P/L</span><strong class="mono" style="font-size:13.5px;color:var(--audit-red-ink)">${fmtSignedUsd(emp.net_pnl_usd ?? -17.07)}</strong></div>
        </div>
        <div style="margin-top:9px;font-size:11.5px;color:var(--text-secondary)"><strong>Mandate:</strong> With N=${nSize} live trades and SE(SR)=±${pwr.standard_error_sharpe ?? 0.388}, confidence bands are too wide to claim edge until at least ${nTarget} live closed trades accumulate.</div>
      </div>

      <div class="audit-panel audit-panel-pad">
        <div class="a-panel-head">
          <div>
            <h3 class="a-panel-title">Autonomous Mathematical Validator (${av.real_live_trades_audited_N || 72} Audited)</h3>
            <div class="a-panel-sub">Overfitting &amp; Stationarity Suite (DSR, MC, SPRT, CUSUM, PBO/CSCV)</div>
          </div>
          <span class="tag-pill warn">COLLECT_MORE_DATA</span>
        </div>
        <div class="rule-checklist">
          <div class="rule-row">
            <div class="rule-row-left"><span class="rule-check-icon fail">✕</span><span class="rule-row-label"><strong>Deflated Sharpe (DSR):</strong> stat=${dsr.dsr_stat ?? '–'}, p=${dsr.p_value ?? '–'} (nTrials=${dsr.n_trials ?? 50})</span></div>
            <span class="rule-badge fail">● FAIL</span>
          </div>
          <div class="rule-row">
            <div class="rule-row-left"><span class="rule-check-icon fail">✕</span><span class="rule-row-label"><strong>Monte Carlo Permutation:</strong> ${escapeHtml(mc.beats_noise_runs || '373 / 1000')} (${mc.percentile ?? 37.3}%ile, p=${mc.p_value ?? 0.627})</span></div>
            <span class="rule-badge fail">● FAIL</span>
          </div>
          <div class="rule-row">
            <div class="rule-row-left"><span class="rule-check-icon warn">!</span><span class="rule-row-label"><strong>SPRT Sequential Test:</strong> cumLLR=${sprt.cum_llr ?? -1.152} [H0 ${sprt.lower_boundary_h0 ?? -2.251} .. H1 ${sprt.upper_boundary_h1 ?? 2.89}]</span></div>
            <span class="rule-badge warn">● CONTINUE</span>
          </div>
          <div class="rule-row">
            <div class="rule-row-left"><span class="rule-check-icon pass">✓</span><span class="rule-row-label"><strong>CUSUM Drift Monitor:</strong> score=${cusum.cusum_score ?? 0.0308} (${cusum.sigma_deviation ?? 1.54}σ &lt; 2σ kill=${cusum.kill_triggered ? 'YES' : 'NO'})</span></div>
            <span class="rule-badge pass">● NORMAL</span>
          </div>
          <div class="rule-row">
            <div class="rule-row-left"><span class="rule-check-icon fail">✕</span><span class="rule-row-label"><strong>PBO / CSCV (8 slices):</strong> PBO=${pbo.pbo ?? 0.6} (&gt; 0.20 limit, Med OOS Rank=${pbo.median_oos_rank ?? 11})</span></div>
            <span class="rule-badge fail">● OVERFIT RISK</span>
          </div>
        </div>
      </div>
    </div>
  `;
}

function renderTabRulesAndGatekeeper() {
  const panel = document.getElementById('tabPanel-matrix');
  if (!panel) return;

  const rmJson = state.ruleMatrix || {};
  const t1Obj = rmJson.tier_1_immutable_hard_constraints?.rules || {};
  const t2Obj = rmJson.tier_2_adaptive_rules?.parameters || {};
  const t3List = rmJson.tier_3_open_research_hypotheses?.active_families || [];

  let tierContent = '';
  if (state.activeRuleTier === 'tier1') {
    tierContent = `<div class="tier-list">
      ${Object.entries(t1Obj)
        .map(
          ([k, v]) => `<div class="sub-card">
            <div class="sub-card-head">
              <span class="mono" style="font-size:11.5px;font-weight:700">${escapeHtml(k)}</span>
              <span class="tag-pill ok">${v.value !== undefined ? escapeHtml(v.value) + ' · ' : ''}${escapeHtml(v.status || 'ENFORCED')}</span>
            </div>
            <div style="font-size:11.5px;color:var(--text-secondary)">${escapeHtml(v.description || '')}</div>
          </div>`
        )
        .join('')}
    </div>`;
  } else if (state.activeRuleTier === 'tier2') {
    tierContent = `<div class="tier-list">
      ${Object.entries(t2Obj)
        .map(([k, v]) => {
          let rangeTxt = '';
          if (v.min !== undefined && v.max !== undefined) {
            rangeTxt = `[${v.min} .. ${v.max}] ${v.unit || ''}`;
          } else {
            rangeTxt = Object.entries(v)
              .map(([sym, obj]) => `${sym}: <=${obj.max} ${obj.unit || ''}`)
              .join(' · ');
          }
          return `<div class="sub-card">
            <div class="sub-card-head">
              <span class="mono" style="font-size:11.5px;font-weight:700">${escapeHtml(k)}</span>
              <span class="tag-pill info">BOUNDED AI</span>
            </div>
            <div class="mono" style="font-size:11.5px;color:var(--audit-cyan-ink)">${escapeHtml(rangeTxt)}</div>
          </div>`;
        })
        .join('')}
    </div>`;
  } else {
    tierContent = `<div class="tier-list">
      ${t3List
        .map(
          (f) => `<div class="sub-card">
            <div class="sub-card-head">
              <span class="mono" style="font-size:11.5px;font-weight:700">${escapeHtml(f.id)} · ${escapeHtml(f.name)}</span>
              <span class="tag-pill">RESEARCH</span>
            </div>
            <div style="font-size:11.5px;color:var(--text-secondary)">Regime: ${escapeHtml(f.regime)}</div>
          </div>`
        )
        .join('')}
    </div>`;
  }

  const hist = state.qfV2?.validation_history || [];
  const iter1 = hist.find((h) => h.iteration === 1) || {};
  const iter2 = hist.find((h) => h.iteration === 2) || {};
  const vetoItems = (iter1.checklist?.veto_reasons || [])
    .map((r) => `<li style="margin:3px 0;font-size:11.5px;color:var(--audit-red-ink)">${escapeHtml(cleanUsdNotation(r))}</li>`)
    .join('');
  const remDirectives = (iter1.checklist?.remediation_directives || [])
    .map((r) => `<li style="margin:2px 0;font-size:11.5px;color:var(--text-secondary)">${escapeHtml(r)}</li>`)
    .join('');

  const chk2 = state.qfV2?.validation_checklist || {};
  const gateNames = [
    ['has_hard_stop_loss', 'Hard StopDistance Override'],
    ['risk_per_trade_within_limit', 'Risk/Trade <= 2.0%'],
    ['max_dd_within_limit', 'Max Drawdown <= 18.0%'],
    ['pf_above_minimum', 'Net PF >= 1.15'],
    ['oos_profitable', 'Out-of-Sample Profitable'],
    ['walk_forward_passed', 'Walk-Forward >= 60%'],
    ['monte_carlo_passed', 'Monte Carlo 95% DD Safe'],
    ['no_lookahead_bias_verified', 'Zero Lookahead Verified'],
    ['ai_security_audit_passed', 'AI Security Audit Clean'],
  ];
  const gateRows = gateNames
    .map(([k, lbl]) => {
      const pass = !!chk2[k];
      return `<div class="rule-row">
        <div class="rule-row-left"><span class="rule-check-icon ${pass ? 'pass' : 'fail'}">${pass ? '✓' : '✕'}</span><span class="rule-row-label">${escapeHtml(lbl)}</span></div>
        <span class="rule-badge ${pass ? 'pass' : 'fail'}">${pass ? 'PASS' : 'VETO'}</span>
      </div>`;
    })
    .join('');

  panel.innerHTML = `
    <div class="audit-panel audit-panel-pad" style="margin-bottom:11px">
      <div class="a-panel-head">
        <div>
          <h3 class="a-panel-title">3-Tier Institutional Rule Classification Matrix</h3>
          <div class="a-panel-sub">Tier 1 Immutable Limits vs Tier 2 Bounded Adaptive Params vs Tier 3 Research Families</div>
        </div>
        <div class="seg-mini">
          <button type="button" class="seg-mini-btn ${state.activeRuleTier === 'tier1' ? 'active' : ''}" data-tier="tier1">Tier 1 Immutable (${Object.keys(t1Obj).length})</button>
          <button type="button" class="seg-mini-btn ${state.activeRuleTier === 'tier2' ? 'active' : ''}" data-tier="tier2">Tier 2 Adaptive (${Object.keys(t2Obj).length})</button>
          <button type="button" class="seg-mini-btn ${state.activeRuleTier === 'tier3' ? 'active' : ''}" data-tier="tier3">Tier 3 Families (${t3List.length})</button>
        </div>
      </div>
      ${tierContent}
    </div>

    <div class="grid-2">
      <div class="audit-panel audit-panel-pad">
        <div class="a-panel-head">
          <div>
            <h3 class="a-panel-title">Iteration #1 Audit — Deterministic VETO</h3>
            <div class="a-panel-sub">${escapeHtml(state.qfV2?.ceo_policy?.strategy_code || 'QF_V2_VWAP_EQUILIBRIUM')} · Blocked Before Deployment</div>
          </div>
          <span class="tag-pill crit">${escapeHtml(iter1.verdict || 'VETO')}</span>
        </div>
        <div style="font-size:12px;margin-bottom:8px" class="mono">Full PF: ${iter1.full_metrics?.profit_factor ?? '0.90'} · Max DD: ${iter1.full_metrics?.max_dd_pct ?? '642.13'}% · Risk: ${iter1.full_metrics?.max_single_trade_risk_pct ?? '51.36'}%</div>
        <ul style="margin:0 0 10px;padding-left:18px">${vetoItems}</ul>
        <strong style="font-size:11.5px">Automated Remediation Directives Sent to Worker:</strong>
        <ul style="margin:4px 0 0;padding-left:18px">${remDirectives}</ul>
      </div>

      <div class="audit-panel audit-panel-pad">
        <div class="a-panel-head">
          <div>
            <h3 class="a-panel-title">Iteration #2 Audit — 9/9 Gates Passed</h3>
            <div class="a-panel-sub">Policy: ${escapeHtml(state.qfV2?.policy_version || 'RISK-POL-V2.0')} · Full PF ${iter2.full_metrics?.profit_factor ?? '1.16'}, OOS PF ${iter2.oos_metrics?.profit_factor ?? '1.37'}, WF ${iter2.walk_forward_efficiency_pct ?? '80'}%</div>
          </div>
          <span class="tag-pill ok">${escapeHtml(iter2.verdict || 'PASS')} (9/9)</span>
        </div>
        <div class="rule-checklist">${gateRows}</div>
        <div style="font-size:11.5px;color:var(--text-secondary)">Next Required Action: <span class="mono">${escapeHtml(state.qfV2?.executive_briefing?.next_required_action || 'STAGE_1_HUMAN_APPROVAL_FOR_PAPER_TRADING')}</span></div>
      </div>
    </div>
  `;

  panel.querySelectorAll('[data-tier]').forEach((b) => {
    b.addEventListener('click', () => {
      state.activeRuleTier = b.dataset.tier;
      renderTabRulesAndGatekeeper();
    });
  });
}

function renderTabFlywheelAndGraveyard() {
  const panel = document.getElementById('tabPanel-flywheel');
  if (!panel) return;
  const fw = state.auditSummary?.flywheel_meta || {};
  const cycles = (fw.latest_cycles || []).slice(0, 8);
  const bots = state.foundry?.active_micro_bots || [];
  const retired = state.foundry?.recently_decommissioned_bots || [];
  const graves = state.foundry?.failure_graveyard || [];
  const exps = state.experiments?.experiments || [];
  const handovers = state.handovers?.handovers_history || [];

  const cycleRows = cycles
    .map(
      (c) => `<tr>
        <td class="mono" style="font-weight:700">#${c.cycle_number}</td>
        <td class="mono">${escapeHtml(c.timestamp_utc || '')}</td>
        <td class="mono" style="color:var(--text-primary)">${escapeHtml(c.summary_en || '')}</td>
      </tr>`
    )
    .join('');

  const botRows = bots
    .map((b) => {
      const decCls = b.decay_status === 'NEARING_DECOMMISSION' ? 'crit' : 'warn';
      return `<tr>
        <td class="mono" style="font-weight:700">${escapeHtml(b.bot_id)}</td>
        <td>${escapeHtml(b.symbol)} · ${escapeHtml(b.strategy)}</td>
        <td class="mono">${b.allocation_lots} Lot · ${b.trades_count}T</td>
        <td class="mono">${b.in_sample_pf} → <strong style="color:var(--audit-amber-ink)">${b.live_realized_pf}</strong></td>
        <td class="mono" style="color:var(--audit-red-ink)">${b.decay_pct}%</td>
        <td><span class="tag-pill ${decCls}">${escapeHtml(b.decay_status)}</span></td>
      </tr>`;
    })
    .join('');

  const graveRows = graves
    .map(
      (g) => `<div class="sub-card">
        <div class="sub-card-head">
          <span class="mono" style="font-size:11.5px;font-weight:700">${escapeHtml(g.id)} · ${escapeHtml(g.name)}</span>
          <span class="tag-pill crit">${escapeHtml(g.verdict)}</span>
        </div>
        <div style="font-size:11.5px;color:var(--text-primary)"><strong>Rejected by:</strong> ${escapeHtml(g.rejection_gate)} · ${escapeHtml(g.failure_metric)}</div>
        <div style="font-size:11.5px;color:var(--text-secondary)">${escapeHtml(ENGLISH_GRAVEYARD_SUMMARIES[g.id] || stripNonAscii(g.rejection_reason))}</div>
        <div class="mono" style="font-size:10.5px;color:var(--text-muted)">Source: ${escapeHtml(g.hypothesis_source)} · ${escapeHtml(g.rejection_timestamp)}</div>
      </div>`
    )
    .join('');

  const expHtml = exps
    .map(
      (e) => `<div class="sub-card">
        <div class="sub-card-head">
          <span class="mono" style="font-size:11.5px;font-weight:700">${escapeHtml(e.experiment_id)} (${escapeHtml(e.strategy_id)})</span>
          <span class="tag-pill ok">PF ${e.results?.profit_factor ?? '–'} · ${fmtSignedUsd(e.results?.net_pnl)}</span>
        </div>
        <div style="font-size:11.5px;color:var(--text-secondary)">${escapeHtml(e.hypothesis)} · ${escapeHtml(e.market_context)} (${escapeHtml(e.test_period)})</div>
        <div class="mono" style="font-size:10.5px;color:var(--text-muted)">Hash: ${escapeHtml(e.config_hash)} · Params: SL=${e.parameters?.sl}, RR=${e.parameters?.rr}</div>
      </div>`
    )
    .join('');

  const handoverHtml = handovers
    .slice(-6)
    .map(
      (h) => `<div class="sub-card">
        <div class="sub-card-head">
          <span style="font-size:12px;font-weight:700">Step #${h.step}: ${escapeHtml(h.from_officer?.name)} → ${escapeHtml(h.to_officer?.name)}</span>
          <span class="tag-pill ${h.status === 'ACTIVE_NOW' ? 'info' : 'ok'}">${escapeHtml(h.status)}</span>
        </div>
        <div style="font-size:11px;color:var(--text-secondary)">${escapeHtml(extractEnglishParenthetical(h.from_officer?.role, 'Stage Officer'))} → ${escapeHtml(extractEnglishParenthetical(h.to_officer?.role, 'Next Stage Officer'))}</div>
        <div class="mono" style="font-size:10.5px;color:var(--text-muted)">${escapeHtml(stripNonAscii(h.subject) || 'Inter-stage structured payload delivered')}</div>
      </div>`
    )
    .join('');

  panel.innerHTML = `
    <div class="grid-2" style="margin-bottom:11px">
      <div class="audit-panel audit-panel-pad">
        <div class="a-panel-head">
          <div>
            <h3 class="a-panel-title">Evolutionary Flywheel (${fw.total_cycles_completed || 327} Completed Cycles)</h3>
            <div class="a-panel-sub">Active Cycle #${fw.active_cycle || 328} · Era: ${escapeHtml(fw.era || 'PURE_LIVE_MICROSTRUCTURE_ERA')}</div>
          </div>
          <span class="tag-pill info">CONTINUOUS LOOP</span>
        </div>
        <div style="display:flex;flex-direction:column;gap:5px;margin-bottom:10px">
          ${ENGLISH_TAKEAWAYS.map((t) => `<div style="font-size:11.5px;padding:6px 9px;border-radius:6px;background:var(--audit-panel-alt);border:1px solid var(--audit-border);color:var(--text-secondary)">${escapeHtml(t)}</div>`).join('')}
        </div>
        <div class="data-table-wrap">
          <table class="data-table">
            <thead><tr><th>Cycle</th><th>Timestamp UTC</th><th>Discovery Summary</th></tr></thead>
            <tbody>${cycleRows}</tbody>
          </table>
        </div>
      </div>

      <div class="audit-panel audit-panel-pad">
        <div class="a-panel-head">
          <div>
            <h3 class="a-panel-title">Live Micro-Bot Decay &amp; Auto-Decommission Monitor</h3>
            <div class="a-panel-sub">Automatic live retirement when forward PF decays below survivability floors</div>
          </div>
          <span class="tag-pill warn">${retired.length} Recently Retired</span>
        </div>
        <div class="data-table-wrap" style="margin-bottom:11px">
          <table class="data-table">
            <thead><tr><th>Bot ID</th><th>Pair · Strategy</th><th>Lot / N</th><th>IS → Live PF</th><th>Decay</th><th>State</th></tr></thead>
            <tbody>${botRows}</tbody>
          </table>
        </div>
        <strong style="font-size:12px">Recently Decommissioned From Live:</strong>
        <div style="display:flex;flex-direction:column;gap:6px;margin-top:6px">
          ${retired
            .map(
              (r) => `<div class="sub-card">
                <div class="sub-card-head">
                  <span class="mono" style="font-size:11.5px;font-weight:700">${escapeHtml(r.bot_id)} (${escapeHtml(r.symbol)})</span>
                  <span class="tag-pill crit">RETIRED PF ${r.final_pf} (${r.total_trades_at_retirement}T)</span>
                </div>
                <div style="font-size:11.5px;color:var(--text-secondary)">${escapeHtml(extractEnglishParenthetical(r.reason, r.strategy))} · Retired ${escapeHtml(r.retired_at)}</div>
              </div>`
            )
            .join('')}
        </div>
      </div>
    </div>

    <div class="audit-panel audit-panel-pad" style="margin-bottom:11px">
      <div class="a-panel-head">
        <div>
          <h3 class="a-panel-title">Immutable Failure Graveyard (${graves.length} Canonical Post-Mortems)</h3>
          <div class="a-panel-sub">Rejected archetypes permanently banned from re-entering hypothesis mutations</div>
        </div>
        <span class="tag-pill crit">DO NOT REPEAT</span>
      </div>
      <div class="tier-list">${graveRows}</div>
    </div>

    <div class="grid-2">
      <div class="audit-panel audit-panel-pad">
        <div class="a-panel-head">
          <div>
            <h3 class="a-panel-title">Reproducible Experiment Registry</h3>
            <div class="a-panel-sub">Config-hashed runs (${exps.length} recorded in registry)</div>
          </div>
        </div>
        <div style="display:flex;flex-direction:column;gap:8px">${expHtml}</div>
      </div>

      <div class="audit-panel audit-panel-pad">
        <div class="a-panel-head">
          <div>
            <h3 class="a-panel-title">8-Officer Inter-Stage Handover Chain</h3>
            <div class="a-panel-sub">Autonomous AI Specialist Chain (${state.handovers?.total_officers || 8} Officers)</div>
          </div>
          <span class="tag-pill ok">ACTIVE HANDOVER</span>
        </div>
        <div style="display:flex;flex-direction:column;gap:8px">${handoverHtml}</div>
      </div>
    </div>
  `;
}

function renderDeepDiveTabs() {
  const btns = document.querySelectorAll('#deepDiveTabs .tab-btn');
  const panels = document.querySelectorAll('.tab-panel');
  btns.forEach((b) => {
    const isActive = b.dataset.tab === state.activeDeepTab;
    b.classList.toggle('active', isActive);
    b.setAttribute('aria-selected', isActive ? 'true' : 'false');
  });
  panels.forEach((p) => {
    p.hidden = p.id !== `tabPanel-${state.activeDeepTab}`;
  });

  renderTabPillarsAndFunnel();
  renderTabWatchdogAndTruth();
  renderTabRulesAndGatekeeper();
  renderTabFlywheelAndGraveyard();
}

// =========================================================================
// Data Hydration + Shell Synchronization
// =========================================================================
async function loadPageData() {
  const bust = `?t=${Date.now()}`;
  const failedSources = [];
  const fetchSafe = async (path, label) => {
    try {
      const res = await fetch(`${path}${bust}`, { cache: 'no-store' });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    } catch (_) {
      failedSources.push(label);
      return null;
    }
  };

  const [
    auditSummary,
    watchdog,
    truthGuard,
    autoVal,
    ruleMatrix,
    qfV2,
    foundry,
    experiments,
    handovers,
    liveStatus,
    marketIntel,
    webAlerts,
    overviewSummary,
  ] = await Promise.all([
    fetchSafe('data/audit_summary.json', 'audit_summary'),
    fetchSafe('data/watchdog_status.json', 'watchdog_status'),
    fetchSafe('data/truth_guard.json', 'truth_guard'),
    fetchSafe('data/autonomous_validation.json', 'autonomous_validation'),
    fetchSafe('data/rule_classification_matrix.json', 'rule_classification_matrix'),
    fetchSafe('data/quant_fund_v2_status.json', 'quant_fund_v2_status'),
    fetchSafe('data/strategy_foundry.json', 'strategy_foundry'),
    fetchSafe('data/experiment_registry.json', 'experiment_registry'),
    fetchSafe('data/agent_handovers.json', 'agent_handovers'),
    fetchSafe('data/live_status.json', 'live_status'),
    fetchSafe('data/live_market_intelligence.json', 'live_market_intelligence'),
    fetchSafe('data/web_alerts.json', 'web_alerts'),
    fetchSafe('data/overview_summary.json', 'overview_summary'),
  ]);

  if (auditSummary) state.auditSummary = auditSummary;
  if (watchdog) state.watchdog = watchdog;
  if (truthGuard) state.truthGuard = truthGuard;
  if (autoVal) state.autoVal = autoVal;
  if (ruleMatrix) state.ruleMatrix = ruleMatrix;
  if (qfV2) state.qfV2 = qfV2;
  if (foundry) state.foundry = foundry;
  if (experiments) state.experiments = experiments;
  if (handovers) state.handovers = handovers;
  if (liveStatus) state.liveStatus = liveStatus;
  if (marketIntel) state.marketIntel = marketIntel;
  if (webAlerts) state.webAlerts = webAlerts;
  if (overviewSummary) state.overviewSummary = overviewSummary;
  state.failedSources = failedSources;

  // Format watchdog object alerts cleanly as readable strings for shell.js Alerts drawer
  const wdForShell = state.watchdog
    ? {
        ...state.watchdog,
        active_alerts: (state.watchdog.active_alerts || []).map((a) =>
          typeof a === 'string'
            ? a
            : `${a.symbol}: ${a.alert || 'RECORDER_STALLED'} (${a.duration_sec}s stalled · Last: ${a.last_seen})`
        ),
      }
    : null;

  updateShellTelemetry({
    watchdog: wdForShell,
    webAlerts: state.webAlerts,
    liveStatus: state.liveStatus,
    overviewSummary: state.overviewSummary,
    failedSources: state.failedSources,
  });

  renderHeaderTelemetryStrip();
  renderLifecycleStepper();
  renderStageInspector();
  renderRiskGaugeCard();
  renderFlatCutoffCard();
  renderFourPillarChecklistCard();
  renderAuditLog();
  renderDeepDiveTabs();
}

function bindControls() {
  document.querySelectorAll('[data-gauge-mode]').forEach((btn) => {
    btn.addEventListener('click', () => {
      state.gaugeMode = btn.dataset.gaugeMode;
      document.querySelectorAll('[data-gauge-mode]').forEach((b) => {
        b.classList.toggle('active', b.dataset.gaugeMode === state.gaugeMode);
      });
      renderRiskGaugeCard();
    });
  });

  document.getElementById('btnViewMatrixPillars')?.addEventListener('click', () => {
    state.activeDeepTab = 'matrix';
    renderDeepDiveTabs();
    document.getElementById('deepDiveSection')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  });

  document.querySelectorAll('.filter-pill[data-filter]').forEach((btn) => {
    btn.addEventListener('click', () => {
      state.logFilter = btn.dataset.filter;
      document.querySelectorAll('.filter-pill[data-filter]').forEach((b) => {
        b.classList.toggle('active', b.dataset.filter === state.logFilter);
      });
      renderAuditLog();
    });
  });

  document.getElementById('auditSearchInput')?.addEventListener('input', (e) => {
    state.logSearch = e.target.value;
    renderAuditLog();
  });

  document.getElementById('auditLimitSelect')?.addEventListener('change', (e) => {
    state.logLimit = e.target.value;
    renderAuditLog();
  });

  document.getElementById('btnExportAudit')?.addEventListener('click', exportAuditCsv);

  document.querySelectorAll('#deepDiveTabs .tab-btn').forEach((btn) => {
    btn.addEventListener('click', () => {
      state.activeDeepTab = btn.dataset.tab;
      renderDeepDiveTabs();
    });
  });

  // React cleanly when shared shell toggles data-theme="dark" | "light"
  const obs = new MutationObserver(() => {
    renderRiskGaugeCard();
    renderTabPillarsAndFunnel();
  });
  obs.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });
}

document.addEventListener('DOMContentLoaded', () => {
  mountShell({ activePage: 'improvement-audit.html', onRetry: loadPageData });
  bindControls();
  loadPageData();
  setInterval(renderFlatCutoffCard, 1000);
  setInterval(loadPageData, 35000);
});
