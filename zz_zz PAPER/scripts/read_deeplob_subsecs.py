import urllib.request, re, sys
from html.parser import HTMLParser

sys.stdout.reconfigure(encoding='utf-8')

class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text = []
        self.ignore = False
    def handle_starttag(self, tag, attrs):
        if tag in ['script', 'style']: self.ignore = True
    def handle_endtag(self, tag):
        if tag in ['script', 'style']: self.ignore = False
    def handle_data(self, data):
        if not self.ignore: self.text.append(data)
    def get_text(self):
        return ' '.join(self.text)

def clean(s):
    t = TextExtractor()
    t.feed(s)
    return re.sub(r'\s+', ' ', t.get_text()).strip()

url = "https://arxiv.org/html/1808.03668"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req) as resp:
    html = resp.read().decode('utf-8', errors='ignore')

subsecs = re.findall(r'<section\s+id="([^"]+)"\s+class="ltx_subsection"[^>]*>(.*?)</section>', html, re.DOTALL)
for sid, scontent in subsecs:
    h3 = re.search(r'<h3[^>]*>(.*?)</h3>', scontent, re.DOTALL)
    title = clean(h3.group(1)) if h3 else sid
    print(f"\n=== Subsection: {title} ({sid}) ===")
    paras = re.findall(r'<p\s+[^>]*class="ltx_p"[^>]*>(.*?)</p>', scontent, re.DOTALL)
    for p in paras[:2]:
        print("  *", clean(p)[:250] + "...")
