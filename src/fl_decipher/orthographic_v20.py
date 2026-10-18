"""Frozen copying hypotheses with explicit eligibility, multiplicity and controls."""
from collections import Counter
import unicodedata

RULES = ('primary', 'baseline')


def exact(surface):
    return unicodedata.normalize('NFC', surface).casefold()


def folded(surface):
    return ''.join(c for c in unicodedata.normalize('NFD', surface.casefold())
                   if not unicodedata.category(c).startswith('M'))


def eligible(token):
    s = token['view_surface']
    key = folded(s)
    return token['index'] > 0 and bool(s) and s[0].isupper() and len(key) >= 4 and all('a' <= c <= 'z' for c in key)


def proposal(fl, english, rule):
    if rule not in RULES:
        raise ValueError('Unregistered rule')
    spelling = folded if rule == 'primary' else exact
    fk = [spelling(t['view_surface']) for t in fl]
    ek = [spelling(t['view_surface']) for t in english]
    fc, ec = Counter(fk), Counter(ek)
    rows, proposals = [], []
    for i, t in enumerate(fl):
        candidates = [j for j, key in enumerate(ek) if key == fk[i]] if eligible(t) else []
        if not eligible(t):
            status = 'outside_capitalized_latin_rule'
        elif not candidates:
            status = 'no_equal_english_key'
        elif fc[fk[i]] != 1 or ec[fk[i]] != 1:
            status = 'ambiguous_key_occurrence'
        elif not eligible(english[candidates[0]]):
            status = 'english_candidate_ineligible'
        else:
            status = 'proposed'
            source = english[candidates[0]]
            proposals.append({'key': fk[i], 'fl_token': t, 'source_token': source,
                              'positional_agreement': t['index'] == source['index'],
                              'diacritic_dependent': exact(t['view_surface']) != exact(source['view_surface'])})
        rows.append({'fl_token': t, 'key': fk[i], 'eligible': eligible(t),
                     'equal_english_indices': [english[j]['index'] for j in candidates], 'status': status})
    return {'fl_token_denominator': len(fl), 'source_token_denominator': len(english),
            'fl_candidates': sum(eligible(t) for t in fl), 'source_candidates': sum(eligible(t) for t in english),
            'fl_ledger': rows,
            'source_ledger': [{'token': t, 'key': ek[i], 'eligible': eligible(t)} for i, t in enumerate(english)],
            'proposals': proposals, 'proposal_denominator': len(proposals),
            'abstentions': len(fl)-len(proposals)}


def name_pool(panel):
    pool = {}
    for unit in panel:
        for t in unit['source_tokens']:
            if eligible(t):
                key = folded(t['surface'])
                pool.setdefault(key, []).append(t)
    return [{'key': key, 'surface': min(t['surface'] for t in rows), 'origins': rows} for key, rows in sorted(pool.items())]


def wrong_name_view(unit, pool):
    replacements, english = [], []
    lookup = {p['key']: pool[(i+1) % len(pool)] for i, p in enumerate(pool)} if len(pool) >= 2 else {}
    for t in unit['source_tokens']:
        if eligible(t) and lookup:
            replacement = lookup[folded(t['surface'])]
            english.append(t | {'view_surface': replacement['surface']})
            replacements.append({'index': t['index'], 'original_token': t,
                                 'replacement_key': replacement['key'], 'replacement_surface': replacement['surface'],
                                 'replacement_origins': replacement['origins']})
        else:
            english.append(t.copy())
    return english, replacements


def frame_lure(unit, surface):
    return [t | {'view_surface': t['surface'] if eligible(t) else surface} for t in unit['source_tokens']]


def calibrate(panel, config):
    pool = name_pool(panel)
    rules = {}
    cross_expected = sum(a['component'] != b['component'] for a in panel for b in panel)
    for rule in RULES:
        units, wrong_names, cross_component, frame_lures = [], [], [], []
        for unit in panel:
            units.append({'uid': unit['uid'], 'component': unit['component'],
                          'result': proposal(unit['fl_tokens'], unit['source_tokens'], rule)})
            view, replacements = wrong_name_view(unit, pool)
            wrong_names.append({'uid': unit['uid'], 'replacements': replacements,
                                'result': proposal(unit['fl_tokens'], view, rule)})
            for other in panel:
                if other['component'] != unit['component']:
                    cross_component.append({'fl_uid': unit['uid'], 'source_uid': other['uid'],
                                            'result': proposal(unit['fl_tokens'], other['source_tokens'], rule)})
            frame_lures.append({'uid': unit['uid'], 'synthetic_source_absent': True,
                                'result': proposal(unit['fl_tokens'], frame_lure(unit, config['lure_surface']), rule),
                                'source_identity_accepted': False})
        anchors = [a for u in units for a in u['result']['proposals']]
        summary = {'unit_denominator': len(panel), 'fl_token_denominator': sum(len(u['fl_tokens']) for u in panel),
                   'source_token_denominator': sum(len(u['source_tokens']) for u in panel),
                   'fl_candidates': sum(u['result']['fl_candidates'] for u in units),
                   'source_candidates': sum(u['result']['source_candidates'] for u in units),
                   'abstentions': sum(u['result']['abstentions'] for u in units), 'proposals': len(anchors),
                   'support_units': [u['uid'] for u in units if u['result']['proposals']],
                   'support_components': sorted({u['component'] for u in units if u['result']['proposals']}),
                   'keys': sorted({a['key'] for a in anchors}),
                   'positional_conflicts': sum(not a['positional_agreement'] for a in anchors),
                   'diacritic_dependent': sum(a['diacritic_dependent'] for a in anchors),
                   'wrong_name_views': len(wrong_names), 'wrong_name_proposals': sum(x['result']['proposal_denominator'] for x in wrong_names),
                   'cross_component_comparisons': len(cross_component), 'cross_component_proposals': sum(x['result']['proposal_denominator'] for x in cross_component),
                   'frame_lure_views': len(frame_lures), 'frame_lure_proposals': sum(x['result']['proposal_denominator'] for x in frame_lures)}
        limits = config['calibration_gate']
        requirements = {'minimum_proposals': summary['proposals'] >= limits['min_proposals'],
                        'minimum_support_units': len(summary['support_units']) >= limits['min_units'],
                        'minimum_distinct_keys': len(summary['keys']) >= limits['min_keys'],
                        'diacritic_dependent_support': summary['diacritic_dependent'] >= limits['min_diacritic_dependent'],
                        'no_positional_conflicts': summary['positional_conflicts'] <= limits['max_positional_conflicts'],
                        'wrong_name_controls_complete': len(pool) >= 2 and len(wrong_names) == config['unit_denominator'],
                        'no_wrong_name_proposals': summary['wrong_name_proposals'] <= limits['max_wrong_name_proposals'],
                        'cross_component_controls_complete': len(cross_component) == cross_expected and cross_expected > 0,
                        'no_cross_component_proposals': summary['cross_component_proposals'] <= limits['max_cross_component_proposals']}
        gate = {'conditional_anchor_calibration_eligible': all(requirements.values()), 'requirements': requirements,
                'unmet': [k for k, v in requirements.items() if not v], 'semantic_training_eligible': False,
                'untouched_test_eligible': False, 'source_identity_classifier': False}
        rules[rule] = {'units': units, 'wrong_name_controls': wrong_names, 'cross_component_controls': cross_component,
                       'frame_lures': frame_lures, 'summary': summary, 'gate': gate}
    return {'name_pool': pool, 'rules': rules, 'target_used_for_calibration': False, 'rule_fitted_or_changed': False}


def compare_target(target, alignments, calibration):
    rules = {}
    for rule in RULES:
        anchors = proposal(target['fl_tokens'], target['source_tokens'], rule)
        pairs = {(a['fl_token']['index'], a['source_token']['index']) for a in anchors['proposals']}
        hypotheses = []
        for a in alignments:
            rows = [row | {'orthographic_anchor_agreement': (row['fl_token']['index'], row['source_token']['index']) in pairs} for row in a['rows']]
            hypotheses.append({'gap': a['gap'], 'unpaired_source_token': a['unpaired_source_token'],
                               'rows': rows, 'anchor_matches': sum(row['orthographic_anchor_agreement'] for row in rows),
                               'anchor_denominator': len(pairs)})
        maximum = max(h['anchor_matches'] for h in hypotheses)
        gaps = [h['gap'] for h in hypotheses if h['anchor_matches'] == maximum]
        available = calibration['rules'][rule]['gate']['conditional_anchor_calibration_eligible'] and target['gap_gate']['development_gap_score_eligible'] and bool(pairs)
        unique = available and len(gaps) == 1
        rules[rule] = {'anchor_ledger': anchors, 'hypotheses': hypotheses, 'maximum_anchor_matches': maximum,
                       'descriptive_maximizers': gaps, 'conditional_comparison_available': bool(available),
                       'unique_conditional_development_lead': bool(unique),
                       'eligible_gap_lead': gaps[0] if unique else None}
    return {'unit_uid': target['uid'], 'hypothesis_denominator': len(alignments), 'original_v19_gaps': [a['gap'] for a in alignments],
            'rules': rules, 'primary_gap_lead': rules['primary']['eligible_gap_lead'],
            'original_hypotheses_modified': False, 'semantic_training_eligible': False,
            'untouched_test_eligible': False, 'source_identity_accepted': False}
