"""Independent E78 reconstruction with no diagnostic/model imports."""
import hashlib,json,math
from collections import Counter
from itertools import product
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT='runs/000078_order_diagnosis/'
def read(p):return json.loads((ROOT/p).read_text())
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def close(a,b):
 if isinstance(a,dict):
  assert a.keys()==b.keys()
  for k in a:close(a[k],b[k])
 elif isinstance(a,list):
  assert len(a)==len(b)
  for x,y in zip(a,b):close(x,y)
 elif isinstance(a,float):assert math.isclose(a,b,rel_tol=1e-11,abs_tol=1e-11),(a,b)
 else:assert a==b,(a,b)
def main():
 reg=read('experiments/order_diagnosis_v78.json');m=read(OUT+'manifest.json')
 assert m['state']=='complete' and m['new_predictions'] is False
 assert reg['registered_at_utc']<m['started_at_utc']<m['finished_at_utc']
 assert m['input_hashes']==reg['input_hashes']|{'experiments/order_diagnosis_v78.json':sha('experiments/order_diagnosis_v78.json')}
 for p,h in (m['input_hashes']|m['output_hashes']).items():assert sha(p)==h,p
 for v in (76,77):
  for p,h in read(f'reports/0000{v}_deliverable_seal.json')['deliverable_hashes'].items():assert sha(p)==h,p
 old=read('runs/000077_word_order/report.json');gs=[f['group'] for f in old['folds']]
 units=[r for r in read('runs/000076_order_corpus/unit_ledger.json') if r['exclusion'] is None and r['group'] in gs]
 lookup={r['uid']:r for r in units};actual=read(OUT+'target_ledger.json');expected=[];folds=[]
 keys=['|'.join(x) for x in product(['known','unknown'],['known','unknown'],['unseen_context','unseen_pair','seen_pair'])]
 for fi,g in enumerate(gs):
  f=read(f'runs/000077_word_order/fold_{fi:02}.json');v=set(f['vocabulary'])
  cat=lambda w:w if w in v else '<UNK>'
  train=[r for r in units if r['group']!=g]
  wc=Counter(t['form'] for r in train for t in r['tokens'] if not t['blocked'])
  assert v=={w for w,n in wc.items() if n>=2}
  pairs=[(cat(r['tokens'][i-1]['form']),cat(t['form'])) for r in train for i,t in enumerate(r['tokens']) if t['pair_from_previous']]
  pc=Counter(pairs);hc=Counter(a for a,b in pairs);rows=[]
  for j,t in enumerate(f['targets']):
   unit=lookup[t['uid']];i=t['target_index'];token=unit['tokens'][i];binding=unit['canonical_binding']
   assert unit['group']==g and t['context_index']==i-1 and token['pair_from_previous']
   a,b=cat(unit['tokens'][i-1]['form']),cat(token['form']);assert (a,b)==(t['context'],t['target'])
   count=wc[token['form']];state='known' if count>=2 else 'training_singleton' if count else 'training_absent'
   kind='seen_pair' if pc[a,b] else 'unseen_pair' if hc[a] else 'unseen_context'
   cell='|'.join(['unknown' if b=='<UNK>' else 'known','unknown' if a=='<UNK>' else 'known',kind])
   u=f['unigram_probabilities'][j];p=f['observed_probabilities'][j]
   value=math.log2(p)-math.log2(u)
   if hc[a]==0:assert abs(value)<1e-11
   if hc[a]>0 and pc[a,b]==0:assert value<0 and math.isclose(value,math.log2(10)-math.log2(hc[a]+10),abs_tol=1e-11)
   rows.append({'group':g,'uid':t['uid'],'context_index':i-1,'target_index':i,'source_path':binding['path'],
    'target_span':[binding['start']+token['start'],binding['start']+token['end']],
    'target_status':state,'context_count':hc[a],'pair_count':pc[a,b],'cell':cell,'gain':value,
    'control_gains':[math.log2(cp[j])-math.log2(u) for cp in f['control_probabilities']]})
  n=len(rows);cells=[]
  for key in keys:
   subset=[r for r in rows if r['cell']==key];total=math.fsum(r['gain'] for r in subset)
   controls=[math.fsum(r['control_gains'][d] for r in subset) for d in range(99)]
   cells.append({'cell':key,'count':len(subset),'sum_gain':total,'mean_gain':total/len(subset) if subset else None,
                 'contribution':total/n,'control_sum_gains':controls,'control_contributions':[c/n for c in controls]})
  known=[r for r in rows if r['target_status']=='known']
  agg={'group':g,'pairs':n,'cells':cells,'gain':math.fsum(r['gain'] for r in rows)/n,
       'known_targets':len(known),'known_gain':math.fsum(r['gain'] for r in known)/len(known) if known else None,
       'target_status_counts':{k:sum(r['target_status']==k for r in rows) for k in ('known','training_singleton','training_absent')}}
  close(agg['gain'],f['observed']['gain']);close(agg['known_gain'],f['observed']['known_gain'])
  for d in range(99):close(math.fsum(c['control_contributions'][d] for c in cells),f['controls'][d]['gain'])
  assert sum(c['count'] for c in cells)==n
  folds.append(agg);expected+=rows
 close(expected,actual)
 macro=[{'cell':key,'count':sum(f['cells'][i]['count'] for f in folds),
         'contribution':math.fsum(f['cells'][i]['contribution'] for f in folds)/13,
         'control_contributions':[math.fsum(f['cells'][i]['control_contributions'][d] for f in folds)/13 for d in range(99)]} for i,key in enumerate(keys)]
 report={'experiment_id':'order_diagnosis_v78','folds':folds,'macro_cells':macro,'pairs':len(expected),'groups':len(folds),
         'original_development_gate':old['summary']['development_gate'],'new_predictions':False,'semantic_benchmark_qualifying_works':0}
 close(report,read(OUT+'report.json'));assert len(expected)==1918 and len(folds)==13
 close(math.fsum(c['contribution'] for c in macro),old['summary']['macro_gain'])
 close(math.fsum(f['known_gain'] for f in folds)/13,old['summary']['macro_known_gain'])
 for d in range(99):close(math.fsum(c['control_contributions'][d] for c in macro),old['summary']['control_macro_gains'][d])
 assert report['original_development_gate'] is False
 print(json.dumps({'verified':True,'targets':len(expected),'groups':13,'cells_per_group':12,
                   'saved_control_draws':99,'gain_values_checked':191800,'original_development_gate':False,'new_predictions':False},indent=2))
if __name__=='__main__':main()
