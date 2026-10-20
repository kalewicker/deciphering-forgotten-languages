"""Fixed five-page numeric comparison; original text spans and all controls retained."""
from collections import Counter
from fl_decipher.scaffold_v46 import anchors, controls, merged, metrics, quote_masks


def representation(scope):
    body = scope['body_text']; units = []; ledger = []; unsupported = []
    for i, run in enumerate(scope['paragraph_runs']):
        span = run['body_span']; text = run['text']
        if run['unit'] != i or not text or body[slice(*span)] != text: raise ValueError('invalid original paragraph run')
        if units and span[0] < units[-1]['span'][1]: raise ValueError('overlapping paragraph runs')
        units.append({'unit': i, 'span': span, 'text': text})
        try: masks = quote_masks(text)
        except ValueError: unsupported.append(i); continue
        ledger += [{'unit': i, 'span': [span[0] + a, span[0] + b], 'reason': 'publisher_quoted_speech'} for a, b in masks]
    masks = merged([r['span'] for r in ledger], len(body))
    available = bool(units) and not unsupported
    return {'available': available, 'units': units, 'quote_mask_ledger': ledger, 'quote_masks': masks,
            'unsupported_quote_units': unsupported, 'inventory': anchors(body, units, masks) if available else None}


def numeric_score(left, right): return metrics(left, right)['number']


def capped_scan(left, right, budget):
    if budget < 1: raise ValueError('positive numeric budget required')
    source = [r for r in right if r['kind'] == 'number']; width = min(len(source), budget)
    windows = []
    for start in range(len(source) - width + 1):
        selected = source[start:start + width]
        windows.append({'numeric_span': [start, start + width], 'anchor_indices': [r['anchor_index'] for r in selected],
                        'scores': numeric_score(left, selected)})
    maximum = max(w['scores']['ordered_lcs'] for w in windows)
    return {'numeric_anchor_count': len(source), 'numeric_budget': budget, 'capped_width': width,
            'window_count': len(windows), 'windows': windows, 'maximum_lcs': maximum,
            'maximizing_starts': [w['numeric_span'][0] for w in windows if w['scores']['ordered_lcs'] == maximum]}


def assessment(left, rep, cfg):
    right = rep['inventory']['anchors']; observed = {'whole': numeric_score(left, right), 'capped_scan': capped_scan(left, right, cfg['numeric_budget'])}
    cases = controls(right, len(rep['units']), cfg['seed'], cfg['draws_per_shuffle_family'])
    ids = list(range(len(right))); bag = Counter(r['key'] for r in right)
    for case in cases:
        rows = [right[i] for i in case['anchor_order']]
        case['index_inventory_preserved'] = sorted(case['anchor_order']) == ids
        case['bag_preserved'] = Counter(r['key'] for r in rows) == bag
        case['whole'] = numeric_score(left, rows); case['capped_scan'] = capped_scan(left, rows, cfg['numeric_budget'])
    selfcopy = {label: numeric_score(rows, rows) for label, rows in [('target', left), ('source', right)]}
    self_ok = all(s['ordered_lcs'] == s['target_count'] == s['source_count'] == s['bag_capacity'] for s in selfcopy.values())
    no_leak = all(not (r['span'][0] < b and r['span'][1] > a) for r in right for a, b in rep['quote_masks'])
    scans = [observed['capped_scan']] + [c['capped_scan'] for c in cases]
    lengths_ok = all(w['scores']['ordered_lcs'] <= w['scores']['bag_capacity'] <= min(w['scores']['target_count'], w['scores']['source_count']) for scan in scans for w in scan['windows'])
    functional = self_ok and no_leak and lengths_ok and all(c['index_inventory_preserved'] and c['bag_preserved'] for c in cases)
    maxima = {f: max(c['capped_scan']['maximum_lcs'] for c in cases if c['family'] == f) for f in cfg['control_families']}
    value = observed['capped_scan']['maximum_lcs']; eligible = functional and observed['whole']['shared_distinct'] >= cfg['minimum_shared_numeric_types']
    return {'observed': observed, 'controls': cases, 'selfcopy_numeric': selfcopy, 'no_source_quote_mask_leakage': no_leak,
        'functional_checks_passed': functional, 'numeric_family_maxima': maxima, 'within_page_order_eligible': eligible,
        'within_page_order_separated': all(value > v for v in maxima.values()) if eligible else None,
        'control_ties': sum(c['capped_scan']['maximum_lcs'] == value for c in cases),
        'controls_greater': sum(c['capped_scan']['maximum_lcs'] > value for c in cases),
        'index_identity_controls': sum(c['index_identity'] for c in cases), 'key_identity_controls': sum(c['key_identity'] for c in cases)}


def panel_decision(reference, comparators, minimum_shared):
    ready = reference is not None and all(c is not None for c in comparators)
    eligible = bool(ready and reference['functional_checks_passed'] and all(c['functional_checks_passed'] for c in comparators)
                    and reference['observed']['whole']['shared_distinct'] >= minimum_shared)
    primary = (all(reference['observed']['capped_scan']['maximum_lcs'] > c['observed']['capped_scan']['maximum_lcs'] for c in comparators)
               if eligible else None)
    whole = (all(reference['observed']['whole']['ordered_lcs'] > c['observed']['whole']['ordered_lcs'] for c in comparators)
             if eligible else None)
    return {'panel_comparison_eligible': eligible, 'registered_capped_specificity_gate': primary,
            'whole_page_specificity_diagnostic': whole}
