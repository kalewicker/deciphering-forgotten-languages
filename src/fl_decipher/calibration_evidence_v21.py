"""Conservative statement-view evidence audit; no lexical or name scoring."""
from collections import defaultdict
import re
from .text import tokens, sentences


def atoms(document):
    blocks = document.get('blocks') or [{'id': 0, 'text': document['text'], 'span': [0, len(document['text'])]}]
    result = []
    for block in blocks:
        assert document['text'][slice(*block['span'])] == block['text']
        for s in sentences(block['text']):
            ts = tokens(s.text, block['span'][0]+s.start)
            result.append({'index': len(result), 'block_id': block['id'], 'text': s.text,
                           'span': [block['span'][0]+s.start, block['span'][0]+s.end],
                           'token_span': [ts[0].start, ts[-1].end],
                           'complete': ts[0].surface[0].isupper() and bool(re.search(r'[.!?][\"”’\']*$', s.text))})
    return result


def locate(locator, document):
    expected = [t.normalized for t in tokens(locator)]
    ts, aa = tokens(document['text']), atoms(document)
    forms = [t.normalized for t in ts]
    result = []
    for i in range(len(ts)-len(expected)+1):
        if not expected or forms[i:i+len(expected)] != expected:
            continue
        window = ts[i:i+len(expected)]
        left = next((j for j, a in enumerate(aa) if a['token_span'][0] == window[0].start), None)
        right = next((j for j, a in enumerate(aa) if a['token_span'][1] == window[-1].end), None)
        group = aa[left:right+1] if left is not None and right is not None and left <= right else []
        cover = bool(group) and [t.normalized for t in tokens(document['text'][group[0]['span'][0]:group[-1]['span'][1]])] == expected
        span = [group[0]['span'][0], group[-1]['span'][1]] if cover else [window[0].start, window[-1].end]
        result.append({'token_span': [window[0].start, window[-1].end], 'statement_span': span if cover else None,
                       'text': document['text'][slice(*span)], 'complete_group': cover and all(a['complete'] for a in group),
                       'atoms': group if cover else [], 'failure': None if cover and all(a['complete'] for a in group) else 'incomplete_atom' if cover else 'partial_statement_match',
                       'tokens': [{'index': j, 'document_token_index': i+j, 'surface': t.surface, 'form': t.normalized,
                                   'span': [t.start, t.end]} for j, t in enumerate(window)]})
    return result


def occurrence_records(spec, side, documents):
    result = []
    for path in spec[side+'_documents']:
        entry = documents[path]
        for occurrence in locate(spec[side+'_locator'], entry['document']):
            result.append({'document_id': entry['document']['id'], 'document': path, **occurrence})
    return result


def audit(specs, documents, target_uid):
    rows = []
    for spec in specs:
        source = occurrence_records(spec, 'source', documents)
        fl = occurrence_records(spec, 'fl', documents)
        fl_counts = {p: sum(o['document'] == p for o in fl) for p in spec['fl_documents']}
        single_source = source[0] if len(source) == 1 else None
        compatible = bool(fl) and len({o['text'] for o in fl}) == 1
        canonical_fl = min(fl, key=lambda o: (o['document_id'], o['document'])) if fl else None
        requirements = {
            'unique_source_occurrence': len(source) == 1,
            'source_complete_statement_group': single_source is not None and single_source['complete_group'],
            'source_provenance_reviewed': all(documents[p]['provenance']['eligible'] for p in spec['source_documents']) and bool(spec['source_documents']),
            'source_expected_component': all(documents[p]['document']['source_group'] in spec['connected_group'] for p in spec['source_documents']),
            'unique_fl_occurrence_per_support_view': bool(fl_counts) and all(n == 1 for n in fl_counts.values()),
            'all_fl_complete_statement_groups': bool(fl) and all(o['complete_group'] for o in fl),
            'fl_support_views_compatible': compatible,
            'fl_historical_provenance_and_article_scope': bool(spec['fl_documents']) and all(documents[p]['provenance']['eligible'] and documents[p]['document']['url'] == spec['article_url'] and documents[p]['document']['source_group'] in spec['connected_group'] for p in spec['fl_documents']),
            'equal_project_token_counts': single_source is not None and canonical_fl is not None and len(single_source['tokens']) == len(canonical_fl['tokens']),
            'target_excluded': spec['uid'] != target_uid,
            'no_observed_order_conflicts': True}
        rows.append({'uid': spec['uid'], 'article': spec['article'], 'connected_group': spec['connected_group'],
                     'source_occurrences': source, 'fl_occurrences': fl, 'fl_support_view_denominator': len(spec['fl_documents']),
                     'fl_occurrences_per_document': fl_counts, 'canonical_source': single_source, 'canonical_fl': canonical_fl,
                     'fl_token_count': len(canonical_fl['tokens']) if canonical_fl else None,
                     'source_token_count': len(single_source['tokens']) if single_source else None,
                     'requirements': requirements, 'order_conflicts': [], 'semantic_gold': False,
                     'current_raw_fl': False, 'semantic_training_eligible': False, 'untouched_test_eligible': False})
    ordering = []
    for i, a in enumerate(rows):
        for b in rows[i+1:]:
            if a['article'] != b['article']:
                continue
            for side in ('source', 'fl'):
                x, y = a['canonical_'+side], b['canonical_'+side]
                if x is None or y is None or not x['complete_group'] or not y['complete_group'] or x['document'] != y['document']:
                    continue
                orderly = x['statement_span'][1] <= y['statement_span'][0]
                check = {'earlier_uid': a['uid'], 'later_uid': b['uid'], 'side': side, 'document': x['document'],
                         'earlier_span': x['statement_span'], 'later_span': y['statement_span'], 'ordered_nonoverlapping': orderly}
                ordering.append(check)
                if not orderly:
                    a['order_conflicts'].append(check);b['order_conflicts'].append(check)
    for row in rows:
        row['requirements']['no_observed_order_conflicts'] = not row['order_conflicts']
        row['gate'] = {'development_packet_eligible': all(row['requirements'].values()),
                       'unmet': [k for k, v in row['requirements'].items() if not v],
                       'semantic_training_eligible': False, 'untouched_test_eligible': False, 'current_raw_reference_eligible': False}
    return {'unit_denominator': len(rows), 'rows': rows, 'order_checks': ordering,
            'eligible_uids': [r['uid'] for r in rows if r['gate']['development_packet_eligible']]}


def packet(row):
    assert row['gate']['development_packet_eligible']
    def ts(side):
        occurrence = row['canonical_'+side]
        return [{'unit_uid': row['uid'], 'document': occurrence['document'], 'index': t['index'], 'surface': t['surface'],
                 'form': t['form'], 'span': t['span'], 'view_surface': t['surface']} for t in occurrence['tokens']]
    return {'uid': row['uid'], 'connected_group': row['connected_group'], 'fl_document': row['canonical_fl']['document'],
            'source_document': row['canonical_source']['document'], 'fl_statement': row['canonical_fl'],
            'source_statement': row['canonical_source'], 'fl_tokens': ts('fl'), 'source_tokens': ts('source'),
            'positional_assumptions_unvalidated': True, 'semantic_gold': False, 'current_raw_fl': False, 'untouched_test_eligible': False}


def assemble(nominees, comparator, config):
    routes = defaultdict(list)
    for origin, result in [('comparator', comparator), ('nominee', nominees)]:
        for row in result['rows']:
            routes[row['uid']].append((origin, row))
    panel, excluded = [], []
    for uid, rr in sorted(routes.items()):
        if not all(r['gate']['development_packet_eligible'] for _, r in rr):
            excluded.append({'uid': uid, 'routes': [{'origin': origin, 'eligible': r['gate']['development_packet_eligible']} for origin, r in rr]})
            continue
        origin, row = rr[0]
        panel.append(packet(row) | {'preferred_route': origin, 'eligible_routes': [o for o, _ in rr]})
    baseline_uids = set(config['comparator_uids'])
    baseline_groups = {tuple(r['connected_group']) for r in comparator['rows']}
    new_rows = [r for r in nominees['rows'] if r['gate']['development_packet_eligible'] and r['uid'] not in baseline_uids]
    new_groups = sorted({tuple(r['connected_group']) for r in new_rows}-baseline_groups)
    all_groups = sorted({tuple(r['connected_group']) for r in panel})
    limits = config['broadening_gate']
    req = {'minimum_new_eligible_units': len(new_rows) >= limits['min_new_eligible_units'],
           'minimum_additional_connected_groups': len(new_groups) >= limits['min_additional_connected_groups'],
           'minimum_total_connected_groups': len(all_groups) >= limits['min_total_connected_groups']}
    decision = {'meaningfully_broader_panel_available': all(req.values()), 'requirements': req,
                'unmet': [k for k, v in req.items() if not v], 'new_eligible_uids': [r['uid'] for r in new_rows],
                'additional_connected_groups': [list(g) for g in new_groups], 'future_panel_groups': [list(g) for g in all_groups],
                'next_step': 'separately_register_unchanged_rule_retest' if all(req.values()) else 'prioritize_evidence_acquisition_and_independent_review',
                'orthographic_rule_executed': False, 'semantic_acceptance': False, 'untouched_test_eligible': False}
    return {'units': panel, 'unit_denominator': len(panel), 'route_failures_retained': excluded,
            'target_excluded': all(r['uid'] != config['excluded_target_uid'] for r in panel), 'decision': decision}
