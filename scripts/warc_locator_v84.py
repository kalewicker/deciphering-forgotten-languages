"""Two exact public-metadata requests; no WARC download."""
import argparse,hashlib,json,subprocess
from datetime import datetime,timezone
from pathlib import Path
from fl_decipher.warc_locator_v84 import source,query,locator,inventory,decision
from fl_decipher.reserved_intake_v80 import transport
ROOT=Path(__file__).resolve().parents[1];REG='experiments/warc_locator_v84.json';DATA='data/v84';OUT='runs/000084_warc_locator'
CODE=['experiments/warc_locator_v84.md','src/fl_decipher/warc_locator_v84.py','scripts/warc_locator_v84.py',
 'scripts/verify_warc_locator_v84.py','tests/test_warc_locator_v84.py','src/fl_decipher/reserved_intake_v80.py','src/fl_decipher/routing_v53.py']
def read(p):return json.loads((ROOT/p).read_text())
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def now():return datetime.now(timezone.utc).isoformat()
def write(p,x):
 path=ROOT/p;path.parent.mkdir(parents=True,exist_ok=True)
 with path.open('x') as f:json.dump(x,f,indent=2);f.write('\n')
def prepare():
 seal='reports/000083_deliverable_seal.json'
 for p,h in read(seal)['deliverable_hashes'].items():assert sha(p)==h,p
 path='data/v82/acquisition/label_replay/headers.txt';src=source((ROOT/path).read_bytes())
 recpath='data/v82/label_index.json';record=read(recpath)['selection']['record']
 write(REG,{'experiment_id':'warc_locator_v84','registered_at_utc':now(),'source':src,'record':record,
 'requests':[{'id':'locator','url':query(record)},{'id':'item','url':'https://archive.org/metadata/'+src['item']}],
 'maximum_attempts':2,'input_hashes':{p:sha(p) for p in CODE+[seal,path,recpath]}})
 print('Frozen exact capture/item metadata pair; no requests yet.')
def acquire(spec):
 dest=ROOT/DATA/'acquisition'/spec['id'];dest.mkdir(parents=True,exist_ok=False);url=spec['url']
 cmd=['/usr/bin/curl','--disable','--silent','--show-error','--compressed','--proto','=https','--retry','0',
 '--connect-timeout','8','--max-time','20','--max-redirs','0','--max-filesize','4194304',
 '--user-agent','FL-Decipher/0.1 E84 bounded WARC locator metadata','--output',str(dest/'body.bin'),
 '--dump-header',str(dest/'headers.txt'),'--write-out','%{json}',url]
 write(str((dest/'intent.json').relative_to(ROOT)),{**spec,'started_at_utc':now(),'command':cmd})
 p=subprocess.run(cmd,capture_output=True);(dest/'stdout.bin').write_bytes(p.stdout);(dest/'stderr.bin').write_bytes(p.stderr)
 try:t=json.loads(p.stdout)
 except (ValueError,TypeError):t={}
 receipt={**spec,'finished_at_utc':now(),'curl_returncode':p.returncode,'http_status':t.get('http_code'),
 'final_url':t.get('url_effective'),'num_redirects':t.get('num_redirects'),'content_type':t.get('content_type'),
 'artifacts':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in dest.iterdir() if p.is_file()}}
 write(str((dest/'receipt.json').relative_to(ROOT)),receipt)
 raw=(dest/'body.bin').read_bytes() if (dest/'body.bin').exists() else b'';hdr=(dest/'headers.txt').read_bytes() if (dest/'headers.txt').exists() else b''
 checks=transport(raw,hdr,receipt,url);checks.pop('html_media');checks.pop('no_challenge')
 print(json.dumps({'attempt':spec['id'],'curl_exit':p.returncode,'http_status':receipt['http_status']}),flush=True)
 return raw,checks

def run():
 reg=read(REG)
 for p,h in reg['input_hashes'].items():assert sha(p)==h,p
 (ROOT/OUT).mkdir(exist_ok=False)
 m={'experiment_id':'warc_locator_v84','state':'running','started_at_utc':now(),'input_hashes':reg['input_hashes']|{REG:sha(REG)}}
 write(OUT+'/manifest.json',m)
 try:
  values=[]
  for spec in reg['requests']:
   raw,checks=acquire(spec)
   value=locator(raw,reg['record'],reg['source']) if spec['id']=='locator' else inventory(raw,reg['source'])
   if not all(checks.values()):value=value|{'eligible':False,'reason':'transport_failed'}
   values.append({'checks':checks,'assessment':value})
  result=decision(values[0]['assessment'],values[1]['assessment'],reg['source'])
  report={'experiment_id':'warc_locator_v84','source':reg['source'],'locator':values[0],'item':values[1],
          'decision':result,'attempts':2,'e82_gate_value':False,'new_predictions':False,
          'confirmation_eligibility':'unresolved','semantic_benchmark_qualifying_works':0}
  write(OUT+'/report.json',report)
  files=[p for p in (ROOT/DATA).rglob('*') if p.is_file()]+[ROOT/OUT/'report.json']
  m.update(state='complete',finished_at_utc=now(),output_hashes={str(p.relative_to(ROOT)):sha(str(p.relative_to(ROOT))) for p in files})
  print(json.dumps(report,indent=2))
 except Exception as e:m.update(state='failed',finished_at_utc=now(),error=repr(e));raise
 finally:(ROOT/OUT/'manifest.json').write_text(json.dumps(m,indent=2)+'\n')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','run']);a=p.parse_args();{'prepare':prepare,'run':run}[a.action]()
