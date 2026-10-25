"""Independent frozen-snapshot navigation reconstruction; no E86 imports."""
import hashlib,json,re
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit,parse_qs
from bs4 import BeautifulSoup,Tag
ROOT=Path(__file__).resolve().parents[1];OUT='runs/000086_listing_navigation/'
SIGNAL='blog-pager-older-link';HOST='forgottenlanguages-full.forgottenlanguages.org'
def read(p):return json.loads((ROOT/p).read_text())
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def reason(u):
 try:
  x=urlsplit(u)
  if not(x.scheme=='https' and x.hostname==HOST and x.port is None and x.username is None and x.password is None and not x.fragment and x.path=='/search/label/Kamri'):return 'not_strict_native_listing'
  values=parse_qs(x.query,keep_blank_values=True,strict_parsing=True)
  if not values or any(k not in ('updated-max','max-results','start','by-date') or len(v)!=1 or v==[''] for k,v in values.items()):return 'unsupported_or_duplicate_query'
  q={k:v[0] for k,v in values.items()}
  decimal=lambda s:bool(s) and s.isascii() and s.isdecimal()
  if 'start' in q and not decimal(q['start']):return 'invalid_start'
  if 'max-results' in q and (not decimal(q['max-results']) or int(q['max-results'])<1 or int(q['max-results'])>100):return 'invalid_page_size'
  if 'by-date' in q and q['by-date'] not in ['false','true']:return 'invalid_by_date'
  if 'updated-max' in q:
   t=datetime.fromisoformat(q['updated-max'].replace('Z','+00:00'))
   if t.tzinfo is None or t.utcoffset() is None:return 'invalid_time_cursor'
  elif int(q.get('start','0'))==0:return 'missing_forward_cursor'
  return None
 except (ValueError,TypeError,OverflowError):return 'malformed_url_or_cursor'
def main():
 reg=read('experiments/listing_navigation_v86.json');m=read(OUT+'manifest.json')
 assert m['state']=='complete' and reg['registered_at_utc']<m['started_at_utc']<m['finished_at_utc']
 assert m['input_hashes']==reg['input_hashes']|{'experiments/listing_navigation_v86.json':sha('experiments/listing_navigation_v86.json')}
 for p,h in (m['input_hashes']|m['output_hashes']).items():assert sha(p)==h,p
 for p,h in read('reports/000085_deliverable_seal.json')['deliverable_hashes'].items():assert sha(p)==h,p
 assert reg['html_path']==read('experiments/browser_listing_v85.json')['html_path']
 soup=BeautifulSoup((ROOT/reg['html_path']).read_bytes(),'html.parser');rows=[]
 tags=[t for t in soup.descendants if isinstance(t,Tag)]
 for index,t in enumerate(tags):
  if t.name not in ('a','link') or 'href' not in t.attrs:continue
  classes=t.get('class',[]);rels=t.get('rel',[]);ident=t.get('id')
  older=t.name=='a' and (ident==SIGNAL or SIGNAL in classes)
  inside=t.name=='a' and any(isinstance(a,Tag) and (a.get('id')=='blog-pager' or 'blog-pager' in a.get('class',[])) for a in t.parents)
  channels=[]
  if inside:channels.append('pager_anchor')
  if older:channels.append('explicit_older')
  if 'next' in rels:channels.append('rel_next')
  if not channels:continue
  why=reason(t['href'])
  rows.append({'tag_index':index,'tag_name':t.name,'id':ident,'classes':classes,'rel':rels,'href':t['href'],
               'label':t.get_text(' ',strip=True) if t.name=='a' else None,'channels':channels,'explicit_older':older,
               'route_reason':why,'route_eligible':why is None})
 older=[r for r in rows if r['explicit_older']];urls={r['href'] for r in older if r['route_eligible']}
 base=bool(soup.find_all('base',href=True));chosen=None
 if base:why='base_href'
 elif not older:why='no_explicit_older_link'
 elif not all(r['route_eligible'] for r in older):why='invalid_explicit_older_link'
 elif len(urls)!=1:why='ambiguous_older_routes'
 elif any('rel_next' in r['channels'] and r['route_eligible'] and r['href'] not in urls for r in rows):why='conflicting_rel_next'
 else:why='one_bound_older_route';chosen=next(iter(urls))
 expected={'experiment_id':'listing_navigation_v86','inventory':rows,'base_href':base,'explicit_older_signals':len(older),
 'distinct_eligible_older_urls':len(urls),'selection_reason':why,'next_capture_url':chosen,'next_capture_targets':int(chosen is not None),
 'network_requests':0,'new_predictions':False,'new_post_captures':0,'confirmation_eligibility':'unresolved',
 'independent_groups_admitted':0,'untouched_units_admitted':0,'semantic_benchmark_qualifying_works':0}
 assert expected==read(OUT+'report.json') and reg['network_requests']==m['network_requests']==0
 print(json.dumps({'verified':True,'navigation_tags':len(rows),'explicit_older_signals':len(older),
                   'selection_reason':why,'next_capture_url':chosen,'network_requests':0,'new_predictions':False},indent=2))
if __name__=='__main__':main()
