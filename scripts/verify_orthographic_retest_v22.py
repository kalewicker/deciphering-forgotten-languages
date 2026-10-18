"""Independent retest replay using frozen v20 verification primitives, not its scorer."""
from pathlib import Path
import json
from fl_decipher.corpus import digest, dump_json
from fl_decipher.natural_v12 import utc
from fl_decipher.text import tokens
from verify_correspondence_v6 import check_hashes
from verify_orthographic_v20 import replay_proposals, candidate, plain, nfc

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads(path.read_text())


def replay_calibration(panel):
    all_names = [t for u in panel for t in u['source_tokens'] if candidate(t)]
    pool = []
    for key in sorted(set(plain(t['surface']) for t in all_names)):
        origins = [t for t in all_names if plain(t['surface']) == key]
        pool.append({'key': key, 'surface': sorted(t['surface'] for t in origins)[0], 'origins': origins})
    rules = {}
    for name in ['primary', 'baseline']:
        units, wrong_names, cross, frames = [], [], [], []
        for u in panel:
            units.append({'uid': u['uid'], 'component': u['component'], 'result': replay_proposals(u['fl_tokens'], u['source_tokens'], name)})
            view, replacements = [], []
            for t in u['source_tokens']:
                replacement = None
                if candidate(t) and len(pool) >= 2:
                    at = next(i for i, p in enumerate(pool) if p['key'] == plain(t['surface']))
                    replacement = pool[(at+1) % len(pool)]
                if replacement is None:
                    view.append(dict(t))
                else:
                    assert replacement['key'] != plain(t['surface'])
                    view.append(dict(t, view_surface=replacement['surface']))
                    replacements.append({'index': t['index'], 'original_token': t, 'replacement_key': replacement['key'],
                                         'replacement_surface': replacement['surface'], 'replacement_origins': replacement['origins']})
            wrong_names.append({'uid': u['uid'], 'replacements': replacements, 'result': replay_proposals(u['fl_tokens'], view, name)})
            for other in panel:
                if other['connected_group'] != u['connected_group']:
                    cross.append({'fl_uid': u['uid'], 'source_uid': other['uid'], 'result': replay_proposals(u['fl_tokens'], other['source_tokens'], name)})
            frame = [dict(t, view_surface=t['surface'] if candidate(t) else 'xqframe') for t in u['source_tokens']]
            frames.append({'uid': u['uid'], 'synthetic_source_absent': True, 'result': replay_proposals(u['fl_tokens'], frame, name), 'source_identity_accepted': False})
        anchors = [a for u in units for a in u['result']['proposals']]
        summary = {'unit_denominator': 19, 'fl_token_denominator': sum(len(u['fl_tokens']) for u in panel),
                   'source_token_denominator': sum(len(u['source_tokens']) for u in panel),
                   'fl_candidates': sum(u['result']['fl_candidates'] for u in units), 'source_candidates': sum(u['result']['source_candidates'] for u in units),
                   'abstentions': sum(u['result']['abstentions'] for u in units), 'proposals': len(anchors),
                   'support_units': [u['uid'] for u in units if u['result']['proposals']],
                   'support_components': sorted(set(u['component'] for u in units if u['result']['proposals'])),
                   'keys': sorted(set(a['key'] for a in anchors)), 'positional_conflicts': sum(not a['positional_agreement'] for a in anchors),
                   'diacritic_dependent': sum(a['diacritic_dependent'] for a in anchors),
                   'wrong_name_views': len(wrong_names), 'wrong_name_proposals': sum(len(x['result']['proposals']) for x in wrong_names),
                   'cross_component_comparisons': len(cross), 'cross_component_proposals': sum(len(x['result']['proposals']) for x in cross),
                   'frame_lure_views': len(frames), 'frame_lure_proposals': sum(len(x['result']['proposals']) for x in frames)}
        req = {'minimum_proposals': len(anchors) >= 3, 'minimum_support_units': len(summary['support_units']) >= 3,
               'minimum_distinct_keys': len(summary['keys']) >= 3, 'diacritic_dependent_support': summary['diacritic_dependent'] >= 1,
               'no_positional_conflicts': summary['positional_conflicts'] == 0, 'wrong_name_controls_complete': len(pool) >= 2 and len(wrong_names) == 19,
               'no_wrong_name_proposals': summary['wrong_name_proposals'] == 0, 'cross_component_controls_complete': len(cross) == 274,
               'no_cross_component_proposals': summary['cross_component_proposals'] == 0}
        gate = {'conditional_anchor_calibration_eligible': all(req.values()), 'requirements': req, 'unmet': [k for k, v in req.items() if not v],
                'semantic_training_eligible': False, 'untouched_test_eligible': False, 'source_identity_classifier': False}
        assert len(units) == len(wrong_names) == len(frames) == 19 and len(cross) == 274
        rules[name] = {'units': units, 'wrong_name_controls': wrong_names, 'cross_component_controls': cross,
                       'frame_lures': frames, 'summary': summary, 'gate': gate}
    return {'name_pool': pool, 'rules': rules, 'target_used_for_calibration': False, 'rule_fitted_or_changed': False}


def positive_summary(units):
    anchors = [a for u in units for a in u['result']['proposals']]
    return {'proposals': len(anchors), 'support_units': [u['uid'] for u in units if u['result']['proposals']],
            'keys': sorted(set(a['key'] for a in anchors)), 'diacritic_dependent': sum(a['diacritic_dependent'] for a in anchors),
            'positional_conflicts': sum(a['positional_agreement'] is False for a in anchors)}


def group_outputs(calibration, panel):
    accounting, removal = [], []
    for comp in sorted(set(u['component'] for u in panel)):
        group_units = [u for u in panel if u['component'] == comp]
        uids = [u['uid'] for u in group_units]
        keep = [u for u in panel if u['component'] != comp]
        positive, dropped = {}, {}
        for name, r in calibration['rules'].items():
            units = [u for u in r['units'] if u['uid'] in uids]
            controls = [[x for x in r[key] if x[uid_field] in uids] for key, uid_field in [('wrong_name_controls', 'uid'), ('cross_component_controls', 'fl_uid'), ('frame_lures', 'uid')]]
            wrong, cross, frame = controls
            positive[name] = positive_summary(units) | {
                'fl_candidates': sum(u['result']['fl_candidates'] for u in units), 'source_candidates': sum(u['result']['source_candidates'] for u in units),
                'abstentions': sum(u['result']['abstentions'] for u in units),
                'wrong_name_views': len(wrong), 'wrong_name_proposals': sum(len(x['result']['proposals']) for x in wrong),
                'cross_group_comparisons': len(cross), 'cross_group_proposals': sum(len(x['result']['proposals']) for x in cross),
                'frame_lure_views': len(frame), 'frame_lure_proposals': sum(len(x['result']['proposals']) for x in frame)}
            assert len(cross) == len(uids)*(19-len(uids))
            s = positive_summary([u for u in r['units'] if u['uid'] not in uids])
            req = {'minimum_proposals': s['proposals'] >= 3, 'minimum_support_units': len(s['support_units']) >= 3,
                   'minimum_distinct_keys': len(s['keys']) >= 3, 'diacritic_dependent_support': s['diacritic_dependent'] >= 1,
                   'no_positional_conflicts': s['positional_conflicts'] == 0}
            dropped[name] = s | {'positive_requirements': req, 'positive_conditions_met': all(req.values())}
        accounting.append({'component': comp, 'connected_group': json.loads(comp), 'unit_uids': uids,
                           'unit_denominator': len(uids), 'token_pair_denominator': sum(len(u['fl_tokens']) for u in group_units), 'rules': positive})
        removal.append({'removed_group': json.loads(comp), 'removed_uids': uids, 'remaining_unit_denominator': len(keep),
                        'remaining_token_pair_denominator': sum(len(u['fl_tokens']) for u in keep), 'rules': dropped,
                        'full_calibration_gate_recomputed': False, 'used_for_primary_decision': False, 'fresh_holdout': False})
    return accounting, removal


def main():
    out = ROOT/'runs/000022_kamri_orthographic_retest'
    m = check_hashes(out)
    cp = ROOT/'experiments/kamri_orthographic_retest_v22.json';config = read(cp)
    benchmark = read(ROOT/'benchmarks/kamri_orthographic_retest_v22.json')
    panel_file, target_file = read(ROOT/benchmark['panel']), read(ROOT/benchmark['target'])
    panel, target = panel_file['units'], target_file['target']
    report = read(out/'report.json')
    for p, sha in config['input_hashes'].items():
        assert digest((ROOT/p).read_bytes()) == sha, p
    v20_config = read(ROOT/'experiments/kamri_orthographic_v20.json')
    assert all(config[k] == v20_config[k] for k in ['rule', 'calibration_gate', 'lure_surface', 'target_uid', 'target_gaps'])
    assert config['calibration_gate'] == {'min_proposals': 3, 'min_units': 3, 'min_keys': 3, 'min_diacritic_dependent': 1,
                                          'max_positional_conflicts': 0, 'max_wrong_name_proposals': 0, 'max_cross_component_proposals': 0}
    assert config['group_removal_primary_decision'] is False
    assert config['unit_denominator'] == m['unit_denominator'] == report['calibration_unit_denominator'] == 19
    assert config['token_pair_denominator'] == m['token_pair_denominator'] == report['token_pair_denominator'] == 476
    assert config['connected_group_denominator'] == m['connected_group_denominator'] == report['connected_group_denominator'] == 5
    assert config['cross_group_comparison_denominator'] == m['cross_group_comparison_denominator'] == report['cross_group_comparison_denominator'] == 274
    assert config['registered_at_utc'] < panel_file['sealed_at_utc'] == target_file['sealed_at_utc'] <= benchmark['frozen_at_utc'] < m['started_at_utc']
    original = read(ROOT/'runs/000021_kamri_calibration_evidence/future_panel.json')
    assert original['decision']['meaningfully_broader_panel_available'] and original['target_excluded']
    expected = [u | {'component': json.dumps(u['connected_group'], ensure_ascii=False, separators=(',', ':'))} for u in original['units']]
    assert panel == expected and panel_file['target_excluded'] is True
    assert [u['uid'] for u in panel] == config['calibration_uids'] and len(set(u['uid'] for u in panel)) == 19
    assert config['target_uid'] == '03:007' and all(u['uid'] != '03:007' for u in panel)
    assert config['connected_groups'] == [list(g) for g in sorted(set(tuple(u['connected_group']) for u in panel))]
    assert panel_file['origin_panel_sha256'] == digest((ROOT/'runs/000021_kamri_calibration_evidence/future_panel.json').read_bytes())
    original_target = read(ROOT/'data/v20/frozen_target.json')
    assert target == original_target['target'] and target_file['origin_target_sealed_at_utc'] == original_target['sealed_at_utc']
    assert target_file['origin_target_sha256'] == digest((ROOT/'data/v20/frozen_target.json').read_bytes())
    for u in panel:
        assert not u['semantic_gold'] and not u['current_raw_fl'] and not u['untouched_test_eligible'] and u['positional_assumptions_unvalidated']
        for side in ['fl', 'source']:
            d = read(ROOT/u[side+'_document']);statement = u[side+'_statement']
            assert d['text'][slice(*statement['statement_span'])] == statement['text'] and statement['complete_group']
            tt = tokens(statement['text'], statement['statement_span'][0])
            expected_tokens = [{'unit_uid': u['uid'], 'document': u[side+'_document'], 'index': i, 'surface': t.surface,
                                'form': t.normalized, 'span': [t.start, t.end], 'view_surface': t.surface} for i, t in enumerate(tt)]
            assert u[side+'_tokens'] == expected_tokens
        assert len(u['fl_tokens']) == len(u['source_tokens'])
    assert sum(len(u['fl_tokens']) for u in panel) == 476
    sizes = [sum(u['component'] == comp for u in panel) for comp in sorted(set(u['component'] for u in panel))]
    assert sorted(sizes) == [1, 3, 4, 5, 6] and sum(a['component'] != b['component'] for a in panel for b in panel) == 274
    calibration = replay_calibration(panel)
    assert calibration == read(out/'calibration.json')
    groups, removal = group_outputs(calibration, panel)
    assert groups == read(out/'group_accounting.json') == report['group_accounting']
    assert removal == read(out/'group_removal_support.json') == report['group_removal_support']
    for name, rule in calibration['rules'].items():
        assert sum(g['rules'][name]['proposals'] for g in groups) == rule['summary']['proposals']
        assert sum(g['rules'][name]['cross_group_comparisons'] for g in groups) == 274
        assert sum(g['rules'][name]['wrong_name_views'] for g in groups) == sum(g['rules'][name]['frame_lure_views'] for g in groups) == 19
    seal = read(out/'calibration_seal.json')
    assert seal['calibration_artifact_hashes'] == {p: digest((out/p).read_bytes()) for p in ['calibration.json', 'group_accounting.json', 'group_removal_support.json']}
    assert seal['rule_config_sha256'] == digest(cp.read_bytes())
    v20_manifest = read(ROOT/'runs/000020_kamri_orthographic_anchors/manifest.json')
    sha = digest((ROOT/'src/fl_decipher/orthographic_v20.py').read_bytes())
    assert seal['rule_implementation_sha256'] == sha == v20_manifest['code_hashes']['src/fl_decipher/orthographic_v20.py']
    assert seal['primary_gate'] == calibration['rules']['primary']['gate'] and not seal['target_used_for_calibration'] and not seal['group_removal_used_for_primary_decision']
    comparison = read(out/'target_comparison.json')
    assert m['started_at_utc'] < seal['sealed_at_utc'] < comparison['comparison_started_at_utc'] < m['finished_at_utc']
    assert [a['gap'] for a in target['alignments']] == config['target_gaps'] == [1, 2]
    rules = {}
    for name in ['primary', 'baseline']:
        anchors = replay_proposals(target['fl_tokens'], target['source_tokens'], name)
        hypotheses = []
        for a in target['alignments']:
            rows = []
            for row in a['rows']:
                agree = any(p['fl_token']['index'] == row['fl_token']['index'] and p['source_token']['index'] == row['source_token']['index'] for p in anchors['proposals'])
                rows.append(dict(row, orthographic_anchor_agreement=agree))
            hypotheses.append({'gap': a['gap'], 'unpaired_source_token': a['unpaired_source_token'], 'rows': rows,
                               'anchor_matches': sum(row['orthographic_anchor_agreement'] for row in rows), 'anchor_denominator': len(anchors['proposals'])})
        best = max(h['anchor_matches'] for h in hypotheses)
        gaps = [h['gap'] for h in hypotheses if h['anchor_matches'] == best]
        available = calibration['rules'][name]['gate']['conditional_anchor_calibration_eligible'] and target['gap_gate']['development_gap_score_eligible'] and len(anchors['proposals']) > 0
        unique = available and len(gaps) == 1
        rules[name] = {'anchor_ledger': anchors, 'hypotheses': hypotheses, 'maximum_anchor_matches': best, 'descriptive_maximizers': gaps,
                       'conditional_comparison_available': bool(available), 'unique_conditional_development_lead': bool(unique), 'eligible_gap_lead': gaps[0] if unique else None}
    expected_comparison = {'unit_uid': '03:007', 'hypothesis_denominator': 2, 'original_v19_gaps': [1, 2], 'rules': rules,
                           'primary_gap_lead': rules['primary']['eligible_gap_lead'], 'original_hypotheses_modified': False,
                           'semantic_training_eligible': False, 'untouched_test_eligible': False, 'source_identity_accepted': False,
                           'comparison_started_at_utc': comparison['comparison_started_at_utc']}
    assert comparison == expected_comparison and report['primary_gap_lead'] == comparison['primary_gap_lead']
    assert report['calibration'] == {n: {'summary': r['summary'], 'gate': r['gate']} for n, r in calibration['rules'].items()}
    assert report['target'] == {n: {k: v for k, v in r.items() if k not in ['anchor_ledger', 'hypotheses']} for n, r in rules.items()}
    assert report['original_v19_gaps'] == [1, 2] and not report['original_hypotheses_modified'] and report['calibration_sealed_before_target']
    assert report['target_uid'] == '03:007' and report['target_hypothesis_denominator'] == m['target_hypothesis_denominator'] == 2 and m['target_unit_denominator'] == 1
    assert report['semantic_training_eligible_tokens'] == report['untouched_test_eligible_units'] == report['source_identity_claims_admitted'] == 0 and report['current_raw_fl'] is False
    for item in (m, report):
        assert item['model_executed'] and item['model_kind'] == 'frozen Unicode orthographic copying proposal rule'
        assert not item['translation_model_executed'] and not item['new_lexical_induction_executed'] and not item['shared_lexicons_used']
    assert m['outcome'] == ('conditional_orthographic_gap_lead' if comparison['primary_gap_lead'] is not None else 'orthographic_gap_selection_unavailable')
    prior20 = read(ROOT/'runs/000020_kamri_orthographic_anchors/report.json')
    prior19 = read(ROOT/'runs/000019_kamri_single_gap/report.json')
    assert prior20['primary_gap_lead'] is None and not prior20['calibration']['primary']['gate']['conditional_anchor_calibration_eligible']
    assert prior19['observed']['maxima']['primary']['gaps'] == list(range(14)) and prior19['observed']['maxima']['secondary']['gaps'] == [1, 2]
    previous = []
    for directory in sorted(p for p in (ROOT/'runs').glob('0000*') if p.name < out.name):
        check_hashes(directory)
        previous.append({'run_id': directory.name, 'manifest_sha256': digest((directory/'manifest.json').read_bytes())})
    assert len(previous) == 21
    for sealpath in ['reports/000020_deliverable_seal.json', 'reports/000021_deliverable_seal.json']:
        for p, sha in read(ROOT/sealpath)['deliverable_hashes'].items():
            assert digest((ROOT/p).read_bytes()) == sha, p
    receipt = {'state': 'verified', 'verified_at_utc': utc(), 'run_id': out.name, 'manifest_sha256': digest((out/'manifest.json').read_bytes()),
               'calibration': report['calibration'], 'primary_gap_lead': comparison['primary_gap_lead'], 'previous_runs': previous,
               'checks': ['Exact frozen nineteen-unit panel, 476 pairs, target exclusion, connected groups and original source/FL spans',
                          'Byte-unchanged v20 scorer, rules and thresholds; independent Unicode keys and all-token multiplicity',
                          'Every positive, nineteen wrong-name views, 274 cross-group comparisons and nineteen frame lures per rule',
                          'Full group accounting and all five descriptive positive-support removals; no subset-dependent gate',
                          'Calibration-before-target seal and independent replay of both unchanged target alignments',
                          'Original v20 failure and v19 ties, twenty-one prior archives and two latest prior deliverable seals preserved'],
               'limits': report['limits']}
    rp = ROOT/'reports/000022_verification.json';preserved = rp.exists()
    if preserved:
        saved = read(rp)
        assert saved['state'] == 'verified' and saved['manifest_sha256'] == receipt['manifest_sha256'] and saved['calibration'] == receipt['calibration'] and saved['primary_gap_lead'] == receipt['primary_gap_lead']
    else:
        dump_json(rp, receipt)
    print(json.dumps({'state': 'verified', 'units': 19, 'token_pairs': 476, 'cross_group_controls_per_rule': 274,
                      'previous_runs': 21, 'primary_gap_lead': comparison['primary_gap_lead'], 'calibration': report['calibration'], 'existing_receipt_preserved': preserved}, indent=2))

if __name__ == '__main__':
    main()
