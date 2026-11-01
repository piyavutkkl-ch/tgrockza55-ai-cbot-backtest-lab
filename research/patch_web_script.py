import json
import re

html_path = r'd:\cbot-atgvt\docs\index.html'
json_path = r'd:\cbot-atgvt\docs\data\backtest_data.json'

with open(html_path, 'r', encoding='utf-8') as f:
    html = f.read()

with open(json_path, 'r', encoding='utf-8') as f:
    db = json.load(f)

# 1. Update inlined DATA
data_json_str = json.dumps(db, ensure_ascii=False)
data_pattern = r'const DATA = \{.*?\};\s+let currentStrat'
m = re.search(data_pattern, html, flags=re.DOTALL)
if m:
    html = html[:m.start()] + f'const DATA = {data_json_str};\n    let currentStrat' + html[m.end()-len('let currentStrat'):]
    print('Updated inlined DATA with new equity_curve!')
else:
    print('Error: Could not find const DATA pattern')

# 2. Update switchStrategy
new_switch_func = """    function switchStrategy(strat) {
      currentStrat = strat;
      
      const tabBtc = document.getElementById('tab-dom-abs-btc');
      const tabEth = document.getElementById('tab-dom-abs-eth');
      const tabRunner = document.getElementById('tab-runner');
      const tabSmc = document.getElementById('tab-smc');
      const tabFade = document.getElementById('tab-fade');
      const tabCompare = document.getElementById('tab-compare');
      
      [tabBtc, tabEth, tabRunner, tabSmc, tabFade, tabCompare].forEach(t => {
        if (!t) return;
        t.className = "px-3 py-1.5 text-xs md:text-sm font-medium rounded-lg transition-all text-slate-400 hover:text-white flex items-center gap-1.5";
      });

      const singleView = document.getElementById('single-view');
      const compareView = document.getElementById('compare-view');

      if (strat === 'compare') {
        if (tabCompare) tabCompare.className = "px-3 py-1.5 text-xs md:text-sm font-bold rounded-lg transition-all bg-emerald-500 text-slate-950 shadow flex items-center gap-1.5";
        if (singleView) singleView.classList.add('hidden');
        if (compareView) compareView.classList.remove('hidden');
        renderKpis('compare');
      } else {
        if (strat === 'dom_absorption_btc' && tabBtc) {
          tabBtc.className = "px-3 py-1.5 text-xs md:text-sm font-bold rounded-lg transition-all bg-amber-500 text-slate-950 shadow flex items-center gap-1.5";
        } else if (strat === 'dom_absorption_eth' && tabEth) {
          tabEth.className = "px-3 py-1.5 text-xs md:text-sm font-bold rounded-lg transition-all bg-blue-500 text-white shadow flex items-center gap-1.5";
        } else if (strat === 'dom_smart_runner' && tabRunner) {
          tabRunner.className = "px-3 py-1.5 text-xs md:text-sm font-bold rounded-lg transition-all bg-emerald-500 text-slate-950 shadow flex items-center gap-1.5";
        } else if (strat === 'smc_fibo_dom' && tabSmc) {
          tabSmc.className = "px-3 py-1.5 text-xs md:text-sm font-bold rounded-lg transition-all bg-emerald-500 text-slate-950 shadow flex items-center gap-1.5";
        } else if (tabFade) {
          tabFade.className = "px-3 py-1.5 text-xs md:text-sm font-bold rounded-lg transition-all bg-emerald-500 text-slate-950 shadow flex items-center gap-1.5";
        }
        if (singleView) singleView.classList.remove('hidden');
        if (compareView) compareView.classList.add('hidden');
        renderKpis(strat);
        renderTable();
        
        const list = DATA[strat] ? DATA[strat].trades : [];
        if (list.length > 0) {
          selectTrade(list[0].id, false);
        }
      }
    }"""

switch_pattern = r'function switchStrategy\(strat\) \{.*?\n    \}'
m2 = re.search(switch_pattern, html, flags=re.DOTALL)
if m2:
    html = html[:m2.start()] + new_switch_func + html[m2.end():]
    print('Updated switchStrategy function successfully!')
else:
    print('Error: Could not find switchStrategy pattern')

# 3. Update init()
old_init = """    function init() {
      switchStrategy('dom_smart_runner');
    }"""

new_init = """    function init() {
      switchStrategy('dom_absorption_btc');
      fetchLiveStatus();
    }"""

if old_init in html:
    html = html.replace(old_init, new_init)
    print('Updated init() to load dom_absorption_btc and fetchLiveStatus!')
else:
    print('Warning: old_init pattern not found')

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(html)
print('Saved docs/index.html successfully!')
