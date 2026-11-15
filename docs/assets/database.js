/* ==========================================================================
   AI Quant Backtest Lab — Page 8/8: Unified Data Catalog & JSON Inspector
   ES Module integrated cleanly with shared shell.js & shell.css
   ========================================================================== */

import { mountShell, updateShellTelemetry, escapeHtml } from './shell.js';

const DEFAULT_FILE = 'backtest_data.json';
const ARRAY_PAGE_SIZE = 60;
const EXPAND_ALL_LINE_CAP = 3500;
const MAX_AUTO_EXPAND_MATCHES = 80;

const state = {
  catalog: null,
  selectedFile: DEFAULT_FILE,
  scope: 'core', // 'core' (33) | 'all' (45)
  sortBy: 'folder', // 'folder' | 'size' | 'rows' | 'name'
  catalogQuery: '',
  collapsedFolders: new Set(),

  // Loaded file payloads cached by filename
  cache: new Map(), // filename -> { format, rawText, parsed, validJson, parseError, fetchError }
  loadingFile: null,

  // Inspector state
  viewMode: 'tree', // 'tree' | 'raw'
  expandedPaths: new Set(['$']),
  arrayLimits: new Map(), // path -> max items currently visible
  jsonQuery: '',
  searchMatchPaths: [], // ordered array of matching JSONPaths
  activeMatchIndex: -1,
  activeLinePath: '$',
  cursorLn: 1,
  cursorCol: 1,
  renderedLines: [],
  filterOpen: false,
  failedSources: [],
};

function $(id) {
  return document.getElementById(id);
}

let toastTimer = null;
function showToast(msg) {
  const el = $('db-toast');
  if (!el) return;
  el.textContent = msg;
  el.hidden = false;
  if (toastTimer) clearTimeout(toastTimer);
  toastTimer = setTimeout(() => {
    el.hidden = true;
  }, 2400);
}

async function copyText(text) {
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

async function fetchJsonSafe(path, label) {
  try {
    const res = await fetch(`${path}?t=${Date.now()}`, { cache: 'no-store' });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (_) {
    state.failedSources.push(label);
    return null;
  }
}

function getFileFromHash() {
  const raw = window.location.hash || '';
  const m = raw.match(/file=([^&]+)/);
  if (!m) return null;
  try {
    return decodeURIComponent(m[1]);
  } catch (_) {
    return null;
  }
}

function setFileHash(filename) {
  try {
    const next = `#file=${encodeURIComponent(filename)}`;
    if (window.location.hash !== next) {
      history.replaceState(null, '', next);
    }
  } catch (_) {}
}

/* -------------------------------------------------------------------------- */
/*  Catalog Filtering, Sorting & Rendering (Left 35% Panel)                   */
/* -------------------------------------------------------------------------- */

function getScopedDatasets() {
  const all = Array.isArray(state.catalog?.datasets) ? state.catalog.datasets : [];
  const scoped = state.scope === 'core' ? all.filter((d) => d.is_core) : all;
  const q = state.catalogQuery.trim().toLowerCase();
  if (!q) return scoped;
  return scoped.filter((d) => {
    const haystack = [
      d.filename,
      d.schema_name,
      d.description,
      ...(Array.isArray(d.top_keys) ? d.top_keys : []),
    ]
      .join(' ')
      .toLowerCase();
    return haystack.includes(q);
  });
}

function sortDatasets(list) {
  const copy = [...list];
  if (state.sortBy === 'size') {
    copy.sort((a, b) => b.size_bytes - a.size_bytes || a.filename.localeCompare(b.filename));
  } else if (state.sortBy === 'rows') {
    copy.sort((a, b) => b.record_count - a.record_count || a.filename.localeCompare(b.filename));
  } else if (state.sortBy === 'name') {
    copy.sort((a, b) => a.filename.localeCompare(b.filename));
  }
  return copy;
}

function folderSvg(isCache = false) {
  return `<svg class="folder-icon-svg ${isCache ? 'cache' : ''}" width="15" height="15" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M10 4l2 2h8a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h6z"/></svg>`;
}

function chevronSvg() {
  return `<svg class="folder-chevron" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polyline points="6 9 12 15 18 9"/></svg>`;
}

function renderCatalogPanel() {
  const titleEl = $('catalog-panel-title');
  const footprintEl = $('catalog-footprint-pill');
  const treeEl = $('catalog-tree-scroll');
  const footerLeft = $('catalog-footer-left');
  const footerRight = $('catalog-footer-right');
  if (!treeEl) return;

  const counts = state.catalog?.counts || {};
  const visible = getScopedDatasets();
  const scopeTotal = state.scope === 'core' ? (counts.core_datasets ?? visible.length) : (counts.total_files ?? visible.length);

  if (titleEl) {
    titleEl.textContent = `Data Catalog (${scopeTotal} Datasets)`;
  }
  if (footprintEl) {
    const label = state.scope === 'core' ? (counts.core_total_label || '–') : (counts.all_total_label || '–');
    footprintEl.textContent = label;
    footprintEl.title = `Total size across ${scopeTotal} files`;
  }

  const folders = Array.isArray(state.catalog?.folders) ? state.catalog.folders : [];
  const activeFolders = folders.filter((f) => state.scope === 'all' || f.id !== 'generated_caches');

  if (visible.length === 0) {
    treeEl.innerHTML = `<div class="catalog-empty">No datasets match "<strong>${escapeHtml(state.catalogQuery)}</strong>".<br><span style="font-size:11px;">Try clearing search or switching filter scope.</span></div>`;
  } else if (state.sortBy !== 'folder') {
    const sorted = sortDatasets(visible);
    treeEl.innerHTML = `
      <div class="catalog-folder-items" style="padding-left:2px;">
        ${sorted.map((d) => renderFileRowHtml(d)).join('')}
      </div>
    `;
  } else {
    const htmlParts = [];
    for (const folder of activeFolders) {
      const items = visible.filter((d) => d.folder_id === folder.id);
      if (items.length === 0 && state.catalogQuery.trim()) continue;
      const isCollapsed = !state.catalogQuery.trim() && state.collapsedFolders.has(folder.id);
      const isCache = folder.id === 'generated_caches';
      htmlParts.push(`
        <section class="catalog-folder ${isCollapsed ? 'is-collapsed' : ''}" data-folder-id="${escapeHtml(folder.id)}">
          <button type="button"
                  class="catalog-folder-btn"
                  aria-expanded="${String(!isCollapsed)}"
                  data-folder-toggle="${escapeHtml(folder.id)}"
                  title="${escapeHtml(folder.description || folder.name)}">
            <span class="folder-left">
              ${chevronSvg()}
              ${folderSvg(isCache)}
              <span class="folder-name">${escapeHtml(folder.name)}</span>
              <span class="folder-count mono">(${items.length})</span>
            </span>
            <span class="folder-status-dot ${escapeHtml(folder.dot || 'green')}" title="Verified on disk"></span>
          </button>
          <div class="catalog-folder-items" role="group" aria-label="${escapeHtml(folder.name)}">
            ${items.map((d) => renderFileRowHtml(d)).join('')}
          </div>
        </section>
      `);
    }
    treeEl.innerHTML = htmlParts.join('');
  }

  if (footerLeft) {
    footerLeft.textContent = state.catalogQuery.trim()
      ? `Showing ${visible.length} of ${scopeTotal} datasets`
      : `${scopeTotal} verified files · docs/data/`;
  }
  if (footerRight) {
    const activeMeta = findDatasetMeta(state.selectedFile);
    footerRight.textContent = activeMeta ? `Active: ${activeMeta.filename}` : 'Ready';
  }
}

function renderFileRowHtml(d) {
  const isSel = d.filename === state.selectedFile;
  const glyph = d.format === 'MD' ? 'MD' : '{}';
  return `
    <button type="button"
            class="catalog-file-row ${isSel ? 'is-selected' : ''}"
            data-file-select="${escapeHtml(d.filename)}"
            aria-selected="${String(isSel)}"
            title="${escapeHtml(`${d.filename} — ${d.description}`)}">
      <span class="file-type-glyph" aria-hidden="true">${glyph}</span>
      <span class="file-row-name">${escapeHtml(d.filename)}</span>
      <span class="file-row-rows">${escapeHtml(d.row_label)}</span>
      <span class="file-row-size">${escapeHtml(d.size_label)}</span>
    </button>
  `;
}

function findDatasetMeta(filename) {
  const all = state.catalog?.datasets || [];
  return all.find((d) => d.filename === filename) || null;
}

/* -------------------------------------------------------------------------- */
/*  Dataset Fetching & Smart Initial Tree Expansion                           */
/* -------------------------------------------------------------------------- */

function seedDefaultExpansion(parsed) {
  const expanded = new Set(['$']);
  const limits = new Map();

  if (Array.isArray(parsed)) {
    limits.set('$', ARRAY_PAGE_SIZE);
    const previewCount = Math.min(parsed.length, 3);
    for (let i = 0; i < previewCount; i++) {
      const childPath = `$[${i}]`;
      if (parsed[i] && typeof parsed[i] === 'object') {
        expanded.add(childPath);
      }
    }
  } else if (parsed && typeof parsed === 'object') {
    const keys = Object.keys(parsed);
    const expandKeysCap = Math.min(keys.length, 6);
    for (let i = 0; i < expandKeysCap; i++) {
      const k = keys[i];
      const v = parsed[k];
      const p = formatChildPath('$', k, false);
      if (Array.isArray(v)) {
        expanded.add(p);
        limits.set(p, ARRAY_PAGE_SIZE);
        if (v.length > 0 && v[0] && typeof v[0] === 'object') {
          expanded.add(`${p}[0]`);
        }
      } else if (v && typeof v === 'object') {
        expanded.add(p);
        const subKeys = Object.keys(v);
        for (let j = 0; j < Math.min(subKeys.length, 4); j++) {
          const sk = subKeys[j];
          const sv = v[sk];
          const sp = formatChildPath(p, sk, false);
          if (Array.isArray(sv)) {
            limits.set(sp, ARRAY_PAGE_SIZE);
            if (sv.length <= 20) expanded.add(sp);
          } else if (sv && typeof sv === 'object' && Object.keys(sv).length <= 14) {
            expanded.add(sp);
          }
        }
      }
    }
  }

  state.expandedPaths = expanded;
  state.arrayLimits = limits;
}

function formatChildPath(parentPath, key, isArrayIndex) {
  if (isArrayIndex) return `${parentPath}[${key}]`;
  if (/^[A-Za-z_][A-Za-z0-9_]*$/.test(key)) return `${parentPath}.${key}`;
  return `${parentPath}[${JSON.stringify(key)}]`;
}

async function selectDataset(filename) {
  const meta = findDatasetMeta(filename);
  if (!meta) return;

  // Ensure folder is expanded if selected via search/hash
  state.collapsedFolders.delete(meta.folder_id);
  state.selectedFile = filename;
  state.activeLinePath = '$';
  state.cursorLn = 1;
  state.cursorCol = 1;
  state.jsonQuery = '';
  state.searchMatchPaths = [];
  state.activeMatchIndex = -1;
  const searchInput = $('inspector-search-input');
  if (searchInput) searchInput.value = '';
  updateMatchNavUi();

  setFileHash(filename);
  renderCatalogPanel();
  updateInspectorHeaderAndBadges(meta, null);

  if (state.cache.has(filename)) {
    const entry = state.cache.get(filename);
    if (entry.validJson) seedDefaultExpansion(entry.parsed);
    renderInspectorBody(meta, entry);
    return;
  }

  state.loadingFile = filename;
  renderInspectorLoading(meta);

  try {
    const res = await fetch(`${meta.path}?t=${Date.now()}`, { cache: 'no-store' });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const rawText = await res.text();
    let parsed = null;
    let validJson = false;
    let parseError = null;

    if (meta.format === 'JSON') {
      try {
        parsed = JSON.parse(rawText);
        validJson = true;
      } catch (err) {
        parseError = err?.message || 'Invalid JSON';
      }
    }

    const entry = {
      format: meta.format,
      rawText,
      parsed,
      validJson,
      parseError,
      fetchError: null,
    };
    state.cache.set(filename, entry);

    if (state.selectedFile === filename) {
      state.loadingFile = null;
      if (validJson) seedDefaultExpansion(parsed);
      renderInspectorBody(meta, entry);
    }
  } catch (err) {
    const entry = {
      format: meta.format,
      rawText: '',
      parsed: null,
      validJson: false,
      parseError: null,
      fetchError: err?.message || 'Fetch failed',
    };
    if (state.selectedFile === filename) {
      state.loadingFile = null;
      renderInspectorBody(meta, entry);
    }
  }
}

/* -------------------------------------------------------------------------- */
/*  Inspector Header, Schema Badges & Search                                  */
/* -------------------------------------------------------------------------- */

function updateInspectorHeaderAndBadges(meta, entry) {
  const crumb = $('inspector-breadcrumb');
  const badges = $('schema-badge-strip');
  const dlJson = $('btn-download-json');
  const dlCsv = $('btn-export-csv');
  const copyBtn = $('btn-copy-json');
  const statusValid = $('status-valid-chip');
  const statusRecs = $('status-records-label');

  if (crumb) {
    crumb.textContent = meta ? meta.path : '–';
    crumb.title = meta ? meta.description : '';
  }

  const ready = Boolean(entry && !entry.fetchError);
  if (dlJson) {
    dlJson.disabled = !ready;
    dlJson.innerHTML = meta?.format === 'MD'
      ? `${downloadSvg()}<span>Download .MD</span>`
      : `${downloadSvg()}<span>Download .JSON</span>`;
  }
  if (dlCsv) dlCsv.disabled = !ready || meta?.format !== 'JSON' || !entry?.validJson;
  if (copyBtn) copyBtn.disabled = !ready;

  if (!meta || !badges) return;

  const isJson = meta.format === 'JSON';
  const validFlag = entry ? (entry.fetchError ? false : isJson ? entry.validJson : true) : meta.valid;
  const validLabel = entry?.fetchError
    ? 'Fetch Error'
    : isJson
      ? (validFlag ? 'Valid JSON' : 'Invalid JSON')
      : 'Valid Markdown';

  badges.innerHTML = `
    <span class="schema-pill fmt-blue">${isJson ? '{}' : 'MD'} ${escapeHtml(meta.format)}</span>
    <span class="schema-pill sch-green" title="${escapeHtml(meta.description)}">Schema: ${escapeHtml(meta.schema_name)}</span>
    <span class="schema-pill rec-purple">Records: ${escapeHtml(meta.row_label)}</span>
    <span class="schema-pill size-amber">Size: ${escapeHtml(meta.size_label)}</span>
    <span class="schema-pill ${validFlag ? 'valid-emerald' : 'invalid-red'}">${validFlag ? '✓' : '✕'} ${escapeHtml(validLabel)}</span>
  `;

  if (statusValid) {
    statusValid.className = `status-valid-chip ${validFlag ? '' : 'is-invalid'}`;
    statusValid.innerHTML = validFlag ? `✓ ${isJson ? 'JSON Valid' : 'Markdown'}` : `✕ ${escapeHtml(validLabel)}`;
    statusValid.title = `sha256:${meta.sha256_short} · ${meta.description}`;
  }
  if (statusRecs) {
    statusRecs.textContent = meta.row_label;
  }
}

function downloadSvg() {
  return `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>`;
}

function renderInspectorLoading(meta) {
  const vp = $('json-tree-scroll');
  if (vp) {
    vp.innerHTML = `<div class="inspector-state-box"><div class="mono" style="font-size:13px;">Loading <strong>${escapeHtml(meta.filename)}</strong> (${escapeHtml(meta.size_label)})...</div></div>`;
  }
}

/* -------------------------------------------------------------------------- */
/*  Collapsible Syntax-Highlighted JSON Tree Builder                          */
/* -------------------------------------------------------------------------- */

function buildJsonTreeLines(rootData) {
  const lines = [];
  const query = state.jsonQuery.trim().toLowerCase();

  function walk(value, keyLabel, path, depth, isLast, isArrayItem) {
    const isObj = value !== null && typeof value === 'object';
    const isArr = Array.isArray(value);

    if (!isObj) {
      lines.push({
        type: 'scalar',
        path,
        depth,
        keyLabel,
        isArrayItem,
        value,
        isLast,
        matchHit: matchesQuery(keyLabel, value, query),
      });
      return;
    }

    const keys = isArr ? null : Object.keys(value);
    const len = isArr ? value.length : keys.length;
    const isExpanded = state.expandedPaths.has(path) && len > 0;
    const keyHit = keyLabel !== null && query && String(keyLabel).toLowerCase().includes(query);

    if (!isExpanded) {
      lines.push({
        type: 'collapsed',
        path,
        depth,
        keyLabel,
        isArrayItem,
        isArr,
        len,
        isLast,
        matchHit: keyHit,
      });
      return;
    }

    lines.push({
      type: 'open',
      path,
      depth,
      keyLabel,
      isArrayItem,
      isArr,
      len,
      matchHit: keyHit,
    });

    if (isArr) {
      const limit = state.arrayLimits.get(path) ?? ARRAY_PAGE_SIZE;
      const shown = Math.min(len, limit);
      for (let i = 0; i < shown; i++) {
        const childPath = `${path}[${i}]`;
        walk(value[i], null, childPath, depth + 1, i === len - 1, true);
      }
      if (shown < len) {
        lines.push({
          type: 'load-more',
          path,
          depth: depth + 1,
          shown,
          total: len,
        });
      }
    } else {
      for (let i = 0; i < keys.length; i++) {
        const k = keys[i];
        const childPath = formatChildPath(path, k, false);
        walk(value[k], k, childPath, depth + 1, i === keys.length - 1, false);
      }
    }

    lines.push({
      type: 'close',
      path,
      depth,
      isArr,
      isLast,
    });
  }

  walk(rootData, null, '$', 0, true, false);
  return lines;
}

function matchesQuery(keyLabel, value, query) {
  if (!query) return false;
  if (keyLabel !== null && String(keyLabel).toLowerCase().includes(query)) return true;
  if (value === null) return 'null'.includes(query);
  if (typeof value === 'boolean' || typeof value === 'number') {
    return String(value).toLowerCase().includes(query);
  }
  if (typeof value === 'string') {
    return value.toLowerCase().includes(query);
  }
  return false;
}

function highlightEscapedText(raw, query) {
  const str = String(raw);
  if (!query) return escapeHtml(str);
  const lower = str.toLowerCase();
  const qLen = query.length;
  let idx = lower.indexOf(query);
  if (idx === -1) return escapeHtml(str);
  let out = '';
  let pos = 0;
  while (idx !== -1) {
    out += escapeHtml(str.slice(pos, idx));
    out += `<mark class="tok-match">${escapeHtml(str.slice(idx, idx + qLen))}</mark>`;
    pos = idx + qLen;
    idx = lower.indexOf(query, pos);
  }
  out += escapeHtml(str.slice(pos));
  return out;
}

function formatScalarHtml(value, query) {
  if (value === null) {
    return `<span class="tok-null">${highlightEscapedText('null', query)}</span>`;
  }
  if (typeof value === 'boolean') {
    return `<span class="tok-bool">${highlightEscapedText(String(value), query)}</span>`;
  }
  if (typeof value === 'number') {
    return `<span class="tok-num">${highlightEscapedText(String(value), query)}</span>`;
  }
  const s = String(value);
  const clipped = s.length > 420 ? `${s.slice(0, 420)}…` : s;
  return `<span class="tok-str">"${highlightEscapedText(clipped, query)}"</span>`;
}

function chevDownMiniSvg() {
  return `<svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polyline points="6 9 12 15 18 9"/></svg>`;
}

function renderInspectorBody(meta, entry) {
  updateInspectorHeaderAndBadges(meta, entry);
  const vp = $('json-tree-scroll');
  if (!vp) return;

  if (!entry || entry.fetchError) {
    vp.innerHTML = `
      <div class="inspector-state-box">
        <div style="font-size:15px;font-weight:700;color:var(--accent-red-text);">Unable to load ${escapeHtml(meta.filename)}</div>
        <div class="mono" style="font-size:12px;">${escapeHtml(entry?.fetchError || 'Network error')}</div>
        <button type="button" class="action-btn" id="retry-active-file-btn">Retry Fetch</button>
      </div>
    `;
    $('retry-active-file-btn')?.addEventListener('click', () => {
      state.cache.delete(meta.filename);
      selectDataset(meta.filename);
    });
    state.renderedLines = [];
    drawMinimap();
    return;
  }

  // Markdown or Raw view or invalid JSON fallback
  if (meta.format !== 'JSON' || !entry.validJson || state.viewMode === 'raw') {
    const lines = entry.rawText.split('\n');
    const previewLimit = 2500;
    const shownLines = lines.slice(0, previewLimit);
    const truncatedNotice = lines.length > previewLimit
      ? `\n\n/* ... Showing first ${previewLimit.toLocaleString()} of ${lines.length.toLocaleString()} lines. Use Download button for full file. ... */`
      : '';
    vp.innerHTML = `<pre class="json-raw-pre">${escapeHtml(shownLines.join('\n') + truncatedNotice)}</pre>`;
    state.renderedLines = shownLines.map((_, idx) => ({ type: 'raw', depth: 0, ln: idx + 1 }));
    updateStatusBar();
    drawMinimap();
    return;
  }

  const query = state.jsonQuery.trim().toLowerCase();
  const lines = buildJsonTreeLines(entry.parsed);
  state.renderedLines = lines;

  const activeMatchPath = state.activeMatchIndex >= 0 ? state.searchMatchPaths[state.activeMatchIndex] : null;
  let ln = 0;
  const html = [];

  for (const row of lines) {
    if (row.type === 'load-more') {
      const rem = row.total - row.shown;
      html.push(`
        <div class="json-load-more-row">
          <button type="button" class="json-more-btn" data-more-path="${escapeHtml(row.path)}" data-more-next="${row.shown + ARRAY_PAGE_SIZE}">
            + Load next ${Math.min(ARRAY_PAGE_SIZE, rem)} items (${row.shown} / ${row.total} shown)
          </button>
          <button type="button" class="json-more-btn" data-more-path="${escapeHtml(row.path)}" data-more-next="${row.total}">
            Show all ${row.total}
          </button>
        </div>
      `);
      continue;
    }

    ln += 1;
    row.ln = ln;
    const indentPx = row.depth * 18 + 20;
    const isActiveLine = row.path === state.activeLinePath && row.type !== 'close';
    const isCurrentMatch = Boolean(activeMatchPath && row.path === activeMatchPath && row.type !== 'close');

    let keyPart = '';
    if (row.keyLabel !== null && row.keyLabel !== undefined) {
      keyPart = `<span class="tok-key">"${highlightEscapedText(row.keyLabel, query)}"</span><span class="tok-punct">: </span>`;
    }

    let bodyHtml = '';
    let toggleHtml = '';

    if (row.type === 'scalar') {
      const comma = row.isLast ? '' : '<span class="tok-punct">,</span>';
      bodyHtml = `${keyPart}${formatScalarHtml(row.value, query)}${comma}`;
    } else if (row.type === 'open') {
      toggleHtml = `<button type="button" class="json-toggle-btn" data-toggle-path="${escapeHtml(row.path)}" aria-label="Collapse node" aria-expanded="true">${chevDownMiniSvg()}</button>`;
      const openCh = row.isArr ? '[' : '{';
      bodyHtml = `${keyPart}<span class="tok-punct">${openCh}</span>`;
    } else if (row.type === 'collapsed') {
      const openCh = row.isArr ? '[' : '{';
      const closeCh = row.isArr ? ']' : '}';
      const comma = row.isLast ? '' : '<span class="tok-punct">,</span>';
      if (row.len > 0) {
        toggleHtml = `<button type="button" class="json-toggle-btn is-collapsed" data-toggle-path="${escapeHtml(row.path)}" aria-label="Expand node" aria-expanded="false">${chevDownMiniSvg()}</button>`;
      }
      const badgeText = row.len === 0 ? '' : `<span class="tok-summary-chip">${row.len} ${row.isArr ? 'items' : 'keys'}</span>`;
      bodyHtml = `${keyPart}<span class="tok-punct">${openCh}</span>${badgeText}<span class="tok-punct">${closeCh}</span>${comma}`;
    } else if (row.type === 'close') {
      const closeCh = row.isArr ? ']' : '}';
      const comma = row.isLast ? '' : '<span class="tok-punct">,</span>';
      bodyHtml = `<span class="tok-punct">${closeCh}</span>${comma}`;
    }

    html.push(`
      <div class="json-line ${isActiveLine ? 'is-active-line' : ''} ${isCurrentMatch ? 'is-match-current' : ''}"
           data-line-path="${escapeHtml(row.path)}"
           data-ln="${ln}"
           data-depth="${row.depth}">
        <span class="json-ln">${ln}</span>
        <div class="json-code-cell" style="padding-left:${indentPx}px;">
          ${toggleHtml}
          <span class="json-content-span">${bodyHtml}</span>
        </div>
      </div>
    `);
  }

  vp.innerHTML = html.join('');
  updateStatusBar();
  drawMinimap();
  syncMinimapThumb();
}

function updateStatusBar() {
  const pathEl = $('statusbar-jsonpath');
  const cursorEl = $('statusbar-cursor');
  if (pathEl) {
    pathEl.textContent = state.activeLinePath || '$';
    pathEl.title = `Active JSONPath: ${state.activeLinePath} (click to copy)`;
  }
  if (cursorEl) {
    cursorEl.textContent = `Ln ${state.cursorLn}, Col ${state.cursorCol}`;
  }
}

/* -------------------------------------------------------------------------- */
/*  Expand All / Collapse All / Recursive Key Search                          */
/* -------------------------------------------------------------------------- */

function expandAllNodes() {
  const entry = state.cache.get(state.selectedFile);
  if (!entry?.validJson) return;
  const expanded = new Set(['$']);
  const limits = new Map();
  let approxLines = 1;

  function walk(val, path) {
    if (approxLines >= EXPAND_ALL_LINE_CAP) return;
    if (!val || typeof val !== 'object') {
      approxLines += 1;
      return;
    }
    if (Array.isArray(val)) {
      if (val.length === 0) return;
      expanded.add(path);
      const cap = Math.min(val.length, ARRAY_PAGE_SIZE);
      limits.set(path, cap);
      approxLines += 2;
      for (let i = 0; i < cap; i++) {
        walk(val[i], `${path}[${i}]`);
        if (approxLines >= EXPAND_ALL_LINE_CAP) break;
      }
    } else {
      const keys = Object.keys(val);
      if (keys.length === 0) return;
      expanded.add(path);
      approxLines += 2;
      for (const k of keys) {
        walk(val[k], formatChildPath(path, k, false));
        if (approxLines >= EXPAND_ALL_LINE_CAP) break;
      }
    }
  }

  walk(entry.parsed, '$');
  state.expandedPaths = expanded;
  state.arrayLimits = limits;
  renderInspectorBody(findDatasetMeta(state.selectedFile), entry);
}

function collapseAllNodes() {
  const entry = state.cache.get(state.selectedFile);
  if (!entry?.validJson) return;
  state.expandedPaths = new Set(['$']);
  state.arrayLimits = new Map();
  renderInspectorBody(findDatasetMeta(state.selectedFile), entry);
}

function expandAncestorsForPath(mp) {
  state.expandedPaths.add('$');
  let cur = '$';
  const rest = mp.slice(1);
  const tokenRegex = /\.([A-Za-z_][A-Za-z0-9_]*)|\[(\d+|"(?:\\.|[^"])*")\]/g;
  let m;
  while ((m = tokenRegex.exec(rest)) !== null) {
    if (m[2] !== undefined && /^\d+$/.test(m[2])) {
      const idx = Number(m[2]);
      const currLim = state.arrayLimits.get(cur) ?? ARRAY_PAGE_SIZE;
      if (idx >= currLim) {
        state.arrayLimits.set(cur, Math.min(idx + 15, 5000));
      }
      state.expandedPaths.add(cur);
      cur = `${cur}[${idx}]`;
    } else if (m[1] !== undefined) {
      state.expandedPaths.add(cur);
      cur = `${cur}.${m[1]}`;
    } else if (m[2] !== undefined) {
      state.expandedPaths.add(cur);
      cur = `${cur}[${m[2]}]`;
    }
  }
}

function runJsonSearch(queryRaw) {
  state.jsonQuery = queryRaw;
  const q = queryRaw.trim().toLowerCase();
  const entry = state.cache.get(state.selectedFile);
  if (!entry?.validJson || !q) {
    state.searchMatchPaths = [];
    state.activeMatchIndex = -1;
    updateMatchNavUi();
    if (entry) renderInspectorBody(findDatasetMeta(state.selectedFile), entry);
    return;
  }

  const matches = [];

  function scan(val, keyLabel, path) {
    if (keyLabel !== null && String(keyLabel).toLowerCase().includes(q)) {
      matches.push(path);
    }
    if (val === null || typeof val !== 'object') {
      if (matchesQuery(null, val, q)) {
        if (matches[matches.length - 1] !== path) matches.push(path);
      }
      return;
    }

    if (Array.isArray(val)) {
      for (let i = 0; i < val.length; i++) {
        scan(val[i], null, `${path}[${i}]`);
        if (matches.length >= 500) break;
      }
    } else {
      for (const k of Object.keys(val)) {
        scan(val[k], k, formatChildPath(path, k, false));
        if (matches.length >= 500) break;
      }
    }
  }

  scan(entry.parsed, null, '$');

  for (const mp of matches.slice(0, MAX_AUTO_EXPAND_MATCHES)) {
    expandAncestorsForPath(mp);
  }

  state.searchMatchPaths = matches;
  state.activeMatchIndex = matches.length > 0 ? 0 : -1;
  updateMatchNavUi();
  renderInspectorBody(findDatasetMeta(state.selectedFile), entry);
  scrollToActiveMatch();
}

function stepMatch(delta) {
  const len = state.searchMatchPaths.length;
  if (len === 0) return;
  state.activeMatchIndex = (state.activeMatchIndex + delta + len) % len;
  const targetPath = state.searchMatchPaths[state.activeMatchIndex];
  if (targetPath) expandAncestorsForPath(targetPath);
  updateMatchNavUi();
  const entry = state.cache.get(state.selectedFile);
  if (entry) renderInspectorBody(findDatasetMeta(state.selectedFile), entry);
  scrollToActiveMatch();
}

function updateMatchNavUi() {
  const nav = $('search-match-nav');
  const count = $('match-count-badge');
  if (!nav || !count) return;
  if (!state.jsonQuery.trim()) {
    nav.hidden = true;
    return;
  }
  nav.hidden = false;
  const total = state.searchMatchPaths.length;
  if (total === 0) {
    count.textContent = '0 matches';
  } else {
    const capNote = total >= 500 ? '+' : '';
    count.textContent = `${state.activeMatchIndex + 1} / ${total}${capNote}`;
  }
}

function scrollToActiveMatch() {
  const cur = document.querySelector('.json-line.is-match-current');
  if (cur) {
    cur.scrollIntoView({ block: 'center', behavior: 'auto' });
  }
}

/* -------------------------------------------------------------------------- */
/*  Minimap Canvas Rendering & Scroll Sync                                    */
/* -------------------------------------------------------------------------- */

function drawMinimap() {
  const canvas = $('json-minimap-canvas');
  const col = $('json-minimap-col');
  if (!canvas || !col) return;

  const w = col.clientWidth || 56;
  const h = col.clientHeight || 400;
  if (w === 0 || h === 0) return;

  const dpr = window.devicePixelRatio || 1;
  canvas.width = Math.floor(w * dpr);
  canvas.height = Math.floor(h * dpr);
  const ctx = canvas.getContext('2d');
  if (!ctx) return;

  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.clearRect(0, 0, w, h);

  const lines = state.renderedLines;
  if (!lines.length) return;

  const isLight = document.documentElement.getAttribute('data-theme') === 'light';
  const maxLines = Math.min(lines.length, 1400);
  const step = lines.length / maxLines;
  const barH = Math.max(1.2, Math.min(2.4, h / maxLines));

  for (let i = 0; i < maxLines; i++) {
    const row = lines[Math.floor(i * step)];
    const y = (i / maxLines) * (h - 4) + 2;
    const indent = Math.min(24, (row?.depth || 0) * 3);
    const barW = Math.max(6, Math.min(w - indent - 6, 12 + ((i * 7) % 22)));

    if (row?.matchHit) {
      ctx.fillStyle = '#FACC15';
    } else if (row?.type === 'open' || row?.type === 'collapsed') {
      ctx.fillStyle = isLight ? 'rgba(2, 132, 199, 0.55)' : 'rgba(86, 212, 245, 0.55)';
    } else if (row?.type === 'scalar') {
      const t = typeof row.value;
      if (t === 'number') ctx.fillStyle = isLight ? 'rgba(21, 128, 61, 0.52)' : 'rgba(74, 222, 128, 0.52)';
      else if (t === 'boolean') ctx.fillStyle = isLight ? 'rgba(126, 34, 206, 0.52)' : 'rgba(192, 132, 252, 0.55)';
      else ctx.fillStyle = isLight ? 'rgba(180, 83, 9, 0.45)' : 'rgba(245, 184, 100, 0.48)';
    } else {
      ctx.fillStyle = isLight ? 'rgba(100, 116, 139, 0.30)' : 'rgba(148, 163, 184, 0.25)';
    }
    ctx.fillRect(4 + indent, y, barW, barH);
  }
}

function syncMinimapThumb() {
  const scrollEl = $('json-tree-scroll');
  const col = $('json-minimap-col');
  const thumb = $('json-minimap-thumb');
  if (!scrollEl || !col || !thumb) return;

  const sh = scrollEl.scrollHeight || 1;
  const ch = scrollEl.clientHeight || 1;
  const mh = col.clientHeight || 1;
  if (sh <= ch) {
    thumb.style.top = '0px';
    thumb.style.height = `${mh}px`;
    return;
  }
  const thumbH = Math.max(24, (ch / sh) * mh);
  const maxTop = mh - thumbH;
  const ratio = scrollEl.scrollTop / Math.max(1, sh - ch);
  thumb.style.height = `${thumbH.toFixed(1)}px`;
  thumb.style.top = `${(ratio * maxTop).toFixed(1)}px`;
}

/* -------------------------------------------------------------------------- */
/*  Real Client-Side Download .JSON & Export .CSV                             */
/* -------------------------------------------------------------------------- */

function triggerBlobDownload(content, filename, mimeType) {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

function downloadActiveJson() {
  const meta = findDatasetMeta(state.selectedFile);
  const entry = state.cache.get(state.selectedFile);
  if (!meta || !entry || entry.fetchError) return;

  if (meta.format === 'JSON' && entry.validJson) {
    const pretty = JSON.stringify(entry.parsed, null, 2);
    triggerBlobDownload(pretty, meta.filename, 'application/json;charset=utf-8');
    showToast(`Downloaded ${meta.filename}`);
  } else {
    triggerBlobDownload(entry.rawText, meta.filename, 'text/plain;charset=utf-8');
    showToast(`Downloaded ${meta.filename}`);
  }
}

function csvCell(val) {
  if (val === null || val === undefined) return '';
  let str;
  if (typeof val === 'object') {
    str = JSON.stringify(val);
  } else {
    str = String(val);
  }
  if (/[",\n\r]/.test(str)) {
    return `"${str.replace(/"/g, '""')}"`;
  }
  return str;
}

function flattenToTabularRows(filename, parsed) {
  // 1. Direct array of objects or primitives
  if (Array.isArray(parsed)) {
    if (parsed.length === 0) return [{ index: 0, value: '' }];
    if (parsed.every((x) => x && typeof x === 'object' && !Array.isArray(x))) {
      return parsed;
    }
    return parsed.map((v, i) => ({ index: i, value: v }));
  }

  if (parsed && typeof parsed === 'object') {
    // 2. backtest_data.json -> flatten trades across all strategy models
    if (filename === 'backtest_data.json') {
      const rows = [];
      for (const [modelKey, modelObj] of Object.entries(parsed)) {
        if (modelObj && Array.isArray(modelObj.trades)) {
          for (const t of modelObj.trades) {
            rows.push({ model: modelKey, symbol: modelObj.symbol || '', ...t });
          }
        }
      }
      if (rows.length > 0) return rows;
    }

    // 3. Multi-symbol stream objects (terminal_stream_data / terminal_compact)
    if (filename === 'terminal_stream_data.json' || filename === 'terminal_compact.json') {
      const rows = [];
      for (const [sym, symObj] of Object.entries(parsed)) {
        const list = symObj?.bars || symObj?.stream || symObj?.initial || [];
        if (Array.isArray(list)) {
          for (const bar of list) {
            rows.push({ symbol: sym, ...bar });
          }
        }
      }
      if (rows.length > 0) return rows;
    }

    // 4. Primary largest array inside object (daystudy rows, alerts, cycles, etc.)
    let bestKey = null;
    let bestArr = null;
    for (const [k, v] of Object.entries(parsed)) {
      if (Array.isArray(v) && v.length > (bestArr?.length || 0)) {
        bestKey = k;
        bestArr = v;
      }
    }
    if (bestArr && bestArr.length > 0) {
      if (bestArr.every((x) => x && typeof x === 'object' && !Array.isArray(x))) {
        return bestArr;
      }
      return bestArr.map((v, i) => ({ section: bestKey, index: i, value: v }));
    }

    // 5. Fallback: flatten nested object keys as path / type / value
    const flatRows = [];
    const flattenWalk = (node, path) => {
      if (node === null || typeof node !== 'object') {
        flatRows.push({
          json_path: path,
          type: node === null ? 'null' : typeof node,
          value: node,
        });
        return;
      }
      if (Array.isArray(node)) {
        if (node.length === 0) {
          flatRows.push({ json_path: path, type: 'array(0)', value: '[]' });
          return;
        }
        node.forEach((item, idx) => flattenWalk(item, `${path}[${idx}]`));
      } else {
        const keys = Object.keys(node);
        if (keys.length === 0) {
          flatRows.push({ json_path: path, type: 'object(0)', value: '{}' });
          return;
        }
        for (const k of keys) {
          flattenWalk(node[k], formatChildPath(path, k, false));
        }
      }
    };
    flattenWalk(parsed, '$');
    return flatRows;
  }

  return [{ value: parsed }];
}

function exportActiveCsv() {
  const meta = findDatasetMeta(state.selectedFile);
  const entry = state.cache.get(state.selectedFile);
  if (!meta || !entry || !entry.validJson) return;

  const rows = flattenToTabularRows(meta.filename, entry.parsed);
  if (!rows.length) return;

  const colSet = new Set();
  for (const r of rows) {
    if (r && typeof r === 'object') {
      for (const k of Object.keys(r)) colSet.add(k);
    }
  }
  const cols = [...colSet];
  const csvLines = [cols.map(csvCell).join(',')];
  for (const r of rows) {
    csvLines.push(cols.map((c) => csvCell(r?.[c])).join(','));
  }

  const csvName = meta.filename.replace(/\.json$/i, '.csv');
  triggerBlobDownload('\uFEFF' + csvLines.join('\r\n'), csvName, 'text/csv;charset=utf-8');
  showToast(`Exported ${rows.length.toLocaleString()} rows to ${csvName}`);
}

/* -------------------------------------------------------------------------- */
/*  Resolve Node at JSONPath for Copy                                         */
/* -------------------------------------------------------------------------- */

function getNodeByPath(root, path) {
  if (!path || path === '$') return root;
  // Parse tokens like $.foo["bar"][0]
  let cur = root;
  const rest = path.slice(1);
  const tokenRegex = /\.([A-Za-z_][A-Za-z0-9_]*)|\[(\d+|"(?:\\.|[^"])*")\]/g;
  let m;
  while ((m = tokenRegex.exec(rest)) !== null) {
    if (cur === null || typeof cur !== 'object') return undefined;
    if (m[1] !== undefined) {
      cur = cur[m[1]];
    } else if (m[2] !== undefined) {
      const raw = m[2];
      const key = raw.startsWith('"') ? JSON.parse(raw) : Number(raw);
      cur = cur[key];
    }
  }
  return cur;
}

/* -------------------------------------------------------------------------- */
/*  Event Binding                                                             */
/* -------------------------------------------------------------------------- */

function bindPageEvents() {
  // Catalog Search
  const catInput = $('catalog-search-input');
  const catClear = $('catalog-search-clear');
  catInput?.addEventListener('input', () => {
    state.catalogQuery = catInput.value;
    if (catClear) catClear.hidden = !catInput.value;
    renderCatalogPanel();
  });
  catClear?.addEventListener('click', () => {
    state.catalogQuery = '';
    if (catInput) catInput.value = '';
    catClear.hidden = true;
    renderCatalogPanel();
    catInput?.focus();
  });

  // Catalog Filter Popover
  const filterBtn = $('catalog-filter-btn');
  const filterPop = $('catalog-filter-popover');
  filterBtn?.addEventListener('click', (e) => {
    e.stopPropagation();
    if (!filterPop) return;
    const open = filterPop.hidden;
    filterPop.hidden = !open;
    filterBtn.setAttribute('aria-expanded', String(open));
  });

  filterPop?.addEventListener('click', (e) => {
    e.stopPropagation();
    const scopeBtn = e.target.closest('[data-scope]');
    if (scopeBtn) {
      state.scope = scopeBtn.dataset.scope;
      filterPop.querySelectorAll('[data-scope]').forEach((b) => b.classList.toggle('is-active', b === scopeBtn));
      renderCatalogPanel();
      return;
    }
    const sortBtn = e.target.closest('[data-sort]');
    if (sortBtn) {
      state.sortBy = sortBtn.dataset.sort;
      filterPop.querySelectorAll('[data-sort]').forEach((b) => b.classList.toggle('is-active', b === sortBtn));
      renderCatalogPanel();
      return;
    }
    const folderAct = e.target.closest('[data-folder-action]');
    if (folderAct) {
      const act = folderAct.dataset.folderAction;
      const folders = state.catalog?.folders || [];
      if (act === 'expand') {
        state.collapsedFolders.clear();
      } else {
        folders.forEach((f) => state.collapsedFolders.add(f.id));
      }
      renderCatalogPanel();
    }
  });

  document.addEventListener('click', (e) => {
    if (filterPop && !filterPop.hidden && !filterPop.contains(e.target) && !filterBtn?.contains(e.target)) {
      filterPop.hidden = true;
      filterBtn?.setAttribute('aria-expanded', 'false');
    }
  });

  // Catalog Tree Delegated Clicks (folder toggle + file selection)
  const catTree = $('catalog-tree-scroll');
  catTree?.addEventListener('click', (e) => {
    const folderBtn = e.target.closest('[data-folder-toggle]');
    if (folderBtn) {
      const fid = folderBtn.dataset.folderToggle;
      if (state.collapsedFolders.has(fid)) {
        state.collapsedFolders.delete(fid);
      } else {
        state.collapsedFolders.add(fid);
      }
      renderCatalogPanel();
      return;
    }
    const fileBtn = e.target.closest('[data-file-select]');
    if (fileBtn) {
      selectDataset(fileBtn.dataset.fileSelect);
    }
  });

  // Keyboard navigation in catalog
  catTree?.addEventListener('keydown', (e) => {
    if (e.key !== 'ArrowDown' && e.key !== 'ArrowUp') return;
    const rows = [...catTree.querySelectorAll('.catalog-file-row')];
    if (!rows.length) return;
    const idx = rows.indexOf(document.activeElement);
    if (idx === -1) return;
    e.preventDefault();
    const next = rows[(idx + (e.key === 'ArrowDown' ? 1 : -1) + rows.length) % rows.length];
    next.focus();
  });

  // Inspector Search
  const inspInput = $('inspector-search-input');
  const inspClear = $('inspector-search-clear');
  let searchDebounce = null;
  inspInput?.addEventListener('input', () => {
    if (inspClear) inspClear.hidden = !inspInput.value;
    if (searchDebounce) clearTimeout(searchDebounce);
    searchDebounce = setTimeout(() => runJsonSearch(inspInput.value), 140);
  });
  inspInput?.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      stepMatch(e.shiftKey ? -1 : 1);
    }
  });
  inspClear?.addEventListener('click', () => {
    if (inspInput) inspInput.value = '';
    inspClear.hidden = true;
    runJsonSearch('');
    inspInput?.focus();
  });

  $('match-prev-btn')?.addEventListener('click', () => stepMatch(-1));
  $('match-next-btn')?.addEventListener('click', () => stepMatch(1));

  // Expand All / Collapse All / View Mode
  $('btn-expand-all')?.addEventListener('click', expandAllNodes);
  $('btn-collapse-all')?.addEventListener('click', collapseAllNodes);

  document.querySelectorAll('[data-view-mode]').forEach((btn) => {
    btn.addEventListener('click', () => {
      state.viewMode = btn.dataset.viewMode;
      document.querySelectorAll('[data-view-mode]').forEach((b) => b.classList.toggle('is-active', b === btn));
      const entry = state.cache.get(state.selectedFile);
      if (entry) renderInspectorBody(findDatasetMeta(state.selectedFile), entry);
    });
  });

  // Download / Export / Copy
  $('btn-download-json')?.addEventListener('click', downloadActiveJson);
  $('btn-export-csv')?.addEventListener('click', exportActiveCsv);
  $('btn-copy-json')?.addEventListener('click', async () => {
    const entry = state.cache.get(state.selectedFile);
    if (!entry) return;
    let payload = entry.rawText;
    if (entry.validJson && state.activeLinePath && state.activeLinePath !== '$') {
      const sub = getNodeByPath(entry.parsed, state.activeLinePath);
      if (sub !== undefined) payload = JSON.stringify(sub, null, 2);
    }
    const ok = await copyText(payload);
    if (ok) {
      showToast(state.activeLinePath !== '$' ? `Copied node ${state.activeLinePath}` : `Copied ${state.selectedFile}`);
    }
  });

  // Statusbar JSONPath click to copy
  $('statusbar-jsonpath')?.addEventListener('click', async () => {
    if (await copyText(state.activeLinePath || '$')) {
      showToast(`Copied JSONPath: ${state.activeLinePath}`);
    }
  });

  // Tree viewport interactions (toggle node, load more array items, select active line)
  const vp = $('json-tree-scroll');
  vp?.addEventListener('click', (e) => {
    const moreBtn = e.target.closest('[data-more-path]');
    if (moreBtn) {
      const path = moreBtn.dataset.morePath;
      const nextLim = Number(moreBtn.dataset.moreNext) || ARRAY_PAGE_SIZE;
      state.arrayLimits.set(path, nextLim);
      const entry = state.cache.get(state.selectedFile);
      if (entry) renderInspectorBody(findDatasetMeta(state.selectedFile), entry);
      return;
    }

    const toggleBtn = e.target.closest('[data-toggle-path]');
    if (toggleBtn) {
      const path = toggleBtn.dataset.togglePath;
      if (state.expandedPaths.has(path)) {
        state.expandedPaths.delete(path);
      } else {
        state.expandedPaths.add(path);
      }
      const entry = state.cache.get(state.selectedFile);
      if (entry) renderInspectorBody(findDatasetMeta(state.selectedFile), entry);
      return;
    }

    const lineEl = e.target.closest('.json-line');
    if (lineEl) {
      vp.querySelectorAll('.json-line.is-active-line').forEach((el) => el.classList.remove('is-active-line'));
      lineEl.classList.add('is-active-line');
      state.activeLinePath = lineEl.dataset.linePath || '$';
      state.cursorLn = Number(lineEl.dataset.ln) || 1;
      state.cursorCol = (Number(lineEl.dataset.depth) || 0) * 2 + 1;
      updateStatusBar();
    }
  });

  vp?.addEventListener('scroll', syncMinimapThumb);

  // Minimap click-to-jump
  const minimapCol = $('json-minimap-col');
  const jumpMinimap = (clientY) => {
    if (!vp || !minimapCol) return;
    const rect = minimapCol.getBoundingClientRect();
    const ratio = Math.max(0, Math.min(1, (clientY - rect.top) / Math.max(1, rect.height)));
    vp.scrollTop = ratio * Math.max(0, vp.scrollHeight - vp.clientHeight);
  };
  let minimapDragging = false;
  minimapCol?.addEventListener('mousedown', (e) => {
    minimapDragging = true;
    jumpMinimap(e.clientY);
  });
  window.addEventListener('mousemove', (e) => {
    if (minimapDragging) jumpMinimap(e.clientY);
  });
  window.addEventListener('mouseup', () => {
    minimapDragging = false;
  });

  // Redraw minimap on theme change or window resize
  const obs = new MutationObserver(() => drawMinimap());
  obs.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });
  window.addEventListener('resize', () => {
    drawMinimap();
    syncMinimapThumb();
  });
}

/* -------------------------------------------------------------------------- */
/*  Boot & Telemetry Synchronization                                          */
/* -------------------------------------------------------------------------- */

async function loadAllTelemetryAndCatalog() {
  state.failedSources = [];
  const [catalog, watchdog, webAlerts, liveStatus, overviewSummary] = await Promise.all([
    fetchJsonSafe('assets/database_catalog.json', 'database_catalog'),
    fetchJsonSafe('data/watchdog_status.json', 'watchdog_status'),
    fetchJsonSafe('data/web_alerts.json', 'web_alerts'),
    fetchJsonSafe('data/live_status.json', 'live_status'),
    fetchJsonSafe('data/overview_summary.json', 'overview_summary'),
  ]);

  updateShellTelemetry({
    watchdog,
    webAlerts,
    liveStatus,
    overviewSummary,
    failedSources: state.failedSources,
  });

  if (catalog) {
    state.catalog = catalog;
    const coreBtn = document.querySelector('[data-scope="core"]');
    const allBtn = document.querySelector('[data-scope="all"]');
    if (coreBtn && catalog.counts?.core_datasets) {
      coreBtn.textContent = `Core Datasets (${catalog.counts.core_datasets})`;
    }
    if (allBtn && catalog.counts?.total_files) {
      allBtn.textContent = `All Files (${catalog.counts.total_files})`;
    }
    const hashFile = getFileFromHash();
    const validHash = hashFile && findDatasetMeta(hashFile);
    if (validHash && !validHash.is_core) {
      state.scope = 'all';
      document.querySelectorAll('[data-scope]').forEach((b) => b.classList.toggle('is-active', b.dataset.scope === 'all'));
    }
    const targetFile = validHash ? validHash.filename : (catalog.default_file || DEFAULT_FILE);
    renderCatalogPanel();
    await selectDataset(targetFile);
  } else {
    const tree = $('catalog-tree-scroll');
    if (tree) {
      tree.innerHTML = `<div class="catalog-empty">Unable to load <code>assets/database_catalog.json</code>.</div>`;
    }
  }
}

function initDatabasePage() {
  mountShell({
    activePage: 'database.html',
    onRetry: loadAllTelemetryAndCatalog,
  });
  bindPageEvents();
  loadAllTelemetryAndCatalog();
}

initDatabasePage();
