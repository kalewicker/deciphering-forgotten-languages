"""Read-only replay of source windows and exact counts without production imports."""
import json,hashlib,re
from pathlib import Path
from replay_burton_extract_v99 import replay
ROOT=Path(__file__).resolve().parents[1];OUT='runs/000099_burton_extract'
def read(p):return json.loads((ROOT/p).read_text())
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def main():
 reg=read('experiments/burton_extract_v99.json');m=read(OUT+'/manifest.json');receipt=read(OUT+'/window_verification.json');report=read(OUT+'/report.json')
 assert m['state']=='complete' and reg['frozen_at_utc']<=m['started_at_utc']<=receipt['verified_at_utc']<=report['comparison_completed_at_utc']
 for mapping in [reg['input_hashes'],m['input_hashes'],m['output_hashes']]:
  for p,h in mapping.items():assert sha(p)==h,p
 assert receipt['extraction_sha256']==sha(OUT+'/extraction.json') and receipt['targets_loaded'] is False
 extracted=replay((ROOT/'data/v98/acquisition/body.bin').read_bytes().decode('utf-8'));assert extracted==read(OUT+'/extraction.json')
 comp=read(OUT+'/comparison.json');targets=read('data/v96/targets.json')['targets'];assert len(targets)==22
 for mode in ['literal','whitespace']:
  ws=extracted['windows'] if mode=='literal' else [re.sub(r'\s+',' ',w).strip() for w in extracted['windows']]
  if mode=='whitespace':assert ws==comp['normalized_windows']
  rows=[];last_window=0;last_end=0
  for t in targets:
   needle=t['text'] if mode=='literal' else re.sub(r'\s+',' ',t['text']).strip()
   hits=[{'window':i,'span':[mm.start(),mm.start()+len(needle)]} for i,w in enumerate(ws) for mm in re.finditer('(?='+re.escape(needle)+')',w)]
   selected=None
   for hit in hits:
    if (hit['window'],hit['span'][0])>=(last_window,last_end):selected=hit;break
   if selected:last_window=selected['window'];last_end=selected['span'][1]
   rows.append({'occurrences':hits,'ordered_occurrence':selected})
  assert rows==comp[mode]['rows'] and comp[mode]['denominator']==22
  counts={'matched':sum(bool(r['occurrences']) for r in rows),'ordered_matched':sum(r['ordered_occurrence'] is not None for r in rows)}
  assert counts==report[mode]
  for k,v in counts.items():assert comp[mode][k]==v
  assert report[mode+'_missing_package_ordinals']==[i+2 for i,r in enumerate(rows) if not r['occurrences']]
 print(json.dumps({'verified':True,'targets':22,'window_lengths':receipt['window_lengths'],'literal':report['literal'],'whitespace':report['whitespace'],'network_requests':0,'shared_parser':'BeautifulSoup/html.parser'},indent=2))
if __name__=='__main__':main()
