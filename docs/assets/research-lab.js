// ANTIGRAVITY QUANT · Page 3 / 8: Research Lab ES Module
import { mountShell, loadShellTelemetryOnly } from './shell.js';

// Research Lab Core Controller (Shared 8-Page Shell Compatible)
(function () {
  'use strict';

  window.RLAB = {
    state: {
      activeTab: 'papers',
      search: '',
      f1: 'ALL',
      f2: 'ALL',
      f3: 'ALL',
      promotedHighlight: null
    },
    renderers: {}
  };

  function escHtml(v) {
    return String(v == null ? '' : v)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }
  window.RLAB.esc = escHtml;

  function observeShellTheme() {
    if (typeof MutationObserver === 'undefined') return;
    var obs = new MutationObserver(function (muts) {
      for (var i = 0; i < muts.length; i++) {
        if (muts[i].attributeName === 'data-theme') {
          if (window.RLAB.renderers.engines && window.RLAB.state.activeTab === 'engines') {
            window.RLAB.renderers.engines.redrawRadar();
          }
          if (window.RLAB.renderers.candlestick && window.RLAB.state.activeTab === 'candlestick') {
            window.RLAB.renderers.candlestick.drawCharts();
          }
          break;
        }
      }
    });
    obs.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });
  }

  function fillSelect(sel, options, selectedVal) {
    if (!sel) return;
    sel.innerHTML = options.map(function (o) {
      return '<option value="' + escHtml(o.value) + '"' + (o.value === selectedVal ? ' selected' : '') + '>' + escHtml(o.label) + '</option>';
    }).join('');
  }

  function configureFiltersForTab(tab) {
    var sInput = document.getElementById('global-search');
    var f1 = document.getElementById('filter-select-1');
    var f2 = document.getElementById('filter-select-2');
    var f3 = document.getElementById('filter-select-3');
    var data = window.LAB_DATA || {};

    if (tab === 'papers') {
      if (sInput) sInput.placeholder = 'Search 193 papers by title, author, ID, mechanism, or tag (e.g. DeepLOB, VWAP, Rough)...';
      var cats = [
        { value: 'ALL', label: 'All Categories (13 · 193)' },
        { value: 'SRC:arXiv', label: 'Source: arXiv (141)' },
        { value: 'SRC:SSRN', label: 'Source: SSRN (52)' }
      ];
      ((data.papers && data.papers.categories) || []).forEach(function (c) {
        cats.push({ value: c.id, label: c.short + ' (' + c.count + ')' });
      });
      fillSelect(f1, cats, window.RLAB.state.f1);
      fillSelect(f2, [
        { value: 'ALL', label: 'All Asset Classes' },
        { value: 'XAUUSD', label: 'XAUUSD (Gold Spot)' },
        { value: 'BTCUSD', label: 'BTCUSD (Bitcoin)' },
        { value: 'ETHUSD', label: 'ETHUSD (Ethereum)' },
        { value: 'GOLD-PERP', label: 'GOLD-PERP' }
      ], window.RLAB.state.f2);
      fillSelect(f3, [
        { value: 'ALL', label: 'All Horizons' },
        { value: 'Tick / L2 DOM', label: 'Tick / L2 DOM' },
        { value: 'M1 / Scalping', label: 'M1 / Scalping' },
        { value: 'M5 - H1 Intraday', label: 'M5 - H1 Intraday' },
        { value: 'Multi-Horizon', label: 'Multi-Horizon' }
      ], window.RLAB.state.f3);
    } else if (tab === 'engines') {
      if (sInput) sInput.placeholder = 'Filter 14 Quant Engines by ID, name, cTrader code, or academic ref (e.g. Kelly, Rough, DeepLOB)...';
      fillSelect(f1, [
        { value: 'ALL', label: 'Dataset: BTCUSD Optimized (Default)' },
        { value: 'btc_base', label: 'Dataset: BTCUSD Baseline' },
        { value: 'eth_base', label: 'Dataset: ETHUSD Baseline' }
      ], window.RLAB.state.f1 === 'ALL' ? 'ALL' : window.RLAB.state.f1);
      fillSelect(f2, [
        { value: 'ALL', label: 'Radar Preset: Top 3 Champions' },
        { value: 'TOP5', label: 'Preset: Top 5 BTC Optimized' },
        { value: 'EXEC', label: 'Preset: Execution & Microstructure' },
        { value: 'RISK', label: 'Preset: Risk & Regime Guards' }
      ], window.RLAB.state.f2);
      fillSelect(f3, [
        { value: 'ALL', label: 'All 14 Engines' },
        { value: 'ACTIVE', label: 'Active Only (Trades > 0)' },
        { value: 'CTRADER', label: 'cTrader Param Mapped (4)' }
      ], window.RLAB.state.f3);
    } else if (tab === 'candlestick') {
      if (sInput) sInput.placeholder = 'Instant Search Dictionary: Heikin-Ashi, VWAP SD, OFI, Doji, PBO, DSR, Rough Vol...';
      fillSelect(f1, [
        { value: 'ALL', label: 'Symbol: XAUUSD / Switch Chart' },
        { value: 'XAUUSD', label: 'Chart Symbol: XAUUSD' },
        { value: 'BTCUSD', label: 'Chart Symbol: BTCUSD' },
        { value: 'ETHUSD', label: 'Chart Symbol: ETHUSD' }
      ], window.RLAB.state.f1);
      fillSelect(f2, [
        { value: 'ALL', label: 'Dict: All Categories (32)' },
        { value: 'Candlestick & HA', label: 'Candlestick & Heikin-Ashi' },
        { value: 'VWAP & Execution', label: 'VWAP & Mean Reversion' },
        { value: 'DOM & Microstructure', label: 'DOM & Microstructure' },
        { value: 'Quant Validation', label: 'Quant & Statistical Tests' }
      ], window.RLAB.state.f2);
      fillSelect(f3, [
        { value: 'ALL', label: 'View: Split Chart + Dictionary' },
        { value: 'SD_ON', label: 'Overlay: Show ±1/±2 VWAP SD' },
        { value: 'SD_OFF', label: 'Overlay: Clean HA + OHLC Only' }
      ], window.RLAB.state.f3);
    } else if (tab === 'foundry') {
      if (sInput) sInput.placeholder = 'Filter STR-001..STR-009, Graveyard bots, or Immune Genes by name, metric, or asset...';
      fillSelect(f1, [
        { value: 'ALL', label: 'All Foundry Statuses (9)' },
        { value: 'PASSED', label: 'Status: PASSED (3)' },
        { value: 'INCUBATING', label: 'Status: INCUBATING (5)' },
        { value: 'REJECTED', label: 'Status: REJECTED (1)' }
      ], window.RLAB.state.f1);
      fillSelect(f2, [
        { value: 'ALL', label: 'All Asset Affinities' },
        { value: 'XAUUSD', label: 'XAUUSD' },
        { value: 'BTCUSD', label: 'BTCUSD' },
        { value: 'ETHUSD', label: 'ETHUSD' },
        { value: 'GOLD-PERP', label: 'GOLD-PERP' }
      ], window.RLAB.state.f2);
      fillSelect(f3, [
        { value: 'ALL', label: 'All Cost Sensitivities' },
        { value: 'ZERO', label: 'Cost Sensitivity: ZERO' },
        { value: 'LOW', label: 'Cost Sensitivity: LOW' },
        { value: 'MEDIUM', label: 'Cost Sensitivity: MEDIUM' },
        { value: 'HIGH', label: 'Cost Sensitivity: HIGH' }
      ], window.RLAB.state.f3);
    }
  }

  window.switchTab = function (tab, opts) {
    if (!tab) return;
    opts = opts || {};
    var prev = window.RLAB.state.activeTab;
    window.RLAB.state.activeTab = tab;

    if (prev !== tab && !opts.keepFilters) {
      window.RLAB.state.f1 = 'ALL';
      window.RLAB.state.f2 = 'ALL';
      window.RLAB.state.f3 = 'ALL';
      if (!opts.keepSearch) {
        window.RLAB.state.search = '';
        var si = document.getElementById('global-search');
        if (si) si.value = '';
      }
    }

    document.querySelectorAll('.workspace-tab').forEach(function (btn) {
      btn.classList.toggle('active', btn.dataset.tab === tab);
    });
    document.querySelectorAll('.tab-pane').forEach(function (pane) {
      pane.classList.toggle('hidden', pane.id !== 'pane-' + tab);
    });

    configureFiltersForTab(tab);

    var r = window.RLAB.renderers[tab];
    if (r && typeof r.onActivate === 'function') {
      r.onActivate(opts);
    }
  };

  window.onGlobalFilterChange = function () {
    var si = document.getElementById('global-search');
    var f1 = document.getElementById('filter-select-1');
    var f2 = document.getElementById('filter-select-2');
    var f3 = document.getElementById('filter-select-3');
    window.RLAB.state.search = si ? si.value : '';
    window.RLAB.state.f1 = f1 ? f1.value : 'ALL';
    window.RLAB.state.f2 = f2 ? f2.value : 'ALL';
    window.RLAB.state.f3 = f3 ? f3.value : 'ALL';

    var tab = window.RLAB.state.activeTab;
    var r = window.RLAB.renderers[tab];
    if (r && typeof r.onFilter === 'function') {
      r.onFilter();
    }
  };

  window.clearGlobalSearch = function () {
    var si = document.getElementById('global-search');
    if (si) si.value = '';
    window.RLAB.state.search = '';
    window.RLAB.state.f1 = 'ALL';
    window.RLAB.state.f2 = 'ALL';
    window.RLAB.state.f3 = 'ALL';
    configureFiltersForTab(window.RLAB.state.activeTab);
    window.onGlobalFilterChange();
  };

  window.promotePaperTarget = function (strId, engineId, paperCode) {
    window.RLAB.state.promotedHighlight = { strId: strId, engineId: engineId, paperCode: paperCode };
    if (strId) {
      window.switchTab('foundry', { keepSearch: false, keepFilters: false, highlightStr: strId });
    } else if (engineId) {
      window.switchTab('engines', { keepSearch: false, keepFilters: false, highlightEngine: engineId });
    }
  };

  function setupKeyboard() {
    document.addEventListener('keydown', function (e) {
      var tag = (document.activeElement && document.activeElement.tagName) || '';
      var inInput = tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT';
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        var si = document.getElementById('global-search');
        if (si) { si.focus(); si.select(); }
      } else if (e.key === '/' && !inInput) {
        e.preventDefault();
        var si2 = document.getElementById('global-search');
        if (si2) si2.focus();
      } else if (e.key === 'Escape') {
        var r = window.RLAB.renderers[window.RLAB.state.activeTab];
        if (r && typeof r.onEscape === 'function') r.onEscape();
      }
    });
  }

  window.initResearchLabApp = function () {
    observeShellTheme();
    setupKeyboard();

    ['papers', 'engines', 'candlestick', 'foundry'].forEach(function (k) {
      var r = window.RLAB.renderers[k];
      if (r && typeof r.init === 'function') r.init();
    });

    var hashTab = (window.location.hash || '').replace('#', '');
    var startTab = ['papers', 'engines', 'candlestick', 'foundry'].indexOf(hashTab) >= 0 ? hashTab : 'papers';
    window.switchTab(startTab, { keepFilters: false });
  };
})();


// Tab 1: 193 Papers Database (True Virtual List + Right Slide-over Inspector Drawer)
(function () {
  'use strict';

  var ROW_HEIGHT = 60;
  var OVERSCAN = 5;
  var initialized = false;
  var allPapers = [];
  var filteredPapers = [];
  var selectedCode = null;
  var drawerOpen = true;
  var sortKey = 'score';
  var sortDir = 'desc';
  var renderPending = false;

  function esc(v) {
    return window.RLAB.esc(v);
  }

  function tagColorClass(tag) {
    var t = String(tag).toLowerCase();
    if (t.indexOf('deeplob') >= 0 || t.indexOf('ofi') >= 0 || t.indexOf('order flow') >= 0 || t.indexOf('l2') >= 0) {
      return 'bg-cyan-500/15 text-cyan-300 border-cyan-500/35';
    }
    if (t.indexOf('vwap') >= 0 || t.indexOf('kelly') >= 0 || t.indexOf('rough') >= 0 || t.indexOf('kalman') >= 0) {
      return 'bg-emerald-500/15 text-emerald-300 border-emerald-500/35';
    }
    if (t.indexOf('ssrn') >= 0 || t.indexOf('hmm') >= 0 || t.indexOf('diffusion') >= 0 || t.indexOf('hawkes') >= 0) {
      return 'bg-purple-500/15 text-purple-300 border-purple-500/35';
    }
    if (t.indexOf('gold') >= 0 || t.indexOf('xau') >= 0 || t.indexOf('news') >= 0 || t.indexOf('risk') >= 0) {
      return 'bg-amber-500/15 text-amber-300 border-amber-500/35';
    }
    return 'bg-sky-500/15 text-sky-300 border-sky-500/35';
  }

  function scoreColorClass(score) {
    if (score >= 0.90) return 'text-emerald-400';
    if (score >= 0.83) return 'text-cyan-400';
    return 'text-amber-300';
  }

  function buildIndex() {
    var payload = (window.LAB_DATA && window.LAB_DATA.papers) || {};
    allPapers = (payload.papers || []).map(function (p) {
      var authorsStr = (p.authors || []).join(' ');
      p._blob = [
        p.code, p.strat_id, p.paper_id, p.title, authorsStr,
        p.cat_short, p.cat_th, (p.tags || []).join(' '),
        (p.assets || []).join(' '), p.source, p.strategy_type,
        p.mechanism, p.entry, p.exit, p.abstract, p.engine_id, p.str_id
      ].join(' ').toLowerCase();
      return p;
    });
  }

  function applyFilterAndSort() {
    var st = window.RLAB.state;
    var q = (st.search || '').trim().toLowerCase();
    var terms = q ? q.split(/\s+/).filter(Boolean) : [];
    var f1 = st.f1 || 'ALL';
    var f2 = st.f2 || 'ALL';
    var f3 = st.f3 || 'ALL';

    filteredPapers = allPapers.filter(function (p) {
      if (f1 === 'SRC:arXiv' && p.source !== 'arXiv') return false;
      else if (f1 === 'SRC:SSRN' && p.source !== 'SSRN') return false;
      else if (f1 !== 'ALL' && f1.indexOf('SRC:') !== 0 && p.cat !== f1) return false;

      if (f2 !== 'ALL' && (p.assets || []).indexOf(f2) < 0) return false;
      if (f3 !== 'ALL' && p.horizon !== f3) return false;

      for (var i = 0; i < terms.length; i++) {
        if (p._blob.indexOf(terms[i]) < 0) return false;
      }
      return true;
    });

    filteredPapers.sort(function (a, b) {
      var av, bv;
      if (sortKey === 'score') { av = a.score; bv = b.score; }
      else if (sortKey === 'year') { av = a.year; bv = b.year; }
      else if (sortKey === 'title') { av = a.title.toLowerCase(); bv = b.title.toLowerCase(); }
      else { av = a.idx; bv = b.idx; }
      if (av < bv) return sortDir === 'asc' ? -1 : 1;
      if (av > bv) return sortDir === 'asc' ? 1 : -1;
      return a.idx - b.idx;
    });

    updateSummaryStats();
    var vp = document.getElementById('papers-viewport');
    if (vp) vp.scrollTop = 0;

    if (filteredPapers.length > 0 && (!selectedCode || !filteredPapers.some(function (x) { return x.code === selectedCode; }))) {
      selectedCode = filteredPapers[0].code;
    } else if (filteredPapers.length === 0) {
      selectedCode = null;
    }

    renderVirtualSlice();
    if (drawerOpen) renderDrawer();
  }

  function updateSummaryStats() {
    var countEl = document.getElementById('papers-count-readout');
    var srcEl = document.getElementById('papers-src-readout');
    if (countEl) {
      countEl.textContent = 'Showing ' + filteredPapers.length + ' of ' + allPapers.length + ' papers · Virtual List (DOM rendered on viewport)';
    }
    if (srcEl) {
      var ax = 0, ss = 0;
      filteredPapers.forEach(function (p) { if (p.source === 'SSRN') ss++; else ax++; });
      srcEl.textContent = 'arXiv: ' + ax + ' · SSRN: ' + ss;
    }
  }

  function renderVirtualSlice() {
    var vp = document.getElementById('papers-viewport');
    var spacer = document.getElementById('papers-spacer');
    var layer = document.getElementById('papers-slice-layer');
    var emptyEl = document.getElementById('papers-empty');
    if (!vp || !spacer || !layer) return;

    var total = filteredPapers.length;
    spacer.style.height = Math.max(ROW_HEIGHT, total * ROW_HEIGHT) + 'px';

    if (total === 0) {
      layer.innerHTML = '';
      if (emptyEl) emptyEl.classList.remove('hidden');
      return;
    }
    if (emptyEl) emptyEl.classList.add('hidden');

    var scrollTop = vp.scrollTop || 0;
    var viewH = vp.clientHeight || 600;
    var start = Math.max(0, Math.floor(scrollTop / ROW_HEIGHT) - OVERSCAN);
    var end = Math.min(total - 1, Math.ceil((scrollTop + viewH) / ROW_HEIGHT) + OVERSCAN);

    var domNodesSpan = document.getElementById('papers-dom-readout');
    if (domNodesSpan) {
      domNodesSpan.textContent = 'DOM Rows: ' + (end - start + 1) + ' / ' + total;
    }

    var html = [];
    for (var i = start; i <= end; i++) {
      var p = filteredPapers[i];
      var isSel = p.code === selectedCode && drawerOpen;
      var topPx = i * ROW_HEIGHT;
      var tagHtml = (p.tags || []).slice(0, 3).map(function (t) {
        return '<span class="tag-pill ' + tagColorClass(t) + '">' + esc(t) + '</span>';
      }).join(' ');
      var subInfo = (p.authors && p.authors[0] ? esc(p.authors[0]) : 'Quant Research') + ' · ' + esc(p.cat_short);

      html.push(
        '<div class="paper-row' + (isSel ? ' selected' : '') + '" style="top:' + topPx + 'px;" data-code="' + esc(p.code) + '" onclick="window.selectPaperRow(\'' + esc(p.code) + '\')">' +
          '<div class="mono text-xs font-semibold text-slate-400">' + (i + 1) + '</div>' +
          '<div class="mono text-xs font-bold text-slate-200">' + esc(p.code) + '<div class="text-[9px] font-normal text-slate-500">' + esc(p.source) + '</div></div>' +
          '<div class="min-w-0 pr-2">' +
            '<div class="text-[13px] font-semibold text-white truncate">' + esc(p.title) + '</div>' +
            '<div class="text-[11px] text-slate-400 truncate">' + subInfo + '</div>' +
          '</div>' +
          '<div class="paper-col-tags flex items-center gap-1 overflow-hidden">' + tagHtml + '</div>' +
          '<div class="mono text-sm font-extrabold tabular-nums text-right pr-2 ' + scoreColorClass(p.score) + '" title="Deterministic Research Alignment Rubric [0.650–0.985] (not an empirical win rate)">' + p.score.toFixed(3) + '</div>' +
          '<div class="paper-col-year mono text-xs text-slate-300 text-center">' + esc(p.year) + '</div>' +
          '<div class="flex justify-center">' +
            '<button type="button" class="px-2 py-1 rounded-md text-xs border border-slate-700/80 text-slate-300 hover:border-cyan-400 hover:text-cyan-300 transition" title="Open Slide-over Paper Inspector">↗</button>' +
          '</div>' +
        '</div>'
      );
    }
    layer.innerHTML = html.join('');
  }

  function renderMath(el, tex) {
    if (!el) return;
    if (window.katex && typeof window.katex.render === 'function') {
      try {
        window.katex.render(tex, el, { displayMode: true, throwOnError: false });
        return;
      } catch (_) {}
    }
    el.innerHTML = '<code class="mono text-xs text-cyan-300 break-words">' + esc(tex) + '</code>';
  }

  function setLayoutDrawerState(open) {
    drawerOpen = open;
    var layout = document.getElementById('papers-layout');
    var drawer = document.getElementById('paper-drawer');
    var backdrop = document.getElementById('drawer-backdrop');
    if (layout) layout.classList.toggle('drawer-open', open);
    if (drawer) {
      drawer.classList.toggle('hidden', !open);
      drawer.classList.toggle('is-open', open);
    }
    if (backdrop) {
      backdrop.classList.toggle('hidden', !open);
    }
    renderVirtualSlice();
  }

  function renderDrawer() {
    var body = document.getElementById('paper-drawer-content');
    if (!body) return;
    var p = allPapers.find(function (x) { return x.code === selectedCode; }) || filteredPapers[0];
    if (!p) {
      body.innerHTML = '<div class="p-6 text-sm text-slate-400">No paper matches the current filter.</div>';
      return;
    }
    selectedCode = p.code;
    setLayoutDrawerState(true);

    var tagsHtml = (p.tags || []).map(function (t) {
      return '<span class="tag-pill ' + tagColorClass(t) + '">' + esc(t) + '</span>';
    }).join('') + (p.assets || []).map(function (a) {
      return '<span class="tag-pill bg-slate-800 text-slate-300 border-slate-700">' + esc(a) + '</span>';
    }).join('');

    var abstractText = p.abstract && p.abstract.trim().length > 10
      ? p.abstract
      : (p.mechanism || p.strategy_type || 'Institutional quantitative study mapped to ' + p.cat_short);

    var abstractLabel = (p.abstract && p.abstract.trim().length > 10)
      ? 'Abstract / Paper Summary'
      : 'Institutional Mechanism (สรุปหลักการทำกำไร)';

    var findings = [];
    if (p.mechanism) findings.push({ ok: true, label: 'Mechanism', text: p.mechanism });
    if (p.entry) findings.push({ ok: true, label: 'Entry Trigger', text: p.entry });
    if (p.exit) findings.push({ ok: true, label: 'Exit / Target', text: p.exit });
    if (p.risks || p.weaknesses) findings.push({ ok: false, label: 'Risk / Weakness', text: p.risks || p.weaknesses });

    var extLinks = '';
    if (p.html_url) {
      extLinks += '<a href="' + esc(p.html_url) + '" target="_blank" rel="noopener noreferrer" class="px-2.5 py-1.5 rounded-lg bg-slate-900 border border-slate-700 hover:border-cyan-400 text-xs font-medium text-cyan-300 transition">Source Paper (' + esc(p.source) + ') ↗</a>';
    }
    if (p.pdf_url) {
      extLinks += '<a href="' + esc(p.pdf_url) + '" target="_blank" rel="noopener noreferrer" class="px-2.5 py-1.5 rounded-lg bg-slate-900 border border-slate-700 hover:border-emerald-400 text-xs font-medium text-emerald-300 transition">PDF Document ↗</a>';
    }

    body.innerHTML =
      '<div class="flex items-start justify-between gap-2 pb-3 border-b border-slate-800/80">' +
        '<div class="flex flex-wrap items-center gap-2">' +
          '<span class="px-2.5 py-1 rounded-lg bg-sky-500/20 text-sky-300 border border-sky-500/40 mono text-xs font-bold">' + esc(p.code) + '</span>' +
          '<span class="px-2.5 py-1 rounded-lg bg-emerald-500/15 text-emerald-300 border border-emerald-500/35 mono text-xs font-bold" title="Deterministic alignment index (not live win rate)">Alignment: ' + p.score.toFixed(3) + '</span>' +
          '<span class="px-2 py-1 rounded-lg bg-slate-800 text-slate-300 mono text-[11px]">' + esc(p.source) + ' · ' + esc(p.year) + '</span>' +
        '</div>' +
        '<button type="button" onclick="window.closePaperDrawer()" class="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition" title="Close Inspector Drawer (Esc)">✕</button>' +
      '</div>' +

      '<div class="mt-3">' +
        '<h3 class="text-base font-extrabold text-white leading-snug">' + esc(p.title) + '</h3>' +
        '<div class="text-xs text-slate-400 mt-1">' + esc((p.authors || []).join(', ')) + ' · ID: <span class="mono text-slate-300">' + esc(p.paper_id || p.strat_id) + '</span></div>' +
        '<div class="flex flex-wrap gap-1.5 mt-2.5">' + tagsHtml + '</div>' +
      '</div>' +

      '<div class="mt-4 space-y-1.5">' +
        '<div class="text-xs font-bold text-slate-200 flex items-center gap-1.5"><span>📄</span> <span>' + esc(abstractLabel) + '</span></div>' +
        '<p class="text-xs leading-relaxed text-slate-300 bg-slate-900/70 border border-slate-800/80 rounded-xl p-3">' + esc(abstractText) + '</p>' +
      '</div>' +

      '<div class="mt-4 space-y-1.5">' +
        '<div class="flex items-center justify-between text-xs font-bold text-slate-200">' +
          '<span class="flex items-center gap-1.5"><span>🧮</span> <span>Key Formula (' + esc(p.cat_short) + ')</span></span>' +
          '<span class="mono text-[10px] text-cyan-400">' + esc(p.engine_id) + '</span>' +
        '</div>' +
        '<div id="drawer-katex-box" class="formula-box text-sm"></div>' +
      '</div>' +

      '<div class="mt-4 space-y-2">' +
        '<div class="text-xs font-bold text-slate-200 flex items-center gap-1.5"><span>💡</span> <span>Key Findings & Execution Translation</span></div>' +
        '<div class="space-y-1.5">' +
          findings.map(function (f) {
            return '<div class="flex items-start gap-2 text-xs leading-relaxed">' +
              '<span class="mt-0.5 shrink-0 ' + (f.ok ? 'text-emerald-400' : 'text-amber-400') + '">' + (f.ok ? '✔' : '⚠') + '</span>' +
              '<div class="text-slate-300"><strong class="text-slate-100">' + esc(f.label) + ':</strong> ' + esc(f.text) + '</div>' +
            '</div>';
          }).join('') +
        '</div>' +
      '</div>' +

      '<div class="mt-4 flex flex-wrap items-center gap-2">' + extLinks + '</div>' +

      '<div class="mt-5 pt-3 border-t border-slate-800/80 grid grid-cols-1 gap-2">' +
        '<button type="button" onclick="window.promotePaperTarget(\'' + esc(p.str_id) + '\', \'' + esc(p.engine_id) + '\', \'' + esc(p.code) + '\')" class="w-full py-2.5 px-4 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-extrabold text-sm flex items-center justify-center gap-2 shadow-lg shadow-cyan-500/20 transition cursor-pointer">' +
          '<span>🚀</span> <span>Promote to Strategy (' + esc(p.str_id) + ') →</span>' +
        '</button>' +
        '<button type="button" onclick="window.promotePaperTarget(null, \'' + esc(p.engine_id) + '\', \'' + esc(p.code) + '\')" class="w-full py-2 px-3 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-200 font-semibold text-xs flex items-center justify-center gap-1.5 transition cursor-pointer">' +
          '<span>⚗️</span> <span>Inspect Quant Engine: ' + esc(p.engine_id) + '</span>' +
        '</button>' +
      '</div>' +
      '<div class="mt-2.5 text-[10px] text-slate-500 leading-snug">' +
        '*Alignment score is a static rubric index (recency, category weight, completeness) — not a forward win-rate promise. All hypotheses must survive Gate 1–5 Validation.' +
      '</div>';

    renderMath(document.getElementById('drawer-katex-box'), p.formula);
  }

  window.selectPaperRow = function (code) {
    selectedCode = code;
    drawerOpen = true;
    renderDrawer();
    renderVirtualSlice();
  };

  window.closePaperDrawer = function () {
    setLayoutDrawerState(false);
  };

  window.sortPapersBy = function (key) {
    if (sortKey === key) {
      sortDir = sortDir === 'desc' ? 'asc' : 'desc';
    } else {
      sortKey = key;
      sortDir = (key === 'title' || key === 'idx') ? 'asc' : 'desc';
    }
    ['idx', 'title', 'score', 'year'].forEach(function (k) {
      var ind = document.getElementById('sort-ind-' + k);
      if (ind) {
        ind.textContent = k === sortKey ? (sortDir === 'desc' ? '▼' : '▲') : '';
      }
    });
    applyFilterAndSort();
  };

  window.RLAB.renderers.papers = {
    init: function () {
      if (initialized) return;
      initialized = true;
      buildIndex();
      var vp = document.getElementById('papers-viewport');
      if (vp) {
        vp.addEventListener('scroll', function () {
          if (renderPending) return;
          renderPending = true;
          requestAnimationFrame(function () {
            renderPending = false;
            renderVirtualSlice();
          });
        }, { passive: true });
        vp.addEventListener('keydown', function (e) {
          if (e.key !== 'ArrowDown' && e.key !== 'ArrowUp') return;
          if (!filteredPapers.length) return;
          e.preventDefault();
          var curIdx = filteredPapers.findIndex(function (p) { return p.code === selectedCode; });
          var nextIdx = e.key === 'ArrowDown'
            ? Math.min(filteredPapers.length - 1, curIdx + 1)
            : Math.max(0, (curIdx < 0 ? 0 : curIdx - 1));
          selectedCode = filteredPapers[nextIdx].code;
          drawerOpen = true;
          var targetTop = nextIdx * ROW_HEIGHT;
          if (targetTop < vp.scrollTop) vp.scrollTop = targetTop;
          else if (targetTop + ROW_HEIGHT > vp.scrollTop + vp.clientHeight) {
            vp.scrollTop = targetTop + ROW_HEIGHT - vp.clientHeight;
          }
          renderDrawer();
          renderVirtualSlice();
        });
      }
      window.addEventListener('resize', function () {
        if (window.RLAB.state.activeTab === 'papers') renderVirtualSlice();
      });
      // Close drawer by default on narrow viewports so mobile users see list first
      if (window.innerWidth < 1100) drawerOpen = false;
      applyFilterAndSort();
    },
    onActivate: function (opts) {
      if (opts && opts.filterCategory) {
        window.RLAB.state.f1 = opts.filterCategory;
        var f1 = document.getElementById('filter-select-1');
        if (f1) f1.value = opts.filterCategory;
      }
      applyFilterAndSort();
    },
    onFilter: function () {
      applyFilterAndSort();
    },
    onEscape: function () {
      if (drawerOpen) window.closePaperDrawer();
    }
  };
})();


// Tab 2: 13 Quant Engines (+ Engine 14 Master Pipeline) Radar Chart, Trajectory & Leaderboard
(function () {
  'use strict';

  var initialized = false;
  var PALETTE = ['#22d3ee', '#34d399', '#f59e0b', '#a855f7', '#fb7185'];
  var PRESETS = {
    TOP3: ['ENGINE_12_KELLY_SIZING', 'ENGINE_13_ROUGH_VOL', 'ENGINE_01_DEEPLOB'],
    TOP5: ['ENGINE_12_KELLY_SIZING', 'ENGINE_13_ROUGH_VOL', 'ENGINE_01_DEEPLOB', 'ENGINE_04_VWAP_SLICER', 'ENGINE_11_NEWS_GATE'],
    EXEC: ['ENGINE_01_DEEPLOB', 'ENGINE_02_OFI_IMPACT', 'ENGINE_04_VWAP_SLICER', 'ENGINE_08_LEAD_LAG'],
    RISK: ['ENGINE_12_KELLY_SIZING', 'ENGINE_11_NEWS_GATE', 'ENGINE_07_HMM_REGIME', 'ENGINE_14_MASTER_PIPELINE']
  };
  var activeOverlays = PRESETS.TOP3.slice();
  var selectedEngineId = 'ENGINE_12_KELLY_SIZING';
  var hoveredEngineId = null;

  function esc(v) { return window.RLAB.esc(v); }

  function getEnginesData() {
    return (window.LAB_DATA && window.LAB_DATA.engines) || { axes: [], engines: [] };
  }

  function getDatasetKey() {
    var f1 = window.RLAB.state.f1;
    if (f1 === 'btc_base' || f1 === 'eth_base') return f1;
    return 'btc_opt';
  }

  function applyPresetIfRequested() {
    var f2 = window.RLAB.state.f2;
    if (f2 === 'TOP5') activeOverlays = PRESETS.TOP5.slice();
    else if (f2 === 'EXEC') activeOverlays = PRESETS.EXEC.slice();
    else if (f2 === 'RISK') activeOverlays = PRESETS.RISK.slice();
    else if (f2 === 'ALL' && window.RLAB.state.f2 === 'ALL') {
      // keep current custom or TOP3
    }
  }

  function filteredEnginesList() {
    var data = getEnginesData();
    var ds = getDatasetKey();
    var q = (window.RLAB.state.search || '').trim().toLowerCase();
    var f3 = window.RLAB.state.f3 || 'ALL';

    return (data.engines || []).filter(function (eng) {
      var m = eng[ds] || eng.btc_opt;
      if (f3 === 'ACTIVE' && !(m && m.trades > 0)) return false;
      if (f3 === 'CTRADER' && !eng.ctrader) return false;
      if (q) {
        var blob = [eng.id, eng.code, eng.name, eng.pillar, eng.ref].join(' ').toLowerCase();
        if (blob.indexOf(q) < 0) return false;
      }
      return true;
    });
  }

  function renderChips() {
    var wrap = document.getElementById('engine-overlay-chips');
    if (!wrap) return;
    var engines = getEnginesData().engines || [];
    wrap.innerHTML = engines.map(function (eng) {
      var ovIdx = activeOverlays.indexOf(eng.id);
      var isSel = eng.id === selectedEngineId;
      var color = ovIdx >= 0 ? PALETTE[ovIdx % PALETTE.length] : null;
      var style = color
        ? 'border-color:' + color + ';background:' + color + '22;color:' + color + ';'
        : '';
      return '<button type="button" onclick="window.toggleEngineOverlay(\'' + esc(eng.id) + '\')" onmouseenter="window.hoverEngineRadar(\'' + esc(eng.id) + '\')" onmouseleave="window.hoverEngineRadar(null)" ' +
        'class="px-2.5 py-1 rounded-lg border text-[11px] font-mono font-bold transition flex items-center gap-1.5 cursor-pointer ' +
        (color ? '' : 'border-slate-700/80 text-slate-400 hover:text-white bg-slate-900/70') +
        (isSel ? ' ring-1 ring-white/50' : '') + '" style="' + style + '">' +
        (color ? '<span class="w-2 h-2 rounded-full" style="background:' + color + '"></span>' : '<span class="w-2 h-2 rounded-full bg-slate-600"></span>') +
        '<span>' + esc(eng.short) + '</span>' +
      '</button>';
    }).join('');
  }

  function renderRadarSvg() {
    var box = document.getElementById('engines-radar-svg');
    var legend = document.getElementById('radar-legend-list');
    if (!box) return;

    var data = getEnginesData();
    var axes = data.axes || [];
    var engines = data.engines || [];
    var ds = getDatasetKey();
    var isLight = document.documentElement.getAttribute('data-theme') === 'light' || document.documentElement.classList.contains('light');
    var ringStroke = isLight ? '#cbd5e1' : '#1e293b';
    var axisStroke = isLight ? '#94a3b8' : '#334155';
    var labelFill = isLight ? '#1e293b' : '#cbd5e1';
    var tickFill = isLight ? '#64748b' : '#64748b';

    var W = 520, H = 410, CX = 260, CY = 205, R = 140;
    var n = axes.length || 6;

    function polar(axisIdx, val) {
      var angle = -Math.PI / 2 + (axisIdx * 2 * Math.PI) / n;
      var rad = (Math.max(0, Math.min(100, val)) / 100) * R;
      return [CX + Math.cos(angle) * rad, CY + Math.sin(angle) * rad];
    }

    var parts = ['<svg viewBox="0 0 ' + W + ' ' + H + '" class="w-full h-auto max-h-[410px]" role="img" aria-label="6-Axis Quant Engine Radar Chart">'];

    // Grid rings
    [20, 40, 60, 80, 100].forEach(function (pct) {
      var pts = [];
      for (var i = 0; i < n; i++) {
        var xy = polar(i, pct);
        pts.push(xy[0].toFixed(1) + ',' + xy[1].toFixed(1));
      }
      parts.push('<polygon points="' + pts.join(' ') + '" fill="none" stroke="' + ringStroke + '" stroke-width="' + (pct === 100 ? '1.5' : '1') + '" stroke-dasharray="' + (pct < 100 ? '3,3' : '0') + '"/>');
      parts.push('<text x="' + (CX + 4) + '" y="' + (CY - (pct / 100) * R + 10) + '" fill="' + tickFill + '" font-size="9" font-family="JetBrains Mono">' + pct + '</text>');
    });

    // Spokes & Axis labels
    for (var i = 0; i < n; i++) {
      var outer = polar(i, 100);
      parts.push('<line x1="' + CX + '" y1="' + CY + '" x2="' + outer[0].toFixed(1) + '" y2="' + outer[1].toFixed(1) + '" stroke="' + axisStroke + '" stroke-width="1"/>');
      var lblPt = polar(i, 121);
      var anchor = Math.abs(lblPt[0] - CX) < 18 ? 'middle' : (lblPt[0] > CX ? 'start' : 'end');
      parts.push('<text x="' + lblPt[0].toFixed(1) + '" y="' + (lblPt[1] + 4).toFixed(1) + '" fill="' + labelFill + '" font-size="11" font-weight="700" text-anchor="' + anchor + '">' + esc(axes[i] || '') + '</text>');
    }

    // Overlays
    var legendHtml = [];
    activeOverlays.forEach(function (eid, idx) {
      var eng = engines.find(function (e) { return e.id === eid; });
      if (!eng) return;
      var color = PALETTE[idx % PALETTE.length];
      var m = eng[ds] || eng.btc_opt;
      var vals = (m && m.radar) || [15, 15, 50, 50, 50, 70];
      var pts = [];
      var dots = [];
      for (var a = 0; a < n; a++) {
        var pt = polar(a, vals[a] || 0);
        pts.push(pt[0].toFixed(1) + ',' + pt[1].toFixed(1));
        dots.push('<circle cx="' + pt[0].toFixed(1) + '" cy="' + pt[1].toFixed(1) + '" r="3.6" fill="' + color + '" stroke="#090d16" stroke-width="1"><title>' + esc(eng.name) + ' · ' + esc(axes[a]) + ': ' + vals[a] + '/100</title></circle>');
      }
      var isEmph = hoveredEngineId ? (hoveredEngineId === eid) : (selectedEngineId === eid);
      var fillOp = hoveredEngineId ? (hoveredEngineId === eid ? '0.32' : '0.07') : (selectedEngineId === eid ? '0.26' : '0.14');
      var sw = isEmph ? '2.8' : '1.8';
      parts.push('<polygon class="radar-poly" points="' + pts.join(' ') + '" fill="' + color + '" fill-opacity="' + fillOp + '" stroke="' + color + '" stroke-width="' + sw + '" style="cursor:pointer" onclick="window.selectEngineInspector(\'' + esc(eid) + '\')"/>');
      parts.push(dots.join(''));

      var pnlStr = (m.pnl >= 0 ? '+$' : '-$') + Math.abs(m.pnl || 0).toFixed(2);
      legendHtml.push(
        '<div onclick="window.selectEngineInspector(\'' + esc(eid) + '\')" class="flex items-center justify-between px-2.5 py-1.5 rounded-lg border cursor-pointer transition ' +
        (selectedEngineId === eid ? 'bg-slate-800/80 border-cyan-500/50' : 'bg-slate-900/60 border-slate-800 hover:border-slate-700') + '">' +
          '<div class="flex items-center gap-2 min-w-0">' +
            '<span class="w-2.5 h-2.5 rounded-full shrink-0" style="background:' + color + '"></span>' +
            '<span class="text-xs font-bold text-white truncate">' + esc(eng.name) + '</span>' +
          '</div>' +
          '<div class="mono text-[11px] font-bold ' + (m.pnl >= 0 ? 'text-emerald-400' : 'text-rose-400') + '">' + pnlStr + ' · PF ' + Number(m.pf || 0).toFixed(2) + '</div>' +
        '</div>'
      );
    });

    parts.push('</svg>');
    box.innerHTML = parts.join('');
    if (legend) legend.innerHTML = legendHtml.join('');
  }

  function renderTrajectorySvg(eng) {
    var traj = eng.trajectory || [];
    if (!traj.length) {
      return '<div class="text-xs text-slate-400 bg-slate-950/60 border border-slate-800 rounded-lg p-3">No coordinate-descent trajectory sweep recorded for this engine (0 trades under BTCUSD cost grid).</div>';
    }
    var pts = [];
    traj.forEach(function (t) {
      var bestStep = (t.steps || []).reduce(function (best, s) {
        return (!best || s.pnl > best.pnl) ? s : best;
      }, null);
      if (bestStep) pts.push({ label: t.var, v: bestStep.v, pnl: bestStep.pnl, pf: bestStep.pf });
    });
    if (!pts.length) return '';

    var W = 380, H = 96, PAD_L = 38, PAD_R = 16, PAD_T = 16, PAD_B = 24;
    var vals = pts.map(function (p) { return p.pnl; });
    var mn = Math.min.apply(null, vals.concat([0]));
    var mx = Math.max.apply(null, vals.concat([1]));
    var span = (mx - mn) || 1;
    function px(i) { return pts.length === 1 ? W / 2 : PAD_L + (i / (pts.length - 1)) * (W - PAD_L - PAD_R); }
    function py(v) { return PAD_T + (1 - (v - mn) / span) * (H - PAD_T - PAD_B); }

    var poly = pts.map(function (p, i) { return px(i).toFixed(1) + ',' + py(p.pnl).toFixed(1); }).join(' ');
    var zeroY = py(0).toFixed(1);
    var circles = pts.map(function (p, i) {
      var x = px(i).toFixed(1), y = py(p.pnl).toFixed(1);
      return '<circle cx="' + x + '" cy="' + y + '" r="3.5" fill="' + (p.pnl >= 0 ? '#34d399' : '#fb7185') + '"><title>' + esc(p.label) + '=' + esc(p.v) + ' → PnL $' + p.pnl.toFixed(2) + ' (PF ' + p.pf.toFixed(2) + ')</title></circle>' +
        '<text x="' + x + '" y="' + (H - 6) + '" font-size="8.5" fill="#94a3b8" text-anchor="middle" font-family="JetBrains Mono">' + esc(p.label.slice(0, 8)) + '</text>';
    }).join('');

    return '<svg viewBox="0 0 ' + W + ' ' + H + '" class="w-full h-24 bg-slate-950/60 border border-slate-800 rounded-lg">' +
      '<line x1="' + PAD_L + '" y1="' + zeroY + '" x2="' + (W - PAD_R) + '" y2="' + zeroY + '" stroke="#334155" stroke-dasharray="3,3"/>' +
      '<text x="4" y="' + (Number(zeroY) + 3) + '" font-size="8.5" fill="#64748b" font-family="JetBrains Mono">$0</text>' +
      '<polyline fill="none" stroke="#22d3ee" stroke-width="2" points="' + poly + '"/>' +
      circles +
    '</svg>';
  }

  function renderInspector() {
    var box = document.getElementById('engine-inspector-panel');
    if (!box) return;
    var engines = getEnginesData().engines || [];
    var eng = engines.find(function (e) { return e.id === selectedEngineId; }) || engines[0];
    if (!eng) return;

    var ds = getDatasetKey();
    var m = eng[ds] || eng.btc_opt;
    var opt = eng.btc_opt || {};
    var pnlPos = Number(m.pnl || 0) >= 0;
    var radarAxes = getEnginesData().axes || [];
    var radarVals = m.radar || [];

    var ctraderHtml = eng.ctrader
      ? '<div class="mt-3 space-y-1.5">' +
          '<div class="flex items-center justify-between text-xs font-bold text-slate-200">' +
            '<span>⚙️ cTrader Automate Parameter Mapping (' + esc(eng.ctrader.strategy_code) + ')</span>' +
          '</div>' +
          '<div class="text-[11px] text-amber-300 font-mono">' + esc(eng.ctrader.sl_tp_note) + '</div>' +
          '<div class="overflow-x-auto rounded-lg border border-slate-800">' +
            '<table class="w-full text-[11px] font-mono text-left">' +
              '<thead class="bg-slate-900 text-slate-400"><tr><th class="px-2.5 py-1.5">Parameter</th><th class="px-2.5 py-1.5">Optimal</th><th class="px-2.5 py-1.5">Sweep Range</th></tr></thead>' +
              '<tbody class="divide-y divide-slate-800/80">' +
                eng.ctrader.params.map(function (pr) {
                  return '<tr><td class="px-2.5 py-1.5 text-cyan-300 font-bold">' + esc(pr.name) + '</td><td class="px-2.5 py-1.5 text-emerald-300 font-bold">' + esc(pr.def) + '</td><td class="px-2.5 py-1.5 text-slate-400">' + esc(pr.range) + '</td></tr>';
                }).join('') +
              '</tbody>' +
            '</table>' +
          '</div>' +
        '</div>'
      : '';

    var optParams = Object.entries(opt.params || {});
    var paramsBadges = optParams.map(function (kv) {
      return '<span class="px-2 py-0.5 rounded bg-slate-900 border border-slate-800 mono text-[10px] text-slate-300"><strong class="text-cyan-300">' + esc(kv[0]) + '</strong>=' + esc(kv[1]) + '</span>';
    }).join(' ');

    box.innerHTML =
      '<div class="flex items-start justify-between gap-2 border-b border-slate-800 pb-3">' +
        '<div>' +
          '<div class="flex items-center gap-2">' +
            '<span class="px-2 py-0.5 rounded bg-cyan-500/15 text-cyan-300 border border-cyan-500/35 mono text-[11px] font-bold">' + esc(eng.id) + '</span>' +
            '<span class="px-2 py-0.5 rounded bg-slate-800 text-slate-300 mono text-[11px]">' + esc(eng.code) + '</span>' +
          '</div>' +
          '<h3 class="text-base font-extrabold text-white mt-1.5">' + esc(eng.name) + '</h3>' +
          '<div class="text-xs text-slate-400">' + esc(eng.pillar) + ' · <span class="text-slate-300">' + esc(eng.ref) + '</span></div>' +
        '</div>' +
      '</div>' +

      '<div class="grid grid-cols-2 sm:grid-cols-4 gap-2 mt-3">' +
        '<div class="p-2.5 rounded-xl bg-slate-900/80 border border-slate-800"><div class="text-[10px] text-slate-400">Net PnL (' + esc(ds.toUpperCase()) + ')</div><div class="mono text-sm font-extrabold ' + (pnlPos ? 'text-emerald-400' : 'text-rose-400') + '">' + (pnlPos ? '+$' : '-$') + Math.abs(m.pnl || 0).toFixed(2) + '</div></div>' +
        '<div class="p-2.5 rounded-xl bg-slate-900/80 border border-slate-800"><div class="text-[10px] text-slate-400">Profit Factor</div><div class="mono text-sm font-extrabold text-cyan-300">' + Number(m.pf || 0).toFixed(2) + '</div></div>' +
        '<div class="p-2.5 rounded-xl bg-slate-900/80 border border-slate-800"><div class="text-[10px] text-slate-400">Win Rate / Trades</div><div class="mono text-sm font-extrabold text-white">' + Number(m.wr || 0).toFixed(1) + '% <span class="text-[11px] text-slate-400">(' + esc(m.trades) + ')</span></div></div>' +
        '<div class="p-2.5 rounded-xl bg-slate-900/80 border border-slate-800"><div class="text-[10px] text-slate-400">Max DD · Params</div><div class="mono text-sm font-extrabold text-amber-300">$' + Number(m.dd || 0).toFixed(2) + ' <span class="text-[11px] text-slate-400">(' + esc(eng.param_count) + 'p)</span></div></div>' +
      '</div>' +

      '<div class="mt-3">' +
        '<div class="text-[11px] font-bold text-slate-300 mb-1">6-Axis Normalized Strength Profile (0–100)</div>' +
        '<div class="grid grid-cols-2 sm:grid-cols-3 gap-1.5">' +
          radarAxes.map(function (ax, i) {
            return '<div class="px-2 py-1 rounded bg-slate-900/60 border border-slate-800/80 flex items-center justify-between text-[11px]"><span class="text-slate-400 truncate mr-1">' + esc(ax.split(' ')[0]) + '</span><span class="mono font-bold text-cyan-300">' + (radarVals[i] || 0) + '</span></div>';
          }).join('') +
        '</div>' +
      '</div>' +

      '<div class="mt-3 space-y-1.5">' +
        '<div class="flex items-center justify-between text-xs font-bold text-slate-200">' +
          '<span>📈 Coordinate-Descent Optimization Trajectory</span>' +
          '<span class="mono text-[11px] ' + (opt.gain >= 0 ? 'text-emerald-400' : 'text-slate-400') + '">Base $' + Number(opt.base_pnl || 0).toFixed(2) + ' → Opt $' + Number(opt.pnl || 0).toFixed(2) + '</span>' +
        '</div>' +
        renderTrajectorySvg(eng) +
        (paramsBadges ? '<div class="flex flex-wrap gap-1 pt-1">' + paramsBadges + '</div>' : '') +
      '</div>' +

      ctraderHtml +

      '<div class="mt-3 pt-2 border-t border-slate-800 flex items-center justify-between">' +
        '<span class="text-[11px] text-slate-400">ETH Opt Subset: ' + (eng.eth_opt_subset ? 'Checked ($' + Number((eng.eth_opt_subset.optimized_metrics || {}).net_pnl || 0).toFixed(2) + ')' : 'Baseline tested') + '</span>' +
        '<button type="button" onclick="window.openEnginePapers(\'' + esc(eng.id) + '\')" class="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-cyan-300 transition cursor-pointer">Related Papers →</button>' +
      '</div>';
  }

  function renderScorecardTable() {
    var tbody = document.getElementById('engines-table-body');
    if (!tbody) return;
    var rows = filteredEnginesList();
    var ds = getDatasetKey();

    tbody.innerHTML = rows.map(function (eng) {
      var m = eng[ds] || eng.btc_opt;
      var inRadar = activeOverlays.indexOf(eng.id) >= 0;
      var isSel = eng.id === selectedEngineId;
      var pnl = Number(m.pnl || 0);
      return '<tr onclick="window.selectEngineInspector(\'' + esc(eng.id) + '\')" class="border-b border-slate-800/70 cursor-pointer transition ' +
        (isSel ? 'bg-cyan-500/12' : 'hover:bg-slate-900/70') + '">' +
        '<td class="px-3 py-2 text-center" onclick="event.stopPropagation()">' +
          '<input type="checkbox" ' + (inRadar ? 'checked' : '') + ' onchange="window.toggleEngineOverlay(\'' + esc(eng.id) + '\')" class="accent-cyan-400 cursor-pointer" title="Toggle in Radar Chart (max 5)"/>' +
        '</td>' +
        '<td class="px-3 py-2">' +
          '<div class="font-bold text-white text-xs">' + esc(eng.name) + '</div>' +
          '<div class="mono text-[10px] text-slate-400">' + esc(eng.id) + ' · ' + esc(eng.code) + '</div>' +
        '</td>' +
        '<td class="px-3 py-2 text-xs text-slate-300 hidden md:table-cell">' + esc(eng.pillar) + '</td>' +
        '<td class="px-3 py-2 mono text-xs text-right font-bold ' + (pnl >= 0 ? 'text-emerald-400' : 'text-rose-400') + '">' + (pnl >= 0 ? '+$' : '-$') + Math.abs(pnl).toFixed(2) + '</td>' +
        '<td class="px-3 py-2 mono text-xs text-right text-cyan-300 font-bold">' + Number(m.pf || 0).toFixed(2) + '</td>' +
        '<td class="px-3 py-2 mono text-xs text-right text-slate-200">' + Number(m.wr || 0).toFixed(1) + '%</td>' +
        '<td class="px-3 py-2 mono text-xs text-right text-amber-300">$' + Number(m.dd || 0).toFixed(2) + '</td>' +
        '<td class="px-3 py-2 mono text-xs text-right text-slate-400">' + esc(m.trades) + '</td>' +
      '</tr>';
    }).join('');
  }

  window.toggleEngineOverlay = function (eid) {
    var idx = activeOverlays.indexOf(eid);
    if (idx >= 0) {
      if (activeOverlays.length > 1) activeOverlays.splice(idx, 1);
    } else {
      if (activeOverlays.length >= 5) activeOverlays.shift();
      activeOverlays.push(eid);
    }
    selectedEngineId = eid;
    renderChips();
    renderRadarSvg();
    renderInspector();
    renderScorecardTable();
  };

  window.applyRadarPreset = function (key) {
    if (PRESETS[key]) {
      activeOverlays = PRESETS[key].slice();
      selectedEngineId = activeOverlays[0];
      renderChips();
      renderRadarSvg();
      renderInspector();
      renderScorecardTable();
    }
  };

  window.selectEngineInspector = function (eid) {
    selectedEngineId = eid;
    if (activeOverlays.indexOf(eid) < 0) {
      if (activeOverlays.length >= 5) activeOverlays.shift();
      activeOverlays.push(eid);
    }
    renderChips();
    renderRadarSvg();
    renderInspector();
    renderScorecardTable();
  };

  window.hoverEngineRadar = function (eid) {
    hoveredEngineId = eid;
    renderRadarSvg();
  };

  window.openEnginePapers = function (eid) {
    var cats = (window.LAB_DATA && window.LAB_DATA.papers && window.LAB_DATA.papers.categories) || [];
    var match = cats.find(function (c) { return c.engine_id === eid; });
    window.switchTab('papers', { keepFilters: true, filterCategory: match ? match.id : 'ALL' });
  };

  function renderAll() {
    applyPresetIfRequested();
    renderChips();
    renderRadarSvg();
    renderInspector();
    renderScorecardTable();
    var noteEl = document.getElementById('engines-weekend-note');
    if (noteEl && window.LAB_DATA && window.LAB_DATA.engines) {
      noteEl.textContent = window.LAB_DATA.engines.weekend_anomaly_note || '';
    }
  }

  window.RLAB.renderers.engines = {
    init: function () {
      if (initialized) return;
      initialized = true;
    },
    onActivate: function (opts) {
      if (opts && opts.highlightEngine) {
        selectedEngineId = opts.highlightEngine;
        if (activeOverlays.indexOf(selectedEngineId) < 0) {
          if (activeOverlays.length >= 5) activeOverlays.shift();
          activeOverlays.push(selectedEngineId);
        }
      }
      renderAll();
    },
    onFilter: function () {
      renderAll();
    },
    redrawRadar: function () {
      renderRadarSvg();
    }
  };
})();


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


// Tab 4: Strategy Foundry (STR-001..STR-009 Status Board, Micro-Forward Fleet, Failure Graveyard & Immune Genes)
(function () {
  'use strict';

  var initialized = false;
  var activeStatusFilter = 'ALL';

  function esc(v) { return window.RLAB.esc(v); }

  function statusBadgeClass(st) {
    if (st === 'PASSED') return 'badge-passed';
    if (st === 'REJECTED') return 'badge-rejected';
    return 'badge-incubating';
  }

  function costColorClass(cost) {
    if (cost === 'ZERO') return 'text-emerald-400 bg-emerald-500/15 border-emerald-500/30';
    if (cost === 'LOW') return 'text-cyan-300 bg-cyan-500/15 border-cyan-500/30';
    if (cost === 'HIGH') return 'text-rose-300 bg-rose-500/15 border-rose-500/30';
    return 'text-amber-300 bg-amber-500/15 border-amber-500/30';
  }

  function renderFunnelBanner() {
    var box = document.getElementById('foundry-funnel-banner');
    if (!box) return;
    var f = (window.LAB_DATA && window.LAB_DATA.foundry) || {};
    var fs = f.foundry_stats || {};
    var tg = (f.truth_guard && f.truth_guard.metrics_empirical) || {};
    var sp = (f.truth_guard && f.truth_guard.statistical_power) || {};
    var av = f.autonomous_validation || {};
    var dsr = av.real_dsr_results || {};
    var pbo = av.real_pbo_cscv || {};
    var sprt = av.real_sprt_sequential_test || {};

    box.innerHTML =
      '<div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2.5">' +
        '<div class="lab-card p-3"><div class="text-[10px] text-slate-400">Hypotheses Screened</div><div class="mono text-lg font-black text-white mt-0.5">' + esc(fs.total_screened_by_math || 1420) + '</div><div class="text-[10px] text-cyan-300 font-mono">Sieve Active</div></div>' +
        '<div class="lab-card p-3"><div class="text-[10px] text-slate-400">Foundry Rejection Rate</div><div class="mono text-lg font-black text-rose-400 mt-0.5">' + Number(fs.rejection_rate_pct || 98.0).toFixed(1) + '%</div><div class="text-[10px] text-slate-400 font-mono">' + esc(fs.discarded_to_graveyard || 1392) + ' Discarded</div></div>' +
        '<div class="lab-card p-3"><div class="text-[10px] text-slate-400">Micro-Forward Bots</div><div class="mono text-lg font-black text-emerald-400 mt-0.5">' + esc(fs.active_micro_forward || 3) + ' LIVE</div><div class="text-[10px] text-slate-400 font-mono">0.01 Lot (' + esc(fs.auto_decommissioned_retired || 25) + ' retired)</div></div>' +
        '<div class="lab-card p-3"><div class="text-[10px] text-slate-400">Live Sample Power</div><div class="mono text-lg font-black text-amber-300 mt-0.5">N=' + esc(tg.total_closed_trades_N || 79) + '/' + esc(sp.target_n || 500) + '</div><div class="text-[10px] text-rose-300 font-mono">' + Number(sp.power_pct || 15.8).toFixed(1) + '% · UNDERPOWERED</div></div>' +
        '<div class="lab-card p-3"><div class="text-[10px] text-slate-400">Live Portfolio (Truth)</div><div class="mono text-lg font-black text-rose-400 mt-0.5">-$' + Math.abs(tg.net_pnl_usd || 17.07).toFixed(2) + '</div><div class="text-[10px] text-slate-400 font-mono">WR ' + Number(tg.win_rate_pct || 34.2).toFixed(1) + '% · PF ' + Number(tg.profit_factor || 0.79).toFixed(2) + '</div></div>' +
        '<div class="lab-card p-3"><div class="text-[10px] text-slate-400">Honest Overfit Tests</div><div class="mono text-sm font-extrabold text-cyan-300 mt-1">DSR ' + Number(dsr.dsr_stat || 0.0362).toFixed(4) + '</div><div class="text-[10px] text-slate-400 font-mono">PBO ' + Number(pbo.pbo || 0.6).toFixed(2) + ' · ' + esc(sprt.verdict || 'COLLECT_MORE_DATA') + '</div></div>' +
      '</div>';
  }

  function renderStrategyCards() {
    var grid = document.getElementById('foundry-cards-grid');
    if (!grid) return;
    var f = (window.LAB_DATA && window.LAB_DATA.foundry) || {};
    var cards = f.cards || [];
    var st = window.RLAB.state;

    var statusF = st.f1 !== 'ALL' ? st.f1 : activeStatusFilter;
    var assetF = st.f2 || 'ALL';
    var costF = st.f3 || 'ALL';
    var q = (st.search || '').trim().toLowerCase();
    var terms = q ? q.split(/\s+/).filter(Boolean) : [];
    var hlStr = (st.promotedHighlight && st.promotedHighlight.strId) || '';

    // Update quick pills
    var counts = { ALL: cards.length, PASSED: 0, INCUBATING: 0, REJECTED: 0 };
    cards.forEach(function (c) { counts[c.foundry_status] = (counts[c.foundry_status] || 0) + 1; });
    document.querySelectorAll('.foundry-status-btn').forEach(function (btn) {
      var k = btn.dataset.st;
      var active = statusF === k;
      btn.classList.toggle('bg-cyan-500/20', active);
      btn.classList.toggle('text-cyan-300', active);
      btn.classList.toggle('border-cyan-500/50', active);
      var sp = btn.querySelector('.cnt');
      if (sp) sp.textContent = counts[k] || 0;
    });

    var filtered = cards.filter(function (c) {
      if (statusF !== 'ALL' && c.foundry_status !== statusF) return false;
      if (assetF !== 'ALL' && (c.assets || []).indexOf(assetF) < 0) return false;
      if (costF !== 'ALL' && c.cost_sensitivity !== costF) return false;
      if (terms.length) {
        var blob = [c.id, c.name, c.th_name, c.hypothesis, c.evidence, (c.engines || []).join(' '), (c.assets || []).join(' '), c.foundry_status].join(' ').toLowerCase();
        return terms.every(function (t) { return blob.indexOf(t) >= 0; });
      }
      return true;
    });

    if (!filtered.length) {
      grid.innerHTML = '<div class="col-span-full lab-card p-6 text-center text-xs text-slate-400">No STR cards matched current filter criteria.</div>';
      return;
    }

    grid.innerHTML = filtered.map(function (c) {
      var isPromoted = hlStr && c.id === hlStr;
      var params = Object.entries(c.params || {}).slice(0, 6).map(function (kv) {
        return '<span class="px-1.5 py-0.5 rounded bg-slate-900 border border-slate-800 mono text-[10px] text-slate-300"><span class="text-cyan-300">' + esc(kv[0]) + '</span>: ' + esc(kv[1]) + '</span>';
      }).join(' ');
      var engBtns = (c.engines || []).map(function (eid) {
        return '<button type="button" onclick="window.promotePaperTarget(null, \'' + esc(eid) + '\', \'' + esc(c.id) + '\')" class="px-2 py-0.5 rounded bg-sky-500/15 hover:bg-sky-500/25 border border-sky-500/35 mono text-[10px] font-bold text-sky-300 transition cursor-pointer">⚗️ ' + esc(eid) + '</button>';
      }).join(' ');
      var assetTags = (c.assets || []).map(function (a) {
        return '<span class="px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 mono text-[10px]">' + esc(a) + '</span>';
      }).join(' ');

      return '<div id="card-' + esc(c.id) + '" class="lab-card p-4 flex flex-col justify-between gap-3 ' +
        (isPromoted ? 'ring-2 ring-cyan-400 shadow-lg shadow-cyan-500/20' : '') + '">' +
        '<div class="space-y-2">' +
          '<div class="flex items-start justify-between gap-2">' +
            '<div class="flex items-center gap-2">' +
              '<span class="px-2 py-0.5 rounded-md bg-slate-900 border border-slate-700 mono text-xs font-extrabold text-white">' + esc(c.id) + '</span>' +
              '<span class="mono text-[10px] text-slate-400">v' + esc(c.version) + '</span>' +
              '<span class="px-1.5 py-0.5 rounded border mono text-[10px] font-bold ' + costColorClass(c.cost_sensitivity) + '">COST: ' + esc(c.cost_sensitivity) + '</span>' +
            '</div>' +
            '<span class="px-2.5 py-0.5 rounded-full border mono text-[11px] font-extrabold ' + statusBadgeClass(c.foundry_status) + '">' + esc(c.foundry_status) + '</span>' +
          '</div>' +

          '<div>' +
            '<h3 class="text-sm font-extrabold text-white leading-snug">' + esc(c.name) + '</h3>' +
            '<div class="text-xs text-amber-300 font-medium mt-0.5">' + esc(c.th_name) + '</div>' +
          '</div>' +

          '<p class="text-xs text-slate-300 leading-relaxed">' + esc(c.hypothesis) + '</p>' +

          '<div class="p-2.5 rounded-lg bg-slate-950/75 border border-slate-800/80 text-[11px] text-slate-200 leading-relaxed">' +
            '<strong class="text-cyan-300">Audit Evidence (' + esc(c.registry_status) + '):</strong> ' + esc(c.evidence) +
          '</div>' +

          (params ? '<div class="flex flex-wrap gap-1">' + params + '</div>' : '') +
        '</div>' +

        '<div class="pt-2 border-t border-slate-800/80 flex flex-wrap items-center justify-between gap-2">' +
          '<div class="flex flex-wrap gap-1">' + assetTags + '</div>' +
          '<div class="flex flex-wrap gap-1">' + engBtns + '</div>' +
        '</div>' +
      '</div>';
    }).join('');
  }

  function renderBottomTelemetry() {
    var botEl = document.getElementById('foundry-bots-panel');
    var graveEl = document.getElementById('foundry-graveyard-panel');
    var f = (window.LAB_DATA && window.LAB_DATA.foundry) || {};

    if (botEl) {
      var activeBots = f.active_micro_bots || [];
      var retiredBots = f.retired_bots || [];
      botEl.innerHTML =
        '<div class="text-xs font-extrabold text-white mb-2 flex items-center justify-between">' +
          '<span>🤖 Active Micro-Forward Bots (0.01 Lot Live) &amp; Decommissioned</span>' +
          '<span class="mono text-[10px] text-amber-300">Auto-Retire Triggered @ 33.5 avg trades</span>' +
        '</div>' +
        '<div class="space-y-2">' +
          activeBots.map(function (b) {
            return '<div class="p-2.5 rounded-lg bg-slate-900/75 border border-emerald-500/30 text-xs">' +
              '<div class="flex items-center justify-between font-mono font-bold">' +
                '<span class="text-emerald-300">' + esc(b.symbol) + ' · ' + esc(b.strategy) + '</span>' +
                '<span class="text-amber-300">Live PF ' + Number(b.live_realized_pf || 0).toFixed(2) + ' (N=' + esc(b.trades_count) + ') · Decay ' + esc(b.decay_pct) + '%</span>' +
              '</div>' +
              '<div class="text-[11px] text-slate-400 mt-1">In-sample PF ' + Number(b.in_sample_pf || 0).toFixed(2) + ' · ' + esc(b.decommission_trigger) + '</div>' +
            '</div>';
          }).join('') +
          retiredBots.map(function (r) {
            return '<div class="p-2.5 rounded-lg bg-slate-950/75 border border-rose-500/25 text-xs">' +
              '<div class="flex items-center justify-between font-mono">' +
                '<span class="text-rose-300 font-bold">RETIRED · ' + esc(r.symbol) + ' · ' + esc(r.strategy) + '</span>' +
                '<span class="text-slate-400">Final PF ' + Number(r.final_pf || 0).toFixed(2) + ' (N=' + esc(r.total_trades_at_retirement) + ')</span>' +
              '</div>' +
              '<div class="text-[11px] text-slate-400 mt-0.5">' + esc(r.reason) + '</div>' +
            '</div>';
          }).join('') +
        '</div>';
    }

    if (graveEl) {
      var grave = f.graveyard || [];
      var genes = f.immune_genes || [];
      graveEl.innerHTML =
        '<div class="text-xs font-extrabold text-white mb-2 flex items-center justify-between">' +
          '<span>☠️ Failure Graveyard &amp; Permanent Immune Memory</span>' +
          '<span class="mono text-[10px] text-rose-300">' + grave.length + ' Banned · ' + genes.length + ' Immune Genes</span>' +
        '</div>' +
        '<div class="space-y-2">' +
          genes.map(function (g) {
            return '<div class="p-2.5 rounded-lg bg-amber-950/20 border border-amber-500/35 text-xs">' +
              '<div class="font-mono font-bold text-amber-300">🛡️ ' + esc(g.gene_id) + '</div>' +
              '<div class="text-[11px] text-slate-200 mt-0.5">' + esc(g.immune_countermeasure) + '</div>' +
              '<div class="text-[10px] text-slate-400 mt-0.5">Origin: ' + esc(g.discovered_from_loss) + '</div>' +
            '</div>';
          }).join('') +
          grave.map(function (gv) {
            return '<div class="p-2.5 rounded-lg bg-rose-950/20 border border-rose-500/30 text-xs">' +
              '<div class="flex items-center justify-between font-mono font-bold">' +
                '<span class="text-rose-300">✕ ' + esc(gv.id) + '</span>' +
                '<span class="text-[10px] text-slate-400">' + esc(gv.rejection_gate) + '</span>' +
              '</div>' +
              '<div class="text-[11px] text-slate-200 font-semibold mt-0.5">' + esc(gv.name) + '</div>' +
              '<div class="text-[11px] text-slate-400 mt-0.5">' + esc(gv.failure_metric) + '</div>' +
            '</div>';
          }).join('') +
        '</div>';
    }
  }

  window.filterFoundryQuick = function (st) {
    activeStatusFilter = st;
    window.RLAB.state.f1 = st;
    var f1 = document.getElementById('filter-select-1');
    if (f1) f1.value = st;
    renderStrategyCards();
  };

  window.RLAB.renderers.foundry = {
    init: function () {
      if (initialized) return;
      initialized = true;
    },
    onActivate: function () {
      renderFunnelBanner();
      renderStrategyCards();
      renderBottomTelemetry();
    },
    onFilter: function () {
      renderStrategyCards();
    }
  };
})();


async function ensureLabData() {
  if (window.LAB_DATA && window.LAB_DATA.papers) return window.LAB_DATA;
  try {
    const res = await fetch(`data/research_lab_summary.json?t=${Date.now()}`, { cache: 'no-store' });
    if (res.ok) {
      window.LAB_DATA = await res.json();
      return window.LAB_DATA;
    }
  } catch (_) {}
  return window.LAB_DATA || {};
}

async function initPage() {
  mountShell({ activePage: 'research-lab.html', onRetry: loadShellTelemetryOnly });
  await Promise.all([loadShellTelemetryOnly(), ensureLabData()]);
  if (typeof window.initResearchLabApp === 'function') {
    window.initResearchLabApp();
  }
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initPage);
} else {
  initPage();
}
