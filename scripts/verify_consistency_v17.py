"""Independent brute-force occurrence-pair statistics and full randomization replay."""
from collections import Counter
from fractions import Fraction
from itertools import combinations
from pathlib import Path
import json,random
from fl_decipher.corpus import digest,dump_json
from fl_decipher.natural_v12 import utc
from verify_correspondence_v6 import check_hashes
ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text())
def rat(value):return None if value is None else {'numerator':value.numerator,'denominator':value.denominator,'value':float(value)}
def scope_metrics(rows,scope):
 scores=[];unit_pairs=occ_pairs=equal_pairs=0
 for f in sorted({r['fl_form'] for r in rows}):
  group=[r for r in rows if r['fl_form']==f];uids=sorted({r['unit_uid'] for r in group});form_scores=[]
  for a,b in combinations(uids,2):
   left=[r for r in group if r['unit_uid']==a];right=[r for r in group if r['unit_uid']==b]
   same=left[0]['component']==right[0]['component']
   if scope=='within_component' and not same or scope=='between_components' and same:continue
   equal=sum(x['english_form']==y['english_form'] for x in left for y in right);den=len(left)*len(right)
   form_scores.append(Fraction(equal,den));unit_pairs+=1;occ_pairs+=den;equal_pairs+=equal
  if form_scores:scores.append(sum(form_scores,Fraction(0))/len(form_scores))
 return {'scope':scope,'eligible_forms':len(scores),'distinct_unit_pairs':unit_pairs,'occurrence_pairs':occ_pairs,'equal_occurrence_pairs':equal_pairs,
  'macro_form_cross_unit_agreement':rat(sum(scores,Fraction(0))/len(scores) if scores else None),'occurrence_weighted_agreement':rat(Fraction(equal_pairs,occ_pairs) if occ_pairs else None)}
def form_stats(rows):
 ans=[]
 for f in sorted({r['fl_form'] for r in rows}):
  group=[r for r in rows if r['fl_form']==f];uids=sorted({r['unit_uid'] for r in group});groups=sorted({r['component'] for r in group})
  by={c:{'units':sorted({r['unit_uid'] for r in group if r['component']==c}),'english_counts':dict(sorted(Counter(r['english_form'] for r in group if r['component']==c).items())), 'occurrences':sum(r['component']==c for r in group)} for c in groups}
  outcomes=dict(sorted(Counter(r['english_form'] for r in group).items()));repeated=len(uids)>1
  ans.append({'fl_form':f,'occurrences':len(group),'unit_uids':uids,'components':groups,'english_counts':outcomes,'occurrence_uids':[r['uid'] for r in group],
   'english_outcomes':len(outcomes),'cross_unit_repeated':repeated,'within_unit_repetition_only':len(group)>1 and not repeated,
   'strict_global_positional_consistency':repeated and len(outcomes)==1,'conflicting_repeated_form':repeated and len(outcomes)>1,
   'cross_component_review_lead':len(groups)>1 and len(outcomes)==1 and all(len(by[c]['units'])>=2 for c in groups),
   'by_component':by,'semantic_training_eligible':False,'untouched_test_eligible':False,'agreement':scope_metrics(group,'global')['macro_form_cross_unit_agreement']})
 return ans
def stats(rows):
 forms=form_stats(rows);components=sorted({r['component'] for r in rows})
 return {'occurrences':len(rows),'units':len({r['unit_uid'] for r in rows}),'components':len(components),'form_types':len(forms),
  'cross_unit_repeated_types':sum(f['cross_unit_repeated'] for f in forms),'within_unit_repetition_only_types':sum(f['within_unit_repetition_only'] for f in forms),
  'strict_global_types':sum(f['strict_global_positional_consistency'] for f in forms),'conflicting_repeated_types':sum(f['conflicting_repeated_form'] for f in forms),
  'cross_component_types':sum(len(f['components'])>1 for f in forms),'cross_component_review_leads':sum(f['cross_component_review_lead'] for f in forms),
  'strict_types_by_component':{c:sum(len(f['by_component'][c]['units'])>=2 and len(f['by_component'][c]['english_counts'])==1 for f in forms if c in f['by_component']) for c in components},
  'global':scope_metrics(rows,'global'),'within_component':scope_metrics(rows,'within_component'),'between_components':scope_metrics(rows,'between_components')}
def fraction(s):
 q=s['global']['macro_form_cross_unit_agreement'];return Fraction(q['numerator'],q['denominator'])
def transform(rows,orders,origins=None):
 origins=origins or {};units={u:sorted([r for r in rows if r['unit_uid']==u],key=lambda r:r['index']) for u in sorted({r['unit_uid'] for r in rows})}
 result=[]
 for u in units:
  original=units[origins.get(u,u)];assert len(original)==len(units[u]) and sorted(orders[u])==list(range(len(original)))
  for i,r in enumerate(units[u]):result.append(r|{'english_form':original[orders[u][i]]['english_form']})
 return result

def main():
 out=ROOT/'runs/000017_kamri_positional_consistency';m=check_hashes(out);cfg=read(ROOT/'experiments/kamri_consistency_v17.json');report=read(out/'report.json')
 rows=read(out/'occurrence_ledger.json')['rows'];original=read(ROOT/'runs/000016_kamri_correspondence_review/unit_ledger.json')['units'];units={r['uid']:r for r in original};uidlist=sorted(units)
 assert uidlist==cfg['unit_uids'] and len(rows)==212 and len({r['uid'] for r in rows})==212
 assert cfg['seed']==m['seed']==2026100117 and cfg['permutations']==m['permutation_denominator']==999
 assert cfg['registered_at_utc']<m['started_at_utc'] and cfg['primary_criterion']['p_max']==0.01
 assert report['stage']==cfg['stage']=='development_positional_consistency'
 cursor=0
 for u in original:
  for h in u['positional_hypotheses']:
   r=rows[cursor];cursor+=1
   assert r['uid']==u['uid']+f":t{h['index']:03d}" and r['unit_uid']==u['uid'] and r['component']==u['component'] and r['index']==h['index']
   for key in ('fl_form','english_form','fl_surface','english_surface','fl_span','english_span'):assert r[key]==h[key]
   for side in ('fl','english'):
    d=read(ROOT/f"data/v16/normalized/{u['component']}_{'fl' if side=='fl' else 'source'}.json")
    assert d['text'][slice(*r[side+'_span'])]==r[side+'_surface']
   assert r['status']=='frozen unvalidated positional hypothesis'
 assert report['unit_inventory']==[{'uid':r['uid'],'component':r['component'],'occurrences':len(r['positional_hypotheses']),'fl_provenance':'historical_indexed_excerpt','current_raw_fl':False} for r in original]
 observed=stats(rows);forms=form_stats(rows);assert observed==report['observed'] and forms==read(out/'form_ledger.json')['forms']
 assert len(forms)==read(out/'form_ledger.json')['denominator']
 assert observed['strict_global_types']+observed['conflicting_repeated_types']==observed['cross_unit_repeated_types']
 leads=read(out/'review_leads.json');assert leads['forms']==[f for f in forms if f['cross_component_review_lead']] and leads['denominator']==len(leads['forms'])
 assert report['review_lead_forms']==[f['fl_form'] for f in leads['forms']]
 assert not leads['semantic_training_eligible'] and not leads['untouched_test_eligible'] and not leads['independently_reviewed_meanings']
 controls=read(out/'fixed_controls.json');assert [c['name'] for c in controls]==cfg['controls']
 lengths={u:len(units[u]['positional_hypotheses']) for u in uidlist};equal_pairs=[list(p) for p in combinations(uidlist,2) if lengths[p[0]]==lengths[p[1]]]
 assert equal_pairs==[cfg['length_matched_swap']]==[['03:003','13:004']]
 for c in controls:
  orders={};origins={}
  for u in uidlist:
   count=lengths[u];name=c['name']
   if name.startswith('rotate_'):orders[u]=[(i-int(name.split('_')[1]))%count for i in range(count)]
   elif name=='reverse':orders[u]=list(range(count-1,-1,-1))
   else:
    assert name=='length_matched_swap';orders[u]=list(range(count))
    if u in cfg['length_matched_swap']:origins[u]=next(v for v in cfg['length_matched_swap'] if v!=u)
  assert c['orders']==orders and c['english_origin_units']==origins
  changed=transform(rows,orders,origins);assert stats(changed)==c['metrics'] and form_stats(changed)==c['form_ledger']
  assert [r['uid'] for r in changed]==[r['uid'] for r in rows] and Counter(r['english_form'] for r in changed)==Counter(r['english_form'] for r in rows)
 assert report['fixed_controls']==[{'name':c['name'],'metrics':c['metrics']} for c in controls]
 permutations=read(out/'permutations.json');assert len(permutations)==999 and [p['number'] for p in permutations]==list(range(999))
 rng=random.Random(cfg['seed']);primary=fraction(observed);values=[];ge=ties=0
 for p in permutations:
  orders={}
  for u in uidlist:
   positions=list(range(lengths[u]));rng.shuffle(positions);orders[u]=positions
  assert p['orders']==orders
  changed=transform(rows,orders);s=stats(changed);assert s==p['metrics'];value=fraction(s);values.append(value)
  assert p['greater_or_equal_to_observed']==(value>=primary) and p['exact_tie']==(value==primary)
  ge+=value>=primary;ties+=value==primary
  assert len(changed)==212
  for u in uidlist:assert Counter(x['english_form'] for x in changed if x['unit_uid']==u)==Counter(x['english_form'] for x in rows if x['unit_uid']==u)
 pval=Fraction(1+ge,1000);s=report['primary_test'];ordered=sorted(values)
 assert s['observed']==rat(primary) and s['greater_or_equal']==ge and s['exact_ties']==ties and s['p_one_sided']==rat(pval)
 assert s['null_mean']==rat(sum(values,Fraction(0))/999) and s['null_min']==rat(ordered[0]) and s['null_median']==rat(ordered[499]) and s['null_max']==rat(ordered[-1])
 assert s['null_permutations']==999 and s['registered_p_max']==0.01 and s['development_signal_criterion_met']==(pval<=Fraction(1,100))
 assert m['outcome']==('conditional_development_signal' if pval<=Fraction(1,100) else 'registered_development_signal_not_met')
 assert not m['model_executed'] and not report['model_executed'] and not report['lexicons_used']
 assert report['semantic_training_eligible_occurrences']==report['untouched_test_eligible_units']==0
 assert not any((out/p).exists() for p in ('lexicon.json','predictions.json','training_labels.json','thresholds.json'))
 previous=[]
 for p in sorted((ROOT/'runs').glob('0000*')):
  if p==out:continue
  check_hashes(p);previous.append({'run_id':p.name,'manifest_sha256':digest((p/'manifest.json').read_bytes())})
 assert len(previous)==16
 receipt={'state':'verified','verified_at_utc':utc(),'run_id':out.name,'manifest_sha256':digest((out/'manifest.json').read_bytes()),'observed':observed,'primary_test':s,'previous_runs':previous,
  'checks':['All 212 frozen input identities, eight units, two exposed components and independent source offsets','Brute-force occurrence-pair agreement and exact form/unit denominators','All singleton/conflicting/strict types and zero semantic admissions','Six complete fixed controls, directions and sole length-matched swap','All 999 RNG orders, per-unit multisets, exact statistics, ties and registered criterion','Input/code/output hashes and sixteen historical archives preserved'],
  'limits':['Conditional development randomization does not establish word meanings or generalization','Historical indexed FL provenance and source-group exposure unchanged']}
 dump_json(ROOT/'reports/000017_verification.json',receipt)
 print(json.dumps({'state':'verified','occurrences':212,'units':8,'permutations':999,'previous_runs':16,'development_signal_criterion_met':s['development_signal_criterion_met']},indent=2))
if __name__=='__main__':main()
