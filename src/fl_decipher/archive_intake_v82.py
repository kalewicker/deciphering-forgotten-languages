"""Exact archive selection and digest binding; no opaque-text scoring."""
import base64,hashlib,json,re
from datetime import datetime
from email.utils import parsedate_to_datetime
from urllib.parse import urlencode
from bs4 import BeautifulSoup
from fl_decipher.reserved_intake_v80 import LABEL,CHALLENGES

def cdx_url(url,cutoff):
 return 'https://web.archive.org/cdx/search/cdx?'+urlencode([
 ('url',url),('matchType','exact'),('output','json'),('filter','statuscode:200'),
 ('filter','mimetype:text/html'),('fl','timestamp,original,statuscode,mimetype,digest'),('limit','-1'),('to',cutoff)])

def selection(raw,url,cutoff):
 result={'eligible':False,'record':None,'replay_url':None,'reason':'schema_or_record_failure'}
 try:
  value=json.loads(raw)
  assert type(value) is list and len(value)==2
  assert value[0]==['timestamp','original','statuscode','mimetype','digest']
  assert type(value[1]) is list and len(value[1])==5 and all(type(x) is str for x in value[1])
  r=dict(zip(value[0],value[1]));stamp=r['timestamp']
  assert re.fullmatch(r'\d{14}',stamp) and datetime.strptime(stamp,'%Y%m%d%H%M%S') and stamp<=cutoff
  assert r['original']==url and r['statuscode']=='200' and r['mimetype']=='text/html'
  assert re.fullmatch(r'[A-Z2-7]{32}',r['digest'])
 except (ValueError,TypeError,AssertionError):return result
 return {'eligible':True,'record':r,'replay_url':'https://web.archive.org/web/'+stamp+'id_/'+url,'reason':'one_exact_record'}

def archive_checks(raw,headers,pick):
 values=re.findall(r'^memento-datetime:\s*(.*?)\s*\r?$',headers.decode('iso-8859-1'),re.I|re.M)
 try:stamp=parsedate_to_datetime(values[0]).strftime('%Y%m%d%H%M%S') if len(values)==1 else None
 except (ValueError,TypeError,OverflowError):stamp=None
 digest=base64.b32encode(hashlib.sha1(raw).digest()).decode().rstrip('=')
 return {'memento_matches_cdx':stamp==pick['record']['timestamp'],
         'body_digest_matches_cdx':digest==pick['record']['digest']}

def label_checks(raw):
 soup=BeautifulSoup(raw,'html.parser');titles=soup.select('title')
 ids=[t.get('href','') for t in soup.select('link[rel~=canonical]')]+[t.get('content','') for t in soup.select('meta[property="og:url"]')]
 return {'one_kamri_title':len(titles)==1 and bool(re.search(r'\bKamri\b',titles[0].get_text())),
         'no_label_identity_conflict':all(u==LABEL for u in ids),
         'no_challenge':not any(s in soup.get_text(' ',strip=True).casefold() for s in CHALLENGES)}
