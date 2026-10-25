"""Read-only verification of E96's failed acquisition; never fetch or compare."""
import json,hashlib,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads((ROOT/p).read_text())
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def main():
 reg=read('experiments/burton_wording_v96.json');intent=read('data/v96/acquisition/intent.json');receipt=read('data/v96/acquisition/receipt.json')
 for p,h in reg['input_hashes'].items():assert sha(p)==h,p
 assert reg['registered_at_utc']<=intent['started_at_utc']<=receipt['finished_at_utc']
 assert intent['script_sha256']==sha('scripts/burton_acquire_v96.py')
 assert intent['url']==read('data/v96/retrieval.json')['url']
 assert intent['max_gets']==1 and intent['redirects_allowed']==0
 assert receipt['status'] is None and receipt['headers']==[] and receipt['bytes']==0
 assert 'SSLCertVerificationError' in receipt['error'] and 'CERTIFICATE_VERIFY_FAILED' in receipt['error']
 assert (ROOT/'data/v96/acquisition/body.bin').read_bytes()==b'' and sha('data/v96/acquisition/body.bin')==receipt['sha256']
 t=read('data/v96/targets.json')
 with zipfile.ZipFile(ROOT/'data/v90/acquisition/hop_01/body.bin') as z:raw=z.read(t['member']);text=raw.decode('utf-8')
 assert hashlib.sha256(raw).hexdigest()==t['member_sha256'] and [x['package_ordinal'] for x in t['targets']]==list(range(2,24))
 for x in t['targets']:assert text[slice(*x['span'])]==x['text']
 report=read('runs/000096_burton_wording/report.json');assert report['target_denominator']==22 and report['wording_counts'] is None and report['comparison_executed'] is False and report['page_binding_executed'] is False
 m=read('runs/000096_burton_wording/manifest.json');assert m['state']=='complete_acquisition_failed'
 for p,h in m['artifact_hashes'].items():assert sha(p)==h,p
 print(json.dumps({'verified':True,'registered_targets':22,'attempts':1,'http_responses':0,'received_bytes':0,'page_binding_executed':False,'comparison_executed':False},indent=2))
if __name__=='__main__':main()
