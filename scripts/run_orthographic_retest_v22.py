"""One-shot retest with unchanged v20 scoring and full-panel gate."""
from pathlib import Path
import json
import platform
import sys
import time
from fl_decipher.corpus import digest, dump_json
from fl_decipher.natural_v12 import utc
from fl_decipher.orthographic_v20 import calibrate, compare_target
from fl_decipher.orthographic_retest_v22 import group_accounting, group_removal_support

ROOT = Path(__file__).resolve().parents[1]

def read(path):
    return json.loads(path.read_text())


def main():
    cp, bp = ROOT/'experiments/kamri_orthographic_retest_v22.json', ROOT/'benchmarks/kamri_orthographic_retest_v22.json'
    config, benchmark = read(cp), read(bp)
    for p, sha in benchmark['input_hashes'].items():
        assert digest((ROOT/p).read_bytes()) == sha, p
    panel, target = read(ROOT/benchmark['panel']), read(ROOT/benchmark['target'])
    prior = read(ROOT/'experiments/kamri_orthographic_v20.json')
    assert all(config[k] == prior[k] for k in ['rule', 'calibration_gate', 'lure_surface', 'target_uid', 'target_gaps'])
    assert config['registered_at_utc'] < panel['sealed_at_utc'] == target['sealed_at_utc'] <= benchmark['frozen_at_utc']
    assert [u['uid'] for u in panel['units']] == config['calibration_uids'] and len(panel['units']) == 19
    out = ROOT/'runs/000022_kamri_orthographic_retest'
    out.mkdir(exist_ok=False)
    code = sorted([*(ROOT/'src/fl_decipher').glob('*.py'), *(ROOT/'scripts').glob('*.py'), *(ROOT/'tests').glob('*.py')])
    flags = {'model_executed': True, 'model_kind': 'frozen Unicode orthographic copying proposal rule',
             'translation_model_executed': False, 'new_lexical_induction_executed': False, 'shared_lexicons_used': False}
    manifest = {'run_id': out.name, 'experiment_id': config['experiment_id'], 'stage': config['stage'], 'state': 'running',
                'started_at_utc': utc(), **flags, 'unit_denominator': 19, 'token_pair_denominator': 476,
                'connected_group_denominator': 5, 'cross_group_comparison_denominator': 274,
                'target_unit_denominator': 1, 'target_hypothesis_denominator': 2, 'python': sys.version, 'platform': platform.platform(),
                'input_hashes': benchmark['input_hashes'] | {str(bp.relative_to(ROOT)): digest(bp.read_bytes())},
                'code_hashes': {str(p.relative_to(ROOT)): digest(p.read_bytes()) for p in code}}
    dump_json(out/'manifest.json', manifest)
    start = time.monotonic()
    try:
        calibration = calibrate(panel['units'], config)
        groups = group_accounting(calibration, panel['units'])
        removal = group_removal_support(calibration, panel['units'], config['calibration_gate'])
        assert len(groups) == len(removal) == 5
        for r in calibration['rules'].values():
            assert r['summary']['cross_component_comparisons'] == 274
            assert r['summary']['fl_token_denominator'] == r['summary']['source_token_denominator'] == 476
        dump_json(out/'calibration.json', calibration)
        dump_json(out/'group_accounting.json', groups)
        dump_json(out/'group_removal_support.json', removal)
        files = ['calibration.json', 'group_accounting.json', 'group_removal_support.json']
        seal = {'sealed_at_utc': utc(), 'calibration_artifact_hashes': {p: digest((out/p).read_bytes()) for p in files},
                'rule_config_sha256': digest(cp.read_bytes()), 'rule_implementation_sha256': digest((ROOT/config['rule_implementation']).read_bytes()),
                'primary_gate': calibration['rules']['primary']['gate'], 'target_used_for_calibration': False,
                'group_removal_used_for_primary_decision': False}
        dump_json(out/'calibration_seal.json', seal)
        started = utc()
        result = compare_target(target['target'], target['target']['alignments'], calibration)
        result['comparison_started_at_utc'] = started
        dump_json(out/'target_comparison.json', result)
        report = {'experiment_id': config['experiment_id'], 'stage': config['stage'], **flags,
                  'calibration_unit_denominator': 19, 'token_pair_denominator': 476, 'connected_group_denominator': 5,
                  'cross_group_comparison_denominator': 274, 'target_uid': config['target_uid'], 'target_hypothesis_denominator': 2,
                  'calibration': {n: {'summary': r['summary'], 'gate': r['gate']} for n, r in calibration['rules'].items()},
                  'group_accounting': groups, 'group_removal_support': removal,
                  'target': {n: {k: v for k, v in r.items() if k not in ['anchor_ledger', 'hypotheses']} for n, r in result['rules'].items()},
                  'primary_gap_lead': result['primary_gap_lead'], 'original_v19_gaps': [1, 2], 'original_hypotheses_modified': False,
                  'semantic_training_eligible_tokens': 0, 'untouched_test_eligible_units': 0, 'current_raw_fl': False,
                  'source_identity_claims_admitted': 0, 'calibration_sealed_before_target': True,
                  'limits': ['Previously exposed panel/rule/target, not untouched validation', 'Group-removal summaries are descriptive positive-support diagnostics only',
                             'Copied names can survive source-absent frame lures; no source-identity classifier',
                             'Minimum breadth is an engineering gate, not semantic accuracy or statistical confidence',
                             'Original v20 failure, v19 alternatives and v18 length gate remain unchanged']}
        dump_json(out/'report.json', report)
        md = '# Experiment 22: unchanged orthographic retest\n\n'
        md += 'Nineteen fixed units, five exposed connected groups, 476 token pairs. The byte-unchanged v20 rule and calibration thresholds execute on the v21 frozen panel. Target 03:007 remains excluded from calibration.\n\n'
        md += '| Rule | Proposals | Support units | Keys | Diacritic-dependent | Conflicts | Wrong-name proposals / views | Cross-group proposals / comparisons | Frame-lure proposals / views | Gate |\n|---|---:|---:|---:|---:|---:|---|---|---|---|\n'
        for n, r in calibration['rules'].items():
            s = r['summary']
            md += f"| {n} | {s['proposals']} | {len(s['support_units'])} | {len(s['keys'])} | {s['diacritic_dependent']} | {s['positional_conflicts']} | {s['wrong_name_proposals']} / {s['wrong_name_views']} | {s['cross_component_proposals']} / {s['cross_component_comparisons']} | {s['frame_lure_proposals']} / {s['frame_lure_views']} | {'passes' if r['gate']['conditional_anchor_calibration_eligible'] else 'fails'} |\n"
        md += '\n| Connected group | Units | Token pairs | Primary proposals | Primary keys | Primary support units |\n|---|---:|---:|---:|---|---|\n'
        for g in groups:
            s = g['rules']['primary']
            md += f"| {', '.join(g['connected_group'])} | {g['unit_denominator']} | {g['token_pair_denominator']} | {s['proposals']} | {s['keys']} | {s['support_units']} |\n"
        md += f"\nPrimary unmet requirements: {calibration['rules']['primary']['gate']['unmet']}.\n\n"
        md += '| Target rule | Gap 1 matches | Gap 2 matches | Descriptive maximizers | Eligible gap lead |\n|---|---:|---:|---|---|\n'
        for n, r in result['rules'].items():
            md += f"| {n} | {r['hypotheses'][0]['anchor_matches']} | {r['hypotheses'][1]['anchor_matches']} | {r['descriptive_maximizers']} | {r['eligible_gap_lead']} |\n"
        md += '\nAll nineteen units and complete control horizons are retained. Every group-removal summary reports remaining positive support and does not recalibrate controls or change the full-panel decision. Calibration and group ledgers were sealed before target scoring. Name-frame lure survival is a source-specificity limitation; no semantic, source-identity, raw-FL or untouched-test admission occurs.\n'
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
