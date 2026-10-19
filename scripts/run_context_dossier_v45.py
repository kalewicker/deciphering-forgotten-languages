"""Prepare the registered single-case context dossier from frozen bytes."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from fl_decipher.context_dossier_v45 import build, render

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads((ROOT / path).read_text())


def sha(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def write(path, value):
    path = ROOT / path; path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False); stream.write('\n')


def main():
    cfg = read('experiments/context_dossier_v45.json')
    assert not (ROOT / 'data/v45').exists()
    for path, expected in cfg['input_hashes'].items():
        assert sha(path) == expected, path
    paths = ['experiments/context_dossier_v45.json', 'src/fl_decipher/context_dossier_v45.py',
             'scripts/run_context_dossier_v45.py', 'tests/test_context_dossier_v45.py', 'src/fl_decipher/dated_capture_scope_v38.py']
    write('data/v45/preflight.json', {'sealed_at_utc': datetime.now(timezone.utc).isoformat(),
          'hashes': cfg['input_hashes'] | {p: sha(p) for p in paths}})
    quote = read('data/v39/frozen_queries.json')['queries'][2]
    run = read('data/v44/assessment.json')['queries'][0]['runs'][0]
    assert quote['quote_id'] == cfg['quote_id'] and run['token_count'] == 22
    write('data/v45/fixed_selection.json', {'quote': quote, 'witness': run})
    d = build((ROOT / cfg['raw_html']).read_bytes(), (ROOT / cfg['source_text']).read_text(),
              read('data/v38/target_export.json')['text'], quote, run, cfg['target_context_characters'])
    write('data/v45/dossier.json', d)
    with (ROOT / 'data/v45/dossier.md').open('x') as stream:
        stream.write(render(d))
    available = d['status'] == 'context_available'
    report = {'experiment_id': 'context_dossier_v45', 'outcome': d['status'], 'network_requests': 0,
        'source_reextractions_from_frozen_bytes': 1, 'new_overlap_assessments': 0, 'case_denominator': 1,
        'fixed_witness_tokens': 22, 'fixed_witness_changed': False, 'context_available': available,
        'literal_check_denominator': 11, 'literal_checks_available': len(d['context_checks']) if available else 0,
        'publisher_paragraph_index': d['selected_paragraph']['paragraph_index'] if available else None,
        'partition_reassembly_passed': d.get('partition_reassembly_passed'), 'opaque_passages_scored': 0,
        'semantic_labels_admitted': 0, 'source_identities_admitted': 0, 'independent_reviews_admitted': 0,
        'untouched_test_units_admitted': 0, 'external_messages_sent': 0, 'original_attribution_authenticated': False,
        'semantic_evaluation_metrics': None, 'scientific_acceptance': None}
    write('runs/000045_context_dossier/report.json', report)
    print(json.dumps(report, indent=2))
    if available:
        print(json.dumps({'partition_lengths': {k: [len(r['text']) for r in d[k]] for k in ['target_partition', 'source_partition']},
                          'checks': {c['check_id']: c['present'] for c in d['context_checks']}}, indent=2))


if __name__ == '__main__':
    main()
