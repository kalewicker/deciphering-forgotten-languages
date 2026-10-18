"""Seal, prepare, or execute the single registered v36 experiment (offline)."""
from datetime import datetime, timezone
from pathlib import Path
import argparse
import hashlib
import json

from fl_decipher.mixed_edit_transfer_v36 import prepare, predict, assess, payload_hash

ROOT = Path(__file__).resolve().parents[1]
RUN = 'runs/000036_mixed_edit_transfer'
CFG = 'experiments/mixed_edit_transfer_v36.json'
PREFLIGHT = 'data/v36/preflight_revision1.json'


def now():
    return datetime.now(timezone.utc).isoformat()


def read(path):
    return json.loads((ROOT/path).read_text())


def sha(path):
    return hashlib.sha256((ROOT/path).read_bytes()).hexdigest()


def write(path, value):
    target = ROOT/path
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open('x') as f:
        json.dump(value, f, indent=2)
        f.write('\n')


def check(hashes):
    for path, expected in hashes.items():
        assert sha(path) == expected, path


def seal():
    cfg = read(CFG)
    check(cfg['input_hashes'])
    assert not (ROOT/'data/v36/public_observations.json').exists()
    assert not (ROOT/RUN).exists()
    code = list((ROOT/'src/fl_decipher').glob('*.py')) + list((ROOT/'scripts').glob('*.py')) + list((ROOT/'tests').glob('*.py'))
    extra = [CFG, 'benchmarks/kamri_dataset_audit_v15.json', 'runs/000015_kamri_dataset_audit/report.json',
             'runs/000014_kamri_source_feasibility/report.json', 'runs/000025_kamri_review_handoff/report.json',
             'runs/000030_paragraph_patterns/report.json']
    revision = read('experiments/mixed_edit_transfer_v36_preparation_revision1.json')
    check(revision['input_hashes'])
    extra += ['experiments/mixed_edit_transfer_v36_preparation_revision1.json', *revision['input_hashes']]
    extra += [str(p.relative_to(ROOT)) for p in (ROOT/'data/v36/preparation_failure').glob('*.py')]
    extra += ['data/v36/preparation_failure/snapshot_recovery.json']
    benchmark = read('benchmarks/kamri_dataset_audit_v15.json')
    extra += [d['path'] for d in benchmark['documents'].values()]
    write(PREFLIGHT, {'sealed_at_utc': now(), 'input_hashes': cfg['input_hashes'] | {p: sha(p) for p in extra},
                                     'code_hashes': {str(p.relative_to(ROOT)): sha(p) for p in sorted(code)},
                                     'new_passages_generated': 0, 'predictions_computed': 0})
    print('Registration, implementation and inputs sealed; no new passages generated.')


def freeze():
    cfg, pre = read(CFG), read(PREFLIGHT)
    check(pre['input_hashes'])
    check(pre['code_hashes'])
    assert not (ROOT/RUN).exists()
    assert not (ROOT/'data/v36/public_observations.json').exists()
    public, oracle, variants = prepare(cfg, read('data/v32/frozen_mapping.json')['model'])
    assert len(public['observations']) <= cfg['pairs_per_branch']
    assert sum(len(q['observation_ids']) for q in oracle['queries']) == cfg['pairs_per_branch']
    assert len(public['panels']) == cfg['panels_per_branch']
    assert len(oracle['queries']) == cfg['queries'] and len(oracle['bases']) == cfg['parents']
    paths = {'data/v36/public_observations.json': public, 'data/v36/oracle.json': oracle, 'data/v36/model_variants.json': variants}
    for path, value in paths.items():
        write(path, value)
    write('data/v36/preparation_receipt.json', {'prepared_at_utc': now(), 'output_hashes': {p: sha(p) for p in paths},
                                               'new_parents': len(oracle['bases']), 'queries': len(oracle['queries']), 'predictions_computed': 0})
    inputs = pre['input_hashes'] | {p: sha(p) for p in [*paths, PREFLIGHT, 'data/v36/preparation_receipt.json']}
    write('benchmarks/mixed_edit_transfer_v36.json', {'frozen_at_utc': now(), 'input_hashes': inputs})
    print(json.dumps({'parents': len(oracle['bases']), 'queries': len(oracle['queries']), 'pairs_per_branch': len(public['observations']),
                      'panels_per_branch': len(public['panels']), 'predictions_computed': 0}))


def natural_audit():
    """Inventory saved evidence; never create a split by reclassifying exposure."""
    articles = read('runs/000015_kamri_dataset_audit/report.json')['articles']
    future = read('runs/000021_kamri_calibration_evidence/future_panel.json')
    handoff = read('runs/000025_kamri_review_handoff/report.json')
    links = {name: name for article in articles for name in article['component']}

    def root(name):
        while links[name] != name:
            name = links[name]
        return name

    for article in articles:
        names = article['component']
        for name in names[1:]:
            links[root(name)] = root(names[0])
    groups = {}
    for name in links:
        groups.setdefault(root(name), []).append(name)
    ledger = []
    for members in sorted(groups.values()):
        selected = [a for a in articles if set(a['component']) & set(members)]
        ledger.append({'connected_components': sorted(members), 'article_entries': [a['entry'] for a in selected],
                       'article_titles': [a['title'] for a in selected], 'annotation_units': sum(a['units'] for a in selected),
                       'exposed': True, 'exposure_evidence': 'runs/000015_kamri_dataset_audit/report.json',
                       'independently_reviewed_passage_units_admitted': 0, 'eligible_for_untouched_pilot': False,
                       'exclusion_reasons': ['already_exposed', 'no_admitted_independent_passage_review']})
    counts = CounterTuple(future['units'])
    return {'scope': 'Existing tracked v15 reading-edition inventory, v21 development panel and v25/v26 review records; not the entire FL archive',
            'connected_group_ledger': ledger, 'tracked_article_editions': len(articles), 'tracked_connected_groups': len(ledger),
            'development_panel': [{'connected_components': list(g), 'units': n} for g, n in sorted(counts.items())],
            'development_units': len(future['units']), 'development_groups': len(counts),
            'indexed_excerpt_limit': 'v21 FL support views are historical/indexed; equal counts and projected pairs are not semantic gold',
            'full_dated_post_dossiers': len(handoff['records']), 'dossier_ids': [r['nominee_id'] for r in handoff['records']],
            'dossier_scope': 'Western fixed PDF90-94 and Risk PDF1-3; whole-post source coverage unresolved',
            'review_status': 'No accepted independent return; supplied automated source-disclosed report and exact spans are development leads',
            'review_status_evidence': ['reports/000025_interpretation.md', 'reports/000026_interpretation.md'],
            'unexposed_reviewed_connected_works_available': 0,
            'capacity_requirements': read(CFG)['natural_capacity_rule'], 'immediate_untouched_benchmark_feasible': False,
            'remaining_unexposed_components_in_v14_inventory': read('runs/000014_kamri_source_feasibility/report.json')['remaining_unexposed_components_in_inventory_after_v14'],
            'next_decision': 'Stop synthetic feature expansion. Acquire and independently review new connected works under a frozen source-first intake plan, or record review access as unresolved.',
            'new_network_requests': 0, 'natural_targets_rescored': 0, 'source_identities_admitted': 0,
            'semantic_labels_admitted': 0, 'independent_reviews_admitted': 0, 'untouched_test_units_admitted': 0,
            'semantic_evaluation_metrics': None, 'scientific_acceptance': None}


def CounterTuple(units):
    from collections import Counter
    return Counter(tuple(sorted(u['connected_group'])) for u in units)


def execute():
    cfg, pre, bench = read(CFG), read(PREFLIGHT), read('benchmarks/mixed_edit_transfer_v36.json')
    check(bench['input_hashes'])
    check(pre['code_hashes'])
    (ROOT/RUN).mkdir(exist_ok=False)
    manifest = {'experiment_id': cfg['experiment_id'], 'state': 'running', 'started_at_utc': now(),
                'input_hashes': bench['input_hashes'] | {'benchmarks/mixed_edit_transfer_v36.json': sha('benchmarks/mixed_edit_transfer_v36.json')},
                'code_hashes': pre['code_hashes']}
    manifest_path = ROOT/RUN/'manifest.json'
    manifest_path.write_text(json.dumps(manifest, indent=2)+'\n')
    try:
        prep = read('data/v36/preparation_receipt.json')
        assert cfg['registered_at_utc'] < pre['sealed_at_utc'] < prep['prepared_at_utc'] < bench['frozen_at_utc'] < manifest['started_at_utc']
        public, variants = read('data/v36/public_observations.json'), read('data/v36/model_variants.json')
        outputs, receipts = {}, {}
        for name in cfg['branches']:
            model = variants['models'][name]
            before = payload_hash(model)
            print(f'Predicting frozen {name} branch ({len(public["observations"])} pairs).', flush=True)
            outputs[name] = predict(public, model)
            assert payload_hash(model) == before
            path = f'{RUN}/predictions_{name}.json'
            write(path, outputs[name])
            receipts[name] = {'frozen_at_utc': now(), 'predictions_sha256': sha(path),
                              'model_payload_before': before, 'model_payload_after': payload_hash(model)}
        write(RUN+'/prediction_receipt.json', {'branches': receipts, 'all_predictions_frozen_at_utc': now(), 'oracle_used_for_prediction': False})
        # First runtime oracle load occurs only after all branch predictions are on disk.
        assessment = assess(public, read('data/v36/oracle.json'), outputs)
        write(RUN+'/assessment.json', assessment)
        audit = natural_audit()
        write(RUN+'/natural_evidence_audit.json', audit)
        report = {'experiment_id': cfg['experiment_id'], 'engineering_integrity_passed': True, 'original_mapping_unchanged': True,
                  'parents': cfg['parents'], 'queries_per_branch': cfg['queries'], 'alignments': cfg['pairs_per_branch']*3,
                  'distinct_alignments_computed': len(public['observations'])*3,
                  'panel_decisions': cfg['panels_per_branch']*3, 'branches': cfg['branches'],
                  'synthetic_transfer_gate': assessment['synthetic_transfer_gate'], 'summaries': assessment['summaries'],
                  'full_token_denominator_per_branch': assessment['full_token_denominator_per_branch'],
                  'immediate_untouched_natural_benchmark_feasible': audit['immediate_untouched_benchmark_feasible'],
                  'unexposed_reviewed_connected_works_available': 0,
                  'synthetic_feature_expansion_stopped': True, 'symbolic_transposition_aligner_executed': True,
                  'external_or_neural_model_executed': False, 'new_network_requests': 0, 'natural_targets_rescored': 0,
                  'semantic_labels_admitted': 0, 'source_identities_admitted': 0, 'independent_reviews_admitted': 0,
                  'untouched_test_units_admitted': 0, 'scientific_acceptance': None, 'semantic_evaluation_metrics': None}
        write(RUN+'/report.json', report)
        check(bench['input_hashes'])
        check(pre['code_hashes'])
        manifest.update(state='completed', finished_at_utc=now(), outcome='synthetic_transfer_gate_met' if assessment['synthetic_transfer_gate']['passed'] else 'synthetic_transfer_gate_failed',
                        output_hashes={p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/RUN).iterdir() if p.name != 'manifest.json'})
        manifest_path.write_text(json.dumps(manifest, indent=2)+'\n')
        print(json.dumps({'gate': assessment['synthetic_transfer_gate'], 'natural_capacity': audit['unexposed_reviewed_connected_works_available']}))
    except Exception as error:
        manifest.update(state='failed', error=f'{type(error).__name__}: {error}')
        manifest_path.write_text(json.dumps(manifest, indent=2)+'\n')
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['seal', 'prepare', 'run'])
    action = parser.parse_args().action
    {'seal': seal, 'prepare': freeze, 'run': execute}[action]()
