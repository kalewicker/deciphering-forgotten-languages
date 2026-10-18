"""Fixed extension transfer against source-only references; preserve every denominator."""
from pathlib import Path
import json,random,sys,platform,time
from fl_decipher.corpus import digest,dump_json
from fl_decipher.natural_v12 import utc
from fl_decipher.transfer_v18 import evaluate,ratio
ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text())
def main():
 cp=ROOT/'experiments/kamri_transfer_v18.json';cfg=read(cp);bp=ROOT/'benchmarks/kamri_transfer_v18.json';b=read(bp)
 for p,sha in b['input_hashes'].items():assert digest((ROOT/p).read_bytes())==sha,p
 pred=read(ROOT/b['predictions']);ref=read(ROOT/b['references']);ps=pred['units'];rs=ref['units']
 assert [u['uid'] for u in ps]==[u['uid'] for u in rs]==cfg['unit_uids']
 assert pred['sealed_at_utc']<ref['preparation_started_at_utc']<=ref['reviewed_at_utc']<=b['frozen_at_utc']
 out=ROOT/'runs/000018_kamri_passage_transfer';out.mkdir(exist_ok=False)
 code=sorted([*(ROOT/'src/fl_decipher').glob('*.py'),*(ROOT/'scripts').glob('*.py'),*(ROOT/'tests').glob('*.py')])
 m={'run_id':out.name,'experiment_id':cfg['experiment_id'],'stage':cfg['stage'],'state':'running','started_at_utc':utc(),
  'model_executed':True,'model_kind':'frozen positional candidate lookup','translation_model_executed':False,'new_lexical_induction_executed':False,
  'seed':cfg['seed'],'permutation_denominator':999,'unit_denominator':8,'token_denominator':pred['token_denominator'],
  'python':sys.version,'platform':platform.platform(),'input_hashes':b['input_hashes']|{str(bp.relative_to(ROOT)):digest(bp.read_bytes())},
  'code_hashes':{str(p.relative_to(ROOT)):digest(p.read_bytes()) for p in code}}
 dump_json(out/'manifest.json',m);start=time.monotonic()
 try:
  observed=evaluate(ps,rs);dump_json(out/'token_ledger.json',{'denominator':pred['token_denominator'],'rows':observed['tokens']})
  dump_json(out/'unit_ledger.json',{'denominator':8,'units':observed['units']})
  orders0={r['uid']:list(range(len(r['source_tokens']))) for r in rs};controls=[]
  for name in cfg['controls']:
   orders={}
   for uid,seq in sorted(orders0.items()):
    if name=='reverse':order=list(reversed(seq))
    else:
     k=int(name.split('_')[1])%len(seq);order=seq[-k:]+seq[:-k] if k else seq[:]
    orders[uid]=order
   s=evaluate(ps,rs,orders);controls.append({'name':name,'orders':orders,'stats':s['stats'],'eligible_units':s['eligible_units']})
  dump_json(out/'fixed_controls.json',controls)
  primary=observed['stats']['primary'];count=primary['verified_positional_matches'];available=primary['predictions']>0 and primary['evaluated_predictions']>0
  rng=random.Random(cfg['seed']);permutations=[];values=[];ge=ties=0
  for number in range(cfg['permutations']):
   orders={}
   for uid,seq in sorted(orders0.items()):
    order=seq[:];rng.shuffle(order);orders[uid]=order
   result=evaluate(ps,rs,orders);value=result['stats']['primary']['verified_positional_matches'];values.append(value)
   ge+=value>=count;ties+=value==count
   permutations.append({'number':number,'orders':orders,'stats':result['stats'],'eligible_units':result['eligible_units'],
     'greater_or_equal_to_observed':value>=count,'exact_tie':value==count})
  assert len(permutations)==999;dump_json(out/'permutations.json',permutations)
  p=ratio(1+ge,1000) if available else None;met=bool(p and p['value']<=cfg['p_max'])
  per_form=[]
  for form in sorted({t['fl_form'] for t in observed['tokens']}):
   rows=[t for t in observed['tokens'] if t['fl_form']==form]
   per_form.append({'fl_form':form,'unit_uids':sorted({t['unit_uid'] for t in rows}),'occurrence_uids':[t['uid'] for t in rows],
    **{name:{status:sum(t[name]['status']==status for t in rows) for status in ('matched','conflict','unscoreable','abstained')} for name in ('primary','secondary')},
    'semantic_training_eligible':False})
  dump_json(out/'per_form_outcomes.json',per_form)
  components=[]
  for g in cfg['components']:
   subp=[u for u in ps if u['component']==g];subr=[u for u in rs if u['component']==g];s=evaluate(subp,subr)
   components.append({'component':g,'units':s['unit_denominator'],'eligible_units':s['eligible_units'],'stats':s['stats']})
  report={'experiment_id':cfg['experiment_id'],'stage':cfg['stage'],'model_executed':True,'model_kind':'frozen positional candidate lookup',
   'translation_model_executed':False,'new_lexical_induction_executed':False,'shared_lexicons_used':False,
   'unit_denominator':8,'component_denominator':2,'token_denominator':pred['token_denominator'],'source_token_denominator':sum(len(r['source_tokens']) for r in rs),
   'eligible_units':observed['eligible_units'],'stats':observed['stats'],'components':components,
   'primary_test':{'available':available,'statistic':'verified primary matches / all frozen primary predictions','observed':primary['supported_agreement_all_predictions'],
     'observed_verified_matches':count,'null_permutations':999,'greater_or_equal':ge,'exact_ties':ties,'p_one_sided':p,'registered_p_max':cfg['p_max'],
     'development_transfer_criterion_met':met,'null_mean_verified_matches':ratio(sum(values),999),'null_max_verified_matches':max(values),
     'interpretation':'Conditional ordering-specific development transfer on the supported subset; not semantic accuracy or held-out generalization.'},
   'fixed_controls':controls,'semantic_training_eligible_tokens':0,'untouched_test_eligible_units':0,
   'limits':['Previously exposed components/inventory; extension new only relative to v16/v17 fitting units','Historical indexed FL; current raw captures unavailable','No candidate changes after target/reference review','Unscoreable predictions remain in the primary denominator, without being called proven errors','Positional reference comparison is not independent semantic gold']}
  dump_json(out/'report.json',report)
  md='# Experiment 18: frozen-candidate passage extension\n\nEight fixed extension units, two previously exposed components, '+str(pred['token_denominator'])+' target tokens. Three primary and 34 secondary candidates were frozen from v17 before FL-only target predictions and source-only reference preparation. Shared lexicons and proposed target English were not used.\n\n'
  md+=f"{observed['eligible_units']}/8 units pass the development positional-scoring gates. Four lack independent complete FL coverage; one has 21 FL versus 22 source tokens. They remain in the denominator. All FL evidence is historical/indexed; semantic and untouched-test eligibility remain zero.\n\n"
  md+='| Predictor | All tokens | Predictions | Abstentions | Scoreable predictions | Verified positional matches | Conflicts | Unscoreable predictions |\n|---|---:|---:|---:|---:|---:|---:|---:|\n'
  for name,s in observed['stats'].items():md+=f"| {name} | {s['all_tokens']} | {s['predictions']} | {s['abstentions']} | {s['evaluated_predictions']} | {s['verified_positional_matches']} | {s['positional_conflicts']} | {s['unscoreable_predictions']} |\n"
  md+=f"\nPrimary supported agreement over all frozen primary predictions: {primary['verified_positional_matches']}/{primary['predictions']}. Conditional agreement on scoreable predictions: {primary['verified_positional_matches']}/{primary['evaluated_predictions']}. The unsupported remainder is unresolved, not proven wrong.\n\n"
  md+=f"Registered one-sided ordering diagnostic p: {p['value'] if p else 'unavailable'}; criterion p <= 0.01: {'met' if met else 'not met'}. {ge}/999 null match counts meet or exceed the observed count, with {ties} exact ties; null mean {sum(values)/999:.6f}, maximum {max(values)}. All orders, gates and prediction denominators are preserved. This is conditional development evidence on three supported units, not lexical accuracy or fresh validation.\n\n"
  md+='| Fixed control | Primary verified matches | Secondary verified matches |\n|---|---:|---:|\n'
  for c in controls:md+=f"| {c['name']} | {c['stats']['primary']['verified_positional_matches']} | {c['stats']['secondary']['verified_positional_matches']} |\n"
  md+='\nThe full unit, token and per-form ledgers preserve every abstention, positional conflict and unmet evidence gate. The original training conflicts remain unresolved; no majority label, alias, alternate tokenization or offset repair was introduced. The next experiment must address the observed mismatch and missing evidence with a separately registered rule, retaining this archive.\n'
  (out/'report.md').write_text(md)
  m.update(state='completed',outcome='conditional_development_transfer_signal' if met else 'registered_development_transfer_criterion_not_met',finished_at_utc=utc(),elapsed_seconds=time.monotonic()-start,
   output_hashes={p.name:digest(p.read_bytes()) for p in out.iterdir() if p.name!='manifest.json'})
  dump_json(out/'manifest.json',m);print(json.dumps({k:report[k] for k in ('unit_denominator','token_denominator','eligible_units','stats','primary_test')},indent=2))
 except Exception as e:
  m.update(state='failed',error=f'{type(e).__name__}: {e}');dump_json(out/'manifest.json',m);raise
if __name__=='__main__':main()
