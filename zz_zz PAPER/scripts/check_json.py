import json
import sys

sys.stdout.reconfigure(encoding='utf-8')
data = json.load(open('d:/cbot-atgvt/zz_zz PAPER/scripts/curated_arxiv_papers.json', encoding='utf-8'))
sample = data[0]
print("Key fields in curated_arxiv_papers.json:")
for k, v in sample.items():
    if k == 'abstract':
        print(f"  {k}: {v[:200]}...")
    else:
        print(f"  {k}: {v}")
