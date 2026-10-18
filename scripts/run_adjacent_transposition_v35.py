"""Run the frozen crossing model, then assess ancestry and control outcomes."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
from fl_decipher.adjacent_transposition_v35 import predict, assess

ROOT = Path(__file__).resolve().parents[1]
RUN = 'runs/000035_adjacent_transposition'
def read(p): return json.loads((ROOT/p).read_text())
def sha(p): return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def write(p, v): (ROOT/p).write_text(json.dumps(v, indent=2)+'\n')
def payload_sha(v): return hashlib.sha256(json.dumps(v, sort_keys=True).encode()).hexdigest()


def main():
    cfg = read('experiments/adjacent_transposition_v35.json'); pre = read('data/v35/preflight.json'); bench = read('benchmarks/adjacent_transposition_v35.json')
    for hashes in [bench['input_hashes'], pre['code_hashes']]:
        for p, h in hashes.items(): assert sha(p) == h, p
    (ROOT/RUN).mkdir(exist_ok=False)
    manifest = {'experiment_id': cfg['experiment_id'], 'state': 'running', 'started_at_utc': datetime.now(timezone.utc).isoformat(),
                'input_hashes': bench['input_hashes'] | {'benchmarks/adjacent_transposition_v35.json': sha('benchmarks/adjacent_transposition_v35.json')},
                'code_hashes': pre['code_hashes']}
    write(RUN+'/manifest.json', manifest)
    try:
        prep = read('data/v35/preparation_receipt.json')
        assert cfg['registered_at_utc'] < pre['sealed_at_utc'] < prep['prepared_at_utc'] < bench['frozen_at_utc'] < manifest['started_at_utc']
        public = read('data/v35/public_observations.json'); model = read('data/v32/frozen_mapping.json')['model']; before = payload_sha(model)
        predictions = predict(public, model); assert before == payload_sha(model)
        write(RUN+'/predictions.json', predictions)
        write(RUN+'/prediction_receipt.json', {'predictions_frozen_at_utc': datetime.now(timezone.utc).isoformat(),
                                              'predictions_sha256': sha(RUN+'/predictions.json'), 'oracle_used_for_prediction': False,
                                              'model_payload_sha256_before': before, 'model_payload_sha256_after': payload_sha(model)})
        assessment = assess(public, read('data/v35/oracle.json'), predictions, read('runs/000034_positional_worlds/assessment.json'))
        write(RUN+'/assessment.json', assessment)
        w = assessment['world_assessment']
        assert w['site_inventory']['worlds'] == cfg['v34_worlds'] and w['site_inventory']['sites'] == cfg['v34_sites'] and w['site_inventory']['excluded_sites'] == cfg['v34_excluded_sites']
        assert len(assessment['controls']) == cfg['control_rows'] and len(assessment['panels']) == cfg['panels']
        assert all(sha(p) == h for p, h in cfg['input_hashes'].items())
        report = {'experiment_id': cfg['experiment_id'], 'engineering_integrity_passed': True, 'mapping_unchanged': True,
                  'observations': len(public['observations']), 'v34_observations_preserved': prep['v34_observations_preserved'],
                  'control_rows': len(assessment['controls']), 'panels': len(assessment['panels']),
                  'site_inventory': w['site_inventory'], 'by_relation_world': w['by_relation_world'], 'all_worlds': w['all_worlds'],
                  'collision_demonstration': w['identifiability_demonstration'], 'synthetic_recovery_gate': assessment['synthetic_recovery_gate'],
                  'baseline_comparison': assessment['baseline_comparison'],
                  'structural_summary': {'observations_with_cross_operations': sum(p['alignment']['cross_operations'] > 0 for p in predictions['predictions'].values()),
                                         'observations_with_matched_pair_ambiguity': sum(p['ambiguity']['matched_pair_ambiguity'] for p in predictions['predictions'].values()),
                                         'possible_cross_operations': sum(op['kind'] == 'swap' for p in predictions['predictions'].values() for op in p['ambiguity']['possible_operations'])},
                  'symbolic_transposition_aligner_executed': True, 'external_or_neural_model_executed': False,
                  'scientific_acceptance': None, 'semantic_evaluation_metrics': None, 'semantic_labels_admitted': 0, 'source_identities_admitted': 0,
                  'independent_reviews_admitted': 0, 'untouched_test_units_admitted': 0, 'natural_targets_rescored': 0,
                  'prior_retrieval_decisions_changed': 0, 'new_network_requests': 0, 'symbol_compatibility_is_independent_accuracy': False}
        write(RUN+'/report.json', report)
        manifest.update(state='completed', finished_at_utc=datetime.now(timezone.utc).isoformat(),
                        outcome='synthetic_recovery_gate_met' if assessment['synthetic_recovery_gate']['passed'] else 'synthetic_recovery_gate_failed',
                        output_hashes={p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/RUN).iterdir() if p.name != 'manifest.json'})
        write(RUN+'/manifest.json', manifest)
        print(json.dumps(report, indent=2))
    except Exception as error:
        manifest.update(state='failed', error=f'{type(error).__name__}: {error}'); write(RUN+'/manifest.json', manifest); raise


if __name__ == '__main__': main()
