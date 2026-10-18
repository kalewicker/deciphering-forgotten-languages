"""Controlled substitution packets. Gold identities never enter the matcher."""
from __future__ import annotations

import random

from .text import sentences, tokens

FAMILIES = ('diagonal', 'source_split', 'fl_split', 'insertion', 'deletion',
            'abbreviation', 'reordering', 'sparse_anchors')
FUNCTION_FORMS = {'the': 'şu', 'and': 'aš'}


def chunks(items, sizes):
    result, offset = [], 0
    for size in sizes:
        result.append(items[offset:offset+size])
        offset += size
    assert offset == len(items)
    return result


def render(groups, forms=None, abbreviation=False):
    strings, identities = [], []
    for index, group in enumerate(groups):
        words = [(forms[word] if forms else word) for uid, word in group]
        if abbreviation and index == 0:
            assert words[-2:] == ['e', 'g']
            strings.append(' '.join(words[:-2]) + ' e.g.')
        else:
            strings.append(' '.join(words) + '.')
        identities.extend(uid for uid, word in group)
    text = ' '.join(strings)
    ts = tokens(text)
    assert len(ts) == len(identities)
    atoms = sentences(text)
    identity_spans = []
    for uid, token in zip(identities, ts, strict=True):
        atom_index = next(i for i, s in enumerate(atoms) if s.start <= token.start < s.end)
        identity_spans.append({'uid': uid, 'span': [token.start, token.end], 'atom_index': atom_index})
    return text, identity_spans


def generate(seed, family, lexicon):
    if family not in FAMILIES:
        raise ValueError(family)
    rng = random.Random(seed)
    vocabulary = [f'concept{seed}x{k}' for k in range(6)]
    base = []
    for i in range(30):
        # Repetitions and anchors vary by seed, independently of correct candidate position.
        draw = rng.random()
        word = 'the' if draw < .25 else ('and' if draw < .38 else rng.choice(vocabulary))
        if family == 'sparse_anchors' and word in FUNCTION_FORMS:
            word = rng.choice(vocabulary)
        base.append((i, word))
    fl_sizes = [8, 10, 12]
    source_sizes = [8, 10, 12]
    source = list(base)
    if family in ('source_split', 'abbreviation'):
        fl_sizes, source_sizes = [12, 10, 8], [4, 8, 10, 8]
    if family == 'fl_split':
        fl_sizes, source_sizes = [4, 8, 10, 8], [12, 10, 8]
    if family == 'insertion':
        source.insert(5, (None, f'insert{seed}'))
        source_sizes = [9, 10, 12]
    if family == 'deletion':
        source.pop(3)
        source_sizes = [7, 10, 12]
    if family == 'abbreviation':
        base[6:8] = [(6, 'e'), (7, 'g')]
        source = list(base)
        source_sizes = [8, 4, 10, 8]
    source_groups = chunks(source, source_sizes)
    if family == 'reordering':
        source_groups = [source_groups[0], source_groups[2], source_groups[1]]
    forms = dict(FUNCTION_FORMS)
    for k, word in enumerate(sorted({w for _, w in base} - forms.keys())):
        form = f'ž{seed}q{k}a'
        assert form not in lexicon
        forms[word] = form
    fl_text, fl_ids = render(chunks(base, fl_sizes), forms)
    correct_text, source_ids = render(source_groups, abbreviation=family == 'abbreviation')
    candidates = [correct_text]
    for _ in range(3):
        shuffled = []
        for index, group in enumerate(source_groups):
            if family == 'abbreviation' and index == 0:
                prefix = list(group[:-2])
                rng.shuffle(prefix)
                shuffled.append(prefix + group[-2:])
            else:
                copy = list(group)
                rng.shuffle(copy)
                shuffled.append(copy)
        text, _ = render(shuffled, abbreviation=family == 'abbreviation')
        candidates.append(text)
    order = list(range(4))
    rng.shuffle(order)
    answer_index = order.index(0)
    by_uid = {item['uid']: item for item in source_ids if item['uid'] is not None}
    pairs = []
    for f in fl_ids:
        if f['uid'] in by_uid:
            s = by_uid[f['uid']]
            pairs.append({'uid': f['uid'], 'fl_span': f['span'], 'source_span': s['span'],
                          'fl_index': f['atom_index'], 'source_index': s['atom_index']})
    edges = sorted({(p['fl_index'], p['source_index']) for p in pairs})
    fa, sa = sentences(fl_text), sentences(correct_text)
    return {'seed': seed, 'family': family, 'fl_text': fl_text,
            'candidate_texts': [candidates[i] for i in order], 'answer_index': answer_index,
            'token_pairs': pairs, 'fl_token_ids': fl_ids, 'source_token_ids': source_ids,
            'substitution_key': forms,
            'edges': [{'fl_index': f, 'source_index': s, 'fl_span': [fa[f].start, fa[f].end],
                       'source_span': [sa[s].start, sa[s].end], 'state': 'generated_identity',
                       'semantic_gold': False} for f, s in edges]}
