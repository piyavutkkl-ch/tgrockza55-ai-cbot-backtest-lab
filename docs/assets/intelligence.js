/* ==========================================================================
   Antigravity Quant · Page 5: Intelligence Dashboard Controller
   ES Module integrated with shared 8-page shell.js (mountShell/telemetry)
   Pure CSS Grid + Pure Inline SVG — Zero external chart libraries
   ========================================================================== */

import {
  mountShell,
  updateShellTelemetry,
  escapeHtml,
} from './shell.js';

const SVG_NS = 'http://www.w3.org/2000/svg';
const DATA_URLS = {
  summary: 'data/intelligence_summary.json',
  live: 'data/live_status.json',
  watchdog: 'data/watchdog_status.json',
  alerts: 'data/web_alerts.json',
  overview: 'data/overview_summary.json',
};

const state = {
  summary: null,
  liveStatus: null,
  watchdog: null,
  alerts: null,
  overview: null,
  matrixMode: 'champion',
  sortKey: null,
  sortDir: 'desc',
  selectedSymbol: 'XAUUSD',
  heatmapView: 'xauusd_3y',
  activeCellKey: null,
  showLevels: true,
  refreshTimer: null,
};

const $ = (id) => document.getElementById(id);

function svgEl(tag, attrs = {}) {
  const el = document.createElementNS(SVG_NS, tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v !== undefined && v !== null) {
      el.setAttribute(k, String(v));
    }
  }
  return el;
}

function isLightTheme() {
  return document.documentElement.getAttribute('data-theme') === 'light';
}

function fmtNum(val, decimals = 2) {
  if (val === null || val === undefined || Number.isNaN(Number(val))) return '–';
  return Number(val).toLocaleString('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}

function fmtSignedUsd(val) {
  if (val === null || val === undefined || Number.isNaN(Number(val))) return '–';
  const n = Number(val);
  const arrow = n > 0 ? '▲' : n < 0 ? '▼' : '';
  const sign = n > 0 ? '+' : n < 0 ? '-' : '';
  return `${arrow ? arrow + ' ' : ''}${sign}$${Math.abs(n).toFixed(2)}`;
}

function formatUtcShort(isoStr) {
  if (!isoStr) return '–';
  const d = new Date(isoStr);
  if (Number.isNaN(d.getTime())) return String(isoStr);
  return d.toISOString().slice(0, 16).replace('T', ' ') + ' UTC';
}

async function fetchJson(url) {
  const sep = url.includes('?') ? '&' : '?';
  const res = await fetch(`${url}${sep}t=${Date.now()}`, { cache: 'no-store' });
  if (!res.ok) {
    throw new Error(`HTTP ${res.status} loading ${url}`);
  }
  return res.json();
}

/* ========================================================================
   Compact Live Market Ticker Strip (Inline SVG Sparklines)
   ======================================================================== */

function buildSparklineSvg(points, isUp) {
  const w = 52;
  const h = 22;
  const svg = svgEl('svg', {
    viewBox: `0 0 ${w} ${h}`,
    class: 'spark-svg',
    'aria-hidden': 'true',
  });
  if (!points || points.length < 2) return svg;

  const min = Math.min(...points);
  const max = Math.max(...points);
  const span = max - min || 1;
  const coords = points.map((v, i) => {
    const x = (i / (points.length - 1)) * (w - 4) + 2;
    const y = h - 3 - ((v - min) / span) * (h - 6);
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  });

  const light = isLightTheme();
  const color = isUp
    ? (light ? '#15803d' : '#22c55e')
    : (light ? '#dc2626' : '#ef4444');

  svg.appendChild(
    svgEl('polyline', {
      fill: 'none',
      stroke: color,
      'stroke-width': '1.6',
      'stroke-linecap': 'round',
      'stroke-linejoin': 'round',
      points: coords.join(' '),
    })
  );
  return svg;
}

function renderTickers() {
  const container = $('intelTickers');
  if (!container) return;
  const tickers = state.summary?.ticker_strip || [];
  container.innerHTML = '';

  for (const t of tickers) {
    const chip = document.createElement('button');
    chip.type = 'button';
    chip.className = 'ticker-chip';
    chip.title = `${t.symbol} · VWAP $${fmtNum(t.vwap)} · Spread ${t.spread} · Regime: ${t.regime} (คลิกเพื่อดู Heatmap)`;

    const delta = Number(t.delta_vs_vwap_pct || 0);
    const isUp = delta >= 0;
    const arrow = isUp ? '▲' : '▼';
    const sign = isUp ? '+' : '';

    const left = document.createElement('div');
    left.className = 'ticker-chip-left';

    const badge = document.createElement('span');
    badge.className = `ticker-badge tone-${t.tone || 'sky'}`;
    badge.textContent = t.badge || t.symbol.slice(0, 2);

    const info = document.createElement('div');
    info.className = 'ticker-info';
    info.innerHTML = `
      <span class="ticker-sym">${escapeHtml(t.symbol)}</span>
      <div class="ticker-price-row mono">
        <span class="ticker-price">$${fmtNum(t.price)}</span>
        <span class="ticker-delta ${isUp ? 'up' : 'down'}">${arrow} ${sign}${delta.toFixed(2)}%</span>
      </div>
    `;

    left.appendChild(badge);
    left.appendChild(info);
    chip.appendChild(left);
    chip.appendChild(buildSparklineSvg(t.sparkline, isUp));

    chip.addEventListener('click', () => {
      focusSymbolInHeatmap(t.symbol);
    });
    container.appendChild(chip);
  }
}

/* ========================================================================
   Section 1: Performance Matrix (Inline Progress Bars in WR & PF)
   ======================================================================== */

function statusClassName(status) {
  const s = String(status || '').toUpperCase();
  if (s === 'LIVE' || s === 'PROMOTED' || s === 'VALIDATED') return 'is-live';
  if (s === 'DEFENDED') return 'is-defended';
  if (s.includes('DATA') || s.includes('RECORD')) return 'is-data';
  return '';
}

function barTierClass(kind, value) {
  if (kind === 'wr') {
    if (value >= 55) return 'is-good';
    if (value >= 48) return 'is-mid';
    if (value >= 35) return 'is-warn';
    return 'is-bad';
  }
  // Profit Factor
  if (value >= 2.0) return 'is-good';
  if (value >= 1.25) return 'is-mid';
  if (value >= 1.0) return 'is-warn';
  return 'is-bad';
}

function renderMatrix() {
  const tbody = $('matrixBody');
  const subEl = $('matrixSubtitle');
  const modeData = state.summary?.performance_matrix?.[state.matrixMode];
  if (!tbody || !modeData) return;

  if (subEl) {
    subEl.textContent = modeData.subtitle || '';
  }

  // Statistical power callout strictly visible on live_forward mode
  const banner = $('powerBanner');
  if (banner) {
    const sp = state.summary?.meta?.statistical_power;
    const tg = state.summary?.meta?.truth_guard_metrics;
    if (state.matrixMode === 'live_forward' && sp) {
      banner.hidden = false;
      banner.innerHTML = `
        <div>
          <span class="power-tag">${escapeHtml(sp.status || 'UNDERPOWERED')} · N=${escapeHtml(sp.sample_size_N)}/${escapeHtml(sp.target_preliminary_N)}</span>
          <span style="margin-left:8px;">${escapeHtml(sp.description || '')}</span>
        </div>
        <div class="mono" style="font-weight:700;">
          พอร์ตจริง #5258778: Equity $${fmtNum(tg?.current_balance)} (${fmtSignedUsd(tg?.net_pnl_usd)})
        </div>
      `;
    } else {
      banner.hidden = true;
    }
  }

  let rows = [...(modeData.rows || [])];
  if (state.sortKey) {
    const k = state.sortKey;
    const mult = state.sortDir === 'asc' ? 1 : -1;
    rows.sort((a, b) => {
      const va = a[k];
      const vb = b[k];
      if (typeof va === 'string' || typeof vb === 'string') {
        return String(va || '').localeCompare(String(vb || '')) * mult;
      }
      return ((Number(va) || 0) - (Number(vb) || 0)) * mult;
    });
  }

  // Update header sort indicators
  document.querySelectorAll('.sort-btn').forEach((btn) => {
    const ind = btn.querySelector('.sort-ind');
    const isCur = btn.dataset.sort === state.sortKey;
    btn.classList.toggle('is-sorted', isCur);
    if (ind) {
      ind.textContent = isCur ? (state.sortDir === 'asc' ? '▲' : '▼') : '';
    }
  });

  if (rows.length === 0) {
    tbody.innerHTML = '<tr><td colspan="8" class="empty-cell">ไม่พบข้อมูลในโหมดนี้</td></tr>';
    return;
  }

  tbody.innerHTML = '';
  for (const r of rows) {
    const tr = document.createElement('tr');
    tr.className = 'matrix-row';
    tr.tabIndex = 0;
    if (r.symbol === state.selectedSymbol) {
      tr.classList.add('is-selected');
    }
    tr.setAttribute('aria-label', `${r.display_name} (${r.symbol}) คลิกเพื่อดู Heatmap`);

    const wr = Number(r.win_rate_pct || 0);
    const wrWidth = Math.max(0, Math.min(100, wr));
    const pf = Number(r.profit_factor || 0);
    const pfWidth = Math.max(0, Math.min(100, (pf / 4.0) * 100));
    const sharpe = r.sharpe !== null && r.sharpe !== undefined ? Number(r.sharpe) : null;
    const ddUsd = Number(r.max_dd_usd || 0);
    const expUsd = Number(r.expectancy_usd || 0);
    const trades = Number(r.trades || 0);
    const dailyWrNote =
      r.daily_win_rate_pct !== null && r.daily_win_rate_pct !== undefined
        ? `${Number(r.daily_win_rate_pct).toFixed(0)}% daily WR`
        : (r.net_pnl_usd !== undefined ? `Net ${fmtSignedUsd(r.net_pnl_usd)}` : '');

    tr.innerHTML = `
      <td>
        <div class="market-cell">
          <span class="asset-badge tone-${escapeHtml(r.tone || 'sky')}">${escapeHtml(r.badge || r.symbol.slice(0, 2))}</span>
          <div class="market-meta">
            <div class="market-name-row">
              <span class="market-name">${escapeHtml(r.display_name)}</span>
              <span class="status-chip ${statusClassName(r.status)}">${escapeHtml(r.status || '–')}</span>
            </div>
            <div class="strategy-sub" title="${escapeHtml(r.strategy_label)}">${escapeHtml(r.symbol)} · ${escapeHtml(r.strategy_type)}</div>
          </div>
        </div>
      </td>
      <td>
        <div class="tf-main">${escapeHtml(r.timeframe || 'M1')}</div>
        <div class="tf-sub">${escapeHtml(r.session_filter || 'ALL')}</div>
      </td>
      <td>
        <div class="inline-bar-cell">
          <span class="inline-bar-val mono">${trades > 0 ? wr.toFixed(1) + '%' : '–'}</span>
          <div class="inline-track" title="Win Rate ${wr.toFixed(1)}% (เส้นขีด 50%)">
            <div class="inline-fill ${barTierClass('wr', wr)}" style="width:${trades > 0 ? wrWidth.toFixed(1) : 0}%"></div>
            <span class="inline-ref-tick" style="left:50%" title="50% threshold"></span>
          </div>
        </div>
      </td>
      <td>
        <div class="inline-bar-cell">
          <span class="inline-bar-val mono">${trades > 0 ? pf.toFixed(2) : '–'}</span>
          <div class="inline-track" title="Profit Factor ${pf.toFixed(2)} (เส้นขีด 1.0x จุดคุ้มทุน / เต็มแถบ ≥ 4.0)">
            <div class="inline-fill ${barTierClass('pf', pf)}" style="width:${trades > 0 ? pfWidth.toFixed(1) : 0}%"></div>
            <span class="inline-ref-tick" style="left:25%" title="1.0x breakeven"></span>
          </div>
        </div>
      </td>
      <td class="num-col mono ${sharpe !== null && sharpe >= 1 ? 'val-pos' : sharpe !== null && sharpe < 0 ? 'val-neg' : 'val-neutral'}">
        ${sharpe !== null ? sharpe.toFixed(2) : '–'}
      </td>
      <td class="num-col mono val-neg">
        ${trades > 0 ? `-$${ddUsd.toFixed(2)}` : '–'}
      </td>
      <td class="num-col mono ${expUsd > 0 ? 'val-pos' : expUsd < 0 ? 'val-neg' : 'val-neutral'}">
        ${trades > 0 ? fmtSignedUsd(expUsd) : '–'}
      </td>
      <td class="num-col">
        <div class="trades-cell">
          <span class="mono" style="font-weight:700;">${trades.toLocaleString('en-US')}</span>
          ${dailyWrNote ? `<span class="trades-daily">${escapeHtml(dailyWrNote)}</span>` : ''}
        </div>
      </td>
    `;

    const selectRow = () => {
      state.selectedSymbol = r.symbol;
      renderMatrix();
      focusSymbolInHeatmap(r.symbol);
    };
    tr.addEventListener('click', selectRow);
    tr.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        selectRow();
      }
    });
    tbody.appendChild(tr);
  }
}

function focusSymbolInHeatmap(sym) {
  state.selectedSymbol = sym;
  const views = state.summary?.day_session_heatmap?.views || {};
  if (sym === 'XAUUSD') {
    if (state.heatmapView !== 'XAUUSD' && state.heatmapView !== 'xauusd_3y') {
      state.heatmapView = 'xauusd_3y';
    }
  } else if (views[sym]) {
    state.heatmapView = sym;
  }
  state.activeCellKey = null;
  syncHeatmapPills();
  renderHeatmap();
}

/* ========================================================================
   Section 2: Day & Session Intelligence Heatmap (Pure 2D CSS Grid)
   ======================================================================== */

function syncHeatmapPills() {
  document.querySelectorAll('#heatmapViewPills .view-pill').forEach((btn) => {
    btn.classList.toggle('active', btn.dataset.view === state.heatmapView);
  });
}

function updateCellInspector(cell, sessionObj, weekdayObj, is3y) {
  const badge = $('inspBadge');
  const title = $('inspTitle');
  const reason = $('inspReason');
  const stats = $('inspStats');
  if (!badge || !title || !reason || !stats || !cell) return;

  badge.className = 'inspector-badge ' + (
    cell.is_no_trade ? 'is-warn' : (cell.edge_tier === 'strong_edge' || cell.edge_tier === 'moderate_edge' ? 'is-good' : '')
  );
  badge.textContent = cell.tier_label || cell.edge_tier;

  title.textContent = `${weekdayObj.key} (${weekdayObj.th}) · ${sessionObj.name} (${sessionObj.hours})`;
  reason.textContent = cell.reason || '–';

  if (is3y) {
    stats.innerHTML = `
      <span class="insp-kv">Exp: <b>${escapeHtml(cell.primary_value)}</b></span>
      <span class="insp-kv">WR: <b>${Number(cell.win_rate_pct).toFixed(1)}%</b></span>
      <span class="insp-kv">PF: <b>${Number(cell.profit_factor).toFixed(2)}</b></span>
      <span class="insp-kv">Z: <b>${Number(cell.z_score) >= 0 ? '+' : ''}${Number(cell.z_score).toFixed(2)}</b></span>
      <span class="insp-kv">n = <b>${escapeHtml(cell.sample_size)}</b> days</span>
    `;
  } else {
    stats.innerHTML = `
      <span class="insp-kv">|DOM Imb|: <b>${escapeHtml(cell.primary_value)}</b></span>
      <span class="insp-kv">Avg Spread: <b>${Number(cell.avg_spread).toFixed(3)}</b></span>
      <span class="insp-kv">Return: <b>${Number(cell.raw_value) >= 0 ? '+' : ''}${Number(cell.raw_value).toFixed(3)}%</b></span>
      <span class="insp-kv">Bars: <b>${escapeHtml(cell.sample_size)}</b> M1</span>
    `;
  }
}

function renderHeatmap() {
  const hm = state.summary?.day_session_heatmap;
  const grid = $('heatmapGrid');
  const sub = $('heatmapSubtitle');
  if (!hm || !grid) return;

  const viewObj = hm.views?.[state.heatmapView] || hm.views?.[hm.default_view];
  if (!viewObj) return;
  const is3y = state.heatmapView === 'xauusd_3y';

  if (sub) {
    sub.textContent = viewObj.subtitle || '';
  }

  const weekdays = hm.weekdays || [];
  const sessions = hm.sessions || [];
  const cells = viewObj.cells || {};

  if (!state.activeCellKey || !cells[state.activeCellKey]) {
    let bestKey = `${sessions[0]?.key || 'ASIA'}_${weekdays[0]?.key || 'MONDAY'}`;
    let bestScore = -9999;
    for (const [k, c] of Object.entries(cells)) {
      const sc = c.is_no_trade ? -100 : Number(c.z_score ?? c.avg_abs_imbalance ?? 0);
      if (sc > bestScore) {
        bestScore = sc;
        bestKey = k;
      }
    }
    state.activeCellKey = bestKey;
  }

  grid.innerHTML = '';

  const corner = document.createElement('div');
  corner.className = 'hm-corner';
  corner.innerHTML = `
    <span>${escapeHtml(viewObj.metric_unit || 'Expectancy')}</span>
    <span style="font-size:9.5px;opacity:0.75;">UTC / TH (UTC+7)</span>
  `;
  grid.appendChild(corner);

  for (const wd of weekdays) {
    const colHead = document.createElement('div');
    colHead.className = 'hm-col-head';
    colHead.setAttribute('role', 'columnheader');
    colHead.innerHTML = `
      <span class="hm-col-en">${escapeHtml(wd.key)}</span>
      <span class="hm-col-th">วัน${escapeHtml(wd.th)}</span>
    `;
    grid.appendChild(colHead);
  }

  for (const sess of sessions) {
    const rHead = document.createElement('div');
    rHead.className = 'hm-row-head';
    rHead.setAttribute('role', 'rowheader');
    rHead.innerHTML = `
      <span class="hm-row-title">${escapeHtml(sess.name)}</span>
      <span class="hm-row-hours">${escapeHtml(sess.hours)}</span>
      <span class="hm-row-th">TH: ${escapeHtml(sess.th)}</span>
    `;
    grid.appendChild(rHead);

    for (const wd of weekdays) {
      const cellKey = `${sess.key}_${wd.key}`;
      const cell = cells[cellKey] || {};
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.setAttribute('role', 'gridcell');
      btn.className = `hm-cell tier-${cell.edge_tier || 'low_edge'}`;
      if (state.activeCellKey === cellKey) {
        btn.classList.add('is-active');
        updateCellInspector(cell, sess, wd, is3y);
      }

      if (cell.is_no_trade) {
        const shortStat = is3y
          ? `${cell.primary_value} · PF ${Number(cell.profit_factor).toFixed(2)}`
          : `${cell.secondary_metric || 'Filter Active'}`;
        btn.innerHTML = `
          <span class="hm-hazard-icon" aria-hidden="true">◆</span>
          <span class="hm-val">No-Trade Zone</span>
          <span class="hm-sub">${escapeHtml(shortStat)}</span>
        `;
      } else {
        const microStat = is3y
          ? `WR ${Number(cell.win_rate_pct).toFixed(0)}% · Z ${Number(cell.z_score) >= 0 ? '+' : ''}${Number(cell.z_score).toFixed(1)}`
          : `${cell.secondary_metric || ''} · ${cell.sample_size || 0}b`;
        btn.innerHTML = `
          <span class="hm-val">${escapeHtml(cell.primary_value || '–')}</span>
          <span class="hm-tier">${escapeHtml(cell.tier_label || '–')}</span>
          <span class="hm-sub">${escapeHtml(microStat)}</span>
        `;
      }

      btn.setAttribute('aria-label', `${wd.key} ${sess.name}: ${cell.tier_label} (${cell.primary_value})`);

      const activate = () => {
        state.activeCellKey = cellKey;
        grid.querySelectorAll('.hm-cell').forEach((el) => el.classList.remove('is-active'));
        btn.classList.add('is-active');
        updateCellInspector(cell, sess, wd, is3y);
      };
      btn.addEventListener('click', activate);
      btn.addEventListener('mouseenter', activate);
      btn.addEventListener('focus', activate);
      grid.appendChild(btn);
    }
  }
}

/* ========================================================================
   Section 3: Microstructure Pattern Cards (Pure Inline Vector SVG)
   ======================================================================== */

function buildMicrostructureSvg(card, ohlcEl) {
  const W = 360;
  const H = 158;
  const padL = 8;
  const padR = 54;
  const padT = 16;
  const padB = 18;
  const plotW = W - padL - padR;
  const plotH = H - padT - padB;

  const diag = card.diagram || {};
  const candles = diag.candles || [];
  const svg = svgEl('svg', {
    viewBox: `0 0 ${W} ${H}`,
    class: `micro-svg${state.showLevels ? '' : ' hide-levels'}`,
    role: 'img',
    'aria-label': `แผนภาพแท่งเทียน ${card.title} ${card.subtitle}`,
  });

  if (candles.length === 0) return svg;

  const light = isLightTheme();
  const cBg = light ? '#eef2f7' : '#070b14';
  const cGrid = light ? 'rgba(15, 23, 42, 0.08)' : 'rgba(148, 163, 184, 0.12)';
  const cGreen = light ? '#15803d' : '#22c55e';
  const cRed = light ? '#dc2626' : '#ef4444';
  const cBear = light ? '#64748b' : '#7c8ba1';
  const cPurple = light ? '#7e22ce' : '#a855f7';
  const cSky = light ? '#0284c7' : '#38bdf8';
  const cText = light ? '#334155' : '#cbd5e1';
  const cPillBg = light ? '#0f172a' : '#162238';
  const cPillBorder = '#334155';

  const priceSamples = [];
  for (const c of candles) {
    priceSamples.push(Number(c.low), Number(c.high));
  }
  if (diag.zone_price) priceSamples.push(Number(diag.zone_price));
  if (diag.entry_price) priceSamples.push(Number(diag.entry_price));
  if (diag.sl_price) priceSamples.push(Number(diag.sl_price));
  if (diag.tp_price) priceSamples.push(Number(diag.tp_price));
  if (diag.ll_price) priceSamples.push(Number(diag.ll_price));

  const rawMin = Math.min(...priceSamples);
  const rawMax = Math.max(...priceSamples);
  const padPrice = (rawMax - rawMin || 1) * 0.13;
  const minP = rawMin - padPrice;
  const maxP = rawMax + padPrice;
  const spanP = maxP - minP || 1;

  const yOf = (price) => padT + ((maxP - price) / spanP) * plotH;
  const step = plotW / candles.length;
  const xCenter = (idx) => padL + step * (idx + 0.5);

  const makeHaloText = (attrs, text) => {
    const el = svgEl('text', {
      ...attrs,
      stroke: cBg,
      'stroke-width': '3',
      'stroke-linejoin': 'round',
      style: 'paint-order: stroke;',
    });
    el.textContent = text;
    return el;
  };

  const fgAnnotations = svgEl('g');
  const fgLevels = svgEl('g', { class: 'level-overlay' });

  // 1. Subtle horizontal gridlines
  for (let i = 0; i <= 3; i += 1) {
    const gy = padT + (plotH * i) / 3;
    svg.appendChild(
      svgEl('line', {
        x1: padL,
        y1: gy.toFixed(1),
        x2: W - padR + 2,
        y2: gy.toFixed(1),
        stroke: cGrid,
        'stroke-width': '1',
        'stroke-dasharray': '2,3',
      })
    );
  }

  // 2. Structure Zone / Trigger Line
  if (diag.zone_price) {
    const zy = yOf(diag.zone_price);
    if (diag.zone_type === 'support') {
      const bandH = Math.min(18, Math.max(8, H - padB - zy + 4));
      svg.appendChild(
        svgEl('rect', {
          x: padL,
          y: (zy - 4).toFixed(1),
          width: plotW,
          height: bandH.toFixed(1),
          fill: light ? 'rgba(21,128,61,0.10)' : 'rgba(34,197,94,0.10)',
          rx: '2',
        })
      );
      svg.appendChild(
        svgEl('line', {
          x1: padL,
          y1: zy.toFixed(1),
          x2: padL + plotW,
          y2: zy.toFixed(1),
          stroke: cGreen,
          'stroke-width': '1.2',
          'stroke-dasharray': '4,3',
          opacity: '0.85',
        })
      );
      fgAnnotations.appendChild(
        makeHaloText(
          {
            x: padL + plotW - 4,
            y: Math.min(H - 5, zy + 11).toFixed(1),
            'text-anchor': 'end',
            fill: cGreen,
            'font-size': '9',
            'font-weight': '700',
          },
          'Support Zone'
        )
      );
    } else if (diag.zone_type === 'resistance') {
      const topY = Math.max(padT - 8, zy - 8);
      svg.appendChild(
        svgEl('rect', {
          x: padL,
          y: topY.toFixed(1),
          width: plotW,
          height: '14',
          fill: light ? 'rgba(220,38,38,0.09)' : 'rgba(239,68,68,0.10)',
          rx: '2',
        })
      );
      svg.appendChild(
        svgEl('line', {
          x1: padL,
          y1: zy.toFixed(1),
          x2: padL + plotW,
          y2: zy.toFixed(1),
          stroke: cRed,
          'stroke-width': '1.2',
          'stroke-dasharray': '4,3',
          opacity: '0.85',
        })
      );
      fgAnnotations.appendChild(
        makeHaloText(
          {
            x: padL + plotW - 4,
            y: Math.max(11, zy - 4).toFixed(1),
            'text-anchor': 'end',
            fill: cRed,
            'font-size': '9',
            'font-weight': '700',
          },
          'Resistance Zone'
        )
      );
    } else if (diag.zone_type === 'choch') {
      const bosI = diag.bos_idx ?? 5;
      const xStart = xCenter(Math.max(0, (diag.ll_idx ?? 3) - 1));
      svg.appendChild(
        svgEl('line', {
          x1: xStart.toFixed(1),
          y1: zy.toFixed(1),
          x2: (padL + plotW).toFixed(1),
          y2: zy.toFixed(1),
          stroke: cPurple,
          'stroke-width': '1.2',
          'stroke-dasharray': '4,3',
        })
      );

      if (candles[0] && diag.ll_idx !== undefined && candles[diag.ll_idx]) {
        svg.appendChild(
          svgEl('line', {
            x1: xCenter(0).toFixed(1),
            y1: yOf(candles[0].high).toFixed(1),
            x2: xCenter(diag.ll_idx).toFixed(1),
            y2: yOf(diag.ll_price ?? candles[diag.ll_idx].low).toFixed(1),
            stroke: cText,
            'stroke-width': '1',
            'stroke-dasharray': '2,3',
            opacity: '0.45',
          })
        );
        fgAnnotations.appendChild(
          makeHaloText(
            {
              x: xCenter(diag.ll_idx).toFixed(1),
              y: Math.min(H - 4, yOf(diag.ll_price ?? candles[diag.ll_idx].low) + 11).toFixed(1),
              'text-anchor': 'middle',
              fill: cText,
              'font-size': '8.5',
              'font-weight': '700',
            },
            'Lower Low (LL)'
          )
        );
      }

      fgAnnotations.appendChild(
        makeHaloText(
          {
            x: xCenter(bosI).toFixed(1),
            y: Math.max(12, yOf(candles[bosI]?.high ?? diag.bos_price) - 5).toFixed(1),
            'text-anchor': 'middle',
            fill: cText,
            'font-size': '8.5',
            'font-weight': '700',
          },
          'BOS'
        )
      );

      fgAnnotations.appendChild(
        makeHaloText(
          {
            x: (padL + plotW - 4).toFixed(1),
            y: Math.min(H - 5, zy + 10).toFixed(1),
            'text-anchor': 'end',
            fill: cPurple,
            'font-size': '9.5',
            'font-weight': '700',
          },
          'CHoCH Trigger'
        )
      );
    }
  }

  // 3. VWAP trajectory where inside plot bounds
  const vwapPts = candles
    .map((c, idx) => {
      if (c.vwap === undefined || c.vwap === null) return null;
      if (c.vwap < minP || c.vwap > maxP) return null;
      return `${xCenter(idx).toFixed(1)},${yOf(c.vwap).toFixed(1)}`;
    })
    .filter(Boolean);
  if (vwapPts.length >= 3) {
    svg.appendChild(
      svgEl('polyline', {
        fill: 'none',
        stroke: cSky,
        'stroke-width': '1',
        'stroke-dasharray': '2,2',
        opacity: '0.55',
        points: vwapPts.join(' '),
      })
    );
  }

  // 4. Level Overlays (TP / SL)
  const levelsG = svgEl('g', { class: 'level-overlay' });
  if (diag.tp_price) {
    const tpy = yOf(diag.tp_price);
    levelsG.appendChild(
      svgEl('line', {
        x1: padL,
        y1: tpy.toFixed(1),
        x2: padL + plotW,
        y2: tpy.toFixed(1),
        stroke: cGreen,
        'stroke-width': '1',
        'stroke-dasharray': '2,3',
        opacity: '0.7',
      })
    );
    fgLevels.appendChild(
      makeHaloText(
        {
          x: padL + 2,
          y: Math.max(10, tpy - 3).toFixed(1),
          fill: cGreen,
          'font-size': '8.5',
          'font-weight': '700',
          class: 'mono',
        },
        `TP ${Number(diag.tp_price).toFixed(2)}`
      )
    );
  }

  if (diag.sl_price) {
    const sly = yOf(diag.sl_price);
    levelsG.appendChild(
      svgEl('line', {
        x1: padL,
        y1: sly.toFixed(1),
        x2: padL + plotW,
        y2: sly.toFixed(1),
        stroke: cRed,
        'stroke-width': '1',
        'stroke-dasharray': '2,3',
        opacity: '0.75',
      })
    );
    fgLevels.appendChild(
      makeHaloText(
        {
          x: padL + 2,
          y: Math.min(H - 3, sly + 9).toFixed(1),
          fill: cRed,
          'font-size': '8.5',
          'font-weight': '700',
          class: 'mono',
        },
        `SL ${Number(diag.sl_price).toFixed(2)}`
      )
    );
  }
  svg.appendChild(levelsG);

  // 5. Real M1 Candlesticks
  const bodyW = Math.max(4.5, Math.min(11, step * 0.56));
  let entryIdx = candles.findIndex((c) => c.is_entry);
  if (entryIdx < 0) entryIdx = Math.floor(candles.length / 2);

  candles.forEach((c, idx) => {
    const cx = xCenter(idx);
    const isBull = Number(c.close) >= Number(c.open);
    const col = isBull ? cGreen : (diag.zone_type === 'resistance' ? cRed : cBear);

    const yHigh = yOf(Number(c.high));
    const yLow = yOf(Number(c.low));
    const yOpen = yOf(Number(c.open));
    const yClose = yOf(Number(c.close));
    const rectY = Math.min(yOpen, yClose);
    const rectH = Math.max(2.2, Math.abs(yOpen - yClose));

    svg.appendChild(
      svgEl('line', {
        x1: cx.toFixed(1),
        y1: yHigh.toFixed(1),
        x2: cx.toFixed(1),
        y2: yLow.toFixed(1),
        stroke: col,
        'stroke-width': '1.25',
      })
    );

    if (c.is_entry) {
      svg.appendChild(
        svgEl('rect', {
          x: (cx - bodyW / 2 - 2.5).toFixed(1),
          y: (rectY - 2.5).toFixed(1),
          width: (bodyW + 5).toFixed(1),
          height: (rectH + 5).toFixed(1),
          fill: 'none',
          stroke: cSky,
          'stroke-width': '1.4',
          rx: '2.5',
        })
      );
    } else if (c.is_exit) {
      svg.appendChild(
        svgEl('circle', {
          cx: cx.toFixed(1),
          cy: (yClose - 5).toFixed(1),
          r: '2.8',
          fill: cGreen,
          stroke: '#ffffff',
          'stroke-width': '1',
        })
      );
    }

    svg.appendChild(
      svgEl('rect', {
        x: (cx - bodyW / 2).toFixed(1),
        y: rectY.toFixed(1),
        width: bodyW.toFixed(1),
        height: rectH.toFixed(1),
        fill: col,
        rx: '1',
        opacity: isBull ? '0.96' : '0.88',
      })
    );
  });

  svg.appendChild(fgAnnotations);
  svg.appendChild(fgLevels);

  // 6. Right-side Price Callout Pill
  const calloutPrice = diag.callout_price ?? diag.entry_price ?? candles[entryIdx]?.close;
  if (calloutPrice !== undefined && calloutPrice !== null) {
    const cy = Math.max(12, Math.min(H - 12, yOf(Number(calloutPrice))));
    const cxEntry = xCenter(entryIdx);

    levelsG.appendChild(
      svgEl('line', {
        x1: cxEntry.toFixed(1),
        y1: cy.toFixed(1),
        x2: (W - padR + 4).toFixed(1),
        y2: cy.toFixed(1),
        stroke: cSky,
        'stroke-width': '1',
        'stroke-dasharray': '2,2',
        opacity: '0.8',
      })
    );

    const pillX = W - padR + 3;
    const pillW = padR - 5;
    const pillH = 18;
    svg.appendChild(
      svgEl('rect', {
        x: pillX,
        y: (cy - pillH / 2).toFixed(1),
        width: pillW,
        height: pillH,
        rx: '4',
        fill: cPillBg,
        stroke: cPillBorder,
        'stroke-width': '1',
      })
    );

    const pillText = svgEl('text', {
      x: (pillX + pillW / 2).toFixed(1),
      y: (cy + 3.2).toFixed(1),
      'text-anchor': 'middle',
      fill: '#f8fafc',
      'font-size': '9.5',
      'font-weight': '700',
      class: 'mono',
    });
    pillText.textContent = Number(calloutPrice).toFixed(2);
    svg.appendChild(pillText);
  }

  // 7. Interactive hover/focus hitboxes
  candles.forEach((c, idx) => {
    const hit = svgEl('rect', {
      x: (padL + idx * step).toFixed(1),
      y: padT - 6,
      width: step.toFixed(1),
      height: plotH + 12,
      class: 'candle-hit',
      tabindex: '0',
      'aria-label': `${c.time} Open ${c.open} High ${c.high} Low ${c.low} Close ${c.close}`,
    });

    const showCandleInfo = () => {
      if (!ohlcEl) return;
      const tag = c.is_entry ? 'ENTRY' : c.is_exit ? 'EXIT' : 'M1';
      ohlcEl.innerHTML = `
        <span class="mono"><b>${escapeHtml(tag)} ${escapeHtml(c.time)}</b></span>
        <span class="mono">O:${Number(c.open).toFixed(2)} H:${Number(c.high).toFixed(2)} L:${Number(c.low).toFixed(2)} C:<b>${Number(c.close).toFixed(2)}</b></span>
      `;
    };
    hit.addEventListener('mouseenter', showCandleInfo);
    hit.addEventListener('focus', showCandleInfo);
    svg.appendChild(hit);
  });

  return svg;
}

function renderMicrostructure() {
  const grid = $('microGrid');
  if (!grid) return;
  const cards = state.summary?.microstructure_patterns || [];
  grid.innerHTML = '';

  for (const card of cards) {
    const el = document.createElement('article');
    el.className = 'micro-card';

    const diag = card.diagram || {};
    const net = Number(diag.net_usd || 0);
    const edge = Number(card.edge_usd || 0);
    const pf = Number(card.profit_factor || 0);

    const head = document.createElement('div');
    head.className = 'micro-head';
    head.innerHTML = `
      <div class="micro-title-block">
        <h3>${escapeHtml(card.title)}</h3>
        <div class="micro-sub-row">
          <span class="tone-dot ${escapeHtml(card.badge_tone || 'green')}"></span>
          <span>${escapeHtml(card.subtitle)}</span>
        </div>
      </div>
      <span class="trade-example-pill" title="ตัวอย่างเทรดจริงจาก backtest_data.json (${escapeHtml(diag.timestamp || '')})">
        ${escapeHtml(diag.side || '')} ${net >= 0 ? '+' : '-'}$${Math.abs(net).toFixed(2)}
      </span>
    `;

    const entryCandle = (diag.candles || []).find((c) => c.is_entry) || (diag.candles || [])[0];
    const ohlcBar = document.createElement('div');
    ohlcBar.className = 'micro-ohlc-bar';
    ohlcBar.innerHTML = entryCandle
      ? `<span class="mono"><b>ENTRY ${escapeHtml(entryCandle.time)}</b> · hover แท่งเทียน</span>
         <span class="mono">C:<b>${Number(entryCandle.close).toFixed(2)}</b> · PF ${pf.toFixed(2)}</span>`
      : '<span>–</span>';

    const svgWrap = document.createElement('div');
    svgWrap.className = 'micro-svg-wrap';
    svgWrap.appendChild(buildMicrostructureSvg(card, ohlcBar));

    const desc = document.createElement('p');
    desc.className = 'micro-desc';
    desc.textContent = card.description || '';

    const rules = document.createElement('div');
    rules.className = 'micro-rules';
    rules.innerHTML = `
      <div><strong>Entry:</strong> ${escapeHtml(card.trigger_rule || '–')}</div>
      <div><strong>SL/TP:</strong> ${escapeHtml(card.exit_rule || '–')}</div>
    `;

    const metrics = document.createElement('div');
    metrics.className = 'micro-metrics';
    metrics.innerHTML = `
      <div class="mm-item">
        <span class="mm-label">Confidence</span>
        <span class="mm-val">${Number(card.confidence_pct || 0).toFixed(1)}%</span>
      </div>
      <div class="mm-item align-center">
        <span class="mm-label">Frequency</span>
        <span class="mm-val">${Number(card.frequency || 0).toLocaleString('en-US')}</span>
      </div>
      <div class="mm-item align-right">
        <span class="mm-label">Edge</span>
        <span class="mm-val ${edge > 0 ? 'pos' : edge < 0 ? 'neg' : ''}">${edge >= 0 ? '+' : '-'}$${Math.abs(edge).toFixed(2)}</span>
      </div>
    `;

    el.appendChild(head);
    el.appendChild(ohlcBar);
    el.appendChild(svgWrap);
    el.appendChild(desc);
    el.appendChild(rules);
    el.appendChild(metrics);
    grid.appendChild(el);
  }
}

/* ========================================================================
   Contextual Info Modal & Page Interactions
   ======================================================================== */

const HELP_CONTENT = {
  matrix: `
    <h4>Performance Matrix · ตารางเปรียบเทียบคู่เงิน</h4>
    <p>เปรียบเทียบประสิทธิภาพรายคู่เงินใน 3 ชุดข้อมูลจริงจาก Repository:</p>
    <ul>
      <li><b>Champion (L2 DOM):</b> พารามิเตอร์ที่ผ่านวิวัฒนาการล่าสุดบนข้อมูล 1-Minute Order Book (<code>champion_registry.json</code>)</li>
      <li><b>Live Demo (#5258778):</b> ผลเทรดจริงสะสมจากบัญชี Pepperstone Demo (#5258778) รายงานตรงตามสถานการณ์จริง (V5 Situational Reporting) ควบคู่ผล Out-of-Sample จาก <code>regime_strategy_matrix.json</code></li>
      <li><b>Backtest Engines:</b> กลยุทธ์ทั้ง 8 รุ่นในห้องทดลอง (<code>backtest_data.json</code>)</li>
    </ul>
    <p><b>Inline Progress Bar:</b> แถบ Win Rate มีเส้นอ้างอิงที่ <code>50%</code> และแถบ Profit Factor ใช้สเกล <code>0–4.0+</code> พร้อมเส้นจุดคุ้มทุนที่ <code>1.0x</code> · คลิกแถวใดก็ได้เพื่อกระโดดดู Heatmap ของคู่เงินนั้น</p>
  `,
  heatmap: `
    <h4>Day &amp; Session Intelligence Heatmap (2D CSS Grid)</h4>
    <p>วิเคราะห์ความได้เปรียบเชิงเวลาตลอด 5 วันทำการ (จันทร์–ศุกร์) × 3 เซสชันหลัก:</p>
    <ul>
      <li><b>ASIA SESSION:</b> 00:00 – 08:00 UTC (07:00 – 15:00 น. ไทย)</li>
      <li><b>LONDON SESSION:</b> 08:00 – 16:00 UTC (15:00 – 23:00 น. ไทย)</li>
      <li><b>NEW YORK SESSION:</b> 16:00 – 00:00 UTC (23:00 – 07:00 น. ไทย)</li>
    </ul>
    <p><b>No-Trade Zones (ช่องแรเงาสีส้ม):</b> ช่วงเวลาที่ค่าคาดหวังติดลบอย่างมีนัยสำคัญ, มีความเสี่ยงสเปรดถ่างช่วง Rollover (เช่น GOLD-PERP กลางคืน / ETHUSD นอก Asia), หรือเข้าเขต <b>Daily Flat Cutoff 21:45 UTC วันศุกร์</b></p>
  `,
  micro: `
    <h4>Microstructure Pattern · แผนภาพแท่งเทียนเวกเตอร์ SVG ล้วน</h4>
    <p>การ์ดทั้ง 3 ใบวาดจากแท่งเทียน M1 ของเทรดจริงใน <code>backtest_data.json</code> พร้อมแสดง Zone และจุด Entry / SL / TP:</p>
    <ul>
      <li><b>Absorption · Buy Side:</b> ราคาทดสอบแนวรับ/VWAP Discount ขณะ Bid Wall ดูดซับแรงขาย</li>
      <li><b>Absorption · Sell Side:</b> ราคาพุ่งเข้าแนวต้าน/Premium Zone เกิด Ask Wall ปฏิเสธราคา</li>
      <li><b>CHoCH (Change of Character):</b> กวาดสภาพคล่องทำ Lower Low แล้วเบรก High ก่อนหน้า (BOS/CHoCH) เปลี่ยนโครงสร้างเป็นขาขึ้น</li>
    </ul>
    <p><b>Interactive:</b> ชี้เมาส์หรือใช้ Tab โฟกัสที่แท่งเทียนใดก็ได้บน SVG เพื่ออ่านค่า O/H/L/C รายนาที</p>
  `,
};

function openInfoModal(topic = 'matrix') {
  const modal = $('infoModal');
  const title = $('infoModalTitle');
  const body = $('infoModalBody');
  if (!modal || !body) return;
  const titles = {
    matrix: 'คำอธิบาย: Performance Matrix',
    heatmap: 'คำอธิบาย: Day & Session Heatmap & No-Trade Zones',
    micro: 'คำอธิบาย: Microstructure SVG Pattern Cards',
  };
  if (title) title.textContent = titles[topic] || titles.matrix;
  body.innerHTML = HELP_CONTENT[topic] || HELP_CONTENT.matrix;
  modal.hidden = false;
}

function initInteractions() {
  document.querySelectorAll('#matrixModeTabs .seg-tab').forEach((btn) => {
    btn.addEventListener('click', () => {
      state.matrixMode = btn.dataset.mode || 'champion';
      state.sortKey = null;
      document.querySelectorAll('#matrixModeTabs .seg-tab').forEach((b) => {
        const active = b === btn;
        b.classList.toggle('active', active);
        b.setAttribute('aria-selected', String(active));
      });
      renderMatrix();
    });
  });

  document.querySelectorAll('.sort-btn').forEach((btn) => {
    btn.addEventListener('click', () => {
      const key = btn.dataset.sort;
      if (!key) return;
      if (state.sortKey === key) {
        state.sortDir = state.sortDir === 'desc' ? 'asc' : 'desc';
      } else {
        state.sortKey = key;
        state.sortDir = key === 'symbol' ? 'asc' : 'desc';
      }
      renderMatrix();
    });
  });

  document.querySelectorAll('#heatmapViewPills .view-pill').forEach((btn) => {
    btn.addEventListener('click', () => {
      state.heatmapView = btn.dataset.view || 'xauusd_3y';
      state.activeCellKey = null;
      syncHeatmapPills();
      renderHeatmap();
    });
  });

  const chkLevels = $('chkShowLevels');
  if (chkLevels) {
    chkLevels.addEventListener('change', () => {
      state.showLevels = chkLevels.checked;
      document.querySelectorAll('.micro-svg').forEach((svg) => {
        svg.classList.toggle('hide-levels', !state.showLevels);
      });
    });
  }

  document.querySelectorAll('.intel-info-btn').forEach((btn) => {
    btn.addEventListener('click', () => openInfoModal(btn.dataset.info || 'matrix'));
  });

  const infoModal = $('infoModal');
  const btnCloseInfo = $('btnCloseInfo');
  if (btnCloseInfo && infoModal) {
    btnCloseInfo.addEventListener('click', () => { infoModal.hidden = true; });
  }
  if (infoModal) {
    infoModal.addEventListener('click', (e) => {
      if (e.target === infoModal) infoModal.hidden = true;
    });
  }
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && infoModal) infoModal.hidden = true;
  });

  const btnRefresh = $('btnRefreshData');
  if (btnRefresh) {
    btnRefresh.addEventListener('click', () => loadAllData(true));
  }

  // Watch shared shell data-theme attribute so SVGs adapt immediately
  const obs = new MutationObserver((muts) => {
    for (const m of muts) {
      if (m.attributeName === 'data-theme') {
        renderTickers();
        renderMicrostructure();
      }
    }
  });
  obs.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });
}

/* ========================================================================
   Data Loader & Bootstrap
   ======================================================================== */

function formatWatchdogForShell(wd) {
  if (!wd) return null;
  const raw = Array.isArray(wd.active_alerts) ? wd.active_alerts : [];
  return {
    ...wd,
    active_alerts: raw.map((a) => (
      typeof a === 'string'
        ? a
        : `${a.symbol || 'FEED'}: ${a.alert || 'STALLED'} (last: ${a.last_seen || '–'} UTC)`
    )),
  };
}

async function loadAllData(isManual = false) {
  const offlineBanner = $('offlineBanner');
  const offlineText = $('offlineBannerText');
  const btnRefresh = $('btnRefreshData');
  if (isManual && btnRefresh) {
    btnRefresh.disabled = true;
  }

  const failedSources = [];
  const tryFetch = async (url, label) => {
    try {
      return await fetchJson(url);
    } catch (err) {
      failedSources.push(label);
      return null;
    }
  };

  try {
    const [summary, liveStatus, watchdog, alerts, overview] = await Promise.all([
      tryFetch(DATA_URLS.summary, 'intelligence_summary'),
      tryFetch(DATA_URLS.live, 'live_status'),
      tryFetch(DATA_URLS.watchdog, 'watchdog_status'),
      tryFetch(DATA_URLS.alerts, 'web_alerts'),
      tryFetch(DATA_URLS.overview, 'overview_summary'),
    ]);

    if (liveStatus) state.liveStatus = liveStatus;
    if (watchdog) state.watchdog = watchdog;
    if (alerts) state.alerts = alerts;
    if (overview) state.overview = overview;

    updateShellTelemetry({
      watchdog: formatWatchdogForShell(state.watchdog),
      webAlerts: state.alerts,
      liveStatus: state.liveStatus,
      overviewSummary: state.overview,
      failedSources,
    });

    if (!summary) {
      throw new Error('ไม่สามารถโหลด docs/data/intelligence_summary.json ได้');
    }
    state.summary = summary;

    const syncNote = $('syncNote');
    const asOf = state.liveStatus?.timestamp_utc || state.summary?.meta?.data_as_of_utc;
    if (syncNote) {
      syncNote.textContent = `Data snapshot: ${formatUtcShort(asOf)}`;
    }

    if (offlineBanner) offlineBanner.hidden = true;

    renderTickers();
    renderMatrix();
    syncHeatmapPills();
    renderHeatmap();
    renderMicrostructure();
  } catch (err) {
    console.error('Intelligence fetch error:', err);
    if (offlineBanner && offlineText) {
      offlineBanner.hidden = false;
      offlineText.textContent = state.summary
        ? `ไม่สามารถดึงข้อมูลล่าสุดได้ (${err.message}) — กำลังแสดงข้อมูลที่แคชไว้ล่าสุด`
        : `โหลดข้อมูลไม่สำเร็จ (${err.message}) — กรุณาเปิดผ่านเว็บเซิร์ฟเวอร์ (GitHub Pages หรือ python -m http.server)`;
    }
  } finally {
    if (btnRefresh) btnRefresh.disabled = false;
  }
}

function init() {
  mountShell({
    activePage: 'intelligence.html',
    onRetry: () => loadAllData(true),
  });
  initInteractions();
  loadAllData(false);
  state.refreshTimer = setInterval(() => loadAllData(false), 60000);
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
