"""Exhaustive one-English-token-gap development diagnostic; never select a tie."""
from .transfer_v18 import ratio
from .text import tokens

NAMES = ('primary', 'secondary')
EVIDENCE_REQUIREMENTS = ('source_authority', 'source_statement_complete',
                         'source_continuation_orderly', 'historical_fl_unique_complete')


def gap_gate(reference, fl_count, source_count):
    old = reference['gate']['requirements']
    requirements = {key: old.get(key) is True for key in EVIDENCE_REQUIREMENTS}
    requirements.update(exact_registered_lengths=fl_count == 21 and source_count == 22,
                        single_english_token_excess=source_count == fl_count + 1)
    return {'development_gap_score_eligible': all(requirements.values()),
            'requirements': requirements, 'unmet': [k for k, v in requirements.items() if not v],
            'semantic_training_eligible': False, 'untouched_test_eligible': False}


def alignment(prediction, reference, gap, order=None):
    fl = prediction['tokens']
    english = reference['source_tokens']
    if len(english) != len(fl) + 1:
        raise ValueError('Exactly one excess English token required')
    order = list(range(len(english))) if order is None else list(order)
    if sorted(order) != list(range(len(english))) or any(type(i) is not int for i in order):
        raise ValueError('Source order must be a bijection of original token indices')
    if type(gap) is not int or not 0 <= gap < len(english):
        raise ValueError('Invalid gap position')
    stats = {name: {'predictions': 0, 'abstentions': 0, 'matches': 0, 'conflicts': 0} for name in NAMES}
    historical = reference.get('historical_fl_statement_matches', [])
    historical_tokens = tokens(historical[0]['text'], historical[0]['span'][0]) if len(historical) == 1 else None
    if historical_tokens is not None:
        assert len(historical_tokens) == len(fl)
        assert [t.normalized for t in historical_tokens] == [t['fl_form'] for t in fl]
    rows = []
    for i, token in enumerate(fl):
        j = i + (i >= gap)
        source = english[order[j]]
        row = {'fl_token': {k: token[k] for k in ('uid', 'index', 'fl_form', 'fl_surface', 'fl_span')},
               'fl_document_span': [historical_tokens[i].start, historical_tokens[i].end] if historical_tokens is not None else None,
               'source_position': j, 'source_token': source}
        for name in NAMES:
            value = token[name]['form']
            status = 'abstained' if value is None else 'matched' if value == source['form'] else 'conflict'
            stats[name]['abstentions' if value is None else 'predictions'] += 1
            if value is not None:
                stats[name]['matches' if status == 'matched' else 'conflicts'] += 1
            row[name] = {'prediction': value, 'status': status,
                         'abstention_reason': token[name]['abstention_reason']}
        rows.append(row)
    return {'gap': gap, 'order': order, 'unpaired_source_token': english[order[gap]],
            'fl_token_denominator': len(fl), 'source_token_denominator': len(english),
            'aligned_pairs': len(rows), 'stats': stats, 'rows': rows}


def search(prediction, reference, order=None, *, include_alignments=False):
    alignments = [alignment(prediction, reference, gap, order) for gap in range(len(reference['source_tokens']))]
    curves = [{'gap': a['gap'], **{n: a['stats'][n]['matches'] for n in NAMES}} for a in alignments]
    maxima = {}
    for name in NAMES:
        value = max(c[name] for c in curves)
        gaps = [c['gap'] for c in curves if c[name] == value]
        stats = alignments[0]['stats'][name]
        maxima[name] = {'matches': value, 'gaps': gaps, 'unique': len(gaps) == 1,
                        'predictions': stats['predictions'], 'abstentions': stats['abstentions'],
                        'agreement': ratio(value, stats['predictions'])}
    result = {'gap_denominator': len(curves), 'curve': curves, 'maxima': maxima,
              'maximizer_intersection': sorted(set(maxima['primary']['gaps']) & set(maxima['secondary']['gaps']))}
    if include_alignments:
        result['alignments'] = alignments
    return result


def control_order(name, size):
    sequence = list(range(size))
    if name == 'reverse':
        return sequence[::-1]
    if name not in ('rotate_+1', 'rotate_+2', 'rotate_-1', 'rotate_-2'):
        raise ValueError('Unregistered control')
    k = int(name.split('_')[1]) % size
    return sequence[-k:] + sequence[:-k] if k else sequence


def tail(observed, values):
    ge = sum(v >= observed for v in values)
    return {'greater_or_equal': ge, 'exact_ties': sum(v == observed for v in values),
            'p_one_sided': ratio(1 + ge, 1 + len(values)),
            'null_mean_max_matches': ratio(sum(values), len(values)),
            'null_max_matches': max(values)}
