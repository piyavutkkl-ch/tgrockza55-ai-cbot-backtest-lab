import { mountShell, updateShellTelemetry, escapeHtml, formatRelativeTime } from './shell.js';

const REFRESH_INTERVAL_MS = 45000;

const state = {
  selectedChampion: null,
  showOfflineBots: false,
  expandedBots: new Set(),
  lastData: {
    overviewSummary: null,
    liveStatus: null,
    watchdog: null,
    webAlerts: null,
    truthGuard: null,
    foundry: null,
    championRegistry: null,
  },
  failedSources: [],
};

let refreshTimer = null;
let signalTimer = null;

function numOrNull(v) {
  if (v === null || v === undefined || v === '') return null;
  const n = Number(v);
  return Number.isFinite(n) ? n : null;
}

function fmtMoney(v, { signed = false, decimals = 2 } = {}) {
  const n = numOrNull(v);
  if (n === null) return null;
  const abs = Math.abs(n).toLocaleString('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
  if (n < 0) return `-$${abs}`;
  if (signed && n > 0) return `+$${abs}`;
  return `$${abs}`;
}

function fmtPrice(v, symbol = '') {
  const n = numOrNull(v);
  if (n === null || n <= 0) return null;
  const dec = symbol.includes('BTC') || symbol.includes('ETH') || symbol.includes('XAU') || symbol.includes('GOLD') ? 2 : 2;
  return '$' + n.toLocaleString('en-US', { minimumFractionDigits: dec, maximumFractionDigits: dec });
}

function fmtPct(v, { signed = false, decimals = 1 } = {}) {
  const n = numOrNull(v);
  if (n === null) return null;
  const abs = Math.abs(n).toFixed(decimals);
  if (n < 0) return `-${abs}%`;
  if (signed && n > 0) return `+${abs}%`;
  return `${abs}%`;
}

function missingCell(tip = 'ยังไม่มีข้อมูล') {
  return `<span class="val-muted" data-tooltip="${escapeHtml(tip)}" title="${escapeHtml(tip)}">–</span>`;
}

function signClass(v) {
  const n = numOrNull(v);
  if (n === null || n === 0) return '';
  return n > 0 ? 'val-pos' : 'val-neg';
}

function signArrow(v) {
  const n = numOrNull(v);
  if (n === null || n === 0) return '';
  return n > 0 ? '▲ ' : '▼ ';
}

function formatM1Countdown() {
  const now = new Date();
  const rem = Math.max(0, 60 - now.getUTCSeconds());
  const sec = rem === 60 ? 0 : rem;
  return `00:${String(sec).padStart(2, '0')}`;
}

/**
 * Reusable pure-SVG responsive line/area chart with interactive hover crosshair & tooltip
 */
function renderSvgSparkline(container, points, opts = {}) {
  if (!container) return;
  const valid = (Array.isArray(points) ? points : []).filter((p) => numOrNull(p?.y) !== null);
  if (valid.length < 2) {
    container.innerHTML = `<div style="height:100%;display:flex;align-items:center;justify-content:center;font-size:11px;color:var(--text-muted);" title="ยังไม่มีข้อมูลกราฟเพียงพอ">ไม่มีกราฟ</div>`;
    return;
  }

  const W = opts.width || 280;
  const H = opts.height || 92;
  const padX = 6;
  const padY = 8;
  const stroke = opts.stroke || '#22c55e';
  const uid = opts.id || `spk-${Math.random().toString(36).slice(2, 8)}`;

  const ys = valid.map((p) => Number(p.y));
  if (numOrNull(opts.baseline) !== null) ys.push(Number(opts.baseline));
  const minY = Math.min(...ys);
  const maxY = Math.max(...ys);
  const spanY = maxY - minY || Math.abs(maxY) * 0.01 || 1;

  const mapX = (i) => padX + (i / (valid.length - 1)) * (W - padX * 2);
  const mapY = (val) => padY + (1 - (val - minY) / spanY) * (H - padY * 2);

  const coords = valid.map((p, i) => ({
    x: Number(mapX(i).toFixed(2)),
    y: Number(mapY(Number(p.y)).toFixed(2)),
    rawY: Number(p.y),
    label: p.label || '',
    sub: p.sub || '',
  }));

  const linePath = coords.map((c, i) => `${i === 0 ? 'M' : 'L'}${c.x},${c.y}`).join(' ');
  const areaPath = `${linePath} L${coords[coords.length - 1].x},${H} L${coords[0].x},${H} Z`;
  const last = coords[coords.length - 1];

  let baselineSvg = '';
  if (numOrNull(opts.baseline) !== null) {
    const by = mapY(Number(opts.baseline)).toFixed(2);
    baselineSvg = `<line x1="${padX}" y1="${by}" x2="${W - padX}" y2="${by}" stroke="var(--border-strong)" stroke-width="1" stroke-dasharray="3 3" opacity="0.7" />`;
  }

  const gridSvg = opts.showGrid
    ? [0.25, 0.5, 0.75]
        .map((r) => {
          const gy = (padY + r * (H - padY * 2)).toFixed(1);
          return `<line x1="${padX}" y1="${gy}" x2="${W - padX}" y2="${gy}" stroke="var(--border-subtle)" stroke-width="0.7" opacity="0.65" />`;
        })
        .join('')
    : '';

  const trophyWatermark = opts.trophyWatermark
    ? `<g opacity="0.16" transform="translate(${W - 64}, ${H - 64}) scale(2.2)">
         <path d="M6 9H4.5a2.5 2.5 0 0 1 0-5H6" fill="none" stroke="#f5b301" stroke-width="1.5"/>
         <path d="M18 9h1.5a2.5 2.5 0 0 0 0-5H18" fill="none" stroke="#f5b301" stroke-width="1.5"/>
         <path d="M4 22h16" stroke="#f5b301" stroke-width="1.5"/>
         <path d="M10 14.66V17c0 .55-.47.98-.97 1.21C7.85 18.75 7 20.24 7 22" fill="none" stroke="#f5b301" stroke-width="1.5"/>
         <path d="M14 14.66V17c0 .55.47.98.97 1.21C16.15 18.75 17 20.24 17 22" fill="none" stroke="#f5b301" stroke-width="1.5"/>
         <path d="M18 2H6v7a6 6 0 0 0 12 0V2Z" fill="rgba(245,179,1,0.35)" stroke="#f5b301" stroke-width="1.5"/>
       </g>`
    : '';

  container.innerHTML = `
    <svg viewBox="0 0 ${W} ${H}" width="100%" height="100%" preserveAspectRatio="none" role="img" aria-label="${escapeHtml(opts.ariaLabel || 'Equity sparkline')}">
      <defs>
        <linearGradient id="${uid}" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="${stroke}" stop-opacity="0.34"/>
          <stop offset="100%" stop-color="${stroke}" stop-opacity="0.02"/>
        </linearGradient>
      </defs>
      ${gridSvg}
      ${trophyWatermark}
      ${baselineSvg}
      <path d="${areaPath}" fill="url(#${uid})"/>
      <path d="${linePath}" fill="none" stroke="${stroke}" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>
      <line class="crosshair-line" x1="0" y1="0" x2="0" y2="${H}" stroke="var(--text-muted)" stroke-width="1" stroke-dasharray="2 2" visibility="hidden"/>
      <circle class="crosshair-dot" cx="${last.x}" cy="${last.y}" r="3.2" fill="${stroke}" stroke="var(--bg-card)" stroke-width="1.4"/>
    </svg>
    <div class="chart-hover-tip" hidden></div>
  `;

  const svg = container.querySelector('svg');
  const tip = container.querySelector('.chart-hover-tip');
  const xLine = container.querySelector('.crosshair-line');
  const dot = container.querySelector('.crosshair-dot');
  const formatVal = opts.formatVal || ((v) => fmtMoney(v, { signed: false }) ?? String(v));

  container.addEventListener('mousemove', (e) => {
    const rect = svg.getBoundingClientRect();
    if (!rect.width) return;
    const relX = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
    const idx = Math.min(coords.length - 1, Math.max(0, Math.round(relX * (coords.length - 1))));
    const pt = coords[idx];
    xLine.setAttribute('x1', pt.x);
    xLine.setAttribute('x2', pt.x);
    xLine.setAttribute('visibility', 'visible');
    dot.setAttribute('cx', pt.x);
    dot.setAttribute('cy', pt.y);

    tip.hidden = false;
    tip.textContent = `${pt.label ? pt.label + ' · ' : ''}${formatVal(pt.rawY)}${pt.sub ? ' (' + pt.sub + ')' : ''}`;
    const tipX = Math.min(rect.width - tip.offsetWidth - 6, Math.max(6, (pt.x / W) * rect.width - tip.offsetWidth / 2));
    tip.style.left = `${tipX}px`;
    tip.style.top = '6px';
  });

  container.addEventListener('mouseleave', () => {
    xLine.setAttribute('visibility', 'hidden');
    dot.setAttribute('cx', last.x);
    dot.setAttribute('cy', last.y);
    tip.hidden = true;
  });
}

function buildLiveEquitySeries(liveStatus, overviewSummary) {
  const ft = liveStatus?.forward_trading || {};
  const histCurve = Array.isArray(overviewSummary?.live_history?.equity_curve)
    ? overviewSummary.live_history.equity_curve.map((p) => ({
        y: numOrNull(p.balance),
        label: p.time === 'Start' ? 'Deposit' : String(p.time || '').slice(5, 16),
        sub: p.symbol || '',
      }))
    : [];

  // Ensure live updates to recent_closed_deals / balance in live_status.json immediately reflect at tail
  const recentDeals = [...(Array.isArray(liveStatus?.recent_closed_deals) ? liveStatus.recent_closed_deals : [])]
    .sort((a, b) => String(a.close_time || '').localeCompare(String(b.close_time || '')));

  let points = histCurve.filter((p) => p.y !== null);
  if (points.length === 0 && recentDeals.length > 0) {
    const dep = numOrNull(ft.initial_deposit);
    if (dep !== null) points.push({ y: dep, label: 'Deposit', sub: '' });
    for (const d of recentDeals) {
      const b = numOrNull(d.balance);
      if (b !== null) points.push({ y: b, label: String(d.close_time || '').slice(5, 16), sub: d.symbol || '' });
    }
  } else if (points.length > 0 && recentDeals.length > 0) {
    const lastDeal = recentDeals[recentDeals.length - 1];
    const lastBal = numOrNull(lastDeal.balance);
    if (lastBal !== null && Math.abs(points[points.length - 1].y - lastBal) > 0.01) {
      points.push({ y: lastBal, label: String(lastDeal.close_time || '').slice(5, 16), sub: lastDeal.symbol || '' });
    }
  }

  const curBal = numOrNull(ft.balance);
  if (curBal !== null && points.length > 0 && Math.abs(points[points.length - 1].y - curBal) > 0.01) {
    points.push({ y: curBal, label: 'Current Balance', sub: 'Live Demo' });
  }
  return points;
}

function computeTodayRealizedPnl(liveStatus) {
  const ft = liveStatus?.forward_trading || {};
  if (numOrNull(ft.today_pnl) !== null) {
    return { val: numOrNull(ft.today_pnl), tip: 'ค่า Today PnL จาก forward_trading.today_pnl' };
  }
  const deals = Array.isArray(liveStatus?.recent_closed_deals) ? liveStatus.recent_closed_deals : [];
  if (deals.length === 0) {
    return { val: null, tip: 'ยังไม่มีข้อมูล' };
  }
  const sessionDate = String(liveStatus?.timestamp_utc || deals[0]?.close_time || '').slice(0, 10);
  if (!sessionDate) return { val: null, tip: 'ยังไม่มีข้อมูล' };
  const todayDeals = deals.filter((d) => String(d.close_time || '').startsWith(sessionDate));
  const sum = todayDeals.reduce((acc, d) => acc + (numOrNull(d.net) || 0), 0);
  return {
    val: Number(sum.toFixed(2)),
    tip: todayDeals.length > 0
      ? `รวม ${todayDeals.length} ไม้ที่ปิดในวันที่ ${sessionDate} (recent_closed_deals)`
      : `ยังไม่มีไม้ปิดในวันที่ ${sessionDate}`,
  };
}

function renderLiveDemoCard(liveStatus, truthGuard, overviewSummary) {
  const card = document.getElementById('card-live-demo');
  if (!card) return;

  const ft = liveStatus?.forward_trading || {};
  const emp = truthGuard?.metrics_empirical || {};
  const balance = numOrNull(ft.balance ?? emp.current_balance);
  const equity = numOrNull(ft.equity ?? balance);
  const deposit = numOrNull(ft.initial_deposit ?? emp.initial_deposit);
  const netPnl = numOrNull(ft.net_pnl ?? emp.net_pnl_usd);
  const netPct = numOrNull(ft.net_pnl_pct ?? emp.net_pnl_pct);
  const winRate = numOrNull(ft.win_rate ?? emp.win_rate_pct);
  const pf = numOrNull(emp.profit_factor);
  const totalN = numOrNull(ft.total_trades ?? emp.total_closed_trades_N);

  const accountStr = String(ft.account || truthGuard?.account_number || '–');
  const acctMatch = accountStr.match(/#?\d{5,}/);
  const accountBadge = acctMatch ? `#${acctMatch[0].replace('#', '')}` : accountStr;

  const statusRaw = String(ft.status || '').toUpperCase();
  const isLive = statusRaw === 'RUNNING' || statusRaw === 'LIVE';
  const statusPill = statusRaw
    ? `<span class="badge ${isLive ? 'badge-green' : 'badge-gold'}"><span class="pulse-dot ${isLive ? 'green' : 'amber'}" aria-hidden="true"></span>${isLive ? 'LIVE' : escapeHtml(statusRaw)}</span>`
    : `<span class="badge badge-muted">–</span>`;

  const todayPnl = computeTodayRealizedPnl(liveStatus);
  const weekPnlVal = numOrNull(ft.week_pnl ?? emp.week_pnl);
  const monthPnlVal = numOrNull(ft.month_pnl ?? emp.month_pnl);
  const maxDdVal = numOrNull(ft.max_dd_pct ?? emp.max_dd_pct);

  const deltaHtml = netPnl !== null
    ? `<span class="mono ${signClass(netPnl)}" style="font-weight:700;">${signArrow(netPnl)}${escapeHtml(fmtMoney(netPnl, { signed: true }))}${netPct !== null ? ` (${escapeHtml(fmtPct(netPct, { signed: true }))})` : ''}</span>`
    : missingCell();

  card.innerHTML = `
    <div class="hero-card-top">
      <div class="hero-title-group">
        <span style="width:26px;height:26px;border-radius:7px;background:linear-gradient(135deg,#0ea5e9,#2563eb);color:#fff;display:inline-flex;align-items:center;justify-content:center;font-weight:800;font-size:13px;" aria-hidden="true">P</span>
        <h2 class="hero-card-title">LIVE DEMO PEPPERSTONE</h2>
        ${statusPill}
        <span class="hero-account-tag mono" title="${escapeHtml(accountStr)}">${escapeHtml(accountBadge)}</span>
      </div>
      <span class="hero-category-pill badge-blue">ยอดเงินพอร์ตสด (Live Demo)</span>
    </div>

    <div class="hero-main-split">
      <div>
        <div class="hero-big-value mono">${balance !== null ? escapeHtml(fmtMoney(balance)) : missingCell()}</div>
        <div class="hero-delta-row">
          ${deltaHtml}
          <span style="color:var(--border-strong);" aria-hidden="true">|</span>
          <span class="mono">Deposit: ${deposit !== null ? escapeHtml(fmtMoney(deposit)) : '–'}</span>
        </div>
        <div class="hero-subline mono">
          <span>Equity: ${equity !== null ? escapeHtml(fmtMoney(equity)) : '–'}</span>
          <span>·</span>
          <span>Trades: ${totalN !== null ? escapeHtml(String(totalN)) : '–'}</span>
          ${pf !== null ? `<span>·</span><span>PF: ${escapeHtml(pf.toFixed(2))}</span>` : ''}
        </div>
      </div>

      <div class="hero-chart-box" id="live-demo-sparkline"></div>
    </div>

    <div class="hero-stats-strip">
      <div class="stat-cell">
        <div class="stat-cell-label">Today PnL</div>
        <div class="stat-cell-val mono ${signClass(todayPnl.val)}" title="${escapeHtml(todayPnl.tip)}">
          ${todayPnl.val !== null ? escapeHtml(fmtMoney(todayPnl.val, { signed: true })) : missingCell(todayPnl.tip)}
        </div>
      </div>
      <div class="stat-cell">
        <div class="stat-cell-label">Week PnL</div>
        <div class="stat-cell-val mono ${signClass(weekPnlVal)}">
          ${weekPnlVal !== null ? escapeHtml(fmtMoney(weekPnlVal, { signed: true })) : missingCell('ยังไม่มีข้อมูลครบทั้งสัปดาห์')}
        </div>
      </div>
      <div class="stat-cell">
        <div class="stat-cell-label">Month PnL</div>
        <div class="stat-cell-val mono ${signClass(monthPnlVal)}">
          ${monthPnlVal !== null ? escapeHtml(fmtMoney(monthPnlVal, { signed: true })) : missingCell('ยังไม่มีข้อมูลครบทั้งเดือน')}
        </div>
      </div>
      <div class="stat-cell">
        <div class="stat-cell-label">Win Rate</div>
        <div class="stat-cell-val mono" title="${emp.wins_count != null ? `${emp.wins_count}W / ${emp.losses_count}L` : ''}">
          ${winRate !== null ? escapeHtml(fmtPct(winRate)) : missingCell()}
        </div>
      </div>
      <div class="stat-cell">
        <div class="stat-cell-label">Max DD</div>
        <div class="stat-cell-val mono">
          ${maxDdVal !== null ? escapeHtml(fmtPct(maxDdVal)) : missingCell('ยังไม่มีข้อมูล')}
        </div>
      </div>
    </div>
  `;

  const pts = buildLiveEquitySeries(liveStatus, overviewSummary);
  const sparkStroke = netPnl !== null && netPnl < 0 ? '#38bdf8' : '#22c55e';
  renderSvgSparkline(document.getElementById('live-demo-sparkline'), pts, {
    id: 'live-eq',
    stroke: sparkStroke,
    baseline: deposit,
    showGrid: true,
    ariaLabel: 'Live Demo Pepperstone balance trajectory',
    formatVal: (v) => fmtMoney(v) ?? String(v),
  });
}

function resolveChampionModels(championRegistry, overviewSummary) {
  const results = championRegistry?.results;
  if (results && typeof results === 'object' && Object.keys(results).length > 0) {
    const entries = Object.entries(results).map(([sym, item]) => {
      const m = item?.metrics || {};
      const dailyPnl = m.daily_pnl || {};
      const curve = [{ label: 'Start', y: 0 }];
      let cum = 0;
      for (const day of Object.keys(dailyPnl).sort()) {
        cum += Number(dailyPnl[day]) || 0;
        curve.push({ label: day.slice(5), y: Number(cum.toFixed(2)) });
      }
      const netPnl = numOrNull(m.net_pnl ?? m.net_pnl_usd);
      return {
        key: sym,
        symbol: sym,
        status: String(item.status || 'CHAMPION').toUpperCase(),
        name: item.name || sym,
        strategyType: item.parameters?.type || m.config?.type || 'DOM_ABSORPTION',
        trades: numOrNull(m.trades),
        winRate: numOrNull(m.win_rate),
        pf: numOrNull(m.profit_factor),
        netPnl,
        dailyWinRate: numOrNull(m.daily_win_rate ?? m.daily_win_rate_pct),
        positiveDays: numOrNull(m.positive_days),
        totalDays: numOrNull(m.total_days),
        maxDdUsd: numOrNull(m.max_dd_usd ?? m.max_dd ?? m.max_drawdown),
        curve,
      };
    });
    entries.sort((a, b) => {
      if (a.status === 'PROMOTED' && b.status !== 'PROMOTED') return -1;
      if (b.status === 'PROMOTED' && a.status !== 'PROMOTED') return 1;
      return (b.netPnl || 0) - (a.netPnl || 0);
    });
    return entries;
  }

  // Fallback from overview_summary.backtest_fallback if champion_registry.json failed
  const fb = overviewSummary?.backtest_fallback || {};
  const fbKeys = Object.keys(fb);
  if (fbKeys.length > 0) {
    const pick = fb.vwap_equilibrium_xau ? 'vwap_equilibrium_xau' : fbKeys[0];
    const m = fb[pick];
    const s = m.summary || {};
    return [{
      key: pick,
      symbol: m.symbol || 'XAUUSD',
      status: 'FALLBACK',
      name: m.name || pick,
      strategyType: m.timeframe || 'Backtest',
      trades: numOrNull(s.total_trades),
      winRate: numOrNull(s.win_rate),
      pf: numOrNull(s.profit_factor),
      netPnl: numOrNull(s.net_profit),
      dailyWinRate: numOrNull(s.daily_win_rate),
      positiveDays: null,
      totalDays: null,
      maxDdUsd: numOrNull(s.max_drawdown),
      curve: (m.equity_curve || []).map((p) => ({ label: p.label, y: numOrNull(p.pnl) })),
    }];
  }

  return [];
}

function renderChampionCard(championRegistry, overviewSummary) {
  const card = document.getElementById('card-champion-backtest');
  if (!card) return;

  const models = resolveChampionModels(championRegistry, overviewSummary);
  if (models.length === 0) {
    card.innerHTML = `
      <div class="hero-card-top">
        <div class="hero-title-group">
          <span aria-hidden="true">🏆</span>
          <h2 class="hero-card-title">CHAMPION BACKTEST</h2>
        </div>
        <span class="hero-category-pill badge-gold">ผลการทดสอบย้อนหลัง (Backtest Lab)</span>
      </div>
      <div style="padding:24px 0;color:var(--text-muted);">ยังไม่มีข้อมูล Champion Backtest</div>
    `;
    return;
  }

  if (!state.selectedChampion || !models.some((m) => m.key === state.selectedChampion)) {
    state.selectedChampion = models[0].key;
  }
  const active = models.find((m) => m.key === state.selectedChampion) || models[0];

  const netText = active.netPnl !== null ? fmtMoney(active.netPnl, { signed: true }) : null;
  const subDays = active.positiveDays !== null && active.totalDays !== null
    ? `${active.positiveDays}/${active.totalDays} วันบวก`
    : (active.dailyWinRate !== null ? `Daily WR ${fmtPct(active.dailyWinRate)}` : '');

  card.innerHTML = `
    <div class="hero-card-top">
      <div class="hero-title-group">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path d="M6 9H4.5a2.5 2.5 0 0 1 0-5H6M18 9h1.5a2.5 2.5 0 0 0 0-5H18M4 22h16M10 14.66V17c0 .55-.47.98-.97 1.21C7.85 18.75 7 20.24 7 22M14 14.66V17c0 .55.47.98.97 1.21C16.15 18.75 17 20.24 17 22" stroke="#f5b301" stroke-width="1.9" stroke-linecap="round"/>
          <path d="M18 2H6v7a6 6 0 0 0 12 0V2Z" fill="rgba(245,179,1,0.22)" stroke="#f5b301" stroke-width="1.9"/>
        </svg>
        <h2 class="hero-card-title">CHAMPION BACKTEST</h2>
        <span class="badge ${active.status === 'PROMOTED' ? 'badge-gold' : 'badge-muted'}">${escapeHtml(active.status)}</span>
      </div>
      <span class="hero-category-pill badge-gold">ผลการทดสอบย้อนหลัง (Backtest Lab)</span>
    </div>

    <div class="hero-main-split">
      <div>
        <div class="hero-big-inline">
          <div class="hero-big-value mono ${signClass(active.netPnl)}">${netText !== null ? escapeHtml(netText) : missingCell()}</div>
          <span class="hero-big-suffix">Net PnL</span>
        </div>
        <div class="hero-subline">
          <span title="${escapeHtml(active.name)}" style="font-weight:600;color:var(--text-secondary);max-width:100%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">
            ${escapeHtml(active.name)}
          </span>
        </div>
        <div class="hero-subline mono">
          <span>Model: ${escapeHtml(active.strategyType)}</span>
          ${subDays ? `<span>·</span><span>${escapeHtml(subDays)}</span>` : ''}
        </div>
        ${models.length > 1 ? `
          <div class="champion-switch-row" style="margin-top:8px;" role="tablist" aria-label="เลือกดูผลการทดสอบย้อนหลังตามสินทรัพย์">
            ${models.map((m) => `
              <button type="button"
                      role="tab"
                      aria-selected="${m.key === active.key}"
                      class="champ-tab-btn mono ${m.key === active.key ? 'is-active' : ''}"
                      data-champ-key="${escapeHtml(m.key)}">
                ${escapeHtml(m.symbol)}${m.status === 'PROMOTED' ? ' ★' : ''}
              </button>
            `).join('')}
          </div>
        ` : ''}
      </div>

      <div class="hero-chart-box" id="champion-backtest-chart"></div>
    </div>

    <div class="hero-stats-strip cols-4">
      <div class="stat-cell">
        <div class="stat-cell-label">Total Trades</div>
        <div class="stat-cell-val mono">${active.trades !== null ? escapeHtml(String(active.trades)) : missingCell()}</div>
      </div>
      <div class="stat-cell">
        <div class="stat-cell-label">Win Rate</div>
        <div class="stat-cell-val mono">${active.winRate !== null ? escapeHtml(fmtPct(active.winRate)) : missingCell()}</div>
      </div>
      <div class="stat-cell">
        <div class="stat-cell-label">Profit Factor</div>
        <div class="stat-cell-val mono">${active.pf !== null ? escapeHtml(active.pf.toFixed(2)) : missingCell()}</div>
      </div>
      <div class="stat-cell">
        <div class="stat-cell-label">Max DD</div>
        <div class="stat-cell-val mono">
          ${active.maxDdUsd !== null ? escapeHtml(fmtMoney(active.maxDdUsd)) : missingCell(`ยังไม่มีข้อมูล Max DD ของ ${active.symbol} ใน champion_registry.json`)}
        </div>
      </div>
    </div>
  `;

  card.querySelectorAll('[data-champ-key]').forEach((btn) => {
    btn.addEventListener('click', () => {
      state.selectedChampion = btn.getAttribute('data-champ-key');
      renderChampionCard(state.lastData.championRegistry, state.lastData.overviewSummary);
    });
  });

  renderSvgSparkline(document.getElementById('champion-backtest-chart'), active.curve, {
    id: 'champ-eq',
    stroke: '#38bdf8',
    baseline: 0,
    showGrid: true,
    trophyWatermark: true,
    ariaLabel: `${active.symbol} backtest cumulative PnL curve`,
    formatVal: (v) => fmtMoney(v, { signed: true }) ?? String(v),
  });
}

function botTheme(symbol) {
  const s = String(symbol || '').toUpperCase();
  if (s.includes('BTC')) {
    return {
      icon: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true"><circle cx="12" cy="12" r="10" fill="rgba(245,158,11,0.2)" stroke="#f59e0b" stroke-width="1.6"/><text x="12" y="16" text-anchor="middle" font-size="12" font-weight="800" fill="#f59e0b" font-family="system-ui,sans-serif">B</text></svg>',
      display: 'BTC/USD',
      bg: 'rgba(245,158,11,0.14)',
      fg: '#f59e0b',
      line: '#22c55e',
    };
  }
  if (s.includes('ETH')) {
    return {
      icon: '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" aria-hidden="true"><polygon points="12,2 19,12 12,16 5,12" fill="rgba(129,140,248,0.85)"/><polygon points="12,17.5 19,13.5 12,22 5,13.5" fill="rgba(99,102,241,0.65)"/></svg>',
      display: 'ETH/USD',
      bg: 'rgba(99,102,241,0.16)',
      fg: '#818cf8',
      line: '#38bdf8',
    };
  }
  if (s.includes('GOLD-PERP')) {
    return {
      icon: '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" aria-hidden="true"><polygon points="12,3 21,12 12,21 3,12" fill="rgba(234,179,8,0.8)"/></svg>',
      display: 'GOLD-PERP',
      bg: 'rgba(234,179,8,0.16)',
      fg: '#eab308',
      line: '#f5b301',
    };
  }
  if (s.includes('XAU')) {
    return {
      icon: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true"><rect x="4" y="13" width="7" height="5" rx="1" fill="#f5b301"/><rect x="13" y="13" width="7" height="5" rx="1" fill="#eab308"/><rect x="8.5" y="7" width="7" height="5" rx="1" fill="#fbbf24"/></svg>',
      display: 'XAU/USD',
      bg: 'rgba(245,179,1,0.16)',
      fg: '#f5b301',
      line: '#f5b301',
    };
  }
  return { icon: '●', display: symbol || 'BOT', bg: 'rgba(148,163,184,0.18)', fg: '#94a3b8', line: '#94a3b8' };
}

function findOpenTradesMap(recentTrades) {
  const openMap = new Map();
  const closedIds = new Set();
  for (const t of Array.isArray(recentTrades) ? recentTrades : []) {
    if (String(t.event || '').toUpperCase() === 'CLOSE' && t.id) {
      closedIds.add(String(t.id));
    }
  }
  for (const t of Array.isArray(recentTrades) ? recentTrades : []) {
    if (String(t.event || '').toUpperCase() === 'OPEN' && t.id && !closedIds.has(String(t.id))) {
      openMap.set(String(t.symbol || ''), t);
    }
  }
  return openMap;
}

function findLatestBotLatency(symbol, recentTrades) {
  let latestTime = '';
  let lat = null;
  for (const t of Array.isArray(recentTrades) ? recentTrades : []) {
    if (t.symbol !== symbol) continue;
    const v = numOrNull(t.latencyMs);
    if (v === null) continue;
    const tStr = String(t.time || '');
    if (!latestTime || tStr >= latestTime) {
      latestTime = tStr;
      lat = Math.round(v);
    }
  }
  return lat;
}

function shortStrategyLabel(str) {
  const s = String(str || '').trim();
  if (!s) return '–';
  if (s === 'DOM_ABSORPTION') return 'DOM Abs.';
  if (s === 'VWAP_EQUILIBRIUM') return 'VWAP Eq.';
  if (s === 'SMC_FIBO_5M') return 'SMC 5M';
  return s.length > 14 ? s.slice(0, 13) + '…' : s;
}

function renderBotsSection(liveStatus, overviewSummary) {
  const section = document.getElementById('bots-heartbeat-section');
  if (!section) return;

  const fleet = Array.isArray(liveStatus?.bots_fleet) ? liveStatus.bots_fleet : [];
  const summaryMeta = liveStatus?.summary || {};
  const onlineBots = fleet.filter((b) => b.is_online);
  const offlineBots = fleet.filter((b) => !b.is_online);
  const onlineCount = numOrNull(summaryMeta.online_bots) ?? onlineBots.length;

  const visibleBots = state.showOfflineBots ? fleet : onlineBots;
  const openTradesMap = findOpenTradesMap(liveStatus?.recent_trades);
  const assetsMeta = liveStatus?.market_intelligence_v4?.assets || {};
  const symSparkMap = overviewSummary?.symbols || {};

  section.innerHTML = `
    <div class="section-head-row">
      <h2 class="section-title">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--accent-green-text)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
        </svg>
        <span>Live Heartbeat – Trading Bots</span>
      </h2>
      <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap;">
        <span class="badge ${onlineCount > 0 ? 'badge-green' : 'badge-muted'}">
          <span class="pulse-dot ${onlineCount > 0 ? 'green' : 'gray'}" aria-hidden="true"></span>
          <span>${onlineCount} Bots Active</span>
        </span>
        ${offlineBots.length > 0 ? `
          <button type="button" id="toggle-offline-bots-btn" class="refresh-mini-btn" aria-pressed="${state.showOfflineBots}">
            ${state.showOfflineBots ? `ซ่อน Offline (${offlineBots.length})` : `แสดงทั้งหมด (${fleet.length})`}
          </button>
        ` : ''}
      </div>
    </div>

    ${visibleBots.length === 0 ? `
      <div style="padding:20px;text-align:center;color:var(--text-muted);font-size:13px;">ยังไม่มีข้อมูลบอทใน bots_fleet</div>
    ` : `
      <div class="bots-grid">
        ${visibleBots.map((bot) => {
          const id = String(bot.id || bot.symbol);
          const theme = botTheme(bot.symbol);
          const mi = assetsMeta[bot.symbol] || {};
          const price = numOrNull(bot.current_price) > 0 ? numOrNull(bot.current_price) : numOrNull(mi.latest_price);
          const openTrade = openTradesMap.get(bot.symbol);
          const inPos = Boolean(bot.is_online && ((numOrNull(bot.open_positions) || 0) > 0 || openTrade));
          const isOffline = !bot.is_online;
          const isExpanded = state.expandedBots.has(id);

          let statusBadge = `<span class="badge badge-muted"><span class="pulse-dot gray" aria-hidden="true"></span>OFFLINE</span>`;
          if (!isOffline) {
            statusBadge = inPos
              ? `<span class="badge badge-green"><span class="pulse-dot green" aria-hidden="true"></span>IN_POSITION</span>`
              : `<span class="badge badge-blue"><span class="pulse-dot green" aria-hidden="true"></span>SCANNING</span>`;
          }

          // Compute price delta cleanly without fabricating metrics
          let deltaHtml = missingCell('ยังไม่มีข้อมูล % เปลี่ยนแปลง');
          const explicitPct = numOrNull(bot.price_change_pct ?? mi.price_change_pct);
          const vwap = numOrNull(bot.vwap);
          if (explicitPct !== null) {
            const cls = signClass(explicitPct);
            deltaHtml = `<span class="mono ${cls}">${signArrow(explicitPct)}${escapeHtml(fmtPct(explicitPct, { signed: true, decimals: 2 }))}</span>`;
          } else if (price !== null && vwap !== null && vwap > 0) {
            const diffUsd = price - vwap;
            const diffPct = (diffUsd / vwap) * 100;
            const cls = signClass(diffUsd);
            const tip = `เทียบ Session VWAP ($${vwap.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })})`;
            deltaHtml = `<span class="mono ${cls}" title="${escapeHtml(tip)}">${signArrow(diffUsd)}${escapeHtml(fmtPct(diffPct, { signed: true, decimals: 2 }))} <span style="color:var(--text-muted);font-weight:500;">vs VWAP</span></span>`;
          }

          let bottomCells = '';
          if (inPos) {
            const entryV = openTrade?.price ?? bot.entry_price;
            const slV = openTrade?.stopLoss ?? bot.sl_price;
            const tpV = openTrade?.takeProfit ?? bot.tp_price;
            const rrV = numOrNull(bot.rr_ratio);
            bottomCells = `
              <div class="bot-mini-cell"><div class="lbl">Entry</div><div class="val mono">${entryV ? escapeHtml(String(entryV)) : missingCell()}</div></div>
              <div class="bot-mini-cell"><div class="lbl">SL</div><div class="val mono">${slV ? escapeHtml(String(slV)) : missingCell()}</div></div>
              <div class="bot-mini-cell"><div class="lbl">TP</div><div class="val mono">${tpV ? escapeHtml(String(tpV)) : missingCell()}</div></div>
              <div class="bot-mini-cell"><div class="lbl">R:R</div><div class="val mono">${rrV !== null ? `${rrV.toFixed(1)}:1` : missingCell()}</div></div>
            `;
          } else if (!isOffline) {
            const tfVal = bot.timeframe || 'M1';
            const riskVal = numOrNull(bot.risk_pct);
            bottomCells = `
              <div class="bot-mini-cell"><div class="lbl">Next Signal</div><div class="val mono val-pos" data-next-signal="m1">${formatM1Countdown()}</div></div>
              <div class="bot-mini-cell"><div class="lbl">TF</div><div class="val mono">${escapeHtml(tfVal)}</div></div>
              <div class="bot-mini-cell"><div class="lbl">Strategy</div><div class="val" title="${escapeHtml(bot.strategy || '')}">${escapeHtml(shortStrategyLabel(bot.strategy))}</div></div>
              <div class="bot-mini-cell"><div class="lbl">Risk</div><div class="val mono">${riskVal !== null ? escapeHtml(fmtPct(riskVal)) : missingCell('ยังไม่มีข้อมูล % Risk ใน live_status.json')}</div></div>
            `;
          } else {
            const wr = numOrNull(bot.win_rate);
            const pnl = numOrNull(bot.net_pnl);
            bottomCells = `
              <div class="bot-mini-cell"><div class="lbl">Trades</div><div class="val mono">${numOrNull(bot.closed_trades) ?? '–'}</div></div>
              <div class="bot-mini-cell"><div class="lbl">Win Rate</div><div class="val mono">${wr !== null ? escapeHtml(fmtPct(wr)) : missingCell()}</div></div>
              <div class="bot-mini-cell"><div class="lbl">Net PnL</div><div class="val mono ${signClass(pnl)}">${pnl !== null ? escapeHtml(fmtMoney(pnl, { signed: true })) : missingCell()}</div></div>
              <div class="bot-mini-cell"><div class="lbl">Last Beat</div><div class="val" title="${escapeHtml(bot.heartbeat_desc || '')}">${escapeHtml(bot.heartbeat_desc || 'OFFLINE')}</div></div>
            `;
          }

          const latSym = findLatestBotLatency(bot.symbol, liveStatus?.recent_trades);
          const botWr = numOrNull(bot.win_rate);
          const botPnl = numOrNull(bot.net_pnl);

          return `
            <article class="bot-card ${isOffline ? 'is-offline' : ''}" data-bot-id="${escapeHtml(id)}">
              <div class="bot-card-head">
                <div class="bot-identity">
                  <span class="bot-coin-icon" style="background:${theme.bg};color:${theme.fg};" aria-hidden="true">${theme.icon}</span>
                  <div>
                    <div class="bot-symbol-name">${escapeHtml(theme.display)}</div>
                    <div style="font-size:10.5px;color:var(--text-muted);" title="${escapeHtml(mi.primary_regime || bot.strategy || '')}">
                      ${escapeHtml(mi.primary_regime || bot.strategy || '')}
                    </div>
                  </div>
                </div>
                <div class="bot-head-actions">
                  ${statusBadge}
                  <button type="button"
                          class="bot-expand-btn"
                          data-expand-bot="${escapeHtml(id)}"
                          aria-expanded="${isExpanded}"
                          aria-label="ดูรายละเอียดบอท ${escapeHtml(theme.display)}">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" aria-hidden="true">
                      <polyline points="6 9 12 15 18 9"/>
                    </svg>
                  </button>
                </div>
              </div>

              <div class="bot-price-row">
                <div>
                  <div class="bot-price-val mono">${price !== null ? escapeHtml(fmtPrice(price, bot.symbol)) : missingCell('ราคาไม่พร้อมใช้งาน')}</div>
                  <div class="bot-price-delta">${deltaHtml}</div>
                </div>
                <div class="bot-spark-wrap" id="bot-spark-${escapeHtml(id)}"></div>
              </div>

              <div class="bot-bottom-strip">
                ${bottomCells}
              </div>

              <div class="bot-details-drawer" id="bot-drawer-${escapeHtml(id)}" ${isExpanded ? '' : 'hidden'}>
                <div style="font-weight:700;color:var(--text-primary);">${escapeHtml(bot.name || theme.display)}</div>
                ${bot.role_desc ? `<div style="color:var(--text-secondary);line-height:1.4;">${escapeHtml(bot.role_desc)}</div>` : ''}
                <div class="bot-details-grid mono">
                  <div>Heartbeat: <strong>${escapeHtml(bot.heartbeat_desc || '–')}</strong></div>
                  <div>Open Pos: <strong>${numOrNull(bot.open_positions) ?? 0}</strong></div>
                  <div>Closed / WR: <strong>${bot.closed_trades ?? 0} (${botWr !== null ? fmtPct(botWr) : '–'})</strong></div>
                  <div>Net PnL: <strong class="${signClass(botPnl)}">${botPnl !== null ? fmtMoney(botPnl, { signed: true }) : '–'}</strong></div>
                  <div>Spread / Imb: <strong>${bot.spread ?? '–'} / ${bot.imbalance ?? '–'}</strong></div>
                  <div>Latency: <strong>${latSym !== null ? `${latSym}ms` : '–'}</strong></div>
                  <div>SL / TP ($): <strong>$${bot.sl_usd ?? '–'} / $${bot.tp_usd ?? '–'}</strong></div>
                  <div>Lots: <strong>${bot.lots ?? '–'}</strong></div>
                </div>
                ${bot.defense ? `<div style="color:var(--text-muted);">🛡️ ${escapeHtml(bot.defense)}</div>` : ''}
              </div>
            </article>
          `;
        }).join('')}
      </div>
    `}
  `;

  document.getElementById('toggle-offline-bots-btn')?.addEventListener('click', () => {
    state.showOfflineBots = !state.showOfflineBots;
    renderBotsSection(state.lastData.liveStatus, state.lastData.overviewSummary);
  });

  section.querySelectorAll('[data-expand-bot]').forEach((btn) => {
    btn.addEventListener('click', () => {
      const id = btn.getAttribute('data-expand-bot');
      const drawer = document.getElementById(`bot-drawer-${id}`);
      const isOpen = state.expandedBots.has(id);
      if (isOpen) {
        state.expandedBots.delete(id);
        btn.setAttribute('aria-expanded', 'false');
        if (drawer) drawer.hidden = true;
      } else {
        state.expandedBots.add(id);
        btn.setAttribute('aria-expanded', 'true');
        if (drawer) drawer.hidden = false;
      }
    });
  });

  // Render bot sparklines after DOM is attached
  for (const bot of visibleBots) {
    const id = String(bot.id || bot.symbol);
    const theme = botTheme(bot.symbol);
    const el = document.getElementById(`bot-spark-${id}`);
    const sData = symSparkMap[bot.symbol];
    if (el && sData && Array.isArray(sData.points) && sData.points.length >= 2) {
      const pts = sData.points.map((val, idx) => ({
        y: val,
        label: sData.times?.[idx] ? String(sData.times[idx]).slice(5) : '',
        sub: 'M1 Bar',
      }));
      renderSvgSparkline(el, pts, {
        id: `bot-${id}`,
        width: 150,
        height: 48,
        stroke: bot.is_online ? theme.line : '#64748b',
        ariaLabel: `${theme.display} M1 price sparkline`,
        formatVal: (v) => fmtPrice(v, bot.symbol) ?? String(v),
      });
    } else if (el) {
      el.innerHTML = `<div style="height:100%;display:flex;align-items:center;justify-content:center;font-size:10.5px;color:var(--text-muted);border:1px dashed var(--border-subtle);border-radius:6px;">No M1 series</div>`;
    }
  }
}

function renderAlphaFunnel(foundry, overviewSummary) {
  const container = document.getElementById('card-alpha-funnel');
  if (!container) return;

  const stats = foundry?.stats || {};
  const af = overviewSummary?.alpha_funnel || {};

  const ideas = numOrNull(stats.total_hypotheses_generated ?? af.ideas_count);
  const papers = numOrNull(af.papers_count);
  const strategies = numOrNull(af.strategies_count);
  const survivors = numOrNull(stats.active_micro_forward ?? af.survivors_count);
  const screened = numOrNull(stats.survived_screening ?? af.survived_screening_count);

  const pctIdeas = (n) => (n !== null && ideas > 0 ? `${((n / ideas) * 100).toFixed(1)}%` : '–');
  const stratSubPct = strategies !== null && ideas > 0
    ? `${((strategies / ideas) * 100).toFixed(1)}%`
    : '–';
  const stratOfPapers = strategies !== null && papers > 0
    ? `${((strategies / papers) * 100).toFixed(1)}% of papers`
    : '';

  const steps = [
    {
      num: ideas !== null ? ideas.toLocaleString('en-US') : '–',
      name: 'Ideas',
      cls: 'funnel-step-blue',
      dot: '#38bdf8',
      stage: 'Idea Filtering',
      pctText: ideas !== null ? '(100%)' : '(–)',
      tip: 'สมมติฐานที่ระบบ Foundry สร้างและคัดกรองทั้งหมด (strategy_foundry.json)',
    },
    {
      num: papers !== null ? papers.toLocaleString('en-US') : '–',
      name: 'Papers',
      cls: 'funnel-step-teal',
      dot: '#14b8a6',
      stage: 'Research',
      pctText: `(${pctIdeas(papers)})`,
      tip: 'จำนวนงานวิจัยในฐานข้อมูล (papers_database.json)',
    },
    {
      num: strategies !== null ? strategies.toLocaleString('en-US') : '–',
      name: 'Strategies',
      cls: 'funnel-step-purple',
      dot: '#a855f7',
      stage: 'Validation',
      pctText: `(${stratSubPct})`,
      tip: `กลยุทธ์ในคลังจดทะเบียน (strategy_registry.json)${stratOfPapers ? ' · ' + stratOfPapers : ''}`,
    },
    {
      num: survivors !== null ? survivors.toLocaleString('en-US') : '–',
      name: 'Survivors',
      cls: 'funnel-step-gold',
      dot: '#f5b301',
      stage: 'Production',
      pctText: `(${pctIdeas(survivors)})`,
      tip: `บอทที่รอดการคัดกรอง ${screened ?? '–'} ตัว และขึ้นรัน Forward Test จริง ${survivors ?? '–'} ตัว`,
    },
  ];

  container.innerHTML = `
    <div class="section-head-row" style="margin-bottom:12px;">
      <h2 class="section-title">
        <span aria-hidden="true">🧪</span>
        <span>Alpha Funnel</span>
      </h2>
      <a href="improvement-audit.html" class="footer-legacy-link" style="font-size:11px;">ดูทฤษฎี &amp; 10 Stages (หน้า 6) →</a>
    </div>

    <div class="funnel-arrows-row">
      ${steps.map((st) => `
        <div class="funnel-step-wrap" title="${escapeHtml(st.tip)}">
          <div class="funnel-arrow-box ${st.cls}">
            <div class="funnel-num mono">${escapeHtml(st.num)}</div>
            <div class="funnel-name">${escapeHtml(st.name)}</div>
          </div>
          <div class="funnel-track-node">
            <span class="funnel-node-dot" style="background:${st.dot};" aria-hidden="true"></span>
            <div style="font-weight:700;color:var(--text-primary);font-size:11.5px;">${escapeHtml(st.stage)}</div>
            <div class="mono" style="color:var(--text-muted);font-size:11px;">${escapeHtml(st.pctText)}</div>
          </div>
        </div>
      `).join('')}
    </div>
  `;
}

function renderQuickAccess() {
  const container = document.getElementById('card-quick-access');
  if (!container) return;

  const tiles = [
    { href: 'experiment-lab.html', icon: '▶️', bg: 'rgba(56,189,248,0.16)', fg: '#38bdf8', title: 'Backtest Studio', sub: 'Experiment Lab (หน้า 4)' },
    { href: 'research-lab.html', icon: '🧠', bg: 'rgba(168,85,247,0.16)', fg: '#c084fc', title: 'Strategy Library', sub: 'Research Lab (หน้า 3)' },
    { href: 'intelligence.html', icon: '📊', bg: 'rgba(34,197,94,0.16)', fg: '#4ade80', title: 'Analytics Pro', sub: 'Intelligence (หน้า 5)' },
    { href: 'intelligence.html#reports', icon: '📑', bg: 'rgba(245,179,1,0.16)', fg: '#fbbf24', title: 'Reports Center', sub: 'Day Study & Charts (หน้า 5)' },
    { href: 'data-center.html', icon: '📡', bg: 'rgba(6,182,212,0.16)', fg: '#22d3ee', title: 'Data Manager', sub: 'Data & Paper Sim (หน้า 2)', tip: 'โหมดจำลองการเทรด (Interactive Paper Trading Simulator จากชุดข้อมูลบันทึกจริง)' },
    { href: 'improvement-audit.html', icon: '🛡️', bg: 'rgba(239,68,68,0.16)', fg: '#f87171', title: 'Risk & Audit', sub: 'Improvement & Audit (หน้า 6)' },
    { href: 'database.html', icon: '🗄️', bg: 'rgba(148,163,184,0.18)', fg: '#cbd5e1', title: 'Unified Database', sub: 'ฐานข้อมูลรวม (หน้า 8)' },
    { href: 'archive-system.html', icon: '📦', bg: 'rgba(168,85,247,0.16)', fg: '#a855f7', title: 'Archive & Docs', sub: 'Transcript, Feedback (หน้า 7)' },
  ];

  container.innerHTML = `
    <div class="section-head-row" style="margin-bottom:12px;">
      <h2 class="section-title">
        <span aria-hidden="true">⚡</span>
        <span>Quick Access</span>
      </h2>
      <span style="font-size:11px;color:var(--text-muted);">ทางลัด 8 หมวดหลัก</span>
    </div>

    <div class="quick-grid">
      ${tiles.map((t) => `
        <a href="${escapeHtml(t.href)}" class="quick-tile" title="${escapeHtml(t.tip || t.sub)}">
          <div class="quick-tile-top">
            <span class="quick-tile-icon" style="background:${t.bg};color:${t.fg};" aria-hidden="true">${t.icon}</span>
            <span>${escapeHtml(t.title)}</span>
          </div>
          <div class="quick-tile-sub">${escapeHtml(t.sub)}</div>
        </a>
      `).join('')}
    </div>

    <a href="data-center.html" style="display:flex;align-items:center;justify-content:space-between;gap:8px;margin-top:10px;padding:7px 10px;border-radius:8px;background:var(--accent-blue-bg);border:1px solid var(--accent-blue-border);font-size:11px;color:var(--accent-blue-text);font-weight:600;">
      <span>📡 โหมดจำลองการเทรด (Interactive Paper Trading Simulator จากชุดข้อมูลบันทึกจริง)</span>
      <span aria-hidden="true">→</span>
    </a>
  `;
}

async function fetchJsonSafe(path, label, failedSources) {
  const bust = `?t=${Date.now()}`;
  try {
    const res = await fetch(`${path}${bust}`, { cache: 'no-store' });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (_) {
    failedSources.push(label);
    return null;
  }
}

async function loadAndRenderOverview() {
  const failedSources = [];
  const [
    overviewSummary,
    liveStatus,
    watchdog,
    webAlerts,
    truthGuard,
    foundry,
    championRegistry,
  ] = await Promise.all([
    fetchJsonSafe('data/overview_summary.json', 'overview_summary', failedSources),
    fetchJsonSafe('data/live_status.json', 'live_status', failedSources),
    fetchJsonSafe('data/watchdog_status.json', 'watchdog_status', failedSources),
    fetchJsonSafe('data/web_alerts.json', 'web_alerts', failedSources),
    fetchJsonSafe('data/truth_guard.json', 'truth_guard', failedSources),
    fetchJsonSafe('data/strategy_foundry.json', 'strategy_foundry', failedSources),
    fetchJsonSafe('data/champion_registry.json', 'champion_registry', failedSources),
  ]);

  // Preserve previous good snapshots if an individual fetch fails transiently
  if (overviewSummary) state.lastData.overviewSummary = overviewSummary;
  if (liveStatus) state.lastData.liveStatus = liveStatus;
  if (watchdog) state.lastData.watchdog = watchdog;
  if (webAlerts) state.lastData.webAlerts = webAlerts;
  if (truthGuard) state.lastData.truthGuard = truthGuard;
  if (foundry) state.lastData.foundry = foundry;
  if (championRegistry) state.lastData.championRegistry = championRegistry;
  state.failedSources = failedSources;

  updateShellTelemetry({
    watchdog: state.lastData.watchdog,
    webAlerts: state.lastData.webAlerts,
    liveStatus: state.lastData.liveStatus,
    overviewSummary: state.lastData.overviewSummary,
    failedSources,
  });

  renderLiveDemoCard(state.lastData.liveStatus, state.lastData.truthGuard, state.lastData.overviewSummary);
  renderChampionCard(state.lastData.championRegistry, state.lastData.overviewSummary);
  renderBotsSection(state.lastData.liveStatus, state.lastData.overviewSummary);
  renderAlphaFunnel(state.lastData.foundry, state.lastData.overviewSummary);
  renderQuickAccess();

  const refreshEl = document.getElementById('overview-last-refresh');
  if (refreshEl) {
    const rel = formatRelativeTime(state.lastData.liveStatus?.timestamp_utc);
    refreshEl.textContent = `Data sync: ${rel.short}`;
    refreshEl.title = `Source timestamp: ${rel.full}`;
  }
}

function initOverview() {
  mountShell({
    activePage: 'index.html',
    onRetry: loadAndRenderOverview,
  });

  renderQuickAccess();
  document.getElementById('overview-manual-refresh')?.addEventListener('click', () => {
    loadAndRenderOverview();
  });

  loadAndRenderOverview();

  if (refreshTimer) clearInterval(refreshTimer);
  refreshTimer = setInterval(loadAndRenderOverview, REFRESH_INTERVAL_MS);

  if (signalTimer) clearInterval(signalTimer);
  signalTimer = setInterval(() => {
    const nextTxt = formatM1Countdown();
    document.querySelectorAll('[data-next-signal="m1"]').forEach((el) => {
      el.textContent = nextTxt;
    });
  }, 1000);
}

initOverview();
