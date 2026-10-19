"""Uniform five-page structural-scope audit, no scoring or admission changes."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from fl_decipher.cohort_scope_v52 import accounting, extract_scope
from fl_decipher.heading_scope_v51 import audit

ROOT = Path(__file__).resolve().parents[1]
CODE = ['src/fl_decipher/cohort_scope_v52.py', 'scripts/run_cohort_scope_v52.py', 'tests/test_cohort_scope_v52.py']


def read(p): return json.loads((ROOT / p).read_text())
def sha(p): return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()
def write(p, value):
    path = ROOT / p; path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as stream: json.dump(value, stream, indent=2, ensure_ascii=False); stream.write('\n')


def main():
    cfgpath = 'experiments/cohort_scope_v52.json'; cfg = read(cfgpath)
    assert not (ROOT / 'data/v52').exists() and not (ROOT / 'runs/000052_cohort_scope').exists()
    for p, h in cfg['input_hashes'].items(): assert sha(p) == h, p
    write('data/v52/preflight.json', {'sealed_at_utc': datetime.now(timezone.utc).isoformat(),
          'hashes': cfg['input_hashes'] | {p: sha(p) for p in CODE + [cfgpath]}})
    old_intake = read('runs/000050_publisher_intake/report.json')
    assert old_intake['ready_captures'] == 1 and old_intake['intake_capacity_met'] is False
    rows = []
    for spec in cfg['pages']:
        raw = (ROOT / spec['raw']).read_bytes(); receipt = read(spec['receipt']); original = read(spec['observation'])
        assert sha(spec['raw']) == receipt['artifacts']['body.bin']['sha256'] and receipt['transport_complete']
        expected_body = original[spec['body_field']]
        scope = extract_scope(raw, expected_body, cfg['selector'])
        identity = audit(raw, spec['expected_title'], spec['url'], receipt['final_url'], cfg['selector'])
        assert identity['body_text'] == scope['body_text'] == expected_body
        assert identity['paragraph_units'] == scope['legacy_direct_paragraphs']
        if spec['id'] == 'reference_v42':
            legacy = read('data/v46/scope.json')['source_units']
            assert [{k: p[k] for k in ['unit', 'span', 'text']} for p in scope['legacy_direct_paragraphs']] == legacy
            old_ready = None
        else:
            assert scope['legacy_direct_paragraphs'] == original['paragraph_units']
            old_result = next(r for r in old_intake['slot_results'] if r['slot_id'] == spec['id'])
            old_ready = old_result['ready_for_future_registration']
            assert old_ready == original['ready_for_future_registration']
        if spec['id'] == 'q01s01': assert identity == read('data/v51/audit.json')
        checks = accounting(scope)
        write(f"data/v52/{spec['id']}_scope.json", scope)
        write(f"data/v52/{spec['id']}_title_identity.json", identity)
        leaves = scope['container_leaves']; ps = scope['paragraph_inventory']
        rows.append({'id': spec['id'], 'title': spec['expected_title'], 'url': spec['url'],
            'legacy_direct_paragraphs': len(scope['legacy_direct_paragraphs']), 'paragraph_owner_inventory': len(ps),
            'empty_paragraph_owners': sum(not p['text'] for p in ps), 'owners_with_nested_p': sum(p['nested_p_descendants'] > 0 for p in ps),
            'container_leaf_count': len(leaves), 'legacy_included_leaf_count': sum(r['old_direct_p_included'] for r in leaves),
            'paragraph_channel_leaf_count': scope['channel_leaf_counts'].get('paragraph', 0), 'paragraph_runs': len(scope['paragraph_runs']),
            'added_paragraph_leaf_count': len(scope['added_paragraph_leaf_indices']), 'removed_legacy_leaf_count': len(scope['removed_legacy_leaf_indices']),
            'channel_leaf_counts': scope['channel_leaf_counts'], 'channel_characters': scope['channel_characters'],
            'legacy_direct_p_characters': len(scope['legacy_direct_p_text']),
            'prospective_paragraph_run_characters': sum(len(r['text']) for r in scope['paragraph_runs']),
            'all_document_h1_count': identity['all_document_h1_count'], 'descriptive_metadata_agreement': identity['descriptive_metadata_agreement'],
            'identity_urls_agree': identity['identity_urls_agree'], 'v50_ready_unchanged': old_ready,
            'old_scope_reproduced': True, 'accounting_checks': checks, 'accounting_passed': all(checks.values())})
    assert len(rows) == 5
    gate = all(r['accounting_passed'] and r['old_scope_reproduced'] for r in rows)
    report = {'experiment_id': 'cohort_scope_v52', 'outcome': 'uniform_accounting_verified' if gate else 'accounting_failure',
        'page_denominator': 5, 'pages': rows, 'registered_engineering_accounting_gate': gate,
        'pages_with_added_paragraph_leaves': sum(r['added_paragraph_leaf_count'] > 0 for r in rows),
        'pages_with_removed_legacy_leaves': sum(r['removed_legacy_leaf_count'] > 0 for r in rows),
        'v50_ready_captures_unchanged': 1, 'v50_intake_capacity_met_unchanged': False,
        'network_requests': 0, 'browser_renders': 0, 'new_structural_scores': 0, 'opaque_lexical_or_semantic_scores': 0,
        'new_candidate_readiness_admissions': 0, 'semantic_labels_admitted': 0, 'source_identities_admitted': 0,
        'independent_reviews_admitted': 0, 'untouched_test_units_admitted': 0, 'external_messages_sent': 0,
        'scientific_acceptance': None, 'semantic_evaluation_metrics': None}
    write('runs/000052_cohort_scope/report.json', report)
    outputs = sorted(str(p.relative_to(ROOT)) for p in (ROOT / 'data/v52').glob('*.json'))
    write('runs/000052_cohort_scope/manifest.json', {'experiment_id': report['experiment_id'], 'state': 'completed',
        'finished_at_utc': datetime.now(timezone.utc).isoformat(), 'outcome': report['outcome'],
        'input_hashes': cfg['input_hashes'] | {cfgpath: sha(cfgpath)}, 'code_hashes': {p: sha(p) for p in CODE},
        'output_hashes': {'report.json': sha('runs/000052_cohort_scope/report.json')} |
            {str(Path('../../') / p): sha(p) for p in outputs}, 'verifier_written_after_audit': True})
    print(json.dumps(report, indent=2))


if __name__ == '__main__': main()
