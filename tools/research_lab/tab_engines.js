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
