"""Matched negatives; identity and availability references never enter scoring."""
import random
from .synthetic_v7 import generate as generate_v7, render
from .text import sentences

DENSITIES = ['normal', 'zero']
EXTENTS = ['full', 'half']
FAMILIES = ['rotation', 'renamed', 'content_order']
CONDITIONS = [{'density': d, 'extent': e, 'family': f} for d in DENSITIES for e in EXTENTS for f in FAMILIES]


def generate(seed, density, extent, family, lexicon):
    assert density in DENSITIES and extent in EXTENTS and family in FAMILIES
    initial = generate_v7(seed, 0, lexicon)
    source = sentences(initial['candidate_texts'][initial['answer_index']])
    ids = initial['source_token_ids']
    groups = [[(x['uid'], t.normalized) for x, t in zip([x for x in ids if x['atom_index'] == i], a.tokens, strict=True)]
              for i, a in enumerate(source)]
    forms = dict(initial['substitution_key'])
    if density == 'zero':
        forms.update({'the': f'ž{seed}zeroa', 'and': f'ž{seed}zerob'})
        assert forms['the'] not in lexicon and forms['and'] not in lexicon
    fl_text, fi = render(groups, forms)
    available = groups if extent == 'full' else groups[:3]
    correct_text, si = render(available)
    candidates = [correct_text]
    for k in (1, 2, 3):
        if family == 'rotation':
            changed = [g[-k:]+g[:-k] for g in available]
        elif family == 'renamed':
            vocabulary = sorted(w for w in forms if w not in ('the', 'and'))
            renamed = {w: f'foil{seed}f{k}x{j}' for j, w in enumerate(vocabulary)}
            changed = [[(uid, renamed.get(w, w)) for uid, w in g] for g in available]
        else:
            changed = []
            for g in available:
                content = [(uid, w) for uid, w in g if w not in ('the', 'and')]
                rotated = iter(content[-k:]+content[:-k])
                changed.append([(uid, w) if w in ('the', 'and') else next(rotated) for uid, w in g])
        candidates.append(render(changed)[0])
    assert len(set(candidates)) == 4, 'Duplicate negative: fail without replacement'
    order = list(range(4)); random.Random(seed+900000).shuffle(order)
    by_uid = {t['uid']: t for t in si}
    pairs = [{'uid': f['uid'], 'fl_span': f['span'], 'source_span': by_uid[f['uid']]['span'],
              'fl_index': f['atom_index'], 'source_index': by_uid[f['uid']]['atom_index']}
             for f in fi if f['uid'] in by_uid]
    fa, sa = sentences(fl_text), sentences(correct_text)
    edges = [{'fl_index': f, 'source_index': s, 'fl_span': [fa[f].start, fa[f].end],
              'source_span': [sa[s].start, sa[s].end], 'state': 'generated_available_occurrence_identity', 'semantic_gold': False}
             for f, s in sorted({(p['fl_index'], p['source_index']) for p in pairs})]
    return {'seed': seed, 'density': density, 'extent': extent, 'family': family, 'fl_text': fl_text,
            'candidate_texts': [candidates[i] for i in order], 'answer_index': order.index(0),
            'candidate_roles': ['correct' if i == 0 else f'{family}_{i}' for i in order],
            'fl_token_ids': fi, 'source_token_ids': si, 'token_pairs': pairs, 'edges': edges,
            'unavailable_query_uids': [f['uid'] for f in fi if f['uid'] not in by_uid],
            'substitution_key': forms, 'independent_unit': f'world_{seed}', 'semantic_gold': False}
