"""Frozen occurrence selection and complete visual-review accounting, no scoring."""
from collections import Counter
import hashlib

GLYPH_STATUSES = {'literal_match', 'serialization_mismatch', 'unreadable', 'ambiguous'}
CONTEXTS = {'prose', 'figure', 'table', 'header', 'reference', 'ambiguous'}


def select_occurrences(source_id, target, inventory, export, image_digests, radius):
    if radius < 0:
        raise ValueError('negative context radius')
    keys = {r['key'] for r in target if r['kind'] == 'number'}
    units = {u['unit']: u for u in inventory['units']}
    result = []
    for row in inventory['inventory']['anchors']:
        if row['kind'] != 'number' or row['key'] not in keys:
            continue
        page = export['pages'][row['page'] - 1]; text = page['text']
        a, b = row['page_span']; unit = units[row['unit']]
        if (page['page'] != row['page'] or row['key'] != 'number:' + row['value']
                or not 0 <= a < b <= len(text) or text[a:b] != row['value']
                or row['span'] != [unit['span'][0] + a, unit['span'][0] + b]
                or unit['page'] != row['page']
                or hashlib.sha256(text.encode()).hexdigest() != page['text_sha256']
                or image_digests[page['image']] != page['image_sha256']):
            raise ValueError('occurrence/page/text/image identity failed')
        bounds = [max(0, a - radius), min(len(text), b + radius)]
        result.append({'occurrence_id': f"{source_id}:{row['anchor_index']}", 'source_id': source_id,
            'anchor_index': row['anchor_index'], 'key': row['key'], 'value': row['value'], 'page': row['page'],
            'span': row['span'], 'page_span': row['page_span'], 'image': page['image'], 'image_sha256': page['image_sha256'],
            'context_span': bounds, 'context_text': text[slice(*bounds)]})
    if len({r['occurrence_id'] for r in result}) != len(result):
        raise ValueError('duplicate frozen occurrence IDs')
    return result


def summarize(selection, reviews):
    expected = {r['occurrence_id']: r for r in selection}
    if not selection or len(expected) != len(selection):
        raise ValueError('empty or duplicate selection')
    if len(reviews) != len(selection) or {r['occurrence_id'] for r in reviews} != set(expected):
        raise ValueError('review coverage must equal frozen selection')
    for review in reviews:
        frozen = expected[review['occurrence_id']]
        status = review['glyph_status']; literal = review['visible_literal']
        if review['image_sha256'] != frozen['image_sha256'] or status not in GLYPH_STATUSES or review['context'] not in CONTEXTS:
            raise ValueError('invalid image/status/context')
        if not all(isinstance(review[k], str) and review[k].strip() for k in ['locator', 'context_detail', 'note']):
            raise ValueError('review needs locator/context detail/note')
        if status == 'literal_match' and literal != frozen['value']:
            raise ValueError('literal match contradicts frozen value')
        if status == 'serialization_mismatch' and (not isinstance(literal, str) or not literal or literal == frozen['value']):
            raise ValueError('mismatch requires a different literal')
        if status == 'unreadable' and literal is not None:
            raise ValueError('unreadable literal must be null')
        if status == 'ambiguous' and literal is not None and not isinstance(literal, str):
            raise ValueError('ambiguous literal must be null or text')
    glyphs = dict(sorted(Counter(r['glyph_status'] for r in reviews).items()))
    contexts = dict(sorted(Counter(r['context'] for r in reviews).items()))
    gate = False if glyphs.get('serialization_mismatch') else True if glyphs.get('literal_match', 0) == len(selection) else None
    by_source = {}
    for source in sorted({r['source_id'] for r in selection}):
        ids = {r['occurrence_id'] for r in selection if r['source_id'] == source}
        rs = [r for r in reviews if r['occurrence_id'] in ids]
        by_source[source] = {'occurrences': len(rs), 'glyph_status_counts': dict(sorted(Counter(r['glyph_status'] for r in rs).items())),
                             'context_counts': dict(sorted(Counter(r['context'] for r in rs).items()))}
    return {'occurrence_denominator': len(selection), 'page_denominator': len({(r['source_id'], r['page']) for r in selection}),
            'review_coverage_complete': True, 'glyph_status_counts': glyphs, 'context_counts': contexts,
            'literal_glyph_agreement_gate': gate, 'all_contexts_resolved': 'ambiguous' not in contexts, 'by_source': by_source}
