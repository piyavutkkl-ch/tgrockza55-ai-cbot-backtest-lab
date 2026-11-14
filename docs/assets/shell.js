/**
 * AI Quant Backtest Lab — Shared 8-Page Shell
 * Renders sticky Sidebar (8 hubs + Help), sticky Top Bar (Watchdog, 21:45 UTC Cutoff countdown,
 * DB Synced, Latency, Theme Switcher, Alerts Popover), Mobile Nav Drawer, and Footer.
 */

export const NAV_ITEMS = [
  { href: 'index.html', icon: '🏠', shortLabel: 'Overview', label: 'Overview', desc: 'ภาพรวมระบบ พอร์ตสด Backtest และสถานะบอท' },
  { href: 'data-center.html', icon: '📡', shortLabel: 'Data Center', label: 'Data Center', desc: 'Tick / DOM / Spread / Order Flow และ Simulator' },
  { href: 'research-lab.html', icon: '🧠', shortLabel: 'Research Lab', label: 'Research Lab', desc: 'ค้นหา Edge สร้างสมมติฐาน พัฒนากลยุทธ์' },
  { href: 'experiment-lab.html', icon: '🧪', shortLabel: 'Experiment', label: 'Experiment Lab', desc: 'ทดลอง Backtest เปรียบเทียบ Version และทดสอบซ้ำ' },
  { href: 'intelligence.html', icon: '📊', shortLabel: 'Intelligence', label: 'Intelligence', desc: 'วิเคราะห์ผลลัพธ์ กลไก จุดแข็ง และจุดอ่อน' },
  { href: 'improvement-audit.html', icon: '🔄', shortLabel: 'Audit', label: 'Improvement & Audit', desc: 'เสนอการพัฒนา ติดตามการทดลอง และตรวจสอบระบบ' },
  { href: 'archive-system.html', icon: '📦', shortLabel: 'Archive', label: 'Archive / System', desc: 'chat_transcript, legacy, feedback และ privacy' },
  { href: 'database.html', icon: '🗄️', shortLabel: 'Database', label: 'Unified Database', desc: 'ฐานข้อมูลรวมทุกตารางและผลทดสอบในที่เดียว' },
];

const THEME_KEY = 'cbot_quant_theme_v1';

export function escapeHtml(str) {
  return String(str ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

export function formatRelativeTime(isoStr) {
  if (!isoStr) return { short: '–', full: 'ยังไม่มีข้อมูล' };
  const d = new Date(isoStr);
  if (Number.isNaN(d.getTime())) return { short: '–', full: String(isoStr) };
  const diffSec = Math.max(0, Math.floor((Date.now() - d.getTime()) / 1000));
  const full = d.toISOString().replace('T', ' ').slice(0, 19) + ' UTC';
  if (diffSec < 60) return { short: `${diffSec}s ago`, full };
  const mins = Math.floor(diffSec / 60);
  if (mins < 60) return { short: `${mins}m ago`, full };
  const hrs = Math.floor(mins / 60);
  if (hrs < 48) return { short: `${hrs}h ago`, full };
  const days = Math.floor(hrs / 24);
  return { short: `${days}d ago`, full };
}

export function formatCutoffCountdown(now = new Date()) {
  const target = new Date(Date.UTC(
    now.getUTCFullYear(),
    now.getUTCMonth(),
    now.getUTCDate(),
    21, 45, 0, 0
  ));
  if (now.getTime() >= target.getTime()) {
    target.setUTCDate(target.getUTCDate() + 1);
  }
  const sec = Math.max(0, Math.floor((target.getTime() - now.getTime()) / 1000));
  const h = String(Math.floor(sec / 3600)).padStart(2, '0');
  const m = String(Math.floor((sec % 3600) / 60)).padStart(2, '0');
  const s = String(sec % 60).padStart(2, '0');
  return `${h}:${m}:${s}`;
}

export function getSavedTheme() {
  try {
    const saved = localStorage.getItem(THEME_KEY);
    if (saved === 'light' || saved === 'dark') return saved;
  } catch (_) {}
  const attr = document.documentElement?.getAttribute('data-theme');
  return attr === 'light' ? 'light' : 'dark';
}

export function applyTheme(theme) {
  const clean = theme === 'light' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', clean);
  try {
    localStorage.setItem(THEME_KEY, clean);
  } catch (_) {}
  const btn = document.getElementById('shell-theme-btn');
  if (btn) {
    btn.setAttribute('aria-pressed', String(clean === 'light'));
    btn.title = clean === 'light' ? 'สลับเป็นธีมมืด (Dark Mode)' : 'สลับเป็นธีมสว่าง (Light Mode)';
    btn.innerHTML = clean === 'light'
      ? '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>'
      : '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>';
  }
}

export function extractLatestLatencyMs(liveStatus, summaryData) {
  const trades = Array.isArray(liveStatus?.recent_trades) ? liveStatus.recent_trades : [];
  let latestTime = '';
  let latestLat = null;
  for (const t of trades) {
    const raw = String(t?.latencyMs ?? '').trim();
    if (!raw) continue;
    const val = Number(raw);
    if (!Number.isFinite(val)) continue;
    const tStr = String(t?.time ?? '');
    if (!latestTime || tStr >= latestTime) {
      latestTime = tStr;
      latestLat = Math.round(val);
    }
  }
  if (latestLat !== null) return latestLat;
  const fallback = summaryData?.live_history?.latest_trade_latency_ms;
  return Number.isFinite(Number(fallback)) ? Math.round(Number(fallback)) : null;
}

function getCurrentPageFile() {
  const bodyAttr = document.body?.dataset?.page;
  if (bodyAttr) return bodyAttr;
  const part = window.location.pathname.split('/').pop();
  return part || 'index.html';
}

function brandLogoSvg() {
  return `
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <rect x="3" y="13" width="3.5" height="7" rx="1" fill="#38bdf8"/>
      <rect x="8.5" y="9.5" width="3.5" height="10.5" rx="1" fill="#22c55e"/>
      <rect x="14" y="6" width="3.5" height="14" rx="1" fill="#f5b301"/>
      <path d="M3 10.5L9.5 6L14 8.5L21 3" stroke="#38bdf8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
      <path d="M17.5 3H21V6.5" stroke="#38bdf8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>
  `;
}

function bellSvg() {
  return `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg>`;
}

function clockSvg() {
  return `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#22c55e" stroke-width="2" aria-hidden="true"><circle cx="12" cy="12" r="9"/><polyline points="12 7 12 12 15.5 14"/></svg>`;
}

function dbSvg() {
  return `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" stroke-width="2" aria-hidden="true"><ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v6c0 1.66 3.58 3 8 3s8-1.34 8-3V5"/><path d="M4 11v6c0 1.66 3.58 3 8 3s8-1.34 8-3v-6"/></svg>`;
}

function signalSvg(color = '#22c55e') {
  return `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="${color}" stroke-width="2.2" stroke-linecap="round" aria-hidden="true"><line x1="4" y1="20" x2="4" y2="15"/><line x1="9" y1="20" x2="9" y2="11"/><line x1="14" y1="20" x2="14" y2="7"/><line x1="19" y1="20" x2="19" y2="4"/></svg>`;
}

let countdownTimer = null;

export function mountShell(options = {}) {
  applyTheme(getSavedTheme());

  const activeFile = options.activePage || getCurrentPageFile();
  const root = document.getElementById('app-shell');
  if (!root) {
    console.warn('mountShell: #app-shell container not found');
    return;
  }

  const pageMain = document.getElementById('page-main-template');
  const initialMainHtml = pageMain ? pageMain.innerHTML : root.innerHTML;
  if (pageMain) pageMain.remove();

  root.className = 'app-frame';
  root.innerHTML = `
    <aside class="shell-sidebar" aria-label="เมนูหลัก 8 หมวด">
      <a href="index.html" class="sidebar-brand" aria-label="หน้าหลัก Overview">
        ${brandLogoSvg()}
      </a>
      <nav class="sidebar-nav">
        ${NAV_ITEMS.map((item) => {
          const isActive = item.href === activeFile;
          return `
            <a href="${escapeHtml(item.href)}"
               class="nav-rail-item ${isActive ? 'is-active' : ''}"
               aria-label="${escapeHtml(item.label)}"
               title="${escapeHtml(item.label + ' — ' + item.desc)}"
               ${isActive ? 'aria-current="page"' : ''}>
              <span class="nav-rail-icon" aria-hidden="true">${item.icon}</span>
              <span class="nav-rail-label">${escapeHtml(item.shortLabel)}</span>
            </a>`;
        }).join('')}
      </nav>
      <div class="sidebar-footer-actions">
        <button type="button" id="shell-help-btn" class="nav-rail-item" aria-label="คำแนะนำการใช้งานเว็บ 8 หน้า" title="คำแนะนำ & คู่มือระบบ">
          <span class="nav-rail-icon" aria-hidden="true">❓</span>
          <span class="nav-rail-label">Help</span>
        </button>
      </div>
    </aside>

    <div class="shell-main-col">
      <header class="shell-topbar" role="banner">
        <div class="topbar-left">
          <button type="button" id="shell-watchdog-pill" class="watchdog-pill status-offline" aria-expanded="false" aria-controls="shell-alerts-popover" title="คลิกเพื่อดูรายละเอียด Watchdog และสถานะข้อมูล">
            <span class="pulse-dot gray" id="shell-watchdog-dot" aria-hidden="true"></span>
            <span>WATCHDOG 24/7: <strong class="status-label" id="shell-watchdog-status">LOADING</strong></span>
          </button>

          <span class="topbar-divider" aria-hidden="true"></span>

          <div class="cutoff-widget" title="ระบบบังคับปิดสถานะ (Daily Flat Cutoff) ทุกวันเวลา 21:45 UTC">
            ${clockSvg()}
            <span class="cutoff-label">21:45 UTC CUTOFF</span>
            <span class="cutoff-time mono" id="shell-cutoff-timer">${formatCutoffCountdown()}</span>
          </div>
        </div>

        <div class="topbar-right">
          <div class="topbar-telemetry hide-tablet" id="shell-db-sync-box" title="ยังไม่มีข้อมูล">
            ${dbSvg()}
            <div>
              <strong>DB synced</strong>
              <small id="shell-db-sync-val" class="mono">–</small>
            </div>
          </div>

          <div class="topbar-telemetry" id="shell-latency-box" title="ยังไม่มีข้อมูล">
            ${signalSvg('#94a3b8')}
            <div>
              <strong>Latency</strong>
              <small id="shell-latency-val" class="mono">–</small>
            </div>
          </div>

          <button type="button" id="shell-theme-btn" class="icon-btn" aria-label="สลับธีมมืด/สว่าง" aria-pressed="false"></button>

          <button type="button" id="shell-alerts-btn" class="icon-btn" aria-label="รายการแจ้งเตือน Watchdog และ Web Alerts" aria-expanded="false" aria-controls="shell-alerts-popover">
            ${bellSvg()}
            <span class="alert-badge-count mono" id="shell-alerts-badge" hidden>0</span>
          </button>
        </div>
      </header>

      <main class="shell-content" id="shell-content-slot" tabindex="-1">
        <div class="stale-banner" id="shell-stale-banner" hidden role="status">
          <span id="shell-stale-text">⚠️ ไม่สามารถเชื่อมต่อไฟล์ข้อมูลบางส่วน — กำลังแสดงสถานะออฟไลน์/ข้อมูลล่าสุดที่มี</span>
          <button type="button" class="btn-secondary-link" id="shell-retry-btn" style="padding:4px 10px;">ลองโหลดใหม่</button>
        </div>
        ${initialMainHtml}
      </main>

      <footer class="shell-footer">
        <div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap;">
          <a href="old-web/index.html" class="footer-legacy-link">📁 เว็บเวอร์ชันเดิม</a>
          <span>Read-only Research Portal · แสดงข้อมูลจากชุดบันทึกวิจัยใน docs/data/</span>
        </div>
        <div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap;">
          <span id="shell-footer-updated" class="mono">อัปเดตล่าสุด: –</span>
          <span>·</span>
          <span>v4.0 (8-Page Hub)</span>
        </div>
      </footer>
    </div>

    <div class="alerts-popover" id="shell-alerts-popover" hidden role="dialog" aria-label="การแจ้งเตือนและสถานะ Watchdog">
      <div class="alerts-popover-head">
        <div>
          <strong style="font-size:13px;">🔔 System Alerts &amp; Watchdog</strong>
          <div style="font-size:11px;color:var(--text-muted);" id="shell-alerts-sub">กำลังตรวจสอบ...</div>
        </div>
        <button type="button" class="icon-btn" id="shell-alerts-close" aria-label="ปิดหน้าต่างแจ้งเตือน">✕</button>
      </div>
      <div class="alerts-popover-body" id="shell-alerts-body">
        <p style="margin:0;color:var(--text-muted);font-size:12px;">กำลังโหลดรายการแจ้งเตือน...</p>
      </div>
    </div>

    <div class="help-backdrop" id="shell-help-modal" hidden role="dialog" aria-modal="true" aria-labelledby="shell-help-title">
      <div class="help-dialog">
        <div style="display:flex;align-items:center;justify-content:space-between;gap:10px;margin-bottom:12px;">
          <h2 id="shell-help-title" style="margin:0;font-size:17px;">❓ คู่มือโครงสร้างระบบวิจัย 8 หน้า</h2>
          <button type="button" class="icon-btn" id="shell-help-close" aria-label="ปิดคู่มือ">✕</button>
        </div>
        <p style="margin:0 0 12px;font-size:13px;color:var(--text-secondary);">
          เว็บวิจัยถูกจัดกลุ่มใหม่เหลือ <strong>8 หมวดหลัก</strong> เพื่อให้เห็นภาพรวมพอร์ตสดและผลการทดสอบย้อนหลังแยกจากกันชัดเจน:
        </p>
        <div style="display:grid;gap:8px;margin-bottom:14px;">
          ${NAV_ITEMS.map((item, idx) => `
            <a href="${escapeHtml(item.href)}" style="display:flex;align-items:flex-start;gap:10px;padding:8px 10px;border-radius:10px;border:1px solid var(--border-subtle);background:var(--bg-subcard);">
              <span style="font-size:16px;">${item.icon}</span>
              <div>
                <div style="font-weight:700;font-size:13px;">${idx + 1}. ${escapeHtml(item.label)}</div>
                <div style="font-size:11.5px;color:var(--text-muted);">${escapeHtml(item.desc)}</div>
              </div>
            </a>
          `).join('')}
        </div>
        <div style="padding:10px 12px;border-radius:10px;background:var(--bg-subcard);border:1px solid var(--border-subtle);font-size:12px;color:var(--text-secondary);">
          ต้องการเปิดหน้าเว็บชุดเดิมทั้ง 14 หน้า? ดูได้ที่ลิงก์ <strong>📁 เว็บเวอร์ชันเดิม</strong> บริเวณด้านล่างสุด (footer) ของทุกหน้า
        </div>
      </div>
    </div>

    <nav class="mobile-bottom-nav" aria-label="เมนูมือถือ">
      ${[NAV_ITEMS[0], NAV_ITEMS[1], NAV_ITEMS[2], NAV_ITEMS[7]].map((item) => {
        const isActive = item.href === activeFile;
        return `
          <a href="${escapeHtml(item.href)}" class="mobile-nav-btn ${isActive ? 'is-active' : ''}" ${isActive ? 'aria-current="page"' : ''}>
            <span style="font-size:16px;" aria-hidden="true">${item.icon}</span>
            <span>${escapeHtml(item.shortLabel)}</span>
          </a>
        `;
      }).join('')}
      <button type="button" id="shell-mobile-menu-btn" class="mobile-nav-btn" aria-expanded="false" aria-controls="shell-mobile-drawer">
        <span style="font-size:16px;" aria-hidden="true">☰</span>
        <span>ทั้ง 8 หน้า</span>
      </button>
    </nav>

    <div class="mobile-drawer" id="shell-mobile-drawer" hidden role="dialog" aria-label="เมนูทั้ง 8 หมวด">
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px;">
        <strong style="font-size:13px;">เลือกหมวดหลักทั้ง 8 หน้า</strong>
        <button type="button" class="icon-btn" id="shell-mobile-drawer-close" aria-label="ปิดเมนู" style="width:28px;height:28px;">✕</button>
      </div>
      <div class="mobile-drawer-grid">
        ${NAV_ITEMS.map((item) => {
          const isActive = item.href === activeFile;
          return `
            <a href="${escapeHtml(item.href)}" class="mobile-drawer-link ${isActive ? 'is-active' : ''}">
              <span>${item.icon}</span>
              <span>${escapeHtml(item.label)}</span>
            </a>
          `;
        }).join('')}
      </div>
    </div>
  `;

  applyTheme(getSavedTheme());
  bindShellInteractions(options.onRetry);
  startCutoffCountdown();
}

function startCutoffCountdown() {
  if (countdownTimer) clearInterval(countdownTimer);
  const tick = () => {
    const el = document.getElementById('shell-cutoff-timer');
    if (el) el.textContent = formatCutoffCountdown();
  };
  tick();
  countdownTimer = setInterval(tick, 1000);
}

function bindShellInteractions(onRetry) {
  const themeBtn = document.getElementById('shell-theme-btn');
  themeBtn?.addEventListener('click', () => {
    const curr = document.documentElement.getAttribute('data-theme') || 'dark';
    applyTheme(curr === 'dark' ? 'light' : 'dark');
  });

  const alertsPopover = document.getElementById('shell-alerts-popover');
  const alertsBtn = document.getElementById('shell-alerts-btn');
  const watchdogBtn = document.getElementById('shell-watchdog-pill');
  const alertsClose = document.getElementById('shell-alerts-close');

  const setAlertsOpen = (open) => {
    if (!alertsPopover) return;
    alertsPopover.hidden = !open;
    alertsBtn?.setAttribute('aria-expanded', String(open));
    watchdogBtn?.setAttribute('aria-expanded', String(open));
  };

  alertsBtn?.addEventListener('click', (e) => {
    e.stopPropagation();
    setAlertsOpen(alertsPopover?.hidden ?? true);
  });
  watchdogBtn?.addEventListener('click', (e) => {
    e.stopPropagation();
    setAlertsOpen(alertsPopover?.hidden ?? true);
  });
  alertsClose?.addEventListener('click', () => setAlertsOpen(false));

  const helpModal = document.getElementById('shell-help-modal');
  const helpBtn = document.getElementById('shell-help-btn');
  const helpClose = document.getElementById('shell-help-close');
  helpBtn?.addEventListener('click', () => { if (helpModal) helpModal.hidden = false; });
  helpClose?.addEventListener('click', () => { if (helpModal) helpModal.hidden = true; });
  helpModal?.addEventListener('click', (e) => {
    if (e.target === helpModal) helpModal.hidden = true;
  });

  const drawer = document.getElementById('shell-mobile-drawer');
  const drawerBtn = document.getElementById('shell-mobile-menu-btn');
  const drawerClose = document.getElementById('shell-mobile-drawer-close');
  drawerBtn?.addEventListener('click', () => {
    if (!drawer) return;
    const next = !drawer.hidden;
    drawer.hidden = next;
    drawerBtn.setAttribute('aria-expanded', String(!next));
  });
  drawerClose?.addEventListener('click', () => {
    if (drawer) drawer.hidden = true;
    drawerBtn?.setAttribute('aria-expanded', 'false');
  });

  document.addEventListener('click', (e) => {
    if (alertsPopover && !alertsPopover.hidden) {
      if (!alertsPopover.contains(e.target) && !alertsBtn?.contains(e.target) && !watchdogBtn?.contains(e.target)) {
        setAlertsOpen(false);
      }
    }
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      setAlertsOpen(false);
      if (helpModal) helpModal.hidden = true;
      if (drawer) drawer.hidden = true;
    }
  });

  const retryBtn = document.getElementById('shell-retry-btn');
  if (retryBtn && typeof onRetry === 'function') {
    retryBtn.addEventListener('click', () => onRetry());
  }
}

export function updateShellTelemetry({ watchdog, webAlerts, liveStatus, overviewSummary, failedSources = [] }) {
  // 1. Watchdog Pill
  const pill = document.getElementById('shell-watchdog-pill');
  const dot = document.getElementById('shell-watchdog-dot');
  const label = document.getElementById('shell-watchdog-status');

  const rawStatus = String(watchdog?.overall_status || '').toUpperCase();
  if (pill && dot && label) {
    pill.classList.remove('status-ok', 'status-warn', 'status-crit', 'status-offline');
    dot.classList.remove('green', 'amber', 'red', 'gray');
    if (!rawStatus) {
      pill.classList.add('status-offline');
      dot.classList.add('gray');
      label.textContent = 'OFFLINE';
    } else if (['OK', 'ONLINE', 'HEALTHY'].includes(rawStatus)) {
      pill.classList.add('status-ok');
      dot.classList.add('green');
      label.textContent = rawStatus === 'HEALTHY' ? 'ONLINE' : rawStatus;
    } else if (rawStatus.includes('CRITICAL')) {
      pill.classList.add('status-crit');
      dot.classList.add('red');
      label.textContent = 'CRITICAL ALERT';
    } else {
      pill.classList.add('status-warn');
      dot.classList.add('amber');
      label.textContent = rawStatus;
    }
  }

  // 2. DB Synced + Footer Timestamp
  const dbRel = formatRelativeTime(liveStatus?.timestamp_utc);
  const dbVal = document.getElementById('shell-db-sync-val');
  const dbBox = document.getElementById('shell-db-sync-box');
  if (dbVal) dbVal.textContent = dbRel.short;
  if (dbBox) dbBox.title = `Timestamp: ${dbRel.full}`;
  const footUpd = document.getElementById('shell-footer-updated');
  if (footUpd) footUpd.textContent = `อัปเดตล่าสุด: ${dbRel.full}`;

  // 3. Latency
  const latMs = extractLatestLatencyMs(liveStatus, overviewSummary);
  const latVal = document.getElementById('shell-latency-val');
  const latBox = document.getElementById('shell-latency-box');
  if (latVal) latVal.textContent = latMs !== null ? `${latMs}ms` : '–';
  if (latBox) {
    latBox.title = latMs !== null
      ? `Execution Latency ล่าสุดจาก OPEN event (${latMs} ms)`
      : 'ยังไม่มีข้อมูล Latency ใน live_status.json';
    const sigIcon = latBox.querySelector('svg');
    if (sigIcon) {
      const sigColor = latMs === null ? '#94a3b8' : latMs <= 350 ? '#22c55e' : latMs <= 800 ? '#f5b301' : '#ef4444';
      sigIcon.setAttribute('stroke', sigColor);
    }
  }

  // 4. Alerts Badge & Popover
  const alertsList = Array.isArray(webAlerts?.alerts) ? webAlerts.alerts : [];
  const unackCount = alertsList.filter((a) => !a.acknowledged).length;
  const wdAlerts = Array.isArray(watchdog?.active_alerts) ? watchdog.active_alerts : [];
  const badge = document.getElementById('shell-alerts-badge');
  if (badge) {
    if (unackCount > 0) {
      badge.hidden = false;
      badge.textContent = String(unackCount);
    } else {
      badge.hidden = true;
    }
  }

  const subEl = document.getElementById('shell-alerts-sub');
  if (subEl) {
    const wdAudit = formatRelativeTime(watchdog?.audited_at_utc).full;
    subEl.textContent = `Web Alerts: ${alertsList.length} (ยังไม่อ่าน ${unackCount}) · Watchdog: ${watchdog?.active_alerts_count ?? 0} · ${wdAudit}`;
  }

  const bodyEl = document.getElementById('shell-alerts-body');
  if (bodyEl) {
    const blocks = [];
    if (wdAlerts.length > 0) {
      blocks.push(`<div style="font-size:11px;font-weight:700;color:var(--accent-red-text);letter-spacing:.03em;text-transform:uppercase;">Watchdog Incidents (${wdAlerts.length})</div>`);
      for (const msg of wdAlerts) {
        blocks.push(`<div class="alert-item-card sev-critical"><strong>⚠️ Recorder Alert</strong><div style="margin-top:3px;color:var(--text-secondary);">${escapeHtml(msg)}</div></div>`);
      }
    }
    if (alertsList.length > 0) {
      blocks.push(`<div style="font-size:11px;font-weight:700;color:var(--accent-blue-text);letter-spacing:.03em;text-transform:uppercase;margin-top:4px;">Web Alerts (${alertsList.length})</div>`);
      for (const a of alertsList.slice(0, 8)) {
        const sev = String(a.severity || '').toUpperCase();
        const cls = sev === 'CRITICAL' ? 'sev-critical' : sev === 'WARNING' ? 'sev-warn' : sev === 'PASS' ? 'sev-pass' : 'sev-gate';
        const ts = formatRelativeTime(a.created_at_utc).full;
        blocks.push(`
          <div class="alert-item-card ${cls}">
            <div style="display:flex;justify-content:space-between;gap:8px;align-items:flex-start;">
              <strong>${escapeHtml(a.title || a.severity || 'Alert')}</strong>
              <span class="mono" style="font-size:10px;color:var(--text-muted);white-space:nowrap;">${escapeHtml(a.symbol || '')}</span>
            </div>
            <div style="margin-top:4px;color:var(--text-secondary);line-height:1.45;">${escapeHtml(a.message || '')}</div>
            <div class="mono" style="margin-top:5px;font-size:10px;color:var(--text-muted);">${escapeHtml(ts)}</div>
          </div>
        `);
      }
    }
    if (blocks.length === 0) {
      blocks.push(`<div style="padding:12px;text-align:center;color:var(--text-muted);font-size:12px;">ไม่มีการแจ้งเตือนค้างในระบบ</div>`);
    }
    bodyEl.innerHTML = blocks.join('');
  }

  // 5. Offline/Stale Banner
  const staleBanner = document.getElementById('shell-stale-banner');
  const staleText = document.getElementById('shell-stale-text');
  if (staleBanner) {
    if (failedSources.length > 0) {
      staleBanner.hidden = false;
      if (staleText) {
        staleText.textContent = `⚠️ โหมดออฟไลน์ / ข้อมูลบางส่วนโหลดไม่สำเร็จ (${failedSources.join(', ')}) — อัปเดตล่าสุด: ${dbRel.full}`;
      }
    } else {
      staleBanner.hidden = true;
    }
  }
}

/**
 * Convenience loader for Pages 2–8 placeholders (loads lightweight telemetry only)
 */
export async function loadShellTelemetryOnly() {
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
  const [watchdog, webAlerts, liveStatus, overviewSummary] = await Promise.all([
    fetchSafe('data/watchdog_status.json', 'watchdog_status'),
    fetchSafe('data/web_alerts.json', 'web_alerts'),
    fetchSafe('data/live_status.json', 'live_status'),
    fetchSafe('data/overview_summary.json', 'overview_summary'),
  ]);
  updateShellTelemetry({ watchdog, webAlerts, liveStatus, overviewSummary, failedSources });
}
