"""Fixed occurrence-preserving anchor corruption and deterministic prediction lures."""
import random
from .content_v10 import CONTENT_FORMS
from .synthetic_v10 import generate as generate_v10
from .synthetic_v7 import render
from .text import sentences

SETTINGS = [{'density': 0, 'corruption': 'clean'}] + [{'density': 3, 'corruption': c} for c in
            ('clean', 'conflict_one', 'conflict_all', 'omit_one', 'omit_all')]
FAMILIES = ['content_renamed', 'prediction_lure']
CONDITIONS = [s | {'extent': e, 'family': f} for s in SETTINGS for e in ('full', 'half') for f in FAMILIES]


def generate(seed, density, corruption, extent, family, lexicon):
    assert {'density': density, 'corruption': corruption} in SETTINGS
    assert extent in ('full', 'half') and family in FAMILIES
    initial = generate_v10(seed, density, 'full', 'content_renamed', lexicon)
    atoms = sentences(initial['candidate_texts'][initial['answer_index']]); ids = initial['source_token_ids']
    groups = [[(x['uid'], t.normalized) for x, t in zip([x for x in ids if x['atom_index'] == i], a.tokens, strict=True)]
              for i, a in enumerate(atoms)]
    words = list(CONTENT_FORMS); inverse = {v: k for k, v in CONTENT_FORMS.items()}
    surfaces = []; expectations = {}; evidence = []
    for i, g in enumerate(groups):
        out = []
        for j, (uid, truth) in enumerate(g):
            surface = initial['substitution_key'][truth]
            selected = truth in CONTENT_FORMS and (corruption.endswith('_all') or
                       (corruption.endswith('_one') and j == initial['probe_positions'][i][0]))
            if selected and corruption.startswith('conflict'):
                surface = CONTENT_FORMS[words[(words.index(truth)+1)%3]]
            elif selected and corruption.startswith('omit'):
                surface = f'ž{seed}omit{uid}'
                assert surface not in lexicon
            expected = inverse.get(surface)
            expectations[uid] = expected
            if truth in CONTENT_FORMS:
                evidence.append({'uid': uid, 'atom_index': i, 'truth_word': truth, 'expected_prediction': expected,
                                 'surface': surface, 'changed': selected, 'kind': corruption if selected else 'clean'})
            out.append((uid, surface))
        surfaces.append(out)
    fl_text, fi = render(surfaces)
    by_fl_uid = {x['uid']: x for x in fi}
    for e in evidence:
        e['fl_span'] = by_fl_uid[e['uid']]['span']
    available = groups if extent == 'full' else groups[:3]
    correct, si = render(available); candidates = [correct]
    for k in (1, 2, 3):
        changed = []
        unknown = sorted({w for g in available for _, w in g if w not in ('the', 'and') and w not in CONTENT_FORMS})
        renamed = {w: f'foil{seed}f{k}x{j}' for j, w in enumerate(unknown)}
        if family == 'content_renamed':
            vocab = sorted({w for g in available for _, w in g}-{'the', 'and'})
            replacements = {w: f'foil{seed}f{k}x{j}' for j, w in enumerate(vocab)}
            changed = [[(uid, replacements.get(w, w)) for uid, w in g] for g in available]
        else:
            for i, g in enumerate(available):
                row = []
                for j, (uid, truth) in enumerate(g):
                    if j in initial['probe_positions'][i]:
                        expected = expectations[uid]
                        if k == 1:
                            word = expected if expected is not None else f'lure{seed}f{k}u{uid}'
                        elif expected is not None or truth in CONTENT_FORMS:
                            original = expected if expected is not None else truth
                            word = words[(words.index(original)+k-1)%3]
                        else:
                            word = f'lure{seed}f{k}u{uid}'
                    else:
                        word = renamed.get(truth, truth)
                    row.append((uid, word))
                changed.append(row)
        candidates.append(render(changed)[0])
    assert len(set(candidates)) == 4, 'Duplicate pool: fail without replacement'
    agreements = []
    for candidate in candidates:
        ca = sentences(candidate); known = matched = 0
        for i, g in enumerate(available):
            for j, (uid, _) in enumerate(g):
                expected = expectations[uid]
                if expected is not None:
                    known += 1
                    matched += ca[i].tokens[j].normalized == expected
        agreements.append({'known_content_predictions': known, 'matches_at_truth_positions': matched})
    order = list(range(4)); random.Random(seed+1100000).shuffle(order)
    by_uid = {t['uid']: t for t in si}
    pairs = [{'uid': f['uid'], 'fl_span': f['span'], 'source_span': by_uid[f['uid']]['span'],
              'fl_index': f['atom_index'], 'source_index': by_uid[f['uid']]['atom_index']} for f in fi if f['uid'] in by_uid]
    fa, sa = sentences(fl_text), sentences(correct)
    edges = [{'fl_index': f, 'source_index': s, 'fl_span': [fa[f].start, fa[f].end], 'source_span': [sa[s].start, sa[s].end],
              'state': 'generated_available_occurrence_identity', 'semantic_gold': False}
             for f, s in sorted({(p['fl_index'], p['source_index']) for p in pairs})]
    return {'seed': seed, 'density': density, 'corruption': corruption, 'extent': extent, 'family': family,
            'fl_text': fl_text, 'candidate_texts': [candidates[i] for i in order], 'answer_index': order.index(0),
            'candidate_content_agreements': [agreements[i] for i in order],
            'candidate_roles': ['correct' if i == 0 else f'{family}_{i}' for i in order],
            'fl_token_ids': fi, 'source_token_ids': si, 'token_pairs': pairs, 'edges': edges,
            'unavailable_query_uids': [f['uid'] for f in fi if f['uid'] not in by_uid],
            'content_query_uids': initial['content_query_uids'], 'probe_positions': initial['probe_positions'],
            'content_truth': evidence, 'substitution_key': initial['substitution_key'],
            'independent_unit': f'world_{seed}', 'semantic_gold': False}
