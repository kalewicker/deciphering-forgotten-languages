"""Independent grouped reconstruction; exact rational guarded probabilities."""
import hashlib,json,math
from collections import Counter,defaultdict
from fractions import Fraction
from pathlib import Path
from verify_word_order_v77 import close,stats
ROOT=Path(__file__).resolve().parents[1];OUT='runs/000079_context_guard/'
def read(p):return json.loads((ROOT/p).read_text())
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def avg(xs):return math.fsum(xs)/len(xs) if xs else None
def main():
 reg=read('experiments/context_guard_v79.json');m=read(OUT+'manifest.json')
 assert m['state']=='complete' and reg['registered_at_utc']<m['started_at_utc']<m['finished_at_utc']
 assert m['input_hashes']==reg['input_hashes']|{'experiments/context_guard_v79.json':sha('experiments/context_guard_v79.json')}
 for p,h in (m['input_hashes']|m['output_hashes']).items():assert sha(p)==h,p
 for v in (76,77,78):
  for p,h in read(f'reports/0000{v}_deliverable_seal.json')['deliverable_hashes'].items():assert sha(p)==h,p
 old=read('runs/000077_word_order/report.json');gs=[f['group'] for f in old['folds']]
 rows=[r for r in read('runs/000076_order_corpus/unit_ledger.json') if r['exclusion'] is None and r['group'] in gs]
 assert len(gs)==13 and len(rows)==98
 segs={}
 for r in rows:
  starts=[i for i,t in enumerate(r['tokens']) if not t['blocked'] and not t['pair_from_previous']]
  parts=[]
  for i in starts:
   end=i+1
   while end<len(r['tokens']) and r['tokens'][end]['pair_from_previous']:end+=1
   parts.append(list(range(i,end)))
  assert [i for p in parts for i in p]==[i for i,t in enumerate(r['tokens']) if not t['blocked']]
  segs[r['uid']]=parts
 orders=read('data/v77/control_orders.json')
 assert set(orders)==set(segs)
 for uid,parts in segs.items():
  assert orders[uid]==[[sorted(p,key=lambda i:(hashlib.sha256(f'v77|{d}|{uid}|{p[0]}|{i}'.encode()).hexdigest(),i)) for p in parts] for d in range(99)]
 computed=[];checked=0;distribution_checks=0
 for fi,g in enumerate(gs):
  train=[r for r in rows if r['group']!=g];test=[r for r in rows if r['group']==g]
  wc=Counter(t['form'] for r in train for t in r['tokens'] if not t['blocked'])
  vocab=sorted(w for w,n in wc.items() if n>=2);vs=set(vocab)
  cat=lambda w:w if w in vs else '<UNK>'
  counts=Counter()
  for w,n in wc.items():counts[cat(w)]+=n
  total=sum(counts.values());K=len(vocab)+1
  prior={w:Fraction(2*counts[w]+1,2*total+K) for w in vocab+['<UNK>']}
  targets=[]
  for r in test:
   for part in segs[r['uid']]:
    for a,b in zip(part,part[1:]):targets.append({'uid':r['uid'],'context_index':a,'target_index':b,
       'context':cat(r['tokens'][a]['form']),'target':cat(r['tokens'][b]['form'])})
  f=read(OUT+f'fold_{fi:02}.json');previous=read(f'runs/000077_word_order/fold_{fi:02}.json')
  assert targets==f['targets']==previous['targets'] and vocab==f['vocabulary']==previous['vocabulary']
  u=[float(prior[t['target']]) for t in targets];close(u,f['unigram_probabilities']);close(u,previous['unigram_probabilities'])
  known=[t['target']!='<UNK>' for t in targets];results=[];support=None;eligible_original=None
  for d in [-1,*range(99)]:
   pairs=defaultdict(Counter);support_groups=defaultdict(set)
   for r in train:
    for part in (segs[r['uid']] if d==-1 else orders[r['uid']][d]):
     for a,b in zip(part,part[1:]):
      h=r['tokens'][a]['form'];w=r['tokens'][b]['form']
      if h in vs and w in vs:pairs[h][w]+=1;support_groups[h].add(r['group'])
   ns={h:sum(c.values()) for h,c in pairs.items()}
   eligible={h for h in ns if ns[h]>=5 and len(support_groups[h])>=2}
   distributions={}
   for h in eligible:
    n=ns[h];q=1-prior['<UNK>']
    # Simplified exact formula: ((n+20)*U(w)+q*c(h,w))/(2*(n+10)).
    distribution={w:((n+20)*prior[w]+q*pairs[h][w])/(2*(n+10)) for w in vocab}
    distribution['<UNK>']=prior['<UNK>']
    assert sum(distribution.values())==1 and all(p>0 for p in distribution.values())
    for w in vocab:
     if not pairs[h][w]:assert distribution[w]/prior[w]==Fraction(1,2)+Fraction(5,n+10)
    distributions[h]=distribution;distribution_checks+=1
   ps=[float(distributions.get(t['context'],prior)[t['target']]) for t in targets]
   saved=f['observed_probabilities'] if d==-1 else f['control_probabilities'][d]
   close(ps,saved);checked+=len(ps)
   for j,t in enumerate(targets):
    if t['target']=='<UNK>' or t['context'] not in eligible:assert saved[j]==f['unigram_probabilities'][j]
   results.append(stats(u,ps,known))
   if d==-1:
    support={h:{'known_transitions':ns[h],'groups':sorted(support_groups[h]),'eligible':h in eligible} for h in sorted(ns)}
    eligible_original=eligible
  assert f['context_support']==support
  expected={'group':g,'training_groups':[h for h in gs if h!=g],'vocabulary':vocab,'pairs':len(targets),
    'unknown_targets':sum(not k for k in known),'unknown_contexts':sum(t['context']=='<UNK>' for t in targets),
    'eligible_evaluation_contexts':sum(t['context'] in eligible_original for t in targets),
    'eligible_known_target_pairs':sum(t['context'] in eligible_original and t['target']!='<UNK>' for t in targets),
    'gain_change_from_e77':results[0]['gain']-previous['observed']['gain'],'observed':results[0],'controls':results[1:]}
  close(expected,{k:f[k] for k in expected});computed.append(expected)
 report=read(OUT+'report.json');close(computed,report['folds'])
 gains=[f['observed']['gain'] for f in computed];kg=[f['observed']['known_gain'] for f in computed]
 macro=avg(gains);known_macro=avg(kg) if all(x is not None for x in kg) else None
 controls=[avg([f['controls'][d]['gain'] for f in computed]) for d in range(99)]
 rank=(1+sum(x>=macro for x in controls))/100
 components={'macro_gain_at_least_005':macro>=.05,'positive_at_least_10_groups':sum(x>0 for x in gains)>=10,
 'known_targets_at_least_20_each':all(f['observed']['known_targets']>=20 for f in computed),
 'known_macro_gain_positive':known_macro is not None and known_macro>0,'conditional_rank_at_most_005':rank<=.05}
 summary={'groups':13,'pairs':sum(f['pairs'] for f in computed),'macro_gain':macro,'macro_known_gain':known_macro,
 'positive_groups':sum(x>0 for x in gains),'token_weighted_gain':math.fsum(f['pairs']*f['observed']['gain'] for f in computed)/sum(f['pairs'] for f in computed),
 'control_macro_gains':controls,'conditional_rank':rank,'gate_components':components,'development_gate':all(components.values())}
 assert summary['pairs']==1918;close(summary,report['summary'])
 assert report['engineering_requirements_passed'] is True and report['e77_development_gate'] is False
 assert report['adaptive_development'] is True and report['semantic_benchmark_qualifying_works']==0 and report['semantic_claims_admitted'] is False
 print(json.dumps({'verified':True,'groups':13,'targets':1918,'context_probabilities_checked':checked,
                   'unigram_probabilities_checked':1918,'exact_distribution_checks':distribution_checks,
                   'development_gate':summary['development_gate'],'engineering_requirements_passed':True},indent=2))
if __name__=='__main__':main()
