"""Static pager metadata only; never resolves/follows hrefs."""
from datetime import datetime
import re
from urllib.parse import urlsplit,parse_qsl
from bs4 import BeautifulSoup
HOST='forgottenlanguages-full.forgottenlanguages.org'
SIGNAL='blog-pager-older-link'

def route_reason(url):
 try:
  p=urlsplit(url)
  if p.scheme!='https' or p.hostname!=HOST or p.port is not None or p.username is not None or p.password is not None or p.fragment or p.path!='/search/label/Kamri':return 'not_strict_native_listing'
  pairs=parse_qsl(p.query,keep_blank_values=True,strict_parsing=True)
  if not pairs or any(not k or not v or k not in {'updated-max','max-results','start','by-date'} for k,v in pairs) or len({k for k,v in pairs})!=len(pairs):return 'unsupported_or_duplicate_query'
  q=dict(pairs)
  if 'start' in q and not re.fullmatch('[0-9]+',q['start']):return 'invalid_start'
  if 'max-results' in q and (not re.fullmatch('[0-9]+',q['max-results']) or not 1<=int(q['max-results'])<=100):return 'invalid_page_size'
  if 'by-date' in q and q['by-date'] not in ('true','false'):return 'invalid_by_date'
  if 'updated-max' in q:
   stamp=datetime.fromisoformat(q['updated-max'].replace('Z','+00:00'))
   if stamp.tzinfo is None or stamp.utcoffset() is None:return 'invalid_time_cursor'
  elif int(q.get('start','0'))<=0:return 'missing_forward_cursor'
  return None
 except (ValueError,TypeError,OverflowError):return 'malformed_url_or_cursor'

def inventory(raw):
 soup=BeautifulSoup(raw,'html.parser');rows=[]
 pager_ids={id(t) for t in soup.select('#blog-pager a[href],.blog-pager a[href]')}
 for i,tag in enumerate(soup.find_all(True)):
  if tag.name not in ('a','link') or not tag.has_attr('href'):continue
  classes=list(tag.get('class',[]));rels=list(tag.get('rel',[]));ident=tag.get('id')
  older=tag.name=='a' and (ident==SIGNAL or SIGNAL in classes)
  channels=[]
  if id(tag) in pager_ids:channels.append('pager_anchor')
  if older:channels.append('explicit_older')
  if 'next' in rels:channels.append('rel_next')
  if not channels:continue
  url=tag.get('href');reason=route_reason(url)
  rows.append({'tag_index':i,'tag_name':tag.name,'id':ident,'classes':classes,'rel':rels,'href':url,
               'label':tag.get_text(' ',strip=True) if tag.name=='a' else None,'channels':channels,
               'explicit_older':older,'route_reason':reason,'route_eligible':reason is None})
 older=[r for r in rows if r['explicit_older']];unique=sorted({r['href'] for r in older if r['route_eligible']})
 base=bool(soup.select('base[href]'));chosen=None
 if base:reason='base_href'
 elif not older:reason='no_explicit_older_link'
 elif any(not r['route_eligible'] for r in older):reason='invalid_explicit_older_link'
 elif len(unique)!=1:reason='ambiguous_older_routes'
 elif any('rel_next' in r['channels'] and r['route_eligible'] and r['href']!=unique[0] for r in rows):reason='conflicting_rel_next'
 else:reason='one_bound_older_route';chosen=unique[0]
 return {'inventory':rows,'base_href':base,'explicit_older_signals':len(older),'distinct_eligible_older_urls':len(unique),
         'selection_reason':reason,'next_capture_url':chosen,'next_capture_targets':int(chosen is not None),
         'network_requests':0,'new_predictions':False,'new_post_captures':0,'confirmation_eligibility':'unresolved',
         'independent_groups_admitted':0,'untouched_units_admitted':0,'semantic_benchmark_qualifying_works':0}
