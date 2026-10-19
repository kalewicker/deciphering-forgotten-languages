"""Frozen six-block partial-overlap assay; no network or document extraction."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from fl_decipher.exact_fragments_v44 import audit, token_rows

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
    cfg = read('experiments/exact_fragments_v44.json')
    assert not (ROOT / 'data/v44').exists()
    for path, expected in cfg['input_hashes'].items():
        assert sha(path) == expected, path
    paths = ['experiments/exact_fragments_v44.json', 'src/fl_decipher/exact_fragments_v44.py',
             'scripts/run_exact_fragments_v44.py', 'tests/test_exact_fragments_v44.py']
    write('data/v44/preflight.json', {'sealed_at_utc': datetime.now(timezone.utc).isoformat(),
          'hashes': cfg['input_hashes'] | {p: sha(p) for p in paths}})
    original = read('data/v39/frozen_queries.json')['queries']
    selected = [q for q in original if q['quote_id'] in cfg['query_ids']]
    assert [q['quote_id'] for q in selected] == cfg['query_ids']
    target = read('data/v38/target_export.json')['text']
    for q in selected:
        assert target[slice(*q['span'])] == q['text']
    write('data/v44/frozen_queries.json', {'queries': selected, 'controls': original[:2], 'minimum_tokens': cfg['minimum_tokens']})
    source = (ROOT / cfg['source_text']).read_text()
    page = read('data/v42/page_observations.json')
    assert source == page['text'] and len(source) == 12072 and page['material_available']
    results = [{'quote_id': q['quote_id'], **audit(q['text'], source, cfg['minimum_tokens'], q['span'][0])} for q in selected]
    positive = audit(original[0]['text'], source, cfg['minimum_tokens'], original[0]['span'][0])
    name = audit(original[1]['text'], source, cfg['minimum_tokens'], original[1]['span'][0])
    negative = audit(cfg['absent_query'], source, cfg['minimum_tokens'])
    reversed_text = ' '.join(reversed(re.findall(r'\S+', original[0]['text'])))
    reversed_control = audit(reversed_text, source, cfg['minimum_tokens'])
    required_positive = max(cfg['minimum_tokens'], len(token_rows(original[0]['text'])) - 2)
    passed = {'known_positive': positive['longest_run_tokens'] >= required_positive,
              'short_name_below_threshold': not name['qualifying_overlap_present'],
              'nonce_absent': negative['longest_run_tokens'] == 0,
              'reversed_positive_below_threshold': not reversed_control['qualifying_overlap_present']}
    controls = {'known_positive': positive, 'known_positive_minimum': required_positive, 'short_name': name,
                'absent_query': cfg['absent_query'], 'absent': negative, 'reversed_query': reversed_text,
                'reversed_positive': reversed_control, 'passed': passed}
    write('data/v44/assessment.json', {'queries': results, 'controls': controls})
    valid = all(passed.values())
    report = {'experiment_id': 'exact_fragments_v44', 'outcome': 'completed_exact_fragment_audit' if valid else 'invalid_control_failure',
        'network_requests': 0, 'new_document_extractions': 0, 'whole_query_results_revised': False,
        'minimum_tokens': cfg['minimum_tokens'], 'query_denominator': 6, 'source_characters': len(source),
        'controls_passed': passed, 'primary_readout_valid': valid,
        'queries_with_qualifying_run': sum(r['qualifying_overlap_present'] for r in results) if valid else None,
        'qualifying_run_occurrences': sum(r['qualifying_run_count'] for r in results),
        'covered_query_tokens': sum(r['covered_query_tokens'] for r in results),
        'total_query_tokens': sum(r['query_token_count'] for r in results),
        'opaque_passages_scored': 0, 'semantic_labels_admitted': 0, 'source_identities_admitted': 0,
        'independent_reviews_admitted': 0, 'untouched_test_units_admitted': 0, 'external_messages_sent': 0,
        'semantic_evaluation_metrics': None, 'scientific_acceptance': None}
    write('runs/000044_exact_fragments/report.json', report)
    print(json.dumps(report, indent=2))
    print(json.dumps([{'quote_id': r['quote_id'], 'longest_run': r['longest_run_tokens'],
                      'qualifying_runs': r['qualifying_run_count'], 'covered_tokens': r['covered_query_tokens'],
                      'total_tokens': r['query_token_count']} for r in results], indent=2))


if __name__ == '__main__':
    main()
