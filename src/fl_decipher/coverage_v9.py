"""Factor token-DP agreement and uncovered-query costs without changing search."""
from .order_v8 import BACKGROUNDS, order_quality

VARIANTS = [{'id': f'{b["id"]}_o{int(o)}_c{int(c)}', 'background': b['id'], 'order': o, 'coverage': c}
            for b in BACKGROUNDS for o in (False, True) for c in (False, True)]


def components(alignment, fa, sa, ps, cfg):
    q = order_quality(alignment, fa, sa, ps, cfg)
    covered = {i for b in alignment['blocks'] for i in b['fl_atoms']}
    upper = sum(cfg['token_exact'] if p['prediction'] is not None else cfg['token_unknown'] for i in covered for p in ps[i])
    return {**q, 'covered_upper_bound': upper}


def factor_quality(q, order, coverage):
    numerator = q['block_objective_sum'] if order else q['covered_upper_bound']
    penalty = q['uncovered_query_penalty'] if coverage else 0.
    denominator = q['upper_bound'] if coverage else q['covered_upper_bound']
    raw = (numerator+penalty)/denominator if denominator else 0.
    quality = min(1., max(0., raw)) if order or coverage else 1.
    return {'quality': quality, 'raw_quality': raw if order or coverage else 1.,
            'numerator': numerator, 'penalty': penalty, 'denominator': denominator,
            'order': order, 'coverage': coverage}


def apply_factors(alignment, q, variant):
    f = factor_quality(q, variant['order'], variant['coverage'])
    return {**alignment, 'base_strength': alignment['strength'], 'order_quality': q,
            'factor_quality': f, 'strength': alignment['strength']*f['quality']}
