"""Freeze comparator before one fixed-window wording test."""
from pathlib import Path
import json,hashlib,datetime
from fl_decipher.burton_paginated_v98 import assess
ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads((ROOT/p).read_text())
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def write(p,o):
 with (ROOT/p).open('x') as f:json.dump(o,f,indent=2,ensure_ascii=False);f.write('\n')
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def freeze():
 old=read('experiments/burton_paginated_v98.json')['input_hashes']
 for p,h in old.items():assert sha(p)==h,p
 paths=set(old)|{'experiments/burton_paginated_v98.json','experiments/burton_paginated_v98_link_resolution.md','src/fl_decipher/burton_paginated_v98.py','scripts/burton_paginated_v98.py','scripts/burton_html_acquire_v98.py','tests/test_burton_paginated_v98.py'}|{str(p.relative_to(ROOT)) for p in (ROOT/'data/v98').rglob('*') if p.is_file()}
 write('experiments/burton_paginated_v98_execution.json',{'frozen_at_utc':now(),'input_hashes':{p:sha(p) for p in sorted(paths)}})
 print('Comparator frozen before target matching.')
def run():
 reg=read('experiments/burton_paginated_v98_execution.json')
 for p,h in reg['input_hashes'].items():assert sha(p)==h,p
 out=ROOT/'runs/000098_burton_paginated';out.mkdir(exist_ok=False)
 m={'state':'running','started_at_utc':now(),'input_hashes':reg['input_hashes']};write('runs/000098_burton_paginated/manifest.json',m)
 try:
  receipt=read('data/v98/acquisition/receipt.json');assert receipt['exit_code']==0 and receipt['http_status']=='200' and receipt['bytes']<=8388608
  headers=(ROOT/'data/v98/acquisition/headers.txt').read_text().lower();assert 'content-encoding:' not in headers or 'content-encoding: identity' in headers
  html=(ROOT/'data/v98/acquisition/body.bin').read_bytes().decode('utf-8')
  target=read('data/v96/targets.json')['targets'];assert len(target)==22
  result=assess(html,[t['text'] for t in target]);write('runs/000098_burton_paginated/comparison.json',result)
  report={'target_denominator':22,'page_binding_admitted':True,'literal':{k:result['literal'][k] for k in ['matched','ordered_matched']},'whitespace':{k:result['whitespace'][k] for k in ['matched','ordered_matched']},'window_characters':[len(w) for w in result['windows']],'native_http_gets':1,'provider_calls':2,'semantic_benchmark_qualifying_works':0,'new_confirmation_units':0}
  write('runs/000098_burton_paginated/report.json',report)
  m.update(state='complete',finished_at_utc=now(),output_hashes={str(p.relative_to(ROOT)):sha(str(p.relative_to(ROOT))) for p in out.glob('*.json') if p.name!='manifest.json'});print(json.dumps(report,indent=2))
 except Exception as e:m.update(state='failed',error=repr(e));raise
 finally:(out/'manifest.json').write_text(json.dumps(m,indent=2)+'\n')
if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('action',choices=['freeze','run']);{'freeze':freeze,'run':run}[p.parse_args().action]()
