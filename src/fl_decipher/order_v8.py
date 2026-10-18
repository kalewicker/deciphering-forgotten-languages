"""Candidate order evidence from frozen token predictions; no reference inputs."""
from .editorial_v7 import VARIANTS as EDITORIAL_VARIANTS

BACKGROUNDS = [v for v in EDITORIAL_VARIANTS if v['id'] in ('p0_r0_l0', 'p1_r1_l1')]
VARIANTS = [{'id': b['id']+'_order_'+('on' if active else 'off'), 'background': b['id'], 'order': active}
            for b in BACKGROUNDS for active in (False, True)]


def token_objective(predicted, source, cfg):
    """Full inherited global-DP objective, including costs omitted by token output."""
    n, m = len(predicted), len(source)
    gap = cfg['token_gap']
    previous = [j*gap for j in range(m+1)]
    for i, prediction in enumerate(predicted, 1):
        current = [i*gap]
        for j, word in enumerate(source, 1):
            diagonal = (cfg['token_exact'] if prediction == word else cfg['token_mismatch']) if prediction is not None else (
                cfg['token_unknown']-abs((i-.5)/n-(j-.5)/m))
            current.append(max(previous[j-1]+diagonal, previous[j]+gap, current[j-1]+gap))
        previous = current
    return previous[m]


def order_quality(alignment, fl_atoms, source_atoms, ps, cfg):
    covered = set(); blocks = []
    total = sum(len(a.tokens) for a in fl_atoms)
    upper = sum(cfg['token_exact'] if p['prediction'] is not None else cfg['token_unknown'] for row in ps for p in row)
    for block in alignment['blocks']:
        ids = block['fl_atoms']
        assert not covered.intersection(ids), 'Overlapping selected query blocks'
        covered.update(ids)
        predictions = [p['prediction'] for i in ids for p in ps[i]]
        source = [t.normalized for i in block['source_atoms'] for t in source_atoms[i].tokens]
        blocks.append({'fl_atoms': ids, 'source_atoms': block['source_atoms'], 'fl_tokens': len(predictions),
                       'source_tokens': len(source), 'objective': token_objective(predictions, source, cfg)})
    covered_tokens = sum(len(fl_atoms[i].tokens) for i in covered)
    uncovered = total-covered_tokens
    objective = sum(b['objective'] for b in blocks)
    adjusted = objective+cfg['token_gap']*uncovered
    raw = adjusted/upper if upper else 0.
    return {'quality': min(1., max(0., raw)), 'raw_quality': raw, 'upper_bound': upper,
            'block_objective_sum': objective, 'uncovered_query_penalty': cfg['token_gap']*uncovered,
            'adjusted_objective': adjusted, 'covered_query_tokens': covered_tokens,
            'uncovered_query_tokens': uncovered, 'total_query_tokens': total, 'blocks': blocks,
            'evidence': 'Frozen prediction agreement and positional unknowns; not semantic truth'}


def apply_order(alignment, quality, active):
    return {**alignment, 'base_strength': alignment['strength'], 'order_quality': quality,
            'order_applied': active, 'strength': alignment['strength']*quality['quality'] if active else alignment['strength']}
