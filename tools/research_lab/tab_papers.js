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
