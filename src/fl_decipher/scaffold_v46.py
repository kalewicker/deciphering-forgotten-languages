"""Literal numeric/uppercase scaffold lengths; no word model or ancestry path."""
from bisect import bisect_left
from collections import Counter
import hashlib
import re
from bs4 import BeautifulSoup


def merged(spans, length):
    out = []
    for a, b in sorted(spans):
        if not 0 <= a <= b <= length:
            raise ValueError('invalid mask span')
        if a == b:
            continue
        if out and a <= out[-1][1]:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return out


def residuals(spans, length):
    out = []; cursor = 0
    for a, b in merged(spans, length):
        if cursor < a:
            out.append([cursor, a])
        cursor = b
    if cursor < length:
        out.append([cursor, length])
    return out


def quote_masks(text):
    curved = list(re.finditer('“[^“”]*”', text)); straight = list(re.finditer(r'"[^"]*"', text))
    if len(curved) != text.count('“') or len(curved) != text.count('”') or len(straight) * 2 != text.count('"'):
        raise ValueError('unsupported or unbalanced source quotation')
    return [[m.start(), m.end()] for m in curved + straight]


def source_units(raw, frozen_body, selector):
    soup = BeautifulSoup(raw, 'html.parser')
    for tag in soup.select('script,style,noscript,template,svg,canvas'):
        tag.decompose()
    bodies = soup.select('body'); containers = soup.select(selector)
    if len(bodies) != 1 or len(containers) != 1 or bodies[0].get_text(' ', strip=True) != frozen_body:
        raise ValueError('source scope/body identity failed')
    units = []; masks = []
    for i, p in enumerate(containers[0].find_all('p', recursive=False)):
        text = p.get_text(' ', strip=True)
        spans = [[m.start(), m.end()] for m in re.finditer(re.escape(text), frozen_body)] if text else []
        if text and len(spans) != 1:
            raise ValueError('source paragraph mapping ambiguous')
        span = spans[0] if spans else None
        units.append({'unit': i, 'span': span, 'text': text})
        for a, b in quote_masks(text):
            masks.append({'unit': i, 'span': [span[0] + a, span[0] + b], 'reason': 'publisher_quoted_speech'})
    if not units:
        raise ValueError('no source paragraphs')
    return units, masks


def anchors(text, units, masks):
    out = []; excluded = []
    word = lambda c: bool(c) and (c.isalnum() or c == '_')
    for kind, pattern in [('number', r'[0-9]+(?:[.,][0-9]+)*'), ('upper', r'[A-Z]{2,}')]:
        for m in re.finditer(pattern, text):
            a, b = m.span()
            scope = [u['unit'] for u in units if u['span'] is not None and u['span'][0] <= a < b <= u['span'][1]]
            if not scope or any(a < y and b > x for x, y in masks):
                continue
            if len(scope) != 1:
                raise ValueError('overlapping source scopes')
            before = text[a - 1] if a else ''; after = text[b] if b < len(text) else ''
            if word(before) or word(after) or (kind == 'number' and before in '.,' and before):
                excluded.append({'kind': kind, 'value': m.group(), 'span': [a, b], 'reason': 'word_or_leading_decimal_boundary'})
                continue
            out.append({'kind': kind, 'value': m.group(), 'key': kind + ':' + m.group(), 'span': [a, b], 'unit': scope[0]})
    out.sort(key=lambda r: (r['span'], r['kind']))
    for i, row in enumerate(out):
        row['anchor_index'] = i
    return {'anchors': out, 'excluded_boundary_candidates': excluded}


def lcs(left, right):
    positions = {}
    for i, value in enumerate(right):
        positions.setdefault(value, []).append(i)
    tails = []
    for value in left:
        for at in reversed(positions.get(value, [])):
            i = bisect_left(tails, at)
            if i == len(tails):
                tails.append(at)
            else:
                tails[i] = at
    return len(tails)


def metrics(left, right):
    out = {}
    for kind in ['number', 'upper', 'combined']:
        a = [r['key'] for r in left if kind == 'combined' or r['kind'] == kind]
        b = [r['key'] for r in right if kind == 'combined' or r['kind'] == kind]
        ca, cb = Counter(a), Counter(b)
        out[kind] = {'target_count': len(a), 'source_count': len(b), 'shared_distinct': len(ca.keys() & cb.keys()),
                     'bag_capacity': sum((ca & cb).values()), 'ordered_lcs': lcs(a, b)}
    return out


def permutation(count, seed, family, draw):
    return sorted(range(count), key=lambda i: (hashlib.sha256(f'{seed}|{family}|{draw}|{i}'.encode()).digest(), i))


def controls(source, unit_count, seed, draws):
    original = list(range(len(source)))
    groups = [[r['anchor_index'] for r in source if r['unit'] == u] for u in range(unit_count)]
    cases = [('reverse', None, list(reversed(original)), None),
             ('within_paragraph_reverse', None, [i for g in groups for i in reversed(g)], list(range(unit_count)))]
    for draw in range(draws):
        cases.append(('anchor_shuffle', draw, permutation(len(source), seed, 'anchor_shuffle', draw), None))
        order = permutation(unit_count, seed, 'paragraph_shuffle', draw)
        cases.append(('paragraph_shuffle', draw, [i for u in order for i in groups[u]], order))
    return [{'family': family, 'draw': draw, 'anchor_order': order, 'unit_order': units,
             'index_identity': order == original, 'key_identity': [source[i]['key'] for i in order] == [r['key'] for r in source]}
            for family, draw, order, units in cases]
