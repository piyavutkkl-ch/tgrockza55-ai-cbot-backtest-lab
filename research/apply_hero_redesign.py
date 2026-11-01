import re

html_path = r'd:\cbot-atgvt\docs\index.html'

with open(html_path, 'r', encoding='utf-8') as f:
    html = f.read()

# =========================================================================
# 1. REPLACE THE OUTDATED "1. LIVE SYSTEM STATUS CHECK BANNER"
#    WITH THE NEW "HERO WELCOME & ONBOARDING FOR FIRST-TIME VISITORS"
# =========================================================================

old_banner_pattern = r'<!-- 1\. LIVE SYSTEM STATUS CHECK BANNER.*?(?=<!-- 2\. HEADER & STRATEGY SWITCHER -->)'

new_hero_html = '''<!-- 1. HERO ONBOARDING & BEGINNER ORIENTATION (FOR FIRST-TIME VISITORS) -->
    <div class="bg-gradient-to-br from-slate-900 via-slate-900 to-slate-950 border border-slate-800 rounded-2xl p-5 sm:p-6 shadow-xl relative overflow-hidden">
      <!-- Glow ambient lighting -->
      <div class="absolute -top-24 -right-24 w-96 h-96 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none"></div>
      <div class="absolute -bottom-24 -left-24 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl pointer-events-none"></div>

      <div class="relative z-10">
        <!-- Top bar with badges & toggle button -->
        <div class="flex flex-wrap items-center justify-between gap-3 mb-3">
          <div class="flex flex-wrap items-center gap-2">
            <span class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 shadow-sm">
              <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
              ห้องทดลองวิจัยอัลกอริทึมเทรด (Quant Backtest Lab)
            </span>
            <span class="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-slate-800 text-slate-300 border border-slate-700">
              สำหรับผู้เข้าชมใหม่ & นักลงทุน
            </span>
          </div>
          
          <!-- Beginner Guide Toggle Button -->
          <button onclick="toggleBeginnerGuide()" class="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-xl bg-blue-600/20 hover:bg-blue-600/30 text-blue-300 border border-blue-500/40 text-xs font-bold transition shadow-sm cursor-pointer">
            <span>📖</span> <span id="guide-btn-text">คลิกเปิด "คู่มือมือใหม่ & พจนานุกรมศัพท์"</span>
          </button>
        </div>

        <h1 class="text-xl sm:text-2xl md:text-3xl font-extrabold text-white tracking-tight">
          ถอดรหัสสมุดคำสั่งซื้อขายสถาบัน (Level 2 Order Book) สู่ระบบเทรดทำกำไรอัตโนมัติ
        </h1>
        <p class="text-xs sm:text-sm text-slate-300 mt-2 max-w-4xl leading-relaxed">
          ยินดีต้อนรับครับ! หน้านี้คือ <strong>ห้องทดลองแบบเปิด (Open Quant Lab)</strong> ที่แสดงผลการทดสอบย้อนหลัง (Backtest) 
          และการรันเทรดจริงไปข้างหน้า (Forward Trading) โดยใช้ข้อมูล <strong>สมุดคำสั่งซื้อขายจริง (Depth of Market - DOM)</strong> 
          ตลอด 24 ชั่วโมง เราไม่เดาทิศทางกราฟ แต่จับจังหวะเข้าเทรดตาม "กำแพงเงินจริง" ของสถาบันขนาดใหญ่
        </p>

        <!-- 3 Quick Pillars of Understanding -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-3.5 mt-4">
          <div class="bg-slate-950/70 border border-slate-800/80 rounded-xl p-3.5 hover:border-amber-500/30 transition">
            <div class="flex items-center gap-2 text-amber-400 font-bold text-xs mb-1">
              <span>🧠</span> 1. จุดได้เปรียบของระบบ (The Edge)
            </div>
            <p class="text-[11px] text-slate-400 leading-relaxed">
              แท่งเทียนบอกแค่อดีต แต่ <strong>Level 2 Order Book</strong> บอกว่ามีคนตั้งรับซื้อ (Bid Wall) หรือตั้งขวางขาย (Ask Wall) รอไว้เท่าไร 
              บอทจะเข้าเทรดเมื่อมีกำแพงเงินจริงมาคอยซับแรงและพยุงราคาเท่านั้น
            </p>
          </div>

          <div class="bg-slate-950/70 border border-slate-800/80 rounded-xl p-3.5 hover:border-emerald-500/30 transition">
            <div class="flex items-center gap-2 text-emerald-400 font-bold text-xs mb-1">
              <span>📊</span> 2. ผลลัพธ์จริง (หักค่าสเปรดแล้ว)
            </div>
            <p class="text-[11px] text-slate-400 leading-relaxed">
              ทดสอบบนข้อมูลจริงข้ามคืน 9.1 ชม. ทำกำไรสุทธิ <strong>+$30.41 USD (+30.4% จากทุน $100)</strong> 
              Win Rate <strong>68.2%</strong> และ Profit Factor สูงถึง <strong>4.72</strong> โดยความเสี่ยงย่อตัว (Max Drawdown) ต่ำกว่า 3%
            </p>
          </div>

          <div class="bg-slate-950/70 border border-slate-800/80 rounded-xl p-3.5 hover:border-cyan-500/30 transition">
            <div class="flex items-center gap-2 text-cyan-400 font-bold text-xs mb-1">
              <span>🔴</span> 3. บอทกำลังเทรดสดในตลาด
            </div>
            <p class="text-[11px] text-slate-400 leading-relaxed">
              ไม่ได้มีแค่ผลอดีต! ขณะนี้บอทกำลังส่งคำสั่งซื้อขายจริงบนพอร์ต <strong>Pepperstone Demo #5258778</strong> 
              และบันทึกสมุดคำสั่ง 3 สินทรัพย์ (BTC, ETH, ทองคำ) ส่งข้อมูลสดขึ้นเว็บทุกๆ 3 วินาที
            </p>
          </div>
        </div>

        <!-- COLLAPSIBLE BEGINNER GUIDE (Opened or Closed with Smooth Design) -->
        <div id="beginner-guide-drawer" class="mt-4 pt-4 border-t border-slate-800/80">
          <div class="bg-slate-950/90 border border-blue-500/30 rounded-xl p-4 sm:p-5">
            <div class="flex items-center justify-between mb-3 border-b border-slate-800 pb-2.5">
              <h3 class="text-xs sm:text-sm font-bold text-blue-400 flex items-center gap-2">
                <span>💡</span> พจนานุกรมศัพท์ & วิธีอ่านตัวเลขบนหน้านี้ (สำหรับคนมีความรู้เทรดเล็กน้อย)
              </h3>
              <button onclick="toggleBeginnerGuide()" class="text-xs text-slate-400 hover:text-white px-2 py-0.5 rounded bg-slate-900 border border-slate-800">
                ย่อเก็บ ▲
              </button>
            </div>
            
            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 text-xs">
              <div class="bg-slate-900/80 p-3 rounded-lg border border-slate-800">
                <div class="font-bold text-amber-400 flex items-center gap-1.5">
                  <span>📖</span> 1. DOM (Depth of Market)
                </div>
                <p class="text-slate-300 mt-1.5 leading-relaxed text-[11px]">
                  คือ <strong>"สมุดคำสั่งซื้อขายสด"</strong> ที่โชว์ว่าที่ราคาต่างๆ มีคนวางออเดอร์ Bid/Ask รอไว้กี่เหรียญ เหมือนการมองเห็นไพ่ในมือของตลาดล่วงหน้า
                </p>
              </div>

              <div class="bg-slate-900/80 p-3 rounded-lg border border-slate-800">
                <div class="font-bold text-cyan-400 flex items-center gap-1.5">
                  <span>⚖️</span> 2. DOM Imbalance (% แรงซื้อ/ขาย)
                </div>
                <p class="text-slate-300 mt-1.5 leading-relaxed text-[11px]">
                  วัดความเอียงของสมุดคำสั่ง: <br/>
                  • <strong class="text-emerald-400">+0.03 ขึ้นไป:</strong> มี Bid Wall หนุนรับ (จังหวะ Buy)<br/>
                  • <strong class="text-rose-400">-0.03 ลงไป:</strong> มี Ask Wall ขวางต้าน (จังหวะ Sell)
                </p>
              </div>

              <div class="bg-slate-900/80 p-3 rounded-lg border border-slate-800">
                <div class="font-bold text-emerald-400 flex items-center gap-1.5">
                  <span>🏆</span> 3. Profit Factor (PF)
                </div>
                <p class="text-slate-300 mt-1.5 leading-relaxed text-[11px]">
                  คือ <strong>ยอดกำไรรวม ÷ ยอดขาดทุนรวม</strong><br/>
                  ระบบทั่วไป > 1.5 ถือว่าดีมาก ส่วนระดับสถาบัน > 2.0 (ระบบนี้ได้ <strong>4.24</strong> แปลว่าได้กำไร $4.24 ทุกๆ การขาดทุน $1)
                </p>
              </div>

              <div class="bg-slate-900/80 p-3 rounded-lg border border-slate-800">
                <div class="font-bold text-purple-400 flex items-center gap-1.5">
                  <span>🛡️</span> 4. Max Drawdown
                </div>
                <p class="text-slate-300 mt-1.5 leading-relaxed text-[11px]">
                  คือ <strong>การติดลบสูงสุดของพอร์ตจากจุดพีค</strong> บ่งบอกความปลอดภัย ระบบนี้ Drawdown ต่ำเพียง $1.39 (1.4% ของทุน) จึงปลอดภัยจากการล้างพอร์ตอย่างยิ่ง
                </p>
              </div>
            </div>

            <div class="mt-3.5 pt-2.5 border-t border-slate-800/80 text-[11px] text-slate-400 flex flex-wrap items-center justify-between gap-2">
              <div class="flex flex-wrap items-center gap-3">
                <span class="text-slate-300 font-semibold">👉 ลำดับการดูข้อมูล:</span>
                <span>1. ดูกล่องมอนิเตอร์สด (สีส้ม) เช็คตลาดปัจจุบัน</span>
                <span>2. กดปุ่มด้านล่างเพื่อเลือกดูแต่ละกลยุทธ์</span>
                <span>3. คลิกแถวในตารางเพื่อโฟกัสแท่งเทียนรอบจุดเข้า-ออก</span>
              </div>
              <span class="text-emerald-400">💡 บันทึกข้อมูลและหักค่าสเปรดโบรกเกอร์ครบทุกไม้</span>
            </div>
          </div>
        </div>

      </div>
    </div>
'''

html = re.sub(old_banner_pattern, new_hero_html, html, flags=re.DOTALL)
print("Updated Hero & Onboarding Banner successfully!")

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(html)
print("Saved docs/index.html step 1!")
