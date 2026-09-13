"""Read-only content validation, not a substitute for visual browser QA."""
import json,re
from html.parser import HTMLParser
from pathlib import Path

root=Path(__file__).resolve().parent
class Reader(HTMLParser):
    def __init__(self):
        super().__init__(); self.main=False; self.text=[]; self.tables=0; self.scripts=0
    def handle_starttag(self,tag,attrs):
        if tag=='main' and dict(attrs).get('id')=='data-analytics-portable-fallback':self.main=True
        self.scripts+=tag=='script'
        if self.main:self.tables+=tag=='table'
    def handle_endtag(self,tag):
        if tag=='main':self.main=False
    def handle_data(self,data):
        if self.main:self.text.append(data)

a=json.loads((root/'artifact-readable-v2.json').read_text())
html=(root/'report-readable-v2.html').read_text();p=Reader();p.feed(html)
text=' '.join(p.text)
missing=[]
for table in a['manifest']['tables']:
    for row in a['snapshot']['datasets'][table['dataset']]:
        for value in row.values():
            if str(value) not in text:missing.append(str(value))
headings=[line.lstrip('# ').strip() for b in a['manifest']['blocks'] if b['type']=='markdown'
          for line in b['body'].splitlines() if line.startswith('#')]
missing.extend(h for h in headings if h not in text)
result={'status':'passed' if not missing and p.scripts==0 and p.tables==4 else 'failed',
        'missing_headings_or_cells':missing,'tables':p.tables,'scripts':p.scripts,
        'headings_verified':len(headings),'browser_visual_qa':'not_run_url_policy_block',
        'mobile_css_present':'max-width:760px' in html,
        'dark_css_present':'prefers-color-scheme:dark' in html}
(root/'readability-content-audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
print(json.dumps(result,ensure_ascii=False))
raise SystemExit(result['status']!='passed')
