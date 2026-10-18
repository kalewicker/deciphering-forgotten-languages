"""One-shot deterministic anchor diagnostic; calibration sealed before target scoring."""
from pathlib import Path
import json
import platform
import sys
import time
from fl_decipher.corpus import digest, dump_json
from fl_decipher.natural_v12 import utc
from fl_decipher.orthographic_v20 import calibrate, compare_target

ROOT = Path(__file__).resolve().parents[1]

def read(path):
    return json.loads(path.read_text())


def main():
    cp, bp = ROOT/'experiments/kamri_orthographic_v20.json', ROOT/'benchmarks/kamri_orthographic_v20.json'
    config, benchmark = read(cp), read(bp)
    for path, sha in benchmark['input_hashes'].items():
        assert digest((ROOT/path).read_bytes()) == sha, path
    panel, target = read(ROOT/benchmark['panel']), read(ROOT/benchmark['target'])
    assert config['registered_at_utc'] < panel['sealed_at_utc'] == target['sealed_at_utc'] <= benchmark['frozen_at_utc']
    out = ROOT/'runs/000020_kamri_orthographic_anchors'
    out.mkdir(exist_ok=False)
    code = sorted([*(ROOT/'src/fl_decipher').glob('*.py'), *(ROOT/'scripts').glob('*.py'), *(ROOT/'tests').glob('*.py')])
    flags = {'model_executed': True, 'model_kind': 'frozen Unicode orthographic copying proposal rule',
             'translation_model_executed': False, 'new_lexical_induction_executed': False, 'shared_lexicons_used': False}
    manifest = {'run_id': out.name, 'experiment_id': config['experiment_id'], 'stage': config['stage'],
                'state': 'running', 'started_at_utc': utc(), **flags,
                'unit_denominator': 11, 'target_unit_denominator': 1, 'target_hypothesis_denominator': 2,
                'python': sys.version, 'platform': platform.platform(),
                'input_hashes': benchmark['input_hashes'] | {str(bp.relative_to(ROOT)): digest(bp.read_bytes())},
                'code_hashes': {str(p.relative_to(ROOT)): digest(p.read_bytes()) for p in code}}
    dump_json(out/'manifest.json', manifest)
    start = time.monotonic()
    try:
        assert [u['uid'] for u in panel['units']] == config['calibration_uids']
        calibration = calibrate(panel['units'], config)
        dump_json(out/'calibration.json', calibration)
        seal = {'sealed_at_utc': utc(), 'calibration_sha256': digest((out/'calibration.json').read_bytes()),
                'rule_config_sha256': digest(cp.read_bytes()), 'target_used_for_calibration': False,
                'primary_gate': calibration['rules']['primary']['gate']}
        dump_json(out/'calibration_seal.json', seal)
        target_started = utc()
        result = compare_target(target['target'], target['target']['alignments'], calibration)
        result['comparison_started_at_utc'] = target_started
        dump_json(out/'target_comparison.json', result)
        report = {'experiment_id': config['experiment_id'], 'stage': config['stage'], **flags,
                  'calibration_unit_denominator': 11, 'component_denominator': 2,
                  'target_uid': config['target_uid'], 'target_unit_denominator': 1, 'target_hypothesis_denominator': 2,
                  'calibration': {n: {'summary': r['summary'], 'gate': r['gate']} for n, r in calibration['rules'].items()},
                  'target': {n: {k: v for k, v in r.items() if k not in ('anchor_ledger', 'hypotheses')} for n, r in result['rules'].items()},
                  'primary_gap_lead': result['primary_gap_lead'], 'original_v19_gaps': [1, 2], 'original_hypotheses_modified': False,
                  'semantic_training_eligible_tokens': 0, 'untouched_test_eligible_units': 0, 'current_raw_fl': False,
                  'source_identity_claims_admitted': 0, 'calibration_sealed_before_target': True,
                  'limits': ['Previously exposed rules and panel; no held-out or semantic accuracy',
                             'Names alone can survive source-absent frame lures; no source-identity classifier',
                             'Calibration minima are breadth requirements, not statistical guarantees',
                             'Original v18 gate and v19 primary/secondary ties remain unchanged']}
        dump_json(out/'report.json', report)
        primary = calibration['rules']['primary']
        md = '# Experiment 20: orthographic-anchor diagnostic\n\n'
        md += 'Eleven fixed development pairs, two exposed components, frozen folded-spelling rule and descriptive exact NFC baseline. Target 03:007 is excluded from calibration. Every token and all negative comparisons remain in the ledgers.\n\n'
        md += '| Rule | Proposals | Support units | Distinct keys | Diacritic-dependent | Positional conflicts | Wrong-name proposals / views | Other-component proposals / comparisons | Name-frame lure proposals / views | Calibration gate |\n|---|---:|---:|---:|---:|---:|---|---|---|---|\n'
        for n, r in calibration['rules'].items():
            s = r['summary']
            md += f"| {n} | {s['proposals']} | {len(s['support_units'])} | {len(s['keys'])} | {s['diacritic_dependent']} | {s['positional_conflicts']} | {s['wrong_name_proposals']} / {s['wrong_name_views']} | {s['cross_component_proposals']} / {s['cross_component_comparisons']} | {s['frame_lure_proposals']} / {s['frame_lure_views']} | {'passes' if r['gate']['conditional_anchor_calibration_eligible'] else 'fails'} |\n"
        md += f"\nPrimary unmet calibration requirements: {primary['gate']['unmet']}. All zero-coverage units remain in the eleven-unit denominator. Name-preserving source-absent lure proposals are descriptive failures of source specificity; they are not positive calibration support.\n\n"
        md += '| Target rule | Gap 1 anchor matches | Gap 2 anchor matches | Descriptive maximizers | Eligible gap lead |\n|---|---:|---:|---|---|\n'
        for n, r in result['rules'].items():
            h = r['hypotheses']
            md += f"| {n} | {h[0]['anchor_matches']} | {h[1]['anchor_matches']} | {r['descriptive_maximizers']} | {r['eligible_gap_lead']} |\n"
        md += '\nThe calibration ledger, rules and gate were sealed before target scoring. A mechanical target preference cannot bypass the primary calibration gate. Original v19 hypotheses [1,2], the fourteen primary v19 maximizers and the v18 equal-length failure are preserved. No source identity, word meanings, semantic training labels, current raw FL or untouched test units are admitted. No p-value or fitted model is claimed.\n'
        (out/'report.md').write_text(md)
        manifest.update(state='completed', outcome='conditional_orthographic_gap_lead' if result['primary_gap_lead'] is not None else 'orthographic_gap_selection_unavailable',
                        finished_at_utc=utc(), elapsed_seconds=time.monotonic()-start,
                        output_hashes={p.name: digest(p.read_bytes()) for p in out.iterdir() if p.name != 'manifest.json'})
        dump_json(out/'manifest.json', manifest)
        print(json.dumps({'calibration': report['calibration'], 'target': report['target'], 'primary_gap_lead': report['primary_gap_lead']}, indent=2))
    except Exception as error:
        manifest.update(state='failed', error=f'{type(error).__name__}: {error}')
        dump_json(out/'manifest.json', manifest)
        raise

if __name__ == '__main__':
    main()
