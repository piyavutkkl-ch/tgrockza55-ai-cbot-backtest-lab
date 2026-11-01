import json
import sys

sys.stdout.reconfigure(encoding='utf-8')
data = json.load(open('d:/cbot-atgvt/zz_zz PAPER/scripts/curated_arxiv_papers.json', encoding='utf-8'))
print(f"Total papers: {len(data)}\n")
for i, p in enumerate(data, 1):
    print(f"{i:2d}. [{p['category_folder']}] {p['arxiv_id']} ({p['published']}): {p['title']}")
