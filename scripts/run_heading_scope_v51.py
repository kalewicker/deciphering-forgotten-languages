"""Versioned offline audit of one fixed missing-h1 intake failure."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from fl_decipher.heading_scope_v51 import audit
from fl_decipher.publisher_intake_v50 import inspect_page, service_title

ROOT = Path(__file__).resolve().parents[1]
CODE = ['src/fl_decipher/heading_scope_v51.py', 'scripts/run_heading_scope_v51.py', 'tests/test_heading_scope_v51.py']


def read(p): return json.loads((ROOT / p).read_text())
def sha(p): return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()
def write(p, value):
    path = ROOT / p; path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as stream: json.dump(value, stream, indent=2, ensure_ascii=False); stream.write('\n')


def main():
    config_path = 'experiments/heading_scope_v51.json'; cfg = read(config_path)
    assert not (ROOT / 'data/v51').exists() and not (ROOT / 'runs/000051_heading_scope').exists()
    for p, h in cfg['input_hashes'].items(): assert sha(p) == h, p
    write('data/v51/preflight.json', {'sealed_at_utc': datetime.now(timezone.utc).isoformat(),
          'hashes': cfg['input_hashes'] | {p: sha(p) for p in CODE + [config_path]}})
    oldcfg = read('experiments/publisher_intake_v50.json'); old = read('runs/000050_publisher_intake/report.json')
    slot = next(s for s in read('data/v50/selection.json')['slots'] if s['slot_id'] == cfg['slot_id'])
    nominee = slot['nominee']; receipt = read(cfg['receipt']); raw = (ROOT / cfg['raw']).read_bytes()
    original = read(cfg['observation']); reproduced = inspect_page(raw, receipt, nominee, oldcfg)
    assert original == reproduced and original['checks']['single_matching_h1'] is False
    assert original['headings'] == [] and original['unmet'] == ['single_matching_h1']
    assert old['ready_captures'] == 1 and old['intake_capacity_met'] is False
    result = audit(raw, service_title(nominee['title']), nominee['url'], receipt['final_url'], oldcfg['source_selector'])
    assert result['body_text'] == original['body_text'] and result['paragraph_units'] == original['paragraph_units']
    assert result['publication_values'] == original['published_time_values'] and result['modification_values'] == original['modified_time_values']
    assert result['all_document_h1_count'] == 0
    write('data/v51/audit.json', result)
    report = {'experiment_id': 'heading_scope_v51', 'outcome': 'metadata_agrees_h1_absent' if result['descriptive_metadata_agreement'] else 'metadata_conflicting_or_unresolved',
        'slot_id': cfg['slot_id'], 'candidate_url': nominee['url'], 'candidate_title': result['expected_title'],
        'descriptive_metadata_agreement': result['descriptive_metadata_agreement'],
        'metadata_title_values_agree': result['metadata_title_values_agree'], 'identity_urls_agree': result['identity_urls_agree'],
        'nonempty_metadata_title_families': result['nonempty_metadata_title_families'], 'all_document_h1_count': 0,
        'matching_title_record_counts': {channel: sum(r['matches_expected'] for r in result['title_inventory'] if r['channel'] == channel)
                                       for channel in sorted({r['channel'] for r in result['title_inventory']})},
        'body_title_occurrences': len(result['body_title_occurrences']), 'jsonld_errors': len(result['jsonld_errors']),
        'direct_paragraph_count': len(result['paragraph_units']), 'full_container_characters': len(result['container_text']),
        'direct_p_characters': len(result['direct_p_text']), 'leaf_count': result['leaf_count'], 'included_leaf_count': result['included_leaf_count'],
        'excluded_leaf_count': result['excluded_leaf_count'], 'excluded_category_counts': result['excluded_category_counts'],
        'excluded_category_characters': result['excluded_category_characters'],
        'all_static_container_text_in_direct_p': result['all_static_container_text_in_direct_p'],
        'v50_candidate_ready_unchanged': False, 'v50_ready_captures_unchanged': 1, 'v50_intake_capacity_met_unchanged': False,
        'network_requests': 0, 'browser_renders': 0, 'new_structural_scores': 0, 'opaque_lexical_or_semantic_scores': 0,
        'semantic_labels_admitted': 0, 'source_identities_admitted': 0, 'independent_reviews_admitted': 0,
        'untouched_test_units_admitted': 0, 'new_candidate_readiness_admissions': 0, 'external_messages_sent': 0,
        'scientific_acceptance': None, 'semantic_evaluation_metrics': None}
    write('runs/000051_heading_scope/report.json', report)
    outputs = sorted(str(p.relative_to(ROOT)) for p in (ROOT / 'data/v51').glob('*.json'))
    write('runs/000051_heading_scope/manifest.json', {'experiment_id': report['experiment_id'], 'state': 'completed',
        'finished_at_utc': datetime.now(timezone.utc).isoformat(), 'outcome': report['outcome'],
        'input_hashes': cfg['input_hashes'] | {config_path: sha(config_path)}, 'code_hashes': {p: sha(p) for p in CODE},
        'output_hashes': {'report.json': sha('runs/000051_heading_scope/report.json')} |
            {str(Path('../../') / p): sha(p) for p in outputs}, 'verifier_written_after_audit': True})
    print(json.dumps(report, indent=2))


if __name__ == '__main__': main()
