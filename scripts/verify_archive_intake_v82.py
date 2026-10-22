"""Archive accounting reconstructed without E82 acquisition/selection functions.

E80 candidate/post parsers and BeautifulSoup are shared historical dependencies.
"""
import base64,hashlib,json,re
from datetime import datetime
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import urlencode
from bs4 import BeautifulSoup
from fl_decipher.reserved_intake_v80 import select,post_checks
ROOT=Path(__file__).resolve().parents[1];DATA='data/v82/';OUT='runs/000082_archive_intake/'
LABEL='https://forgottenlanguages-full.forgottenlanguages.org/search/label/Kamri'
def read(p):return json.loads((ROOT/p).read_text())
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def cdx(url,cutoff):
 return 'https://web.archive.org/cdx/search/cdx?'+urlencode([('url',url),('matchType','exact'),('output','json'),('filter','statuscode:200'),('filter','mimetype:text/html'),('fl','timestamp,original,statuscode,mimetype,digest'),('limit','-1'),('to',cutoff)])
def choose(raw,url,cutoff):
 failed={'eligible':False,'record':None,'replay_url':None,'reason':'schema_or_record_failure'}
 try:
  x=json.loads(raw)
  if not (isinstance(x,list) and len(x)==2 and x[0]==['timestamp','original','statuscode','mimetype','digest'] and type(x[1]) is list and len(x[1])==5 and all(type(v) is str for v in x[1])):return failed
  t,u,s,m,d=x[1];datetime.strptime(t,'%Y%m%d%H%M%S')
  if not (re.fullmatch('[0-9]{14}',t) and t<=cutoff and u==url and s=='200' and m=='text/html' and re.fullmatch('[A-Z2-7]{32}',d)):return failed
 except (ValueError,TypeError):return failed
 return {'eligible':True,'record':dict(zip(x[0],x[1])),'replay_url':f'https://web.archive.org/web/{t}id_/{url}','reason':'one_exact_record'}

def verify_capture(name,url,replay,visited,timing):
 dest=ROOT/DATA/'acquisition'/name;r=json.loads((dest/'receipt.json').read_text());intent=json.loads((dest/'intent.json').read_text())
 assert intent['requested_url']==r['requested_url']==url and intent['is_replay']==replay
 assert timing[0]<=intent['started_at_utc']<r['finished_at_utc'];timing[0]=r['finished_at_utc']
 cmd=['/usr/bin/curl','--disable','--silent','--show-error','--compressed','--proto','=https','--retry','0','--connect-timeout','8','--max-time','20','--max-redirs','0','--max-filesize','4194304','--user-agent','FL-Decipher/0.1 E82 bounded archive intake','--output',str(dest/'body.bin'),'--dump-header',str(dest/'headers.txt'),'--write-out','%{json}',url]
 assert intent['command']==cmd;visited.add(name)
 assert {p.name for p in dest.iterdir()}==set(r['artifacts'])|{'receipt.json'}
 for p,h in r['artifacts'].items():assert hashlib.sha256((dest/p).read_bytes()).hexdigest()==h,p
 try:t=json.loads((dest/'stdout.bin').read_bytes())
 except (ValueError,TypeError):t={}
 for k,v in [('http_status','http_code'),('final_url','url_effective'),('num_redirects','num_redirects'),('content_type','content_type')]:assert r[k]==t.get(v)
 raw=(dest/'body.bin').read_bytes() if (dest/'body.bin').exists() else b'';headers=(dest/'headers.txt').read_bytes() if (dest/'headers.txt').exists() else b''
 blocks=[];cur=None
 for line in headers.decode('iso-8859-1').splitlines():
  if mat:=re.match(r'^HTTP/\S+\s+(\d+)\s*(.*)',line):
   cur={'status':int(mat[1]),'types':[],'locations':[]}
   if cur['status']>=200 and mat[2].strip().lower()!='connection established':blocks.append(cur)
  elif cur is not None and ':' in line:
   k,v=line.split(':',1)
   if k.lower()=='location':cur['locations'].append(v.strip())
   if k.lower()=='content-type':cur['types'].append(v.strip())
  elif not line:cur=None
 media=lambda x:(x or '').split(';')[0].strip().lower()
 checks={'curl_exit_zero':r['curl_returncode']==0,'http_200':r['http_status']==200,'exact_url':r['final_url']==url,'zero_redirects':r['num_redirects']==0,
 'single_response':len(blocks)==1,'headers_consistent':len(blocks)==1 and blocks[0]['status']==200 and not blocks[0]['locations'],'body_size':0<len(raw)<=4194304}
 if replay:
  checks['html_media']=media(r['content_type'])=='text/html' and len(blocks)==1 and bool(blocks[0]['types']) and all(media(v)=='text/html' for v in blocks[0]['types'])
  text=BeautifulSoup(raw,'html.parser').get_text(' ',strip=True).casefold()
  checks['no_challenge']=not any(s in text for s in ['verify you are human','access denied','captcha','just a moment','enable javascript and cookies'])
 return raw,headers,checks

def replay_binding(raw,headers,pick):
 vals=[line.split(':',1)[1].strip() for line in headers.decode('iso-8859-1').splitlines() if line.lower().startswith('memento-datetime:')]
 try:stamp=parsedate_to_datetime(vals[0]).strftime('%Y%m%d%H%M%S') if len(vals)==1 else None
 except (ValueError,TypeError,OverflowError):stamp=None
 return {'memento_matches_cdx':stamp==pick['record']['timestamp'],
 'body_digest_matches_cdx':base64.b32encode(hashlib.sha1(raw).digest()).decode().rstrip('=')==pick['record']['digest']}

def main():
 reg=read('experiments/archive_intake_v82.json');m=read(OUT+'manifest.json');cutoff=reg['archive_cutoff']
 assert m['state']=='complete' and reg['registered_at_utc']<m['started_at_utc']<m['finished_at_utc']
 assert m['input_hashes']==reg['input_hashes']|{'experiments/archive_intake_v82.json':sha('experiments/archive_intake_v82.json')}
 for p,h in (m['input_hashes']|m['output_hashes']).items():assert sha(p)==h,p
 for p,h in read('reports/000081_deliverable_seal.json')['deliverable_hashes'].items():assert sha(p)==h,p
 assert reg['label_url']==LABEL and reg['label_cdx_url']==cdx(LABEL,cutoff) and reg['maximum_attempts']==10 and reg['post_slots']==4
 visited=set();timing=[m['started_at_utc']]
 raw,_,checks=verify_capture('label_index',reg['label_cdx_url'],False,visited,timing)
 pick=choose(raw,LABEL,cutoff) if all(checks.values()) else {'eligible':False,'record':None,'replay_url':None,'reason':'index_transport_failed'}
 assert read(DATA+'label_index.json')=={'checks':checks,'selection':pick}
 noms={'base_href':None,'candidates':[],'selected':[]};rc=None
 if pick['eligible']:
  body,hdr,rc=verify_capture('label_replay',pick['replay_url'],True,visited,timing);rc.update(replay_binding(body,hdr,pick))
  soup=BeautifulSoup(body,'html.parser');titles=soup.find_all('title')
  urls=[x.get('href','') for x in soup.select('link[rel~=canonical]')]+[x.get('content','') for x in soup.select('meta[property="og:url"]')]
  rc.update({'one_kamri_title':len(titles)==1 and bool(re.search(r'\bKamri\b',titles[0].get_text())),'no_label_identity_conflict':all(u==LABEL for u in urls)})
  if all(rc.values()):noms=select(body,set(read('data/v80/exposure.json')['known_article_keys']))
 n=read(DATA+'nominations.json');assert n['frozen_at_utc']>=timing[0]
 assert {k:v for k,v in n.items() if k!='frozen_at_utc'}=={'label_replay_checks':rc,**noms}
 timing[0]=n['frozen_at_utc'];slots=[]
 for i in range(4):
  if i>=len(noms['selected']):slots.append({'slot':i,'nominee':None,'index':None,'replay_checks':None,'raw_capture_pass':False});continue
  nom=noms['selected'][i];url=nom['url'];raw,_,ic=verify_capture(f'post{i:02}_index',cdx(url,cutoff),False,visited,timing)
  ps=choose(raw,url,cutoff) if all(ic.values()) else {'eligible':False,'record':None,'replay_url':None,'reason':'index_transport_failed'}
  pc=None
  if ps['eligible']:
   body,hdr,pc=verify_capture(f'post{i:02}_replay',ps['replay_url'],True,visited,timing);pc.update(replay_binding(body,hdr,ps));pc.update(post_checks(body,nom))
  slots.append({'slot':i,'nominee':nom,'index':{'checks':ic,'selection':ps},'replay_checks':pc,'raw_capture_pass':pc is not None and all(pc.values())})
 assert timing[0]<=m['finished_at_utc'] and len(visited)<=10
 assert visited=={p.name for p in (ROOT/DATA/'acquisition').iterdir()}
 expected={'experiment_id':'archive_intake_v82','label_index':{'checks':checks,'selection':pick},'label_replay_checks':rc,'slots':slots,'slot_denominator':4,'attempts':len(visited),
 'raw_captures_passed':sum(s['raw_capture_pass'] for s in slots),'raw_intake_capacity':all(s['raw_capture_pass'] for s in slots),'confirmation_eligibility':'unresolved',
 'new_predictions':False,'prose_displayed':False,'untouched_units_admitted':0,'semantic_benchmark_qualifying_works':0}
 assert expected==read(OUT+'report.json')
 print(json.dumps({'verified':True,'attempts':len(visited),'slots':4,'raw_captures_passed':expected['raw_captures_passed'],
 'raw_intake_capacity':expected['raw_intake_capacity'],'confirmation_eligibility':'unresolved','shared_E80_metadata_parsers':True},indent=2))
if __name__=='__main__':main()
