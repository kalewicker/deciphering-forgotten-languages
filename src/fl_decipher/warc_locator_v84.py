"""Exact metadata gates for a future bounded WARC-record retrieval."""
import json,re
from urllib.parse import urlencode
FIELDS=['timestamp','original','statuscode','mimetype','digest','filename','offset','length']
def source(headers):
 rows=re.findall(r'^x-archive-src:\s*([^\r\n]+)',headers.decode('iso-8859-1'),re.I|re.M)
 assert len(rows)==1
 parts=rows[0].strip().split('/')
 assert len(parts)==2 and all(re.fullmatch(r'[A-Za-z0-9_.-]+',p) and p not in ('.','..') for p in parts)
 assert parts[1].endswith('.warc.gz')
 return {'item':parts[0],'file':parts[1],'reference':'/'.join(parts)}
def query(record):
 return 'https://web.archive.org/cdx/search/cdx?'+urlencode([('url',record['original']),('matchType','exact'),
 ('from',record['timestamp']),('to',record['timestamp']),('output','json'),('fl',','.join(FIELDS)),('limit','1')])
def integer(x,zero=False):
 if type(x) is int:n=x
 elif type(x) is str and re.fullmatch('[0-9]+',x):n=int(x)
 else:return None
 return n if n>0 or zero and n==0 else None
def locator(raw,record,src):
 out={'eligible':False,'reason':'schema_or_locator_unavailable','row':None,'offset':None,'length':None}
 try:
  x=json.loads(raw)
  if not (type(x) is list and len(x)==2 and x[0]==FIELDS and type(x[1]) is list and len(x[1])==8):return out
  r=dict(zip(FIELDS,x[1]));out['row']=r
  if any(r[k]!=record[k] for k in FIELDS[:5]):return out|{'reason':'capture_identity_mismatch'}
  if r['filename'] not in (src['reference'],src['file']):return out|{'reason':'filename_mismatch'}
  a=integer(r['offset'],True) if type(r['offset']) is str else None
  n=integer(r['length']) if type(r['length']) is str else None
  if a is None or n is None or n>2097152:return out|{'reason':'offset_length_unavailable_or_over_budget'}
  return out|{'eligible':True,'reason':'exact_bounded_locator','offset':a,'length':n}
 except (ValueError,TypeError):return out
def unrestricted(value):
 return value is False or type(value) is int and value==0 or type(value) is str and value in ('false','0')
def inventory(raw,src):
 out={'eligible':False,'reason':'item_or_file_metadata_unavailable','file_size':None}
 try:
  x=json.loads(raw)
  if type(x) is not dict or 'error' in x or type(x.get('metadata')) is not dict or x['metadata'].get('identifier')!=src['item'] or type(x.get('files')) is not list:return out
  hits=[r for r in x['files'] if type(r) is dict and r.get('name')==src['file']]
  if len(hits)!=1:return out|{'reason':'file_missing_or_ambiguous'}
  f=hits[0];size=integer(f.get('size'))
  if size is None:return out|{'reason':'file_size_unavailable'}
  flags=[obj[k] for obj,k in [(x,'is_dark'),(x,'is_restricted'),(x['metadata'],'access-restricted-item'),(f,'private')] if k in obj]
  if not all(unrestricted(v) for v in flags):return out|{'reason':'restricted_or_unknown_access_flags'}
  return out|{'eligible':True,'reason':'metadata_compatible_not_access_proven','file_size':size}
 except (ValueError,TypeError):return out
def decision(loc,inv,src):
 ready=loc['eligible'] and inv['eligible'] and loc['offset']+loc['length']<=inv['file_size']
 return {'bounded_record_feasible':bool(ready),
 'download_url':'https://archive.org/download/'+src['reference'] if ready else None,
 'range':f"bytes={loc['offset']}-{loc['offset']+loc['length']-1}" if ready else None,
 'download_attempted':False,'payload_identity_established':False}
