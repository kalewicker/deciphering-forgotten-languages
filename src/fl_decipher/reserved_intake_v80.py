"""Metadata-only selection and bounded HTML transport checks."""
import re,unicodedata
from urllib.parse import urlsplit
from bs4 import BeautifulSoup
from fl_decipher.routing_v53 import header_blocks
HOST='forgottenlanguages-full.forgottenlanguages.org'
LABEL='https://'+HOST+'/search/label/Kamri'
CHALLENGES=('verify you are human','access denied','captcha','just a moment','enable javascript and cookies')
def key(url,strict=False):
 try:
  p=urlsplit(url)
  if p.hostname!=HOST or p.username or p.password or p.port is not None:return None
  if p.scheme not in (('https',) if strict else ('http','https')):return None
  if strict and (p.query or p.fragment):return None
  if not re.fullmatch(r'/\d{4}/\d{2}/[a-z0-9-]+\.html',p.path):return None
  return 'https://'+HOST+p.path
 except (ValueError,TypeError):return None
def title(s):return ' '.join(unicodedata.normalize('NFC',s).casefold().split())
def transport(raw,headers,receipt,url):
 blocks=header_blocks(headers)['responses'];media=lambda x:(x or '').split(';')[0].strip().lower()
 soup=BeautifulSoup(raw,'html.parser');text=soup.get_text(' ',strip=True).casefold()
 checks={'curl_exit_zero':receipt['curl_returncode']==0,'http_200':receipt['http_status']==200,
 'exact_url':receipt['final_url']==url,'zero_redirects':receipt['num_redirects']==0,
 'single_response':len(blocks)==1,'headers_consistent':len(blocks)==1 and blocks[0]['status']==200 and not blocks[0]['locations'],
 'html_media':media(receipt['content_type'])=='text/html' and len(blocks)==1 and bool(blocks[0]['content_types']) and all(media(v)=='text/html' for v in blocks[0]['content_types']),
 'body_size':0<len(raw)<=4194304,'no_challenge':not any(s in text for s in CHALLENGES)}
 return checks
def select(raw,known):
 soup=BeautifulSoup(raw,'html.parser');base=bool(soup.select('base[href]'));seen=set();rows=[];chosen=[]
 for i,a in enumerate(soup.select('.post-title a[href]')):
  url=a.get('href');name=a.get_text(' ',strip=True);k=key(url,True)
  reason='base_href' if base else 'invalid_url' if not k else 'empty_title' if not name else 'duplicate' if k in seen else 'previously_recorded' if k in known else 'over_cap' if len(chosen)>=4 else None
  row={'index':i,'url':url,'title':name,'key':k,'reason':reason};rows.append(row)
  if k:seen.add(k)
  if reason is None:chosen.append(row)
 return {'base_href':base,'candidates':rows,'selected':chosen}
def post_checks(raw,nominee):
 soup=BeautifulSoup(raw,'html.parser');url=nominee['url'];bodies=soup.select('.post-body');heads=soup.select('.post-title')
 canon=[x.get('href','') for x in soup.select('link[rel~=canonical]')]
 og=[x.get('content','') for x in soup.select('meta[property="og:url"]')]
 links=[x.get('href','') for x in soup.select('.post-title a[href]')]
 bookmarks=[x.get('href','') for x in soup.select('a[rel~=bookmark]')]
 return {'one_nonempty_body':len(bodies)==1 and bool(bodies[0].get_text(' ',strip=True)),
 'one_matching_title':len(heads)==1 and title(heads[0].get_text(' ',strip=True))==title(nominee['title']),
 'kamri_label':any(a.get('href')==LABEL and a.get_text(' ',strip=True)=='Kamri' for a in soup.select('a[rel~=tag]')),
 'positive_identity':bool(canon and all(x==url for x in canon)) or links==[url] and bookmarks==[url],
 'no_identity_conflict':all(x==url for x in canon+og),'no_base_href':not bool(soup.select('base[href]'))}
