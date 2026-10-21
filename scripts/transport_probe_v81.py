"""Four fixed header-only probes. No corpus retrieval or TLS bypass."""
import argparse,hashlib,json,os,ssl,subprocess,sys,urllib.request,urllib.error
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];REG='experiments/transport_probe_v81.json';DATA='data/v81';OUT='runs/000081_transport_probe'
TARGET='https://forgottenlanguages-full.forgottenlanguages.org/robots.txt'
UA='FL-Decipher/0.1 E81 bounded transport diagnostic'
PROXIES=('http_proxy','https_proxy','all_proxy','no_proxy','HTTP_PROXY','HTTPS_PROXY','ALL_PROXY','NO_PROXY')
CERTS=('SSL_CERT_FILE','SSL_CERT_DIR','CURL_CA_BUNDLE','REQUESTS_CA_BUNDLE')
def now():return datetime.now(timezone.utc).isoformat()
def read(p):return json.loads((ROOT/p).read_text())
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def write(p,x):
 p=ROOT/p;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as f:json.dump(x,f,indent=2);f.write('\n')
def environment():
 return {'python':sys.executable,'python_version':sys.version,'ssl':ssl.OPENSSL_VERSION,
 'curl_version':subprocess.check_output(['/usr/bin/curl','--version']).decode(),
 'proxy_vars':[k for k in PROXIES if k in os.environ],'proxy_schemes':sorted(urllib.request.getproxies()),
 'certificate_overrides':[k for k in CERTS if k in os.environ],
 'curl_binary_sha256':sha('/usr/bin/curl'),'python_binary_sha256':sha(sys.executable)}
class NoRedirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,req,fp,code,msg,headers,newurl):return None

def worker(url):
 context=ssl.create_default_context()
 assert context.check_hostname and context.verify_mode==ssl.CERT_REQUIRED
 opener=urllib.request.build_opener(NoRedirect(),urllib.request.HTTPSHandler(context=context))
 request=urllib.request.Request(url,method='HEAD',headers={'User-Agent':UA})
 try:
  try:response=opener.open(request,timeout=20)
  except urllib.error.HTTPError as e:response=e
  try:
   # Do not read the response body, including HTTP errors.
   result={'status':response.code,'url':response.geturl(),'headers':list(response.headers.raw_items()),
           'verification_enabled':True,'method':'HEAD','body_read':False}
  finally:response.close()
 except Exception as e:result={'status':None,'url':url,'error_type':type(e).__name__,'error':str(e),
                             'verification_enabled':True,'method':'HEAD','body_read':False}
 print(json.dumps(result))

def classify(client,url,returncode,timed_out,raw,headers=b''):
 result={'classification':'transport_unresolved','http_status':None,'metadata_valid':False}
 if timed_out or returncode!=0 or len(raw)>65536 or len(headers)>65536:return result
 try:obj=json.loads(raw)
 except (ValueError,TypeError):return result
 if not isinstance(obj,dict):return result
 if client=='curl':
  status=obj.get('http_code');final=obj.get('url_effective')
  okay=obj.get('num_redirects')==0 and obj.get('ssl_verify_result')==0
  lines=[line for line in headers.decode('iso-8859-1').splitlines() if line.startswith('HTTP/') and 'connection established' not in line.casefold()]
  codes=[int(line.split()[1]) for line in lines if len(line.split())>=2 and line.split()[1].isdigit()]
  okay=okay and bool(codes) and codes[-1]==status
 else:
  status=obj.get('status');final=obj.get('url')
  okay=obj.get('method')=='HEAD' and obj.get('body_read') is False and obj.get('verification_enabled') is True and isinstance(obj.get('headers'),list)
 valid=okay and type(status) is int and 100<=status<=599 and final==url
 if valid:result.update(classification='http_response_observed',http_status=status,metadata_valid=True)
 return result

def prepare():
 env=environment();assert not env['proxy_vars'] and not env['proxy_schemes'] and not env['certificate_overrides']
 seal='reports/000080_deliverable_seal.json'
 for p,h in read(seal)['deliverable_hashes'].items():assert sha(p)==h,p
 write(DATA+'/environment.json',env)
 paths=['experiments/transport_probe_v81.md','scripts/transport_probe_v81.py','scripts/verify_transport_probe_v81.py',
        'tests/test_transport_probe_v81.py',DATA+'/environment.json',seal]
 cells=[{'id':'control_curl','client':'curl','url':'https://example.com/'},
        {'id':'control_python','client':'python','url':'https://example.com/'},
        {'id':'target_curl','client':'curl','url':TARGET},{'id':'target_python','client':'python','url':TARGET}]
 write(REG,{'experiment_id':'transport_probe_v81','registered_at_utc':now(),'cells':cells,
            'maximum_attempts':4,'input_hashes':{p:sha(p) for p in paths}})
 print('Frozen four header-only attempts; no network calls yet.')

def run():
 reg=read(REG)
 for p,h in reg['input_hashes'].items():assert sha(p)==h,p
 assert environment()==read(DATA+'/environment.json'),'Environment changed; no probes launched'
 (ROOT/OUT).mkdir(exist_ok=False)
 m={'state':'running','experiment_id':'transport_probe_v81','started_at_utc':now(),
    'input_hashes':reg['input_hashes']|{REG:sha(REG)}};write(OUT+'/manifest.json',m)
 try:
  rows=[]
  for cell in reg['cells']:
   dest=ROOT/DATA/'probes'/cell['id'];dest.mkdir(parents=True,exist_ok=False)
   if cell['client']=='curl':
    cmd=['/usr/bin/curl','--disable','--silent','--show-error','--head','--proto','=https','--retry','0',
         '--connect-timeout','8','--max-time','20','--max-redirs','0','--user-agent',UA,
         '--output','/dev/null','--dump-header',str(dest/'headers.bin'),'--write-out','%{json}',cell['url']]
   else:cmd=[sys.executable,str(ROOT/'scripts/transport_probe_v81.py'),'worker','--url',cell['url']]
   intent={**cell,'started_at_utc':now(),'command':cmd,'outer_timeout_seconds':22}
   write(str((dest/'intent.json').relative_to(ROOT)),intent)
   timeout=False
   try:
    p=subprocess.run(cmd,capture_output=True,timeout=22);code=p.returncode;out=p.stdout;err=p.stderr
   except subprocess.TimeoutExpired as e:timeout=True;code=None;out=e.stdout or b'';err=e.stderr or b''
   (dest/'stdout.bin').write_bytes(out);(dest/'stderr.bin').write_bytes(err)
   headers=(dest/'headers.bin').read_bytes() if (dest/'headers.bin').exists() else b''
   outcome=classify(cell['client'],cell['url'],code,timeout,out,headers)
   receipt={**cell,'finished_at_utc':now(),'returncode':code,'timed_out':timeout,'outcome':outcome,
            'artifact_hashes':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in dest.iterdir() if p.is_file()}}
   write(str((dest/'receipt.json').relative_to(ROOT)),receipt)
   rows.append({**cell,'returncode':code,'timed_out':timeout,**outcome})
   print(json.dumps(rows[-1]),flush=True)
  report={'experiment_id':'transport_probe_v81','cells':rows,'attempts':4,
          'candidate_clients':[r['client'] for r in rows if r['id'].startswith('target_') and r['classification']=='http_response_observed'],
          'bodies_read':False,'e80_captures_unchanged':0,'new_predictions':False,'semantic_benchmark_qualifying_works':0}
  write(OUT+'/report.json',report)
  paths=[p for p in (ROOT/DATA).rglob('*') if p.is_file()]+[ROOT/OUT/'report.json']
  m.update(state='complete',finished_at_utc=now(),output_hashes={str(p.relative_to(ROOT)):sha(str(p.relative_to(ROOT))) for p in paths})
 except Exception as e:m.update(state='failed',finished_at_utc=now(),error=repr(e));raise
 finally:(ROOT/OUT/'manifest.json').write_text(json.dumps(m,indent=2)+'\n')
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('action',choices=['prepare','run','worker']);ap.add_argument('--url');a=ap.parse_args()
 if a.action=='worker':
  assert a.url in ['https://example.com/',TARGET];worker(a.url)
 else:{'prepare':prepare,'run':run}[a.action]()
