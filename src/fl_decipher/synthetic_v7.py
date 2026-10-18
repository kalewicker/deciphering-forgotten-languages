"""Paired editorial perturbations with occurrence identities kept out of scoring."""
import random

from .synthetic_v4 import FUNCTION_FORMS
from .text import sentences, tokens

EDITS = ['punctuation', 'parenthetical_insertion', 'repeated_word_insertion', 'lexical_conflict']


def render(groups, forms=None, mask=0, extras=None):
    text_parts, uids = [], []
    for i, group in enumerate(groups):
        pieces = []
        for j, (uid, word) in enumerate(group):
            surface = forms[word] if forms else word
            if forms and mask & 8 and j == 0:
                assert word == 'the'
                surface = FUNCTION_FORMS['and']
            if forms and mask & 1:
                surface += ',' if j == 1 else ';' if j == 5 else ''
            pieces.append(surface)
            uids.append(uid)
            if not forms and mask & 2 and j == 3:
                aside = [f'aside{extras["seed"]}x{i}q{k}' for k in range(4)]
                pieces.append('('+' '.join(aside)+')')
                uids.extend([None]*4)
            if not forms and mask & 4 and j == 5:
                pieces.extend([extras['repeated'][i]]*2)
                uids.extend([None]*2)
        text_parts.append(' '.join(pieces)+'.')
    text = ' '.join(text_parts)
    ts, atoms = tokens(text), sentences(text)
    assert len(ts) == len(uids)
    ids = [{'uid': uid, 'span': [t.start, t.end],
            'atom_index': next(j for j, a in enumerate(atoms) if a.start <= t.start < a.end)}
           for uid, t in zip(uids, ts, strict=True)]
    return text, ids


def generate(seed, mask, lexicon):
    if mask not in range(16):
        raise ValueError(mask)
    rng = random.Random(seed)
    vocabulary = [f'concept{seed}x{k}' for k in range(6)]
    groups, uid = [], 0
    for _ in range(6):
        n = rng.choice([8, 10, 12])
        group = []
        for j in range(n):
            word = 'the' if j == 0 else 'and' if j == n//2 else rng.choice(vocabulary)
            group.append((uid, word)); uid += 1
        groups.append(group)
    forms = {**FUNCTION_FORMS, **{w: f'ž{seed}q{k}a' for k, w in enumerate(vocabulary)}}
    assert all(v not in lexicon for w, v in forms.items() if w not in FUNCTION_FORMS)
    extras = {'seed': seed, 'repeated': [next(w for _, w in g if w not in FUNCTION_FORMS) for g in groups]}
    fl_text, fi = render(groups, forms, mask)
    correct_text, si = render(groups, mask=mask, extras=extras)
    candidates = [correct_text]
    for rotate in (1, 2, 3):
        rotated = [g[-rotate:]+g[:-rotate] for g in groups]
        candidates.append(render(rotated, mask=mask, extras=extras)[0])
    assert len(set(candidates)) == 4, 'Accidental duplicate; fail without replacement'
    order = list(range(4)); rng.shuffle(order)
    by_uid = {t['uid']: t for t in si if t['uid'] is not None}
    pairs = [{'uid': f['uid'], 'fl_span': f['span'], 'source_span': by_uid[f['uid']]['span'],
              'fl_index': f['atom_index'], 'source_index': by_uid[f['uid']]['atom_index']} for f in fi]
    fa, sa = sentences(fl_text), sentences(correct_text)
    edges = [{'fl_index': f, 'source_index': s, 'fl_span': [fa[f].start, fa[f].end],
              'source_span': [sa[s].start, sa[s].end], 'state': 'generated_occurrence_identity', 'semantic_gold': False}
             for f, s in sorted({(p['fl_index'], p['source_index']) for p in pairs})]
    return {'seed': seed, 'mask': mask, 'edits': [e for bit, e in enumerate(EDITS) if mask & (1 << bit)],
            'fl_text': fl_text, 'candidate_texts': [candidates[i] for i in order], 'answer_index': order.index(0),
            'fl_token_ids': fi, 'source_token_ids': si, 'token_pairs': pairs, 'edges': edges,
            'substitution_key': forms, 'conflicted_fl_spans': [f['span'] for f in fi if mask & 8 and f['uid'] in {g[0][0] for g in groups}],
            'independent_unit': f'world_{seed}', 'semantic_gold': False}
