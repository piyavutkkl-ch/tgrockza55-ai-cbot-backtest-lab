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
