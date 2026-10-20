"""Prospective harder-comparator supply check; no LCS or semantic evaluation."""
from fl_decipher.additional_intake_v55 import body_text, nominate as old_nominate
from fl_decipher.offline_intake_v54 import evaluate


def nominate(responses, prior):
    # E55 excluded even search-only exposure. E58 expressly permits those leads,
    # retaining tags, while excluding every previously captured page.
    result = old_nominate(responses, {'article_exposures': prior['article_exposures'],
                                     'excluded_article_keys': prior['captured_article_keys']})
    for query in result['queries']:
        for hit in query['hits']:
            if hit['decision_reason'] == 'prior_recorded_url_exposure': hit['decision_reason'] = 'previously_captured_url'
    return result


def native_decision(raw, receipt, spec, rule, route=None):
    result = evaluate(raw, receipt, spec, rule, body_text(raw), route)
    for binding in result['og_url_bindings']:
        if binding['binding'] == 'saved_v53_redirect': binding['binding'] = 'saved_v58_redirect'
    result['route_evidence_origin'] = 'v58' if route is not None else None
    result['exposure_status'] = 'development_data; prior search/link exposure retained'
    return result


def feasibility(native, rep, target, minimum):
    if minimum != 3: raise ValueError('registered minimum is three distinct numeric types')
    available = rep is not None and rep['available']
    shared = None; count = None; passed = None
    if available:
        source_keys = {r['key'] for r in rep['inventory']['anchors'] if r['kind'] == 'number'}
        shared = list(dict.fromkeys(r['key'] for r in target if r['kind'] == 'number' and r['key'] in source_keys))
        count = sum(r['kind'] == 'number' for r in rep['inventory']['anchors']); passed = len(shared) >= minimum
    unmet = list(native['unmet'])
    if not available: unmet.append('numeric_representation_unavailable')
    elif not passed: unmet.append('fewer_than_three_shared_numeric_types')
    return {'numeric_representation_available': available, 'shared_numeric_keys': shared,
        'shared_numeric_key_types': len(shared) if shared is not None else None,
        'candidate_numeric_occurrences': count, 'meets_numeric_overlap_threshold': passed,
        'qualifying_harder_comparator': bool(native['development_capture_eligible'] and passed), 'unmet': unmet}
