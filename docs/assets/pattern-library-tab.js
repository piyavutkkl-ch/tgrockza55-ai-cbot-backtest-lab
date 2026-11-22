// ANTIGRAVITY QUANT · Page 3 / 8 Tab 5: Trading Condition Library (V5 Round 2)
// Displays 20-Field Condition Library, 7-Zone Session Playbook, Empirical Confluence Proof & Branching
const LIB_URL = 'data/trading_condition_library.json';

export function registerPatternLibraryTab() {
  'use strict';

  let initialized = false;
  let loading = false;
  let loadError = null;
  let libData = null;

  const patState = {
    symbol: 'XAUUSD',
    subView: 'library', // 'library' | 'playbook' | 'confluence'
    sortKey: 'rank',    // 'rank' | 'oos_dir_prob' | 'oos_wr' | 'oos_exp' | 'oos_pf' | 'sample_n'
    sortAsc: true,
    selectedName: null,
    lastFiltered: [],
  };

  function esc(v) {
    if (window.RLAB && typeof window.RLAB.esc === 'function') return window.RLAB.esc(v);
    return String(v == null ? '' : v)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function fmtPct(v, signed) {
    const n = Number(v);
    if (!Number.isFinite(n)) return '–';
    const pct = n * 100;
    const prefix = signed && pct > 0 ? '+' : '';
    return prefix + pct.toFixed(1) + '%';
  }

  function fmtUsd(v, decimals = 4, signed = true) {
    const n = Number(v);
    if (!Number.isFinite(n)) return '–';
    const prefix = signed && n > 0 ? '+' : '';
    return prefix + n.toFixed(decimals) + ' USD';
  }

  function statusBadge(st) {
    if (st === 'VALIDATED_OOS') return '<span class="pat-badge pat-badge-green">✓ VALIDATED_OOS</span>';
    if (st === 'REGIME_SPECIFIC_EDGE') return '<span class="pat-badge pat-badge-blue">◎ REGIME_SPECIFIC</span>';
    if (st === 'RARE_HIGH_EDGE') return '<span class="pat-badge pat-badge-purple">✦ RARE_HIGH_EDGE</span>';
    if (st === 'IS_ONLY_OVERFIT') return '<span class="pat-badge pat-badge-gold">⚠ IS_ONLY_OVERFIT</span>';
    if (st === 'INSUFFICIENT_DATA') return '<span class="pat-badge pat-badge-muted">… INSUFFICIENT</span>';
    return '<span class="pat-badge pat-badge-red">✕ NO_EDGE</span>';
  }

  function dirBadge(dir) {
    if (dir === 'BUY') return '<span class="pat-badge pat-badge-green">▲ BUY</span>';
    if (dir === 'SELL') return '<span class="pat-badge pat-badge-red">▼ SELL</span>';
    return '<span class="pat-badge pat-badge-muted">' + esc(dir) + '</span>';
  }

  function jitterBadge(jit) {
    if (!jit || !jit.tested) return '<span class="text-slate-500 mono text-[10px]">–</span>';
    return jit.stable
      ? '<span class="pat-badge pat-badge-green">PASS</span>'
      : '<span class="pat-badge pat-badge-gold">FRAGILE</span>';
  }

  async function ensureLibraryLoaded() {
    if (libData) return libData;
    if (loading) return null;
    loading = true;
    loadError = null;
    renderRoot();
    try {
      const res = await fetch(LIB_URL + '?t=' + Date.now(), { cache: 'no-store' });
      if (!res.ok) throw new Error('HTTP ' + res.status);
      libData = await res.json();
    } catch (err) {
      loadError = (err && err.message) ? err.message : 'Failed to load ' + LIB_URL;
    } finally {
      loading = false;
    }
    return libData;
  }

  function getFilteredConditions(sdata) {
    const conds = Array.isArray(sdata?.conditions) ? sdata.conditions : [];
    const st = window.RLAB?.state || {};
    const q = String(st.search || '').trim().toLowerCase();
    const f1 = st.f1 || 'EDGES_ONLY';
    const f2 = st.f2 || 'ALL';
    const f3 = st.f3 || 'ALL';

    const filtered = conds.filter((c) => {
      const vStatus = c.validation?.status || '';
      if (f1 === 'EDGES_ONLY') {
        if (vStatus !== 'VALIDATED_OOS' && vStatus !== 'REGIME_SPECIFIC_EDGE' && vStatus !== 'RARE_HIGH_EDGE') return false;
      } else if (f1 !== 'ALL') {
        if (vStatus !== f1) return false;
      }

      if (f2 === 'ROUND2') {
        if (Number(c.discovery_round) !== 2) return false;
      } else if (f2 === 'ROUND1') {
        if (Number(c.discovery_round) !== 1) return false;
      } else if (f2 === 'MICROSTRUCTURE_ONLY') {
        if (!c.requires_microstructure) return false;
      } else if (f2 !== 'ALL') {
        if (c.condition_type !== f2) return false;
      }

      if (f3 === 'BUY' || f3 === 'SELL') {
        if (c.direction !== f3) return false;
      } else if (f3 === 'JITTER_PASS') {
        if (!c.validation?.jitter_stability?.stable) return false;
      } else if (f3 !== 'ALL') {
        const cats = Array.isArray(c.categories) ? c.categories : [];
        if (cats.indexOf(f3) < 0) return false;
      }

      if (q) {
        const hay = [
          c.condition_name,
          c.formatted_sequence,
          c.entry_criteria,
          c.pre_condition,
          c.session_scope,
          c.condition_type,
          c.regime_priority_tag,
          (c.categories || []).join(' '),
        ].join(' ').toLowerCase();
        if (hay.indexOf(q) < 0) return false;
      }
      return true;
    });

    const k = patState.sortKey;
    const mult = patState.sortAsc ? 1 : -1;
    filtered.sort((a, b) => {
      let va = 0;
      let vb = 0;
      if (k === 'rank') {
        va = a.rank || 0;
        vb = b.rank || 0;
      } else if (k === 'oos_dir_prob') {
        va = a.probability?.oos_dir_prob ?? -999;
        vb = b.probability?.oos_dir_prob ?? -999;
      } else if (k === 'oos_wr') {
        va = a.win_rate?.oos ?? -999;
        vb = b.win_rate?.oos ?? -999;
      } else if (k === 'oos_exp') {
        va = a.expectancy?.oos_usd ?? -999;
        vb = b.expectancy?.oos_usd ?? -999;
      } else if (k === 'oos_pf') {
        va = a.profit_factor?.oos ?? -999;
        vb = b.profit_factor?.oos ?? -999;
      } else if (k === 'sample_n') {
        va = a.sample_size?.total ?? 0;
        vb = b.sample_size?.total ?? 0;
      }
      if (va === vb) return (a.rank || 0) - (b.rank || 0);
      return va < vb ? -1 * mult : 1 * mult;
    });

    return filtered;
  }

  function renderTopBarAndKpis(sdata) {
    const syms = libData?.symbols || {};
    const da = sdata?.data_audit || {};
    const sc = sdata?.summary_counts || {};
    const vb = sc.validation_breakdown || {};
    const r2Sum = sdata?.round2_highlights?.round1_vs_round2_summary || {};
    const totalEdges = (vb.VALIDATED_OOS || 0) + (vb.REGIME_SPECIFIC_EDGE || 0) + (vb.RARE_HIGH_EDGE || 0);
    const overfitOrNo = (vb.IS_ONLY_OVERFIT || 0) + (vb.NO_EDGE || 0);

    const symPills = ['XAUUSD', 'BTCUSD', 'ETHUSD'].map((sym) => {
      const sd = syms[sym];
      const vo = sd?.summary_counts?.validation_breakdown?.VALIDATED_OOS || 0;
      const active = patState.symbol === sym ? ' active' : '';
      const icon = sym === 'XAUUSD' ? '🥇' : (sym === 'BTCUSD' ? '₿' : '⟠');
      return '<button type="button" onclick="window.patSelectSymbol(\'' + sym + '\')" class="pat-pill-btn' + active + '">' +
        '<span>' + icon + ' ' + sym + '</span>' +
        '<span class="pat-cnt-badge">' + vo + ' OOS</span>' +
      '</button>';
    }).join('');

    const subButtons = [
      { id: 'library', icon: '📋', label: '20-Field Library (' + (sc.conditions_archived_in_json || (sdata?.conditions || []).length) + ')' },
      { id: 'playbook', icon: '🕒', label: '7-Zone Session Playbook' },
      { id: 'confluence', icon: '🔀', label: 'Confluence Proof & Branching' },
    ].map((sb) => {
      const active = patState.subView === sb.id ? ' active' : '';
      return '<button type="button" onclick="window.patSwitchSubView(\'' + sb.id + '\')" class="pat-subview-btn' + active + '">' +
        '<span>' + sb.icon + '</span><span>' + esc(sb.label) + '</span>' +
      '</button>';
    }).join('');

    const tfSourcesStr = Object.entries(da.tf_sources || {}).map(([k, v]) => k.toUpperCase() + ':' + (v === 'CTRADER_MCP' ? 'cTrader' : v)).join(' · ');

    return `
      <div class="pat-top-bar">
        <div class="pat-pill-group">
          <span class="text-xs font-extrabold text-slate-300 mr-1">Asset:</span>
          ${symPills}
          <span class="pat-badge pat-badge-purple ml-1">R2 Iteration · ${esc(libData?.schema_version || 'V5')}</span>
        </div>
        <div class="pat-pill-group">${subButtons}</div>
      </div>

      <div class="pat-kpi-grid">
        <div class="pat-kpi-card">
          <span class="pat-kpi-label">Conditions Tested (R1 + R2)</span>
          <span class="pat-kpi-val">${Number(sc.total_conditions_tested || 0).toLocaleString('en-US')}</span>
          <span class="pat-kpi-sub mono">R1 ${r2Sum.round1_tested || 0} (Edges ${r2Sum.round1_validated_or_regime || 0}) · R2 ${r2Sum.round2_tested || 0} (Edges ${r2Sum.round2_validated_or_regime || 0})</span>
        </div>
        <div class="pat-kpi-card">
          <span class="pat-kpi-label">VALIDATED_OOS</span>
          <span class="pat-kpi-val text-emerald-300">${vb.VALIDATED_OOS || 0}</span>
          <span class="pat-kpi-sub">IS + OOS 40% Unseen + Walk-Forward ผ่าน</span>
        </div>
        <div class="pat-kpi-card">
          <span class="pat-kpi-label">REGIME_SPECIFIC_EDGE</span>
          <span class="pat-kpi-val text-cyan-300">${vb.REGIME_SPECIFIC_EDGE || 0}</span>
          <span class="pat-kpi-sub">ชนะจำเพาะ Regime / Session (ไม่แบนถาวร)</span>
        </div>
        <div class="pat-kpi-card">
          <span class="pat-kpi-label">RARE_HIGH_EDGE</span>
          <span class="pat-kpi-val text-purple-300">${vb.RARE_HIGH_EDGE || 0}</span>
          <span class="pat-kpi-sub">N=8..19 แต่ Edge ชัด · Total Edges: ${totalEdges}</span>
        </div>
        <div class="pat-kpi-card">
          <span class="pat-kpi-label">Filtered Out / Overfit</span>
          <span class="pat-kpi-val text-amber-300">${overfitOrNo}</span>
          <span class="pat-kpi-sub mono">Overfit: ${vb.IS_ONLY_OVERFIT || 0} · NoEdge: ${vb.NO_EDGE || 0} · Insuf: ${vb.INSUFFICIENT_DATA || 0}</span>
        </div>
        <div class="pat-kpi-card">
          <span class="pat-kpi-label">Live Data Provenance</span>
          <span class="pat-kpi-val" style="font-size:14px;">${Number(da.live_microstructure_bars || 0).toLocaleString('en-US')} DOM M1</span>
          <span class="pat-kpi-sub mono">Flow ${Number(da.live_order_flow_bars || 0).toLocaleString('en-US')} · ${esc(tfSourcesStr)}</span>
        </div>
      </div>
    `;
  }

  function renderInspector(c) {
    if (!c) {
      return '<div class="text-xs text-slate-400 p-4 text-center">คลิกเลือกรายการ Condition จากตารางด้านซ้ายเพื่อตรวจรายละเอียดครบทั้ง 20 Fields</div>';
    }
    const prob = c.probability || {};
    const horizons = prob.horizons_oos || {};
    const wr = c.win_rate || {};
    const ex = c.expectancy || {};
    const pf = c.profit_factor || {};
    const mm = c.mfe_mae || {};
    const ss = c.sample_size || {};
    const fq = c.frequency || {};
    const st = c.sl_tp || {};
    const val = c.validation || {};
    const jit = val.jitter_stability || {};
    const ab = c.ablation_lift;
    const slift = c.session_lift_vs_allday;
    const wf = c.walk_forward || {};

    const horizonRows = [5, 15, 30, 60].map((h) => {
      const hv = horizons['h_' + h];
      if (!hv) return '';
      const pb = Math.round((hv.p_bull || 0) * 1000) / 10;
      const pn = Math.round((hv.p_neutral || 0) * 1000) / 10;
      const pr = Math.max(0, Math.round((100 - pb - pn) * 10) / 10);
      const isPrim = Number(c.time_horizon?.primary_bars) === h;
      return `
        <div class="space-y-1">
          <div class="flex items-center justify-between text-[11px] mono">
            <span class="${isPrim ? 'text-cyan-300 font-bold' : 'text-slate-300'}">+${h}m (${h}b)${isPrim ? ' ★' : ''}</span>
            <span class="text-slate-300">
              <span class="text-emerald-300">Bull ${pb.toFixed(1)}%</span> ·
              <span class="text-slate-400">Side ${pn.toFixed(1)}%</span> ·
              <span class="text-rose-300">Bear ${pr.toFixed(1)}%</span> ·
              <span class="text-slate-400">Avg ${Number(hv.avg_move_atr || 0) >= 0 ? '+' : ''}${Number(hv.avg_move_atr || 0).toFixed(3)} ATR</span>
            </span>
          </div>
          <div class="pat-prob-bar">
            <div class="pat-prob-bull" style="width:${pb}%"></div>
            <div class="pat-prob-neut" style="width:${pn}%"></div>
            <div class="pat-prob-bear" style="width:${pr}%"></div>
          </div>
        </div>
      `;
    }).join('');

    const wfHtml = (Array.isArray(wf.folds) && wf.folds.length > 0)
      ? `<div class="pat-subbox space-y-1.5">
          <div class="text-[11px] font-extrabold text-slate-200">Walk-Forward Validation (${val.walk_forward_positive_folds}/${val.walk_forward_total_folds} folds positive · Avg ${fmtUsd(val.walk_forward_avg_exp_usd)})</div>
          <div class="grid grid-cols-3 gap-1.5 text-[11px] mono">
            ${wf.folds.map((f) => `
              <div class="p-1.5 rounded border border-slate-700/60">
                <div class="text-slate-400">Fold #${f.fold} (${f.trades}t)</div>
                <div class="${f.expectancy_usd > 0 ? 'text-emerald-300' : 'text-rose-300'} font-bold">${fmtUsd(f.expectancy_usd, 3)}</div>
                <div class="text-[10px] text-slate-400">WR ${fmtPct(f.win_rate)} · ${f.sl_atr}/${f.tp_atr}</div>
              </div>
            `).join('')}
          </div>
        </div>`
      : '';

    const abHtml = ab
      ? `<div class="pat-subbox space-y-1">
          <div class="text-[11px] font-extrabold text-purple-300">Ablation Incremental Lift (เทียบขั้นตอนก่อนหน้า)</div>
          <div class="text-[11px] mono text-slate-200">
            Base: <b>${esc(ab.base_event)}</b> · Prev: <b>${esc(ab.prev_step)}</b><br/>
            ΔP vs Prev: <b class="${(ab.delta_oos_prob_vs_prev || 0) >= 0 ? 'text-emerald-300' : 'text-rose-300'}">${fmtPct(ab.delta_oos_prob_vs_prev, true)}</b> ·
            ΔExp vs Prev: <b class="${(ab.delta_oos_exp_vs_prev || 0) >= 0 ? 'text-emerald-300' : 'text-rose-300'}">${fmtUsd(ab.delta_oos_exp_vs_prev)}</b>
          </div>
        </div>`
      : '';

    const sliftHtml = slift
      ? `<div class="pat-subbox space-y-1">
          <div class="text-[11px] font-extrabold text-cyan-300">Session Lift vs All-Day Baseline (${esc(c.session_scope)})</div>
          <div class="text-[11px] mono text-slate-200">
            Session OOS Exp: <b>${fmtUsd(slift.session_oos_exp_usd)}</b> vs All-Day <b>${fmtUsd(slift.allday_oos_exp_usd)}</b>
            ➔ Lift <b class="${slift.delta_oos_exp_vs_allday >= 0 ? 'text-emerald-300' : 'text-rose-300'}">${fmtUsd(slift.delta_oos_exp_vs_allday)}</b>
            (PF ${Number(slift.session_oos_pf || 0).toFixed(2)} vs ${Number(slift.allday_oos_pf || 0).toFixed(2)})
          </div>
        </div>`
      : '';

    const jitHtml = jit.tested
      ? `<div class="pat-subbox space-y-1">
          <div class="text-[11px] font-extrabold text-slate-200">±15% Parameter Perturbation Stability ${jitterBadge(jit)}</div>
          <div class="text-[11px] mono text-slate-300">
            0.85x Threshold: <b>${fmtUsd(jit.oos_exp_085)}</b> ·
            1.00x Nominal: <b>${fmtUsd(jit.oos_exp_100)}</b> ·
            1.15x Threshold: <b>${fmtUsd(jit.oos_exp_115)}</b>
          </div>
        </div>`
      : '';

    const regEntries = Object.entries(c.regime_breakdown_oos || {});
    const regHtml = regEntries.length > 0
      ? `<div class="pat-subbox space-y-1.5">
          <div class="text-[11px] font-extrabold text-slate-200">OOS Performance by Market Regime</div>
          <div class="space-y-1 text-[11px] mono">
            ${regEntries.map(([rk, rv]) => `
              <div class="flex items-center justify-between">
                <span class="text-slate-300">${esc(rk)} (${rv.trades}t, WR ${fmtPct(rv.win_rate)})</span>
                <span class="${rv.expectancy_usd >= 0 ? 'text-emerald-300' : 'text-rose-300'} font-bold">${fmtUsd(rv.expectancy_usd, 3)} · PF ${Number(rv.profit_factor || 0).toFixed(2)}</span>
              </div>
            `).join('')}
          </div>
        </div>`
      : '';

    const catsHtml = (c.categories || []).map((cat) => '<span class="pat-badge pat-badge-blue">' + esc(cat) + '</span>').join(' ');

    return `
      <div class="space-y-2 border-b pb-3">
        <div class="flex flex-wrap items-center justify-between gap-2">
          <span class="mono text-xs font-extrabold text-cyan-300">RANK #${c.rank} · R${c.discovery_round || 1} · ${esc(c.session_scope || 'ALL')}</span>
          <div class="flex flex-wrap gap-1">${dirBadge(c.direction)} ${statusBadge(val.status)}</div>
        </div>
        <div class="text-sm font-extrabold text-white mono break-all">${esc(c.condition_name)}</div>
        <div class="flex flex-wrap gap-1">${catsHtml}</div>
      </div>

      <div class="pat-subbox space-y-1.5 text-xs">
        <div><span class="text-slate-400 font-bold">Sequence Format:</span> <span class="mono text-cyan-300">${esc(c.formatted_sequence)}</span></div>
        <div><span class="text-slate-400 font-bold">Type &amp; TFs:</span> <span class="mono text-slate-200">${esc(c.condition_type)} · [${esc((c.timeframes || []).join(' + '))}]</span></div>
        <div><span class="text-slate-400 font-bold">Pre-condition:</span> <span class="text-slate-200">${esc(c.pre_condition)}</span></div>
        <div><span class="text-slate-400 font-bold">Entry Criteria:</span> <span class="text-slate-200">${esc(c.entry_criteria)}</span></div>
        <div><span class="text-slate-400 font-bold">Expected Behavior:</span> <span class="text-emerald-300">${esc(c.expected_behavior)}</span></div>
      </div>

      <div class="pat-subbox space-y-2">
        <div class="flex items-center justify-between text-[11px]">
          <span class="font-extrabold text-slate-200">3-State Directional Probability (OOS 40%)</span>
          <span class="mono text-slate-400">Horizon: ${esc(c.time_horizon?.label || '')}</span>
        </div>
        ${horizonRows}
      </div>

      <div class="pat-field-grid text-xs">
        <div class="pat-subbox">
          <div class="text-[10px] text-slate-400 font-bold uppercase">Trade Win Rate</div>
          <div class="mono font-extrabold text-sm text-white">OOS ${fmtPct(wr.oos)} <span class="text-[11px] text-slate-400">(IS ${fmtPct(wr.is)})</span></div>
          <div class="mono text-[10px] text-cyan-300">Wilson 95% LB: ${fmtPct(wr.oos_wilson_lb95)}</div>
        </div>
        <div class="pat-subbox">
          <div class="text-[10px] text-slate-400 font-bold uppercase">Expectancy &amp; PF (Costed)</div>
          <div class="mono font-extrabold text-sm ${ex.oos_usd >= 0 ? 'text-emerald-300' : 'text-rose-300'}">${fmtUsd(ex.oos_usd)}</div>
          <div class="mono text-[10px] text-slate-300">PF OOS <b>${Number(pf.oos || 0).toFixed(2)}</b> (IS ${Number(pf.is || 0).toFixed(2)}) · MaxDD ${Number(ex.max_dd_oos_usd || 0).toFixed(2)} USD</div>
        </div>
        <div class="pat-subbox">
          <div class="text-[10px] text-slate-400 font-bold uppercase">MFE / MAE &amp; First-Passage</div>
          <div class="mono font-bold text-slate-100">${Number(mm.avg_mfe_atr || 0).toFixed(2)} / ${Number(mm.avg_mae_atr || 0).toFixed(2)} ATR</div>
          <div class="mono text-[10px] text-slate-400">MFE First: ${fmtPct(mm.pct_mfe_before_mae)} · Hold ~${ex.avg_holding_bars_oos || 0}b</div>
        </div>
        <div class="pat-subbox">
          <div class="text-[10px] text-slate-400 font-bold uppercase">Sample &amp; Frequency</div>
          <div class="mono font-bold text-slate-100">N=${ss.total} <span class="text-slate-400">(IS ${ss.in_sample} / OOS ${ss.out_of_sample})</span></div>
          <div class="mono text-[10px] text-slate-400">${fq.per_day}/day · ${fq.per_1000_bars}/1k bars (raw ${fq.raw_triggers})</div>
        </div>
        <div class="pat-subbox">
          <div class="text-[10px] text-slate-400 font-bold uppercase">Adaptive SL / TP</div>
          <div class="mono font-bold text-slate-100">${st.sl_atr} / ${st.tp_atr} ATR (RR ${st.rr_ratio})</div>
          <div class="mono text-[10px] text-slate-400">${esc(st.mode)}</div>
        </div>
        <div class="pat-subbox">
          <div class="text-[10px] text-slate-400 font-bold uppercase">Reliability &amp; Provenance</div>
          <div class="mono font-bold text-cyan-300">${esc(c.reliability)} · FDR q=${Number(val.fdr_q_value ?? 1).toFixed(4)}</div>
          <div class="mono text-[10px] text-slate-400">${esc(c.data_tier_provenance)} · ${esc(c.regime_priority_tag)}</div>
        </div>
      </div>

      ${abHtml}
      ${sliftHtml}
      ${jitHtml}
      ${wfHtml}
      ${regHtml}
    `;
  }

  function sortHeader(key, label) {
    const active = patState.sortKey === key;
    const ind = active ? (patState.sortAsc ? ' ▲' : ' ▼') : '';
    return '<button type="button" onclick="window.patSortBy(\'' + key + '\')" class="' + (active ? 'text-cyan-300' : '') + '">' + esc(label) + ind + '</button>';
  }

  function renderLibrarySubView(sdata) {
    const filtered = getFilteredConditions(sdata);
    patState.lastFiltered = filtered;

    let selected = null;
    if (patState.selectedName) {
      selected = filtered.find((c) => c.condition_name === patState.selectedName) || null;
    }
    if (!selected && filtered.length > 0) {
      selected = filtered[0];
      patState.selectedName = selected.condition_name;
    }

    const visible = filtered.slice(0, 150);
    const rowsHtml = visible.map((c, idx) => {
      const isSel = selected && c.condition_name === selected.condition_name;
      const pb = c.probability || {};
      const wr = c.win_rate || {};
      const ex = c.expectancy || {};
      const pf = c.profit_factor || {};
      const mm = c.mfe_mae || {};
      const ss = c.sample_size || {};
      const val = c.validation || {};
      const jit = val.jitter_stability || {};
      const microTag = c.requires_microstructure ? '<span class="pat-badge pat-badge-purple">DOM/Flow</span> ' : '';
      const roundTag = '<span class="pat-badge pat-badge-muted">R' + (c.discovery_round || 1) + '</span> ';

      return `
        <tr class="${isSel ? 'is-selected' : ''}" onclick="window.patSelectRowIdx(${idx})">
          <td class="mono font-bold text-slate-400">#${c.rank}</td>
          <td style="min-width:220px;max-width:320px;">
            <div class="mono font-bold text-xs text-white break-all">${esc(c.condition_name)}</div>
            <div class="flex flex-wrap gap-1 mt-1">${roundTag}${microTag}${c.session_scope && c.session_scope !== 'ALL' ? '<span class="pat-badge pat-badge-blue">' + esc(c.session_scope) + '</span>' : ''}</div>
          </td>
          <td class="mono text-[11px] text-slate-300">${esc(c.condition_type)}<br/><span class="text-slate-500">${esc((c.timeframes || []).join('+'))}</span></td>
          <td>${dirBadge(c.direction)}</td>
          <td class="mono">
            <div class="font-bold">${fmtPct(pb.oos_dir_prob)}</div>
            <div class="text-[10px] ${(pb.oos_dir_lift || 0) >= 0 ? 'text-emerald-300' : 'text-rose-300'}">${fmtPct(pb.oos_dir_lift, true)}</div>
          </td>
          <td class="mono">
            <div class="font-bold">${fmtPct(wr.oos)}</div>
            <div class="text-[10px] text-slate-400">LB ${fmtPct(wr.oos_wilson_lb95)}</div>
          </td>
          <td class="mono font-bold ${ex.oos_usd >= 0 ? 'text-emerald-300' : 'text-rose-300'}">${ex.oos_usd >= 0 ? '+' : ''}${Number(ex.oos_usd || 0).toFixed(4)}</td>
          <td class="mono font-bold">${Number(pf.oos || 0).toFixed(2)}</td>
          <td class="mono text-[11px] text-slate-300">${Number(mm.avg_mfe_atr || 0).toFixed(2)}/${Number(mm.avg_mae_atr || 0).toFixed(2)}</td>
          <td class="mono text-[11px]">${ss.total} <span class="text-slate-400">(${ss.in_sample}/${ss.out_of_sample})</span></td>
          <td class="mono text-[11px]">${val.walk_forward_positive_folds}/${val.walk_forward_total_folds}</td>
          <td>${jitterBadge(jit)}</td>
          <td>${statusBadge(val.status)}</td>
        </tr>
      `;
    }).join('');

    return `
      <div class="pat-split">
        <div class="pat-table-panel">
          <div class="px-4 py-2.5 border-b flex flex-wrap items-center justify-between gap-2 text-xs">
            <span class="font-extrabold text-white">📚 20-Field Trading Condition Library — ${esc(patState.symbol)}</span>
            <span class="mono text-slate-400">Showing ${visible.length} of ${filtered.length} matching (Archived ${(sdata.conditions || []).length} / Tested ${sdata.summary_counts?.total_conditions_tested || 0})</span>
          </div>
          <div class="pat-table-wrap">
            <table class="pat-table">
              <thead>
                <tr>
                  <th>${sortHeader('rank', 'Rank')}</th>
                  <th>Condition Name &amp; Scope</th>
                  <th>Type / TFs</th>
                  <th>Dir</th>
                  <th>${sortHeader('oos_dir_prob', 'OOS P(Dir)')}</th>
                  <th>${sortHeader('oos_wr', 'OOS WR')}</th>
                  <th>${sortHeader('oos_exp', 'OOS Exp')}</th>
                  <th>${sortHeader('oos_pf', 'PF')}</th>
                  <th>MFE/MAE</th>
                  <th>${sortHeader('sample_n', 'N (IS/OOS)')}</th>
                  <th>WF</th>
                  <th>Jitter</th>
                  <th>Validation Status</th>
                </tr>
              </thead>
              <tbody>
                ${rowsHtml || '<tr><td colspan="13" class="text-center p-6 text-slate-400">ไม่พบ Condition ที่ตรงกับตัวกรองปัจจุบัน ลองเปลี่ยน Filter ด้านบนเป็น ALL หรือกด Reset</td></tr>'}
              </tbody>
            </table>
          </div>
        </div>
        <aside class="pat-inspector" id="pat-inspector-panel">${renderInspector(selected)}</aside>
      </div>
    `;
  }

  function renderPlaybookSubView(sdata) {
    const pb = sdata?.round2_highlights?.session_playbook || {};
    const zones = Object.keys(pb);

    const cardsHtml = zones.map((zn) => {
      const zp = pb[zn];
      const lift = Number(zp.delta_oos_exp_vs_allday || 0);
      return `
        <div class="pat-session-card">
          <div class="flex items-center justify-between gap-2">
            <span class="pat-badge pat-badge-blue">🕒 ${esc(zn)}</span>
            ${statusBadge(zp.validation_status)}
          </div>
          <div class="mono text-xs font-extrabold text-white break-all">${esc(zp.best_condition)}</div>
          <div class="flex items-center gap-2 text-xs">
            ${dirBadge(zp.direction)}
            <span class="pat-badge pat-badge-muted">${esc(zp.condition_type)}</span>
            <span class="mono text-slate-300">N=${zp.sample_size} (${esc(zp.sample_is_oos)})</span>
          </div>
          <div class="pat-field-grid text-xs">
            <div class="pat-subbox">
              <div class="text-[10px] text-slate-400 font-bold">Session OOS Exp</div>
              <div class="mono font-extrabold ${zp.oos_expectancy_usd >= 0 ? 'text-emerald-300' : 'text-rose-300'}">${fmtUsd(zp.oos_expectancy_usd)}</div>
              <div class="mono text-[10px] text-slate-400">WR ${fmtPct(zp.oos_win_rate)} · PF ${Number(zp.oos_profit_factor || 0).toFixed(2)}</div>
            </div>
            <div class="pat-subbox">
              <div class="text-[10px] text-slate-400 font-bold">Session Lift vs All-Day</div>
              <div class="mono font-extrabold ${lift >= 0 ? 'text-cyan-300' : 'text-amber-300'}">${fmtUsd(lift)}</div>
              <div class="mono text-[10px] text-slate-400">All-Day: ${fmtUsd(zp.allday_oos_exp_usd)}</div>
            </div>
          </div>
          <div class="flex items-center justify-between text-[11px] mono text-slate-400 border-t pt-2">
            <span>SL/TP: <b>${zp.sl_atr}/${zp.tp_atr} ATR</b></span>
            <button type="button" onclick="window.patJumpToPlaybookZone('${esc(zn)}')" class="text-cyan-300 font-bold hover:underline">Inspect 20 Fields →</button>
          </div>
        </div>
      `;
    }).join('');

    const sesValidated = (sdata?.conditions || [])
      .filter((c) => (c.condition_type === 'Session-Micro' || c.condition_type === 'Session-Specific') && c.validation?.status === 'VALIDATED_OOS')
      .slice(0, 20);

    const sesTableRows = sesValidated.map((c) => {
      const sl = c.session_lift_vs_allday || {};
      return `
        <tr>
          <td><span class="pat-badge pat-badge-blue">${esc(c.session_scope)}</span></td>
          <td class="mono text-xs font-bold text-white">${esc(c.condition_name)}</td>
          <td>${dirBadge(c.direction)}</td>
          <td class="mono">${c.sample_size?.total} (${c.sample_size?.in_sample}/${c.sample_size?.out_of_sample})</td>
          <td class="mono">${fmtPct(c.win_rate?.oos)}</td>
          <td class="mono text-emerald-300 font-bold">${fmtUsd(c.expectancy?.oos_usd)}</td>
          <td class="mono text-cyan-300 font-bold">${fmtUsd(sl.delta_oos_exp_vs_allday)}</td>
          <td class="mono font-bold">${Number(c.profit_factor?.oos || 0).toFixed(2)}</td>
          <td class="mono">${c.validation?.walk_forward_positive_folds}/${c.validation?.walk_forward_total_folds}</td>
        </tr>
      `;
    }).join('');

    return `
      <div class="space-y-4">
        <div class="pat-subbox text-xs text-slate-300">
          <b>7-Zone Session-Specific Scalping Playbooks (${esc(patState.symbol)}):</b>
          ทดสอบ IS/OOS 60/40 และ 3-Fold Walk-Forward แยกขาดเฉพาะแต่ละ Session Zone เพื่อพิสูจน์ว่ากลยุทธ์ที่แพ้หรือขาดทุนเมื่อรันทั้งวัน สามารถกลับมามีกำไรและ PF สูงขึ้นเมื่อจำกัดโซนเวลา (<b>Session Lift</b>)
        </div>
        <div class="pat-playbook-grid">
          ${cardsHtml || '<div class="pat-subbox text-xs text-slate-400">ยังไม่มี Session Playbook สำหรับสินทรัพย์นี้</div>'}
        </div>
        <div class="pat-table-panel">
          <div class="px-4 py-2.5 border-b text-xs font-extrabold text-white">✅ Top Session-Validated Edges (${esc(patState.symbol)} · VALIDATED_OOS Only)</div>
          <div class="pat-table-wrap" style="max-height:360px;">
            <table class="pat-table">
              <thead>
                <tr><th>Zone</th><th>Condition</th><th>Dir</th><th>N (IS/OOS)</th><th>OOS WR</th><th>Session Exp</th><th>Session Lift</th><th>OOS PF</th><th>WF</th></tr>
              </thead>
              <tbody>
                ${sesTableRows || '<tr><td colspan="9" class="text-center p-4 text-slate-400">ไม่มี Session-Specific condition ที่ผ่านเกณฑ์ VALIDATED_OOS เต็มรูปแบบ (ดูรายการย่อยที่ Sub-View A)</td></tr>'}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    `;
  }

  function renderConfluenceSubView(sdata) {
    const syms = ['XAUUSD', 'BTCUSD', 'ETHUSD'];
    const confCards = syms.map((sym) => {
      const cp = libData?.symbols?.[sym]?.confluence_proof;
      if (!cp) return '';
      const tiers = cp.tiers || {};
      const verdictOk = cp.verdict === 'CONFLUENCE_IMPROVES_PROB_AND_EXP';
      const rows = ['1_TF', '2_TF', '3_PLUS_TF'].map((tk) => {
        const t = tiers[tk] || {};
        return `
          <tr>
            <td class="mono font-bold">${tk}</td>
            <td class="mono">${t.patterns_tested || 0}</td>
            <td class="mono">${t.avg_oos_sample || 0}</td>
            <td class="mono">${fmtPct(t.avg_oos_dir_prob)}</td>
            <td class="mono">${fmtPct(t.avg_oos_win_rate)}</td>
            <td class="mono ${(t.avg_oos_expectancy_usd || 0) >= 0 ? 'text-emerald-300' : 'text-rose-300'}">${fmtUsd(t.avg_oos_expectancy_usd)}</td>
            <td class="mono font-bold">${Number(t.avg_oos_pf || 0).toFixed(2)}</td>
          </tr>
        `;
      }).join('');

      return `
        <div class="pat-session-card">
          <div class="flex items-center justify-between gap-2">
            <span class="font-extrabold text-white">${sym} Confluence Test</span>
            <span class="pat-badge ${verdictOk ? 'pat-badge-green' : 'pat-badge-gold'}">${esc(cp.verdict)}</span>
          </div>
          <div class="overflow-x-auto">
            <table class="pat-table">
              <thead><tr><th>Tier</th><th>Set</th><th>Avg N</th><th>OOS P(Dir)</th><th>OOS WR</th><th>OOS Exp</th><th>Avg PF</th></tr></thead>
              <tbody>${rows}</tbody>
            </table>
          </div>
        </div>
      `;
    }).join('');

    const r1Branches = sdata?.branching_patterns || [];
    const obBranches = sdata?.round2_highlights?.orderbook_branching_patterns || [];
    const allBranches = r1Branches.slice(0, 4).concat(obBranches.slice(0, 4));
    const branchHtml = allBranches.map((bp) => `
      <div class="pat-branch-card">
        <div class="text-xs font-extrabold text-cyan-300 mono">Prefix: ${esc(bp.shared_prefix)}</div>
        <div class="space-y-1">
          ${(bp.branches || []).map((b) => `
            <div class="flex items-center justify-between text-[11px] mono border-t pt-1">
              <span>➔ <b>${esc(b.next_step)}</b> (${dirBadge(b.direction)}, N=${b.sample_size})</span>
              <span class="${b.oos_expectancy_usd >= 0 ? 'text-emerald-300' : 'text-rose-300'} font-bold">P ${fmtPct(b.oos_dir_prob)} · ${fmtUsd(b.oos_expectancy_usd, 3)}</span>
            </div>
          `).join('')}
        </div>
      </div>
    `).join('');

    const conv = sdata?.converging_patterns || {};
    const convHtml = ['BUY', 'SELL'].map((d) => {
      const items = conv[d] || [];
      return `
        <div class="pat-branch-card">
          <div class="flex items-center justify-between">
            <span class="text-xs font-extrabold text-white">Converging Patterns ➔ ${dirBadge(d)}</span>
            <span class="mono text-[10px] text-slate-400">จุดเริ่มต่างกันแต่ให้ผลลัพธ์ทิศทางเดียวกัน</span>
          </div>
          <div class="space-y-1 text-[11px] mono">
            ${items.map((it) => `
              <div class="flex items-center justify-between border-t pt-1">
                <span class="text-slate-200">${esc(it.condition_name)} <span class="text-slate-400">(Start: ${esc(it.starting_event)})</span></span>
                <span class="text-emerald-300 font-bold">N=${it.sample_size} · ${fmtUsd(it.oos_expectancy_usd, 3)}</span>
              </div>
            `).join('') || '<div class="text-slate-400">ไม่มีข้อมูล</div>'}
          </div>
        </div>
      `;
    }).join('');

    return `
      <div class="space-y-4">
        <div class="pat-subbox text-xs text-slate-300">
          <b>Empirical Timeframe Confluence Proof (`1 TF` vs `2 TF` vs `3+ TF`):</b>
          พิสูจน์จากข้อมูลจริงแทนการสมมติล่วงหน้า — พบว่า <b>BTCUSD &amp; ETHUSD</b> การเพิ่ม TF ยืนยันช่วยเพิ่มทั้ง OOS Probability และ Expectancy (<code>CONFLUENCE_IMPROVES_PROB_AND_EXP</code>) ส่วน <b>XAUUSD</b> ไม่ได้เพิ่มขึ้นเป็นเส้นตรง (<code>1_TF → 2_TF</code> ตกลงก่อนกลับมาดีขึ้นที่ <code>3_PLUS_TF</code>) จึงต้องคัดเฉพาะคู่ MTF ที่ผ่าน OOS จริงเท่านั้น
        </div>
        <div class="pat-confluence-grid">${confCards}</div>
        <h3 class="text-sm font-extrabold text-white mt-2">🌳 Branching Patterns — จุดเริ่มต้นเดียวกัน แต่แตกแขนงผลลัพธ์ตามเหตุการณ์ถัดไป (${esc(patState.symbol)})</h3>
        <div class="pat-confluence-grid">${branchHtml || '<div class="pat-subbox text-xs text-slate-400">ไม่พบ Branching Divergence</div>'}</div>
        <h3 class="text-sm font-extrabold text-white mt-2">🎯 Converging Patterns — จุดเริ่มต้นต่างกัน แต่รวมสู่ทิศทางเดียวกัน (${esc(patState.symbol)})</h3>
        <div class="pat-confluence-grid">${convHtml}</div>
      </div>
    `;
  }

  function renderRoot() {
    const root = document.getElementById('patterns-root');
    if (!root) return;

    if (loading && !libData) {
      root.innerHTML = '<div class="lab-panel p-8 text-center text-xs text-cyan-300 mono">⏳ กำลังโหลดคลัง Trading Condition Library V5 R2 (XAUUSD · BTCUSD · ETHUSD)...</div>';
      return;
    }
    if (loadError && !libData) {
      root.innerHTML = '<div class="lab-panel p-8 text-center text-xs text-rose-300 mono">❌ โหลดข้อมูลไม่สำเร็จ: ' + esc(loadError) + '</div>';
      return;
    }
    if (!libData || !libData.symbols) {
      root.innerHTML = '<div class="lab-panel p-8 text-center text-xs text-slate-400">กำลังเตรียมข้อมูล...</div>';
      return;
    }

    const sdata = libData.symbols[patState.symbol] || libData.symbols.XAUUSD;
    let bodyHtml = '';
    if (patState.subView === 'playbook') {
      bodyHtml = renderPlaybookSubView(sdata);
    } else if (patState.subView === 'confluence') {
      bodyHtml = renderConfluenceSubView(sdata);
    } else {
      bodyHtml = renderLibrarySubView(sdata);
    }

    root.innerHTML = renderTopBarAndKpis(sdata) + bodyHtml;
  }

  // Global event handlers
  window.patSelectSymbol = function (sym) {
    if (!libData?.symbols?.[sym]) return;
    patState.symbol = sym;
    patState.selectedName = null;
    renderRoot();
  };

  window.patSwitchSubView = function (sv) {
    patState.subView = sv;
    renderRoot();
  };

  window.patSortBy = function (key) {
    if (patState.sortKey === key) {
      patState.sortAsc = !patState.sortAsc;
    } else {
      patState.sortKey = key;
      patState.sortAsc = key === 'rank';
    }
    renderRoot();
  };

  window.patSelectRowIdx = function (idx) {
    const c = patState.lastFiltered[idx];
    if (!c) return;
    patState.selectedName = c.condition_name;
    renderRoot();
  };

  window.patJumpToPlaybookZone = function (zone) {
    const sdata = libData?.symbols?.[patState.symbol];
    const pb = sdata?.round2_highlights?.session_playbook?.[zone];
    if (!pb) return;
    patState.subView = 'library';
    patState.selectedName = pb.best_condition;
    if (window.RLAB?.state) {
      window.RLAB.state.f1 = 'ALL';
      const f1El = document.getElementById('filter-select-1');
      if (f1El) f1El.value = 'ALL';
    }
    renderRoot();
  };

  window.RLAB = window.RLAB || { state: {}, renderers: {} };
  window.RLAB.renderers.patterns = {
    init: function () {
      if (initialized) return;
      initialized = true;
    },
    onActivate: async function () {
      await ensureLibraryLoaded();
      renderRoot();
    },
    onFilter: function () {
      if (!libData) return;
      renderRoot();
    },
  };
}
