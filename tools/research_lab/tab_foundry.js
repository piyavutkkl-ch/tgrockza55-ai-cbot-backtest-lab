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
