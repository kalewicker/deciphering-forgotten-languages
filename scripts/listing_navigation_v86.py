"""Freeze and run one navigation-only inventory on the E85 snapshot."""
import argparse,hashlib,json
from datetime import datetime,timezone
from pathlib import Path
from fl_decipher.listing_navigation_v86 import inventory
ROOT=Path(__file__).resolve().parents[1];REG='experiments/listing_navigation_v86.json';OUT='runs/000086_listing_navigation'
CODE=['experiments/listing_navigation_v86.md','src/fl_decipher/listing_navigation_v86.py','scripts/listing_navigation_v86.py',
 'scripts/verify_listing_navigation_v86.py','tests/test_listing_navigation_v86.py']
def read(p):return json.loads((ROOT/p).read_text())
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def now():return datetime.now(timezone.utc).isoformat()
def write(p,x):
 path=ROOT/p;path.parent.mkdir(parents=True,exist_ok=True)
 with path.open('x') as f:json.dump(x,f,indent=2,ensure_ascii=False);f.write('\n')
def prepare():
 seal='reports/000085_deliverable_seal.json'
 for p,h in read(seal)['deliverable_hashes'].items():assert sha(p)==h,p
 assert read('runs/000085_browser_listing/report.json')['origin']['metadata_use_allowed']
 html=read('experiments/browser_listing_v85.json')['html_path']
 paths=CODE+[seal,html,'runs/000085_browser_listing/report.json']
 write(REG,{'experiment_id':'listing_navigation_v86','registered_at_utc':now(),'html_path':html,
            'input_hashes':{p:sha(p) for p in paths},'network_requests':0,'maximum_next_capture_targets':1})
 print('Frozen navigation scope before pager inspection.')
def run():
 reg=read(REG)
 for p,h in reg['input_hashes'].items():assert sha(p)==h,p
 (ROOT/OUT).mkdir(exist_ok=False)
 m={'experiment_id':'listing_navigation_v86','state':'running','started_at_utc':now(),
    'input_hashes':reg['input_hashes']|{REG:sha(REG)},'network_requests':0}
 write(OUT+'/manifest.json',m)
 try:
  report={'experiment_id':'listing_navigation_v86',**inventory((ROOT/reg['html_path']).read_bytes())}
  write(OUT+'/report.json',report)
  m.update(state='complete',finished_at_utc=now(),output_hashes={OUT+'/report.json':sha(OUT+'/report.json')})
  print(json.dumps(report,indent=2,ensure_ascii=False))
 except Exception as e:m.update(state='failed',finished_at_utc=now(),error=repr(e));raise
 finally:(ROOT/OUT/'manifest.json').write_text(json.dumps(m,indent=2)+'\n')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','run']);a=p.parse_args();{'prepare':prepare,'run':run}[a.action]()
