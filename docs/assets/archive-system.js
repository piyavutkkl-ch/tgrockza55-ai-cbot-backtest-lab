/* ==========================================================================
   QuantGuard / Antigravity Quant — Page 7: Archive / System & Visual Feedback Studio
   ES Module integrated cleanly with shared shell.js & shell.css
   ========================================================================== */

import { mountShell, updateShellTelemetry, escapeHtml } from './shell.js';

const STORAGE_TICKETS_KEY = 'agq_feedback_tasks';

const state = {
  summary: null,
  live: null,
  watchdog: null,
  alerts: null,
  truthGuard: null,
  ruleMatrix: null,
  overviewSummary: null,
  failedSources: [],

  activeMainTab: 'studio',
  activeInspectorTab: 'details',
  activeTranscriptMode: 'chat',
  activeLegacySource: 'strategies',

  logs: [],
  selectedLogId: null,
  tickets: [],

  studioMode: 'inspect',
  selectedSelector: 'div.risk-card:nth-child(1)',
  selectedLabel: '24/7 Watchdog & Risk Governor',
  selectedEl: null,
  uploadedImageDataUrl: null,
  customCropRect: null,
};

function $(id) {
  return document.getElementById(id);
}

function isLightTheme() {
  return document.documentElement.getAttribute('data-theme') === 'light';
}

function pad2(n) {
  return String(n).padStart(2, '0');
}

function formatUtcShort(iso) {
  if (!iso) return '–';
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return String(iso);
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  return `${months[d.getUTCMonth()]} ${pad2(d.getUTCDate())}, ${d.getUTCFullYear()} ${pad2(d.getUTCHours())}:${pad2(d.getUTCMinutes())}:${pad2(d.getUTCSeconds())} UTC`;
}

function loadTicketsFromStorage() {
  try {
    const raw = localStorage.getItem(STORAGE_TICKETS_KEY);
    const parsed = raw ? JSON.parse(raw) : [];
    return Array.isArray(parsed) ? parsed : [];
  } catch (_) {
    return [];
  }
}

function saveTicketsToStorage(list) {
  try {
    localStorage.setItem(STORAGE_TICKETS_KEY, JSON.stringify(list.slice(0, 40)));
  } catch (_) {}
}

async function safeCopyText(text) {
  try {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      await navigator.clipboard.writeText(text);
      return true;
    }
  } catch (_) {}
  try {
    const ta = document.createElement('textarea');
    ta.value = text;
    ta.style.position = 'fixed';
    ta.style.opacity = '0';
    document.body.appendChild(ta);
    ta.select();
    document.execCommand('copy');
    ta.remove();
    return true;
  } catch (_) {
    return false;
  }
}

async function fetchJsonSafe(relPath, label, required = false) {
  const sep = relPath.includes('?') ? '&' : '?';
  try {
    const res = await fetch(`${relPath}${sep}t=${Date.now()}`, { cache: 'no-store' });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    state.failedSources.push(label);
    if (required) throw err;
    return null;
  }
}

/* ------------------------------------------------------------------------ */
/* WORKSPACE TELEMETRY + EMBEDDED STAGE METRICS                             */
/* ------------------------------------------------------------------------ */
function updateCutoffCardTimer() {
  const now = new Date();
  const target = new Date(now.getTime());
  target.setUTCHours(21, 45, 0, 0);
  if (target.getTime() <= now.getTime()) {
    target.setUTCDate(target.getUTCDate() + 1);
  }
  const remSec = Math.max(0, Math.floor((target.getTime() - now.getTime()) / 1000));
  const rh = Math.floor(remSec / 3600);
  const rm = Math.floor((remSec % 3600) / 60);
  if ($('card-cutoff-remaining')) {
    $('card-cutoff-remaining').textContent = `${rh}h ${pad2(rm)}m`;
  }
}

function renderWorkspaceTelemetry() {
  const live = state.live || state.summary?.live_snapshot || {};
  const wd = state.watchdog || state.summary?.governance_and_privacy?.watchdog_status || {};
  const matrix = state.ruleMatrix || state.summary?.governance_and_privacy?.rule_matrix || {};

  const fw = live.forward_trading || {};
  const assets = live.assets || live.market_intelligence_v4?.assets || {};
  const xau = assets.XAUUSD || {};
  const overallWd = wd.overall_status || 'UNKNOWN';

  const xauPrice = xau.latest_price != null
    ? Number(xau.latest_price).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
    : '–';
  const equity = fw.equity != null ? `$${Number(fw.equity).toFixed(2)}` : '–';
  const netPnl = fw.net_pnl != null ? `${fw.net_pnl >= 0 ? '+' : '-'}$${Math.abs(Number(fw.net_pnl)).toFixed(2)}` : '–';
  const netPct = fw.net_pnl_pct != null ? `(${fw.net_pnl_pct >= 0 ? '+' : ''}${Number(fw.net_pnl_pct).toFixed(1)}%)` : '';
  const pnlColor = (fw.net_pnl || 0) >= 0 ? 'var(--green)' : 'var(--red)';

  if ($('ws-xau-price')) $('ws-xau-price').textContent = xauPrice;
  if ($('ws-equity')) $('ws-equity').textContent = equity;
  if ($('ws-pnl')) {
    $('ws-pnl').textContent = `${netPnl} ${netPct}`.trim();
    $('ws-pnl').style.color = pnlColor;
  }

  if ($('stage-xau-val')) $('stage-xau-val').textContent = xauPrice;
  if ($('stage-eq-val')) $('stage-eq-val').textContent = equity;
  if ($('stage-pnl-val')) {
    $('stage-pnl-val').textContent = `${netPnl} ${netPct}`.trim();
    $('stage-pnl-val').style.color = pnlColor;
  }

  // Risk Governor Card (real ceiling from rule_classification_matrix.json)
  const ceiling = matrix?.tier_1_immutable_hard_constraints?.rules?.portfolio_daily_loss_ceiling_usd?.value || 10.0;
  const latestNegTrades = (live.recent_closed_deals || []).filter((d) => Number(d.net) < 0);
  const worstLoss = latestNegTrades.length ? Math.abs(Math.min(...latestNegTrades.map((d) => Number(d.net)))) : 0;
  const ratio = Math.min(1, worstLoss / ceiling);

  if ($('risk-loss-val')) $('risk-loss-val').textContent = `-$${worstLoss.toFixed(2)}`;
  if ($('risk-limit-val')) $('risk-limit-val').textContent = `/ -$${ceiling.toFixed(2)} ceiling`;
  if ($('risk-footer-text')) {
    $('risk-footer-text').innerHTML = `Max Single Deal Loss: <strong class="mono" style="color:var(--cyan);">-$${worstLoss.toFixed(2)} / -$${ceiling.toFixed(2)}</strong>`;
  }

  const riskBadge = $('risk-card-status');
  if (riskBadge) {
    const stalled = overallWd !== 'OK';
    riskBadge.textContent = stalled ? 'WATCHDOG ALERT' : 'ACTIVE';
    riskBadge.className = 'status-pill-sm' + (stalled ? ' crit' : '');
  }

  if ($('stage-health-badge')) {
    $('stage-health-badge').textContent = overallWd === 'OK' ? 'System Healthy' : `Watchdog: ${overallWd}`;
    $('stage-health-badge').style.color = overallWd === 'OK' ? 'var(--green)' : 'var(--amber)';
  }

  // SVG Semicircle Gauge Needle
  const angle = Math.PI * (1 - ratio);
  const nx = 100 + 78 * Math.cos(angle);
  const ny = 96 - 78 * Math.sin(angle);
  const needle = $('risk-gauge-needle');
  if (needle) {
    needle.setAttribute('cx', nx.toFixed(1));
    needle.setAttribute('cy', ny.toFixed(1));
  }
}

function renderLifecycleTrack() {
  const track = $('lifecycle-track');
  if (!track) return;
  const snap = state.summary?.live_snapshot || {};
  const activeStage = Number(snap.flywheel_stage_number) || 7;
  const cycleNum = snap.active_cycle || 328;

  if ($('stage-cycle-pill')) {
    $('stage-cycle-pill').textContent = `Cycle #${cycleNum} · Stage ${activeStage}`;
  }

  const stages = [
    { n: 1, name: 'Data Pipe', desc: 'Collect Markets' },
    { n: 2, name: 'Feature Eng', desc: 'Prepare Signals' },
    { n: 3, name: 'Strategy Core', desc: 'Generate Alpha' },
    { n: 4, name: 'Backtest', desc: 'Validate Logic' },
    { n: 5, name: 'Paper Trade', desc: 'Simulate Live' },
    { n: 6, name: 'Risk Check', desc: 'Assess Exposure' },
    { n: 7, name: 'Live Deploy', desc: 'Run with Guard' },
    { n: 8, name: 'Monitor', desc: 'Track & Alert' },
    { n: 9, name: 'Review', desc: 'Analyze Results' },
    { n: 10, name: 'Feedback', desc: 'Improve System' },
  ];

  const displayStage = 7;
  track.innerHTML = stages
    .map((s) => {
      const cls = s.n < displayStage ? 'done' : s.n === displayStage ? 'current' : 'pending';
      const inner = s.n < displayStage ? '✓' : String(s.n);
      return `
        <div class="stage-node ${cls}" title="Stage ${s.n}: ${escapeHtml(s.name)} — ${escapeHtml(s.desc)}">
          <div class="stage-circle">${inner}</div>
          <div class="stage-name">${s.n}. ${escapeHtml(s.name)}</div>
          <div class="stage-desc">${escapeHtml(s.desc)}</div>
        </div>`;
    })
    .join('');
}

/* ------------------------------------------------------------------------ */
/* TAB NAVIGATION                                                           */
/* ------------------------------------------------------------------------ */
function switchMainTab(tabName) {
  state.activeMainTab = tabName;
  document.querySelectorAll('.ws-tab').forEach((btn) => {
    const active = btn.dataset.tab === tabName;
    btn.classList.toggle('active', active);
    btn.setAttribute('aria-selected', active ? 'true' : 'false');
  });
  document.querySelectorAll('.tab-panel').forEach((panel) => {
    panel.classList.toggle('active', panel.id === `panel-${tabName}`);
  });
  if (tabName === 'studio') {
    requestAnimationFrame(() => {
      positionSelectionOverlay();
      drawElementThumbnail();
    });
  }
}

function initTabs() {
  document.querySelectorAll('.ws-tab').forEach((btn) => {
    btn.addEventListener('click', () => switchMainTab(btn.dataset.tab));
  });

  const params = new URLSearchParams(window.location.search);
  const qTab = params.get('tab');
  if (qTab && ['transcript', 'legacy', 'studio', 'governance'].includes(qTab)) {
    switchMainTab(qTab);
  }
}

/* ------------------------------------------------------------------------ */
/* STUDIO: RESEARCH LOGS ARCHIVE + INSPECTOR                                */
/* ------------------------------------------------------------------------ */
function buildCombinedLogs() {
  const baseLogs = Array.isArray(state.summary?.archive_logs_feed)
    ? state.summary.archive_logs_feed.slice()
    : [];

  const ticketLogs = state.tickets.map((t) => ({
    id: t.id,
    category: 'ui',
    dot_color: 'cyan',
    title: `UI Fix: ${t.component || t.selector}`,
    timestamp_utc: t.created_at,
    badge: 'TICKET',
    summary: t.instruction,
    details_lines: [
      { ts: String(t.created_at).slice(0, 19).replace('T', ' '), level: 'INFO', msg: `UI: Selected element: ${t.selector}` },
      { ts: String(t.created_at).slice(0, 19).replace('T', ' '), level: 'INFO', msg: `Action: Add annotation — "${t.instruction}"` },
      { ts: String(t.created_at).slice(0, 19).replace('T', ' '), level: 'SUCCESS', msg: `Feedback sent. Ticket ID: ${t.id}` },
      { ts: String(t.created_at).slice(0, 19).replace('T', ' '), level: 'INFO', msg: 'Status: Ready for AI prompt execution' },
    ],
    payload_json: {
      ticket_id: t.id,
      page: t.page,
      selector: t.selector,
      instruction: t.instruction,
      created_at: t.created_at,
    },
    diff: {
      baseline_label: 'Current DOM',
      current_label: 'Requested UI Fix',
      rows: [
        { field: 'Target Selector', baseline: t.selector, current: 'Patched Component', delta: 'PENDING AI' },
        { field: 'Directive', baseline: 'Existing UI state', current: t.instruction, delta: t.id },
      ],
    },
  }));

  state.logs = [...ticketLogs, ...baseLogs];
  if (!state.selectedLogId && state.logs.length) {
    state.selectedLogId = state.logs[0].id;
  }
}

function renderLogsList() {
  const container = $('archive-logs-list');
  if (!container) return;

  const query = ($('archive-log-search')?.value || '').trim().toLowerCase();
  const cat = $('archive-log-filter')?.value || 'all';

  const filtered = state.logs.filter((item) => {
    if (cat !== 'all' && item.category !== cat) return false;
    if (!query) return true;
    const hay = `${item.title} ${item.summary} ${item.timestamp_utc} ${item.id}`.toLowerCase();
    return hay.includes(query);
  });

  if ($('archive-total-badge')) {
    $('archive-total-badge').textContent = `Total: ${state.logs.length} logs`;
  }

  if (!filtered.length) {
    container.innerHTML = `<div style="padding:20px; text-align:center; color:var(--text-muted); font-size:12px;">No matching archived logs found.</div>`;
    return;
  }

  container.innerHTML = filtered
    .map((item) => {
      const active = item.id === state.selectedLogId;
      return `
        <button type="button" class="log-item ${active ? 'active' : ''}" data-log-id="${escapeHtml(item.id)}" role="option" aria-selected="${active ? 'true' : 'false'}">
          <div class="log-item-left">
            <span class="ring-dot ${escapeHtml(item.dot_color || 'cyan')}"></span>
            <div style="min-width:0;">
              <div class="log-item-title">${escapeHtml(item.title)}</div>
              <div class="log-item-time">${escapeHtml(formatUtcShort(item.timestamp_utc))}</div>
            </div>
          </div>
          <span class="log-item-chevron" aria-hidden="true">›</span>
        </button>`;
    })
    .join('');

  container.querySelectorAll('.log-item').forEach((btn) => {
    btn.addEventListener('click', () => {
      state.selectedLogId = btn.dataset.logId;
      renderLogsList();
      renderInspectorBody();
    });
  });
}

function getSelectedLog() {
  return state.logs.find((l) => l.id === state.selectedLogId) || state.logs[0] || null;
}

function buildAiFixPrompt(ticket) {
  return [
    `### [${ticket.id}] Visual Feedback Studio — UI Fix Directive`,
    `- **Target Page**: \`${ticket.page}\``,
    `- **DOM Selector**: \`${ticket.selector}\``,
    `- **Component**: ${ticket.component}`,
    `- **Requested Fix**:`,
    `  > "${ticket.instruction}"`,
    `- **Timestamp**: ${ticket.created_at}`,
  ].join('\n');
}

function getInspectorExportText() {
  const log = getSelectedLog();
  if (!log) return '';
  if (state.activeInspectorTab === 'details') {
    return (log.details_lines || [])
      .map((l) => `[${l.ts}] ${String(l.level || 'INFO').padEnd(7)} ${l.msg}`)
      .join('\n');
  }
  if (state.activeInspectorTab === 'json') {
    return JSON.stringify(log.payload_json || log, null, 2);
  }
  if (state.activeInspectorTab === 'diff') {
    return JSON.stringify(log.diff || { note: 'No structured diff for this log entry.' }, null, 2);
  }
  return JSON.stringify(
    state.tickets.map((t) => ({ id: t.id, selector: t.selector, instruction: t.instruction, created_at: t.created_at })),
    null,
    2
  );
}

function renderInspectorBody() {
  const body = $('inspector-body');
  if (!body) return;
  const log = getSelectedLog();

  if ($('insp-ticket-count')) $('insp-ticket-count').textContent = String(state.tickets.length);
  if ($('pill-count-tickets')) $('pill-count-tickets').textContent = String(state.tickets.length);

  if (state.activeInspectorTab === 'details') {
    if (!log) {
      body.innerHTML = '<div style="color:var(--text-muted);">Select an archive log to inspect telemetry details.</div>';
      return;
    }
    const lines = log.details_lines || [];
    body.innerHTML = lines
      .map(
        (l) => `
        <div class="log-line">
          <span class="log-ts">[${escapeHtml(l.ts)}]</span>
          <span class="log-lvl ${escapeHtml(l.level)}">${escapeHtml(l.level)}</span>
          <span class="log-msg">${escapeHtml(l.msg)}</span>
        </div>`
      )
      .join('');
    return;
  }

  if (state.activeInspectorTab === 'json') {
    const text = log ? JSON.stringify(log.payload_json || log, null, 2) : '{}';
    body.innerHTML = `<pre class="json-pre">${escapeHtml(text)}</pre>`;
    return;
  }

  if (state.activeInspectorTab === 'diff') {
    if (!log || !log.diff || !Array.isArray(log.diff.rows)) {
      body.innerHTML = `<div style="color:var(--text-muted); padding:8px 0;">No metric or policy diff attached to <strong class="mono">${escapeHtml(log?.id || 'this item')}</strong>. Select a Risk, Cycle, Experiment, or UI Fix entry to compare baseline vs current state.</div>`;
      return;
    }
    body.innerHTML = `
      <table class="diff-table">
        <thead>
          <tr>
            <th>Field / Metric</th>
            <th>${escapeHtml(log.diff.baseline_label || 'Baseline')}</th>
            <th>${escapeHtml(log.diff.current_label || 'Current')}</th>
            <th>Delta / Status</th>
          </tr>
        </thead>
        <tbody>
          ${log.diff.rows
            .map(
              (r) => `
            <tr>
              <td><strong>${escapeHtml(r.field)}</strong></td>
              <td class="mono" style="color:var(--text-secondary);">${escapeHtml(r.baseline)}</td>
              <td class="mono">${escapeHtml(r.current)}</td>
              <td class="mono" style="color:var(--cyan); font-weight:700;">${escapeHtml(r.delta)}</td>
            </tr>`
            )
            .join('')}
        </tbody>
      </table>`;
    return;
  }

  if (!state.tickets.length) {
    body.innerHTML = `<div style="color:var(--text-muted); padding:10px 0;">No UI Fix requests captured yet. Select a dashboard card or drag-crop an area above, enter a note, and click <strong style="color:var(--cyan);">Send UI Fix to AI</strong>.</div>`;
    return;
  }

  body.innerHTML = `
    <div class="screenshots-grid">
      ${state.tickets
        .map(
          (t) => `
        <div class="ticket-card">
          ${t.imageUrl ? `<img class="ticket-thumb" src="${escapeHtml(t.imageUrl)}" alt="Captured snapshot for ${escapeHtml(t.id)}">` : ''}
          <div style="display:flex; justify-content:space-between; align-items:center; gap:6px;">
            <span class="mono" style="font-size:11px; color:var(--green); font-weight:700;">${escapeHtml(t.id)}</span>
            <span class="mono" style="font-size:10px; color:var(--text-muted);">${escapeHtml(formatUtcShort(t.created_at).slice(0, 18))}</span>
          </div>
          <code class="selector-tag-input" style="font-size:10px;">${escapeHtml(t.selector)}</code>
          <div style="font-size:12px; color:var(--text-primary); line-height:1.4;">${escapeHtml(t.instruction)}</div>
          <div style="display:flex; gap:6px; margin-top:auto;">
            <button type="button" class="tool-btn btn-copy-ticket" data-tid="${escapeHtml(t.id)}" style="flex:1; justify-content:center;">Copy AI Prompt</button>
            <button type="button" class="tool-btn btn-del-ticket" data-tid="${escapeHtml(t.id)}" style="color:var(--red);">Delete</button>
          </div>
        </div>`
        )
        .join('')}
    </div>`;

  body.querySelectorAll('.btn-copy-ticket').forEach((b) => {
    b.addEventListener('click', async () => {
      const t = state.tickets.find((x) => x.id === b.dataset.tid);
      if (!t) return;
      await safeCopyText(buildAiFixPrompt(t));
      showToast('AI Fix Prompt Copied', `Ticket: ${t.id}`);
    });
  });

  body.querySelectorAll('.btn-del-ticket').forEach((b) => {
    b.addEventListener('click', () => {
      state.tickets = state.tickets.filter((x) => x.id !== b.dataset.tid);
      saveTicketsToStorage(state.tickets);
      buildCombinedLogs();
      renderLogsList();
      renderInspectorBody();
    });
  });
}

/* ------------------------------------------------------------------------ */
/* VISUAL FEEDBACK STUDIO: BOUNDING BOX, CONNECTOR, THUMBNAIL, SEND TO AI   */
/* ------------------------------------------------------------------------ */
function positionSelectionOverlay() {
  const wrap = $('studio-stage-wrap');
  const box = $('cyan-selection-box');
  const line = $('connector-line');
  const popover = $('annotation-popover');
  if (!wrap || !box) return;

  const wrapRect = wrap.getBoundingClientRect();

  if (state.customCropRect && state.uploadedImageDataUrl) {
    box.style.display = 'block';
    box.style.left = `${state.customCropRect.x}px`;
    box.style.top = `${state.customCropRect.y}px`;
    box.style.width = `${state.customCropRect.w}px`;
    box.style.height = `${state.customCropRect.h}px`;
  } else {
    const target = state.selectedEl || $('target-risk-card');
    if (!target || $('embedded-frame')?.style.display === 'none') {
      box.style.display = 'none';
      if (line) line.setAttribute('opacity', '0');
      return;
    }
    const tRect = target.getBoundingClientRect();
    if (tRect.width === 0 || tRect.height === 0) {
      box.style.display = 'none';
      return;
    }
    box.style.display = 'block';
    box.style.left = `${tRect.left - wrapRect.left - 3}px`;
    box.style.top = `${tRect.top - wrapRect.top - 3}px`;
    box.style.width = `${tRect.width + 6}px`;
    box.style.height = `${tRect.height + 6}px`;
  }

  if ($('selection-tag-pill')) $('selection-tag-pill').textContent = state.selectedSelector;
  if ($('toolbar-selector-chip')) $('toolbar-selector-chip').textContent = state.selectedSelector;
  if ($('popover-selector-input')) $('popover-selector-input').value = state.selectedSelector;

  if (line && popover && popover.style.display !== 'none' && window.innerWidth > 900) {
    const bLeft = parseFloat(box.style.left) || 0;
    const bTop = parseFloat(box.style.top) || 0;
    const bW = parseFloat(box.style.width) || 0;
    const bH = parseFloat(box.style.height) || 0;

    const pRect = popover.getBoundingClientRect();
    const x1 = pRect.left - wrapRect.left;
    const y1 = pRect.top - wrapRect.top + 38;
    const x2 = bLeft + bW + 4;
    const y2 = bTop + bH * 0.5;

    line.setAttribute('x1', x1.toFixed(1));
    line.setAttribute('y1', y1.toFixed(1));
    line.setAttribute('x2', x2.toFixed(1));
    line.setAttribute('y2', y2.toFixed(1));
    line.setAttribute('opacity', '0.92');
  } else if (line) {
    line.setAttribute('opacity', '0');
  }
}

function drawElementThumbnail() {
  const canvas = $('popover-thumb-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const w = canvas.width;
  const h = canvas.height;
  const isLight = isLightTheme();

  ctx.clearRect(0, 0, w, h);

  if (state.uploadedImageDataUrl && state.customCropRect) {
    const img = $('uploaded-preview-img');
    if (img && img.complete && img.naturalWidth > 0) {
      const imgRect = img.getBoundingClientRect();
      const wrapRect = $('studio-stage-wrap').getBoundingClientRect();
      const sxRatio = img.naturalWidth / (imgRect.width || 1);
      const syRatio = img.naturalHeight / (imgRect.height || 1);
      const sx = Math.max(0, (state.customCropRect.x - (imgRect.left - wrapRect.left)) * sxRatio);
      const sy = Math.max(0, (state.customCropRect.y - (imgRect.top - wrapRect.top)) * syRatio);
      const sw = Math.max(10, state.customCropRect.w * sxRatio);
      const sh = Math.max(10, state.customCropRect.h * syRatio);
      ctx.drawImage(img, sx, sy, sw, sh, 0, 0, w, h);
      if ($('popover-thumb-dims')) {
        $('popover-thumb-dims').textContent = `${Math.round(state.customCropRect.w)}×${Math.round(state.customCropRect.h)}px Crop`;
      }
      return;
    }
  }

  ctx.fillStyle = isLight ? '#F8FAFC' : '#0B0E14';
  ctx.fillRect(0, 0, w, h);
  ctx.strokeStyle = isLight ? '#CBD5E1' : '#1E293B';
  ctx.lineWidth = 2;
  ctx.strokeRect(1, 1, w - 2, h - 2);

  const sel = state.selectedSelector;
  if (sel.includes('risk-card')) {
    ctx.fillStyle = isLight ? '#0F172A' : '#E2E8F0';
    ctx.font = 'bold 10px sans-serif';
    ctx.fillText('24/7 Watchdog & Risk Governor', 12, 20);

    const grad = ctx.createLinearGradient(40, 95, 180, 95);
    grad.addColorStop(0, '#22C55E');
    grad.addColorStop(0.55, '#F59E0B');
    grad.addColorStop(1, '#EF4444');
    ctx.beginPath();
    ctx.arc(w / 2, 102, 50, Math.PI, 0, false);
    ctx.strokeStyle = grad;
    ctx.lineWidth = 10;
    ctx.lineCap = 'round';
    ctx.stroke();

    ctx.fillStyle = isLight ? '#0F172A' : '#FFFFFF';
    ctx.font = 'bold 18px monospace';
    ctx.textAlign = 'center';
    ctx.fillText($('risk-loss-val')?.textContent || '-$2.68', w / 2, 96);
    ctx.fillStyle = '#94A3B8';
    ctx.font = '10px monospace';
    ctx.fillText($('risk-limit-val')?.textContent || '/ -$10.00', w / 2, 114);
    ctx.textAlign = 'left';
    if ($('popover-thumb-dims')) $('popover-thumb-dims').textContent = 'Risk Card · Live SVG';
  } else if (sel.includes('cutoff-card')) {
    ctx.fillStyle = isLight ? '#0F172A' : '#E2E8F0';
    ctx.font = 'bold 11px sans-serif';
    ctx.fillText('Flat Cutoff (Tier-1)', 14, 22);
    ctx.fillStyle = isLight ? '#0284C7' : '#22D3EE';
    ctx.font = 'bold 26px monospace';
    ctx.textAlign = 'center';
    ctx.fillText('21:45:00', w / 2, 84);
    ctx.fillStyle = '#94A3B8';
    ctx.font = 'bold 11px monospace';
    ctx.fillText('UTC', w / 2, 104);
    ctx.textAlign = 'left';
    if ($('popover-thumb-dims')) $('popover-thumb-dims').textContent = 'Cutoff Card · Live DOM';
  } else {
    ctx.fillStyle = isLight ? '#0F172A' : '#E2E8F0';
    ctx.font = 'bold 10px sans-serif';
    ctx.fillText('10-Stage Institutional Lifecycle', 12, 22);
    for (let i = 0; i < 10; i += 1) {
      const cx = 18 + i * 20;
      ctx.beginPath();
      ctx.arc(cx, 75, 7, 0, Math.PI * 2);
      ctx.fillStyle = i === 6 ? '#06B6D4' : i < 6 ? '#22C55E' : '#334155';
      ctx.fill();
      ctx.fillStyle = '#FFFFFF';
      ctx.font = 'bold 8px monospace';
      ctx.textAlign = 'center';
      ctx.fillText(String(i + 1), cx, 78);
    }
    ctx.textAlign = 'left';
    if ($('popover-thumb-dims')) $('popover-thumb-dims').textContent = 'Lifecycle · 10 Nodes';
  }
}

function showToast(title, sub) {
  const toast = $('studio-toast');
  if (!toast) return;
  if ($('toast-title')) $('toast-title').textContent = title;
  if ($('toast-sub')) $('toast-sub').textContent = sub;
  toast.classList.add('show');
  clearTimeout(showToast._timer);
  showToast._timer = setTimeout(() => {
    toast.classList.remove('show');
  }, 4500);
}

function initStudioInteractions() {
  state.selectedEl = $('target-risk-card');

  document.querySelectorAll('.inspectable').forEach((el) => {
    el.addEventListener('click', (e) => {
      if (state.studioMode !== 'inspect') return;
      e.stopPropagation();
      state.selectedEl = el;
      state.selectedSelector = el.dataset.selector || 'div.inspectable';
      state.selectedLabel = el.dataset.label || 'Dashboard Component';
      state.customCropRect = null;

      if ($('annotation-popover')) $('annotation-popover').style.display = 'block';
      if ($('btn-reopen-popover')) $('btn-reopen-popover').style.display = 'none';

      positionSelectionOverlay();
      drawElementThumbnail();
    });
  });

  const btnInspect = $('mode-inspect-btn');
  const btnCrop = $('mode-crop-btn');
  const cropOverlay = $('crop-overlay-layer');
  const marquee = $('crop-marquee');

  function setStudioMode(mode) {
    state.studioMode = mode;
    if (btnInspect) btnInspect.classList.toggle('active', mode === 'inspect');
    if (btnCrop) btnCrop.classList.toggle('active', mode === 'crop');
    if (cropOverlay) cropOverlay.classList.toggle('active', mode === 'crop');
  }

  if (btnInspect) btnInspect.addEventListener('click', () => setStudioMode('inspect'));
  if (btnCrop) btnCrop.addEventListener('click', () => setStudioMode(state.studioMode === 'crop' ? 'inspect' : 'crop'));

  if (cropOverlay && marquee) {
    let dragging = false;
    let startX = 0;
    let startY = 0;
    let curRect = { x: 0, y: 0, w: 0, h: 0 };

    cropOverlay.addEventListener('mousedown', (e) => {
      const rect = cropOverlay.getBoundingClientRect();
      dragging = true;
      startX = e.clientX - rect.left;
      startY = e.clientY - rect.top;
      marquee.style.display = 'block';
      marquee.style.left = `${startX}px`;
      marquee.style.top = `${startY}px`;
      marquee.style.width = '0px';
      marquee.style.height = '0px';
    });

    cropOverlay.addEventListener('mousemove', (e) => {
      if (!dragging) return;
      const rect = cropOverlay.getBoundingClientRect();
      const cx = e.clientX - rect.left;
      const cy = e.clientY - rect.top;
      curRect = {
        x: Math.min(startX, cx),
        y: Math.min(startY, cy),
        w: Math.abs(cx - startX),
        h: Math.abs(cy - startY),
      };
      marquee.style.left = `${curRect.x}px`;
      marquee.style.top = `${curRect.y}px`;
      marquee.style.width = `${curRect.w}px`;
      marquee.style.height = `${curRect.h}px`;
    });

    window.addEventListener('mouseup', () => {
      if (!dragging) return;
      dragging = false;
      marquee.style.display = 'none';
      if (curRect.w >= 24 && curRect.h >= 24) {
        state.customCropRect = { ...curRect };
        state.selectedSelector = `crop-region[x:${Math.round(curRect.x)},y:${Math.round(curRect.y)},${Math.round(curRect.w)}x${Math.round(curRect.h)}]`;
        state.selectedLabel = 'Cropped Canvas Region';
        setStudioMode('inspect');
        if ($('annotation-popover')) $('annotation-popover').style.display = 'block';
        if ($('btn-reopen-popover')) $('btn-reopen-popover').style.display = 'none';
        positionSelectionOverlay();
        drawElementThumbnail();
      }
    });
  }

  function loadUploadedDataUrl(dataUrl) {
    state.uploadedImageDataUrl = dataUrl;
    const upStage = $('uploaded-image-stage');
    const img = $('uploaded-preview-img');
    const emb = $('embedded-frame');
    if (img && upStage && emb) {
      img.onload = () => {
        state.customCropRect = { x: 24, y: 24, w: Math.min(280, upStage.clientWidth - 48), h: 160 };
        state.selectedSelector = 'uploaded-screenshot[region]';
        state.selectedLabel = 'Uploaded Screenshot';
        positionSelectionOverlay();
        drawElementThumbnail();
      };
      img.src = dataUrl;
      emb.style.display = 'none';
      upStage.classList.add('visible');
      setStudioMode('crop');
    }
  }

  if ($('studio-upload-input')) {
    $('studio-upload-input').addEventListener('change', (e) => {
      const file = e.target.files?.[0];
      if (!file) return;
      const reader = new FileReader();
      reader.onload = () => loadUploadedDataUrl(String(reader.result));
      reader.readAsDataURL(file);
    });
  }

  window.addEventListener('paste', (e) => {
    if (state.activeMainTab !== 'studio') return;
    const items = e.clipboardData?.items || [];
    for (const item of items) {
      if (item.type.startsWith('image/')) {
        const blob = item.getAsFile();
        if (blob) {
          const reader = new FileReader();
          reader.onload = () => loadUploadedDataUrl(String(reader.result));
          reader.readAsDataURL(blob);
        }
        break;
      }
    }
  });

  if ($('btn-reset-stage')) {
    $('btn-reset-stage').addEventListener('click', () => {
      state.uploadedImageDataUrl = null;
      state.customCropRect = null;
      state.selectedEl = $('target-risk-card');
      state.selectedSelector = 'div.risk-card:nth-child(1)';
      state.selectedLabel = '24/7 Watchdog & Risk Governor';
      if ($('uploaded-image-stage')) $('uploaded-image-stage').classList.remove('visible');
      if ($('embedded-frame')) $('embedded-frame').style.display = 'block';
      setStudioMode('inspect');
      positionSelectionOverlay();
      drawElementThumbnail();
    });
  }

  if ($('btn-close-popover')) {
    $('btn-close-popover').addEventListener('click', () => {
      if ($('annotation-popover')) $('annotation-popover').style.display = 'none';
      if ($('btn-reopen-popover')) $('btn-reopen-popover').style.display = 'inline-flex';
      positionSelectionOverlay();
    });
  }

  if ($('btn-reopen-popover')) {
    $('btn-reopen-popover').addEventListener('click', () => {
      if ($('annotation-popover')) $('annotation-popover').style.display = 'block';
      $('btn-reopen-popover').style.display = 'none';
      positionSelectionOverlay();
    });
  }

  // Draggable Popover
  const dragHandle = $('popover-drag-handle');
  const popover = $('annotation-popover');
  const wrap = $('studio-stage-wrap');
  if (dragHandle && popover && wrap) {
    let draggingPop = false;
    let offX = 0;
    let offY = 0;
    dragHandle.addEventListener('mousedown', (e) => {
      if (e.target.closest('button') || window.innerWidth <= 900) return;
      draggingPop = true;
      const pRect = popover.getBoundingClientRect();
      offX = e.clientX - pRect.left;
      offY = e.clientY - pRect.top;
    });
    window.addEventListener('mousemove', (e) => {
      if (!draggingPop) return;
      const wRect = wrap.getBoundingClientRect();
      const x = Math.max(8, Math.min(wRect.width - popover.offsetWidth - 8, e.clientX - wRect.left - offX));
      const y = Math.max(8, Math.min(wRect.height - popover.offsetHeight - 8, e.clientY - wRect.top - offY));
      popover.style.left = `${x}px`;
      popover.style.top = `${y}px`;
      popover.style.right = 'auto';
      popover.style.bottom = 'auto';
      positionSelectionOverlay();
    });
    window.addEventListener('mouseup', () => {
      draggingPop = false;
    });
  }

  if ($('btn-send-ui-fix')) {
    $('btn-send-ui-fix').addEventListener('click', async () => {
      const note = ($('popover-note-input')?.value || '').trim();
      if (!note) {
        $('popover-note-input')?.focus();
        return;
      }
      const now = new Date();
      const ymd = `${now.getUTCFullYear()}${pad2(now.getUTCMonth() + 1)}${pad2(now.getUTCDate())}`;
      const rand = String(Math.floor(1000 + Math.random() * 9000));
      const ticketId = `FB-${ymd}-${rand}`;

      let thumbDataUrl = '';
      try {
        thumbDataUrl = $('popover-thumb-canvas')?.toDataURL('image/png') || '';
      } catch (_) {}

      const ticket = {
        id: ticketId,
        page: 'archive-system.html',
        selector: state.selectedSelector,
        component: state.selectedLabel,
        instruction: note,
        imageUrl: thumbDataUrl,
        status: 'QUEUED',
        created_at: now.toISOString(),
      };

      state.tickets.unshift(ticket);
      saveTicketsToStorage(state.tickets);
      buildCombinedLogs();
      state.selectedLogId = ticket.id;
      renderLogsList();
      renderInspectorBody();

      await safeCopyText(buildAiFixPrompt(ticket));
      showToast('UI Fix Request Sent Successfully', `Ticket: ${ticketId}`);
    });
  }

  if ($('btn-dismiss-toast')) {
    $('btn-dismiss-toast').addEventListener('click', () => {
      $('studio-toast')?.classList.remove('show');
    });
  }

  window.addEventListener('keydown', (e) => {
    if (state.activeMainTab !== 'studio') return;
    const tag = (e.target?.tagName || '').toLowerCase();
    if (tag === 'input' || tag === 'textarea' || tag === 'select') return;
    if (e.key.toLowerCase() === 'c') {
      setStudioMode(state.studioMode === 'crop' ? 'inspect' : 'crop');
    } else if (e.key === 'Escape' && state.studioMode === 'crop') {
      setStudioMode('inspect');
    }
  });

  if ($('archive-log-search')) $('archive-log-search').addEventListener('input', renderLogsList);
  if ($('archive-log-filter')) $('archive-log-filter').addEventListener('change', renderLogsList);

  document.querySelectorAll('.insp-tab').forEach((btn) => {
    btn.addEventListener('click', () => {
      state.activeInspectorTab = btn.dataset.insp;
      document.querySelectorAll('.insp-tab').forEach((b) => b.classList.toggle('active', b === btn));
      renderInspectorBody();
    });
  });

  if ($('btn-insp-copy')) {
    $('btn-insp-copy').addEventListener('click', async () => {
      const ok = await safeCopyText(getInspectorExportText());
      if (ok) showToast('Copied to Clipboard', `Inspector: ${state.activeInspectorTab.toUpperCase()}`);
    });
  }

  if ($('btn-insp-download')) {
    $('btn-insp-download').addEventListener('click', () => {
      const text = getInspectorExportText();
      const ext = state.activeInspectorTab === 'details' ? 'log' : 'json';
      const blob = new Blob([text], { type: 'text/plain;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `quantguard-${state.selectedLogId || 'archive'}.${ext}`;
      a.click();
      URL.revokeObjectURL(url);
    });
  }

  window.addEventListener('resize', () => {
    if (state.activeMainTab === 'studio') positionSelectionOverlay();
  });
}

/* ------------------------------------------------------------------------ */
/* TAB 1: AI RESEARCH TRANSCRIPT                                            */
/* ------------------------------------------------------------------------ */
function renderTranscriptTab() {
  const container = $('transcript-container');
  if (!container) return;
  const rt = state.summary?.research_transcript || {};
  const messages = rt.messages || [];
  const handovers = rt.agent_handovers || {};

  if ($('pill-count-transcript')) $('pill-count-transcript').textContent = String(messages.length || 40);

  const query = ($('tr-search-input')?.value || '').trim().toLowerCase();
  const roleFilter = $('tr-role-filter')?.value || 'all';

  if (state.activeTranscriptMode === 'handovers') {
    const hist = handovers.handovers_history || [];
    const filteredH = hist.filter((h) => !query || JSON.stringify(h).toLowerCase().includes(query));
    container.className = 'handover-grid';
    container.innerHTML = filteredH
      .map((h) => {
        const from = h.from_officer || {};
        const to = h.to_officer || {};
        return `
          <article class="card handover-card">
            <div style="display:flex; justify-content:space-between; align-items:center; gap:8px;">
              <span class="status-tag pass">Step #${escapeHtml(h.step)}</span>
              <span class="mono" style="font-size:11px; color:var(--text-muted);">${escapeHtml(h.timestamp || handovers.active_cycle || '')}</span>
            </div>
            <div style="font-size:13px; font-weight:700;">
              ${escapeHtml(from.avatar || '')} ${escapeHtml(from.name || 'Officer')} ➔ ${escapeHtml(to.avatar || '')} ${escapeHtml(to.name || 'Officer')}
            </div>
            <div style="font-size:11.5px; color:var(--cyan);">${escapeHtml(from.role || '')}</div>
            <div style="font-size:12.5px; color:var(--text-secondary); line-height:1.5;">${escapeHtml(h.message || h.summary || h.payload_summary || '')}</div>
          </article>`;
      })
      .join('');
    return;
  }

  container.className = 'transcript-list';
  const filtered = messages.filter((m) => {
    if (roleFilter !== 'all' && m.role !== roleFilter) return false;
    if (!query) return true;
    return `${m.text} ${m.time} ${m.artifact?.title || ''}`.toLowerCase().includes(query);
  });

  if (!filtered.length) {
    container.innerHTML = '<div class="card" style="padding:24px; text-align:center; color:var(--text-muted);">No matching transcript messages.</div>';
    return;
  }

  container.innerHTML = filtered
    .map((m) => {
      const isUser = m.role === 'user';
      const artifactHtml = m.artifact
        ? `<div style="margin-top:10px; padding:10px 12px; border-radius:8px; background:var(--bg-surface-2); border:1px solid var(--border-subtle); display:flex; justify-content:space-between; align-items:center; gap:10px; flex-wrap:wrap;">
             <div>
               <div style="font-size:12px; font-weight:700;">${escapeHtml(m.artifact.icon || '📄')} ${escapeHtml(m.artifact.title || 'Report')}</div>
               <div style="font-size:11px; color:var(--text-muted);">${escapeHtml(m.artifact.summary || '')}</div>
             </div>
             <span class="status-tag pass">${escapeHtml(m.artifact.badge || 'REPORT')}</span>
           </div>`
        : '';
      return `
        <article class="card turn-card ${isUser ? 'user' : 'assistant'}">
          <div class="turn-meta">
            <div style="display:flex; align-items:center; gap:8px;">
              <span class="role-badge ${isUser ? 'user' : 'assistant'}">${isUser ? 'USER PROMPT' : 'ANTIGRAVITY AI'}</span>
              <span class="mono" style="font-size:11px; color:var(--text-muted);">Turn #${escapeHtml(m.turn)} · ID #${escapeHtml(m.id)}</span>
            </div>
            <div style="display:flex; align-items:center; gap:8px;">
              <span class="mono" style="font-size:11px; color:var(--text-muted);">${escapeHtml(m.time || '')}</span>
              <button type="button" class="tool-btn btn-copy-turn" data-mid="${escapeHtml(m.id)}" style="padding:3px 8px; font-size:10.5px;">Copy</button>
            </div>
          </div>
          <div class="turn-text">${escapeHtml(m.text)}</div>
          ${artifactHtml}
        </article>`;
    })
    .join('');

  container.querySelectorAll('.btn-copy-turn').forEach((btn) => {
    btn.addEventListener('click', async () => {
      const m = messages.find((x) => String(x.id) === String(btn.dataset.mid));
      if (!m) return;
      await safeCopyText(m.text || '');
      showToast('Transcript Turn Copied', `Turn #${m.turn} (${m.role})`);
    });
  });
}

function initTranscriptTab() {
  document.querySelectorAll('[data-tr-mode]').forEach((btn) => {
    btn.addEventListener('click', () => {
      state.activeTranscriptMode = btn.dataset.trMode;
      document.querySelectorAll('[data-tr-mode]').forEach((b) => b.classList.toggle('active', b === btn));
      renderTranscriptTab();
    });
  });
  if ($('tr-search-input')) $('tr-search-input').addEventListener('input', renderTranscriptTab);
  if ($('tr-role-filter')) $('tr-role-filter').addEventListener('change', renderTranscriptTab);
}

/* ------------------------------------------------------------------------ */
/* TAB 2: LEGACY RUNS                                                       */
/* ------------------------------------------------------------------------ */
function openLegacyRecordDrawer(title, htmlContent) {
  if ($('drawer-title')) $('drawer-title').textContent = title;
  if ($('drawer-body')) $('drawer-body').innerHTML = htmlContent;
  $('drawer-backdrop')?.classList.add('open');
  $('side-drawer')?.classList.add('open');
}

function closeLegacyRecordDrawer() {
  $('drawer-backdrop')?.classList.remove('open');
  $('side-drawer')?.classList.remove('open');
}

function renderLegacyTab() {
  const leg = state.summary?.legacy_runs || {};
  const counts = state.summary?.counts || {};

  if ($('leg-kpi-v1')) $('leg-kpi-v1').textContent = String(counts.historical_cycles_archived || 123);
  if ($('leg-kpi-fw')) $('leg-kpi-fw').textContent = String(counts.flywheel_cycles_completed || 327);
  if ($('leg-kpi-bt')) $('leg-kpi-bt').textContent = String((leg.backtest_strategies || []).length || 8);
  if ($('leg-kpi-sb')) $('leg-kpi-sb').textContent = `${leg.supabase_backup?.supabase_recent_runs_count || 0} Runs`;
  if ($('leg-kpi-sb-sub')) $('leg-kpi-sb-sub').textContent = `Backup: ${formatUtcShort(leg.supabase_backup?.backup_created_at_utc)}`;
  if ($('pill-count-legacy')) $('pill-count-legacy').textContent = `${counts.historical_cycles_archived || 123}+`;

  const thead = $('legacy-thead');
  const tbody = $('legacy-tbody');
  if (!thead || !tbody) return;

  const q = ($('legacy-search-input')?.value || '').trim().toLowerCase();
  const src = state.activeLegacySource;

  if (src === 'strategies') {
    thead.innerHTML = '<tr><th>Strategy / Engine</th><th>Symbol · TF</th><th>Period</th><th class="num">Trades</th><th class="num">Win Rate</th><th class="num">PF</th><th class="num">Max DD</th><th class="num">Net Profit</th></tr>';
    const rows = (leg.backtest_strategies || []).filter((s) => !q || `${s.name} ${s.symbol} ${s.id}`.toLowerCase().includes(q));
    tbody.innerHTML = rows
      .map((s) => {
        const sm = s.summary || {};
        const net = Number(sm.net_profit || 0);
        return `
          <tr data-leg-type="strategy" data-leg-id="${escapeHtml(s.id)}">
            <td>
              <div style="font-weight:700;">${escapeHtml(s.name)} ${s.is_champion ? '<span class="status-tag pass" style="margin-left:6px;">CHAMPION</span>' : ''}</div>
              <div class="mono" style="font-size:11px; color:var(--text-muted);">${escapeHtml(s.id)}</div>
            </td>
            <td class="mono">${escapeHtml(s.symbol)} · ${escapeHtml(s.timeframe)}</td>
            <td style="font-size:11.5px; color:var(--text-secondary);">${escapeHtml(s.period)}</td>
            <td class="num">${escapeHtml(sm.total_trades ?? '–')}</td>
            <td class="num">${sm.win_rate != null ? `${Number(sm.win_rate).toFixed(1)}%` : '–'}</td>
            <td class="num">${sm.profit_factor != null ? Number(sm.profit_factor).toFixed(2) : '–'}</td>
            <td class="num">${sm.max_drawdown != null ? `$${Number(sm.max_drawdown).toFixed(2)}` : '–'}</td>
            <td class="num ${net >= 0 ? 'pos' : 'neg'}">${net >= 0 ? '+' : '-'}$${Math.abs(net).toFixed(2)}</td>
          </tr>`;
      })
      .join('');
  } else if (src === 'flywheel' || src === 'historical') {
    const list = src === 'flywheel' ? leg.flywheel_cycles || [] : leg.historical_cycles || [];
    thead.innerHTML = '<tr><th>Cycle #</th><th>Era</th><th>Title / Learning Discovery</th><th>Impact</th><th>Completed At</th></tr>';
    const rows = list.filter((c) => !q || JSON.stringify(c).toLowerCase().includes(q));
    tbody.innerHTML = rows
      .map((c) => {
        const l = c.learning || {};
        return `
          <tr data-leg-type="${src}" data-leg-id="${escapeHtml(c.cycle_number)}">
            <td class="mono" style="font-weight:700; color:var(--cyan);">#${escapeHtml(c.cycle_number)}</td>
            <td><span class="status-tag ${src === 'flywheel' ? 'pass' : 'warn'}">${src === 'flywheel' ? 'LIVE ERA' : 'V1 ARCHIVE'}</span></td>
            <td>
              <div style="font-weight:600;">${escapeHtml(l.title || '')}</div>
              <div style="font-size:11.5px; color:var(--text-secondary);">${escapeHtml(l.discovery || '')}</div>
            </td>
            <td style="font-size:11.5px; color:var(--text-secondary);">${escapeHtml(l.impact || '')}</td>
            <td class="mono" style="font-size:11px; color:var(--text-muted);">${escapeHtml(c.completed_at || c.started_at || '')}</td>
          </tr>`;
      })
      .join('');
  } else {
    const exps = (leg.experiments || []).map((e) => ({
      kind: 'EXPERIMENT',
      id: e.experiment_id,
      symbol: e.dataset_id,
      mode: `${e.strategy_id} · ${e.hypothesis}`,
      pf: e.results?.profit_factor,
      net: e.results?.net_pnl,
      ts: e.created_at_utc,
    }));
    const sbRuns = (leg.supabase_backup?.supabase_recent_runs || []).map((r) => ({
      kind: 'SUPABASE_RUN',
      id: `RUN-${r.id}`,
      symbol: `${r.symbol} · ${r.timeframe}`,
      mode: r.running_mode || 'Backtest',
      pf: r.profit_factor,
      net: r.net_profit,
      ts: r.created_at,
    }));
    const combined = [...exps, ...sbRuns].filter((x) => !q || JSON.stringify(x).toLowerCase().includes(q));
    thead.innerHTML = '<tr><th>Record ID</th><th>Source</th><th>Symbol / Dataset</th><th>Mode / Hypothesis</th><th class="num">PF</th><th class="num">Net PnL</th><th>Timestamp</th></tr>';
    tbody.innerHTML = combined
      .map((x) => `
        <tr data-leg-type="supabase_exp" data-leg-id="${escapeHtml(x.id)}">
          <td class="mono" style="font-weight:700; color:var(--cyan);">${escapeHtml(x.id)}</td>
          <td><span class="status-tag ${x.kind === 'EXPERIMENT' ? 'pass' : 'warn'}">${escapeHtml(x.kind)}</span></td>
          <td class="mono">${escapeHtml(x.symbol)}</td>
          <td>${escapeHtml(x.mode)}</td>
          <td class="num">${x.pf != null ? Number(x.pf).toFixed(2) : '–'}</td>
          <td class="num ${Number(x.net || 0) >= 0 ? 'pos' : 'neg'}">${x.net != null ? `${Number(x.net) >= 0 ? '+' : '-'}$${Math.abs(Number(x.net)).toFixed(2)}` : '–'}</td>
          <td class="mono" style="font-size:11px; color:var(--text-muted);">${escapeHtml(formatUtcShort(x.ts))}</td>
        </tr>`)
      .join('');
  }

  tbody.querySelectorAll('tr').forEach((tr) => {
    tr.addEventListener('click', () => {
      const type = tr.dataset.legType;
      const id = tr.dataset.legId;
      let payload = null;
      if (type === 'strategy') payload = (leg.backtest_strategies || []).find((s) => s.id === id);
      else if (type === 'flywheel') payload = (leg.flywheel_cycles || []).find((c) => String(c.cycle_number) === String(id));
      else if (type === 'historical') payload = (leg.historical_cycles || []).find((c) => String(c.cycle_number) === String(id));
      else {
        payload = (leg.experiments || []).find((e) => e.experiment_id === id)
          || (leg.supabase_backup?.supabase_recent_runs || []).find((r) => `RUN-${r.id}` === id);
      }
      if (payload) {
        openLegacyRecordDrawer(`Archive Record · ${id}`, `<pre class="json-pre">${escapeHtml(JSON.stringify(payload, null, 2))}</pre>`);
      }
    });
  });
}

function initLegacyTab() {
  document.querySelectorAll('[data-leg-src]').forEach((btn) => {
    btn.addEventListener('click', () => {
      state.activeLegacySource = btn.dataset.legSrc;
      document.querySelectorAll('[data-leg-src]').forEach((b) => b.classList.toggle('active', b === btn));
      renderLegacyTab();
    });
  });
  if ($('legacy-search-input')) $('legacy-search-input').addEventListener('input', renderLegacyTab);
  $('btn-drawer-close')?.addEventListener('click', closeLegacyRecordDrawer);
  $('drawer-backdrop')?.addEventListener('click', closeLegacyRecordDrawer);
}

/* ------------------------------------------------------------------------ */
/* TAB 4: GOVERNANCE & PRIVACY                                              */
/* ------------------------------------------------------------------------ */
function renderGovernanceTab() {
  const gov = state.summary?.governance_and_privacy || {};
  const matrix = state.ruleMatrix || gov.rule_matrix || {};
  const tg = state.truthGuard || gov.truth_guard || {};
  const v2 = gov.quant_fund_v2 || {};
  const sec = gov.security_audit || {};
  const priv = gov.privacy_statements || [];

  const rulesObj = matrix.tier_1_immutable_hard_constraints?.rules || {};
  const rulesEntries = Object.entries(rulesObj);
  if ($('gov-kpi-rules')) $('gov-kpi-rules').textContent = `${rulesEntries.length} / ${rulesEntries.length}`;
  if ($('pill-count-rules')) $('pill-count-rules').textContent = `${rulesEntries.length}/${rulesEntries.length}`;
  if ($('gov-matrix-meta')) $('gov-matrix-meta').textContent = `${matrix.matrix_version || 'V4.0'} · Updated ${formatUtcShort(matrix.updated_at_utc)}`;

  const power = tg.statistical_power || {};
  if ($('gov-kpi-power')) $('gov-kpi-power').textContent = `N = ${power.sample_size_N ?? '–'} / ${power.target_preliminary_N ?? 500}`;
  if ($('gov-kpi-power-sub')) $('gov-kpi-power-sub').textContent = `${power.status || 'UNDERPOWERED'} · SE(SR) ±${power.standard_error_sharpe ?? '–'}`;

  if ($('gov-tier1-list')) {
    $('gov-tier1-list').innerHTML = rulesEntries
      .map(([k, r]) => `
        <div class="rule-row">
          <div>
            <div class="mono" style="font-weight:700; font-size:12px;">${escapeHtml(k)}${r.value != null ? ` <span style="color:var(--cyan);">(${escapeHtml(r.value)})</span>` : ''}</div>
            <div style="font-size:11.5px; color:var(--text-secondary); margin-top:2px;">${escapeHtml(r.description || '')}</div>
          </div>
          <span class="status-tag pass">${escapeHtml(r.status || 'ENFORCED')}</span>
        </div>`)
      .join('');
  }

  const chk = v2.validation_checklist || {};
  const chkMap = [
    ['CHK-01 Hard Stop Loss', chk.has_hard_stop_loss],
    ['CHK-02 Risk / Trade <= 2.0%', chk.risk_per_trade_within_limit],
    ['CHK-03 Max DD <= 18.0%', chk.max_dd_within_limit],
    ['CHK-04 Profit Factor >= 1.15', chk.pf_above_minimum],
    ['CHK-05 OOS Profitable', chk.oos_profitable],
    ['CHK-06 Walk-Forward Passed', chk.walk_forward_passed],
    ['CHK-07 Monte Carlo <= 1% Ruin', chk.monte_carlo_passed],
    ['CHK-08 Zero Lookahead Verified', chk.no_lookahead_bias_verified],
    ['CHK-09 AI Security Audit Clean', chk.ai_security_audit_passed],
  ];
  if ($('gov-v2-meta')) {
    const dq = v2.data_quality_report || {};
    $('gov-v2-meta').textContent = `${v2.policy_version || 'RISK-POL-V2.0'} · ${(dq.total_bars || 0).toLocaleString()} bars · OOS PF ${v2.out_of_sample_metrics?.profit_factor ?? '–'}`;
  }
  if ($('gov-v2-checklist')) {
    $('gov-v2-checklist').innerHTML = chkMap
      .map(([label, pass]) => `
        <div class="rule-row">
          <span class="mono" style="font-size:12px;">${escapeHtml(label)}</span>
          <span class="status-tag ${pass ? 'pass' : 'crit'}">${pass ? 'TRUE' : 'FALSE'}</span>
        </div>`)
      .join('');
  }

  if ($('gov-security-list')) {
    const rows = sec.rows || [];
    $('gov-security-list').innerHTML = rows
      .map((r) => `
        <div class="rule-row">
          <div>
            <div style="font-weight:700; font-size:12px;">${escapeHtml(r.category)}</div>
            <div style="font-size:11px; color:var(--text-secondary);">${escapeHtml(r.mechanism)}</div>
          </div>
          <span class="status-tag pass">${escapeHtml(r.result)}</span>
        </div>`)
      .join('');
  }

  if ($('gov-privacy-list')) {
    $('gov-privacy-list').innerHTML = priv.map((p) => `<p style="margin:0 0 6px;">• ${escapeHtml(p)}</p>`).join('');
  }
}

/* ------------------------------------------------------------------------ */
/* BOOTSTRAP & SHARED SHELL LIFECYCLE                                       */
/* ------------------------------------------------------------------------ */
async function loadAllData() {
  state.failedSources = [];
  try {
    const [summary, live, watchdog, alerts, truthGuard, ruleMatrix, overviewSummary] = await Promise.all([
      fetchJsonSafe('data/archive_system_summary.json', 'archive_system_summary', true),
      fetchJsonSafe('data/live_status.json', 'live_status'),
      fetchJsonSafe('data/watchdog_status.json', 'watchdog_status'),
      fetchJsonSafe('data/web_alerts.json', 'web_alerts'),
      fetchJsonSafe('data/truth_guard.json', 'truth_guard'),
      fetchJsonSafe('data/rule_classification_matrix.json', 'rule_classification_matrix'),
      fetchJsonSafe('data/overview_summary.json', 'overview_summary'),
    ]);

    state.summary = summary;
    state.live = live;
    state.watchdog = watchdog;
    state.alerts = alerts;
    state.truthGuard = truthGuard;
    state.ruleMatrix = ruleMatrix;
    state.overviewSummary = overviewSummary;

    updateShellTelemetry({
      watchdog,
      webAlerts: alerts,
      liveStatus: live,
      overviewSummary,
      failedSources: state.failedSources,
    });

    if ($('data-status-dot')) $('data-status-dot').className = 'status-dot ok';
    if ($('data-status-text')) $('data-status-text').textContent = 'LIVE ARCHIVE SYNCED';
  } catch (err) {
    if ($('data-status-dot')) $('data-status-dot').className = 'status-dot warn';
    if ($('data-status-text')) $('data-status-text').textContent = 'OFFLINE / CACHED SNAPSHOT';
    console.error('Data sync warning:', err);
  }

  state.tickets = loadTicketsFromStorage();
  buildCombinedLogs();
  renderWorkspaceTelemetry();
  renderLifecycleTrack();
  renderLogsList();
  renderInspectorBody();
  renderTranscriptTab();
  renderLegacyTab();
  renderGovernanceTab();

  requestAnimationFrame(() => {
    positionSelectionOverlay();
    drawElementThumbnail();
  });
}

async function init() {
  mountShell({ activePage: 'archive-system.html', onRetry: loadAllData });

  initTabs();
  initStudioInteractions();
  initTranscriptTab();
  initLegacyTab();

  // Redraw canvas thumbnail whenever shared shell toggles dark/light theme
  const themeObserver = new MutationObserver(() => {
    drawElementThumbnail();
  });
  themeObserver.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });

  updateCutoffCardTimer();
  setInterval(updateCutoffCardTimer, 1000);

  await loadAllData();
  setInterval(loadAllData, 45000);
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
