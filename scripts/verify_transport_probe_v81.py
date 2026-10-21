"""Read-only independent command/evidence check of the four infrastructure cells."""
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT='runs/000081_transport_probe/';DATA='data/v81/'
UA='FL-Decipher/0.1 E81 bounded transport diagnostic'
def read(p):return json.loads((ROOT/p).read_text())
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def main():
 reg=read('experiments/transport_probe_v81.json');m=read(OUT+'manifest.json');env=read(DATA+'environment.json')
 assert m['state']=='complete' and reg['registered_at_utc']<m['started_at_utc']<m['finished_at_utc']
 assert not env['proxy_vars'] and not env['proxy_schemes'] and not env['certificate_overrides']
 assert m['input_hashes']==reg['input_hashes']|{'experiments/transport_probe_v81.json':sha('experiments/transport_probe_v81.json')}
 for p,h in (m['input_hashes']|m['output_hashes']).items():assert sha(p)==h,p
 for p,h in read('reports/000080_deliverable_seal.json')['deliverable_hashes'].items():assert sha(p)==h,p
 expected_cells=[{'id':'control_curl','client':'curl','url':'https://example.com/'},
 {'id':'control_python','client':'python','url':'https://example.com/'},
 {'id':'target_curl','client':'curl','url':'https://forgottenlanguages-full.forgottenlanguages.org/robots.txt'},
 {'id':'target_python','client':'python','url':'https://forgottenlanguages-full.forgottenlanguages.org/robots.txt'}]
 assert reg['cells']==expected_cells and reg['maximum_attempts']==4
 assert {p.name for p in (ROOT/DATA/'probes').iterdir()}=={c['id'] for c in expected_cells}
 rows=[];last=m['started_at_utc']
 for cell in expected_cells:
  dest=ROOT/DATA/'probes'/cell['id'];intent=json.loads((dest/'intent.json').read_text());r=json.loads((dest/'receipt.json').read_text())
  assert last<=intent['started_at_utc']<r['finished_at_utc']<=m['finished_at_utc'];last=r['finished_at_utc']
  for key in cell:assert r[key]==intent[key]==cell[key]
  assert intent['outer_timeout_seconds']==22
  if cell['client']=='curl':
   cmd=['/usr/bin/curl','--disable','--silent','--show-error','--head','--proto','=https','--retry','0',
   '--connect-timeout','8','--max-time','20','--max-redirs','0','--user-agent',UA,'--output','/dev/null',
   '--dump-header',str(dest/'headers.bin'),'--write-out','%{json}',cell['url']]
  else:cmd=[env['python'],str(ROOT/'scripts/transport_probe_v81.py'),'worker','--url',cell['url']]
  assert intent['command']==cmd
  assert {p.name for p in dest.iterdir()}==set(r['artifact_hashes'])|{'receipt.json'}
  for p,h in r['artifact_hashes'].items():assert hashlib.sha256((dest/p).read_bytes()).hexdigest()==h,p
  raw=(dest/'stdout.bin').read_bytes();headers=(dest/'headers.bin').read_bytes() if (dest/'headers.bin').exists() else b''
  valid=False;status=None
  if not r['timed_out'] and r['returncode']==0 and len(raw)<=65536 and len(headers)<=65536:
   try:obj=json.loads(raw)
   except (ValueError,TypeError):obj=None
   if isinstance(obj,dict):
    if cell['client']=='python':
     status=obj.get('status');valid=(obj.get('url')==cell['url'] and obj.get('method')=='HEAD' and obj.get('body_read') is False and obj.get('verification_enabled') is True and isinstance(obj.get('headers'),list))
    else:
     status=obj.get('http_code')
     codes=[int(mat[1]) for line in headers.decode('iso-8859-1').splitlines() if 'connection established' not in line.lower() and (mat:=re.match(r'^HTTP/\S+\s+(\d+)\b',line))]
     valid=(obj.get('url_effective')==cell['url'] and obj.get('num_redirects')==0 and obj.get('ssl_verify_result')==0 and bool(codes) and codes[-1]==status)
    valid=bool(valid and type(status) is int and 100<=status<=599)
  outcome={'classification':'http_response_observed' if valid else 'transport_unresolved','http_status':status if valid else None,'metadata_valid':valid}
  assert outcome==r['outcome'];rows.append({**cell,'returncode':r['returncode'],'timed_out':r['timed_out'],**outcome})
 expected={'experiment_id':'transport_probe_v81','cells':rows,'attempts':4,
 'candidate_clients':[r['client'] for r in rows if r['id'].startswith('target_') and r['classification']=='http_response_observed'],
 'bodies_read':False,'e80_captures_unchanged':0,'new_predictions':False,'semantic_benchmark_qualifying_works':0}
 assert expected==read(OUT+'report.json')
 print(json.dumps({'verified':True,'attempts':4,'candidate_clients':expected['candidate_clients'],
 'http_responses':sum(r['metadata_valid'] for r in rows),'e80_preserved':True,'bodies_read':False},indent=2))
if __name__=='__main__':main()
