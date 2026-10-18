"""Candidate content evidence from fixed emitted predictions, without positional credit."""
from collections import Counter
from .coverage_v9 import BACKGROUNDS, components, factor_quality

CONTENT_FORMS = {'world': 'warċa', 'lord': 'mirnaķ', 'made': 'misndin'}
MODES = ['base', 'positional', 'content_bag', 'content_order']
VARIANTS = [{'id': b['id']+'_'+mode, 'background': b['id'], 'mode': mode} for b in BACKGROUNDS for mode in MODES]


def lcs_length(a, b):
    previous = [0]*(len(b)+1)
    for x in a:
        current = [0]
        for j, y in enumerate(b, 1):
            current.append(previous[j-1]+1 if x == y else max(previous[j], current[j-1]))
        previous = current
    return previous[-1]


def evidence(alignment, fa, sa, ps, cfg):
    positional = components(alignment, fa, sa, ps, cfg)
    blocks = []; denominator = bag = ordered = 0
    for b in alignment['blocks']:
        query = [{'word': p['prediction'], 'span': p['span'], 'atom_index': i} for i in b['fl_atoms'] for p in ps[i]
                 if p['prediction'] in CONTENT_FORMS]
        source = [{'word': t.normalized, 'span': [t.start, t.end], 'atom_index': i} for i in b['source_atoms'] for t in sa[i].tokens
                  if t.normalized in CONTENT_FORMS]
        qw, sw = [x['word'] for x in query], [x['word'] for x in source]
        bm = sum((Counter(qw) & Counter(sw)).values()); om = lcs_length(qw, sw)
        blocks.append({'fl_atoms': b['fl_atoms'], 'source_atoms': b['source_atoms'],
                       'query_content': query, 'source_content': source, 'bag_matches': bm, 'ordered_matches': om})
        denominator += len(query); bag += bm; ordered += om
    return {'positional': positional, 'content': {'blocks': blocks, 'covered_content_predictions': denominator,
            'total_query_content_predictions': sum(p['prediction'] in CONTENT_FORMS for row in ps for p in row),
            'bag_matches': bag, 'ordered_matches': ordered,
            'bag_quality': bag/denominator if denominator else 0., 'ordered_quality': ordered/denominator if denominator else 0.,
            'evidence': 'Fixed roster agreement; no unknown positional or function-word credit; not semantic validation'}}


def mode_quality(e, mode):
    if mode == 'base':
        return 1.
    if mode == 'positional':
        return factor_quality(e['positional'], True, False)['quality']
    if mode == 'content_bag':
        return e['content']['bag_quality']
    if mode == 'content_order':
        return e['content']['ordered_quality']
    raise ValueError(mode)


def apply_mode(alignment, e, mode):
    q = mode_quality(e, mode)
    return {**alignment, 'base_strength': alignment['strength'], 'candidate_evidence': e,
            'mode_quality': q, 'strength': alignment['strength']*q}
