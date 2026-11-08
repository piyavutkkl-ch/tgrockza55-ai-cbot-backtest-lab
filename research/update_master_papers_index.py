"""
Build Master PAPERS_INDEX.md from unified papers_database.json (ArXiv + SSRN)
------------------------------------------------------------------------------
Generates a complete, beautiful markdown catalog linking all 193 papers
with direct HTML viewing links and local markdown dossier links.
"""

import os
import sys
import json

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = r"d:\cbot-atgvt\zz_zz PAPER"
DB_PATH = os.path.join(BASE_DIR, "papers_database.json")
INDEX_PATH = os.path.join(BASE_DIR, "PAPERS_INDEX.md")

CAT_ICONS = {
    "01_lob_and_deep_learning": "🧠 LOB & Deep Learning",
    "02_order_flow_imbalance": "📊 Order Flow Imbalance",
    "03_market_making_and_spread": "⚖️ Market Making & Spread",
    "04_optimal_execution_and_vwap": "⏱️ Execution & VWAP",
    "05_hawkes_and_event_clustering": "📈 Hawkes & Vol Clustering",
    "06_gold_commodity_and_macro": "🥇 Gold & Commodities",
    "07_regime_detection_and_hmm": "🔄 Regime Detection & HMM",
    "08_lead_lag_and_latency": "⚡ Lead-Lag & Latency",
    "09_signal_processing_and_kalman": "📡 Kalman & Filtering",
    "10_synthetic_data_and_simulation": "🎲 Synthetic Simulation",
    "11_financial_llm_and_sentiment": "💬 LLM & Macro News",
    "12_position_sizing_and_risk": "🛡️ Kelly & Risk Sizing",
    "13_rough_volatility_and_jumps": "🌊 Rough Vol & Jumps"
}

def main():
    if not os.path.exists(DB_PATH):
        print("Database not found!")
        return

    with open(DB_PATH, "r", encoding="utf-8") as f:
        db = json.load(f)

    arxiv_count = sum(1 for p in db if 'arxiv_id' in p)
    ssrn_count = sum(1 for p in db if p.get('source') == 'SSRN' or 'ssrn_id' in p)
    total = len(db)

    print(f"Total Papers in Database: {total} (ArXiv: {arxiv_count}, SSRN: {ssrn_count})")

    lines = [
        "# 📑 สารบัญงานวิจัยเชิงปริมาณฉบับสมบูรณ์ (Master Quant Research Library)",
        f"รวบรวมงานวิจัยการเงินเชิงปริมาณจาก **arXiv (Quantitative Finance)** และ **SSRN (Social Science Research Network)** รวมทั้งสิ้น **{total} ชิ้นงาน** (arXiv: {arxiv_count} ฉบับ, SSRN: {ssrn_count} ฉบับ)",
        "",
        "> 💡 **คำแนะนำการเปิดอ่าน (Direct HTML Access):**",
        "> - ทุกลิงก์ถูกจัดเตรียมเป็น **ลิงก์หน้าเว็บ HTML** สามารถคลิกเปิดอ่านบทคัดย่อ ข้อความเต็ม และสมการได้ทันทีในเว็บเบราว์เซอร์ โดย**ไม่ต้องดาวน์โหลดไฟล์ PDF** ให้เสี่ยงติด Rate Limit หรือเปลืองพื้นที่จัดเก็บ",
        "> - ไฟล์สรุปในเครื่องถูกบันทึกเป็น Markdown (.md) อยู่ในโฟลเดอร์หมวดหมู่ 13 โฟลเดอร์ พร้อมนำไปประยุกต์เขียน cBot บน cTrader Automate",
        "",
        "---",
        "",
        "### 📊 สรุปจำนวนงานวิจัยแยกตาม 13 หมวดหมู่วิจัย",
        "| รหัสหมวดหมู่ | ชื่อหมวดหมู่ | จำนวนงานวิจัยรวม | แหล่งข้อมูล (Sources) |",
        "| :---: | :--- | :---: | :--- |"
    ]

    # Category stats
    cat_counts = {}
    for p in db:
        c = p.get('category_folder', 'other')
        cat_counts[c] = cat_counts.get(c, 0) + 1

    for c in sorted(cat_counts.keys()):
        icon_name = CAT_ICONS.get(c, c)
        lines.append(f"| `{c[:2]}` | {icon_name} | **{cat_counts[c]} ฉบับ** | arXiv + SSRN |")

    lines.extend([
        "",
        "---",
        "",
        "## 📚 รายชื่อและลิงก์งานวิจัยทั้งหมด (Full Directory)",
        "",
        "| # | หมวดหมู่ | แหล่งที่มา | รหัสอ้างอิง | ชื่องานวิจัย | ผู้แต่ง | ปี | ลิงก์เปิดอ่าน (HTML) | สรุปในโปรเจกต์ |",
        "| :---: | :--- | :---: | :---: | :--- | :--- | :---: | :---: | :---: |"
    ])

    for i, p in enumerate(db, 1):
        cat = p.get('category_folder', '')
        icon = CAT_ICONS.get(cat, cat).split()[0]
        
        is_ssrn = (p.get('source') == 'SSRN' or 'ssrn_id' in p)
        if is_ssrn:
            source = "SSRN"
            ref_id = f"SSRN-{p.get('ssrn_id', '')}"
            html_link = f"[เปิดอ่าน HTML]({p.get('url', '')})"
            pub_year = str(p.get('published', ''))[:4]
            rel_path = p.get('markdown_file', f"{cat}/ssrn_{p.get('ssrn_id')}.md")
        else:
            source = "arXiv"
            base_id = p.get('base_id', p.get('arxiv_id', '').split('v')[0])
            ref_id = f"`{p.get('arxiv_id', '')}`"
            html_link = f"[เปิดอ่าน HTML](https://arxiv.org/html/{base_id})"
            pub_year = str(p.get('published', ''))[:4]
            slug = p.get('title', '')[:30].replace(' ', '_').lower()
            rel_path = f"{cat}/{base_id}_{slug}.md"

        authors = p.get('authors', [])
        auth_str = authors[0] if len(authors) == 1 else (f"{authors[0]} et al." if authors else "-")
        title_str = p.get('title', '').replace('|', '-').strip()
        if len(title_str) > 60:
            title_str = title_str[:57] + "..."

        lines.append(
            f"| {i} | {icon} `{cat[:2]}` | **{source}** | {ref_id} | {title_str} | {auth_str} | {pub_year} | {html_link} | [`{os.path.basename(rel_path)}`]({rel_path}) |"
        )

    lines.append("\n---\n*ฐานข้อมูลสารบัญงานวิจัยอัปเดตสมบูรณ์ เชื่อมโยงระบบ BacktestLab และ cBot อัตโนมัติ*")

    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"✅ Generated Master PAPERS_INDEX.md with {total} papers at: {INDEX_PATH}")

if __name__ == '__main__':
    main()
