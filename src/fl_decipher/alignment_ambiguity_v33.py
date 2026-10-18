"""All-optimal-path positional audit; no learner, ranking or oracle in audit()."""
from collections import Counter


def prefixes(query, candidate):
    """Minimum indel cost and exact optimal operation counts for all prefixes."""
    n, m = len(query), len(candidate)
    cost = [[0] * (m + 1) for _ in range(n + 1)]
    ways = [[1] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        cost[i][0] = i
    for j in range(m + 1):
        cost[0][j] = j
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            options = [(cost[i - 1][j] + 1, ways[i - 1][j]),
                       (cost[i][j - 1] + 1, ways[i][j - 1])]
            if query[i - 1] is not None and query[i - 1] == candidate[j - 1]:
                options.append((cost[i - 1][j - 1], ways[i - 1][j - 1]))
            best = min(c for c, _ in options)
            cost[i][j] = best
            ways[i][j] = sum(w for c, w in options if c == best)
    return cost, ways


def token_ledger(size, edges, total_paths, side):
    records = []
    for index in range(size):
        selected = [e for e in edges if e[side] == index]
        partners = [e['candidate_index' if side == 'query_index' else 'query_index'] for e in selected]
        matched_paths = sum(e['through_paths'] for e in selected)
        forced = [e for e in selected if e['forced']]
        assert 0 <= matched_paths <= total_paths and len(forced) <= 1
        status = ('always_gap' if not selected else 'forced_match' if forced else
                  'ambiguous_partner' if matched_paths == total_paths else 'optional_match_or_gap')
        records.append({'token_index': index, 'possible_partners': partners,
                        'gap_on_some_optimum': matched_paths < total_paths, 'status': status})
    return records


def audit_pair(decoded, candidate_tokens, original):
    query = [t['source_form'] for t in decoded]
    candidate = [None if t['blocked'] else t['form'] for t in candidate_tokens]
    n, m = len(query), len(candidate)
    forward, ways = prefixes(query, candidate)
    reverse, reverse_ways = prefixes(query[::-1], candidate[::-1])
    optimum, paths = forward[n][m], ways[n][m]
    assert reverse[n][m] == optimum and reverse_ways[n][m] == paths
    assert optimum == original['edit_cost'] and paths == original['optimal_operation_paths']
    assert [i for i, j in original['trace'] if i is not None] == list(range(n))
    assert [j for i, j in original['trace'] if j is not None] == list(range(m))
    edges = []
    for i in range(n):
        for j in range(m):
            if query[i] is not None and query[i] == candidate[j] and forward[i][j] + reverse[n-i-1][m-j-1] == optimum:
                through = ways[i][j] * reverse_ways[n-i-1][m-j-1]
                assert 0 < through <= paths
                edges.append({'query_index': i, 'candidate_index': j,
                              'through_paths': through, 'forced': through == paths})
    possible = {(e['query_index'], e['candidate_index']) for e in edges}
    forced = [[e['query_index'], e['candidate_index']] for e in edges if e['forced']]
    representative = [[i, j] for i, j in original['trace'] if i is not None and j is not None]
    assert len(representative) == original['matched_tokens'] == (n + m - optimum) // 2
    assert set(map(tuple, representative)) <= possible
    assert set(map(tuple, forced)) <= set(map(tuple, representative))
    assert all(a[0] < b[0] and a[1] < b[1] for a, b in zip(forced, forced[1:]))
    return {'edit_cost': optimum, 'optimal_operation_paths': paths,
            'original_qualifies': original['qualifies'], 'original_matched_tokens': len(representative),
            'possible_matches': edges, 'forced_matches': forced, 'representative_matches': representative,
            'matched_pair_ambiguity': len(forced) < len(representative),
            'gap_order_only_multiplicity': paths > 1 and len(forced) == len(representative),
            'query_tokens': token_ledger(n, edges, paths, 'query_index'),
            'candidate_tokens': token_ledger(m, edges, paths, 'candidate_index')}


def audit(public, predictions):
    return {'pairs': {pid: {'query_view_id': p['query_view_id'], 'candidate_view_id': p['candidate_view_id'],
                            **audit_pair(predictions['decoded_queries'][p['query_view_id']],
                                         public['views'][p['candidate_view_id']]['tokens'], p)}
                      for pid, p in predictions['pair_scores'].items()},
            'queries': len(predictions['decoded_queries']), 'panels': len(predictions['panels']),
            'oracle_used': False, 'retrieval_decisions_changed': 0}


SUM_FIELDS = ('query_tokens', 'representative_matches', 'representative_exact', 'forced_matches',
              'forced_exact', 'optional_representative_matches', 'optional_representative_exact',
              'wrong_removed', 'wrong_retained', 'correct_discarded', 'possible_matches')


def summarize(rows):
    result = {'pairs': len(rows), 'qualified_pairs': sum(r['qualifies'] for r in rows),
              'pairs_with_retained_matches': sum(r['forced_matches'] > 0 for r in rows),
              'pairs_with_matched_pair_ambiguity': sum(r['matched_pair_ambiguity'] for r in rows),
              'pairs_with_gap_order_only_multiplicity': sum(r['gap_order_only_multiplicity'] for r in rows)}
    result.update({k: sum(r[k] for r in rows) for k in SUM_FIELDS})
    result['forced_precision'] = [result['forced_exact'], result['forced_matches']]
    result['representative_precision'] = [result['representative_exact'], result['representative_matches']]
    result['retained_fraction_of_representative'] = [result['forced_matches'], result['representative_matches']]
    result['retained_fraction_of_query_tokens'] = [result['forced_matches'], result['query_tokens']]
    return result


def assess(result, oracle):
    parents = {b['base_id']: b['view_ids']['parent'] for b in oracle['bases']}
    rows, disagreements = [], []
    for q in oracle['queries']:
        qid = q['query_view_id']; pid = qid + '::' + parents[q['base_id']]; p = result['pairs'][pid]
        forced = set(map(tuple, p['forced_matches'])); representative = set(map(tuple, p['representative_matches']))
        possible = {(e['query_index'], e['candidate_index']) for e in p['possible_matches']}
        exact = {(i, j) for i, j in representative if q['origins'][i] == j}
        wrong = representative - exact; optional = representative - forced
        rows.append({'pair_id': pid, 'query_view_id': qid, 'group': q['group'], 'mechanism': q['mechanism'],
                     'qualifies': p['original_qualifies'], 'query_tokens': len(p['query_tokens']),
                     'representative_matches': len(representative), 'representative_exact': len(exact),
                     'forced_matches': len(forced), 'forced_exact': len(forced & exact),
                     'optional_representative_matches': len(optional), 'optional_representative_exact': len(optional & exact),
                     'wrong_removed': len(wrong - forced), 'wrong_retained': len(wrong & forced),
                     'correct_discarded': len(exact - forced), 'possible_matches': len(possible),
                     'matched_pair_ambiguity': p['matched_pair_ambiguity'],
                     'gap_order_only_multiplicity': p['gap_order_only_multiplicity']})
        for i, j in sorted(wrong):
            disagreements.append({'pair_id': pid, 'query_index': i, 'returned_candidate_index': j,
                                  'origin_index': q['origins'][i], 'group': q['group'], 'mechanism': q['mechanism'],
                                  'qualifies': p['original_qualifies'], 'retained_as_forced': (i, j) in forced,
                                  'origin_edge_possible': (i, q['origins'][i]) in possible,
                                  'possible_partners': p['query_tokens'][i]['possible_partners']})
    primary = [r for r in rows if r['qualifies']]
    grouped = {}
    for group in dict.fromkeys(q['group'] for q in oracle['queries']):
        grouped[group] = {}
        for mechanism in dict.fromkeys(q['mechanism'] for q in oracle['queries']):
            selected = [r for r in rows if (r['group'], r['mechanism']) == (group, mechanism)]
            grouped[group][mechanism] = {'all_parents': summarize(selected),
                                         'qualified_parents': summarize([r for r in selected if r['qualifies']])}
    requirements = {'all_primary_forced_matches_origin_exact': all(r['wrong_retained'] == 0 for r in primary),
                    'every_primary_pair_retains_a_match': bool(primary) and all(r['forced_matches'] > 0 for r in primary)}
    return {'parent_pairs': rows, 'origin_disagreements': disagreements,
            'all_parent_summary': summarize(rows), 'primary_summary': summarize(primary),
            'qualified_policy_coverage_all_query_tokens': [sum(r['forced_matches'] for r in primary),
                                                          sum(r['query_tokens'] for r in rows)],
            'by_group_mechanism': grouped,
            'synthetic_hypothesis': {'requirements': requirements, 'passed': all(requirements.values())}}


def structural_summary(result):
    ps = list(result['pairs'].values())
    return {'pairs': len(ps), 'queries': result['queries'], 'panels': result['panels'],
            'pairs_without_matches': sum(p['original_matched_tokens'] == 0 for p in ps),
            'pairs_with_multiple_operation_paths': sum(p['optimal_operation_paths'] > 1 for p in ps),
            'pairs_with_matched_pair_ambiguity': sum(p['matched_pair_ambiguity'] for p in ps),
            'pairs_with_gap_order_only_multiplicity': sum(p['gap_order_only_multiplicity'] for p in ps),
            'representative_matches': sum(p['original_matched_tokens'] for p in ps),
            'forced_matches': sum(len(p['forced_matches']) for p in ps),
            'possible_matches': sum(len(p['possible_matches']) for p in ps),
            'query_token_statuses': dict(Counter(t['status'] for p in ps for t in p['query_tokens'])),
            'candidate_token_statuses': dict(Counter(t['status'] for p in ps for t in p['candidate_tokens']))}
