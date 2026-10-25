"""Single fixed source GET; no redirects, retries or content matching."""
import json,hashlib,signal
from pathlib import Path
from datetime import datetime,timezone
from urllib.request import Request,build_opener,HTTPRedirectHandler
from urllib.error import HTTPError
ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads((ROOT/p).read_text())
def now():return datetime.now(timezone.utc).isoformat()
def write(p,x):
 with (ROOT/p).open('x') as f:json.dump(x,f,indent=2);f.write('\n')
class NoRedirect(HTTPRedirectHandler):
 def redirect_request(self,*args,**kwargs):return None
def main():
 for p,h in read('experiments/burton_wording_v96.json')['input_hashes'].items():assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h,p
 r=read('data/v96/retrieval.json');out=ROOT/'data/v96/acquisition';out.mkdir(exist_ok=False)
 write('data/v96/acquisition/intent.json',{'started_at_utc':now(),'url':r['url'],'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'max_bytes':r['max_bytes'],'max_gets':1,'redirects_allowed':0})
 receipt={'status':None,'headers':[],'error':None};body=bytearray()
 def timeout(*args):raise TimeoutError('overall 60 second deadline')
 signal.signal(signal.SIGALRM,timeout);signal.alarm(60)
 try:
  try:response=build_opener(NoRedirect()).open(Request(r['url'],headers={'User-Agent':'FL-Decipher/0.1 research','Accept-Encoding':'identity'}),timeout=30)
  except HTTPError as e:response=e
  with response:
   receipt.update(status=response.status,headers=list(response.headers.items()),returned_url=response.url)
   while len(body)<=r['max_bytes']:
    chunk=response.read(min(65536,r['max_bytes']+1-len(body)))
    if not chunk:break
    body.extend(chunk)
 except Exception as e:receipt['error']=repr(e)
 finally:
  signal.alarm(0)
  (out/'body.bin').write_bytes(body)
  receipt.update(finished_at_utc=now(),bytes=len(body),sha256=hashlib.sha256(body).hexdigest(),oversized=len(body)>r['max_bytes'])
  write('data/v96/acquisition/receipt.json',receipt)
 print(json.dumps({k:receipt[k] for k in ['status','bytes','error','oversized']},indent=2))
if __name__=='__main__':main()
