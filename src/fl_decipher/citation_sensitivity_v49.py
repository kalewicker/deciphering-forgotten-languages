"""Original-coordinate citation masks and filtration of frozen control draws."""
from collections import Counter
import re
from fl_decipher.scaffold_v46 import merged

BRACKET_PATTERN = r'\[\s*[0-9]+(?:\s*[,;\-–−]\s*[0-9]+)*\s*\]'


def citation_masks(text, units, boundary):
    page = boundary['page']; offset = boundary['page_offset']; needle = boundary['needle']
    if not 1 <= page <= len(units):
        raise ValueError('invalid boundary page')
    unit = units[page - 1]; a, b = unit['span']; local = text[a:b]
    if not needle or not 0 <= offset < len(local) or local[offset:offset + len(needle)] != needle or local.count(needle) != 1:
        raise ValueError('reference boundary identity failed')
    start = a + offset
    ledger = [{'reason': 'reference_tail', 'span': [start, len(text)], 'boundary_page': page, 'boundary_page_offset': offset}]
    candidates = []
    for u in units:
        x, y = u['span']
        for match in re.finditer(BRACKET_PATTERN, text[x:y]):
            span = [x + match.start(), x + match.end()]
            before = span[1] <= start
            row = {'page': u['page'], 'page_span': list(match.span()), 'span': span, 'text': match.group(),
                   'treatment': 'inline_numeric_bracket' if before else 'covered_by_reference_tail'}
            candidates.append(row)
            if before:
                ledger.append({'reason': 'inline_numeric_bracket', 'span': span, 'page': u['page'], 'page_span': list(match.span())})
    return {'reference_start': start, 'ledger': ledger, 'bracket_candidates': candidates,
            'masks': merged([r['span'] for r in ledger], len(text))}


def filter_inventory(original, masks):
    retained = []; removed = []
    if [r['anchor_index'] for r in original] != list(range(len(original))):
        raise ValueError('original anchor index inventory invalid')
    for row in original:
        if any(row['span'][0] < b and row['span'][1] > a for a, b in masks):
            removed.append(row)
        else:
            retained.append(row | {'original_anchor_index': row['anchor_index'], 'anchor_index': len(retained)})
    return {'anchors': retained, 'removed_anchors': removed}


def filter_controls(original, retained, parent_controls):
    mapping = {r['original_anchor_index']: r['anchor_index'] for r in retained}
    if len(mapping) != len(retained) or [r['anchor_index'] for r in retained] != list(range(len(retained))):
        raise ValueError('retained index inventory invalid')
    out = []; original_ids = list(range(len(original)))
    for parent_index, parent in enumerate(parent_controls):
        if sorted(parent['anchor_order']) != original_ids:
            raise ValueError('parent permutation inventory invalid')
        order = [mapping[i] for i in parent['anchor_order'] if i in mapping]
        rows = [retained[i] for i in order]
        out.append({'parent_control_index': parent_index, 'family': parent['family'], 'draw': parent['draw'],
                    'anchor_order': order, 'unit_order': parent['unit_order'],
                    'index_identity': order == list(range(len(retained))),
                    'key_identity': [r['key'] for r in rows] == [r['key'] for r in retained],
                    'bag_preserved': Counter(r['key'] for r in rows) == Counter(r['key'] for r in retained),
                    'index_inventory_preserved': sorted(order) == list(range(len(retained)))})
    return out
