"""Single comparison of a fixed constrained model; prior runs are read-only."""
import argparse,hashlib,json
from datetime import datetime,timezone
from pathlib import Path
from fl_decipher.context_guard_v79 import fit,predict,check_model
from fl_decipher.word_order_v77 import segments,vocabulary,metrics,summarize,UNK
ROOT=Path(__file__).resolve().parents[1];REG='experiments/context_guard_v79.json';OUT='runs/000079_context_guard'
CODE=['experiments/context_guard_v79.md','src/fl_decipher/context_guard_v79.py','scripts/context_guard_v79.py',
      'scripts/verify_context_guard_v79.py','tests/test_context_guard_v79.py']
def read(p):return json.loads((ROOT/p).read_text())
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def now():return datetime.now(timezone.utc).isoformat()
def write(p,x):
 path=ROOT/p;path.parent.mkdir(parents=True,exist_ok=True)
 with path.open('x') as f:json.dump(x,f,indent=2,ensure_ascii=False);f.write('\n')
def prepare():
 paths=set(CODE)
 for v in (76,77,78):
  p=f'reports/0000{v}_deliverable_seal.json';paths.add(p)
  for name,h in read(p)['deliverable_hashes'].items():assert sha(name)==h,name;paths.add(name)
 write(REG,{'experiment_id':'context_guard_v79','registered_at_utc':now(),
            'input_hashes':{p:sha(p) for p in sorted(paths)},'minimum_known_transitions':5,
            'minimum_training_groups':2,'context_weight':.5,'prior_mass':10,
            'unknown_target_mass':'fixed_unigram','unknown_context':'unigram',
            'draws':99,'panel':'unchanged_E77','adaptive_development':True})
 print('Frozen model and unchanged panel/controls before scoring.')
def run():
 reg=read(REG)
 for p,h in reg['input_hashes'].items():assert sha(p)==h,p
 (ROOT/OUT).mkdir(exist_ok=False)
 m={'experiment_id':'context_guard_v79','state':'running','started_at_utc':now(),
    'input_hashes':reg['input_hashes']|{REG:sha(REG)}};write(OUT+'/manifest.json',m)
 try:
  old=read('runs/000077_word_order/report.json');gs=[f['group'] for f in old['folds']]
  rows=[r for r in read('runs/000076_order_corpus/unit_ledger.json') if r['exclusion'] is None and r['group'] in gs]
  assert len(gs)==13 and len(rows)==98
  orders=read('data/v77/control_orders.json');folds=[]
  for fi,g in enumerate(gs):
   train=[r for r in rows if r['group']!=g]
   seq=[(r['group'],[r['tokens'][i]['form'] for i in s]) for r in train for s in segments(r)]
   vocab=vocabulary([s for _,s in seq]);model=fit(seq,vocab);check_model(model)
   original=read(f'runs/000077_word_order/fold_{fi:02}.json');assert vocab==original['vocabulary']
   targets=original['targets'];known=[t['target']!=UNK for t in targets]
   u=[model[0][t['target']] for t in targets];assert u==original['unigram_probabilities']
   def probabilities(fitted):
    result=[predict(fitted,t['context'],t['target']) for t in targets]
    for j,t in enumerate(targets):
     if t['target']==UNK or t['context'] not in fitted[4]:assert result[j]==u[j]
    return result
   observed=probabilities(model);cp=[];controls=[]
   for d in range(99):
    shuffled=[(r['group'],[r['tokens'][i]['form'] for i in s]) for r in train for s in orders[r['uid']][d]]
    cm=fit(shuffled,vocab);check_model(cm);assert cm[0]==model[0]
    ps=probabilities(cm);cp.append(ps);controls.append(metrics(u,ps,known))
   obs=metrics(u,observed,known)
   fold={'group':g,'training_groups':[h for h in gs if h!=g],'vocabulary':vocab,'pairs':len(targets),
         'unknown_targets':original['unknown_targets'],'unknown_contexts':original['unknown_contexts'],
         'eligible_evaluation_contexts':sum(t['context'] in model[4] for t in targets),
         'eligible_known_target_pairs':sum(t['context'] in model[4] and t['target']!=UNK for t in targets),
         'gain_change_from_e77':obs['gain']-original['observed']['gain'],
         'observed':obs,'controls':controls}
   support={h:{'known_transitions':model[2][h],'groups':sorted(model[3][h]),'eligible':h in model[4]} for h in sorted(model[2])}
   write(OUT+f'/fold_{fi:02}.json',fold|{'targets':targets,'context_support':support,
          'unigram_probabilities':u,'observed_probabilities':observed,'control_probabilities':cp})
   folds.append(fold)
  summary=summarize(folds);assert summary['pairs']==1918
  report={'experiment_id':'context_guard_v79','folds':folds,'summary':summary,
          'engineering_requirements_passed':True,'e77_development_gate':False,
          'adaptive_development':True,'semantic_benchmark_qualifying_works':0,'semantic_claims_admitted':False}
  write(OUT+'/report.json',report)
  m.update(state='complete',finished_at_utc=now(),output_hashes={str(p.relative_to(ROOT)):sha(str(p.relative_to(ROOT))) for p in sorted((ROOT/OUT).glob('*.json')) if p.name!='manifest.json'})
  print(json.dumps({k:v for k,v in summary.items() if k!='control_macro_gains'},indent=2))
 except Exception as e:m.update(state='failed',finished_at_utc=now(),error=repr(e));raise
 finally:(ROOT/OUT/'manifest.json').write_text(json.dumps(m,indent=2)+'\n')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','run']);args=p.parse_args();{'prepare':prepare,'run':run}[args.action]()
