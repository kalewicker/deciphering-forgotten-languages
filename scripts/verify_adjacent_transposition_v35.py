"""Independent integer-weighted DAG and mandatory token-pair verification."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from verify_synthetic_transfer_v32 import reference_decode, reference_decision
from verify_positional_worlds_v34 import reference_view, reference_assess as reference_worlds, metric_row, canonical

RUN = 'runs/000035_adjacent_transposition'


def read(p): return json.loads((ROOT / p).read_text())
def sha(p): return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()


def incoming(q, c, i, j):
    if i and j and q[i-1] is not None and q[i-1] == c[j-1]:
        yield {'kind': 'match', 'from': [i-1, j-1], 'to': [i, j], 'cost': 0, 'matches': [[i-1, j-1]]}
    if i >= 2 and j >= 2 and q[i-1] is not None and q[i-2] is not None and q[i-1] != q[i-2] and q[i-1] == c[j-2] and q[i-2] == c[j-1]:
        yield {'kind': 'swap', 'from': [i-2, j-2], 'to': [i, j], 'cost': 1, 'matches': [[i-2, j-1], [i-1, j-2]]}
    if i:
        yield {'kind': 'query_gap', 'from': [i-1, j], 'to': [i, j], 'cost': 1, 'matches': []}
    if j:
        yield {'kind': 'candidate_gap', 'from': [i, j-1], 'to': [i, j], 'cost': 1, 'matches': []}


def distances(q, c, keep_mandatory):
    n, m = len(q), len(c); scale = n+m+1
    dist = [[0]*(m+1) for _ in range(n+1)]; ways = [[0]*(m+1) for _ in range(n+1)]
    bits = [[0]*(m+1) for _ in range(n+1)] if keep_mandatory else None
    ways[0][0] = 1
    for i in range(n+1):
        for j in range(m+1):
            if i+j == 0: continue
            choices = []
            for op in incoming(q, c, i, j):
                a, b = op['from']; value = dist[a][b]+scale*op['cost']-len(op['matches'])
                labels = 0
                if keep_mandatory:
                    labels = bits[a][b]
                    for qi, si in op['matches']: labels |= 1 << (qi*m+si)
                choices.append((value, ways[a][b], labels))
            best = min(x[0] for x in choices); selected = [x for x in choices if x[0] == best]
            dist[i][j] = best; ways[i][j] = sum(x[1] for x in selected)
            if keep_mandatory:
                common = selected[0][2]
                for x in selected[1:]: common &= x[2]
                bits[i][j] = common
    return dist, ways, bits[n][m] if keep_mandatory else None


def reference_align(q, c):
    n, m = len(q), len(c); scale = n+m+1
    dist, ways, mandatory = distances(q, c, True)
    rev, tails, _ = distances(q[::-1], c[::-1], False)
    best, paths = dist[n][m], ways[n][m]
    assert best == rev[n][m] and paths == tails[n][m]
    trace = []; i, j = n, m
    while i+j:
        chosen = None
        for op in incoming(q, c, i, j):
            a, b = op['from']
            if dist[a][b]+scale*op['cost']-len(op['matches']) == dist[i][j]: chosen = op; break
        assert chosen is not None
        trace.append(chosen); i, j = chosen['from']
    trace.reverse()
    representatives = [pair for op in trace for pair in op['matches']]
    cost = sum(op['cost'] for op in trace); matched = len(representatives)
    assert cost*scale-matched == best
    possible_ops = []
    for i in range(n+1):
        for j in range(m+1):
            for op in incoming(q, c, i, j):
                a, b = op['from']
                if op['matches'] and dist[a][b]+scale*op['cost']-len(op['matches'])+rev[n-i][m-j] == best:
                    through = ways[a][b]*tails[n-i][m-j]
                    possible_ops.append({**op, 'through_paths': through, 'forced': through == paths})
    order = {'match': 0, 'swap': 1}
    possible_ops.sort(key=lambda op: (*op['from'], order[op['kind']]))
    pair_supports = {}
    for k, op in enumerate(possible_ops):
        for qi, si in op['matches']: pair_supports.setdefault((qi, si), []).append(k)
    edges = []
    for (qi, si), indexes in sorted(pair_supports.items()):
        count = sum(possible_ops[k]['through_paths'] for k in indexes)
        forced = bool(mandatory & (1 << (qi*m+si)))
        assert forced == (count == paths) and 0 < count <= paths
        edges.append({'query_index': qi, 'candidate_index': si, 'through_paths': count,
                      'forced': forced, 'supporting_operations': indexes})
    forced = [[e['query_index'], e['candidate_index']] for e in edges if e['forced']]
    def ledger(size, side, other):
        rows = []
        for index in range(size):
            es = [e for e in edges if e[side] == index]; gap = sum(e['through_paths'] for e in es) < paths
            status = 'always_gap' if not es else 'forced_match' if any(e['forced'] for e in es) else 'optional_match_or_gap' if gap else 'ambiguous_partner'
            rows.append({'token_index': index, 'possible_partners': [e[other] for e in es], 'gap_on_some_optimum': gap, 'status': status})
        return rows
    assert set(map(tuple, forced)) <= set(map(tuple, representatives))
    crosses = sum(op['kind'] == 'swap' for op in trace)
    assert cost == n+m-2*matched+crosses
    assert [x for op in trace for x in range(op['from'][0], op['to'][0])] == list(range(n))
    assert [x for op in trace for x in range(op['from'][1], op['to'][1])] == list(range(m))
    return {'edit_cost': cost, 'matched_tokens': matched, 'score': matched, 'cross_operations': crosses,
            'optimal_operation_paths': paths, 'trace': trace, 'query_coverage': [matched, n], 'candidate_coverage': [matched, m],
            'qualifies': matched >= 24 and matched*5 >= n*4 and matched*5 >= m*4,
            'possible_operations': possible_ops, 'possible_matches': edges, 'forced_matches': forced,
            'representative_matches': representatives, 'matched_pair_ambiguity': len(forced) != matched,
            'pair_invariant_operation_multiplicity': paths > 1 and len(forced) == matched,
            'query_tokens': ledger(n, 'query_index', 'candidate_index'), 'candidate_tokens': ledger(m, 'candidate_index', 'query_index')}


def reference_prepare(old_public, old_gold, model):
    observations = dict(old_public['observations']); rows = []; panels = []; gold_panels = []
    for passage in sorted({s['passage'] for s in old_gold['sites']}):
        sites = [s for s in old_gold['sites'] if s['passage'] == passage]
        site = min((s for s in sites if s['symbol_relation'] == 'unequal'), key=lambda s: s['left_index'])
        obs = old_public['observations'][site['worlds'][0]['observation_id']]
        sf = [t['form'] for t in obs['source']['tokens']]; qf = [t['form'] for t in obs['query']['tokens']]; n = len(sf)
        left = site['left_index']; barrier = min(i for i in range(n-1) if obs['source']['tokens'][i]['blocked'] or obs['source']['tokens'][i+1]['blocked'])
        ids = {}
        for role in ('identity', 'unknown_all', 'unknown_endpoint', 'barrier_swap', 'blocked_source', 'impostor', 'frame_source'):
            source, query = sf.copy(), qf.copy(); affected = []; origins = list(range(n))
            if role == 'unknown_all':
                query = [f'v35unknownallp{passage}at{i}' if not t['blocked'] else t['form'] for i, t in enumerate(obs['query']['tokens'])]
            elif role in ('unknown_endpoint', 'barrier_swap'):
                at = left if role == 'unknown_endpoint' else barrier
                query[at:at+2] = query[at:at+2][::-1]; origins[at:at+2] = origins[at:at+2][::-1]; affected = [at, at+1]
                if role == 'unknown_endpoint': query[at] = f'v35unknownendpointp{passage}'
            elif role == 'blocked_source': source = ['copiedanchor0' for _ in sf]
            elif role == 'impostor':
                source = [t['form'] if t['blocked'] else f"symbol{(int(t['form'][6:])+1)%24}" for t in obs['source']['tokens']]
            elif role == 'frame_source':
                source = [t['form'] if t['blocked'] else f'v35framep{passage}at{i}' for i, t in enumerate(obs['source']['tokens'])]
            if role in ('blocked_source', 'impostor', 'frame_source'): origins = None
            for form in query:
                if form.startswith('v35unknown'): assert form not in model['entries'] and form not in model['ledger']
            observation = {'source': reference_view(source), 'query': reference_view(query)}
            oid = 'observation'+hashlib.sha256(canonical(observation)).hexdigest()
            if oid in observations: assert observations[oid] == observation
            observations[oid] = observation; ids[role] = oid
            rows.append({'control_id': f'p{passage}{role}', 'passage': passage, 'role': role, 'observation_id': oid,
                         'origins': origins, 'affected_positions': affected})
        for scenario in ('present', 'absent', 'duplicate'):
            roles = ['identity', 'impostor', 'frame_source'] if scenario == 'present' else ['impostor', 'frame_source'] if scenario == 'absent' else ['identity', 'identity', 'impostor', 'frame_source']
            candidates = [{'slot_id': f'slot{i}', 'observation_id': ids[role]} for i, role in enumerate(roles)]
            pid = 'panel'+hashlib.sha256(canonical(candidates)).hexdigest()
            panels.append({'panel_id': pid, 'candidates': candidates})
            gold_panels.append({'panel_id': pid, 'passage': passage, 'scenario': scenario, 'expected_nominated': 'slot0' if scenario == 'present' else None})
    return {'observations': observations, 'panels': panels}, {'v34_sites': old_gold['sites'],
        'v34_observation_ids': list(old_public['observations']), 'controls': rows, 'panels': gold_panels}


ALIGN_KEYS = ['edit_cost', 'matched_tokens', 'score', 'cross_operations', 'optimal_operation_paths', 'trace', 'query_coverage', 'candidate_coverage', 'qualifies']


def reference_predict(public, model):
    result = {}
    for oid, obs in public['observations'].items():
        assert set(obs) == {'source', 'query'}
        assert oid == 'observation'+hashlib.sha256(canonical(obs)).hexdigest()
        d = reference_decode(obs['query'], model)
        r = reference_align([t['source_form'] for t in d], [None if t['blocked'] else t['form'] for t in obs['source']['tokens']])
        result[oid] = {'decoded_query': d, 'alignment': {k: r[k] for k in ALIGN_KEYS}, 'ambiguity': {k: v for k, v in r.items() if k not in ALIGN_KEYS}}
    panels = []
    for panel in public['panels']:
        scores = []
        for candidate in panel['candidates']:
            r = result[candidate['observation_id']]['alignment']
            scores.append({'unit_id': candidate['slot_id'], 'score': r['score'], 'qualifies': r['qualifies'], 'observation_id': candidate['observation_id']})
        panels.append({'panel_id': panel['panel_id'], 'scores': scores, 'decision': reference_decision(scores)})
    return {'predictions': result, 'panels': panels, 'oracle_used': False, 'aligner_input_fields': ['source', 'query']}


def reference_assess(public, oracle, pred, baseline):
    worlds = reference_worlds({'observations': {k: public['observations'][k] for k in oracle['v34_observation_ids']}}, {'sites': oracle['v34_sites']}, pred)
    controls = []
    for c in oracle['controls']:
        p = pred['predictions'][c['observation_id']]; obs = public['observations'][c['observation_id']]; metrics = None
        if c['origins'] is not None:
            metrics = {}
            for policy, field in [('representative', 'representative_matches'), ('forced', 'forced_matches')]:
                metrics[policy] = {}
                for scope in ('full', 'affected'):
                    positions = set(range(len(obs['query']['tokens']))) if scope == 'full' else set(c['affected_positions'])
                    chosen = [(i, j) for i, j in p['ambiguity'][field] if i in positions]
                    exact = sum(c['origins'][i] == j for i, j in chosen)
                    compatible = sum(obs['source']['tokens'][j]['form'] == obs['source']['tokens'][c['origins'][i]]['form'] for i, j in chosen)
                    metrics[policy][scope] = metric_row(len(positions), len(chosen), exact, compatible)
        controls.append({**{k: c[k] for k in ('control_id', 'passage', 'role', 'observation_id')},
                         **{k: p['alignment'][k] for k in ('matched_tokens', 'edit_cost', 'cross_operations', 'qualifies')}, 'origin_scores': metrics})
    panel_rows = []
    for gold in oracle['panels']:
        p = next(p for p in pred['panels'] if p['panel_id'] == gold['panel_id'])
        panel_rows.append({**gold, 'decision': p['decision'], 'expected_decision_met': p['decision']['nominated'] == gold['expected_nominated']})
    guard = True
    for oid, p in pred['predictions'].items():
        for e in p['ambiguity']['possible_matches']:
            i, j = e['query_index'], e['candidate_index']; obs = public['observations'][oid]
            if p['decoded_query'][i]['source_form'] is None or obs['query']['tokens'][i]['blocked'] or obs['source']['tokens'][j]['blocked']: guard = False
    known_identity = 0
    for site in oracle['v34_sites']:
        for world in site['worlds']:
            if world['world'] == 'identity': known_identity += sum(d['source_form'] is not None for d in pred['predictions'][world['observation_id']]['decoded_query'])
    identities = [worlds['by_relation_world'][relation]['identity']['forced']['full'] for relation in ('equal', 'unequal')]
    affected = worlds['by_relation_world']['unequal']['swap']['forced']['affected']
    zeros = [c for c in controls if c['role'] in ['unknown_all', 'blocked_source', 'frame_source']]; impostors = [c for c in controls if c['role'] == 'impostor']
    req = {'all_658_unequal_swap_positions_forced_origin_exact': affected['tokens'] == 658 and affected['emitted'] == affected['strict_exact'] == 658,
           'all_mapped_identity_positions_forced_origin_exact': known_identity > 0 and sum(x['emitted'] for x in identities) == known_identity and all(x['emitted'] == x['strict_exact'] for x in identities),
           'no_unknown_or_blocked_possible_matches': guard,
           'all_18_zero_match_controls_rejected': len(zeros) == 18 and all(c['matched_tokens'] == 0 and c['qualifies'] is False for c in zeros),
           'all_6_impostors_rejected': len(impostors) == 6 and all(c['qualifies'] is False for c in impostors),
           'all_6_present_panels_recover': len([p for p in panel_rows if p['scenario'] == 'present']) == 6 and all(p['expected_decision_met'] for p in panel_rows if p['scenario'] == 'present'),
           'all_6_absent_panels_abstain': len([p for p in panel_rows if p['scenario'] == 'absent']) == 6 and all(p['decision']['nominated'] is None for p in panel_rows if p['scenario'] == 'absent'),
           'all_6_duplicate_panels_abstain': len([p for p in panel_rows if p['scenario'] == 'duplicate']) == 6 and all(p['decision']['nominated'] is None for p in panel_rows if p['scenario'] == 'duplicate')}
    before = baseline['by_relation_world']['unequal']['swap']['forced']['affected']
    old_equal = baseline['by_relation_world']['equal']['swap']['forced']['affected']; new_equal = worlds['by_relation_world']['equal']['swap']['forced']['affected']
    return {'world_assessment': worlds, 'controls': controls, 'panels': panel_rows, 'synthetic_recovery_gate': {'requirements': req, 'passed': all(req.values())},
            'baseline_comparison': {'unequal_swap_forced_affected_before': before, 'unequal_swap_forced_affected_after': affected,
                                    'delta_returned': affected['emitted']-before['emitted'], 'delta_exact': affected['strict_exact']-before['strict_exact'],
                                    'equal_swap_affected_wrong_before': old_equal['emitted']-old_equal['strict_exact'],
                                    'equal_swap_affected_wrong_after': new_equal['emitted']-new_equal['strict_exact']}}


def main():
    from verify_correspondence_v6 import check_hashes
    cfg = read('experiments/adjacent_transposition_v35.json'); pre = read('data/v35/preflight.json'); bench = read('benchmarks/adjacent_transposition_v35.json')
    manifest = check_hashes(ROOT / RUN)
    for hashes in [cfg['input_hashes'], pre['input_hashes'], pre['code_hashes'], bench['input_hashes']]:
        for p, h in hashes.items(): assert sha(p) == h, p
    assert {k: cfg[k] for k in ['primary_affected_positions', 'v34_worlds', 'v34_sites', 'v34_excluded_sites', 'control_rows', 'panels']} == dict(zip(['primary_affected_positions', 'v34_worlds', 'v34_sites', 'v34_excluded_sites', 'control_rows', 'panels'], [658, 684, 378, 36, 42, 18]))
    assert cfg['coverage'] == [4, 5] and cfg['minimum_matches'] == 24 and cfg['transposition_cost'] == cfg['gap_cost'] == 1
    assert manifest['code_hashes'] == pre['code_hashes']
    prep = read('data/v35/preparation_receipt.json'); pr = read(RUN+'/prediction_receipt.json')
    assert cfg['registered_at_utc'] < pre['sealed_at_utc'] < prep['prepared_at_utc'] < bench['frozen_at_utc'] < manifest['started_at_utc'] < pr['predictions_frozen_at_utc'] < manifest['finished_at_utc']
    assert prep['predictions_computed'] == 0 and prep['control_rows'] == 42 and prep['panels'] == 18
    for p, h in prep['output_hashes'].items(): assert sha(p) == h, p
    model = read('data/v32/frozen_mapping.json')['model']; old_public = read('data/v34/public_observations.json'); old_gold = read('data/v34/oracle.json')
    public, oracle = reference_prepare(old_public, old_gold, model)
    assert public == read('data/v35/public_observations.json') and oracle == read('data/v35/oracle.json')
    assert oracle['v34_sites'] == old_gold['sites'] and len(oracle['v34_sites']) == 378
    assert all(public['observations'][k] == v for k, v in old_public['observations'].items())
    pred = reference_predict(public, model); assert pred == read(RUN+'/predictions.json')
    assert pr['oracle_used_for_prediction'] is False and pr['predictions_sha256'] == sha(RUN+'/predictions.json')
    payload = hashlib.sha256(json.dumps(model, sort_keys=True).encode()).hexdigest()
    assert pr['model_payload_sha256_before'] == pr['model_payload_sha256_after'] == payload
    assessment = reference_assess(public, oracle, pred, read('runs/000034_positional_worlds/assessment.json'))
    assert assessment == read(RUN+'/assessment.json')
    w = assessment['world_assessment']; assert w['site_inventory']['worlds'] == 684 and w['site_inventory']['excluded_sites'] == 36
    report = {'experiment_id': cfg['experiment_id'], 'engineering_integrity_passed': True, 'mapping_unchanged': True,
              'observations': len(public['observations']), 'v34_observations_preserved': len(old_public['observations']), 'control_rows': 42, 'panels': 18,
              'site_inventory': w['site_inventory'], 'by_relation_world': w['by_relation_world'], 'all_worlds': w['all_worlds'],
              'collision_demonstration': w['identifiability_demonstration'], 'synthetic_recovery_gate': assessment['synthetic_recovery_gate'],
              'baseline_comparison': assessment['baseline_comparison'],
              'structural_summary': {'observations_with_cross_operations': sum(p['alignment']['cross_operations'] > 0 for p in pred['predictions'].values()),
                                     'observations_with_matched_pair_ambiguity': sum(p['ambiguity']['matched_pair_ambiguity'] for p in pred['predictions'].values()),
                                     'possible_cross_operations': sum(op['kind'] == 'swap' for p in pred['predictions'].values() for op in p['ambiguity']['possible_operations'])},
              'symbolic_transposition_aligner_executed': True, 'external_or_neural_model_executed': False,
              'scientific_acceptance': None, 'semantic_evaluation_metrics': None, 'semantic_labels_admitted': 0, 'source_identities_admitted': 0,
              'independent_reviews_admitted': 0, 'untouched_test_units_admitted': 0, 'natural_targets_rescored': 0,
              'prior_retrieval_decisions_changed': 0, 'new_network_requests': 0, 'symbol_compatibility_is_independent_accuracy': False}
    assert report == read(RUN+'/report.json')
    preserved = []
    for p in sorted((ROOT/'runs').glob('*/manifest.json')):
        if p.parent != ROOT/RUN: check_hashes(p.parent); preserved.append(p.parent.name)
    assert len(preserved) == 34
    for p in (ROOT/'reports').glob('*_deliverable_seal.json'):
        for n, h in json.loads(p.read_text()).get('deliverable_hashes', {}).items(): assert sha(n) == h, n
    verified = {'state': 'verified', 'run_manifest_sha256': sha(RUN+'/manifest.json'), 'independent_control_reconstruction': True,
                'independent_integer_dag_and_pair_dominators': True, 'engineering_integrity_passed': True,
                'observations_verified': len(public['observations']), 'v34_worlds_verified': 684, 'control_rows_verified': 42, 'panels_verified': 18,
                'synthetic_recovery_gate_passed': assessment['synthetic_recovery_gate']['passed'], 'baseline_comparison': assessment['baseline_comparison'],
                'prior_runs_preserved': preserved, 'scientific_acceptance': None, 'semantic_labels_admitted': 0}
    target = ROOT/'reports/000035_verification.json'
    if target.exists(): assert {k: v for k, v in json.loads(target.read_text()).items() if k != 'verified_at_utc'} == verified
    else:
        verified['verified_at_utc'] = datetime.now(timezone.utc).isoformat(); target.write_text(json.dumps(verified, indent=2)+'\n')
    print(json.dumps(verified, indent=2))


if __name__ == '__main__': main()
