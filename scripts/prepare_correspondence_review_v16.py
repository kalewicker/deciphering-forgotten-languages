"""Freeze independent source passages and per-unit review before immutable execution."""
from pathlib import Path
import json
from fl_decipher.corpus import digest,dump_json
from fl_decipher.natural_v12 import utc
from fl_decipher.correspondence_review_v16 import extract_html,whole_statement_matches,ordered_nonoverlapping,gates,positional_hypotheses
from fl_decipher.dataset_audit_v15 import occurrences,words
from fl_decipher.text import tokens
ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text())
def main():
 n=read(ROOT/'data/v16/nominations.json');directory=ROOT/'data/v16/normalized';directory.mkdir(exist_ok=False)
 sources={};fls={};inputs=[]
 for p in n['passages']:
  g=p['component'];d=ROOT/'data/v16/acquisition'/f'{g}_source';receipt=read(d/'receipt.json')
  assert receipt['http_status']==200 and receipt['curl_returncode']==0
  raw=(d/'body.bin').read_bytes();doc=extract_html(raw,'article' if g=='nichiren_images' else '.com-content-article__body')
  title='Opening the Eyes of Wooden and Painted Images' if g=='nichiren_images' else 'The Dark Side of Light'
  assert title in doc['html_title']
  assert 'Nichiren' in doc['html_title'] if g=='nichiren_images' else 'John Algeo' in doc['full_body_text'] and '2005' in doc['full_body_text']
  doc|={'id':g+'_source_v16','kind':'source','source_group':g,'url':p['source_url'],'snapshot':receipt,
    'source_authority_reviewed':True,'authority_assessment':'Registered official publisher/library route, matching title and displayed attribution.','scope':'Complete registered HTML body/paragraph extraction; no assertion that every sentence is a complete edition of the work.'}
  dump_json(directory/f'{g}_source.json',doc);sources[g]=doc
  old=read(ROOT/p['source_historical_document']);inputs.append(ROOT/p['source_historical_document'])
  drift={'historical_document':p['source_historical_document'],'historical_text_sha256':digest(old['text'].encode()),'current_body_text_sha256':digest(doc['full_body_text'].encode()),'exact_body_text_same':doc['full_body_text']==old['text'],'ordered_word_body_same':words(doc['full_body_text'])==words(old['text']), 'interpretation':'Whole-body extraction differences are disclosed; per-selected-statement historical/current agreement is checked separately. No claim of textual edition change based on extraction drift alone.'}
  dump_json(ROOT/'data/v16'/f'{g}_source_drift.json',drift)
  fr=read(ROOT/'data/v16/acquisition'/f'{g}_fl'/'receipt.json');prior=read(ROOT/p['fl_historical_document']);inputs.append(ROOT/p['fl_historical_document']);inputs.append(ROOT/prior['snapshot']['artifact'])
  if fr['http_status']==200 and fr['curl_returncode']==0:
   fd=extract_html((ROOT/'data/v16/acquisition'/f'{g}_fl'/'body.bin').read_bytes(),'div.post-body');fd['current_raw_fl']=True;fd['snapshot']=fr
  else:
   fd={'text':prior['text'],'full_body_text':prior['text'],'blocks':[{'id':0,'text':prior['text'],'span':[0,len(prior['text'])]}],
    'current_raw_fl':False,'snapshot':prior['snapshot'],'failed_current_attempt':fr,
    'transformations':prior['transformations'],'scope':'Exact historical indexed excerpt; complete selected statements, not a complete raw FL post.'}
  fd|={'id':g+'_fl_v16','kind':'fl','source_group':g,'url':p['fl_url']}
  dump_json(directory/f'{g}_fl.json',fd);fls[g]=fd
 rows=[];passages=[]
 for p in n['passages']:
  g=p['component'];sd=sources[g];fd=fls[g];selected=[];all_e=[];all_f=[]
  old=read(ROOT/p['source_historical_document'])
  other=next(x for x in sources if x!=g)
  for u in p['units']:
   em=whole_statement_matches(u['english'],sd);fm=whole_statement_matches(u['fl'],fd);all_e.append(em);all_f.append(fm)
   original=em[0]['text'] if len(em)==1 else None
   complete_e=len(em)==1 and em[0]['complete_statement'];complete_f=len(fm)==1 and fm[0]['complete_statement']
   hyp=positional_hypotheses(u['fl'],original,fl_offset=fm[0]['span'][0],english_offset=em[0]['span'][0]) if original and len(fm)==1 else []
   r={'uid':u['uid'],'component':g,'proposed_fl':u['fl'],'proposed_english':u['english'],'original_source_statement':original,
    'english_statement_matches':em,'fl_statement_matches':fm,'historical_source_occurrences':{policy:occurrences(u['english'],old['text'],policy) for policy in ('exact','whitespace','ordered_words')},
    'wrong_source_component':other,'wrong_source_occurrences':{policy:occurrences(u['english'],sources[other]['text'],policy) for policy in ('exact','whitespace','ordered_words')},
    'counts':{'fl_whitespace':len(u['fl'].split()),'reading_english_whitespace':len(u['english'].split()),'original_english_whitespace':len(original.split()) if original else None,
      'fl_project_tokens':len(tokens(u['fl'])),'reading_english_project_tokens':len(tokens(u['english'])),'original_english_project_tokens':len(tokens(original)) if original else None},
    'equal_project_token_counts':original is not None and len(tokens(u['fl']))==len(tokens(original)),
    'independent_complete_statement_pair':bool(complete_e and complete_f),'current_raw_fl':fd['current_raw_fl'],
    'semantic_gold':False,'semantic_training_eligible':False,'untouched_test_eligible':False,'positional_hypotheses':hyp}
   rows.append(r);selected.append(r)
  order=ordered_nonoverlapping(all_e) and ordered_nonoverlapping(all_f)
  gate=gates(source_authority=sd['source_authority_reviewed'],english_statements_unique_complete=all(len(x)==1 and x[0]['complete_statement'] for x in all_e),
    fl_statements_unique_complete=all(len(x)==1 and x[0]['complete_statement'] for x in all_f),ordered_nonoverlapping=order,
    current_raw_fl=fd['current_raw_fl'],independent_semantic_review=False,component_novel=False)
  passages.append({'component':g,'entry':p['entry'],'unit_uids':[r['uid'] for r in selected],'ordered_nonoverlapping':order,'gate':gate,
    'review':'All four full statements reviewed in independent current publisher HTML and a historical indexed FL excerpt. This is previously exposed source-backed development correspondence, not raw-current FL provenance or independent word meanings.'})
 stats={'components':2,'passages':2,'units':len(rows),'independent_complete_statement_pairs':sum(r['independent_complete_statement_pair'] for r in rows),
  'equal_project_token_count_pairs':sum(r['equal_project_token_counts'] for r in rows),
  'equal_reading_whitespace_count_pairs':sum(r['counts']['fl_whitespace']==r['counts']['reading_english_whitespace'] for r in rows),
  'equal_original_whitespace_count_pairs':sum(r['counts']['fl_whitespace']==r['counts']['original_english_whitespace'] for r in rows),
  'unvalidated_positional_hypotheses':sum(len(r['positional_hypotheses']) for r in rows),
  'development_review_eligible_passages':sum(p['gate']['development_correspondence_review_eligible'] for p in passages),
  'current_raw_reference_eligible_passages':sum(p['gate']['current_raw_reference_eligible'] for p in passages),
  'semantic_training_eligible_units':0,'untouched_test_eligible_units':0,
  'wrong_source_exact_or_normalized_match_units':sum(any(r['wrong_source_occurrences'].values()) for r in rows)}
 assert [r['uid'] for r in rows]==['03:001','03:002','03:003','03:004','13:001','13:002','13:003','13:004']
 dump_json(ROOT/'data/v16/frozen_review.json',{'reviewed_at_utc':utc(),'reviewer':'single analyst; automated independent verifier to follow','stage':'development_correspondence_review',
  'model_executed':False,'lexicons_used':False,'registration_sha256':n['registration_sha256'],'stats':stats,'units':rows,'passages':passages,
  'network_assessment':'Two FL endpoints returned TLS protocol-version alerts (curl 35), not DNS failure or a socket permission denial. No evidence of sandbox-specific denial; no bypass, alternate route or retry. Registered historical indexed fallback used.',
  'acquisition_routes':4,'raw_requests':4,'semantic_gold':False,
  'limits':['v15-informed nomination and previous component exposure; no generalization estimate','Historical indexed FL evidence only; current raw FL post acquisition failed','Counts and ordered statements do not independently validate wordwise lexical meanings','Single-analyst correspondence review, no second semantic annotator','Wrong-source literal diagnostics are not classifier false-admission rates']})
 inputs+=list((ROOT/'data/v16').rglob('*'));inputs+=[ROOT/'experiments/kamri_correspondence_pilot_v16.md',ROOT/'data/v15/parsed_annotations.json',ROOT/'data/v15/quarantine/07-su-dackei-ni-lascdir.txt',ROOT/'runs/000015_kamri_dataset_audit/manifest.json',ROOT/'runs/000015_kamri_dataset_audit/unit_ledger.json',ROOT/'runs/000015_kamri_dataset_audit/split_readiness.json']
 inputs=sorted(set(p for p in inputs if p.is_file()))
 dump_json(ROOT/'benchmarks/kamri_correspondence_review_v16.json',{'experiment_id':'kamri_correspondence_review_v16','frozen_at_utc':utc(), 'unit_denominator':8,'passage_denominator':2,'component_denominator':2,'review':'data/v16/frozen_review.json','input_hashes':{str(p.relative_to(ROOT)):digest(p.read_bytes()) for p in inputs}})
 print(json.dumps(stats,indent=2))
if __name__=='__main__':main()
