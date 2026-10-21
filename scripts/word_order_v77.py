"""Single-use preparation and scoring of E77."""
import argparse,json,hashlib
from pathlib import Path
from datetime import datetime,timezone
from fl_decipher.word_order_v77 import segments,order,vocabulary,fit,predict,metrics,summarize,UNK
ROOT=Path(__file__).resolve().parents[1]
OUT='runs/000077_word_order'
REG='experiments/word_order_v77.json'
INPUTS=['runs/000076_order_corpus/unit_ledger.json','runs/000076_order_corpus/report.json','reports/000076_deliverable_seal.json']
CODE=['experiments/word_order_v77.md','src/fl_decipher/word_order_v77.py','scripts/word_order_v77.py','scripts/verify_word_order_v77.py','tests/test_word_order_v77.py']
def read(p):return json.loads((ROOT/p).read_text())
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def now():return datetime.now(timezone.utc).isoformat()
def write(p,x):
 path=ROOT/p;path.parent.mkdir(parents=True,exist_ok=True)
 with path.open('x') as f:json.dump(x,f,indent=2,ensure_ascii=False);f.write('\n')
def panel():
 report=read(INPUTS[1]);assert report['capacity_pass']
 gs=sorted(g['group'] for g in report['groups'] if g['eligible'])
 rows=[r for r in read(INPUTS[0]) if r['exclusion'] is None and r['group'] in gs]
 assert len(gs)==13 and len(rows)==98 and sum(t['pair_from_previous'] for r in rows for t in r['tokens'])==1918
 return gs,rows
def prepare():
 for p,h in read(INPUTS[2])['deliverable_hashes'].items():assert sha(p)==h,p
 gs,rows=panel()
 control={r['uid']:[[order(d,r['uid'],s) for s in segments(r)] for d in range(99)] for r in rows}
 write('data/v77/control_orders.json',control)
 write(REG,{'experiment_id':'word_order_v77','registered_at_utc':now(),
            'input_hashes':{p:sha(p) for p in INPUTS+CODE+['data/v77/control_orders.json']},
            'groups':gs,'draws':99,'training_vocabulary_min_count':2,'unigram_alpha':.5,'context_prior_mass':10})
 print('Frozen code, inputs and 99 control orders per segment; no scores computed.')
def run():
 reg=read(REG)
 for p,h in reg['input_hashes'].items():assert sha(p)==h,p
 gs,rows=panel();orders=read('data/v77/control_orders.json')
 (ROOT/OUT).mkdir(exist_ok=False)
 m={'state':'running','started_at_utc':now(),'input_hashes':reg['input_hashes']|{REG:sha(REG)}}
 write(OUT+'/manifest.json',m)
 try:
  folds=[]
  for g in gs:
   train=[r for r in rows if r['group']!=g];test=[r for r in rows if r['group']==g]
   seqs=[[r['tokens'][i]['form'] for i in s] for r in train for s in segments(r)]
   vocab=vocabulary(seqs);allowed=set(vocab);model=fit(seqs,vocab)
   targets=[]
   for r in test:
    for i,t in enumerate(r['tokens']):
     if t['pair_from_previous']:
      a=r['tokens'][i-1]['form'];b=t['form']
      targets.append({'uid':r['uid'],'context_index':i-1,'target_index':i,
                      'context':a if a in allowed else UNK,'target':b if b in allowed else UNK})
   known=[t['target']!=UNK for t in targets]
   u=[model[0][t['target']] for t in targets]
   p=[predict(model,t['context'],t['target']) for t in targets]
   controls=[];probabilities=[]
   for d in range(99):
    shuffled=[[r['tokens'][i]['form'] for i in s] for r in train for s in orders[r['uid']][d]]
    cm=fit(shuffled,vocab);assert cm[0]==model[0]
    cp=[predict(cm,t['context'],t['target']) for t in targets]
    probabilities.append(cp);controls.append(metrics(u,cp,known))
   fold={'group':g,'training_groups':[h for h in gs if h!=g],'vocabulary':vocab,'pairs':len(targets),
         'unknown_targets':sum(not k for k in known),'unknown_contexts':sum(t['context']==UNK for t in targets),
         'observed':metrics(u,p,known),'controls':controls}
   write(OUT+'/fold_'+str(gs.index(g)).zfill(2)+'.json',fold|{'targets':targets,'unigram_probabilities':u,
         'observed_probabilities':p,'control_probabilities':probabilities})
   folds.append(fold)
  report={'experiment_id':'word_order_v77','folds':folds,'summary':summarize(folds),
          'semantic_benchmark_qualifying_works':0,'semantic_claims_admitted':False}
  write(OUT+'/report.json',report)
  m.update(state='complete',finished_at_utc=now(),output_hashes={str(p.relative_to(ROOT)):sha(str(p.relative_to(ROOT))) for p in sorted((ROOT/OUT).glob('*.json')) if p.name!='manifest.json'})
  print(json.dumps(report['summary'],indent=2))
 except Exception as e:
  m.update(state='failed',finished_at_utc=now(),error=repr(e));raise
 finally:(ROOT/OUT/'manifest.json').write_text(json.dumps(m,indent=2)+'\n')
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('action',choices=['prepare','run']);args=ap.parse_args()
 {'prepare':prepare,'run':run}[args.action]()
