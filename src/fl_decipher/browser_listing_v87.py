"""Chrome snapshot metadata only; does not render or inspect article prose."""
import re
from bs4 import BeautifulSoup
from fl_decipher.reserved_intake_v80 import select

def origin_metadata(raw,expected_url):
 # Only inspect saved-from comment syntax, native metadata, and title nodes.
 soup=BeautifulSoup(raw,'html.parser')
 text=raw.decode('utf-8',errors='replace')
 saved=[{'declared_length':int(m[1]),'url':m[2]} for m in re.finditer(r'<!--\s*saved from url=\((\d+)\)([^\s<>]+)\s*-->',text)]
 native=[{'channel':'canonical','url':x.get('href','')} for x in soup.select('link[rel~=canonical]')]
 native += [{'channel':'og_url','url':x.get('content','')} for x in soup.select('meta[property="og:url"]')]
 titles=[x.get_text(' ',strip=True) for x in soup.select('title')]
 checks={'one_kamri_title':len(titles)==1 and bool(re.search(r'\bKamri\b',titles[0])),
 'no_base_href':not bool(soup.select('base[href]')),
 'positive_origin_binding':len(saved)==1 and saved[0]['url']==expected_url or bool(native) and any(x['url']==expected_url for x in native),
 'no_origin_conflicts':all(x['url']==expected_url for x in saved+native)}
 return {'reported_url':expected_url,'saved_from':saved,'native_identity_fields':native,'html_titles':titles,'checks':checks,
         'metadata_use_allowed':all(checks.values())}

def assess(raw,known,expected_url):
 meta=origin_metadata(raw,expected_url)
 roster=select(raw,known) if meta['metadata_use_allowed'] else None
 slots=[]
 for i in range(4):
  nominee=roster['selected'][i] if roster is not None and i<len(roster['selected']) else None
  slots.append({'slot':i,'nominee':nominee,'filled':nominee is not None})
 return {'origin':meta,'candidate_inventory':roster,'slots':slots,'slot_denominator':4,
         'nomination_capacity':all(s['filled'] for s in slots),
         'representation':'browser_saved_snapshot_for_nomination_metadata' if meta['metadata_use_allowed'] else 'metadata_use_rejected',
         'new_post_captures':0,'confirmation_eligibility':'unresolved','new_predictions':False,
         'independent_groups_admitted':0,'untouched_units_admitted':0,'semantic_benchmark_qualifying_works':0}
