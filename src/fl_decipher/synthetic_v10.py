"""Fixed content-anchor densities and observable-equivalence stress controls."""
import random
from .content_v10 import CONTENT_FORMS
from .synthetic_v7 import generate as generate_v7, render
from .text import sentences

DENSITIES = [0, 1, 3]
EXTENTS = ['full', 'half']
FAMILIES = ['content_renamed', 'unknown_renamed', 'probe_order']
CONDITIONS = [{'density': d, 'extent': e, 'family': f} for d in DENSITIES for e in EXTENTS for f in FAMILIES]


def generate(seed, density, extent, family, lexicon):
    assert density in DENSITIES and extent in EXTENTS and family in FAMILIES
    initial = generate_v7(seed, 0, lexicon)
    source = sentences(initial['candidate_texts'][initial['answer_index']]); ids = initial['source_token_ids']
    groups = [[(x['uid'], t.normalized) for x, t in zip([x for x in ids if x['atom_index'] == i], a.tokens, strict=True)]
              for i, a in enumerate(source)]
    forms = {**initial['substitution_key'], **CONTENT_FORMS}; words = list(CONTENT_FORMS)
    probes = []; content_uids = []
    for i, g in enumerate(groups):
        positions = [j for j, (_, w) in enumerate(g) if w not in ('the', 'and')][:3]
        probes.append(positions)
        for k, j in enumerate(positions):
            uid = g[j][0]
            if k < density:
                word = words[(i+k)%3]; content_uids.append(uid)
            else:
                word = f'probe{seed}a{i}q{k}'
                forms[word] = f'ž{seed}p{i}q{k}'
                assert forms[word] not in lexicon
            g[j] = (uid, word)
    fl_text, fi = render(groups, forms)
    available = groups if extent == 'full' else groups[:3]
    correct, si = render(available); candidates = [correct]
    for k in (1, 2, 3):
        if family == 'probe_order':
            changed = []
            for i, g in enumerate(available):
                positions = probes[i]; values = [g[j] for j in positions]
                values = values[-k:]+values[:-k] if k < 3 else values[::-1]
                transformed = list(g)
                for j, value in zip(positions, values, strict=True):
                    transformed[j] = value
                changed.append(transformed)
        else:
            keep = {'the', 'and'} | (set(CONTENT_FORMS) if family == 'unknown_renamed' else set())
            vocab = sorted({w for g in available for _, w in g}-keep)
            renamed = {w: f'foil{seed}f{k}x{j}' for j, w in enumerate(vocab)}
            changed = [[(uid, renamed.get(w, w)) for uid, w in g] for g in available]
        candidates.append(render(changed)[0])
    assert len(set(candidates)) == 4, 'Duplicate pool: fail without replacement'
    order = list(range(4)); random.Random(seed+1000000).shuffle(order)
    by_uid = {t['uid']: t for t in si}
    pairs = [{'uid': f['uid'], 'fl_span': f['span'], 'source_span': by_uid[f['uid']]['span'],
              'fl_index': f['atom_index'], 'source_index': by_uid[f['uid']]['atom_index']} for f in fi if f['uid'] in by_uid]
    fa, sa = sentences(fl_text), sentences(correct)
    edges = [{'fl_index': f, 'source_index': s, 'fl_span': [fa[f].start, fa[f].end],
              'source_span': [sa[s].start, sa[s].end], 'state': 'generated_available_occurrence_identity', 'semantic_gold': False}
             for f, s in sorted({(p['fl_index'], p['source_index']) for p in pairs})]
    return {'seed': seed, 'density': density, 'extent': extent, 'family': family, 'fl_text': fl_text,
            'candidate_texts': [candidates[i] for i in order], 'answer_index': order.index(0),
            'candidate_roles': ['correct' if i == 0 else f'{family}_{i}' for i in order],
            'fl_token_ids': fi, 'source_token_ids': si, 'token_pairs': pairs, 'edges': edges,
            'unavailable_query_uids': [f['uid'] for f in fi if f['uid'] not in by_uid],
            'probe_positions': probes, 'content_query_uids': content_uids, 'substitution_key': forms,
            'independent_unit': f'world_{seed}', 'semantic_gold': False}
