"""Offline provenance contracts; authority and passage scope are separate gates."""
from collections import Counter


def provenance_gate(*, source_prose, authority_verified, edition_verified,
                    source_scope_matches, extraction_reviewed, passage_reviewed,
                    component_novel):
    values = locals()
    if not all(type(v) is bool for v in values.values()):
        raise ValueError('Evidence gates require explicit booleans')
    return {'eligible': all(values.values()), 'requirements': values,
            'unmet': [k for k, v in values.items() if not v]}


def validate_budget(log, receipts):
    expected = {'liber_azazel', 'vile_darkness'}
    counts = Counter(q['work'] for q in log['queries'])
    assert set(counts) == expected and all(counts[k] == 4 for k in expected)
    routes = log['source_routes']
    assert set(routes) == expected
    assert all(len(v) == len(set(v)) == 4 for v in routes.values())
    allowed = {u for urls in routes.values() for u in urls}
    assert {r['requested_url'] for r in receipts} == allowed
    requests = Counter(r['requested_url'] for r in receipts)
    assert len(receipts) == 9 and len(requests) == 8
    assert sorted(requests.values()) == [1]*7 + [2]
    diagnostic = log['external_diagnostic_url']
    assert requests[diagnostic] == 2
    repeated = [r for r in receipts if r['requested_url'] == diagnostic]
    assert all(r['curl_returncode'] == 6 for r in repeated)


def validate_result(ledger, previous):
    assert ledger['selected_works'] == ledger['selected_queries'] == ledger['selected_components'] == 2
    assert [r['id'] for r in ledger['records']] == [r['id'] for r in previous['records']]
    assert ledger['reference_eligible_queries'] == sum(r['gate']['eligible'] for r in ledger['records'])
    for r, old in zip(ledger['records'], previous['records'], strict=True):
        for key in ('id', 'component', 'fl_url', 'fl_id', 'source_scope', 'fl_whitespace_words', 'fl_atom_count', 'roster_surface_uids'):
            assert r[key] == old[key], key
        assert r['selected_token_count'] == len(old['fl_tokens'])
        assert r['gate'] == provenance_gate(**r['gate']['requirements'])
        if not r['gate']['eligible']:
            assert r['references'] is None and r['lexical_accuracy'] is None and r['controls'] is None
    if ledger['reference_eligible_queries'] == 0:
        assert ledger['evaluated_queries'] == 0 and not ledger['model_executed'] and ledger['metrics'] is None
    return True
