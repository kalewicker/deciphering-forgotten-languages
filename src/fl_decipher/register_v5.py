"""Query-only marker gating and explicitly single-work experimental aliases."""
from __future__ import annotations

from collections import Counter

from .lexicon import predict
from .text import sentences

ALIASES = {'ńańi': 'of', 'daċċęįš': 'and', 'tawwdan': 'that'}


def gate(atoms, aliases=ALIASES):
    counts = Counter(t.normalized for s in atoms for t in s.tokens if t.normalized in aliases)
    return {'active': len(counts) >= 2 and sum(counts.values()) >= 3,
            'distinct_markers': len(counts), 'total_markers': sum(counts.values()), 'counts': dict(counts)}


def predictions(atoms, lexicon, rules, variant):
    if variant not in ('baseline', 'universal_aliases', 'gated_aliases'):
        raise ValueError(variant)
    detector = gate(atoms)
    active = variant == 'universal_aliases' or (variant == 'gated_aliases' and detector['active'])
    result = []
    for sentence in atoms:
        row = predict(sentence, lexicon, rules)
        for item in row:
            item['origin'] = 'frozen_v1' if item['prediction'] is not None else 'abstained'
            if active and item['form'] in ALIASES:
                item['baseline_prediction'] = item['prediction']
                item['prediction'] = ALIASES[item['form']]
                item['state'] = 'experimental_single_work_register_hypothesis'
                item['origin'] = 'registered_alias'
        result.append(row)
    return result, detector


def audit_aliases(fl_text, source_text, reference):
    """Presence and positional compatibility are not semantic confirmation."""
    fa, sa = sentences(fl_text), sentences(source_text)
    result = []
    for index, atom in enumerate(fa):
        source_indices = sorted({e['source_index'] for e in reference if e['fl_index'] == index})
        en = [t for j in source_indices for t in sa[j].tokens]
        for position, token in enumerate(atom.tokens):
            if token.normalized not in ALIASES:
                continue
            meaning = ALIASES[token.normalized]
            equal = len(atom.tokens) == len(en)
            present = [t for t in en if t.normalized == meaning]
            result.append({'form': token.normalized, 'proposal': meaning, 'fl_index': index,
                'fl_span': [token.start, token.end], 'source_indices': source_indices,
                'candidate_source_spans': [[t.start, t.end] for t in present],
                'equal_token_count': equal, 'fl_tokens': len(atom.tokens), 'source_tokens': len(en),
                'projected_word': en[position].normalized if equal else None,
                'state': ('equal_length_positional_compatible' if equal and en[position].normalized == meaning
                          else 'equal_length_positional_conflict' if equal
                          else 'source_span_presence_only' if present else 'absent_in_reviewed_source_span'),
                'independent_source_works': 1, 'semantic_gold': False})
    return result


def label_anchor_origins(alignment, query_predictions):
    """Preserve the inherited decoder's decision while naming experimental evidence."""
    for pair in alignment['token_pairs']:
        if pair['basis'] != 'frozen_anchor':
            pair['anchor_origin'] = 'positional'
            continue
        item = next(p for p in query_predictions[pair['fl_index']] if p['span'] == pair['fl_span'])
        pair['anchor_origin'] = item['origin']
        if item['origin'] == 'registered_alias':
            pair['basis'] = 'experimental_alias'
    return alignment
