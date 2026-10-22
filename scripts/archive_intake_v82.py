"""One bounded archive-label/post batch, all outputs unscored."""
import argparse,hashlib,json,subprocess
from datetime import datetime,timezone
from pathlib import Path
from fl_decipher.archive_intake_v82 import cdx_url,selection,archive_checks,label_checks
from fl_decipher.reserved_intake_v80 import LABEL,transport,select,post_checks
ROOT=Path(__file__).resolve().parents[1];REG='experiments/archive_intake_v82.json';DATA='data/v82';OUT='runs/000082_archive_intake'
CODE=['experiments/archive_intake_v82.md','src/fl_decipher/archive_intake_v82.py','scripts/archive_intake_v82.py',
 'scripts/verify_archive_intake_v82.py','tests/test_archive_intake_v82.py',
 'src/fl_decipher/reserved_intake_v80.py','src/fl_decipher/routing_v53.py']
def read(p):return json.loads((ROOT/p).read_text())
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def now():return datetime.now(timezone.utc).isoformat()
def write(p,x):
 path=ROOT/p;path.parent.mkdir(parents=True,exist_ok=True)
 with path.open('x') as f:json.dump(x,f,indent=2,ensure_ascii=False);f.write('\n')
def prepare():
 seal='reports/000081_deliverable_seal.json'
 for p,h in read(seal)['deliverable_hashes'].items():assert sha(p)==h,p
 cutoff=datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')
 paths=CODE+[seal,'data/v80/exposure.json','data/v23/acquisition/western_esoterism_archive/body.bin']
 write(REG,{'experiment_id':'archive_intake_v82','registered_at_utc':now(),'archive_cutoff':cutoff,
            'label_url':LABEL,'label_cdx_url':cdx_url(LABEL,cutoff),'maximum_attempts':10,'post_slots':4,
            'input_hashes':{p:sha(p) for p in paths}})
 print('Frozen one archive batch; no requests or candidate scoring yet.')
def acquire(name,url,is_replay):
 dest=ROOT/DATA/'acquisition'/name;dest.mkdir(parents=True,exist_ok=False)
 cmd=['/usr/bin/curl','--disable','--silent','--show-error','--compressed','--proto','=https','--retry','0',
 '--connect-timeout','8','--max-time','20','--max-redirs','0','--max-filesize','4194304',
 '--user-agent','FL-Decipher/0.1 E82 bounded archive intake','--output',str(dest/'body.bin'),
 '--dump-header',str(dest/'headers.txt'),'--write-out','%{json}',url]
 write(str((dest/'intent.json').relative_to(ROOT)),{'requested_url':url,'started_at_utc':now(),'command':cmd,'is_replay':is_replay})
 result=subprocess.run(cmd,capture_output=True)
 (dest/'stdout.bin').write_bytes(result.stdout);(dest/'stderr.bin').write_bytes(result.stderr)
 try:t=json.loads(result.stdout)
 except (ValueError,TypeError):t={}
 r={'requested_url':url,'finished_at_utc':now(),'curl_returncode':result.returncode,'http_status':t.get('http_code'),
    'final_url':t.get('url_effective'),'num_redirects':t.get('num_redirects'),'content_type':t.get('content_type'),
    'artifacts':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in dest.iterdir() if p.is_file()}}
 write(str((dest/'receipt.json').relative_to(ROOT)),r)
 raw=(dest/'body.bin').read_bytes() if (dest/'body.bin').exists() else b''
 headers=(dest/'headers.txt').read_bytes() if (dest/'headers.txt').exists() else b''
 checks=transport(raw,headers,r,url)
 if not is_replay:checks.pop('html_media');checks.pop('no_challenge')
 print(json.dumps({'attempt':name,'curl_exit':result.returncode,'http_status':r['http_status']}),flush=True)
 return raw,headers,checks

def run():
 reg=read(REG)
 for p,h in reg['input_hashes'].items():assert sha(p)==h,p
 (ROOT/OUT).mkdir(exist_ok=False)
 m={'state':'running','experiment_id':'archive_intake_v82','started_at_utc':now(),'input_hashes':reg['input_hashes']|{REG:sha(REG)}}
 write(OUT+'/manifest.json',m)
 try:
  cutoff=reg['archive_cutoff'];raw,_,checks=acquire('label_index',reg['label_cdx_url'],False)
  pick=selection(raw,LABEL,cutoff) if all(checks.values()) else {'eligible':False,'record':None,'replay_url':None,'reason':'index_transport_failed'}
  write(DATA+'/label_index.json',{'checks':checks,'selection':pick})
  nominations={'base_href':None,'candidates':[],'selected':[]};replay_checks=None
  if pick['eligible']:
   body,headers,replay_checks=acquire('label_replay',pick['replay_url'],True)
   replay_checks.update(archive_checks(body,headers,pick));replay_checks.update(label_checks(body))
   if all(replay_checks.values()):nominations=select(body,set(read('data/v80/exposure.json')['known_article_keys']))
  write(DATA+'/nominations.json',{'frozen_at_utc':now(),'label_replay_checks':replay_checks,**nominations})
  slots=[]
  for i in range(4):
   if i>=len(nominations['selected']):slots.append({'slot':i,'nominee':None,'index':None,'replay_checks':None,'raw_capture_pass':False});continue
   nom=nominations['selected'][i];url=nom['url'];cdx=cdx_url(url,cutoff)
   raw,_,ic=acquire(f'post{i:02}_index',cdx,False)
   ps=selection(raw,url,cutoff) if all(ic.values()) else {'eligible':False,'record':None,'replay_url':None,'reason':'index_transport_failed'}
   rc=None
   if ps['eligible']:
    body,headers,rc=acquire(f'post{i:02}_replay',ps['replay_url'],True)
    rc.update(archive_checks(body,headers,ps));rc.update(post_checks(body,nom))
   slots.append({'slot':i,'nominee':nom,'index':{'checks':ic,'selection':ps},'replay_checks':rc,'raw_capture_pass':rc is not None and all(rc.values())})
  attempts=len(list((ROOT/DATA/'acquisition').iterdir()));assert attempts<=10
  report={'experiment_id':'archive_intake_v82','label_index':{'checks':checks,'selection':pick},
          'label_replay_checks':replay_checks,'slots':slots,'slot_denominator':4,'attempts':attempts,
          'raw_captures_passed':sum(s['raw_capture_pass'] for s in slots),'raw_intake_capacity':all(s['raw_capture_pass'] for s in slots),
          'confirmation_eligibility':'unresolved','new_predictions':False,'prose_displayed':False,
          'untouched_units_admitted':0,'semantic_benchmark_qualifying_works':0}
  write(OUT+'/report.json',report)
  files=[p for p in (ROOT/DATA).rglob('*') if p.is_file()]+[ROOT/OUT/'report.json']
  m.update(state='complete',finished_at_utc=now(),output_hashes={str(p.relative_to(ROOT)):sha(str(p.relative_to(ROOT))) for p in files})
  print(json.dumps({k:report[k] for k in ['attempts','raw_captures_passed','raw_intake_capacity','confirmation_eligibility']},indent=2))
 except Exception as e:m.update(state='failed',finished_at_utc=now(),error=repr(e));raise
 finally:(ROOT/OUT/'manifest.json').write_text(json.dumps(m,indent=2)+'\n')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','run']);a=p.parse_args();{'prepare':prepare,'run':run}[a.action]()
