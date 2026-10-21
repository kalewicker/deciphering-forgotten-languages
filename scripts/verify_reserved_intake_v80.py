"""Offline independent metadata/budget reconstruction; no production E80 imports."""
import hashlib,json,re,unicodedata
from pathlib import Path
from urllib.parse import urlsplit
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1];OUT='runs/000080_reserved_intake/';DATA='data/v80/'
HOST='forgottenlanguages-full.forgottenlanguages.org';LABEL='https://'+HOST+'/search/label/Kamri'
def read(p):return json.loads((ROOT/p).read_text())
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def norm(s):return ' '.join(unicodedata.normalize('NFC',s).casefold().split())
def urlkey(u,strict=False):
 try:
  x=urlsplit(u)
  ok=x.hostname==HOST and x.scheme in (['https'] if strict else ['http','https']) and x.port is None and x.username is None and x.password is None
  if strict:ok=ok and not x.query and not x.fragment
  return 'https://'+HOST+x.path if ok and re.fullmatch('/[0-9]{4}/[0-9]{2}/[a-z0-9-]+[.]html',x.path) else None
 except (TypeError,ValueError):return None
def captured(name,url):
 base=ROOT/DATA/'acquisition'/name;r=read(str((base/'receipt.json').relative_to(ROOT)));intent=read(str((base/'intent.json').relative_to(ROOT)))
 assert r['requested_url']==intent['requested_url']==url and intent['started_at_utc']<r['finished_at_utc']
 cmd=intent['command'];expected=['curl','--disable','--silent','--show-error','--compressed','--proto','=https','--retry','0',
 '--connect-timeout','8','--max-time','20','--max-redirs','0','--max-filesize','4194304',
 '--user-agent','FL-Decipher/0.1 E80 bounded reserved-material intake','--output',str(base/'body.bin'),
 '--dump-header',str(base/'headers.txt'),'--write-out','%{json}',url]
 assert cmd==expected
 assert {p.name for p in base.iterdir()}==set(r['artifacts'])|{'receipt.json'}
 for p,a in r['artifacts'].items():assert hashlib.sha256((base/p).read_bytes()).hexdigest()==a['sha256'] and (base/p).stat().st_size==a['bytes']
 try:t=json.loads((base/'curl_stdout.bin').read_bytes())
 except (ValueError,TypeError):t={}
 for field,key in [('http_status','http_code'),('final_url','url_effective'),('num_redirects','num_redirects'),('content_type','content_type')]:assert r[field]==t.get(key)
 raw=(base/'body.bin').read_bytes() if (base/'body.bin').exists() else b''
 headers=(base/'headers.txt').read_bytes() if (base/'headers.txt').exists() else b''
 blocks=[];current=None
 for line in headers.decode('iso-8859-1').splitlines():
  if line.startswith('HTTP/'):
   parts=line.split(' ',2);code=int(parts[1]);reason=parts[2].strip() if len(parts)>2 else ''
   current={'status':code,'location':[],'types':[]}
   if code>=200 and reason.lower()!='connection established':blocks.append(current)
  elif current is not None and ':' in line:
   k,v=line.split(':',1)
   if k.lower()=='location':current['location'].append(v.strip())
   if k.lower()=='content-type':current['types'].append(v.strip())
  elif not line:current=None
 media=lambda s:(s or '').split(';')[0].strip().lower()
 soup=BeautifulSoup(raw,'html.parser');txt=soup.get_text(' ',strip=True).casefold()
 checks={'curl_exit_zero':r['curl_returncode']==0,'http_200':r['http_status']==200,'exact_url':r['final_url']==url,
 'zero_redirects':r['num_redirects']==0,'single_response':len(blocks)==1,
 'headers_consistent':len(blocks)==1 and blocks[0]['status']==200 and not blocks[0]['location'],
 'html_media':media(r['content_type'])=='text/html' and len(blocks)==1 and bool(blocks[0]['types']) and all(media(v)=='text/html' for v in blocks[0]['types']),
 'body_size':0<len(raw)<=4194304,'no_challenge':not any(s in txt for s in ['verify you are human','access denied','captcha','just a moment','enable javascript and cookies'])}
 return soup,checks,intent,r

def main():
 reg=read('experiments/reserved_intake_v80.json');m=read(OUT+'manifest.json')
 assert m['state']=='complete' and reg['registered_at_utc']<m['started_at_utc']<m['finished_at_utc']
 assert m['input_hashes']==reg['input_hashes']|{'experiments/reserved_intake_v80.json':sha('experiments/reserved_intake_v80.json')}
 for p,h in (m['input_hashes']|m['output_hashes']).items():assert sha(p)==h,p
 for p,h in read('reports/000079_deliverable_seal.json')['deliverable_hashes'].items():assert sha(p)==h,p
 sources=read(DATA+'exposure_sources.json');exposure=read(DATA+'exposure.json');known=set()
 assert sources.keys()==exposure['input_hashes'].keys()
 for path,txt in sources.items():
  assert hashlib.sha256(txt.encode()).hexdigest()==exposure['input_hashes'][path]
  for u in re.findall(r'https?://[^\s\"\'<>\\]+',txt):
   k=urlkey(u.rstrip(').,;]}`'))
   if k:known.add(k)
 assert sorted(known)==exposure['known_article_keys']
 observed=BeautifulSoup((ROOT/'data/v23/acquisition/western_esoterism_archive/body.bin').read_bytes(),'html.parser')
 assert any(a.get('href')==LABEL and a.get_text(' ',strip=True)=='Kamri' for a in observed.select('a[rel~=tag]'))
 soup,checks,intent,receipt=captured('label',LABEL)
 assert m['started_at_utc']<=intent['started_at_utc']
 selection=read(DATA+'selection.json');assert receipt['finished_at_utc']<=selection['frozen_at_utc']
 chosen=[];candidates=[];seen=set();base=None
 if all(checks.values()):
  base=bool(soup.find_all('base',href=True))
  for i,a in enumerate(soup.select('.post-title a[href]')):
   u=a['href'];name=a.get_text(' ',strip=True);k=urlkey(u,True)
   reason='base_href' if base else 'invalid_url' if k is None else 'empty_title' if not name else 'duplicate' if k in seen else 'previously_recorded' if k in known else 'over_cap' if len(chosen)==4 else None
   row={'index':i,'url':u,'title':name,'key':k,'reason':reason};candidates.append(row)
   if k:seen.add(k)
   if reason is None:chosen.append(row)
 assert {k:v for k,v in selection.items() if k!='frozen_at_utc'}=={'label_checks':checks,'base_href':base,'candidates':candidates,'selected':chosen}
 slots=[]
 for i in range(4):
  if i>=len(chosen):slots.append({'slot':i,'nominee':None,'status':'empty','checks':{},'raw_capture_pass':False});continue
  nominee=chosen[i];s,c,start,end=captured(f'post{i:02}',nominee['url']);assert selection['frozen_at_utc']<start['started_at_utc'] and end['finished_at_utc']<=m['finished_at_utc']
  url=nominee['url'];b=s.select('.post-body');h=s.select('.post-title')
  canon=[t.get('href','') for t in s.select('link[rel~=canonical]')];og=[t.get('content','') for t in s.select('meta[property="og:url"]')]
  links=[a.get('href','') for a in s.select('.post-title a[href]')];bookmarks=[a.get('href','') for a in s.select('a[rel~=bookmark]')]
  c.update({'one_nonempty_body':len(b)==1 and bool(b[0].get_text(' ',strip=True)),
  'one_matching_title':len(h)==1 and norm(h[0].get_text(' ',strip=True))==norm(nominee['title']),
  'kamri_label':any(a.get('href')==LABEL and a.get_text(' ',strip=True)=='Kamri' for a in s.select('a[rel~=tag]')),
  'positive_identity':bool(canon and all(x==url for x in canon)) or links==[url] and bookmarks==[url],
  'no_identity_conflict':all(x==url for x in canon+og),'no_base_href':not bool(s.find_all('base',href=True))})
  slots.append({'slot':i,'nominee':nominee,'status':'captured' if all(c.values()) else 'failed','checks':c,'raw_capture_pass':all(c.values())})
 assert {p.name for p in (ROOT/DATA/'acquisition').iterdir()}=={'label'}|{f'post{i:02}' for i in range(len(chosen))}
 expected={'experiment_id':'reserved_intake_v80','label_checks':checks,'slots':slots,'slot_denominator':4,'requests':1+len(chosen),
 'raw_captures_passed':sum(s['raw_capture_pass'] for s in slots),'raw_intake_capacity':all(s['raw_capture_pass'] for s in slots),
 'confirmation_eligibility':'unresolved','new_predictions':False,'prose_displayed':False,'untouched_units_admitted':0,'semantic_benchmark_qualifying_works':0}
 assert expected==read(OUT+'report.json')
 print(json.dumps({'verified':True,'requests':1+len(chosen),'slots':4,'raw_captures_passed':expected['raw_captures_passed'],
 'raw_intake_capacity':expected['raw_intake_capacity'],'confirmation_eligibility':'unresolved'},indent=2))
if __name__=='__main__':main()
