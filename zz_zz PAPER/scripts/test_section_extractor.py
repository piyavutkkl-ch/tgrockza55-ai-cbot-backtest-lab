import urllib.request
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

url = "https://arxiv.org/html/1808.03668"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req) as resp:
    html = resp.read().decode('utf-8', errors='ignore')

# Extract sections
sections = re.findall(r'<section\s+id="([^"]+)"\s+class="ltx_section"[^>]*>(.*?)</section>', html, re.DOTALL)
print(f"Total sections found: {len(sections)}")

for sec_id, sec_content in sections[:3]:
    title_m = re.search(r'<h2[^>]*>(.*?)</h2>', sec_content, re.DOTALL)
    title = re.sub(r'<[^>]+>', '', title_m.group(1)).strip() if title_m else sec_id
    
    # extract paragraphs
    paras = re.findall(r'<div class="ltx_para"[^>]*>(.*?)</div>', sec_content, re.DOTALL)
    clean_paras = [re.sub(r'<[^>]+>', ' ', p).strip() for p in paras]
    clean_paras = [re.sub(r'\s+', ' ', p) for p in clean_paras if len(p) > 20]
    
    print(f"\n--- Section: {title} (ID: {sec_id}) ---")
    print(f"Paragraphs count: {len(clean_paras)}")
    if clean_paras:
        print(f"First para preview: {clean_paras[0][:200]}...")
