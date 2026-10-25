"""Preserve supplied files, freeze protocol, inspect metadata once. No network."""
import argparse,hashlib,json,shutil
from datetime import datetime,timezone
from pathlib import Path
from fl_decipher.browser_listing_v85 import assess
ROOT=Path(__file__).resolve().parents[1];REG='experiments/browser_listing_v85.json';DATA='data/v85';OUT='runs/000085_browser_listing'
HTML=Path('/Users/kalewicker/Downloads/Forgotten Languages Full_ Kamri.html')
ASSETS=Path('/Users/kalewicker/Downloads/Forgotten Languages Full_ Kamri_files')
CODE=['experiments/browser_listing_v85.md','src/fl_decipher/browser_listing_v85.py','scripts/browser_listing_v85.py',
 'scripts/verify_browser_listing_v85.py','tests/test_browser_listing_v85.py','src/fl_decipher/reserved_intake_v80.py']
def read(p):return json.loads((ROOT/p).read_text())
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def now():return datetime.now(timezone.utc).isoformat()
def write(p,x):
 path=ROOT/p;path.parent.mkdir(parents=True,exist_ok=True)
 with path.open('x') as f:json.dump(x,f,indent=2,ensure_ascii=False);f.write('\n')
def preserve():
 assert HTML.is_file() and ASSETS.is_dir() and not HTML.is_symlink() and not ASSETS.is_symlink()
 all_nodes=[HTML,ASSETS,*ASSETS.rglob('*')]
 assert all(not p.is_symlink() and (p.is_file() or p.is_dir()) for p in all_nodes)
 sources=[p for p in all_nodes if p.is_file()]
 assert len(sources)<=256 and sum(p.stat().st_size for p in sources)<=32*1024*1024
 assert all(p.stat().st_size<=10*1024*1024 for p in sources)
 dest=ROOT/DATA/'snapshot';dest.mkdir(parents=True,exist_ok=False)
 # Preserve even empty companion subdirectories.
 for p in all_nodes:
  if p.is_dir():(dest/p.relative_to(HTML.parent)).mkdir(parents=True,exist_ok=True)
 rows=[]
 for p in sorted(sources):
  before=p.stat();relative=p.relative_to(HTML.parent);target=dest/relative
  target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
  src_hash=sha(p);assert src_hash==sha(target)
  after=p.stat();assert (before.st_size,before.st_mtime_ns)==(after.st_size,after.st_mtime_ns)
  rows.append({'source_path':str(p),'local_path':str(target.relative_to(ROOT)),'relative_path':str(relative),
               'bytes':after.st_size,'sha256':src_hash,'source_mtime_ns':after.st_mtime_ns})
 manifest={'imported_at_utc':now(),'source_html':str(HTML),'source_assets':str(ASSETS),'files':rows,
 'reported_url':'https://forgottenlanguages-full.forgottenlanguages.org/search/label/Kamri',
 'reported_save_time':'6:26 PST','reported_browser':'Chrome','normalized_capture_time_utc':None,
 'reported_capture_date':None,'reported_am_pm':None,'reported_final_url':None,
 'exact_save_method':None,'prior_exposure':'unknown','filesystem_times_are_capture_authentication':False}
 write(DATA+'/custody.json',manifest)
 print(f'Preserved {len(rows)} files and {sum(r["bytes"] for r in rows)} bytes without parsing HTML.')
def prepare():
 custody=read(DATA+'/custody.json')
 for f in custody['files']:
  assert sha(f['source_path'])==sha(f['local_path'])==f['sha256']
 seal='reports/000084_deliverable_seal.json'
 for p,h in read(seal)['deliverable_hashes'].items():assert sha(p)==h,p
 paths=CODE+[seal,DATA+'/custody.json','data/v80/exposure.json']+[f['local_path'] for f in custody['files']]
 write(REG,{'experiment_id':'browser_listing_v85','registered_at_utc':now(),
 'input_hashes':{p:sha(p) for p in paths},'custody_hash':sha(DATA+'/custody.json'),'network_requests':0,
 'html_path':DATA+'/snapshot/'+HTML.name,'nomination_slots':4,'prose_scoring':False})
 print('Frozen metadata intake before title/link parsing.')
def run():
 reg=read(REG)
 for p,h in reg['input_hashes'].items():assert sha(p)==h,p
 (ROOT/OUT).mkdir(exist_ok=False)
 m={'experiment_id':'browser_listing_v85','state':'running','started_at_utc':now(),
 'input_hashes':reg['input_hashes']|{REG:sha(REG)},'network_requests':0}
 write(OUT+'/manifest.json',m)
 try:
  report={'experiment_id':'browser_listing_v85',**assess((ROOT/reg['html_path']).read_bytes(),set(read('data/v80/exposure.json')['known_article_keys']))}
  write(OUT+'/report.json',report)
  m.update(state='complete',finished_at_utc=now(),output_hashes={OUT+'/report.json':sha(OUT+'/report.json')})
  print(json.dumps({'metadata_use_allowed':report['origin']['metadata_use_allowed'],'checks':report['origin']['checks'],
  'nomination_capacity':report['nomination_capacity'],'slots':report['slots'],'new_predictions':False},indent=2))
 except Exception as e:m.update(state='failed',finished_at_utc=now(),error=repr(e));raise
 finally:(ROOT/OUT/'manifest.json').write_text(json.dumps(m,indent=2)+'\n')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['preserve','prepare','run']);a=p.parse_args();{'preserve':preserve,'prepare':prepare,'run':run}[a.action]()
