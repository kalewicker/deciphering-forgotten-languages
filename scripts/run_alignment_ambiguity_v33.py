"""Run the registered audit on frozen v32 alignments without overwriting them."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
from fl_decipher.alignment_ambiguity_v33 import audit, assess, structural_summary

ROOT = Path(__file__).resolve().parents[1]
RUN = 'runs/000033_alignment_ambiguity'


def read(p):
    return json.loads((ROOT / p).read_text())


def sha(p):
    return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()


def write(p, value):
    (ROOT / p).write_text(json.dumps(value, indent=2) + '\n')


def main():
    cfg = read('experiments/alignment_ambiguity_v33.json'); pre = read('data/v33/preflight.json')
    for inventory in (cfg['input_hashes'], pre['input_hashes'], pre['code_hashes']):
        for p, h in inventory.items():
            assert sha(p) == h, p
    (ROOT / RUN).mkdir(exist_ok=False)
    manifest = {'experiment_id': cfg['experiment_id'], 'state': 'running',
                'started_at_utc': datetime.now(timezone.utc).isoformat(),
                'input_hashes': pre['input_hashes'] | {'data/v33/preflight.json': sha('data/v33/preflight.json')},
                'code_hashes': pre['code_hashes']}
    write(RUN + '/manifest.json', manifest)
    try:
        assert cfg['registered_at_utc'] < pre['sealed_at_utc'] < manifest['started_at_utc']
        public = read('data/v32/public_cases.json'); predictions = read('runs/000032_synthetic_transfer/predictions.json')
        result = audit(public, predictions)
        assert len(result['pairs']) == cfg['pair_denominator'] and result['queries'] == cfg['query_denominator'] and result['panels'] == cfg['panel_denominator']
        write(RUN + '/ambiguity.json', result)
        write(RUN + '/audit_receipt.json', {'audit_frozen_at_utc': datetime.now(timezone.utc).isoformat(),
                                         'audit_sha256': sha(RUN + '/ambiguity.json'), 'oracle_used_for_audit': False})
        assessment = assess(result, read('data/v32/oracle.json'))
        assert assessment['primary_summary']['pairs'] == cfg['primary_parent_pairs']
        assert assessment['primary_summary']['representative_matches'] == cfg['primary_returned_matches']
        write(RUN + '/assessment.json', assessment)
        unchanged = all(sha(p) == h for p, h in cfg['input_hashes'].items())
        assert unchanged
        report = {'experiment_id': cfg['experiment_id'], 'engineering_integrity_passed': True,
                  'frozen_inputs_unchanged': unchanged, 'structural_summary': structural_summary(result),
                  'primary_summary': assessment['primary_summary'], 'all_parent_summary': assessment['all_parent_summary'],
                  'qualified_policy_coverage_all_query_tokens': assessment['qualified_policy_coverage_all_query_tokens'],
                  'synthetic_hypothesis': assessment['synthetic_hypothesis'], 'symbolic_audit_executed': True,
                  'external_or_neural_model_executed': False, 'scientific_acceptance': None,
                  'semantic_evaluation_metrics': None, 'source_identities_admitted': 0, 'semantic_labels_admitted': 0,
                  'independent_reviews_admitted': 0, 'untouched_test_units_admitted': 0,
                  'natural_targets_rescored': 0, 'retrieval_decisions_changed': 0, 'new_network_requests': 0}
        write(RUN + '/report.json', report)
        manifest.update(state='completed', finished_at_utc=datetime.now(timezone.utc).isoformat(),
                        outcome='synthetic_forced_origin_hypothesis_met' if assessment['synthetic_hypothesis']['passed'] else 'synthetic_forced_origin_hypothesis_failed',
                        output_hashes={p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT / RUN).iterdir() if p.name != 'manifest.json'})
        write(RUN + '/manifest.json', manifest)
        print(json.dumps(report, indent=2))
    except Exception as error:
        manifest.update(state='failed', error=f'{type(error).__name__}: {error}')
        write(RUN + '/manifest.json', manifest)
        raise


if __name__ == '__main__':
    main()
