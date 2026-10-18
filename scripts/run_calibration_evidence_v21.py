"""Immutable audit of statement provenance and panel availability."""
from pathlib import Path
import json
import platform
import sys
import time
from fl_decipher.corpus import digest, dump_json
from fl_decipher.natural_v12 import utc
from fl_decipher.calibration_evidence_v21 import audit, assemble

ROOT = Path(__file__).resolve().parents[1]

def read(path):
    return json.loads(path.read_text())


def main():
    cp, bp = ROOT/'experiments/kamri_calibration_evidence_v21.json', ROOT/'benchmarks/kamri_calibration_evidence_v21.json'
    config, benchmark = read(cp), read(bp)
    for p, sha in benchmark['input_hashes'].items():
        assert digest((ROOT/p).read_bytes()) == sha, p
    inputs = read(ROOT/benchmark['inputs'])
    assert config['registered_at_utc'] < inputs['sealed_at_utc'] <= benchmark['frozen_at_utc']
    out = ROOT/'runs/000021_kamri_calibration_evidence'
    out.mkdir(exist_ok=False)
    code = sorted([*(ROOT/'src/fl_decipher').glob('*.py'), *(ROOT/'scripts').glob('*.py'), *(ROOT/'tests').glob('*.py')])
    flags = {'model_executed': False, 'orthographic_rule_executed': False, 'lexical_prediction_executed': False,
             'translation_model_executed': False, 'shared_lexicons_used': False}
    manifest = {'run_id': out.name, 'experiment_id': config['experiment_id'], 'stage': config['stage'], 'state': 'running',
                'started_at_utc': utc(), **flags, 'nominee_denominator': 33, 'comparator_denominator': 11,
                'python': sys.version, 'platform': platform.platform(),
                'input_hashes': benchmark['input_hashes'] | {str(bp.relative_to(ROOT)): digest(bp.read_bytes())},
                'code_hashes': {str(p.relative_to(ROOT)): digest(p.read_bytes()) for p in code}}
    dump_json(out/'manifest.json', manifest)
    start = time.monotonic()
    try:
        nominees = audit(inputs['nominees'], inputs['documents'], config['excluded_target_uid'])
        comparator = audit(inputs['comparator'], inputs['documents'], config['excluded_target_uid'])
        assert nominees['unit_denominator'] == 33 and comparator['unit_denominator'] == 11
        panel = assemble(nominees, comparator, config)
        dump_json(out/'nominee_ledger.json', nominees)
        dump_json(out/'comparator_ledger.json', comparator)
        dump_json(out/'future_panel.json', panel)
        decision = panel['decision']
        eligible = [r for r in nominees['rows'] if r['gate']['development_packet_eligible']]
        report = {'experiment_id': config['experiment_id'], 'stage': config['stage'], **flags,
                  'nominee_denominator': 33, 'nominee_eligible_uids': nominees['eligible_uids'],
                  'nominee_eligible_units': len(eligible), 'nominee_ineligible_units': 33-len(eligible),
                  'comparator_denominator': 11, 'comparator_eligible_uids': comparator['eligible_uids'],
                  'future_panel_units': panel['unit_denominator'], 'future_panel_token_pairs': sum(len(u['fl_tokens']) for u in panel['units']),
                  'nominee_eligible_connected_groups': sorted({tuple(r['connected_group']) for r in eligible}),
                  'nominee_order_checks': len(nominees['order_checks']), 'comparator_order_checks': len(comparator['order_checks']),
                  'decision': decision, 'all_groups_previously_exposed': True,
                  'semantic_training_eligible_tokens': 0, 'untouched_test_eligible_units': 0, 'current_raw_fl_admissions': 0,
                  'source_identity_claims_admitted': 0,
                  'limits': ['Saved normalized/indexed statement boundaries; no new raw FL or acquisition',
                             'Prior extraction review reused; no independent semantic reviewer',
                             'Names and orthographic outcomes never used for nomination or eligibility',
                             'Sparse source/FL order opportunities do not prove whole-article continuity',
                             'Availability decision only; unchanged v20 rule still unvalidated']}
        dump_json(out/'report.json', report)
        md = '# Experiment 21: calibration-evidence availability\n\n'
        md += f"All 33 publisher-backed Kamri nominees are retained. {len(eligible)} pass the conservative development-packet gate; {33-len(eligible)} remain ineligible. The separate prior-panel comparator has {len(comparator['eligible_uids'])}/11 eligible statements. The UID-deduplicated future panel contains {panel['unit_denominator']} units and {report['future_panel_token_pairs']} token pairs.\n\n"
        md += f"Eligible new units outside the prior panel: {len(decision['new_eligible_uids'])}. Additional connected groups: {len(decision['additional_connected_groups'])}. Total future-panel groups: {len(decision['future_panel_groups'])}. Meaningfully broader panel available: {decision['meaningfully_broader_panel_available']}. Unmet decision requirements: {decision['unmet']}. Next step: {decision['next_step']}.\n\n"
        md += '| Nominee | FL / source tokens | Eligible | Unmet requirements |\n|---|---|---|---|\n'
        for r in nominees['rows']:
            md += f"| {r['uid']} | {r['fl_token_count']} / {r['source_token_count']} | {r['gate']['development_packet_eligible']} | {', '.join(r['gate']['unmet']) or 'none'} |\n"
        md += '\nEvery raw token occurrence, partial group, duplicate support view, complete statement span, token offset and observed order comparison is retained. Future-panel packets fail closed across conflicting evidence routes. All groups were previously exposed. No orthographic rule, lexical model or target comparison executed; this is an evidence-availability audit. The archived v20 failure and v19 alternatives remain unchanged. Semantic, untouched-test, current-raw-FL and source-identity admissions remain zero.\n'
        (out/'report.md').write_text(md)
        manifest.update(state='completed', outcome='broader_development_panel_available' if decision['meaningfully_broader_panel_available'] else 'prioritize_evidence_acquisition',
                        finished_at_utc=utc(), elapsed_seconds=time.monotonic()-start,
                        output_hashes={p.name: digest(p.read_bytes()) for p in out.iterdir() if p.name != 'manifest.json'})
        dump_json(out/'manifest.json', manifest)
        print(json.dumps(report, indent=2))
    except Exception as error:
        manifest.update(state='failed', error=f'{type(error).__name__}: {error}')
        dump_json(out/'manifest.json', manifest)
        raise

if __name__ == '__main__':
    main()
