"""Read-only independent custody and metadata nomination reconstruction."""
import hashlib,json,re
from pathlib import Path
from urllib.parse import urlsplit
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1];OUT='runs/000087_browser_listing/';DATA='data/v87/'
LABEL='https://forgottenlanguages-full.forgottenlanguages.org/search/label/Kamri?updated-max=2022-11-30T07:37:00%2B01:00&max-results=20&start=1&by-date=false';HOST='forgottenlanguages-full.forgottenlanguages.org'
def read(p):return json.loads((ROOT/p).read_text())
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def strict_key(u):
 try:
  p=urlsplit(u)
  if p.scheme!='https' or p.hostname!=HOST or p.port is not None or p.username is not None or p.password is not None or p.query or p.fragment:return None
  if not re.fullmatch('/[0-9]{4}/[0-9]{2}/[a-z0-9-]+[.]html',p.path):return None
  return 'https://'+HOST+p.path
 except (ValueError,TypeError):return None
def main():
 reg=read('experiments/browser_listing_v87.json');m=read(OUT+'manifest.json');custody=read(DATA+'custody.json')
 assert m['state']=='complete' and custody['imported_at_utc']<reg['registered_at_utc']<m['started_at_utc']<m['finished_at_utc']
 assert m['input_hashes']==reg['input_hashes']|{'experiments/browser_listing_v87.json':sha('experiments/browser_listing_v87.json')}
 for p,h in (m['input_hashes']|m['output_hashes']).items():assert sha(p)==h,p
 for p,h in read('reports/000086_deliverable_seal.json')['deliverable_hashes'].items():assert sha(p)==h,p
 assert reg['custody_hash']==sha(DATA+'custody.json')
 assert reg['expected_url']==LABEL==read('runs/000086_listing_navigation/report.json')['next_capture_url']
 assert custody['reported_url']==LABEL and custody['reported_save_time']=='6:42 pm PST' and custody['reported_browser'] is None
 assert custody['normalized_capture_time_utc'] is None and custody['reported_capture_date'] is None and custody['reported_am_pm']=='pm'
 snapshot=ROOT/DATA/'snapshot';listed=set();source_available=0
 assert len(custody['files'])<=256 and sum(f['bytes'] for f in custody['files'])<=32*1024*1024
 for f in custody['files']:
  local=ROOT/f['local_path'];assert local.is_file() and not local.is_symlink() and local.is_relative_to(snapshot)
  assert str(local.relative_to(snapshot))==f['relative_path']
  assert sha(local)==f['sha256'] and local.stat().st_size==f['bytes']<=10*1024*1024
  source=Path(f['source_path'])
  if source.exists():
   assert source.is_file() and not source.is_symlink() and sha(source)==f['sha256'] and source.stat().st_size==f['bytes'];source_available+=1
  listed.add(local)
 assert listed=={p for p in snapshot.rglob('*') if p.is_file()}
 assert all(not p.is_symlink() for p in snapshot.rglob('*'))
 raw=(ROOT/reg['html_path']).read_bytes();soup=BeautifulSoup(raw,'html.parser')
 comments=re.findall(rb'<!--\s*saved from url=\(([0-9]+)\)([^\s<>]+)\s*-->',raw)
 saved=[{'declared_length':int(n),'url':u.decode('utf-8',errors='replace')} for n,u in comments]
 native=[{'channel':'canonical','url':x.get('href','')} for x in soup.select('link[rel~=canonical]')]+[{'channel':'og_url','url':x.get('content','')} for x in soup.select('meta[property="og:url"]')]
 titles=[t.get_text(' ',strip=True) for t in soup.select('title')]
 checks={'one_kamri_title':len(titles)==1 and bool(re.search(r'\bKamri\b',titles[0])),
 'no_base_href':not bool(soup.select('base[href]')),
 'positive_origin_binding':len(saved)==1 and saved[0]['url']==LABEL or bool(native) and any(x['url']==LABEL for x in native),
 'no_origin_conflicts':all(x['url']==LABEL for x in saved+native)}
 allowed=all(checks.values());meta={'reported_url':LABEL,'saved_from':saved,'native_identity_fields':native,'html_titles':titles,'checks':checks,'metadata_use_allowed':allowed}
 roster=None
 if allowed:
  known=set(read('data/v80/exposure.json')['known_article_keys']);seen=set();candidates=[];selected=[]
  for i,a in enumerate(soup.select('.post-title a[href]')):
   u=a.get('href');name=a.get_text(' ',strip=True);key=strict_key(u)
   reason='invalid_url' if key is None else 'empty_title' if not name else 'duplicate' if key in seen else 'previously_recorded' if key in known else 'over_cap' if len(selected)>=4 else None
   row={'index':i,'url':u,'title':name,'key':key,'reason':reason};candidates.append(row)
   if key:seen.add(key)
   if reason is None:selected.append(row)
  roster={'base_href':False,'candidates':candidates,'selected':selected}
 slots=[{'slot':i,'nominee':roster['selected'][i] if roster is not None and i<len(roster['selected']) else None,
         'filled':roster is not None and i<len(roster['selected'])} for i in range(4)]
 expected={'experiment_id':'browser_listing_v87','origin':meta,'candidate_inventory':roster,'slots':slots,'slot_denominator':4,
 'nomination_capacity':all(s['filled'] for s in slots),'representation':'browser_saved_snapshot_for_nomination_metadata' if allowed else 'metadata_use_rejected',
 'new_post_captures':0,'confirmation_eligibility':'unresolved','new_predictions':False,'independent_groups_admitted':0,'untouched_units_admitted':0,'semantic_benchmark_qualifying_works':0}
 assert expected==read(OUT+'report.json') and reg['network_requests']==m['network_requests']==0
 print(json.dumps({'verified':True,'preserved_files':len(listed),'source_files_available_and_matching':source_available,
 'missing_original_source_files':len(listed)-source_available,'metadata_use_allowed':allowed,'nomination_capacity':expected['nomination_capacity'],
 'candidate_title_links':len(roster['candidates']) if roster is not None else None,'network_requests':0,'new_predictions':False},indent=2))
if __name__=='__main__':main()
