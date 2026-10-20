"""Exhaustive shared-numeral context accounting; no alignment or meaning inference."""
from collections import Counter
import re

NUMBER = r'[0-9]+(?:[.,][0-9]+)*'
UNIT = r'(?:km(?:³|3|\^3)?|MHz|GHz|Hz|GeV|PeV|EeV|m|°|%)(?!\w)'
SOURCE_CLASSES = {'discrete_count', 'distance_or_length', 'volume', 'angle_or_phase', 'calendar_or_campaign_date', 'other_or_unresolved'}


def overlaps(a, b): return a[0] < b[1] and a[1] > b[0]


def literal_cues(text, span, limit, horizon):
    a, b = span; stop = min(limit, b + horizon); tail = text[b:stop]
    direct = re.match(r'\s*(?P<unit>' + UNIT + ')', tail)
    unit = {'span': [b + direct.start('unit'), b + direct.end('unit')], 'text': direct.group('unit')} if direct else None
    interval = re.match(r'\s*[-–−]\s*(?P<endpoint>' + NUMBER + r')(?:\s*(?P<unit>' + UNIT + '))?', tail)
    ranged = None
    if interval:
        ranged = {'span': [a, b + interval.end()], 'text': text[a:b + interval.end()],
                  'endpoint_span': [b + interval.start('endpoint'), b + interval.end('endpoint')], 'endpoint_value': interval.group('endpoint'),
                  'unit': {'span': [b + interval.start('unit'), b + interval.end('unit')], 'text': interval.group('unit')} if interval.group('unit') else None}
    return {'direct_unit_marker': unit, 'numeric_range_surface': ranged}


def occurrences(text, side, keys, units, mask_ledger, frozen_inventory, radius, horizon):
    if side not in ('target', 'source') or radius < 0 or horizon < 0: raise ValueError('invalid side or context bounds')
    expected = {(tuple(r['span']), r['key']): r for r in frozen_inventory if r['kind'] == 'number' and r['key'] in keys}
    rows = []; retained = set()
    for match in re.finditer(NUMBER, text):
        value = match.group(); key = 'number:' + value
        if key not in keys: continue
        a, b = match.span(); span = [a, b]
        containing = [u for u in units if u['span'] is not None and u['span'][0] <= a < b <= u['span'][1]]
        masked = [r for r in mask_ledger if overlaps(span, r['span'])]
        before = text[a - 1] if a else ''; after = text[b] if b < len(text) else ''
        bad = any(c and (c.isalnum() or c == '_') for c in (before, after)) or bool(before and before in '.,')
        admitted = len(containing) == 1 and not masked and not bad
        anchor = expected.get((tuple(span), key))
        if admitted != (anchor is not None): raise ValueError('frozen retained inventory disagrees with original-span accounting')
        if anchor: retained.add((tuple(span), key))
        status = 'retained' if admitted else 'boundary_rejected' if bad else 'masked' if masked else 'outside_selected_scope'
        context = [max(0, a - radius), min(len(text), b + radius)]
        clipped = [max(context[0], containing[0]['span'][0]), min(context[1], containing[0]['span'][1])] if len(containing) == 1 else None
        cues = literal_cues(text, span, containing[0]['span'][1] if len(containing) == 1 else len(text), horizon)
        rows.append({'occurrence_id': f'{side}:{len(rows):03d}', 'side': side, 'key': key, 'value': value, 'span': span,
            'status': status, 'boundary_rejected': bool(bad), 'containing_unit_ids': [u['unit'] for u in containing],
            'mask_overlaps': masked, 'frozen_anchor_index': anchor['anchor_index'] if anchor else None,
            'context_span': context, 'context_text': text[slice(*context)], 'unit_clipped_context_span': clipped,
            'unit_clipped_context_text': text[slice(*clipped)] if clipped else None, 'literal_cues': cues,
            'glyphs_visually_verified': False, 'quantity_correspondence': 'unresolved', 'opaque_meaning_admitted': False})
    if retained != set(expected): raise ValueError('retained occurrence omitted')
    return rows


def summarize(rows, reviews, texts):
    expected = {r['occurrence_id']: r for r in rows}
    if not rows or len(expected) != len(rows) or len(reviews) != len(rows) or {r['occurrence_id'] for r in reviews} != set(expected):
        raise ValueError('review coverage must equal the complete occurrence inventory')
    for review in reviews:
        row = expected[review['occurrence_id']]; text = texts[row['side']]
        if review['glyph_status'] != 'not_visually_checked' or review['quantity_correspondence'] != 'unresolved' or review['opaque_meaning_admitted'] is not False:
            raise ValueError('review cannot promote glyphs, correspondence or meanings')
        if not isinstance(review['note'], str) or not review['note'].strip(): raise ValueError('review note required')
        allowed = SOURCE_CLASSES if row['side'] == 'source' else {'opaque_context_unresolved'} if row['status'] == 'retained' else {'declared_excluded_context'}
        if review['context_class'] not in allowed: raise ValueError('invalid side-specific context class')
        if not review['evidence']: raise ValueError('exact context evidence required')
        for evidence in review['evidence']:
            a, b = evidence['span']
            if not row['context_span'][0] <= a < b <= row['context_span'][1] or text[a:b] != evidence['text']:
                raise ValueError('context evidence does not match original span')
    by_side = {}
    for side in ['target', 'source']:
        subset = [r for r in rows if r['side'] == side]; ids = {r['occurrence_id'] for r in subset}
        by_side[side] = {'occurrences': len(subset), 'status_counts': dict(sorted(Counter(r['status'] for r in subset).items())),
                         'context_class_counts': dict(sorted(Counter(r['context_class'] for r in reviews if r['occurrence_id'] in ids).items()))}
    keys = list(dict.fromkeys(r['key'] for r in rows)); by_key = []
    for key in keys:
        summary = {'key': key}
        for side in ['target', 'source']:
            subset = [r for r in rows if r['key'] == key and r['side'] == side]
            markers = []
            for r in subset:
                cues = r['literal_cues']; marker = cues['direct_unit_marker']
                if marker: markers.append(marker['text'])
                if cues['numeric_range_surface'] and cues['numeric_range_surface']['unit']: markers.append(cues['numeric_range_surface']['unit']['text'])
            summary[side] = {'all_occurrence_ids': [r['occurrence_id'] for r in subset],
                'retained_occurrence_ids': [r['occurrence_id'] for r in subset if r['status'] == 'retained'],
                'literal_unit_markers': sorted(set(markers))}
        by_key.append(summary)
    return {'occurrence_denominator': len(rows), 'retained_occurrences': sum(r['status'] == 'retained' for r in rows),
        'supplementary_occurrences': sum(r['status'] != 'retained' for r in rows), 'by_side': by_side, 'by_key': by_key,
        'review_coverage_complete': True, 'visual_glyph_agreement_gate': None, 'quantity_correspondence_gate': None,
        'opaque_meanings_admitted': 0, 'source_target_pairs_selected': 0}
