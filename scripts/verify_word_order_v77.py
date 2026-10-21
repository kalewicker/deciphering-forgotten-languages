"""Independent E77 probability/count reconstruction; no E77 model imports."""
import hashlib,json,math
from collections import Counter,defaultdict
from datetime import datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT='runs/000077_word_order/'
def read(p):return json.loads((ROOT/p).read_text())
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def close(a,b):
 if isinstance(a,dict):
  assert a.keys()==b.keys(),(a.keys(),b.keys())
  for k in a:close(a[k],b[k])
 elif isinstance(a,list):
  assert len(a)==len(b)
  for x,y in zip(a,b):close(x,y)
 elif isinstance(a,float):assert math.isclose(a,b,rel_tol=1e-12,abs_tol=1e-12),(a,b)
 else:assert a==b,(a,b)
def avg(a):return math.fsum(a)/len(a) if a else None
def stats(u,p,known):
 ul=[-math.log(x,2) for x in u];pl=[-math.log(x,2) for x in p]
 return {'unigram_loss':avg(ul),'context_loss':avg(pl),'gain':avg([x-y for x,y in zip(ul,pl)]),
 'known_targets':sum(known),'known_unigram_loss':avg([v for v,k in zip(ul,known) if k]),
 'known_context_loss':avg([v for v,k in zip(pl,known) if k]),
 'known_gain':avg([x-y for x,y,k in zip(ul,pl,known) if k])}
def main():
 reg=read('experiments/word_order_v77.json');m=read(OUT+'manifest.json')
 assert m['state']=='complete'
 assert datetime.fromisoformat(reg['registered_at_utc'])<datetime.fromisoformat(m['started_at_utc'])<datetime.fromisoformat(m['finished_at_utc'])
 assert m['input_hashes']==reg['input_hashes']|{'experiments/word_order_v77.json':sha('experiments/word_order_v77.json')}
 for p,h in (m['input_hashes']|m['output_hashes']).items():assert sha(p)==h,p
 for p,h in read('reports/000076_deliverable_seal.json')['deliverable_hashes'].items():assert sha(p)==h,p
 gs=sorted(g['group'] for g in read('runs/000076_order_corpus/report.json')['groups'] if g['eligible'])
 assert gs==reg['groups'] and len(gs)==13
 rows=[r for r in read('runs/000076_order_corpus/unit_ledger.json') if r['exclusion'] is None and r['group'] in gs]
 assert len(rows)==98
 segs={}
 for r in rows:
  starts=[i for i,t in enumerate(r['tokens']) if not t['blocked'] and not t['pair_from_previous']]
  ss=[]
  for start in starts:
   stop=start+1
   while stop<len(r['tokens']) and r['tokens'][stop]['pair_from_previous']:stop+=1
   ss.append(list(range(start,stop)))
  assert [i for s in ss for i in s]==[i for i,t in enumerate(r['tokens']) if not t['blocked']]
  segs[r['uid']]=ss
 orders=read('data/v77/control_orders.json');assert set(orders)==set(segs)
 for uid,ss in segs.items():
  expected=[[sorted(s,key=lambda i:(hashlib.sha256(f'v77|{d}|{uid}|{s[0]}|{i}'.encode()).hexdigest(),i)) for s in ss] for d in range(99)]
  assert orders[uid]==expected
 computed=[];prob_count=0
 for fi,g in enumerate(gs):
  train=[r for r in rows if r['group']!=g];test=[r for r in rows if r['group']==g]
  wc=Counter(t['form'] for r in train for t in r['tokens'] if not t['blocked'])
  vocab=sorted(w for w,n in wc.items() if n>=2);vs=set(vocab)
  def cat(w):return w if w in vs else '<UNK>'
  count=Counter()
  for w,n in wc.items():count[cat(w)]+=n
  total=sum(count.values());K=len(vocab)+1
  prior={w:(2*count[w]+1)/(2*total+K) for w in vocab+['<UNK>']}
  targets=[]
  for r in test:
   for s in segs[r['uid']]:
    for a,b in zip(s,s[1:]):targets.append({'uid':r['uid'],'context_index':a,'target_index':b,
     'context':cat(r['tokens'][a]['form']),'target':cat(r['tokens'][b]['form'])})
  f=read(OUT+f'fold_{fi:02}.json');assert f['targets']==targets and f['vocabulary']==vocab
  known=[t['target']!='<UNK>' for t in targets];u=[prior[t['target']] for t in targets]
  close(u,f['unigram_probabilities']);allstats=[]
  for d in [-1,*range(99)]:
   outgoing=defaultdict(Counter)
   for r in train:
    ss=segs[r['uid']] if d==-1 else orders[r['uid']][d]
    for s in ss:
     for a,b in zip(s,s[1:]):outgoing[cat(r['tokens'][a]['form'])][cat(r['tokens'][b]['form'])]+=1
   probs=[]
   for t in targets:
    counts=outgoing[t['context']];c=counts[t['target']];n=sum(counts.values())
    # Same model computed using integer-scaled prior rather than runner formula.
    probs.append((c*(2*total+K)+10*(2*count[t['target']]+1))/((n+10)*(2*total+K)))
   close(probs,f['observed_probabilities'] if d==-1 else f['control_probabilities'][d]);prob_count+=len(probs)
   allstats.append(stats(u,probs,known))
  expected={'group':g,'training_groups':[h for h in gs if h!=g],'vocabulary':vocab,'pairs':len(targets),
   'unknown_targets':sum(not k for k in known),'unknown_contexts':sum(t['context']=='<UNK>' for t in targets),
   'observed':allstats[0],'controls':allstats[1:]}
  close(expected,{k:f[k] for k in expected});computed.append(expected)
 report=read(OUT+'report.json');close(computed,report['folds'])
 gains=[f['observed']['gain'] for f in computed];known=[f['observed']['known_gain'] for f in computed]
 macro=avg(gains);kg=avg(known) if all(x is not None for x in known) else None
 controls=[avg([f['controls'][d]['gain'] for f in computed]) for d in range(99)]
 rank=(1+sum(x>=macro for x in controls))/100
 components={'macro_gain_at_least_005':macro>=.05,'positive_at_least_10_groups':sum(x>0 for x in gains)>=10,
 'known_targets_at_least_20_each':all(f['observed']['known_targets']>=20 for f in computed),
 'known_macro_gain_positive':kg is not None and kg>0,'conditional_rank_at_most_005':rank<=.05}
 summary={'groups':13,'pairs':sum(f['pairs'] for f in computed),'macro_gain':macro,'macro_known_gain':kg,
 'positive_groups':sum(x>0 for x in gains),'token_weighted_gain':math.fsum(f['pairs']*f['observed']['gain'] for f in computed)/sum(f['pairs'] for f in computed),
 'control_macro_gains':controls,'conditional_rank':rank,'gate_components':components,'development_gate':all(components.values())}
 assert summary['pairs']==1918;close(summary,report['summary'])
 assert report['semantic_benchmark_qualifying_works']==0 and report['semantic_claims_admitted'] is False
 print(json.dumps({'verified':True,'groups':13,'pairs':1918,'context_probabilities_checked':prob_count,
 'unigram_probabilities_checked':1918,'development_gate':summary['development_gate']},indent=2))
if __name__=='__main__':main()
