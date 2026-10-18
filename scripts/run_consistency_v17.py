"""Fixed-horizon conditional consistency diagnostic; no lexical model or acceptance."""
from pathlib import Path
from fractions import Fraction
import json,platform,sys,time
from fl_decipher.corpus import digest,dump_json
from fl_decipher.natural_v12 import utc
from fl_decipher.consistency_v17 import observations,summary,form_ledger,apply_orders,control_orders,permutation_orders,primary_fraction,rational,units_by_uid
ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text())
def main():
 cp=ROOT/'experiments/kamri_consistency_v17.json';cfg=read(cp)
 for p,sha in cfg['input_hashes'].items():assert digest((ROOT/p).read_bytes())==sha,p
 ledger=read(ROOT/'runs/000016_kamri_correspondence_review/unit_ledger.json')['units'];rows=observations(ledger)
 assert len(rows)==cfg['occurrence_denominator']==212 and list(units_by_uid(rows))==cfg['unit_uids']
 out=ROOT/'runs/000017_kamri_positional_consistency';out.mkdir(exist_ok=False)
 code=sorted([*(ROOT/'src/fl_decipher').glob('*.py'),*(ROOT/'scripts').glob('*.py'),*(ROOT/'tests').glob('*.py')])
 m={'run_id':out.name,'experiment_id':cfg['experiment_id'],'stage':cfg['stage'],'state':'running','started_at_utc':utc(),'model_executed':False,
  'python':sys.version,'platform':platform.platform(),'seed':cfg['seed'],'permutation_denominator':cfg['permutations'],'unit_denominator':8,'occurrence_denominator':212,
  'input_hashes':cfg['input_hashes']|{str(cp.relative_to(ROOT)):digest(cp.read_bytes())},'code_hashes':{str(p.relative_to(ROOT)):digest(p.read_bytes()) for p in code}}
 dump_json(out/'manifest.json',m);start=time.monotonic()
 try:
  observed=summary(rows);forms=form_ledger(rows);primary=primary_fraction(observed);assert primary is not None
  dump_json(out/'occurrence_ledger.json',{'denominator':212,'rows':rows})
  dump_json(out/'form_ledger.json',{'denominator':len(forms),'forms':forms})
  leads=[f for f in forms if f['cross_component_review_lead']]
  dump_json(out/'review_leads.json',{'stage':'development_positional_review_leads','forms':leads,'denominator':len(leads),
   'semantic_training_eligible':False,'untouched_test_eligible':False,'independently_reviewed_meanings':False,'criterion':'one English outcome; both components; at least two distinct units in each; no typewise significance testing'})
  controls=[]
  for name in cfg['controls']:
   orders,sources=control_orders(rows,name,cfg['length_matched_swap']);changed=apply_orders(rows,orders,sources)
   controls.append({'name':name,'orders':orders,'english_origin_units':sources,'metrics':summary(changed),'form_ledger':form_ledger(changed)})
  dump_json(out/'fixed_controls.json',controls)
  permutations=[];ge=ties=0;null_values=[]
  for number,orders in permutation_orders(rows,cfg['seed'],cfg['permutations']):
   metrics=summary(apply_orders(rows,orders));value=primary_fraction(metrics);null_values.append(value)
   ge+=value>=primary;ties+=value==primary
   permutations.append({'number':number,'orders':orders,'metrics':metrics,'greater_or_equal_to_observed':value>=primary,'exact_tie':value==primary})
  assert len(permutations)==cfg['permutations']==999
  dump_json(out/'permutations.json',permutations)
  p=Fraction(1+ge,1+cfg['permutations']);criterion_met=p<=Fraction(str(cfg['primary_criterion']['p_max']));ordered=sorted(null_values)
  report={'experiment_id':cfg['experiment_id'],'stage':cfg['stage'],'model_executed':False,'lexicons_used':False,'observed':observed,
   'primary_test':{'statistic':'macro_form_cross_unit_agreement','observed':rational(primary),'null_permutations':999,'greater_or_equal':ge,'exact_ties':ties,
    'p_one_sided':rational(p),'registered_p_max':cfg['primary_criterion']['p_max'],'development_signal_criterion_met':criterion_met,
    'null_mean':rational(sum(null_values,Fraction(0))/len(null_values)),'null_min':rational(ordered[0]),'null_median':rational(ordered[len(ordered)//2]),'null_max':rational(ordered[-1]),
    'interpretation':'Conditional ordering-specific development diagnostic on an exposed panel, not linguistic or population significance.'},
   'fixed_controls':[{'name':c['name'],'metrics':c['metrics']} for c in controls],
   'unit_inventory':[{'uid':r['uid'],'component':r['component'],'occurrences':len(r['positional_hypotheses']),'fl_provenance':'historical_indexed_excerpt','current_raw_fl':False} for r in ledger],
   'review_lead_forms':[f['fl_form'] for f in leads],'semantic_training_eligible_occurrences':0,'untouched_test_eligible_units':0,
   'limits':['v15-informed nomination and prior exposure of both components; no independent held-out evaluation','Historical indexed FL, current raw capture unavailable','Repeated token consistency alone cannot establish meanings or rule out polysemy, inflection or reordering','Primary global randomization diagnostic does not grant per-form significance','All controls preserve the eight-unit denominator; no branch, seed, threshold or source replacement']}
  dump_json(out/'report.json',report)
  md='# Experiment 17: positional cross-unit consistency\n\nAll 212 frozen position hypotheses across eight units and two previously exposed components are retained. No new retrieval, lexicon input, morphology aliases, lexical induction or model execution.\n\n'
  md+=f"There are {observed['form_types']} FL form types; {observed['cross_unit_repeated_types']} appear in at least two distinct units. Of those, {observed['strict_global_types']} have one English token outcome and {observed['conflicting_repeated_types']} have conflicting outcomes. {observed['within_unit_repetition_only_types']} types repeat only within one unit and receive no cross-unit-support credit.\n\n"
  md+=f"Primary form-macro cross-unit agreement: {float(primary):.6f}. Null mean: {float(report['primary_test']['null_mean']['value']):.6f}; null maximum: {float(ordered[-1]):.6f}. The one-sided Monte Carlo diagnostic p is {float(p):.6f} ({ge} of 999 controls meet or exceed the observed statistic; {ties} exact ties). Registered criterion p <= 0.01: {'met' if criterion_met else 'not met'}. This is conditional ordering-specific development evidence, not semantic or held-out success.\n\n"
  md+='| Scope | Eligible FL forms | Distinct unit-pairs across forms | Macro agreement | Matching occurrence pairs / all pairs |\n|---|---:|---:|---:|---|\n'
  for scope in ('global','within_component','between_components'):
   s=observed[scope];v=s['macro_form_cross_unit_agreement'];md+=f"| {scope} | {s['eligible_forms']} | {s['distinct_unit_pairs']} | {v['value'] if v else 'undefined'} | {s['equal_occurrence_pairs']} / {s['occurrence_pairs']} |\n"
  md+='\n| Fixed control | Primary agreement | Strict global repeated types | Cross-component review leads |\n|---|---:|---:|---:|\n'
  for c in controls:
   v=primary_fraction(c['metrics']);md+=f"| {c['name']} | {float(v):.6f} | {c['metrics']['strict_global_types']} | {c['metrics']['cross_component_review_leads']} |\n"
  md+=f"\n{len(leads)} FL forms satisfy the strict cross-component review-lead rule: one English outcome, both components, at least two distinct units in each. Their full occurrence evidence and every conflicting form are preserved. No per-form significance or independently validated meanings are assigned.\n\n"
  md+='The primary metric averages English outcome-frequency agreement across distinct unit pairs, then equally across eligible FL forms. Repeated positions within one sentence never create a second independent unit. Exact rational comparisons preserve ties. All 999 shuffled orders, complete statistics and six fixed controls are saved. Identity draws are retained, and the length-matched swap exchanges only the preregistered 26-token pair.\n\nSemantic training eligibility remains zero and no untouched test fold is created, regardless of the diagnostic criterion. The raw-FL provenance limitation from v16 persists. Next work must test these hypotheses on a separately registered extension or independently reviewed word-order/meaning evidence; reuse of this panel remains development.\n'
  (out/'report.md').write_text(md)
  m.update(state='completed',outcome='conditional_development_signal' if criterion_met else 'registered_development_signal_not_met',finished_at_utc=utc(),elapsed_seconds=time.monotonic()-start,
   output_hashes={p.name:digest(p.read_bytes()) for p in out.iterdir() if p.name!='manifest.json'})
  dump_json(out/'manifest.json',m)
  print(json.dumps({'observed':observed,'primary_test':report['primary_test'],'review_lead_forms':report['review_lead_forms']},indent=2))
 except Exception as e:
  m.update(state='failed',error=f'{type(e).__name__}: {e}');dump_json(out/'manifest.json',m);raise
if __name__=='__main__':main()
