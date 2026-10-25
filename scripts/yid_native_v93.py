"""Freeze before HTML decoding; single-use comparison."""
import json,hashlib,argparse
from pathlib import Path
from datetime import datetime,timezone
from fl_decipher.yid_native_v93 import assess
ROOT=Path(__file__).resolve().parents[1];OUT='runs/000093_yid_native';REG='experiments/yid_native_v93_execution.json'
def read(p):return json.loads((ROOT/p).read_text())
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def now():return datetime.now(timezone.utc).isoformat()
def write(p,x):
 with (ROOT/p).open('x') as f:json.dump(x,f,ensure_ascii=False,indent=2);f.write('\n')
def freeze():
 old=read('experiments/yid_native_v93.json')['input_hashes']
 for p,h in old.items():assert sha(p)==h,p
 paths=set(old)|{'experiments/yid_native_v93.json','data/v93/capture_inventory.json','data/v93/final_url_confirmation.json','src/fl_decipher/yid_native_v93.py','scripts/yid_native_v93.py','tests/test_yid_native_v93.py'}
 for e in read('data/v93/capture_inventory.json')['entries']:
  assert sha(e['path'])==e['sha256'];paths.add(e['path'])
 write(REG,{'frozen_at_utc':now(),'input_hashes':{p:sha(p) for p in sorted(paths)},'denominator':23,'network_requests':0})
 print('Execution frozen before decoding.')
def run():
 reg=read(REG)
 for p,h in reg['input_hashes'].items():assert sha(p)==h,p
 (ROOT/OUT).mkdir(exist_ok=False)
 manifest={'state':'running','started_at_utc':now(),'input_hashes':reg['input_hashes']|{REG:sha(REG)}};write(OUT+'/manifest.json',manifest)
 try:
  target=read('data/v93/targets.json');offer=read('data/v93/capture_inventory.json');confirmation=read('data/v93/final_url_confirmation.json')
  assert len(target['targets'])==23
  result=assess((ROOT/'data/v93/capture/page.html').read_bytes(),target['requested_url'],offer['reported_url'],confirmation['reported_final_url'],[x['text'] for x in target['targets']])
  write(OUT+'/comparison.json',result)
  report={'admissible':result['admissible'],'reasons':result['reasons'],'denominator':23,'counts':{k:{x:v[x] for x in ['denominator','matched','ordered_matched']} for k,v in (result['comparison'] or {}).items()},'network_requests':0,'semantic_benchmark_qualifying_works':0,'semantic_labels_validated':False,'new_confirmation_units':0}
  write(OUT+'/report.json',report);manifest.update(state='complete',finished_at_utc=now(),output_hashes={p:sha(p) for p in [OUT+'/comparison.json',OUT+'/report.json']});print(json.dumps(report,indent=2))
 except Exception as e:manifest.update(state='failed',error=repr(e));raise
 finally:(ROOT/OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['freeze','run']);{'freeze':freeze,'run':run}[p.parse_args().action]()
