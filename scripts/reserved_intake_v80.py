"""One native-label intake; selected prose stays unscored and undisplayed."""
import argparse,hashlib,json,re,subprocess
from datetime import datetime,timezone
from pathlib import Path
from bs4 import BeautifulSoup
from fl_decipher.reserved_intake_v80 import key,LABEL,transport,select,post_checks
ROOT=Path(__file__).resolve().parents[1];REG='experiments/reserved_intake_v80.json';OUT='runs/000080_reserved_intake';DATA='data/v80'
CODE=['experiments/reserved_intake_v80.md','src/fl_decipher/reserved_intake_v80.py','scripts/reserved_intake_v80.py',
      'scripts/verify_reserved_intake_v80.py','tests/test_reserved_intake_v80.py','src/fl_decipher/routing_v53.py']
EXTRA=['data/v15/parsed_annotations.json','data/v37/known_exposure.json','data/v37/nominations.json','data/v63_registration/known_exposure.json']
OBSERVED='data/v23/acquisition/western_esoterism_archive/body.bin'
def read(p):return json.loads((ROOT/p).read_text())
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def now():return datetime.now(timezone.utc).isoformat()
def write(p,x):
 path=ROOT/p;path.parent.mkdir(parents=True,exist_ok=True)
 with path.open('x') as f:json.dump(x,f,indent=2,ensure_ascii=False);f.write('\n')
def prepare():
 soup=BeautifulSoup((ROOT/OBSERVED).read_bytes(),'html.parser')
 assert any(a.get('href')==LABEL and a.get_text(' ',strip=True)=='Kamri' for a in soup.select('a[rel~=tag]'))
 tracked=subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode().split('\0')
 paths=sorted(set([p for p in tracked if Path(p).suffix in ('.md','.json','.py')]+EXTRA))
 sources={p:(ROOT/p).read_text(encoding='utf-8') for p in paths}
 write(DATA+'/exposure_sources.json',sources)
 found=set()
 for p in paths:
  for url in re.findall(r'https?://[^\s\"\'<>\\]+',sources[p]):
   k=key(url.rstrip(').,;]}`'))
   if k:found.add(k)
 exposure={'created_at_utc':now(),'known_article_keys':sorted(found),'input_hashes':{p:sha(p) for p in paths},
           'public_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip(),
           'scope':'public tracked UTF-8 md/json/py plus four fixed local inventories; incomplete exposure registry'}
 write(DATA+'/exposure.json',exposure)
 seal='reports/000079_deliverable_seal.json'
 for p,h in read(seal)['deliverable_hashes'].items():assert sha(p)==h,p
 frozen=CODE+[OBSERVED,seal,DATA+'/exposure.json',DATA+'/exposure_sources.json']
 write(REG,{'experiment_id':'reserved_intake_v80','registered_at_utc':now(),'label_url':LABEL,'post_slots':4,
 'maximum_requests':5,'timeout_seconds':20,'max_bytes':4194304,'redirects':0,'retries':0,
 'input_hashes':{p:sha(p) for p in frozen}})
 print(f'Frozen intake and {len(found)} recorded article keys; no requests yet.')
def capture(name,url):
 dest=ROOT/DATA/'acquisition'/name;dest.mkdir(parents=True,exist_ok=False)
 cmd=['curl','--disable','--silent','--show-error','--compressed','--proto','=https','--retry','0',
      '--connect-timeout','8','--max-time','20','--max-redirs','0','--max-filesize','4194304',
      '--user-agent','FL-Decipher/0.1 E80 bounded reserved-material intake',
      '--output',str(dest/'body.bin'),'--dump-header',str(dest/'headers.txt'),'--write-out','%{json}',url]
 write(str((dest/'intent.json').relative_to(ROOT)),{'requested_url':url,'started_at_utc':now(),'command':cmd})
 result=subprocess.run(cmd,capture_output=True)
 (dest/'curl_stdout.bin').write_bytes(result.stdout);(dest/'stderr.bin').write_bytes(result.stderr)
 try:telemetry=json.loads(result.stdout)
 except (ValueError,TypeError):telemetry={}
 receipt={'requested_url':url,'finished_at_utc':now(),'curl_returncode':result.returncode,
 'http_status':telemetry.get('http_code'),'final_url':telemetry.get('url_effective'),
 'num_redirects':telemetry.get('num_redirects'),'content_type':telemetry.get('content_type'),
 'artifacts':{p.name:{'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in dest.iterdir() if p.is_file()}}
 write(str((dest/'receipt.json').relative_to(ROOT)),receipt)
 raw=(dest/'body.bin').read_bytes() if (dest/'body.bin').exists() else b''
 headers=(dest/'headers.txt').read_bytes() if (dest/'headers.txt').exists() else b''
 return raw,transport(raw,headers,receipt,url)
def run():
 reg=read(REG)
 for p,h in reg['input_hashes'].items():assert sha(p)==h,p
 (ROOT/OUT).mkdir(exist_ok=False)
 m={'experiment_id':'reserved_intake_v80','state':'running','started_at_utc':now(),'input_hashes':reg['input_hashes']|{REG:sha(REG)}}
 write(OUT+'/manifest.json',m)
 try:
  raw,label_checks=capture('label',LABEL)
  selection=select(raw,set(read(DATA+'/exposure.json')['known_article_keys'])) if all(label_checks.values()) else {'base_href':None,'candidates':[],'selected':[]}
  write(DATA+'/selection.json',{'frozen_at_utc':now(),'label_checks':label_checks,**selection})
  slots=[]
  for i in range(4):
   if i>=len(selection['selected']):slots.append({'slot':i,'nominee':None,'status':'empty','checks':{},'raw_capture_pass':False});continue
   nominee=selection['selected'][i];body,checks=capture(f'post{i:02}',nominee['url'])
   checks={**checks,**post_checks(body,nominee)}
   slots.append({'slot':i,'nominee':nominee,'status':'captured' if all(checks.values()) else 'failed',
                 'checks':checks,'raw_capture_pass':all(checks.values())})
  report={'experiment_id':'reserved_intake_v80','label_checks':label_checks,'slots':slots,'slot_denominator':4,
   'requests':1+len(selection['selected']),'raw_captures_passed':sum(s['raw_capture_pass'] for s in slots),
   'raw_intake_capacity':all(s['raw_capture_pass'] for s in slots),'confirmation_eligibility':'unresolved',
   'new_predictions':False,'prose_displayed':False,'untouched_units_admitted':0,'semantic_benchmark_qualifying_works':0}
  write(OUT+'/report.json',report)
  allfiles=[p for p in (ROOT/DATA).rglob('*') if p.is_file()]+[ROOT/OUT/'report.json']
  m.update(state='complete',finished_at_utc=now(),output_hashes={str(p.relative_to(ROOT)):sha(str(p.relative_to(ROOT))) for p in sorted(allfiles)})
  print(json.dumps(report,indent=2))
 except Exception as e:m.update(state='failed',finished_at_utc=now(),error=repr(e));raise
 finally:(ROOT/OUT/'manifest.json').write_text(json.dumps(m,indent=2)+'\n')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','run']);a=p.parse_args();{'prepare':prepare,'run':run}[a.action]()
