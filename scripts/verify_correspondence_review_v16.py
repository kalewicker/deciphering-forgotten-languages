"""Independent DOM, sentence, token-offset, gate and archive-preservation audit."""
from pathlib import Path
import json,re,unicodedata
from bs4 import BeautifulSoup
from fl_decipher.corpus import digest,dump_json
from fl_decipher.natural_v12 import utc
from verify_correspondence_v6 import check_hashes
ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text())
def forms(t):return re.findall(r"\w+(?:['’]\w+)*",unicodedata.normalize('NFKC',t).casefold())
def normalized(t,p):return t if p=='exact' else ' '.join(t.split()) if p=='whitespace' else ' '.join(forms(t))
def offsets(a,b,p):
 n,h=normalized(a,p),normalized(b,p);out=[];i=0
 while n:
  i=h.find(n,i)
  if i<0:break
  j=i+len(n)
  if p!='ordered_words' or ((i==0 or h[i-1]==' ') and (j==len(h) or h[j]==' ')):out.append([i,j])
  i+=1
 return out

def independent_statements(d):
 results=[]
 for block in d['blocks']:
  start=0
  for end in re.finditer(r'[.!?]+[\"”’\']*(?=\s|$)',block['text']):
   raw=block['text'][start:end.end()];left=start+len(raw)-len(raw.lstrip());right=end.end();text=block['text'][left:right]
   if text:results.append({'text':text,'span':[block['span'][0]+left,block['span'][0]+right],'block_id':block['id']})
   start=end.end()
 return results

def main():
 out=ROOT/'runs/000016_kamri_correspondence_review';m=check_hashes(out);b=read(ROOT/'benchmarks/kamri_correspondence_review_v16.json');n=read(ROOT/'data/v16/nominations.json');review=read(ROOT/b['review']);r=read(out/'report.json');ledger=read(out/'unit_ledger.json')['units'];gates=read(out/'passage_gates.json')['passages'];a=read(ROOT/'data/v15/parsed_annotations.json')['articles']
 assert b['unit_denominator']==len(ledger)==8 and b['passage_denominator']==len(gates)==2 and b['component_denominator']==2
 assert n['registration_sha256']==review['registration_sha256']==digest((ROOT/n['registration']).read_bytes())
 assert review['reviewed_at_utc']<=b['frozen_at_utc']<=m['started_at_utc']<=m['finished_at_utc']
 assert ledger==review['units'] and gates==review['passages'] and r=={k:v for k,v in review.items() if k!='units'}
 docs={};source_raw_success=fl_raw_success=0
 for p in n['passages']:
  g=p['component'];assert p['units']==a[p['entry']-1]['units'][:4]
  assert g in ('nichiren_images','dark_side_light') and p['entry'] in (3,13)
  for side in ('fl','source'):
   receipt=read(ROOT/'data/v16/acquisition'/f'{g}_{side}'/'receipt.json')
   assert receipt['requested_url']==p[side+'_url'] and n['registered_at_utc']<receipt['started_at_utc']<=receipt['finished_at_utc']<=review['reviewed_at_utc']
   for artifact in receipt['artifacts'].values():assert digest(Path(artifact['path']).read_bytes())==artifact['sha256'] and Path(artifact['path']).stat().st_size==artifact['bytes']
   d=read(ROOT/'data/v16/normalized'/f'{g}_{side}.json');docs[g,side]=d
   if side=='source':
    assert receipt['http_status']==200 and receipt['curl_returncode']==0;source_raw_success+=1
    soup=BeautifulSoup((ROOT/'data/v16/acquisition'/f'{g}_source'/'body.bin').read_bytes(),'html.parser');body=soup.select_one('article' if g=='nichiren_images' else '.com-content-article__body')
    for node in body.select('script,style,noscript,sup,h1,h2,h3,h4'):node.decompose()
    ps=[x.get_text(' ',strip=True) for x in body.find_all('p') if x.get_text(' ',strip=True)]
    assert d['full_body_text']==body.get_text(' ',strip=True) and d['text']=='\n\n'.join(ps)
    assert len(ps)==len(d['blocks']) and d['source_authority_reviewed']
    cursor=0
    for idx,(text,block) in enumerate(zip(ps,d['blocks'],strict=True)):
     assert block=={'id':idx,'text':text,'span':[cursor,cursor+len(text)]};cursor+=len(text)+2
   else:
    assert receipt['http_status']==0 and receipt['curl_returncode']==35 and 'protocol version' in receipt['error']
    prior=read(ROOT/p['fl_historical_document']);assert d['text']==prior['text'] and d['snapshot']==prior['snapshot']
    assert d['snapshot']['acquisition_kind']=='indexed_web_excerpt' and not d['current_raw_fl']
    assert d['blocks']==[{'id':0,'text':prior['text'],'span':[0,len(prior['text'])]}]
  drift=read(ROOT/'data/v16'/f'{g}_source_drift.json');old=read(ROOT/p['source_historical_document'])
  assert drift['historical_text_sha256']==digest(old['text'].encode()) and drift['current_body_text_sha256']==digest(docs[g,'source']['full_body_text'].encode())
 assert source_raw_success==2 and fl_raw_success==0 and review['raw_requests']==review['acquisition_routes']==4
 counts=[];all_hyp=0
 for row in ledger:
  g=row['component'];p=next(x for x in n['passages'] if x['component']==g);u=next(x for x in p['units'] if x['uid']==row['uid'])
  assert row['proposed_fl']==u['fl'] and row['proposed_english']==u['english']
  for side,proposal,key in [('fl',u['fl'],'fl_statement_matches'),('source',u['english'],'english_statement_matches')]:
   d=docs[g,side];found=[s for s in independent_statements(d) if forms(s['text'])==forms(proposal)]
   assert len(found)==len(row[key])==1
   for s,h in zip(found,row[key],strict=True):
    assert all(h[k]==s[k] for k in ('text','span','block_id')) and h['complete_statement']
    assert d['text'][slice(*h['span'])]==h['text']
    policy='exact' if proposal==h['text'] else 'whitespace' if normalized(proposal,'whitespace')==normalized(h['text'],'whitespace') else 'ordered_words'
    assert h['policy']==policy
  en=row['english_statement_matches'][0];fl=row['fl_statement_matches'][0];assert row['original_source_statement']==en['text']
  c={'fl_whitespace':len(u['fl'].split()),'reading_english_whitespace':len(u['english'].split()),'original_english_whitespace':len(en['text'].split()),'fl_project_tokens':len(forms(u['fl'])),'reading_english_project_tokens':len(forms(u['english'])),'original_english_project_tokens':len(forms(en['text']))}
  assert row['counts']==c and row['equal_project_token_counts']==(c['fl_project_tokens']==c['original_english_project_tokens'])
  assert row['independent_complete_statement_pair'] and not row['current_raw_fl'] and not row['semantic_gold'] and not row['semantic_training_eligible'] and not row['untouched_test_eligible']
  other=next(x for x in n['passages'] if x['component']!=g);assert row['wrong_source_component']==other['component']
  for policy in ('exact','whitespace','ordered_words'):
   assert row['wrong_source_occurrences'][policy]==offsets(u['english'],docs[other['component'],'source']['text'],policy)
   assert row['historical_source_occurrences'][policy]==offsets(u['english'],read(ROOT/p['source_historical_document'])['text'],policy)
  fh,eh=0,0
  for idx,h in enumerate(row['positional_hypotheses']):
   assert h['index']==idx and 'unvalidated positional hypothesis' in h['status']
   fs,es=h['fl_span'],h['english_span'];ft=docs[g,'fl']['text'][slice(*fs)];et=docs[g,'source']['text'][slice(*es)]
   assert ft==h['fl_surface'] and et==h['english_surface'];assert ft.casefold().replace('’',"'")==h['fl_form'] and et.casefold().replace('’',"'")==h['english_form']
   assert fs[0]>=fl['span'][0] and fs[1]<=fl['span'][1] and es[0]>=en['span'][0] and es[1]<=en['span'][1]
   assert fs[0]>=fh and es[0]>=eh;fh=fs[1];eh=es[1]
  assert len(row['positional_hypotheses'])==c['fl_project_tokens'];all_hyp+=len(row['positional_hypotheses']);counts.append(c)
 for p in gates:
  selected=[x for x in ledger if x['component']==p['component']];assert len(selected)==4 and p['unit_uids']==[x['uid'] for x in selected]
  for key in ('fl_statement_matches','english_statement_matches'):
   spans=[x[key][0]['span'] for x in selected];assert all(a[1]<=b[0] for a,b in zip(spans,spans[1:]))
  req=p['gate']['requirements'];assert p['ordered_nonoverlapping'] and all(req[k] for k in ('source_authority','english_statements_unique_complete','fl_statements_unique_complete','ordered_nonoverlapping'))
  assert not req['current_raw_fl'] and not req['independent_semantic_review'] and not req['component_novel']
  assert p['gate']['development_correspondence_review_eligible'] and not any(p['gate'][k] for k in ('current_raw_reference_eligible','semantic_training_eligible','untouched_test_eligible'))
 stats=review['stats'];assert stats['units']==stats['equal_project_token_count_pairs']==stats['independent_complete_statement_pairs']==8
 assert stats['equal_reading_whitespace_count_pairs']==sum(c['fl_whitespace']==c['reading_english_whitespace'] for c in counts)==5
 assert stats['equal_original_whitespace_count_pairs']==sum(c['fl_whitespace']==c['original_english_whitespace'] for c in counts)==6
 assert stats['unvalidated_positional_hypotheses']==all_hyp==212 and stats['development_review_eligible_passages']==2
 assert stats['current_raw_reference_eligible_passages']==stats['semantic_training_eligible_units']==stats['untouched_test_eligible_units']==stats['wrong_source_exact_or_normalized_match_units']==0
 assert not m['model_executed'] and not review['model_executed'] and not review['lexicons_used'] and not review['semantic_gold']
 err=read(out/'proposed_annotation_errata.json');assert err==read(ROOT/'data/v16/proposed_annotation_errata.json')
 assert digest((ROOT/err['original_file']).read_bytes())==err['original_sha256'] and len(err['changes'])==3
 seven=a[6];assert all(x in seven['units'][14]['fl'] for x in ('daċkęį','kirglar','saċvęį'))
 assert err['changes'][0]['current_uid']=='07:015' and err['changes'][1]['current_uid']=='07:027' and 'priests who control several temples' in seven['units'][26]['english']
 assert err['changes'][2]['proposed_reference']=='S015' and not err['lexicons_used']
 assert not any((out/p).exists() for p in ['lexicon.json','predictions.json','scores.json','thresholds.json'])
 previous=[]
 for p in sorted((ROOT/'runs').glob('0000*')):
  if p==out:continue
  check_hashes(p);previous.append({'run_id':p.name,'manifest_sha256':digest((p/'manifest.json').read_bytes())})
 assert len(previous)==15
 receipt={'state':'verified','verified_at_utc':utc(),'run_id':out.name,'manifest_sha256':digest((out/'manifest.json').read_bytes()),'stats':stats,'previous_runs':previous,
  'checks':['Exact eight-unit selection and two components without success filtering','Four raw requests, timestamp order, current source DOM and historical FL fallback','Independent paragraph-local whole-statement boundaries, unique occurrences and ordered spans','All 212 positional-hypothesis offsets and forms; whitespace and Unicode token accounting','Development/raw/semantic/test gates remain distinct and fail closed','Three proposed locator corrections; original file bytes unchanged','Input/code/output hashes and fifteen historical archives preserved'],
  'limits':['Source authority and correspondence review are single-analyst inputs','Independent automated verifier is not an independent semantic annotator','Current raw FL provenance unavailable; no semantic gold or held-out result']}
 dump_json(ROOT/'reports/000016_verification.json',receipt);print(json.dumps({'state':'verified','units':8,'positional_hypotheses':212,'previous_runs':15},indent=2))
if __name__=='__main__':main()
