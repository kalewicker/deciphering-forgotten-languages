"""Registered mass normalization and provisional internal token correspondence.

This module consumes only text features and frozen predictions, never gold IDs.
"""
from __future__ import annotations

from collections import defaultdict

from .passage_v3 import align as align_v3


def block_reward(sim, a, b, fl_words, source_words, cfg, mode):
    if mode == 'effective':
        return (sim - cfg['match_floor']) * (a + b) / 2 - cfg['merge_penalty'] * (a + b - 2)
    if mode != 'tokens':
        raise ValueError(mode)
    mass = (fl_words + source_words) / (2 * cfg['reference_tokens'])
    return (sim - cfg['match_floor']) * mass - cfg['merge_penalty'] * max(0., mass - 1.)


def gap_cost(words, cfg, mode):
    return cfg['gap_penalty'] * (words / cfg['reference_tokens'] if mode == 'tokens' else 1.)


def align(fl_units, source, cache, cfg, mode):
    if mode == 'effective':
        return align_v3(fl_units, source, cache, cfg, max_block=2, scoring='lexical')
    n, m = len(fl_units), len(source.units)
    scores = [[0.] * (m + 1) for _ in range(n + 1)]
    trace = [[None] * (m + 1) for _ in range(n + 1)]
    best = (0., 0, 0)
    fl_counts = [sum(len(cache.fl_atoms[k].tokens) for k in u) for u in fl_units]
    source_counts = [sum(source.blocks[1][j].words.values()) for j in range(m)]
    for i in range(1, n + 1):
        available = []
        for a in range(1, min(2, i) + 1):
            ids = tuple(k for u in fl_units[i-a:i] for k in u)
            words = sum(cache.block(ids).words.values())
            for b in (1, 2):
                if b <= m:
                    available.append((a, b, ids, words, cache.row(ids, b, 'lexical')))
        for j in range(1, m + 1):
            value, move = 0., None
            for a, b, ids, words, row in available:
                if b > j:
                    continue
                sim = row[j-b]
                reward = block_reward(sim, a, b, words, sum(source.blocks[b][j-b].words.values()), cfg, mode)
                candidate = scores[i-a][j-b] + reward
                if reward > 0 and candidate > value:
                    value, move = candidate, ('block', a, b, sim)
            candidate = scores[i-1][j] - gap_cost(fl_counts[i-1], cfg, mode)
            if candidate > value:
                value, move = candidate, ('fl_gap', 1, 0, 0.)
            candidate = scores[i][j-1] - gap_cost(source_counts[j-1], cfg, mode)
            if candidate > value:
                value, move = candidate, ('source_gap', 0, 1, 0.)
            scores[i][j], trace[i][j] = value, move
            if value > best[0]:
                best = value, i, j
    value, i, j = best
    blocks, gaps, edges = [], [], set()
    while i and j and scores[i][j] > 0:
        move = trace[i][j]
        if move is None:
            break
        kind, a, b, sim = move
        if kind == 'block':
            fi = tuple(k for u in fl_units[i-a:i] for k in u)
            si = tuple(k for u in source.units[j-b:j] for k in u)
            f, s = cache.block(fi), source.blocks[b][j-b]
            blocks.append({'fl_atoms': list(fi), 'source_atoms': list(si), 'fl_spans': list(f.spans),
                           'source_spans': list(s.spans), 'fl_effective_units': a,
                           'source_effective_units': b, 'similarity': sim})
            edges.update((x, y) for x in fi for y in si)
        else:
            gaps.append({'side': 'fl' if a else 'source', 'unit_index': i-1 if a else j-1})
        i, j = i-a, j-b
    linked = len({f for f, _ in edges})
    return {'strength': value / max(sum(fl_counts) / cfg['reference_tokens'], 1e-12),
            'blocks': list(reversed(blocks)), 'gaps': list(reversed(gaps)),
            'edges': [{'fl_index': f, 'source_index': s} for f, s in sorted(edges)],
            'fl_effective_units': n, 'linked_fl_atoms': linked,
            'minimum_links_met': linked >= cfg['minimum_fl_atoms']}


def token_path(fl_items, source_items, cfg):
    """Global alignment of (atom index, Token, prediction) items to source items."""
    n, m = len(fl_items), len(source_items)
    if not n or not m:
        return []
    gap = cfg['token_gap']
    scores = [[0.] * (m+1) for _ in range(n+1)]
    moves = [[None] * (m+1) for _ in range(n+1)]
    for i in range(1, n+1):
        scores[i][0], moves[i][0] = i*gap, 'f'
    for j in range(1, m+1):
        scores[0][j], moves[0][j] = j*gap, 's'
    def diagonal(i, j):
        prediction = fl_items[i][2]
        if prediction is not None:
            return cfg['token_exact'] if prediction == source_items[j][1].normalized else cfg['token_mismatch']
        return cfg['token_unknown'] - abs((i+.5)/n - (j+.5)/m)
    for i in range(1, n+1):
        for j in range(1, m+1):
            choices = [(scores[i-1][j-1]+diagonal(i-1, j-1), 'd'),
                       (scores[i-1][j]+gap, 'f'), (scores[i][j-1]+gap, 's')]
            scores[i][j], moves[i][j] = max(choices, key=lambda x: x[0])
    pairs = []
    i, j = n, m
    while i or j:
        move = moves[i][j]
        if move == 'd':
            score = diagonal(i-1, j-1)
            fi, f, prediction = fl_items[i-1]
            si, s = source_items[j-1]
            if score >= 0:
                pairs.append({'fl_index': fi, 'source_index': si, 'fl_span': [f.start, f.end],
                              'source_span': [s.start, s.end], 'score': score,
                              'basis': 'frozen_anchor' if prediction is not None else 'positional'})
            i, j = i-1, j-1
        elif move == 'f':
            i -= 1
        elif move == 's':
            j -= 1
        else:
            raise ValueError('Invalid traceback')
    return list(reversed(pairs))


def decode(alignment, fl_atoms, source_atoms, predictions, cfg, mode):
    result = dict(alignment)
    if mode == 'cartesian':
        result['token_pairs'] = None
        return result
    if mode != 'ordered':
        raise ValueError(mode)
    pairs = []
    for block in alignment['blocks']:
        f = [(i, token, p['prediction']) for i in block['fl_atoms']
             for token, p in zip(fl_atoms[i].tokens, predictions[i], strict=True)]
        s = [(i, token) for i in block['source_atoms'] for token in source_atoms[i].tokens]
        pairs.extend(token_path(f, s, cfg))
    evidence = defaultdict(list)
    for pair in pairs:
        evidence[pair['fl_index'], pair['source_index']].append(pair)
    result['edges'] = [{'fl_index': f, 'source_index': s} for (f, s), support in sorted(evidence.items())
                       if len(support) >= cfg['edge_minimum_pairs'] or any(p['basis'] == 'frozen_anchor' for p in support)]
    result['token_pairs'] = pairs
    result['linked_fl_atoms'] = len({e['fl_index'] for e in result['edges']})
    result['minimum_links_met'] = result['linked_fl_atoms'] >= cfg['minimum_fl_atoms']
    return result


def admission(top, margin, threshold):
    return top['minimum_links_met'] and margin > 1e-9 and top['strength'] >= threshold
