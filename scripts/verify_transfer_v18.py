"""Independent prediction, source-continuation, gate, counting and shuffle replay."""
from collections import Counter
from fractions import Fraction
from pathlib import Path
import json,re,random,unicodedata
from fl_decipher.corpus import digest,dump_json
from fl_decipher.natural_v12 import utc
from fl_decipher.text import tokens,sentences
from verify_correspondence_v6 import check_hashes
ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text())
def ratio(a,b):
 if not b:return None
 f=Fraction(a,b);return {'numerator':f.numerator,'denominator':f.denominator,'value':float(f)}
def words(t):return re.findall(r"\w+(?:['’]\w+)*",unicodedata.normalize('NFKC',t).casefold())
def source_statements(doc):
 out=[]
 for b in doc['blocks']:
  for s in sentences(b['text']):out.append({'text':s.text,'span':[b['span'][0]+s.start,b['span'][0]+s.end],'block_id':b['id'],'complete':bool(re.search(r'[.!?][\"”’\']*$',s.text))})
 return out

def score(ps,rs,orders=None):
 refs={r['uid']:r for r in rs};rows=[];units=[];tot={n:dict.fromkeys(['all_tokens','predictions','abstentions','evaluated_predictions','verified_positional_matches','positional_conflicts','unscoreable_predictions'],0) for n in ('primary','secondary')}
 for p in ps:
  ref=refs[p['uid']];eligible=ref['gate']['development_positional_score_eligible'];en=ref['source_tokens'];order=orders[p['uid']] if orders else list(range(len(en)))
  assert sorted(order)==list(range(len(en)))
  counts={n:dict.fromkeys(['predictions','abstentions','verified_positional_matches','positional_conflicts','unscoreable_predictions'],0) for n in tot}
  for t in p['tokens']:
   answer=en[order[t['index']]]['form'] if eligible else None
   row={'uid':t['uid'],'unit_uid':p['uid'],'component':p['component'],'index':t['index'],'fl_form':t['fl_form'],'fl_span':t['fl_span'],'reference_form':answer,'gate_eligible':eligible}
   for name in tot:
    value=t[name]['form'];s=tot[name];s['all_tokens']+=1
    if value is None:status='abstained';s['abstentions']+=1;counts[name]['abstentions']+=1
    else:
     s['predictions']+=1;counts[name]['predictions']+=1
     if not eligible:status='unscoreable';s['unscoreable_predictions']+=1;counts[name]['unscoreable_predictions']+=1
     else:
      s['evaluated_predictions']+=1;status='matched' if value==answer else 'conflict';key='verified_positional_matches' if value==answer else 'positional_conflicts';s[key]+=1;counts[name][key]+=1
    row[name]={'prediction':value,'status':status,'abstention_reason':t[name]['abstention_reason']}
   rows.append(row)
  units.append({'uid':p['uid'],'component':p['component'],'token_denominator':len(p['tokens']),'gate':ref['gate'],'primary':counts['primary'],'secondary':counts['secondary']})
 for s in tot.values():
  assert s['all_tokens']==s['predictions']+s['abstentions'] and s['predictions']==s['verified_positional_matches']+s['positional_conflicts']+s['unscoreable_predictions']
  s['prediction_coverage']=ratio(s['predictions'],s['all_tokens']);s['supported_agreement_all_predictions']=ratio(s['verified_positional_matches'],s['predictions']);s['conditional_agreement_scoreable_predictions']=ratio(s['verified_positional_matches'],s['evaluated_predictions'])
 return {'stats':tot,'tokens':rows,'units':units,'eligible_units':sum(r['gate']['development_positional_score_eligible'] for r in rs)}

def main():
 out=ROOT/'runs/000018_kamri_passage_transfer';m=check_hashes(out);cfg=read(ROOT/'experiments/kamri_transfer_v18.json');b=read(ROOT/'benchmarks/kamri_transfer_v18.json');report=read(out/'report.json')
 c=read(ROOT/cfg['candidates']);targets=read(ROOT/'data/v18/targets.json');pred=read(ROOT/b['predictions']);ref=read(ROOT/b['references']);seal=read(ROOT/'data/v18/prediction_seal.json');rseal=read(ROOT/'data/v18/reference_seal.json');ps=pred['units'];rs=ref['units']
 assert cfg['seed']==m['seed']==2026100218 and cfg['permutations']==m['permutation_denominator']==999 and cfg['p_max']==0.01
 assert c['frozen_at_utc']<=cfg['registered_at_utc']<=targets['selected_at_utc']<=pred['sealed_at_utc']<=seal['sealed_at_utc']<ref['preparation_started_at_utc']<=ref['reviewed_at_utc']<=rseal['sealed_at_utc']<=b['frozen_at_utc']<m['started_at_utc']
 assert digest((ROOT/'data/v18/frozen_predictions.json').read_bytes())==seal['predictions_sha256'] and digest((ROOT/b['references']).read_bytes())==rseal['references_sha256']
 assert pred['candidate_sha256']==seal['candidate_sha256']==digest((ROOT/cfg['candidates']).read_bytes()) and pred['target_sha256']==seal['target_sha256']==digest((ROOT/'data/v18/targets.json').read_bytes())
 assert ref['prediction_seal_sha256']==rseal['prediction_seal_sha256']==digest((ROOT/'data/v18/prediction_seal.json').read_bytes())
 forms=read(ROOT/'runs/000017_kamri_positional_consistency/form_ledger.json')['forms']
 for name,flag in [('primary','cross_component_review_lead'),('secondary','strict_global_positional_consistency')]:
  expected={f['fl_form']:{'paired_english_form':next(iter(f['english_counts'])),'support_units':f['unit_uids'],'support_components':f['components'],'occurrences':f['occurrences'],'status':'unvalidated frozen positional candidate'} for f in forms if f[flag]}
  assert c[name]==expected
 assert c['conflicted_forms']==[f for f in forms if f['conflicting_repeated_form']] and len(c['primary'])==3 and len(c['secondary'])==34
 assert c['training_form_ledger_sha256']==digest((ROOT/'runs/000017_kamri_positional_consistency/form_ledger.json').read_bytes())
 assert not c['semantic_gold'] and not c['lexicons_used'] and not targets['reading_english_exported'] and not pred['target_reference_english_used'] and not ref['target_proposed_english_used']
 assert [t['uid'] for t in targets['units']]==[p['uid'] for p in ps]==[r['uid'] for r in rs]==cfg['unit_uids'] and len(ps)==8
 old=read(ROOT/'data/v15/parsed_annotations.json')['articles'];total=0
 for t,p in zip(targets['units'],ps,strict=True):
  article=old[int(t['uid'][:2])-1];u=article['units'][t['number']-1];assert u['uid']==t['uid'] and u['fl']==t['fl'] and 5<=t['number']<=8
  assert set(t)=={'uid','component','number','fl','original_url','origin'}
  tt=tokens(t['fl']);assert len(p['tokens'])==p['token_denominator']==len(tt);total+=len(tt)
  for i,(tok,row) in enumerate(zip(tt,p['tokens'],strict=True)):
   assert row['uid']==t['uid']+f':t{i:03d}' and row['index']==i and row['fl_form']==tok.normalized and row['fl_surface']==tok.surface and row['fl_span']==[tok.start,tok.end]
   for name in ('primary','secondary'):
    item=c[name].get(tok.normalized);value=item['paired_english_form'] if item else None;reason=None if item else 'conflicted_training_form' if any(f['fl_form']==tok.normalized for f in c['conflicted_forms']) else 'outside_frozen_candidate_set'
    assert row[name]=={'form':value,'abstention_reason':reason}
 assert total==pred['token_denominator']==b['token_denominator']==m['token_denominator']==report['token_denominator']==175
 training=read(ROOT/'runs/000016_kamri_correspondence_review/unit_ledger.json')['units']
 for g in cfg['components']:
  sd=read(ROOT/f'data/v16/normalized/{g}_source.json');fd=read(ROOT/f'data/v16/normalized/{g}_fl.json');ss=source_statements(sd)
  anchor=next(u for u in training if u['component']==g and u['uid'].endswith(':004'))['english_statement_matches'][0]
  at=[i for i,s in enumerate(ss) if s['span']==anchor['span'] and s['text']==anchor['text']];assert len(at)==1
  chosen=[(i,s) for i,s in enumerate(ss) if i>at[0] and s['complete']][:4];assert len(chosen)==4
  recorded=next(a for a in ref['anchors'] if a['component']==g);assert recorded['source_statement_index']==at[0] and recorded['selected_statement_indices']==[i for i,s in chosen]
  historical=source_statements(fd);selected=[r for r in rs if r['component']==g];tt=[t for t in targets['units'] if t['component']==g]
  for (i,s),r,t in zip(chosen,selected,tt,strict=True):
   assert r['source_statement']==s['text'] and r['source_span']==s['span'] and r['source_statement_index']==i and r['source_block_id']==s['block_id']
   assert sd['text'][slice(*r['source_span'])]==r['source_statement'] and r['source_document']==f'data/v16/normalized/{g}_source.json'
   et=tokens(s['text'],s['span'][0]);ft=tokens(t['fl']);assert r['target_token_count']==len(ft) and r['source_token_count']==len(et)
   assert r['source_tokens']==[{'index':j,'surface':tok.surface,'form':tok.normalized,'span':[tok.start,tok.end]} for j,tok in enumerate(et)]
   matches=[s for s in historical if words(s['text'])==words(t['fl'])];assert len(matches)==len(r['historical_fl_statement_matches'])
   for s,h in zip(matches,r['historical_fl_statement_matches'],strict=True):assert s['text']==h['text'] and s['span']==h['span'] and s['block_id']==h['block_id']
   full=len(matches)==1 and matches[0]['complete'] and [tok.normalized for tok in tokens(matches[0]['text'])]==[tok.normalized for tok in ft]
   req={'source_authority':sd['source_authority_reviewed'],'source_statement_complete':True,'source_continuation_orderly':True,'historical_fl_unique_complete':full,'equal_token_counts':len(ft)==len(et)}
   assert r['gate']=={'development_positional_score_eligible':all(req.values()),'requirements':req,'unmet':[k for k,v in req.items() if not v],'semantic_training_eligible':False,'untouched_test_eligible':False}
   assert not r['current_raw_fl'] and not r['semantic_gold'] and fd['snapshot']['acquisition_kind']=='indexed_web_excerpt'
 observed=score(ps,rs);assert observed['stats']==report['stats'] and observed['tokens']==read(out/'token_ledger.json')['rows'] and observed['units']==read(out/'unit_ledger.json')['units']
 assert len(observed['tokens'])==read(out/'token_ledger.json')['denominator']==175 and len(observed['units'])==8 and observed['eligible_units']==report['eligible_units']==3
 assert sum(len(r['source_tokens']) for r in rs)==report['source_token_denominator']==176
 for component in report['components']:
  sub=score([p for p in ps if p['component']==component['component']],[r for r in rs if r['component']==component['component']]);assert sub['stats']==component['stats'] and sub['eligible_units']==component['eligible_units'] and component['units']==4
 outcomes=read(out/'per_form_outcomes.json');assert [f['fl_form'] for f in outcomes]==sorted({t['fl_form'] for t in observed['tokens']})
 for f in outcomes:
  group=[t for t in observed['tokens'] if t['fl_form']==f['fl_form']];assert f['occurrence_uids']==[t['uid'] for t in group] and f['unit_uids']==sorted({t['unit_uid'] for t in group}) and not f['semantic_training_eligible']
  for name in ('primary','secondary'):assert f[name]==dict(Counter(t[name]['status'] for t in group))|{k:sum(t[name]['status']==k for t in group) for k in ('matched','conflict','unscoreable','abstained')}
 lengths={r['uid']:len(r['source_tokens']) for r in rs};controls=read(out/'fixed_controls.json');assert [c['name'] for c in controls]==cfg['controls']
 for control in controls:
  orders={u:list(range(n-1,-1,-1)) if control['name']=='reverse' else [(i-int(control['name'].split('_')[1]))%n for i in range(n)] for u,n in sorted(lengths.items())}
  assert orders==control['orders'];s=score(ps,rs,orders);assert s['stats']==control['stats'] and s['eligible_units']==control['eligible_units']==3
 assert report['fixed_controls']==controls
 permutations=read(out/'permutations.json');assert len(permutations)==999 and [p['number'] for p in permutations]==list(range(999))
 rng=random.Random(cfg['seed']);count=observed['stats']['primary']['verified_positional_matches'];ge=ties=0;values=[]
 for p in permutations:
  orders={}
  for u,n in sorted(lengths.items()):
   order=list(range(n));rng.shuffle(order);orders[u]=order
  assert p['orders']==orders;s=score(ps,rs,orders);assert s['stats']==p['stats'] and s['eligible_units']==p['eligible_units']==3
  value=s['stats']['primary']['verified_positional_matches'];values.append(value);ge+=value>=count;ties+=value==count
  assert p['greater_or_equal_to_observed']==(value>=count) and p['exact_tie']==(value==count)
  for name in ('primary','secondary'):
   for k in ('predictions','abstentions','unscoreable_predictions','evaluated_predictions'):assert s['stats'][name][k]==observed['stats'][name][k]
 q=report['primary_test'];pval=ratio(1+ge,1000)
 assert q['available'] and q['observed']==observed['stats']['primary']['supported_agreement_all_predictions'] and q['observed_verified_matches']==count
 assert q['greater_or_equal']==ge and q['exact_ties']==ties and q['p_one_sided']==pval and q['registered_p_max']==0.01
 assert q['development_transfer_criterion_met']==(pval['value']<=0.01) and q['null_mean_verified_matches']==ratio(sum(values),999) and q['null_max_verified_matches']==max(values)
 assert report['semantic_training_eligible_tokens']==report['untouched_test_eligible_units']==0 and not report['shared_lexicons_used'] and not report['translation_model_executed'] and not report['new_lexical_induction_executed']
 assert m['model_executed'] and report['model_executed'] and pred['model_executed']
 assert m['outcome']==('conditional_development_transfer_signal' if q['development_transfer_criterion_met'] else 'registered_development_transfer_criterion_not_met')
 previous=[]
 for p in sorted((ROOT/'runs').glob('0000*')):
  if p==out:continue
  check_hashes(p);previous.append({'run_id':p.name,'manifest_sha256':digest((p/'manifest.json').read_bytes())})
 assert len(previous)==17
 receipt={'state':'verified','verified_at_utc':utc(),'run_id':out.name,'manifest_sha256':digest((out/'manifest.json').read_bytes()),'stats':report['stats'],'primary_test':q,'previous_runs':previous,
  'checks':['Candidates exactly from v17; FL-only fixed unit inputs and deterministic predictions sealed before references','Eight source-only consecutive statements, every source/target token span and historical coverage gate','All 175 tokens, predictions, abstentions, conflicts and unsupported predictions retained','Independent primary/secondary per-unit/form/component scoring with fixed full denominators','All 999 shuffle orders, five controls, integer tail counts and unchanged criterion','No semantic labels or new untouched units; input/code/output hashes and seventeen archives preserved'],
  'limits':['Only three development-scoreable units; five unresolved units retained','Historical indexed FL, not current raw captures','Conditional positional transfer comparison, not independent lexical accuracy']}
 dump_json(ROOT/'reports/000018_verification.json',receipt);print(json.dumps({'state':'verified','units':8,'tokens':175,'scoreable_units':3,'permutations':999,'previous_runs':17},indent=2))
if __name__=='__main__':main()
