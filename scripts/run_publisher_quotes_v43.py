"""Offline reuse of the frozen v39 whole-query assessor; no new matcher."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from fl_decipher.quoted_citation_v39 import assess_queries, frozen_queries

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads((ROOT / path).read_text())


def sha(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def write(path, value):
    path = ROOT / path
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False); stream.write('\n')


def main():
    cfg = read('experiments/publisher_quotes_v43.json')
    assert not (ROOT / 'data/v43').exists()
    for path, expected in cfg['input_hashes'].items():
        assert sha(path) == expected, path
    paths = ['experiments/publisher_quotes_v43.json', 'scripts/run_publisher_quotes_v43.py',
             'src/fl_decipher/quoted_citation_v39.py', 'src/fl_decipher/dated_capture_scope_v38.py',
             'tests/test_quoted_citation_v39.py']
    hashes = cfg['input_hashes'] | {p: sha(p) for p in paths}
    write('data/v43/preflight.json', {'sealed_at_utc': datetime.now(timezone.utc).isoformat(), 'hashes': hashes})
    target = read('data/v38/target_export.json')['text']
    queries = frozen_queries(target, read('data/v38/observable_scope.json'))
    assert queries == read('data/v39/frozen_queries.json')['queries']
    assert [q['quote_id'] for q in queries] == cfg['query_ids']
    write('data/v43/frozen_queries.json', {'queries': queries, 'source': cfg['source_text']})
    page = read('data/v42/page_observations.json')
    text = (ROOT / cfg['source_text']).read_text()
    assert page['text'] == text and len(text) == cfg['expected_source_characters']
    available = page['material_available']
    assessment = assess_queries(queries, [{'page': 1, 'text': text}] if available else [], [], available)
    assessment['representation_note'] = 'page=1 indexes one saved HTML publisher body; not a physical PDF page'
    write('data/v43/assessment.json', assessment)
    rows = {q['quote_id']: q for q in assessment['quotes']}
    valid = rows['quote00']['literal_source_presence'] is True and assessment['source_extraction_complete']
    residual = [rows[q]['literal_source_presence'] for q in cfg['remaining_long_query_ids']]
    report = {'experiment_id': 'publisher_quotes_v43', 'outcome': 'completed_literal_inventory' if valid else 'invalid_known_control_or_extraction',
        'network_requests': 0, 'new_extractions': 0, 'matcher_changed': False,
        'representation': 'one frozen HTML publisher-page body', 'source_unit_denominator': 1,
        'source_characters': len(text), 'source_material_available': available,
        'quote_denominator': 8, 'long_quote_denominator': 7,
        'complete_quotes_present': assessment['quotes_with_literal_source_presence'],
        'long_quotes_present': assessment['long_quotes_with_literal_presence'],
        'query_outcomes_unavailable': assessment['query_outcomes_unavailable'],
        'known_positive_query': 'quote00', 'known_positive_passed': rows['quote00']['literal_source_presence'],
        'expanded_name_present': rows['quote01']['literal_source_presence'],
        'remaining_long_quote_denominator': 6, 'remaining_long_quotes_present': sum(v is True for v in residual) if valid else None,
        'primary_any_remaining_long_quote_present': any(v is True for v in residual) if valid else None,
        'primary_readout_valid': valid, 'legacy_any_long_presence_includes_known_control': assessment['primary_long_block_presence'],
        'engineered_copy_controls_passed': assessment['positive_controls_passed'],
        'absent_marker_passed': assessment['negative_control']['passed'],
        'opaque_passages_scored': 0, 'semantic_labels_admitted': 0, 'source_identities_admitted': 0,
        'independent_reviews_admitted': 0, 'untouched_test_units_admitted': 0, 'external_messages_sent': 0,
        'semantic_evaluation_metrics': None, 'scientific_acceptance': None}
    write('runs/000043_publisher_quotes/report.json', report)
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
