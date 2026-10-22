"""Independent two-request locator and item-inventory reconstruction."""
import hashlib,json,re
from pathlib import Path
from urllib.parse import urlencode
ROOT=Path(__file__).resolve().parents[1];DATA='data/v84/';OUT='runs/000084_warc_locator/'
FIELDS=['timestamp','original','statuscode','mimetype','digest','filename','offset','length']
def read(p):return json.loads((ROOT/p).read_text())
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def number(x,zero=False):
 if type(x) not in (int,str):return None
 if type(x) is str and not x.isascii():return None
 if type(x) is str and (not x or not x.isdigit()):return None
 try:n=int(x)
 except ValueError:return None
 return n if n>0 or zero and n==0 else None
def assess_locator(raw,record,src):
 out={'eligible':False,'reason':'schema_or_locator_unavailable','row':None,'offset':None,'length':None}
 try:x=json.loads(raw)
 except (ValueError,TypeError):return out
 if not (type(x) is list and len(x)==2 and x[0]==FIELDS and type(x[1]) is list and len(x[1])==8):return out
 row=dict(zip(FIELDS,x[1]));out['row']=row
 if [row[k] for k in FIELDS[:5]]!=[record[k] for k in FIELDS[:5]]:return out|{'reason':'capture_identity_mismatch'}
 if row['filename']!=src['reference'] and row['filename']!=src['file']:return out|{'reason':'filename_mismatch'}
 a=number(row['offset'],True) if type(row['offset']) is str else None;n=number(row['length']) if type(row['length']) is str else None
 if a is None or n is None or n>2**21:return out|{'reason':'offset_length_unavailable_or_over_budget'}
 return out|{'eligible':True,'reason':'exact_bounded_locator','offset':a,'length':n}
def assess_inventory(raw,src):
 out={'eligible':False,'reason':'item_or_file_metadata_unavailable','file_size':None}
 try:x=json.loads(raw)
 except (ValueError,TypeError):return out
 if type(x) is not dict or 'error' in x or type(x.get('metadata')) is not dict or x['metadata'].get('identifier')!=src['item'] or type(x.get('files')) is not list:return out
 matches=[v for v in x['files'] if type(v) is dict and v.get('name')==src['file']]
 if len(matches)!=1:return out|{'reason':'file_missing_or_ambiguous'}
 f=matches[0];size=number(f.get('size'))
 if size is None:return out|{'reason':'file_size_unavailable'}
 for obj,k in [(x,'is_dark'),(x,'is_restricted'),(x['metadata'],'access-restricted-item'),(f,'private')]:
  if k not in obj:continue
  v=obj[k]
  if not (v is False or type(v) is int and v==0 or type(v) is str and v in ('false','0')):return out|{'reason':'restricted_or_unknown_access_flags'}
 return out|{'eligible':True,'reason':'metadata_compatible_not_access_proven','file_size':size}
def capture(spec,last):
 base=ROOT/DATA/'acquisition'/spec['id'];i=json.loads((base/'intent.json').read_text());r=json.loads((base/'receipt.json').read_text())
 assert i['id']==r['id']==spec['id'] and i['url']==r['url']==spec['url']
 assert last<=i['started_at_utc']<r['finished_at_utc']
 cmd=['/usr/bin/curl','--disable','--silent','--show-error','--compressed','--proto','=https','--retry','0','--connect-timeout','8','--max-time','20','--max-redirs','0','--max-filesize','4194304','--user-agent','FL-Decipher/0.1 E84 bounded WARC locator metadata','--output',str(base/'body.bin'),'--dump-header',str(base/'headers.txt'),'--write-out','%{json}',spec['url']]
 assert i['command']==cmd
 assert {p.name for p in base.iterdir()}==set(r['artifacts'])|{'receipt.json'}
 for p,h in r['artifacts'].items():assert hashlib.sha256((base/p).read_bytes()).hexdigest()==h
 try:t=json.loads((base/'stdout.bin').read_bytes())
 except (ValueError,TypeError):t={}
 for a,b in [('http_status','http_code'),('final_url','url_effective'),('num_redirects','num_redirects'),('content_type','content_type')]:assert r[a]==t.get(b)
 raw=(base/'body.bin').read_bytes() if (base/'body.bin').exists() else b'';headers=(base/'headers.txt').read_bytes() if (base/'headers.txt').exists() else b''
 blocks=[];current=None
 for line in headers.decode('iso-8859-1').splitlines():
  if mat:=re.match(r'^HTTP/\S+\s+(\d+)\s*(.*)',line):
   current={'status':int(mat[1]),'locations':[]}
   if int(mat[1])>=200 and mat[2].strip().casefold()!='connection established':blocks.append(current)
  elif current is not None and ':' in line:
   k,v=line.split(':',1)
   if k.casefold()=='location':current['locations'].append(v.strip())
  elif not line:current=None
 checks={'curl_exit_zero':r['curl_returncode']==0,'http_200':r['http_status']==200,'exact_url':r['final_url']==spec['url'],'zero_redirects':r['num_redirects']==0,
 'single_response':len(blocks)==1,'headers_consistent':len(blocks)==1 and blocks[0]['status']==200 and not blocks[0]['locations'],'body_size':0<len(raw)<=4194304}
 return raw,checks,r['finished_at_utc']
def main():
 reg=read('experiments/warc_locator_v84.json');m=read(OUT+'manifest.json')
 assert m['state']=='complete' and reg['registered_at_utc']<m['started_at_utc']<m['finished_at_utc']
 assert m['input_hashes']==reg['input_hashes']|{'experiments/warc_locator_v84.json':sha('experiments/warc_locator_v84.json')}
 for p,h in (m['input_hashes']|m['output_hashes']).items():assert sha(p)==h,p
 for p,h in read('reports/000083_deliverable_seal.json')['deliverable_hashes'].items():assert sha(p)==h,p
 hdr=(ROOT/'data/v82/acquisition/label_replay/headers.txt').read_bytes().decode('iso-8859-1')
 values=[line.split(':',1)[1].strip() for line in hdr.splitlines() if line.lower().startswith('x-archive-src:')]
 assert len(values)==1;parts=values[0].split('/')
 assert len(parts)==2 and all(re.fullmatch('[A-Za-z0-9_.-]+',s) and s not in ('.','..') for s in parts) and parts[1].endswith('.warc.gz')
 src={'item':parts[0],'file':parts[1],'reference':values[0]};assert reg['source']==src
 record=read('data/v82/label_index.json')['selection']['record'];assert reg['record']==record
 query='https://web.archive.org/cdx/search/cdx?'+urlencode([('url',record['original']),('matchType','exact'),('from',record['timestamp']),('to',record['timestamp']),('output','json'),('fl',','.join(FIELDS)),('limit','1')])
 specs=[{'id':'locator','url':query},{'id':'item','url':'https://archive.org/metadata/'+parts[0]}]
 assert reg['requests']==specs and reg['maximum_attempts']==2
 assert {p.name for p in (ROOT/DATA/'acquisition').iterdir()}=={'locator','item'}
 values=[];last=m['started_at_utc']
 for spec in specs:
  raw,checks,last=capture(spec,last)
  value=assess_locator(raw,record,src) if spec['id']=='locator' else assess_inventory(raw,src)
  if not all(checks.values()):value=value|{'eligible':False,'reason':'transport_failed'}
  values.append({'checks':checks,'assessment':value})
 assert last<=m['finished_at_utc'];loc,inv=[x['assessment'] for x in values]
 ready=bool(loc['eligible'] and inv['eligible'] and loc['offset']+loc['length']<=inv['file_size'])
 decision={'bounded_record_feasible':ready,'download_url':'https://archive.org/download/'+src['reference'] if ready else None,
 'range':f"bytes={loc['offset']}-{loc['offset']+loc['length']-1}" if ready else None,'download_attempted':False,'payload_identity_established':False}
 expected={'experiment_id':'warc_locator_v84','source':src,'locator':values[0],'item':values[1],'decision':decision,'attempts':2,
 'e82_gate_value':False,'new_predictions':False,'confirmation_eligibility':'unresolved','semantic_benchmark_qualifying_works':0}
 assert expected==read(OUT+'report.json')
 print(json.dumps({'verified':True,'attempts':2,'bounded_record_feasible':ready,'WARC_download_attempted':False,
 'locator_reason':loc['reason'],'item_reason':inv['reason'],'e82_gate_value':False},indent=2))
if __name__=='__main__':main()
