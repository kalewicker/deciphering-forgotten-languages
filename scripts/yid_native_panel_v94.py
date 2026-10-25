"""Single-use freeze and complete two-post panel."""
import json,hashlib,argparse
from pathlib import Path
from datetime import datetime,timezone
from fl_decipher.yid_native_panel_v94 import panel
ROOT=Path(__file__).resolve().parents[1];OUT='runs/000094_yid_native_panel';REG='experiments/yid_native_panel_v94_execution.json'
def read(p):return json.loads((ROOT/p).read_text())
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def now():return datetime.now(timezone.utc).isoformat()
def write(p,x):
 with (ROOT/p).open('x') as f:json.dump(x,f,indent=2,ensure_ascii=False);f.write('\n')
def freeze():
 old=read('experiments/yid_native_panel_v94.json')['input_hashes']
 for p,h in old.items():assert sha(p)==h,p
 paths=set(old)|{'experiments/yid_native_panel_v94.json','data/v94/capture_inventory.json','data/v94/final_url_confirmation.json','src/fl_decipher/yid_native_panel_v94.py','scripts/yid_native_panel_v94.py','tests/test_yid_native_panel_v94.py'}
 for s in read('data/v94/capture_inventory.json')['slots']:
  for e in s['entries']:
   assert sha(e['path'])==e['sha256'];paths.add(e['path'])
 write(REG,{'frozen_at_utc':now(),'input_hashes':{p:sha(p) for p in sorted(paths)},'fixed_targets':278,'fixed_posts':2})
 print('Panel frozen before either HTML was decoded.')
def run():
 reg=read(REG)
 for p,h in reg['input_hashes'].items():assert sha(p)==h,p
 (ROOT/OUT).mkdir(exist_ok=False)
 m={'state':'running','started_at_utc':now(),'input_hashes':reg['input_hashes']|{REG:sha(REG)}};write(OUT+'/manifest.json',m)
 try:
  docs=read('data/v94/targets.json')['documents'];slots=read('data/v94/capture_inventory.json')['slots'];final=read('data/v94/final_url_confirmation.json')['final_urls']
  assert [d['denominator'] for d in docs]==[36,242]
  for s in slots:s['final_url']=final[str(s['number'])]
  result=panel(docs,slots,lambda p:(ROOT/p).read_bytes())
  write(OUT+'/comparison.json',result['results']);write(OUT+'/report.json',result['report'])
  m.update(state='complete',finished_at_utc=now(),output_hashes={p:sha(p) for p in [OUT+'/comparison.json',OUT+'/report.json']});print(json.dumps(result['report'],indent=2))
 except Exception as e:m.update(state='failed',error=repr(e));raise
 finally:(ROOT/OUT/'manifest.json').write_text(json.dumps(m,indent=2)+'\n')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['freeze','run']);{'freeze':freeze,'run':run}[p.parse_args().action]()
