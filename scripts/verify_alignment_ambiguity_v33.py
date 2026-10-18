"""Independent maximum-LCS and optimal-DAG edge-dominator audit verifier."""
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
RUN = 'runs/000033_alignment_ambiguity'


def read(p):
    return json.loads((ROOT / p).read_text())


def sha(p):
    return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()


def lcs_tables(left, right, dominators=False):
    n, m = len(left), len(right)
    scores = [[0] * (m + 1) for _ in range(n + 1)]
    counts = [[1] * (m + 1) for _ in range(n + 1)]
    mandatory = [[0] * (m + 1) for _ in range(n + 1)] if dominators else None
    for i, a in enumerate(left, 1):
        for j, b in enumerate(right, 1):
            equal = a is not None and a == b
            value = max(scores[i-1][j], scores[i][j-1], scores[i-1][j-1] + 1 if equal else -1)
            predecessors = []
            count = 0
            if scores[i-1][j] == value:
                count += counts[i-1][j]
                if dominators: predecessors.append(mandatory[i-1][j])
            if scores[i][j-1] == value:
                count += counts[i][j-1]
                if dominators: predecessors.append(mandatory[i][j-1])
            if equal and scores[i-1][j-1] + 1 == value:
                count += counts[i-1][j-1]
                if dominators: predecessors.append(mandatory[i-1][j-1] | (1 << ((i-1)*m+j-1)))
            scores[i][j] = value; counts[i][j] = count
            if dominators:
                common = predecessors[0]
                for bits in predecessors[1:]: common &= bits
                mandatory[i][j] = common
    return scores, counts, mandatory[n][m] if dominators else None


def reference_pair(left, right, original):
    n, m = len(left), len(right)
    f, ways, forced_bits = lcs_tables(left, right, True)
    r, suffix_ways, _ = lcs_tables(left[::-1], right[::-1])
    best, paths = f[n][m], ways[n][m]
    assert original['edit_cost'] == n + m - 2 * best
    assert original['matched_tokens'] == best and original['optimal_operation_paths'] == paths
    assert [i for i, j in original['trace'] if i is not None] == list(range(n))
    assert [j for i, j in original['trace'] if j is not None] == list(range(m))
    edges = []
    for i, a in enumerate(left):
        for j, b in enumerate(right):
            if a is not None and a == b and f[i][j] + 1 + r[n-i-1][m-j-1] == best:
                forced = bool(forced_bits & (1 << (i*m+j)))
                count = ways[i][j] * suffix_ways[n-i-1][m-j-1]
                assert forced == (count == paths)
                edges.append({'query_index': i, 'candidate_index': j, 'through_paths': count, 'forced': forced})
    forced = [[e['query_index'], e['candidate_index']] for e in edges if e['forced']]
    representative = [[i, j] for i, j in original['trace'] if i is not None and j is not None]
    assert len(representative) == best
    assert set(map(tuple, representative)) <= {(e['query_index'], e['candidate_index']) for e in edges}
    assert set(map(tuple, forced)) <= set(map(tuple, representative))
    def ledger(size, side, other):
        out = []
        for i in range(size):
            es = [e for e in edges if e[side] == i]
            gap = sum(e['through_paths'] for e in es) != paths
            status = 'always_gap'
            if es:
                status = 'forced_match' if any(e['forced'] for e in es) else 'optional_match_or_gap' if gap else 'ambiguous_partner'
            out.append({'token_index': i, 'possible_partners': [e[other] for e in es],
                        'gap_on_some_optimum': gap, 'status': status})
        return out
    return {'edit_cost': n + m - 2*best, 'optimal_operation_paths': paths,
            'original_qualifies': original['qualifies'], 'original_matched_tokens': best,
            'possible_matches': edges, 'forced_matches': forced, 'representative_matches': representative,
            'matched_pair_ambiguity': len(forced) != best,
            'gap_order_only_multiplicity': paths > 1 and len(forced) == best,
            'query_tokens': ledger(n, 'query_index', 'candidate_index'),
            'candidate_tokens': ledger(m, 'candidate_index', 'query_index')}


FIELDS = ['query_tokens', 'representative_matches', 'representative_exact', 'forced_matches', 'forced_exact',
          'optional_representative_matches', 'optional_representative_exact', 'wrong_removed', 'wrong_retained',
          'correct_discarded', 'possible_matches']


def aggregate(rows):
    out = {k: sum(r[k] for r in rows) for k in FIELDS}
    out.update(pairs=len(rows), qualified_pairs=sum(r['qualifies'] for r in rows),
               pairs_with_retained_matches=sum(bool(r['forced_matches']) for r in rows),
               pairs_with_matched_pair_ambiguity=sum(r['matched_pair_ambiguity'] for r in rows),
               pairs_with_gap_order_only_multiplicity=sum(r['gap_order_only_multiplicity'] for r in rows))
    for key, num, den in [('forced_precision', 'forced_exact', 'forced_matches'),
                          ('representative_precision', 'representative_exact', 'representative_matches'),
                          ('retained_fraction_of_representative', 'forced_matches', 'representative_matches'),
                          ('retained_fraction_of_query_tokens', 'forced_matches', 'query_tokens')]:
        out[key] = [out[num], out[den]]
    return out


def reference_assessment(pairs, oracle):
    parents = {b['base_id']: b['view_ids']['parent'] for b in oracle['bases']}
    rows, errors = [], []
    for q in oracle['queries']:
        pid = q['query_view_id'] + '::' + parents[q['base_id']]; p = pairs[pid]
        row = {k: 0 for k in FIELDS}
        row.update(pair_id=pid, query_view_id=q['query_view_id'], group=q['group'], mechanism=q['mechanism'],
                   qualifies=p['original_qualifies'], query_tokens=len(p['query_tokens']),
                   possible_matches=len(p['possible_matches']), matched_pair_ambiguity=p['matched_pair_ambiguity'],
                   gap_order_only_multiplicity=p['gap_order_only_multiplicity'])
        possible = {(e['query_index'], e['candidate_index']) for e in p['possible_matches']}
        for i, j in p['representative_matches']:
            correct = q['origins'][i] == j
            retained = [i, j] in p['forced_matches']
            row['representative_matches'] += 1; row['representative_exact'] += correct
            row['forced_matches'] += retained; row['forced_exact'] += retained and correct
            row['optional_representative_matches'] += not retained
            row['optional_representative_exact'] += not retained and correct
            row['wrong_removed'] += not correct and not retained
            row['wrong_retained'] += not correct and retained
            row['correct_discarded'] += correct and not retained
            if not correct:
                errors.append({'pair_id': pid, 'query_index': i, 'returned_candidate_index': j,
                               'origin_index': q['origins'][i], 'group': q['group'], 'mechanism': q['mechanism'],
                               'qualifies': p['original_qualifies'], 'retained_as_forced': retained,
                               'origin_edge_possible': (i, q['origins'][i]) in possible,
                               'possible_partners': p['query_tokens'][i]['possible_partners']})
        rows.append(row)
    primary = [r for r in rows if r['qualifies']]
    by_group = {}
    for group in dict.fromkeys(q['group'] for q in oracle['queries']):
        by_group[group] = {}
        for mechanism in dict.fromkeys(q['mechanism'] for q in oracle['queries']):
            selected = [r for r in rows if r['group'] == group and r['mechanism'] == mechanism]
            by_group[group][mechanism] = {'all_parents': aggregate(selected),
                                         'qualified_parents': aggregate([r for r in selected if r['qualifies']])}
    req = {'all_primary_forced_matches_origin_exact': sum(r['wrong_retained'] for r in primary) == 0,
           'every_primary_pair_retains_a_match': bool(primary) and min(r['forced_matches'] for r in primary) > 0}
    return {'parent_pairs': rows, 'origin_disagreements': errors, 'all_parent_summary': aggregate(rows),
            'primary_summary': aggregate(primary), 'by_group_mechanism': by_group,
            'qualified_policy_coverage_all_query_tokens': [sum(r['forced_matches'] for r in primary), sum(r['query_tokens'] for r in rows)],
            'synthetic_hypothesis': {'requirements': req, 'passed': all(req.values())}}


def main():
    from verify_correspondence_v6 import check_hashes
    cfg = read('experiments/alignment_ambiguity_v33.json'); pre = read('data/v33/preflight.json')
    manifest = check_hashes(ROOT / RUN)
    for inventory in (cfg['input_hashes'], pre['input_hashes'], pre['code_hashes']):
        for p, h in inventory.items(): assert sha(p) == h, p
    assert manifest['code_hashes'] == pre['code_hashes']
    receipt = read(RUN + '/audit_receipt.json')
    assert cfg['registered_at_utc'] < pre['sealed_at_utc'] < manifest['started_at_utc'] < receipt['audit_frozen_at_utc'] < manifest['finished_at_utc']
    assert not receipt['oracle_used_for_audit'] and receipt['audit_sha256'] == sha(RUN + '/ambiguity.json')
    public = read('data/v32/public_cases.json'); pred = read('runs/000032_synthetic_transfer/predictions.json')
    model = read('data/v32/frozen_mapping.json')['model']; result = read(RUN + '/ambiguity.json')
    assert result.keys() == {'pairs', 'queries', 'panels', 'oracle_used', 'retrieval_decisions_changed'}
    assert result['queries'] == len(pred['decoded_queries']) == cfg['query_denominator'] == 420
    assert result['panels'] == len(pred['panels']) == len(public['cases']) == cfg['panel_denominator'] == 2100
    assert result['oracle_used'] is False and result['retrieval_decisions_changed'] == 0
    assert set(result['pairs']) == set(pred['pair_scores']) and len(result['pairs']) == cfg['pair_denominator'] == 2520
    decoded = {}
    for qid, ds in pred['decoded_queries'].items():
        q = public['views'][qid]
        forms = [None if t['blocked'] else model['entries'].get(t['form'], {}).get('source_form') for t in q['tokens']]
        assert [d['source_form'] for d in ds] == forms
        decoded[qid] = forms
    for view in public['views'].values():
        for t in view['tokens']: assert view['text'][t['start']:t['end']] == t['form']
    for pid, p in pred['pair_scores'].items():
        qid, cid = p['query_view_id'], p['candidate_view_id']
        source = [None if t['blocked'] else t['form'] for t in public['views'][cid]['tokens']]
        expected = {'query_view_id': qid, 'candidate_view_id': cid, **reference_pair(decoded[qid], source, p)}
        assert result['pairs'][pid] == expected, pid
    expected_assessment = reference_assessment(result['pairs'], read('data/v32/oracle.json'))
    assert read(RUN + '/assessment.json') == expected_assessment
    primary = expected_assessment['primary_summary']
    assert primary['pairs'] == cfg['primary_parent_pairs'] == 120 and primary['representative_matches'] == cfg['primary_returned_matches'] == 6772
    assert primary['representative_exact'] == read('runs/000032_synthetic_transfer/assessment.json')['metrics']['qualified_parent_exact_origin_matches']
    ps = list(result['pairs'].values())
    structural = {'pairs': len(ps), 'queries': 420, 'panels': 2100,
                  'pairs_without_matches': sum(p['original_matched_tokens'] == 0 for p in ps),
                  'pairs_with_multiple_operation_paths': sum(p['optimal_operation_paths'] > 1 for p in ps),
                  'pairs_with_matched_pair_ambiguity': sum(p['matched_pair_ambiguity'] for p in ps),
                  'pairs_with_gap_order_only_multiplicity': sum(p['gap_order_only_multiplicity'] for p in ps),
                  'representative_matches': sum(p['original_matched_tokens'] for p in ps),
                  'forced_matches': sum(len(p['forced_matches']) for p in ps),
                  'possible_matches': sum(len(p['possible_matches']) for p in ps),
                  'query_token_statuses': dict(Counter(t['status'] for p in ps for t in p['query_tokens'])),
                  'candidate_token_statuses': dict(Counter(t['status'] for p in ps for t in p['candidate_tokens']))}
    expected_report = {'experiment_id': cfg['experiment_id'], 'engineering_integrity_passed': True,
                       'frozen_inputs_unchanged': True, 'structural_summary': structural, 'primary_summary': primary,
                       'all_parent_summary': expected_assessment['all_parent_summary'],
                       'qualified_policy_coverage_all_query_tokens': expected_assessment['qualified_policy_coverage_all_query_tokens'],
                       'synthetic_hypothesis': expected_assessment['synthetic_hypothesis'], 'symbolic_audit_executed': True,
                       'external_or_neural_model_executed': False, 'scientific_acceptance': None,
                       'semantic_evaluation_metrics': None, 'source_identities_admitted': 0, 'semantic_labels_admitted': 0,
                       'independent_reviews_admitted': 0, 'untouched_test_units_admitted': 0,
                       'natural_targets_rescored': 0, 'retrieval_decisions_changed': 0, 'new_network_requests': 0}
    assert read(RUN + '/report.json') == expected_report
    preserved = []
    for p in sorted((ROOT / 'runs').glob('*/manifest.json')):
        if p.parent != ROOT / RUN: check_hashes(p.parent); preserved.append(p.parent.name)
    assert len(preserved) == 32
    for p in (ROOT / 'reports').glob('*_deliverable_seal.json'):
        for n, h in json.loads(p.read_text()).get('deliverable_hashes', {}).items(): assert sha(n) == h, n
    verified = {'state': 'verified', 'run_manifest_sha256': sha(RUN + '/manifest.json'),
                'independent_method': 'maximum-LCS possible edges and optimal-DAG mandatory-match bitset intersections',
                'pair_alignments_verified': len(ps), 'queries_verified': 420, 'panels_verified': 2100,
                'all_parent_pairs_verified': len(expected_assessment['parent_pairs']), 'primary_parent_pairs_verified': primary['pairs'],
                'primary_summary': primary, 'engineering_integrity_passed': True,
                'synthetic_hypothesis_passed': expected_assessment['synthetic_hypothesis']['passed'],
                'prior_runs_preserved': preserved, 'scientific_acceptance': None, 'semantic_labels_admitted': 0}
    target = ROOT / 'reports/000033_verification.json'
    if target.exists(): assert {k: v for k, v in json.loads(target.read_text()).items() if k != 'verified_at_utc'} == verified
    else:
        verified['verified_at_utc'] = datetime.now(timezone.utc).isoformat()
        target.write_text(json.dumps(verified, indent=2) + '\n')
    print(json.dumps(verified, indent=2))


if __name__ == '__main__':
    main()
