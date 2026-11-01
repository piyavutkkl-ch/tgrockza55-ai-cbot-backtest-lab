html_path = r'd:\cbot-atgvt\docs\index.html'

with open(html_path, 'r', encoding='utf-8') as f:
    text = f.read()

# Update description
old_desc = 'บอท <strong>BacktestLab (DOM_ABSORPTION)</strong> กำลังเฝ้าสมุดคำสั่ง Level 2 และส่งคำสั่งเทรดสดบนพอร์ต Pepperstone #5258778'
new_desc = 'บอท <strong>BacktestLab (DOM_ABSORPTION)</strong> กำลังรันส่งคำสั่งเทรดสด <strong>2 คู่ขนานกัน (BTCUSD + ETHUSD)</strong> บนพอร์ต Pepperstone Demo #5258778'

if old_desc in text:
    text = text.replace(old_desc, new_desc)
    print("Updated bot description!")

# Update box 1
old_box1 = '''          <div class="text-[11px] text-slate-400">สินทรัพย์ที่เทรดสด</div>
          <div id="live-symbol" class="text-base font-extrabold text-white mt-1 font-mono">BTCUSD (M1)</div>
          <div class="text-[10px] text-amber-400 mt-0.5">0.01 Lot / TP $50 / SL $25</div>'''

new_box1 = '''          <div class="text-[11px] text-slate-400">สินทรัพย์ที่เทรดสด (คู่ขนาน)</div>
          <div id="live-symbol" class="text-base font-extrabold text-white mt-1 font-mono">BTC & ETH (M1)</div>
          <div class="text-[10px] text-amber-400 mt-0.5">0.01 Lot | BTC (TP $50) & ETH (TP $3.5)</div>'''

if old_box1 in text:
    text = text.replace(old_box1, new_box1)
    print("Updated Box 1 text!")

# Update fetchLiveStatus to show both BTC & ETH
old_fetch_btc = """        if (data.dom_recorders && data.dom_recorders.length > 0) {
          const btc = data.dom_recorders[0];
          if (elPrice) elPrice.textContent = '$' + btc.current_price.toFixed(2);
          if (elSpread) elSpread.textContent = 'Spread: $' + btc.spread.toFixed(2);
          if (elImb) {
            elImb.textContent = (btc.imbalance >= 0 ? '+' : '') + btc.imbalance.toFixed(3);
            if (btc.imbalance >= 0.03) {
              elImb.className = 'text-base font-extrabold mt-1 font-mono text-emerald-400';
              document.getElementById('live-imbalance-desc').textContent = '⚠️ Bid Wall หนุนรับ (จังหวะ Buy)';
            } else if (btc.imbalance <= -0.03) {
              elImb.className = 'text-base font-extrabold mt-1 font-mono text-rose-400';
              document.getElementById('live-imbalance-desc').textContent = '⚠️ Ask Wall ขวางต้าน (จังหวะ Sell)';
            } else {
              elImb.className = 'text-base font-extrabold mt-1 font-mono text-cyan-400';
              document.getElementById('live-imbalance-desc').textContent = 'สมุดคำสั่งสมดุลปกติ';
            }
          }
          if (elCvd) elCvd.textContent = (btc.cvd >= 0 ? '+' : '') + Math.round(btc.cvd);
        }"""

new_fetch_btc = """        if (data.dom_recorders && data.dom_recorders.length >= 2) {
          const btc = data.dom_recorders[0];
          const eth = data.dom_recorders[1];
          if (elPrice) elPrice.innerHTML = `<span class="text-amber-400 font-bold">$${btc.current_price.toFixed(0)}</span> <span class="text-slate-500 text-xs">/</span> <span class="text-blue-400 font-bold">$${eth.current_price.toFixed(1)}</span>`;
          if (elSpread) elSpread.textContent = `Spread: BTC $${btc.spread.toFixed(1)} | ETH $${eth.spread.toFixed(2)}`;
          if (elImb) {
            elImb.innerHTML = `<span class="${btc.imbalance >= 0.03 ? 'text-emerald-400' : btc.imbalance <= -0.03 ? 'text-rose-400' : 'text-slate-300'}">${btc.imbalance >= 0 ? '+' : ''}${btc.imbalance.toFixed(2)}</span> <span class="text-slate-600 text-xs">|</span> <span class="${eth.imbalance >= 0.03 ? 'text-emerald-400' : eth.imbalance <= -0.03 ? 'text-rose-400' : 'text-slate-300'}">${eth.imbalance >= 0 ? '+' : ''}${eth.imbalance.toFixed(2)}</span>`;
            document.getElementById('live-imbalance-desc').textContent = 'BTC (ซ้าย) | ETH (ขวา) Imbalance';
          }
          if (elCvd) elCvd.textContent = (btc.cvd >= 0 ? '+' : '') + Math.round(btc.cvd);
        }"""

if old_fetch_btc in text:
    text = text.replace(old_fetch_btc, new_fetch_btc)
    print("Updated fetchLiveStatus function!")

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(text)
print("Saved docs/index.html!")
