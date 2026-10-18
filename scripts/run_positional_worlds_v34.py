"""Freeze content-only predictions before paired-world ancestry assessment."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
from fl_decipher.positional_worlds_v34 import predict, assess

ROOT = Path(__file__).resolve().parents[1]
RUN = 'runs/000034_positional_worlds'


def read(p): return json.loads((ROOT / p).read_text())
def sha(p): return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()
def write(p, v): (ROOT / p).write_text(json.dumps(v, indent=2) + '\n')
def payload_sha(v): return hashlib.sha256(json.dumps(v, sort_keys=True).encode()).hexdigest()


def main():
    cfg = read('experiments/positional_worlds_v34.json'); pre = read('data/v34/preflight.json'); bench = read('benchmarks/positional_worlds_v34.json')
    for inventory in [bench['input_hashes'], pre['code_hashes']]:
        for p, h in inventory.items(): assert sha(p) == h, p
    (ROOT / RUN).mkdir(exist_ok=False)
    manifest = {'experiment_id': cfg['experiment_id'], 'state': 'running', 'started_at_utc': datetime.now(timezone.utc).isoformat(),
                'input_hashes': bench['input_hashes'] | {'benchmarks/positional_worlds_v34.json': sha('benchmarks/positional_worlds_v34.json')},
                'code_hashes': pre['code_hashes']}
    write(RUN + '/manifest.json', manifest)
    try:
        assert cfg['registered_at_utc'] < pre['sealed_at_utc'] < read('data/v34/preparation_receipt.json')['prepared_at_utc'] < bench['frozen_at_utc'] < manifest['started_at_utc']
        public = read('data/v34/public_observations.json'); model = read('data/v32/frozen_mapping.json')['model']; before = payload_sha(model)
        predictions = predict(public, model); assert payload_sha(model) == before
        write(RUN + '/predictions.json', predictions)
        write(RUN + '/prediction_receipt.json', {'predictions_frozen_at_utc': datetime.now(timezone.utc).isoformat(),
                                                'predictions_sha256': sha(RUN + '/predictions.json'), 'oracle_used_for_prediction': False,
                                                'model_payload_sha256_before': before, 'model_payload_sha256_after': payload_sha(model)})
        assessment = assess(public, read('data/v34/oracle.json'), predictions, cfg['minimum_unequal_swap_affected_forced_returns'])
        assert assessment['site_inventory']['sites'] == cfg['site_denominator']
        write(RUN + '/assessment.json', assessment)
        assert all(sha(p) == h for p, h in cfg['input_hashes'].items())
        report = {'experiment_id': cfg['experiment_id'], 'engineering_integrity_passed': True, 'mapping_unchanged': True,
                  **{k: assessment[k] for k in ['site_inventory', 'by_relation_world', 'all_worlds', 'identifiability_demonstration', 'unequal_swap_forced_safety_hypothesis']},
                  'symbolic_aligner_and_audit_executed': True, 'external_or_neural_model_executed': False,
                  'scientific_acceptance': None, 'semantic_evaluation_metrics': None, 'semantic_labels_admitted': 0,
                  'source_identities_admitted': 0, 'independent_reviews_admitted': 0, 'untouched_test_units_admitted': 0,
                  'natural_targets_rescored': 0, 'prior_retrieval_decisions_changed': 0, 'new_network_requests': 0,
                  'symbol_compatibility_is_independent_accuracy': False}
        write(RUN + '/report.json', report)
        manifest.update(state='completed', finished_at_utc=datetime.now(timezone.utc).isoformat(),
                        outcome='paired_world_diagnostic_complete', output_hashes={p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                        for p in (ROOT / RUN).iterdir() if p.name != 'manifest.json'})
        write(RUN + '/manifest.json', manifest)
        print(json.dumps(report, indent=2))
    except Exception as error:
        manifest.update(state='failed', error=f'{type(error).__name__}: {error}'); write(RUN + '/manifest.json', manifest)
        raise


if __name__ == '__main__': main()
