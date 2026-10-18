"""Content-only paired worlds, preserving strict ancestry and symbol checks."""
import hashlib
import json
from collections import Counter

from fl_decipher.synthetic_transfer_v32 import view, decode, align
from fl_decipher.alignment_ambiguity_v33 import audit_pair


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode()


def prepare(public_v32, oracle_v32, model, cfg):
    parents = {b['base_id']: b['view_ids']['parent'] for b in oracle_v32['bases']}
    selected = sorted((q for q in oracle_v32['queries'] if q['group'] == cfg['group'] and
                       q['key'] == cfg['key'] and q['mechanism'] == cfg['query_mechanism']), key=lambda q: q['passage'])
    assert [q['passage'] for q in selected] == cfg['passages']
    observations, sites = {}, []
    def add(source, query):
        observation = {'source': source, 'query': query}
        oid = 'observation' + hashlib.sha256(canonical(observation)).hexdigest()
        assert oid not in observations or observations[oid] == observation
        observations[oid] = observation
        return oid
    for q in selected:
        source_id = parents[q['base_id']]; query_id = q['query_view_id']
        source = public_v32['views'][source_id]; query = public_v32['views'][query_id]
        n = len(source['tokens']); decoded = decode(query, model)
        assert len(query['tokens']) == n == cfg['source_length']
        for i, d in enumerate(decoded):
            assert d['source_form'] is None or d['source_form'] == source['tokens'][i]['form']
        for i in range(n-1):
            row = {'site_id': f"p{q['passage']}at{i}", 'passage': q['passage'], 'left_index': i,
                   'source_view_id': source_id, 'identity_query_view_id': query_id}
            reasons = []
            if any(source['tokens'][j]['blocked'] or query['tokens'][j]['blocked'] for j in (i, i+1)):
                reasons.append('blocked_endpoint')
            if any(decoded[j]['source_form'] is None for j in (i, i+1)):
                reasons.append('unmapped_endpoint')
            row.update(eligible=not reasons, exclusion_reasons=reasons, symbol_relation=None, worlds=[])
            if not reasons:
                row['symbol_relation'] = 'equal' if source['tokens'][i]['form'] == source['tokens'][i+1]['form'] else 'unequal'
                forms = [t['form'] for t in query['tokens']]
                swapped = forms.copy(); swapped[i], swapped[i+1] = swapped[i+1], swapped[i]
                origins = list(range(n)); swapped_origins = origins.copy()
                swapped_origins[i], swapped_origins[i+1] = swapped_origins[i+1], swapped_origins[i]
                row['worlds'] = [{'world': 'identity', 'observation_id': add(source, query), 'origins': origins},
                                 {'world': 'swap', 'observation_id': add(source, view(swapped)), 'origins': swapped_origins}]
            sites.append(row)
    assert len(sites) == cfg['site_denominator']
    return {'observations': observations}, {'sites': sites}


def predict(public, model):
    predictions = {}
    for oid, observation in public['observations'].items():
        assert set(observation) == {'source', 'query'}
        source, query = observation['source'], observation['query']
        decoded = decode(query, model); alignment = align(query, source, decoded)
        predictions[oid] = {'decoded_query': decoded, 'alignment': alignment,
                            'ambiguity': audit_pair(decoded, source['tokens'], alignment)}
    return {'predictions': predictions, 'oracle_used': False, 'predictor_input_fields': ['source', 'query']}


def score(matches, origins, source, positions):
    selected = [(i, j) for i, j in matches if i in positions]
    exact = sum(origins[i] == j for i, j in selected)
    compatible = sum(source['tokens'][j]['form'] == source['tokens'][origins[i]]['form'] for i, j in selected)
    return counts(len(positions), len(selected), exact, compatible)


def counts(tokens, emitted, exact, compatible):
    return {'tokens': tokens, 'emitted': emitted, 'strict_exact': exact, 'symbol_compatible': compatible,
            'strict_precision': [exact, emitted], 'symbol_compatibility': [compatible, emitted], 'coverage': [emitted, tokens]}


def aggregate(rows):
    result = {'worlds': len(rows)}
    for policy in ('representative', 'forced'):
        result[policy] = {}
        for scope in ('full', 'affected'):
            values = [r['scores'][policy][scope] for r in rows]
            result[policy][scope] = counts(*(sum(v[k] for v in values) for k in ('tokens', 'emitted', 'strict_exact', 'symbol_compatible')))
    return result


def assess(public, oracle, predictions, minimum_returns=1):
    world_rows, certificates = [], []
    for site in oracle['sites']:
        if not site['eligible']: continue
        index = site['left_index']; affected = [index, index+1]
        worlds = site['worlds']; a, b = [public['observations'][w['observation_id']] for w in worlds]
        same_input = canonical(a) == canonical(b)
        same_prediction = predictions['predictions'][worlds[0]['observation_id']] == predictions['predictions'][worlds[1]['observation_id']]
        different_origins = [i for i, (x, y) in enumerate(zip(worlds[0]['origins'], worlds[1]['origins'])) if x != y]
        certificate = {'site_id': site['site_id'], 'symbol_relation': site['symbol_relation'],
                       'public_input_bytes_equal': same_input, 'predictions_equal': same_prediction,
                       'origin_difference_indices': different_origins, 'balanced_point_bound': None}
        if same_input:
            choices = []
            for i in affected:
                exact_counts = [sum(w['origins'][i] == j for w in worlds) for j in range(len(a['source']['tokens']))]
                choices.append({'query_index': i, 'origins_by_world': [w['origins'][i] for w in worlds],
                                'exact_world_counts_by_returned_index': exact_counts,
                                'maximum_exact_worlds': max(exact_counts),
                                'set_valued_origin_union': sorted({w['origins'][i] for w in worlds})})
            certificate['balanced_point_bound'] = {'positions': choices, 'maximum_exact_calls': sum(c['maximum_exact_worlds'] for c in choices),
                                                    'fully_answered_calls': 4, 'oracle_union_set_coverage': [4, 4],
                                                    'oracle_union_is_predictor_output': False}
        certificates.append(certificate)
        for w in worlds:
            o = public['observations'][w['observation_id']]; pred = predictions['predictions'][w['observation_id']]
            sets = {'representative': pred['ambiguity']['representative_matches'], 'forced': pred['ambiguity']['forced_matches']}
            scores = {policy: {scope: score(matches, w['origins'], o['source'], pos)
                                for scope, pos in [('full', list(range(len(o['query']['tokens'])))), ('affected', affected)]}
                      for policy, matches in sets.items()}
            world_rows.append({'site_id': site['site_id'], 'world': w['world'], 'symbol_relation': site['symbol_relation'],
                               'observation_id': w['observation_id'], 'alignment_qualifies': pred['alignment']['qualifies'], 'scores': scores})
    strata = {relation: {world: aggregate([r for r in world_rows if r['symbol_relation'] == relation and r['world'] == world])
                         for world in ('identity', 'swap')} for relation in ('equal', 'unequal')}
    equal = [c for c in certificates if c['symbol_relation'] == 'equal']; unequal = [c for c in certificates if c['symbol_relation'] == 'unequal']
    requirements = {'equal_symbol_collision_exists': bool(equal), 'unequal_symbol_control_exists': bool(unequal),
                    'all_equal_inputs_and_predictions_identical': all(c['public_input_bytes_equal'] and c['predictions_equal'] for c in equal),
                    'all_equal_origins_differ_at_two_positions': all(len(c['origin_difference_indices']) == 2 for c in equal),
                    'all_equal_balanced_point_bounds_one_half': all(c['balanced_point_bound'] is not None and c['balanced_point_bound']['maximum_exact_calls'] == 2 for c in equal),
                    'all_unequal_inputs_distinct': all(not c['public_input_bytes_equal'] for c in unequal)}
    forced = strata['unequal']['swap']['forced']['affected']
    safety = {'zero_wrong_unequal_swap_affected_forced_origins': forced['emitted'] == forced['strict_exact'],
              'nonzero_unequal_swap_affected_forced_returns': forced['emitted'] >= minimum_returns}
    return {'site_inventory': {'sites': len(oracle['sites']), 'eligible_sites': len(certificates),
                               'excluded_sites': sum(not s['eligible'] for s in oracle['sites']),
                               'exclusion_reason_counts': dict(Counter(r for s in oracle['sites'] for r in s['exclusion_reasons'])),
                               'equal_sites': len(equal), 'unequal_sites': len(unequal), 'worlds': len(world_rows),
                               'unique_public_observations': len(public['observations']),
                               'reused_observation_occurrences': len(world_rows) - len(public['observations'])},
            'certificates': certificates, 'world_scores': world_rows, 'by_relation_world': strata,
            'all_worlds': aggregate(world_rows),
            'identifiability_demonstration': {'requirements': requirements, 'passed': all(requirements.values())},
            'unequal_swap_forced_safety_hypothesis': {'requirements': safety, 'passed': all(safety.values())}}
