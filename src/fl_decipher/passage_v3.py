"""Offset-preserving abbreviation units and bounded many-to-many local alignment."""
from __future__ import annotations

from array import array
from collections import Counter
from dataclasses import dataclass
import re

from .alignment import features, similarity_features
from .text import Sentence


@dataclass(frozen=True)
class Block:
    atoms: tuple[int, ...]
    spans: tuple[tuple[int, int], ...]
    text: str
    features: dict
    words: Counter


def protected_groups(atoms: list[Sentence], text: str, abbreviations: list[str]) -> list[tuple[int, ...]]:
    """Merge only original sentence ends that are part of a registered abbreviation."""
    pattern = re.compile(r'(?<!\w)(?:' + '|'.join(re.escape(a) for a in abbreviations) + ')', re.I)
    periods = {i + 1 for match in pattern.finditer(text) for i in range(match.start(), match.end()) if text[i] == '.'}
    groups = []
    current = []
    for i, atom in enumerate(atoms):
        current.append(i)
        if atom.end not in periods or i == len(atoms) - 1:
            groups.append(tuple(current))
            current = []
    return groups


def ordered_units(groups: list[tuple[int, ...]], order: list[int]) -> list[tuple[int, ...]]:
    """A protected group survives shuffling only if all its members stay adjacent in order."""
    first = {g[0]: g for g in groups}
    result = []
    i = 0
    while i < len(order):
        group = first.get(order[i], (order[i],))
        if tuple(order[i:i + len(group)]) != group:
            group = (order[i],)
        result.append(group)
        i += len(group)
    return result


def make_block(atoms: list[Sentence], indices: tuple[int, ...]) -> Block:
    chosen = [atoms[i] for i in indices]
    text = ' '.join(s.text for s in chosen)
    ts = tuple(t for s in chosen for t in s.tokens)
    view = Sentence('', text, chosen[0].start, chosen[-1].end, ts)
    return Block(indices, tuple((s.start, s.end) for s in chosen), text,
                 features(view), Counter(t.normalized for t in ts))


class PreparedSource:
    def __init__(self, atoms: list[Sentence], units: list[tuple[int, ...]]):
        self.units = units
        self.blocks = {}
        for size in (1, 2):
            self.blocks[size] = [make_block(atoms, tuple(k for unit in units[j:j + size] for k in unit))
                                 for j in range(len(units) - size + 1)]


class ScoreCache:
    """Cache by actual FL atom order, so shuffled adjacent blocks are scored afresh."""
    def __init__(self, fl_atoms: list[Sentence], source: PreparedSource, cfg: dict, predictions: list[list[dict]]):
        self.fl_atoms, self.source, self.cfg = fl_atoms, source, cfg
        self.predictions = predictions
        self.blocks = {}
        self.rows = {}

    def block(self, ids: tuple[int, ...]) -> Block:
        if ids not in self.blocks:
            self.blocks[ids] = make_block(self.fl_atoms, ids)
        return self.blocks[ids]

    def row(self, ids: tuple[int, ...], source_size: int, scoring: str) -> array:
        key = (ids, source_size)
        if key not in self.rows:
            block = self.block(ids)
            predicted = Counter(p['prediction'] for i in ids for p in self.predictions[i] if p['prediction'] is not None)
            count = sum(predicted.values())
            structural, lexical = array('d'), array('d')
            for target in self.source.blocks[source_size]:
                score = similarity_features(block.features, target.features, self.cfg['weights'])
                anchor = sum(min(n, target.words[w]) for w, n in predicted.items()) / count if count else .5
                structural.append(score)
                lexical.append(self.cfg['structural_weight'] * score + self.cfg['lexical_weight'] * anchor)
            self.rows[key] = {'structural': structural, 'lexical': lexical}
        return self.rows[key][scoring]


def align(fl_units: list[tuple[int, ...]], source: PreparedSource, cache: ScoreCache,
          cfg: dict, *, max_block: int, scoring: str) -> dict:
    n, m = len(fl_units), len(source.units)
    scores = [[0.] * (m + 1) for _ in range(n + 1)]
    trace = [[None] * (m + 1) for _ in range(n + 1)]
    best = (0., 0, 0)
    floor, merge, gap = cfg['match_floor'], cfg['merge_penalty'], cfg['gap_penalty']
    for i in range(1, n + 1):
        available = []
        for a in range(1, min(max_block, i) + 1):
            ids = tuple(k for unit in fl_units[i - a:i] for k in unit)
            for b in range(1, max_block + 1):
                if b <= m:
                    available.append((a, b, ids, cache.row(ids, b, scoring)))
        for j in range(1, m + 1):
            value, move = 0., None
            for a, b, ids, row in available:
                if b > j:
                    continue
                sim = row[j - b]
                reward = (sim - floor) * (a + b) / 2 - merge * (a + b - 2)
                candidate = scores[i - a][j - b] + reward
                if reward > 0 and candidate > value:
                    value, move = candidate, ('block', a, b, sim)
            candidate = scores[i - 1][j] - gap
            if candidate > value:
                value, move = candidate, ('fl_gap', 1, 0, 0.)
            candidate = scores[i][j - 1] - gap
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
            fi = tuple(k for u in fl_units[i - a:i] for k in u)
            si = tuple(k for u in source.units[j - b:j] for k in u)
            f, s = cache.block(fi), source.blocks[b][j - b]
            blocks.append({'fl_atoms': list(fi), 'source_atoms': list(si), 'fl_spans': list(f.spans),
                           'source_spans': list(s.spans), 'fl_effective_units': a, 'source_effective_units': b,
                           'similarity': sim})
            edges.update((x, y) for x in fi for y in si)
        else:
            gaps.append({'side': 'fl' if a else 'source', 'unit_index': i - 1 if a else j - 1})
        i, j = i - a, j - b
    linked = {f for f, _ in edges}
    return {'strength': value / max(n, 1), 'blocks': list(reversed(blocks)), 'gaps': list(reversed(gaps)),
            'edges': [{'fl_index': f, 'source_index': s} for f, s in sorted(edges)],
            'fl_effective_units': n, 'linked_fl_atoms': len(linked),
            'minimum_links_met': len(linked) >= cfg['minimum_fl_atoms']}
