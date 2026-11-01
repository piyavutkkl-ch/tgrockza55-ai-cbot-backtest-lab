import urllib.request
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

def extract_arxiv_html_content(arxiv_id):
    url = f"https://arxiv.org/html/{arxiv_id}"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
    try:
        with urllib.request.urlopen(req) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
        
        # Check title
        title_m = re.search(r'<h1 class="ltx_title ltx_title_document">(.*?)</h1>', html, re.DOTALL)
        if not title_m:
            title_m = re.search(r'<title>(.*?)</title>', html, re.DOTALL)
        title = re.sub(r'<[^>]+>', '', title_m.group(1)).strip() if title_m else arxiv_id
        
        # Check abstract
        abs_m = re.search(r'<div class="ltx_abstract">(.*?)</div>', html, re.DOTALL)
        abstract = re.sub(r'<[^>]+>', ' ', abs_m.group(1)).strip() if abs_m else ""
        abstract = re.sub(r'\s+', ' ', abstract)
        
        # Check sections
        sections = re.findall(r'<h2 class="ltx_title ltx_title_section">(.*?)</h2>', html, re.DOTALL)
        clean_sections = [re.sub(r'<[^>]+>', '', s).strip() for s in sections]
        
        return {
            "status": "success",
            "arxiv_id": arxiv_id,
            "title": title,
            "abstract": abstract[:300],
            "sections": clean_sections[:8],
            "html_length": len(html)
        }
    except Exception as e:
        return {"status": "error", "arxiv_id": arxiv_id, "error": str(e)}

res1 = extract_arxiv_html_content("1808.03668")
print("DeepLOB result:", res1)

res2 = extract_arxiv_html_content("2403.13429")
print("Spoofing TCN result:", res2)
