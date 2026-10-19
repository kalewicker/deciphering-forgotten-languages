"""Unchanged page-text scope and exhaustive fixed numeric-budget windows."""
import hashlib
from fl_decipher.scaffold_v46 import anchors, metrics


def paper_scope(export, pdf_digest, expected_pages):
    pages = export['pages']
    if export['source_pdf_sha256'] != pdf_digest or len(pages) != expected_pages:
        raise ValueError('PDF identity or page count mismatch')
    if export.get('material_available', True) is not True:
        raise ValueError('PDF material unavailable')
    texts = []; units = []; offset = 0
    for i, page in enumerate(pages):
        text = page['text']
        if page['page'] != i + 1 or hashlib.sha256(text.encode()).hexdigest() != page['text_sha256']:
            raise ValueError('page identity or text hash mismatch')
        units.append({'unit': i, 'page': page['page'], 'span': [offset, offset + len(text)], 'text_length': len(text)})
        texts.append(text); offset += len(text) + 1
    return '\n'.join(texts), units


def paper_inventory(text, units):
    result = anchors(text, units, [])
    for row in result['anchors']:
        unit = units[row['unit']]
        row['page'] = unit['page']
        row['page_span'] = [at - unit['span'][0] for at in row['span']]
    return result


def numeric(rows):
    return [r for r in rows if r['kind'] == 'number']


def windows(target, source, budget):
    if budget < 1:
        raise ValueError('positive anchor budget required')
    left = numeric(target); right = numeric(source); results = []
    for start in range(len(right) - budget + 1):
        selected = right[start:start + budget]
        results.append({'numeric_span': [start, start + budget],
                        'anchor_indices': [r['anchor_index'] for r in selected],
                        'scores': metrics(left, selected)['number']})
    maximum = max((w['scores']['ordered_lcs'] for w in results), default=None)
    return {'numeric_anchor_count': len(right), 'window_count': len(results), 'windows': results,
            'maximum_lcs': maximum,
            'maximizing_starts': [w['numeric_span'][0] for w in results if w['scores']['ordered_lcs'] == maximum]}


def decisions(reference, observed, cases, functional, minimum_shared):
    maxima = {f: max(c['window_scan']['maximum_lcs'] for c in cases if c['family'] == f)
              for f in dict.fromkeys(c['family'] for c in cases)} if observed['window_scan']['maximum_lcs'] is not None else {}
    maximum = observed['window_scan']['maximum_lcs']
    eligible = functional and maximum is not None
    order_eligible = eligible and observed['whole']['shared_distinct'] >= minimum_shared
    return {'length_comparison_eligible': eligible,
            'publisher_strictly_exceeds': reference > maximum if eligible else None,
            'numeric_family_maxima': maxima,
            'within_paper_order_eligible': order_eligible,
            'within_paper_order_separated': all(maximum > x for x in maxima.values()) if order_eligible else None,
            'control_ties': sum(c['window_scan']['maximum_lcs'] == maximum for c in cases) if eligible else None,
            'controls_greater': sum(c['window_scan']['maximum_lcs'] > maximum for c in cases) if eligible else None}
