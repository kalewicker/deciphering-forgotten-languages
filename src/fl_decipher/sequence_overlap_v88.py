"""Exact cross-group window accounting; consumes saved gains, fits no model."""
from collections import defaultdict
from math import fsum

LENGTHS = tuple(range(2, 9))
BINS = (0, *LENGTHS)


def segments(row):
    result = []
    for i, token in enumerate(row['tokens']):
        if token['blocked']:
            assert not token['pair_from_previous']
            continue
        if not token['pair_from_previous']:
            result.append([])
        else:
            assert i and not row['tokens'][i-1]['blocked']
            assert result and result[-1][-1] == i-1
        result[-1].append(i)
    return result


def windows(rows):
    for row in rows:
        for segment in segments(row):
            for n in LENGTHS:
                for start in range(len(segment)-n+1):
                    indices = segment[start:start+n]
                    yield n, tuple(row['tokens'][i]['form'] for i in indices), row['uid'], indices


def matches(evaluation, training):
    index = defaultdict(list)
    for n, forms, uid, indices in windows(training):
        index[n, forms].append((uid, indices))
    result = []
    for n, forms, uid, indices in windows(evaluation):
        for other_uid, other_indices in index[n, forms]:
            result.append({'length': n, 'evaluation_uid': uid, 'evaluation_indices': indices,
                           'training_uid': other_uid, 'training_indices': other_indices})
    return sorted(result, key=match_key)


def match_key(m):
    return (m['length'], m['evaluation_uid'], m['evaluation_indices'],
            m['training_uid'], m['training_indices'])


def coverage(occurrences):
    result = defaultdict(set)
    for m in occurrences:
        for a, b in zip(m['evaluation_indices'], m['evaluation_indices'][1:]):
            result[m['evaluation_uid'], a, b].add(m['length'])
    return result


def totals(rows, denominator):
    assert denominator > 0
    gain = fsum(r['gain'] for r in rows)
    positive = fsum(max(0., r['gain']) for r in rows)
    negative = fsum(min(0., r['gain']) for r in rows)
    return {'pairs': len(rows), 'changed_predictions': sum(r['changed'] for r in rows),
            'gain_sum': gain, 'positive_gain_sum': positive, 'negative_gain_sum': negative,
            'mean_gain': gain/len(rows) if rows else None,
            'contribution': gain/denominator,
            'positive_contribution': positive/denominator,
            'negative_contribution': negative/denominator}


def aggregate(rows):
    n = len(rows)
    return {'pairs': n, 'total': totals(rows, n),
            'lengths': {str(k): {label: totals([r for r in rows if (k in r['covered_lengths']) == covered], n)
                                for label, covered in [('covered', True), ('uncovered', False)]}
                       for k in LENGTHS},
            'max_bins': {str(k): totals([r for r in rows if r['max_covered_length'] == k], n) for k in BINS}}


def macro(folds):
    def combine(items):
        return {'pairs': sum(x['pairs'] for x in items),
                'changed_predictions': sum(x['changed_predictions'] for x in items),
                **{k: fsum(x[k] for x in items)/len(items) for k in
                   ['contribution', 'positive_contribution', 'negative_contribution']}}
    total = combine([f['total'] for f in folds])
    lengths = {}
    for k in LENGTHS:
        cells = {label: combine([f['lengths'][str(k)][label] for f in folds])
                 for label in ['covered', 'uncovered']}
        cells['positive_mass_fraction_covered'] = (cells['covered']['positive_contribution']/total['positive_contribution']
                                                   if total['positive_contribution'] else None)
        lengths[str(k)] = cells
    return {'total': total, 'lengths': lengths,
            'max_bins': {str(k): combine([f['max_bins'][str(k)] for f in folds]) for k in BINS}}
