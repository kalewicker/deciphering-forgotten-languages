"""One catalog-selected native HTML GET with default certificate verification."""
from pathlib import Path
import json,hashlib,datetime,subprocess
ROOT=Path(__file__).resolve().parents[1]
def main():
 out=ROOT/'data/v98/acquisition';out.mkdir(exist_ok=False)
 url='https://www.gutenberg.org/cache/epub/57208/pg57208-images.html'
 response=json.loads((ROOT/'data/v98/link_response.json').read_text())['result'];assert url in response
 intent={'url':url,'started_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
 (out/'intent.json').write_text(json.dumps(intent,indent=2)+'\n')
 args=['/usr/bin/curl','--silent','--show-error','--max-time','60','--connect-timeout','20','--max-filesize','8388608','--header','Accept-Encoding: identity','--dump-header',str(out/'headers.txt'),'--output',str(out/'body.bin'),'--write-out','%{http_code}',url]
 p=subprocess.run(args,capture_output=True)
 if not (out/'body.bin').exists():(out/'body.bin').write_bytes(b'')
 raw=(out/'body.bin').read_bytes()
 receipt={'finished_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'exit_code':p.returncode,'http_status':p.stdout.decode(),'stderr':p.stderr.decode(),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
 (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))
if __name__=='__main__':main()
