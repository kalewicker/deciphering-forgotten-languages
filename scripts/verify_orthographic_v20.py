"""Independent whole-panel key-count replay; does not import v20 execution code."""
from pathlib import Path
import json
import unicodedata
from fl_decipher.corpus import digest, dump_json
from fl_decipher.natural_v12 import utc
from fl_decipher.text import tokens, sentences
from verify_correspondence_v6 import check_hashes

ROOT = Path(__file__).resolve().parents[1]
RULES = ('primary', 'baseline')


def read(path):
    return json.loads(path.read_text())


def nfc(s):
    return unicodedata.normalize('NFC', s).casefold()


def plain(s):
    decomposed = unicodedata.normalize('NFD', s).casefold()
    return ''.join(c for c in decomposed if unicodedata.category(c)[0] != 'M')


def candidate(t):
    surface = t['view_surface']
    key = plain(surface)
    return t['index'] != 0 and bool(surface) and surface[0].isupper() and len(key) >= 4 and key.isascii() and key.isalpha() and key.islower()


def replay_proposals(fl, english, rule):
    keys = plain if rule == 'primary' else nfc
    fk, ek = [keys(t['view_surface']) for t in fl], [keys(t['view_surface']) for t in english]
    proposed, ledger = [], []
    for i, t in enumerate(fl):
        same = [j for j in range(len(english)) if ek[j] == fk[i]] if candidate(t) else []
        status = 'outside_capitalized_latin_rule'
        if candidate(t):
            if not same:
                status = 'no_equal_english_key'
            elif fk.count(fk[i]) > 1 or ek.count(fk[i]) > 1:
                status = 'ambiguous_key_occurrence'
            elif not candidate(english[same[0]]):
                status = 'english_candidate_ineligible'
            else:
                source = english[same[0]]
                status = 'proposed'
                proposed.append({'key': fk[i], 'fl_token': t, 'source_token': source,
                                 'positional_agreement': t['index'] == source['index'],
                                 'diacritic_dependent': nfc(t['view_surface']) != nfc(source['view_surface'])})
        ledger.append({'fl_token': t, 'key': fk[i], 'eligible': candidate(t),
                       'equal_english_indices': [english[j]['index'] for j in same], 'status': status})
    return {'fl_token_denominator': len(fl), 'source_token_denominator': len(english),
            'fl_candidates': sum(candidate(t) for t in fl), 'source_candidates': sum(candidate(t) for t in english),
            'fl_ledger': ledger, 'source_ledger': [{'token': t, 'key': ek[i], 'eligible': candidate(t)} for i, t in enumerate(english)],
            'proposals': proposed, 'proposal_denominator': len(proposed), 'abstentions': len(fl)-len(proposed)}


def replay_calibration(panel):
    eligible_english = [t for unit in panel for t in unit['source_tokens'] if candidate(t)]
    pool = []
    for key in sorted({plain(t['surface']) for t in eligible_english}):
        origins = [t for t in eligible_english if plain(t['surface']) == key]
        pool.append({'key': key, 'surface': sorted(t['surface'] for t in origins)[0], 'origins': origins})
    assert len(pool) >= 2
    results = {}
    for rule in RULES:
        units, wrong_names, cross_component, frame_lures = [], [], [], []
        for u in panel:
            units.append({'uid': u['uid'], 'component': u['component'], 'result': replay_proposals(u['fl_tokens'], u['source_tokens'], rule)})
            view, replacements = [], []
            for t in u['source_tokens']:
                replacement = None
                if candidate(t):
                    position = [i for i, entry in enumerate(pool) if entry['key'] == plain(t['surface'])][0]
                    replacement = pool[(position+1) % len(pool)]
                if replacement is None:
                    view.append(dict(t))
                else:
                    assert replacement['key'] != plain(t['surface'])
                    view.append(dict(t, view_surface=replacement['surface']))
                    replacements.append({'index': t['index'], 'original_token': t,
                                         'replacement_key': replacement['key'], 'replacement_surface': replacement['surface'],
                                         'replacement_origins': replacement['origins']})
            wrong_names.append({'uid': u['uid'], 'replacements': replacements, 'result': replay_proposals(u['fl_tokens'], view, rule)})
            for other in panel:
                if u['component'] == other['component']:
                    continue
                cross_component.append({'fl_uid': u['uid'], 'source_uid': other['uid'], 'result': replay_proposals(u['fl_tokens'], other['source_tokens'], rule)})
            lure = [dict(t, view_surface=t['surface'] if candidate(t) else 'xqframe') for t in u['source_tokens']]
            frame_lures.append({'uid': u['uid'], 'synthetic_source_absent': True,
                                'result': replay_proposals(u['fl_tokens'], lure, rule), 'source_identity_accepted': False})
        anchors = [a for item in units for a in item['result']['proposals']]
        summary = {'unit_denominator': len(panel), 'fl_token_denominator': sum(len(u['fl_tokens']) for u in panel),
                   'source_token_denominator': sum(len(u['source_tokens']) for u in panel),
                   'fl_candidates': sum(u['result']['fl_candidates'] for u in units),
                   'source_candidates': sum(u['result']['source_candidates'] for u in units),
                   'abstentions': sum(u['result']['abstentions'] for u in units), 'proposals': len(anchors),
                   'support_units': [u['uid'] for u in units if len(u['result']['proposals']) > 0],
                   'support_components': sorted(set(u['component'] for u in units if len(u['result']['proposals']) > 0)),
                   'keys': sorted(set(a['key'] for a in anchors)), 'positional_conflicts': sum(a['positional_agreement'] is False for a in anchors),
                   'diacritic_dependent': sum(a['diacritic_dependent'] for a in anchors),
                   'wrong_name_views': len(wrong_names), 'wrong_name_proposals': sum(len(x['result']['proposals']) for x in wrong_names),
                   'cross_component_comparisons': len(cross_component), 'cross_component_proposals': sum(len(x['result']['proposals']) for x in cross_component),
                   'frame_lure_views': len(frame_lures), 'frame_lure_proposals': sum(len(x['result']['proposals']) for x in frame_lures)}
        req = {'minimum_proposals': len(anchors) >= 3, 'minimum_support_units': len(summary['support_units']) >= 3,
               'minimum_distinct_keys': len(summary['keys']) >= 3, 'diacritic_dependent_support': summary['diacritic_dependent'] >= 1,
               'no_positional_conflicts': summary['positional_conflicts'] == 0,
               'wrong_name_controls_complete': len(pool) >= 2 and len(wrong_names) == 11,
               'no_wrong_name_proposals': summary['wrong_name_proposals'] == 0,
               'cross_component_controls_complete': len(cross_component) == 60,
               'no_cross_component_proposals': summary['cross_component_proposals'] == 0}
        gate = {'conditional_anchor_calibration_eligible': all(req.values()), 'requirements': req,
                'unmet': [k for k in req if req[k] is False], 'semantic_training_eligible': False,
                'untouched_test_eligible': False, 'source_identity_classifier': False}
        assert len(cross_component) == 60 and len(units) == len(wrong_names) == len(frame_lures) == 11
        results[rule] = {'units': units, 'wrong_name_controls': wrong_names, 'cross_component_controls': cross_component,
                         'frame_lures': frame_lures, 'summary': summary, 'gate': gate}
    return {'name_pool': pool, 'rules': results, 'target_used_for_calibration': False, 'rule_fitted_or_changed': False}


def document_tokens(uid, path, statement):
    return [{'unit_uid': uid, 'document': path, 'index': i, 'surface': t.surface, 'form': t.normalized,
             'span': [t.start, t.end], 'view_surface': t.surface} for i, t in enumerate(tokens(statement['text'], statement['span'][0]))]


def verify_statement(path, statement):
    doc = read(ROOT/path)
    assert doc['text'][slice(*statement['span'])] == statement['text']
    found = []
    for block in doc['blocks']:
        for s in sentences(block['text']):
            if s.text == statement['text']:
                found.append({'span': [block['span'][0]+s.start, block['span'][0]+s.end], 'block_id': block['id']})
    assert found == [{'span': statement['span'], 'block_id': statement['block_id']}]
    assert statement['text'].rstrip().endswith('.')
    return doc


def main():
    out = ROOT/'runs/000020_kamri_orthographic_anchors'
    m = check_hashes(out)
    config = read(ROOT/'experiments/kamri_orthographic_v20.json')
    benchmark = read(ROOT/'benchmarks/kamri_orthographic_v20.json')
    panel, target_file = read(ROOT/benchmark['panel']), read(ROOT/benchmark['target'])
    target = target_file['target']
    report = read(out/'report.json')
    for path, sha in config['input_hashes'].items():
        assert digest((ROOT/path).read_bytes()) == sha, path
    expected_uids = [f'{component}:{n:03d}' for component, maximum in [('03', 6), ('13', 5)] for n in range(1, maximum+1)]
    assert config['calibration_uids'] == expected_uids and config['target_uid'] == target['uid'] == '03:007'
    assert config['unit_denominator'] == 11 and config['target_gaps'] == [1, 2]
    assert config['components'] == ['nichiren_images', 'dark_side_light'] and config['lure_surface'] == 'xqframe'
    assert config['calibration_gate'] == {'min_proposals': 3, 'min_units': 3, 'min_keys': 3, 'min_diacritic_dependent': 1,
                                          'max_positional_conflicts': 0, 'max_wrong_name_proposals': 0, 'max_cross_component_proposals': 0}
    assert config['rule'] == {'primary': 'NFD casefold remove all Unicode mark categories', 'baseline': 'NFC casefold exact',
                              'min_letters': 4, 'noninitial': True, 'uppercase_initial': True, 'folded_ascii_letters_only': True, 'unique_in_entire_statement': True}
    assert config['registered_at_utc'] < panel['sealed_at_utc'] == target_file['sealed_at_utc'] <= benchmark['frozen_at_utc'] < m['started_at_utc']
    assert panel['target_excluded'] and [u['uid'] for u in panel['units']] == expected_uids and target['uid'] not in expected_uids
    v16 = {u['uid']: u for u in read(ROOT/'runs/000016_kamri_correspondence_review/unit_ledger.json')['units']}
    v18 = {u['uid']: u for u in read(ROOT/'data/v18/frozen_references.json')['units']}
    passage_gates = read(ROOT/'runs/000016_kamri_correspondence_review/passage_gates.json')['passages']
    assert all(p['gate']['development_correspondence_review_eligible'] for p in passage_gates)
    rebuilt = []
    for uid in expected_uids:
        if uid in v16:
            u = v16[uid]
            assert u['independent_complete_statement_pair'] and u['equal_project_token_counts']
            fl, source = u['fl_statement_matches'][0], u['english_statement_matches'][0]
            g = u['component']
            fd, sd = f'data/v16/normalized/{g}_fl.json', f'data/v16/normalized/{g}_source.json'
            origin = 'runs/000016_kamri_correspondence_review/unit_ledger.json'
            gate = {'independent_complete_statement_pair': True, 'equal_project_token_counts': True}
        else:
            u = v18[uid]
            assert all(u['gate']['requirements'].values()) and u['gate']['development_positional_score_eligible']
            fl = u['historical_fl_statement_matches'][0]
            source = {'text': u['source_statement'], 'span': u['source_span'], 'block_id': u['source_block_id']}
            g, fd, sd = u['component'], u['fl_document'], u['source_document']
            origin, gate = 'data/v18/frozen_references.json', u['gate']
        fdoc, sdoc = verify_statement(fd, fl), verify_statement(sd, source)
        assert fdoc['snapshot']['acquisition_kind'] == 'indexed_web_excerpt' and fdoc['current_raw_fl'] is False
        assert sdoc['source_authority_reviewed'] is True
        ft, et = document_tokens(uid, fd, fl), document_tokens(uid, sd, source)
        assert len(ft) == len(et)
        rebuilt.append({'uid': uid, 'component': g, 'origin': origin, 'original_gate': gate,
                        'fl_statement': fl, 'source_statement': source, 'fl_document': fd, 'source_document': sd,
                        'fl_tokens': ft, 'source_tokens': et, 'current_raw_fl': False, 'semantic_gold': False, 'untouched_test_eligible': False})
    assert rebuilt == panel['units'] and sum(len(u['fl_tokens']) for u in rebuilt) == 284
    for g in config['components']:
        selected = [u for u in rebuilt if u['component'] == g]
        for side in ['fl', 'source']:
            spans = [u[side+'_statement']['span'] for u in selected]
            assert all(a[1] <= b[0] for a, b in zip(spans, spans[1:]))
    old = read(ROOT/'data/v19/frozen_evidence.json')
    ref = old['reference']
    fl = ref['historical_fl_statement_matches'][0]
    source = {'text': ref['source_statement'], 'span': ref['source_span'], 'block_id': ref['source_block_id']}
    observed_v19 = read(ROOT/'runs/000019_kamri_single_gap/observed_alignments.json')
    chosen = [a for a in observed_v19['alignments'] if a['gap'] in [1, 2]]
    expected_target = {'uid': '03:007', 'component': ref['component'], 'fl_document': ref['fl_document'], 'source_document': ref['source_document'],
                       'fl_statement': fl, 'source_statement': source,
                       'fl_tokens': document_tokens('03:007', ref['fl_document'], fl), 'source_tokens': document_tokens('03:007', ref['source_document'], source),
                       'gap_gate': old['gap_gate'], 'original_v18_gate': old['original_v18_gate'], 'alignments': chosen,
                       'current_raw_fl': False, 'semantic_gold': False, 'untouched_test_eligible': False}
    assert target == expected_target and len(target['fl_tokens']) == 21 and len(target['source_tokens']) == 22
    assert target['original_v18_gate']['unmet'] == ['equal_token_counts'] and target['gap_gate']['development_gap_score_eligible']
    assert observed_v19['maxima']['primary']['gaps'] == list(range(14))
    assert observed_v19['maxima']['secondary']['gaps'] == observed_v19['maximizer_intersection'] == [1, 2]
    verify_statement(ref['fl_document'], fl)
    verify_statement(ref['source_document'], source)
    calibration = replay_calibration(rebuilt)
    assert calibration == read(out/'calibration.json')
    seal = read(out/'calibration_seal.json')
    comparison = read(out/'target_comparison.json')
    assert seal == {'sealed_at_utc': seal['sealed_at_utc'], 'calibration_sha256': digest((out/'calibration.json').read_bytes()),
                    'rule_config_sha256': digest((ROOT/'experiments/kamri_orthographic_v20.json').read_bytes()), 'target_used_for_calibration': False,
                    'primary_gate': calibration['rules']['primary']['gate']}
    assert m['started_at_utc'] < seal['sealed_at_utc'] < comparison['comparison_started_at_utc'] < m['finished_at_utc']
    rules = {}
    for rule in RULES:
        anchors = replay_proposals(target['fl_tokens'], target['source_tokens'], rule)
        hypotheses = []
        for alignment in chosen:
            rows = []
            for row in alignment['rows']:
                agree = any(a['fl_token']['index'] == row['fl_token']['index'] and a['source_token']['index'] == row['source_token']['index'] for a in anchors['proposals'])
                rows.append(dict(row, orthographic_anchor_agreement=agree))
            hypotheses.append({'gap': alignment['gap'], 'unpaired_source_token': alignment['unpaired_source_token'],
                               'rows': rows, 'anchor_matches': sum(row['orthographic_anchor_agreement'] for row in rows), 'anchor_denominator': len(anchors['proposals'])})
        best = max(h['anchor_matches'] for h in hypotheses)
        gaps = [h['gap'] for h in hypotheses if h['anchor_matches'] == best]
        available = calibration['rules'][rule]['gate']['conditional_anchor_calibration_eligible'] and target['gap_gate']['development_gap_score_eligible'] and len(anchors['proposals']) > 0
        unique = available and len(gaps) == 1
        rules[rule] = {'anchor_ledger': anchors, 'hypotheses': hypotheses, 'maximum_anchor_matches': best, 'descriptive_maximizers': gaps,
                       'conditional_comparison_available': bool(available), 'unique_conditional_development_lead': bool(unique),
                       'eligible_gap_lead': gaps[0] if unique else None}
    expected_comparison = {'unit_uid': '03:007', 'hypothesis_denominator': 2, 'original_v19_gaps': [1, 2], 'rules': rules,
                           'primary_gap_lead': rules['primary']['eligible_gap_lead'], 'original_hypotheses_modified': False,
                           'semantic_training_eligible': False, 'untouched_test_eligible': False, 'source_identity_accepted': False,
                           'comparison_started_at_utc': comparison['comparison_started_at_utc']}
    assert comparison == expected_comparison
    assert report['calibration'] == {n: {'summary': r['summary'], 'gate': r['gate']} for n, r in calibration['rules'].items()}
    assert report['target'] == {n: {k: v for k, v in r.items() if k not in ('anchor_ledger', 'hypotheses')} for n, r in rules.items()}
    assert report['primary_gap_lead'] == comparison['primary_gap_lead']
    assert report['original_v19_gaps'] == [1, 2] and not report['original_hypotheses_modified'] and report['calibration_sealed_before_target']
    assert report['calibration_unit_denominator'] == m['unit_denominator'] == 11 and report['component_denominator'] == 2
    assert report['target_unit_denominator'] == m['target_unit_denominator'] == 1 and report['target_hypothesis_denominator'] == m['target_hypothesis_denominator'] == 2
    assert report['semantic_training_eligible_tokens'] == report['untouched_test_eligible_units'] == report['source_identity_claims_admitted'] == 0
    assert report['current_raw_fl'] is False
    for item in (m, report):
        assert item['model_executed'] and item['model_kind'] == 'frozen Unicode orthographic copying proposal rule'
        assert item['translation_model_executed'] is False and item['new_lexical_induction_executed'] is False and item['shared_lexicons_used'] is False
    assert m['outcome'] == ('conditional_orthographic_gap_lead' if comparison['primary_gap_lead'] is not None else 'orthographic_gap_selection_unavailable')
    previous = []
    for directory in sorted((ROOT/'runs').glob('0000*')):
        if directory == out:
            continue
        check_hashes(directory)
        previous.append({'run_id': directory.name, 'manifest_sha256': digest((directory/'manifest.json').read_bytes())})
    assert len(previous) == 19
    prior_seal = read(ROOT/'reports/000019_deliverable_seal.json')
    for path, sha in prior_seal['deliverable_hashes'].items():
        assert digest((ROOT/path).read_bytes()) == sha, path
    assert prior_seal['run_manifest_sha256'] == digest((ROOT/'runs/000019_kamri_single_gap/manifest.json').read_bytes())
    receipt = {'state': 'verified', 'verified_at_utc': utc(), 'run_id': out.name, 'manifest_sha256': digest((out/'manifest.json').read_bytes()),
               'calibration': report['calibration'], 'primary_gap_lead': report['primary_gap_lead'], 'previous_runs': previous,
               'checks': ['Exact eleven-unit selection, 284 pairs, original statements and every source/FL token offset',
                          'Independent Unicode keys, candidate eligibility, full-statement multiplicities, proposals and abstentions',
                          'All eleven name derangements, sixty unrelated-source comparisons, eleven name-preserving frame lures per rule',
                          'Registered calibration breadth and conflict/control gates sealed before independent two-hypothesis replay',
                          'No target fitting, baseline substitution, source identity or semantic admissions',
                          'Input/code/output hashes, experiment 19 deliverable seal and nineteen prior archives unchanged'],
               'limits': ['Previously exposed development panel and target', 'Historical indexed FL only', 'Name copying does not establish source identity']}
    dump_json(ROOT/'reports/000020_verification.json', receipt)
    print(json.dumps({'state': 'verified', 'units': 11, 'token_pairs': 284, 'cross_component_controls_per_rule': 60,
                      'previous_runs': 19, 'calibration': report['calibration'], 'primary_gap_lead': report['primary_gap_lead']}, indent=2))

if __name__ == '__main__':
    main()
