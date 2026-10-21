"""Accounting of fixed prediction gains; no model fitting or prediction."""
from itertools import product
from math import fsum, log2

CELLS=['|'.join(x) for x in product(('known','unknown'),('known','unknown'),
                                  ('unseen_context','unseen_pair','seen_pair'))]

def status(raw_count):
    return 'training_absent' if raw_count == 0 else 'training_singleton' if raw_count == 1 else 'known'

def support(context_count,pair_count):
    assert 0 <= pair_count <= context_count
    return 'unseen_context' if context_count == 0 else 'unseen_pair' if pair_count == 0 else 'seen_pair'

def gain(u,p):
    assert 0 < u <= 1 and 0 < p <= 1
    return log2(p/u)

def aggregate(rows):
    n=len(rows);assert n
    cells=[]
    for key in CELLS:
        selected=[r for r in rows if r['cell']==key]
        total=fsum(r['gain'] for r in selected)
        controls=[fsum(r['control_gains'][d] for r in selected) for d in range(99)]
        cells.append({'cell':key,'count':len(selected),'sum_gain':total,
                      'mean_gain':total/len(selected) if selected else None,'contribution':total/n,
                      'control_sum_gains':controls,'control_contributions':[v/n for v in controls]})
    assert sum(c['count'] for c in cells)==n
    known=[r for r in rows if r['target_status']=='known']
    return {'pairs':n,'cells':cells,'gain':fsum(r['gain'] for r in rows)/n,
            'known_targets':len(known),'known_gain':fsum(r['gain'] for r in known)/len(known) if known else None,
            'target_status_counts':{k:sum(r['target_status']==k for r in rows) for k in ('known','training_singleton','training_absent')}}

def macro(folds):
    return [{'cell':key,'count':sum(f['cells'][i]['count'] for f in folds),
             'contribution':fsum(f['cells'][i]['contribution'] for f in folds)/len(folds),
             'control_contributions':[fsum(f['cells'][i]['control_contributions'][d] for f in folds)/len(folds) for d in range(99)]}
            for i,key in enumerate(CELLS)]
