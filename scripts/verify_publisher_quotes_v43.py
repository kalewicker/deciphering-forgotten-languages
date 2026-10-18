"""Offline whole-query accounting and frozen-result comparison verification."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from verify_correspondence_v6 import check_hashes
from verify_native_quote_v42 import hits


def read(path):
    return json.loads((ROOT / path).read_text())


def sha(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def main():
    run = ROOT / 'runs/000043_publisher_quotes'
    check_hashes(run)
    cfg = read('experiments/publisher_quotes_v43.json'); pre = read('data/v43/preflight.json')
    for path, expected in pre['hashes'].items():
        assert sha(path) == expected, path
    assert all(pre['hashes'][p] == h for p, h in cfg['input_hashes'].items())
    assert pre['hashes']['experiments/publisher_quotes_v43.json'] == sha('experiments/publisher_quotes_v43.json')
    manifest = read('runs/000043_publisher_quotes/manifest.json')
    assert cfg['registered_at_utc'] < pre['sealed_at_utc'] < manifest['finished_at_utc']
    assert cfg['request_budget'] == 0
    assert cfg['query_ids'] == [f'quote{i:02d}' for i in range(8)]
    assert cfg['remaining_long_query_ids'] == [f'quote{i:02d}' for i in range(2, 8)]
    frozen = read('data/v43/frozen_queries.json')
    queries = read('data/v39/frozen_queries.json')['queries']
    assert frozen['queries'] == queries and frozen['source'] == cfg['source_text']
    old38 = read('data/v38/observable_scope.json')
    assert queries == [{k: q[k] for k in ['quote_id', 'span', 'text', 'language_or_meaning_admitted']} for q in old38['quotes']]
    target = read('data/v38/target_export.json')['text']
    for q in queries:
        assert target[slice(*q['span'])] == q['text']
    text = (ROOT / cfg['source_text']).read_text()
    assert text == read('data/v42/page_observations.json')['text'] and len(text) == cfg['expected_source_characters'] == 12072
    assert read('data/v42/page_observations.json')['material_available']
    a = read('data/v43/assessment.json'); report = read('runs/000043_publisher_quotes/report.json')
    assert a['material_available'] and a['source_extraction_complete'] and a['source_page_denominator'] == 1
    assert a['quote_denominator'] == 8 and a['long_quote_denominator'] == 7 and len(a['quotes']) == 8
    for q, row in zip(queries, a['quotes'], strict=True):
        assert all(row[k] == v for k, v in q.items())
        assert len(row['page_results']) == 1
        unit = row['page_results'][0]
        assert unit['page'] == 1 and unit['text_available']
        hits(q['text'], text, unit['hits'])
        assert row['source_hits'] == [{'page': 1, **h} for h in unit['hits']]
        assert unit['literal_presence'] == row['literal_source_presence'] == bool(unit['hits'])
    flags = [q['literal_source_presence'] for q in a['quotes']]
    assert a['quotes_with_literal_source_presence'] == sum(flags) == 2
    assert flags == [True, True, False, False, False, False, False, False]
    assert a['long_quotes_with_literal_presence'] == sum(v for i, v in enumerate(flags) if i != 1) == 1
    assert a['query_outcomes_unavailable'] == 0 and a['primary_long_block_presence'] and a['expanded_name_literal_presence']
    assert len(a['positive_controls']) == a['positive_controls_passed'] == 1 and a['positive_controls_unavailable'] == 0
    control = a['positive_controls'][0]
    assert control['query'] == text.splitlines()[0] == text and control['passed'] and control['page'] == 1
    hits(control['query'], text, control['own_page_hits'])
    negative = a['negative_control']
    assert negative['query'] == 'flv38literalabsencecontrol20261018' and negative['passed'] and negative['source_hits'] == []
    hits(negative['query'], text, [])
    assert a['anchors'] == [] and a['opaque_passages_scored'] == 0 and a['semantic_evaluation_metrics'] is None
    assert report['source_unit_denominator'] == 1 and report['source_characters'] == len(text)
    assert report['source_material_available'] and report['quote_denominator'] == 8 and report['long_quote_denominator'] == 7
    assert report['complete_quotes_present'] == sum(flags) and report['long_quotes_present'] == 1
    assert report['query_outcomes_unavailable'] == 0 and report['known_positive_query'] == 'quote00' and report['known_positive_passed']
    assert report['primary_readout_valid'] and report['expanded_name_present']
    assert report['remaining_long_quote_denominator'] == 6 and report['remaining_long_quotes_present'] == sum(flags[2:]) == 0
    assert report['primary_any_remaining_long_quote_present'] is False
    assert report['legacy_any_long_presence_includes_known_control'] and report['engineered_copy_controls_passed'] == 1 and report['absent_marker_passed']
    assert not report['matcher_changed']
    for k in ['network_requests', 'new_extractions', 'opaque_passages_scored', 'semantic_labels_admitted',
              'source_identities_admitted', 'independent_reviews_admitted', 'untouched_test_units_admitted', 'external_messages_sent']:
        assert report[k] == 0
    assert report['scientific_acceptance'] is report['semantic_evaluation_metrics'] is None
    comparison = read('data/v43/frozen_comparison.json')
    old39 = read('data/v39/assessment.json')
    expected = [{'quote_id': q['quote_id'], 'v38': old38['quotes'][i]['literal_source_presence'],
                 'v39': old39['quotes'][i]['literal_source_presence'], 'v43': flags[i]} for i, q in enumerate(queries)]
    assert comparison['queries'] == expected and comparison['old_sources_rescored'] is False
    assert read('data/v43/setup_note.json')['scoring_before_successful_registration'] is False
    previous = []
    for path in sorted((ROOT / 'runs').glob('000*/manifest.json')):
        if path.parent != run:
            check_hashes(path.parent); previous.append(path.parent.name)
    assert len(previous) == 42
    for path in (ROOT / 'reports').glob('*_deliverable_seal.json'):
        for p, expected_sha in json.loads(path.read_text()).get('deliverable_hashes', {}).items():
            assert sha(p) == expected_sha
    result = {'state': 'verified', 'manifest_sha256': sha('runs/000043_publisher_quotes/manifest.json'),
              'frozen_queries_body_and_code_verified': True, 'independent_whole_query_counts_and_witnesses': True,
              'known_control_and_six_block_partition_verified': True, 'old_results_compared_without_rescoring': True,
              'independent_scientific_review': False, 'semantic_or_original_source_claim_validated': False,
              'prior_runs_preserved': previous}
    out = ROOT / 'reports/000043_verification.json'
    if out.exists():
        assert {k: v for k, v in json.loads(out.read_text()).items() if k != 'verified_at_utc'} == result
    else:
        with out.open('x') as stream:
            json.dump(result | {'verified_at_utc': datetime.now(timezone.utc).isoformat()}, stream, indent=2); stream.write('\n')
    print(json.dumps({'state': 'verified', 'prior_runs_preserved': len(previous), 'matches': sum(flags), 'remaining_long_matches': sum(flags[2:])}, indent=2))


if __name__ == '__main__':
    main()
