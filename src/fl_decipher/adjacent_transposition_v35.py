"""Global alignment with fixed-cost disjoint adjacent crossing blocks."""
from collections import defaultdict
import hashlib

from fl_decipher.synthetic_transfer_v32 import view, decode, decision
from fl_decipher.alignment_ambiguity_v33 import token_ledger
from fl_decipher.positional_worlds_v34 import canonical, assess as assess_worlds, score


def operations(q, c, i, j):
    n, m = len(q), len(c)
    if i < n and j < m and q[i] is not None and q[i] == c[j]:
        yield {'kind': 'match', 'from': [i, j], 'to': [i+1, j+1], 'cost': 0, 'matches': [[i, j]]}
    if i+1 < n and j+1 < m and q[i] is not None and q[i+1] is not None and q[i] != q[i+1] and q[i] == c[j+1] and q[i+1] == c[j]:
        yield {'kind': 'swap', 'from': [i, j], 'to': [i+2, j+2], 'cost': 1, 'matches': [[i, j+1], [i+1, j]]}
    if i < n:
        yield {'kind': 'query_gap', 'from': [i, j], 'to': [i+1, j], 'cost': 1, 'matches': []}
    if j < m:
        yield {'kind': 'candidate_gap', 'from': [i, j], 'to': [i, j+1], 'cost': 1, 'matches': []}


def add(a, b): return a[0]+b[0], a[1]+b[1]
def weight(op): return op['cost'], -len(op['matches'])


def align_forms(q, c):
    n, m = len(q), len(c)
    f = [[None]*(m+1) for _ in range(n+1)]; fw = [[0]*(m+1) for _ in range(n+1)]
    f[0][0] = (0, 0); fw[0][0] = 1
    for i in range(n+1):
        for j in range(m+1):
            for op in operations(q, c, i, j):
                a, b = op['to']; value = add(f[i][j], weight(op))
                if f[a][b] is None or value < f[a][b]: f[a][b] = value; fw[a][b] = fw[i][j]
                elif value == f[a][b]: fw[a][b] += fw[i][j]
    r = [[None]*(m+1) for _ in range(n+1)]; rw = [[0]*(m+1) for _ in range(n+1)]
    r[n][m] = (0, 0); rw[n][m] = 1
    for i in range(n, -1, -1):
        for j in range(m, -1, -1):
            if (i, j) == (n, m): continue
            for op in operations(q, c, i, j):
                a, b = op['to']; value = add(weight(op), r[a][b])
                if r[i][j] is None or value < r[i][j]: r[i][j] = value; rw[i][j] = rw[a][b]
                elif value == r[i][j]: rw[i][j] += rw[a][b]
    optimum, paths = f[n][m], fw[n][m]
    assert r[0][0] == optimum and rw[0][0] == paths
    possible_ops = []; pair_counts = defaultdict(int); supports = defaultdict(list)
    for i in range(n+1):
        for j in range(m+1):
            for op in operations(q, c, i, j):
                a, b = op['to']
                if op['matches'] and add(add(f[i][j], weight(op)), r[a][b]) == optimum:
                    through = fw[i][j]*rw[a][b]; index = len(possible_ops)
                    possible_ops.append({**op, 'through_paths': through, 'forced': through == paths})
                    for pair in op['matches']:
                        pair = tuple(pair); pair_counts[pair] += through; supports[pair].append(index)
    edges = [{'query_index': i, 'candidate_index': j, 'through_paths': count,
              'forced': count == paths, 'supporting_operations': supports[(i, j)]}
             for (i, j), count in sorted(pair_counts.items())]
    assert all(0 < e['through_paths'] <= paths for e in edges)
    forced = [[e['query_index'], e['candidate_index']] for e in edges if e['forced']]
    trace = []; i, j = n, m
    while i or j:
        chosen = None
        for kind, di, dj in [('match', 1, 1), ('swap', 2, 2), ('query_gap', 1, 0), ('candidate_gap', 0, 1)]:
            a, b = i-di, j-dj
            if a < 0 or b < 0: continue
            for op in operations(q, c, a, b):
                if op['kind'] == kind and op['to'] == [i, j] and add(f[a][b], weight(op)) == f[i][j]:
                    chosen = op; break
            if chosen is not None: break
        assert chosen is not None
        trace.append(chosen); i, j = chosen['from']
    trace.reverse(); representative = [pair for op in trace for pair in op['matches']]
    matched = -optimum[1]; crosses = sum(op['kind'] == 'swap' for op in trace)
    assert len(representative) == matched and sum(op['cost'] for op in trace) == optimum[0]
    assert optimum[0] == n+m-2*matched+crosses
    assert set(map(tuple, forced)) <= set(map(tuple, representative))
    assert len({a for a, b in forced}) == len(forced) == len({b for a, b in forced})
    assert [k for op in trace for k in range(op['from'][0], op['to'][0])] == list(range(n))
    assert [k for op in trace for k in range(op['from'][1], op['to'][1])] == list(range(m))
    return {'edit_cost': optimum[0], 'matched_tokens': matched, 'score': matched, 'cross_operations': crosses,
            'optimal_operation_paths': paths, 'trace': trace, 'query_coverage': [matched, n], 'candidate_coverage': [matched, m],
            'qualifies': matched >= 24 and 5*matched >= 4*n and 5*matched >= 4*m,
            'possible_operations': possible_ops, 'possible_matches': edges, 'forced_matches': forced,
            'representative_matches': representative, 'matched_pair_ambiguity': len(forced) < matched,
            'pair_invariant_operation_multiplicity': paths > 1 and len(forced) == matched,
            'query_tokens': token_ledger(n, edges, paths, 'query_index'),
            'candidate_tokens': token_ledger(m, edges, paths, 'candidate_index')}


def prepare(old_public, old_oracle, model):
    observations = dict(old_public['observations']); controls = []; panels = []; panel_gold = []
    def store(source, query):
        obs = {'source': source, 'query': query}; oid = 'observation'+hashlib.sha256(canonical(obs)).hexdigest()
        assert oid not in observations or observations[oid] == obs
        observations[oid] = obs
        return oid
    for passage in sorted({s['passage'] for s in old_oracle['sites']}):
        sites = [s for s in old_oracle['sites'] if s['passage'] == passage]
        unequal = next(s for s in sites if s['symbol_relation'] == 'unequal')
        oid = unequal['worlds'][0]['observation_id']; original = old_public['observations'][oid]
        source, query = original['source'], original['query']; n = len(source['tokens'])
        sf = [t['form'] for t in source['tokens']]; qf = [t['form'] for t in query['tokens']]
        at = unequal['left_index']; barrier = next(i for i in range(n-1) if source['tokens'][i]['blocked'] or source['tokens'][i+1]['blocked'])
        unknown_all = [f if query['tokens'][i]['blocked'] else f'v35unknownallp{passage}at{i}' for i, f in enumerate(qf)]
        endpoint = qf.copy(); endpoint[at], endpoint[at+1] = endpoint[at+1], endpoint[at]; endpoint[at] = f'v35unknownendpointp{passage}'
        barrier_q = qf.copy(); barrier_q[barrier], barrier_q[barrier+1] = barrier_q[barrier+1], barrier_q[barrier]
        rotate = [f if source['tokens'][i]['blocked'] else 'symbol'+str((int(f[6:])+1)%24) for i, f in enumerate(sf)]
        frame = [f if source['tokens'][i]['blocked'] else f'v35framep{passage}at{i}' for i, f in enumerate(sf)]
        ids = {}
        for role, source_forms, query_forms, affected in [
            ('identity', sf, qf, []), ('unknown_all', sf, unknown_all, []),
            ('unknown_endpoint', sf, endpoint, [at, at+1]), ('barrier_swap', sf, barrier_q, [barrier, barrier+1]),
            ('blocked_source', ['copiedanchor0']*n, qf, []), ('impostor', rotate, qf, []), ('frame_source', frame, qf, [])]:
            sid = store(view(source_forms), view(query_forms)); ids[role] = sid
            origins = None if role in ('blocked_source', 'impostor', 'frame_source') else list(range(n))
            if role in ('unknown_endpoint', 'barrier_swap'):
                i, j = affected; origins[i], origins[j] = origins[j], origins[i]
            for f in query_forms:
                if f.startswith('v35unknown'): assert f not in model['entries'] and f not in model['ledger']
            controls.append({'control_id': f'p{passage}{role}', 'passage': passage, 'role': role,
                             'observation_id': sid, 'origins': origins, 'affected_positions': affected})
        for scenario, roles in [('present', ['identity', 'impostor', 'frame_source']),
                                ('absent', ['impostor', 'frame_source']),
                                ('duplicate', ['identity', 'identity', 'impostor', 'frame_source'])]:
            candidates = [{'slot_id': f'slot{i}', 'observation_id': ids[role]} for i, role in enumerate(roles)]
            pid = 'panel'+hashlib.sha256(canonical(candidates)).hexdigest()
            panels.append({'panel_id': pid, 'candidates': candidates})
            panel_gold.append({'panel_id': pid, 'passage': passage, 'scenario': scenario,
                               'expected_nominated': 'slot0' if scenario == 'present' else None})
    return {'observations': observations, 'panels': panels}, {
        'v34_sites': old_oracle['sites'], 'v34_observation_ids': list(old_public['observations']),
        'controls': controls, 'panels': panel_gold}


ALIGN_FIELDS = {'edit_cost', 'matched_tokens', 'score', 'cross_operations', 'optimal_operation_paths', 'trace',
                'query_coverage', 'candidate_coverage', 'qualifies'}


def predict(public, model):
    predictions = {}
    for oid, obs in public['observations'].items():
        assert set(obs) == {'source', 'query'}
        decoded = decode(obs['query'], model); q = [d['source_form'] for d in decoded]
        c = [None if t['blocked'] else t['form'] for t in obs['source']['tokens']]
        r = align_forms(q, c)
        predictions[oid] = {'decoded_query': decoded, 'alignment': {k: v for k, v in r.items() if k in ALIGN_FIELDS},
                            'ambiguity': {k: v for k, v in r.items() if k not in ALIGN_FIELDS}}
    panels = []
    for panel in public['panels']:
        scores = [{'unit_id': c['slot_id'], 'score': predictions[c['observation_id']]['alignment']['score'],
                   'qualifies': predictions[c['observation_id']]['alignment']['qualifies'], 'observation_id': c['observation_id']}
                  for c in panel['candidates']]
        panels.append({'panel_id': panel['panel_id'], 'scores': scores, 'decision': decision(scores)})
    return {'predictions': predictions, 'panels': panels, 'oracle_used': False,
            'aligner_input_fields': ['source', 'query']}


def assess(public, oracle, predictions, baseline):
    old_public = {'observations': {oid: public['observations'][oid] for oid in oracle['v34_observation_ids']}}
    worlds = assess_worlds(old_public, {'sites': oracle['v34_sites']}, predictions)
    controls = []
    for row in oracle['controls']:
        obs = public['observations'][row['observation_id']]; p = predictions['predictions'][row['observation_id']]
        origin_scores = None
        if row['origins'] is not None:
            origin_scores = {policy: {scope: score(p['ambiguity'][field], row['origins'], obs['source'], positions)
                                      for scope, positions in [('full', list(range(len(obs['query']['tokens'])))), ('affected', row['affected_positions'])]}
                             for policy, field in [('representative', 'representative_matches'), ('forced', 'forced_matches')]}
        controls.append({**{k: row[k] for k in ['control_id', 'passage', 'role', 'observation_id']},
                         **{k: p['alignment'][k] for k in ['matched_tokens', 'edit_cost', 'cross_operations', 'qualifies']},
                         'origin_scores': origin_scores})
    panel_rows = []
    by_panel = {p['panel_id']: p for p in predictions['panels']}
    for gold in oracle['panels']:
        p = by_panel[gold['panel_id']]
        panel_rows.append({**gold, 'decision': p['decision'], 'expected_decision_met': p['decision']['nominated'] == gold['expected_nominated']})
    guard = True
    for oid, p in predictions['predictions'].items():
        obs = public['observations'][oid]
        for e in p['ambiguity']['possible_matches']:
            i, j = e['query_index'], e['candidate_index']
            guard = guard and p['decoded_query'][i]['source_form'] is not None and not obs['query']['tokens'][i]['blocked'] and not obs['source']['tokens'][j]['blocked']
    affected = worlds['by_relation_world']['unequal']['swap']['forced']['affected']
    identities = [worlds['by_relation_world'][r]['identity']['forced']['full'] for r in ('equal', 'unequal')]
    expected_identity = sum(sum(d['source_form'] is not None for d in predictions['predictions'][w['observation_id']]['decoded_query'])
                            for site in oracle['v34_sites'] for w in site['worlds'] if w['world'] == 'identity')
    zero_controls = [c for c in controls if c['role'] in ('unknown_all', 'blocked_source', 'frame_source')]
    impostors = [c for c in controls if c['role'] == 'impostor']
    req = {'all_658_unequal_swap_positions_forced_origin_exact': affected['tokens'] == 658 and affected['emitted'] == affected['strict_exact'] == 658,
           'all_mapped_identity_positions_forced_origin_exact': expected_identity > 0 and all(c['emitted'] == c['strict_exact'] for c in identities) and sum(c['emitted'] for c in identities) == expected_identity,
           'no_unknown_or_blocked_possible_matches': guard,
           'all_18_zero_match_controls_rejected': len(zero_controls) == 18 and all(c['matched_tokens'] == 0 and not c['qualifies'] for c in zero_controls),
           'all_6_impostors_rejected': len(impostors) == 6 and all(not c['qualifies'] for c in impostors),
           'all_6_present_panels_recover': sum(r['scenario'] == 'present' for r in panel_rows) == 6 and all(r['expected_decision_met'] for r in panel_rows if r['scenario'] == 'present'),
           'all_6_absent_panels_abstain': sum(r['scenario'] == 'absent' for r in panel_rows) == 6 and all(r['decision']['nominated'] is None for r in panel_rows if r['scenario'] == 'absent'),
           'all_6_duplicate_panels_abstain': sum(r['scenario'] == 'duplicate' for r in panel_rows) == 6 and all(r['decision']['nominated'] is None for r in panel_rows if r['scenario'] == 'duplicate')}
    previous = baseline['by_relation_world']['unequal']['swap']['forced']['affected']
    old_equal = baseline['by_relation_world']['equal']['swap']['forced']['affected']; new_equal = worlds['by_relation_world']['equal']['swap']['forced']['affected']
    return {'world_assessment': worlds, 'controls': controls, 'panels': panel_rows,
            'synthetic_recovery_gate': {'requirements': req, 'passed': all(req.values())},
            'baseline_comparison': {'unequal_swap_forced_affected_before': previous, 'unequal_swap_forced_affected_after': affected,
                                    'delta_returned': affected['emitted']-previous['emitted'], 'delta_exact': affected['strict_exact']-previous['strict_exact'],
                                    'equal_swap_affected_wrong_before': old_equal['emitted']-old_equal['strict_exact'],
                                    'equal_swap_affected_wrong_after': new_equal['emitted']-new_equal['strict_exact']}}
