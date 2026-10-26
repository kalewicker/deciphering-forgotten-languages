"""Read-only structural verification of failed E98 extraction; no wording search."""
import hashlib,json,re
from pathlib import Path
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads((ROOT/p).read_text())
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def main():
 reg=read('experiments/burton_paginated_v98_execution.json');m=read('runs/000098_burton_paginated/manifest.json')
 assert m['state']=='failed' and m['error']=='AssertionError()'
 assert reg['frozen_at_utc']<=m['started_at_utc']
 for p,h in reg['input_hashes'].items():assert sha(p)==h,p
 assert not (ROOT/'runs/000098_burton_paginated/comparison.json').exists()
 receipt=read('data/v98/acquisition/receipt.json');raw=(ROOT/'data/v98/acquisition/body.bin').read_bytes()
 assert receipt['exit_code']==0 and receipt['http_status']=='200' and receipt['bytes']==len(raw)==699009 and receipt['sha256']==hashlib.sha256(raw).hexdigest()
 soup=BeautifulSoup(raw.decode('utf-8'),'html.parser');anchors=[t for t in soup.find_all(id=True) if re.fullmatch(r'Page_[0-9]+',t['id'])]
 assert [int(t['id'].split('_')[1]) for t in anchors]==list(range(1,352))
 for n in range(252,258):
  a=soup.find(id=f'Page_{n}');assert a.parent.get_text()==f'[Pg {n}]'
 unsupported=[]
 for tag in soup.find_all(True):
  if 'pagenum' not in tag.get('class',[]):continue
  ids=[t['id'] for t in tag.find_all(id=True) if re.fullmatch(r'Page_[0-9]+',t['id'])]
  if len(ids)>1:unsupported.append({'anchor_count':len(ids),'first_anchor':ids[0],'last_anchor':ids[-1]})
 assert unsupported
 print(json.dumps({'verified':True,'html_bytes':len(raw),'numeric_page_anchors':351,'required_labels_match':True,'unsupported_multi_anchor_pagenum_elements':unsupported,'comparison_executed':False,'wording_counts':None,'shared_parser':'BeautifulSoup/html.parser'},indent=2))
if __name__=='__main__':main()
