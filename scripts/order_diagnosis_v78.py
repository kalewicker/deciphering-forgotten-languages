"""Freeze and execute E78 once; E77 predictions are read-only inputs."""
import argparse,json,hashlib,math
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
from fl_decipher.order_diagnosis_v78 import status,support,gain,aggregate,macro
ROOT=Path(__file__).resolve().parents[1];OUT='runs/000078_order_diagnosis';REG='experiments/order_diagnosis_v78.json'
CODE=['experiments/order_diagnosis_v78.md','src/fl_decipher/order_diagnosis_v78.py',
      'scripts/order_diagnosis_v78.py','scripts/verify_order_diagnosis_v78.py','tests/test_order_diagnosis_v78.py']
def read(p):return json.loads((ROOT/p).read_text())
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def now():return datetime.now(timezone.utc).isoformat()
def write(p,x):
 p=ROOT/p;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as f:json.dump(x,f,indent=2,ensure_ascii=False);f.write('\n')
def prepare():
 paths=set(CODE)
 for ver in (76,77):
  p=f'reports/0000{ver}_deliverable_seal.json';paths.add(p)
  for name,h in read(p)['deliverable_hashes'].items():assert sha(name)==h,name;paths.add(name)
 write(REG,{'experiment_id':'order_diagnosis_v78','registered_at_utc':now(),
            'input_hashes':{p:sha(p) for p in sorted(paths)},'new_predictions':False})
 print('Frozen read-only diagnostic; no decomposition computed.')
def run():
 reg=read(REG)
 for p,h in reg['input_hashes'].items():assert sha(p)==h,p
 (ROOT/OUT).mkdir(exist_ok=False)
 m={'experiment_id':'order_diagnosis_v78','state':'running','started_at_utc':now(),
    'input_hashes':reg['input_hashes']|{REG:sha(REG)},'new_predictions':False}
 write(OUT+'/manifest.json',m)
 try:
  e77=read('runs/000077_word_order/report.json');gs=[f['group'] for f in e77['folds']]
  units=[r for r in read('runs/000076_order_corpus/unit_ledger.json') if r['exclusion'] is None and r['group'] in gs]
  lookup={r['uid']:r for r in units};folds=[];ledger=[]
  for fi,g in enumerate(gs):
   original=read(f'runs/000077_word_order/fold_{fi:02}.json');vocab=set(original['vocabulary'])
   cat=lambda w:w if w in vocab else '<UNK>'
   wc=Counter();pc=Counter();hc=Counter()
   for r in units:
    if r['group']==g:continue
    for i,t in enumerate(r['tokens']):
     if not t['blocked']:wc[t['form']]+=1
     if t['pair_from_previous']:
      a=cat(r['tokens'][i-1]['form']);b=cat(t['form']);pc[a,b]+=1;hc[a]+=1
   assert vocab=={w for w,c in wc.items() if c>=2}
   rows=[]
   for j,t in enumerate(original['targets']):
    r=lookup[t['uid']];assert r['group']==g
    a=t['context'];b=t['target'];raw=r['tokens'][t['target_index']]
    st=status(wc[raw['form']]);sp=support(hc[a],pc[a,b])
    cell='|'.join(('known' if b!='<UNK>' else 'unknown','known' if a!='<UNK>' else 'unknown',sp))
    value=gain(original['unigram_probabilities'][j],original['observed_probabilities'][j])
    if sp=='unseen_context':assert abs(value)<1e-12
    if sp=='unseen_pair':assert math.isclose(value,math.log2(10/(hc[a]+10)),abs_tol=1e-12)
    binding=r['canonical_binding']
    row={'group':g,'uid':t['uid'],'context_index':t['context_index'],'target_index':t['target_index'],
         'source_path':binding['path'],'target_span':[binding['start']+raw['start'],binding['start']+raw['end']],
         'target_status':st,'context_count':hc[a],'pair_count':pc[a,b],'cell':cell,'gain':value,
         'control_gains':[gain(original['unigram_probabilities'][j],cp[j]) for cp in original['control_probabilities']]}
    rows.append(row)
   agg=aggregate(rows);assert math.isclose(agg['gain'],original['observed']['gain'],abs_tol=1e-12)
   assert math.isclose(agg['known_gain'],original['observed']['known_gain'],abs_tol=1e-12)
   folds.append({'group':g,**agg});ledger+=rows
  report={'experiment_id':'order_diagnosis_v78','folds':folds,'macro_cells':macro(folds),
          'pairs':len(ledger),'groups':len(folds),'original_development_gate':e77['summary']['development_gate'],
          'new_predictions':False,'semantic_benchmark_qualifying_works':0}
  write(OUT+'/target_ledger.json',ledger);write(OUT+'/report.json',report)
  m.update(state='complete',finished_at_utc=now(),output_hashes={OUT+'/'+p:sha(OUT+'/'+p) for p in ['target_ledger.json','report.json']})
  print(json.dumps({k:v for k,v in report.items() if k not in ('folds','macro_cells')},indent=2))
  for c in report['macro_cells']:print(c['cell'],c['count'],round(c['contribution'],9))
 except Exception as e:m.update(state='failed',error=repr(e),finished_at_utc=now());raise
 finally:(ROOT/OUT/'manifest.json').write_text(json.dumps(m,indent=2)+'\n')
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('action',choices=['prepare','run']);a=ap.parse_args();{'prepare':prepare,'run':run}[a.action]()
