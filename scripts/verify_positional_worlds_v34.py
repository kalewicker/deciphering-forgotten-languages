"""Independent paired-world reconstruction and frozen-algorithm replay."""
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from verify_synthetic_transfer_v32 import reference_decode, reference_align
from verify_alignment_ambiguity_v33 import reference_pair

RUN = 'runs/000034_positional_worlds'


def read(p): return json.loads((ROOT / p).read_text())
def sha(p): return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()
def canonical(v): return json.dumps(v, separators=(',', ':'), sort_keys=True).encode('utf-8')


def reference_view(forms):
    text = ' '.join(forms); tokens = []; start = 0
    for form in forms:
        tokens.append({'form': form, 'start': start, 'end': start + len(form),
                       'blocked': form in {'copiedanchor0', 'copiedanchor1', 'copiedanchor2'}})
        start += len(form) + 1
    return {'text': text, 'tokens': tokens}


def reference_prepare(public, gold, model, cfg):
    selected = [q for q in gold['queries'] if (q['key'], q['group'], q['mechanism']) == (cfg['key'], cfg['group'], cfg['query_mechanism'])]
    selected.sort(key=lambda q: q['passage'])
    assert [q['passage'] for q in selected] == cfg['passages']
    observations, registry = {}, []
    for q in selected:
        base = next(b for b in gold['bases'] if b['base_id'] == q['base_id'])
        sid, qid = base['view_ids']['parent'], q['query_view_id']
        source, query = public['views'][sid], public['views'][qid]
        sf = [t['form'] for t in source['tokens']]; qf = [t['form'] for t in query['tokens']]
        assert len(sf) == len(qf) == cfg['source_length']
        assert reference_view(sf) == source and reference_view(qf) == query
        decoded = reference_decode(query, model)
        assert all(d['source_form'] in (None, sf[i]) for i, d in enumerate(decoded))
        for at in range(len(sf)-1):
            exclusions = []
            if source['tokens'][at]['blocked'] or source['tokens'][at+1]['blocked'] or query['tokens'][at]['blocked'] or query['tokens'][at+1]['blocked']:
                exclusions.append('blocked_endpoint')
            if decoded[at]['source_form'] is None or decoded[at+1]['source_form'] is None:
                exclusions.append('unmapped_endpoint')
            site = {'site_id': f"p{q['passage']}at{at}", 'passage': q['passage'], 'left_index': at,
                    'source_view_id': sid, 'identity_query_view_id': qid, 'eligible': not exclusions,
                    'exclusion_reasons': exclusions, 'symbol_relation': None, 'worlds': []}
            if not exclusions:
                site['symbol_relation'] = 'equal' if sf[at] == sf[at+1] else 'unequal'
                for role in ('identity', 'swap'):
                    order = [at+1 if i == at else at if i == at+1 else i for i in range(len(sf))] if role == 'swap' else list(range(len(sf)))
                    observation = {'source': reference_view(sf), 'query': reference_view([qf[i] for i in order])}
                    oid = 'observation' + hashlib.sha256(canonical(observation)).hexdigest()
                    if oid in observations: assert observations[oid] == observation
                    observations[oid] = observation
                    site['worlds'].append({'world': role, 'observation_id': oid, 'origins': order})
            registry.append(site)
    assert len(registry) == cfg['site_denominator']
    return {'observations': observations}, {'sites': registry}


def reference_predict(public, model):
    result = {}
    for oid, obs in public['observations'].items():
        assert set(obs) == {'source', 'query'}
        assert oid == 'observation' + hashlib.sha256(canonical(obs)).hexdigest()
        decoded = reference_decode(obs['query'], model)
        path = reference_align(obs['query'], obs['source'], decoded)
        left = [d['source_form'] for d in decoded]
        right = [None if t['blocked'] else t['form'] for t in obs['source']['tokens']]
        ambiguity = reference_pair(left, right, path)
        result[oid] = {'decoded_query': decoded, 'alignment': path, 'ambiguity': ambiguity}
    return {'predictions': result, 'oracle_used': False, 'predictor_input_fields': ['source', 'query']}


def metric_row(tokens, returned, exact, compatible):
    return {'tokens': tokens, 'emitted': returned, 'strict_exact': exact, 'symbol_compatible': compatible,
            'coverage': [returned, tokens], 'strict_precision': [exact, returned], 'symbol_compatibility': [compatible, returned]}


def aggregate(rows):
    result = {'worlds': len(rows)}
    for policy in ('representative', 'forced'):
        result[policy] = {}
        for scope in ('full', 'affected'):
            cols = [r['scores'][policy][scope] for r in rows]
            result[policy][scope] = metric_row(*(sum(c[k] for c in cols) for k in ('tokens', 'emitted', 'strict_exact', 'symbol_compatible')))
    return result


def reference_assess(public, oracle, pred, minimum=1):
    rows, certificates = [], []
    equal_count = unequal_count = excluded = 0
    reasons = Counter()
    for site in oracle['sites']:
        reasons.update(site['exclusion_reasons'])
        if not site['eligible']:
            excluded += 1; continue
        equal = site['symbol_relation'] == 'equal'
        equal_count += equal; unequal_count += not equal
        first, second = site['worlds']; at = site['left_index']; affected = (at, at+1)
        oa = public['observations'][first['observation_id']]; ob = public['observations'][second['observation_id']]
        same = canonical(oa) == canonical(ob)
        cert = {'site_id': site['site_id'], 'symbol_relation': site['symbol_relation'],
                'public_input_bytes_equal': same,
                'predictions_equal': pred['predictions'][first['observation_id']] == pred['predictions'][second['observation_id']],
                'origin_difference_indices': [i for i in range(len(first['origins'])) if first['origins'][i] != second['origins'][i]],
                'balanced_point_bound': None}
        if same:
            positions = []
            for i in affected:
                origins = [first['origins'][i], second['origins'][i]]; counts = Counter(origins)
                table = [counts[j] for j in range(len(oa['source']['tokens']))]
                positions.append({'query_index': i, 'origins_by_world': origins,
                                  'exact_world_counts_by_returned_index': table, 'maximum_exact_worlds': max(table),
                                  'set_valued_origin_union': sorted(counts)})
            cert['balanced_point_bound'] = {'positions': positions, 'maximum_exact_calls': sum(max(p['exact_world_counts_by_returned_index']) for p in positions),
                                             'fully_answered_calls': len(positions)*2, 'oracle_union_set_coverage': [4, 4],
                                             'oracle_union_is_predictor_output': False}
            assert all(len(p['set_valued_origin_union']) == 2 for p in positions)
        certificates.append(cert)
        for w in site['worlds']:
            prediction = pred['predictions'][w['observation_id']]; obs = public['observations'][w['observation_id']]
            scores = {}
            for policy in ('representative', 'forced'):
                matches = prediction['ambiguity']['representative_matches' if policy == 'representative' else 'forced_matches']
                scores[policy] = {}
                for scope in ('full', 'affected'):
                    included = set(range(len(obs['query']['tokens']))) if scope == 'full' else set(affected)
                    returned = exact = compatible = 0
                    for qi, si in matches:
                        if qi not in included: continue
                        returned += 1
                        exact += si == w['origins'][qi]
                        compatible += obs['source']['tokens'][si]['form'] == obs['source']['tokens'][w['origins'][qi]]['form']
                    scores[policy][scope] = metric_row(len(included), returned, exact, compatible)
            rows.append({'site_id': site['site_id'], 'world': w['world'], 'symbol_relation': site['symbol_relation'],
                         'observation_id': w['observation_id'], 'alignment_qualifies': prediction['alignment']['qualifies'], 'scores': scores})
    strata = {}
    for relation in ('equal', 'unequal'):
        strata[relation] = {role: aggregate([r for r in rows if r['symbol_relation'] == relation and r['world'] == role]) for role in ('identity', 'swap')}
    collisions = [c for c in certificates if c['symbol_relation'] == 'equal']; controls = [c for c in certificates if c['symbol_relation'] == 'unequal']
    req = {'equal_symbol_collision_exists': equal_count > 0, 'unequal_symbol_control_exists': unequal_count > 0,
           'all_equal_inputs_and_predictions_identical': all(c['public_input_bytes_equal'] and c['predictions_equal'] for c in collisions),
           'all_equal_origins_differ_at_two_positions': all(len(c['origin_difference_indices']) == 2 for c in collisions),
           'all_equal_balanced_point_bounds_one_half': all(c['balanced_point_bound'] and c['balanced_point_bound']['maximum_exact_calls'] == 2 for c in collisions),
           'all_unequal_inputs_distinct': all(not c['public_input_bytes_equal'] for c in controls)}
    forced = strata['unequal']['swap']['forced']['affected']
    safety = {'zero_wrong_unequal_swap_affected_forced_origins': forced['strict_exact'] == forced['emitted'],
              'nonzero_unequal_swap_affected_forced_returns': forced['emitted'] >= minimum}
    return {'site_inventory': {'sites': len(oracle['sites']), 'eligible_sites': equal_count+unequal_count,
                               'excluded_sites': excluded, 'exclusion_reason_counts': dict(reasons), 'equal_sites': equal_count,
                               'unequal_sites': unequal_count, 'worlds': len(rows), 'unique_public_observations': len(public['observations']),
                               'reused_observation_occurrences': len(rows)-len(public['observations'])},
            'certificates': certificates, 'world_scores': rows, 'by_relation_world': strata, 'all_worlds': aggregate(rows),
            'identifiability_demonstration': {'requirements': req, 'passed': all(req.values())},
            'unequal_swap_forced_safety_hypothesis': {'requirements': safety, 'passed': all(safety.values())}}


def main():
    from verify_correspondence_v6 import check_hashes
    cfg = read('experiments/positional_worlds_v34.json'); pre = read('data/v34/preflight.json'); bench = read('benchmarks/positional_worlds_v34.json')
    manifest = check_hashes(ROOT / RUN)
    for inventory in [cfg['input_hashes'], pre['input_hashes'], pre['code_hashes'], bench['input_hashes']]:
        for p, h in inventory.items(): assert sha(p) == h, p
    assert cfg['key'] == 11 and cfg['group'] == 'seen' and cfg['query_mechanism'] == 'bijective'
    assert cfg['passages'] == list(range(6)) and cfg['source_length'] == 64 and cfg['site_denominator'] == 378
    assert cfg['worlds_per_eligible_site'] == 2 and cfg['minimum_unequal_swap_affected_forced_returns'] == 1
    assert manifest['code_hashes'] == pre['code_hashes']
    prep = read('data/v34/preparation_receipt.json'); receipt = read(RUN + '/prediction_receipt.json')
    assert cfg['registered_at_utc'] < pre['sealed_at_utc'] < prep['prepared_at_utc'] < bench['frozen_at_utc'] < manifest['started_at_utc'] < receipt['predictions_frozen_at_utc'] < manifest['finished_at_utc']
    assert prep['predictions_computed'] == 0 and prep['site_rows'] == 378 and prep['frozen_mapping_sha256'] == sha('data/v32/frozen_mapping.json')
    for p, h in prep['output_hashes'].items(): assert sha(p) == h
    model = read('data/v32/frozen_mapping.json')['model']
    public, oracle = reference_prepare(read('data/v32/public_cases.json'), read('data/v32/oracle.json'), model, cfg)
    assert public == read('data/v34/public_observations.json') and oracle == read('data/v34/oracle.json')
    predictions = reference_predict(public, model)
    assert predictions == read(RUN + '/predictions.json')
    assert receipt['oracle_used_for_prediction'] is False and receipt['predictions_sha256'] == sha(RUN + '/predictions.json')
    payload = hashlib.sha256(json.dumps(model, sort_keys=True).encode()).hexdigest()
    assert receipt['model_payload_sha256_before'] == receipt['model_payload_sha256_after'] == payload
    assessment = reference_assess(public, oracle, predictions)
    assert assessment == read(RUN + '/assessment.json')
    report = {'experiment_id': cfg['experiment_id'], 'engineering_integrity_passed': True, 'mapping_unchanged': True,
              **{k: assessment[k] for k in ['site_inventory', 'by_relation_world', 'all_worlds', 'identifiability_demonstration', 'unequal_swap_forced_safety_hypothesis']},
              'symbolic_aligner_and_audit_executed': True, 'external_or_neural_model_executed': False,
              'scientific_acceptance': None, 'semantic_evaluation_metrics': None, 'semantic_labels_admitted': 0,
              'source_identities_admitted': 0, 'independent_reviews_admitted': 0, 'untouched_test_units_admitted': 0,
              'natural_targets_rescored': 0, 'prior_retrieval_decisions_changed': 0, 'new_network_requests': 0,
              'symbol_compatibility_is_independent_accuracy': False}
    assert report == read(RUN + '/report.json')
    preserved = []
    for p in sorted((ROOT / 'runs').glob('*/manifest.json')):
        if p.parent != ROOT / RUN: check_hashes(p.parent); preserved.append(p.parent.name)
    assert len(preserved) == 33
    for p in (ROOT / 'reports').glob('*_deliverable_seal.json'):
        for n, h in json.loads(p.read_text()).get('deliverable_hashes', {}).items(): assert sha(n) == h, n
    verified = {'state': 'verified', 'run_manifest_sha256': sha(RUN + '/manifest.json'),
                'independent_fixture_reconstruction': True, 'independent_lcs_mandatory_edge_replay': True,
                'engineering_integrity_passed': True, 'site_inventory': assessment['site_inventory'],
                'identifiability_demonstration_passed': assessment['identifiability_demonstration']['passed'],
                'unequal_swap_forced_safety_hypothesis_passed': assessment['unequal_swap_forced_safety_hypothesis']['passed'],
                'prior_runs_preserved': preserved, 'semantic_labels_admitted': 0, 'scientific_acceptance': None}
    target = ROOT / 'reports/000034_verification.json'
    if target.exists(): assert {k: v for k, v in json.loads(target.read_text()).items() if k != 'verified_at_utc'} == verified
    else:
        verified['verified_at_utc'] = datetime.now(timezone.utc).isoformat(); target.write_text(json.dumps(verified, indent=2) + '\n')
    print(json.dumps(verified, indent=2))


if __name__ == '__main__': main()
