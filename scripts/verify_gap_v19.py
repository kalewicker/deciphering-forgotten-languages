"""Independent deletion-and-zip gap replay; does not import the v19 scorer."""
from fractions import Fraction
from pathlib import Path
import json
import random
import re
from fl_decipher.corpus import digest, dump_json
from fl_decipher.natural_v12 import utc
from fl_decipher.text import tokens, sentences
from verify_correspondence_v6 import check_hashes

ROOT = Path(__file__).resolve().parents[1]
NAMES = ('primary', 'secondary')


def read(path):
    return json.loads(path.read_text())


def fraction(a, b):
    if not b:
        return None
    f = Fraction(a, b)
    return {'numerator': f.numerator, 'denominator': f.denominator, 'value': float(f)}


def replay(prediction, reference, order, full=False):
    english = reference['source_tokens']
    historical = reference['historical_fl_statement_matches'][0]
    document_fl = tokens(historical['text'], historical['span'][0])
    assert sorted(order) == list(range(len(english)))
    curves, alignments = [], []
    for gap in range(len(english)):
        paired_indices = order[:gap] + order[gap+1:]
        rows = []
        stats = {n: dict.fromkeys(('predictions', 'abstentions', 'matches', 'conflicts'), 0) for n in NAMES}
        for token, index in zip(prediction['tokens'], paired_indices, strict=True):
            source = english[index]
            row = {'fl_token': {k: token[k] for k in ('uid', 'index', 'fl_form', 'fl_surface', 'fl_span')},
                   'fl_document_span': [document_fl[token['index']].start, document_fl[token['index']].end],
                   'source_position': order.index(index), 'source_token': source}
            for name in NAMES:
                value = token[name]['form']
                status = 'abstained' if value is None else 'matched' if value == source['form'] else 'conflict'
                stats[name]['abstentions' if value is None else 'predictions'] += 1
                if value is not None:
                    stats[name]['matches' if value == source['form'] else 'conflicts'] += 1
                row[name] = {'prediction': value, 'status': status, 'abstention_reason': token[name]['abstention_reason']}
            rows.append(row)
        a = {'gap': gap, 'order': order, 'unpaired_source_token': english[order[gap]],
             'fl_token_denominator': len(prediction['tokens']), 'source_token_denominator': len(english),
             'aligned_pairs': len(rows), 'stats': stats, 'rows': rows}
        assert len(rows) == 21 and len(english) == 22
        assert sorted([r['source_token']['index'] for r in rows] + [a['unpaired_source_token']['index']]) == list(range(22))
        for n, s in stats.items():
            assert s['predictions'] == s['matches'] + s['conflicts']
            assert s['predictions'] + s['abstentions'] == 21
            assert s['predictions'] == sum(t[n]['form'] is not None for t in prediction['tokens'])
        curves.append({'gap': gap, **{n: stats[n]['matches'] for n in NAMES}})
        alignments.append(a)
    maxima = {}
    for n in NAMES:
        best = max(c[n] for c in curves)
        gaps = [c['gap'] for c in curves if c[n] == best]
        count = sum(t[n]['form'] is not None for t in prediction['tokens'])
        maxima[n] = {'matches': best, 'gaps': gaps, 'unique': len(gaps) == 1,
                     'predictions': count, 'abstentions': 21-count, 'agreement': fraction(best, count)}
    result = {'gap_denominator': 22, 'curve': curves, 'maxima': maxima,
              'maximizer_intersection': sorted(g for g in range(22) if g in maxima['primary']['gaps'] and g in maxima['secondary']['gaps'])}
    if full:
        result['alignments'] = alignments
    return result


def statements(doc):
    result = []
    for block in doc['blocks']:
        for s in sentences(block['text']):
            result.append({'text': s.text, 'span': [block['span'][0]+s.start, block['span'][0]+s.end],
                           'block_id': block['id'], 'complete': bool(re.search(r'[.!?][\"”’\']*$', s.text))})
    return result


def main():
    out = ROOT/'runs/000019_kamri_single_gap'
    m = check_hashes(out)
    cfg = read(ROOT/'experiments/kamri_gap_v19.json')
    benchmark = read(ROOT/'benchmarks/kamri_gap_v19.json')
    evidence = read(ROOT/benchmark['evidence'])
    report = read(out/'report.json')
    assert evidence == read(out/'evidence.json')
    for path, sha in cfg['input_hashes'].items():
        assert digest((ROOT/path).read_bytes()) == sha, path
    assert cfg['seed'] == m['seed'] == 2026100219
    assert cfg['permutations'] == m['permutation_denominator'] == 999 and cfg['p_max'] == 0.01
    assert cfg['controls'] == ['rotate_+1', 'rotate_+2', 'rotate_-1', 'rotate_-2', 'reverse']
    assert cfg['unit_uid'] == report['unit_uid'] == evidence['uid'] == '03:007'
    assert cfg['registered_at_utc'] < evidence['sealed_at_utc'] <= benchmark['frozen_at_utc'] < m['started_at_utc']
    for key, count in [('unit_denominator', 1), ('fl_token_denominator', 21), ('source_token_denominator', 22), ('gap_denominator', 22)]:
        assert cfg[key] == m[key] == report[key] == count
    predictions = read(ROOT/'data/v18/frozen_predictions.json')
    references = read(ROOT/'data/v18/frozen_references.json')
    p = next(u for u in predictions['units'] if u['uid'] == cfg['unit_uid'])
    r = next(u for u in references['units'] if u['uid'] == cfg['unit_uid'])
    target = next(u for u in read(ROOT/'data/v18/targets.json')['units'] if u['uid'] == cfg['unit_uid'])
    assert evidence['prediction'] == p and evidence['reference'] == r and evidence['target'] == target
    pseal = read(ROOT/'data/v18/prediction_seal.json')
    rseal = read(ROOT/'data/v18/reference_seal.json')
    assert digest((ROOT/'data/v18/frozen_predictions.json').read_bytes()) == pseal['predictions_sha256']
    assert digest((ROOT/'data/v18/frozen_references.json').read_bytes()) == rseal['references_sha256']
    assert predictions['sealed_at_utc'] <= pseal['sealed_at_utc'] < references['preparation_started_at_utc'] <= references['reviewed_at_utc'] <= rseal['sealed_at_utc'] < cfg['registered_at_utc']
    c = read(ROOT/'data/v18/frozen_candidates.json')
    assert len(c['primary']) == 3 and len(c['secondary']) == 34
    assert digest((ROOT/'data/v18/frozen_candidates.json').read_bytes()) == predictions['candidate_sha256'] == pseal['candidate_sha256']
    assert digest((ROOT/'data/v18/targets.json').read_bytes()) == predictions['target_sha256'] == pseal['target_sha256']
    assert digest((ROOT/'data/v18/prediction_seal.json').read_bytes()) == references['prediction_seal_sha256'] == rseal['prediction_seal_sha256']
    original = read(ROOT/'data/v15/parsed_annotations.json')['articles'][2]['units'][6]
    assert original['uid'] == target['uid'] and original['fl'] == target['fl']
    fl_tokens = tokens(target['fl'])
    assert len(fl_tokens) == p['token_denominator'] == 21
    for i, (t, row) in enumerate(zip(fl_tokens, p['tokens'], strict=True)):
        assert row['uid'] == '03:007'+f':t{i:03d}' and row['index'] == i
        assert row['fl_form'] == t.normalized and row['fl_surface'] == t.surface and row['fl_span'] == [t.start, t.end]
        for n in NAMES:
            item = c[n].get(t.normalized)
            value = item['paired_english_form'] if item else None
            reason = None if item else 'conflicted_training_form' if t.normalized in {f['fl_form'] for f in c['conflicted_forms']} else 'outside_frozen_candidate_set'
            assert row[n] == {'form': value, 'abstention_reason': reason}
    sd, fd = read(ROOT/r['source_document']), read(ROOT/r['fl_document'])
    ss, fs = statements(sd), statements(fd)
    assert sd['text'][slice(*r['source_span'])] == r['source_statement']
    assert r['source_tokens'] == [{'index': i, 'surface': t.surface, 'form': t.normalized, 'span': [t.start, t.end]} for i, t in enumerate(tokens(r['source_statement'], r['source_span'][0]))]
    anchor = next(u for u in read(ROOT/'runs/000016_kamri_correspondence_review/unit_ledger.json')['units'] if u['uid'] == '03:004')['english_statement_matches'][0]
    at = [i for i, s in enumerate(ss) if s['text'] == anchor['text'] and s['span'] == anchor['span']]
    assert len(at) == 1
    extension = [(i, s) for i, s in enumerate(ss) if i > at[0] and s['complete']][:4]
    si, statement = extension[2]
    assert r['source_statement_index'] == si and statement['text'] == r['source_statement'] and statement['span'] == r['source_span'] and statement['block_id'] == r['source_block_id']
    historical = [s for s in fs if [t.normalized for t in tokens(s['text'])] == [t.normalized for t in fl_tokens]]
    assert len(historical) == len(r['historical_fl_statement_matches']) == 1
    h, saved = historical[0], r['historical_fl_statement_matches'][0]
    assert h['text'] == saved['text'] == target['fl'] and h['span'] == saved['span'] and h['block_id'] == saved['block_id']
    assert h['complete'] and saved['complete_statement'] and fd['text'][slice(*h['span'])] == target['fl']
    assert not fd['current_raw_fl'] and fd['snapshot']['acquisition_kind'] == 'indexed_web_excerpt'
    req = {'source_authority': sd['source_authority_reviewed'], 'source_statement_complete': statement['complete'],
           'source_continuation_orderly': True, 'historical_fl_unique_complete': len(historical) == 1 and h['complete'], 'equal_token_counts': False}
    old_gate = {'development_positional_score_eligible': False, 'requirements': req, 'unmet': ['equal_token_counts'],
                'semantic_training_eligible': False, 'untouched_test_eligible': False}
    previous_unit = next(u for u in read(ROOT/'runs/000018_kamri_passage_transfer/unit_ledger.json')['units'] if u['uid'] == cfg['unit_uid'])
    assert r['gate'] == old_gate == previous_unit['gate'] == evidence['original_v18_gate'] == report['original_v18_gate']
    new_req = {k: req[k] for k in req if k != 'equal_token_counts'} | {'exact_registered_lengths': True, 'single_english_token_excess': True}
    new_gate = {'development_gap_score_eligible': True, 'requirements': new_req, 'unmet': [], 'semantic_training_eligible': False, 'untouched_test_eligible': False}
    assert evidence['gap_gate'] == report['gap_gate'] == new_gate and all(new_req.values())
    observed = replay(p, r, list(range(22)), True)
    assert observed == read(out/'observed_alignments.json')
    assert report['observed'] == {k: v for k, v in observed.items() if k != 'alignments'}
    assert report['direct_index_comparator']['gap'] == 21 and report['direct_index_comparator']['stats'] == observed['alignments'][21]['stats']
    controls = read(out/'fixed_controls.json')
    assert [x['name'] for x in controls] == cfg['controls'] and report['fixed_controls'] == controls
    for control in controls:
        name = control['name']
        order = list(range(21, -1, -1)) if name == 'reverse' else [(i-int(name.split('_')[1])) % 22 for i in range(22)]
        assert control['order'] == order and control['search'] == replay(p, r, order)
    permutations = read(out/'permutations.json')
    assert len(permutations) == 999
    rng = random.Random(2026100219)
    values = []
    count = observed['maxima']['primary']['matches']
    for number, saved in enumerate(permutations):
        order = list(range(22))
        rng.shuffle(order)
        result = replay(p, r, order)
        value = result['maxima']['primary']['matches']
        values.append(value)
        assert saved == {'number': number, 'order': order, 'search': result, 'greater_or_equal_to_observed': value >= count, 'exact_tie': value == count}
    q = report['primary_test']
    ge, ties = sum(v >= count for v in values), sum(v == count for v in values)
    expected = {'available': True, 'statistic': 'maximum primary matches over all 22 gap positions', 'observed_max_matches': count,
                'null_permutations': 999, 'greater_or_equal': ge, 'exact_ties': ties, 'p_one_sided': fraction(1+ge, 1000),
                'null_mean_max_matches': fraction(sum(values), 999), 'null_max_matches': max(values), 'registered_p_max': 0.01,
                'development_gap_criterion_met': Fraction(1+ge, 1000) <= Fraction(1, 100)}
    assert q == expected
    assert observed['maxima']['primary']['predictions'] > 0
    assert report['semantic_training_eligible_tokens'] == report['untouched_test_eligible_units'] == 0
    assert evidence['new_predictions_executed'] is False and evidence['semantic_gold'] is False
    for item in (report, m):
        assert item['model_executed'] and item['model_kind'] == 'exhaustive single-gap search using frozen positional predictions'
        assert not item['translation_model_executed'] and not item['new_lexical_induction_executed'] and not item['shared_lexicons_used']
    for item in (report, evidence, r):
        assert item['current_raw_fl'] is False
    assert m['outcome'] == ('conditional_development_gap_signal' if q['development_gap_criterion_met'] else 'registered_development_gap_criterion_not_met')
    previous = []
    for directory in sorted((ROOT/'runs').glob('0000*')):
        if directory == out:
            continue
        check_hashes(directory)
        previous.append({'run_id': directory.name, 'manifest_sha256': digest((directory/'manifest.json').read_bytes())})
    assert len(previous) == 18
    receipt = {'state': 'verified', 'verified_at_utc': utc(), 'run_id': out.name,
               'manifest_sha256': digest((out/'manifest.json').read_bytes()), 'maxima': observed['maxima'], 'primary_test': q,
               'previous_runs': previous,
               'checks': ['Frozen candidate predictions, source/FL tokens and original spans reconstructed',
                          'Independent publisher continuation and historical indexed FL statement; original v18 gate unchanged',
                          'All 22 full observed alignments, omitted identities, abstentions, conflicts and ties',
                          'Independent deletion-and-zip replay of all 22 gaps in each of 999 permutations and five controls',
                          'Exact integer tail counts and search-corrected primary criterion; secondary never substituted',
                          'Input/code/output hashes and eighteen previous archives preserved; no semantic promotion'],
               'limits': ['Single exposed development unit', 'Historical indexed FL only', 'Positional hypotheses, not semantic accuracy']}
    dump_json(ROOT/'reports/000019_verification.json', receipt)
    print(json.dumps({'state': 'verified', 'observed_gaps': 22, 'permutations': 999, 'previous_runs': 18, 'primary_test': q}, indent=2))

if __name__ == '__main__':
    main()
