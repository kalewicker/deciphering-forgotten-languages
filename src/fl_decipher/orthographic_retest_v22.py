"""Panel adaptation and source-group accounting; v20 scoring remains unchanged."""
import json


def adapt_panel(units, excluded_uid):
    uids = [u['uid'] for u in units]
    if len(uids) != len(set(uids)) or excluded_uid in uids:
        raise ValueError('Duplicate UID or excluded target in calibration')
    result = []
    for u in units:
        if len(u['fl_tokens']) != len(u['source_tokens']):
            raise ValueError('Unequal packet token counts')
        component = json.dumps(u['connected_group'], ensure_ascii=False, separators=(',', ':'))
        result.append(u | {'component': component})
    return result


def positive_support(unit_results):
    proposals = [a for u in unit_results for a in u['result']['proposals']]
    return {'proposals': len(proposals), 'support_units': [u['uid'] for u in unit_results if u['result']['proposals']],
            'keys': sorted({a['key'] for a in proposals}),
            'diacritic_dependent': sum(a['diacritic_dependent'] for a in proposals),
            'positional_conflicts': sum(not a['positional_agreement'] for a in proposals)}


def group_accounting(calibration, panel):
    groups = []
    for component in sorted({u['component'] for u in panel}):
        selected = [u for u in panel if u['component'] == component]
        uids = [u['uid'] for u in selected]
        rules = {}
        for name, r in calibration['rules'].items():
            units = [u for u in r['units'] if u['uid'] in uids]
            wrong = [x for x in r['wrong_name_controls'] if x['uid'] in uids]
            cross = [x for x in r['cross_component_controls'] if x['fl_uid'] in uids]
            frames = [x for x in r['frame_lures'] if x['uid'] in uids]
            assert len(cross) == len(selected)*(len(panel)-len(selected))
            rules[name] = positive_support(units) | {
                'fl_candidates': sum(u['result']['fl_candidates'] for u in units),
                'source_candidates': sum(u['result']['source_candidates'] for u in units),
                'abstentions': sum(u['result']['abstentions'] for u in units),
                'wrong_name_views': len(wrong), 'wrong_name_proposals': sum(x['result']['proposal_denominator'] for x in wrong),
                'cross_group_comparisons': len(cross), 'cross_group_proposals': sum(x['result']['proposal_denominator'] for x in cross),
                'frame_lure_views': len(frames), 'frame_lure_proposals': sum(x['result']['proposal_denominator'] for x in frames)}
        groups.append({'component': component, 'connected_group': json.loads(component), 'unit_uids': uids,
                       'unit_denominator': len(selected), 'token_pair_denominator': sum(len(u['fl_tokens']) for u in selected), 'rules': rules})
    return groups


def group_removal_support(calibration, panel, limits):
    rows = []
    for component in sorted({u['component'] for u in panel}):
        keep = [u for u in panel if u['component'] != component]
        rules = {}
        for name, r in calibration['rules'].items():
            s = positive_support([u for u in r['units'] if u['component'] != component])
            requirements = {'minimum_proposals': s['proposals'] >= limits['min_proposals'],
                            'minimum_support_units': len(s['support_units']) >= limits['min_units'],
                            'minimum_distinct_keys': len(s['keys']) >= limits['min_keys'],
                            'diacritic_dependent_support': s['diacritic_dependent'] >= limits['min_diacritic_dependent'],
                            'no_positional_conflicts': s['positional_conflicts'] <= limits['max_positional_conflicts']}
            rules[name] = s | {'positive_requirements': requirements, 'positive_conditions_met': all(requirements.values())}
        rows.append({'removed_group': json.loads(component), 'removed_uids': [u['uid'] for u in panel if u['component'] == component],
                     'remaining_unit_denominator': len(keep), 'remaining_token_pair_denominator': sum(len(u['fl_tokens']) for u in keep),
                     'rules': rules, 'full_calibration_gate_recomputed': False, 'used_for_primary_decision': False, 'fresh_holdout': False})
    return rows
