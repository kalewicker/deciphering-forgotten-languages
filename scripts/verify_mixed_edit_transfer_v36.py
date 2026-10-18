"""Read-only independent v35 DAG replay, fixture/accounting and evidence audit."""
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from verify_adjacent_transposition_v35 import reference_predict
from verify_positional_worlds_v34 import reference_view
from verify_correspondence_v6 import check_hashes

RUN = 'runs/000036_mixed_edit_transfer'


def read(path):
    return json.loads((ROOT/path).read_text())


def sha(path):
    return hashlib.sha256((ROOT/path).read_bytes()).hexdigest()


def h(text):
    return hashlib.sha256(text.encode()).hexdigest()


def payload_hash(v):
    return h(json.dumps(v, sort_keys=True, separators=(',', ':')))


def check_generator(public, gold, variants, cfg):
    model = read('data/v32/frozen_mapping.json')['model']
    assert variants['models']['clean'] == model
    assert variants['original_mapping_payload_sha256'] == payload_hash(model)
    def alias(key, symbol, parity=0):
        return 'aliascode'+h(f'v32|alias|{key}|{symbol}|{parity}')[:20]
    for name, size in [('sparse', 2), ('dense', 8)]:
        expected = json.loads(json.dumps(model))
        changes = []
        for key in cfg['keys']:
            for symbol in range(size):
                form = alias(key, symbol)
                before = expected['entries'][form]['source_form']
                after = f'symbol{(symbol+1)%size}'
                expected['entries'][form]['source_form'] = after
                changes.append({'alias': form, 'before': before, 'after': after})
        assert variants['models'][name] == expected and variants['injected_changes'][name] == changes
    assert len(gold['bases']) == 16 and len(gold['queries']) == 80 and len(gold['panels']) == 240
    base_by_id = {}
    namespace = cfg['seed_namespace']
    def source_for(key, passage, role):
        forms = [f'symbol{int(h(f"{namespace}|{role}|{key}|{passage}|{i}"),16)%24}' for i in range(72)]
        for pos, label in [(17, 0), (35, 1), (53, 2)]:
            forms[pos] = f'copiedanchor{label}'
        return forms
    for base in gold['bases']:
        key, passage = base['key'], base['passage']
        source = source_for(key, passage, 'parent')
        assert base['source'] == source
        candidates = base['candidate_forms']
        assert candidates['parent'] == source and candidates['unrelated'] == source_for(key, passage, 'unrelated')
        pair = next(([i, j] for i, j in [(1, 61), (2, 62), (3, 63), (4, 64)] if source[i] != source[j]), None)
        assert base['near_swap_indices'] == pair and base['near_swap_byte_collision'] == (pair is None)
        sibling = source.copy()
        if pair:
            i, j = pair
            sibling[i], sibling[j] = sibling[j], sibling[i]
        assert candidates['near_swap'] == sibling
        substituted = [f'symbol{(int(f[6:])+1)%24}' if i in (1,9,21,29,41,49,61,69) else f for i, f in enumerate(source)]
        assert candidates['near_substitution'] == substituted
        positions = [i for i in range(72) if i not in (17,35,53)]
        order = sorted(positions, key=lambda i: (h(f'{namespace}|shuffle|{key}|{passage}|{i}'), i))
        shuffled = source.copy()
        for at, origin in zip(positions, order, strict=True):
            shuffled[at] = source[origin]
        assert candidates['histogram_shuffle'] == shuffled
        assert Counter(source) == Counter(sibling) == Counter(shuffled)
        base_by_id[(key, passage)] = base
    schedules = {
        'identity': ([], [], [], []),
        'light': ([6,26], [10,30], [12,40], [15,45]),
        'moderate': ([6,26,46,66], [10,30,50,62], [8,20,40,58], [15,31,47,63]),
        'dense_unknown': ([6,14,26,34,46,54,66,70], [2,10,22,30,42,50,60,64], [8,20,40,58], [3,11,19,27,39,43,55,67]),
        'block_mismatch': ([6,26,46,66], [10,30,50,62], [8,20,40,58], [15,31,47,63])}
    seen = set()
    for q in gold['queries']:
        key, passage, profile = q['key'], q['passage'], q['profile']
        assert q['query_id'] == f'k{key}p{passage}{profile}'
        base = base_by_id[(key, passage)]
        source = base['source']
        deleted, unknown, swaps, inserted = schedules[profile]
        assert (q['deleted_indices'], q['unknown_origins'], q['swap_left_indices'], q['insertion_after_origins']) == (deleted, unknown, swaps, inserted)
        permutation = list(range(72))
        for at in swaps:
            permutation[at:at+2] = permutation[at:at+2][::-1]
        if profile == 'block_mismatch':
            permutation[38:46] = permutation[38:46][::-1]
        origins, forms = [], []
        for origin in permutation:
            if origin in deleted:
                continue
            f = source[origin]
            origins.append(origin)
            forms.append(f if f.startswith('copiedanchor') else alias(key, int(f[6:]), int(origin in unknown)))
            if origin in inserted:
                origins.append(None)
                forms.append(f'v36insertk{key}p{passage}{profile.replace("_", "")}at{origin}')
        assert q['origins'] == origins and len(origins) == len(forms) == 72
        affected_origins = set(unknown) | {j for at in swaps for j in (at,at+1)}
        if profile == 'block_mismatch':
            affected_origins.update(range(38,46))
        assert q['affected_origins'] == sorted(affected_origins) and q['block_reversal'] == (profile == 'block_mismatch')
        recoverable = [i for i, o in enumerate(origins) if o is not None and not source[o].startswith('copiedanchor') and o not in unknown]
        assert q['recoverable_positions'] == recoverable
        assert q['singleton_symbol_positions'] == [i for i in recoverable if source.count(source[origins[i]]) == 1]
        assert q['repeated_symbol_positions'] == [i for i in recoverable if source.count(source[origins[i]]) != 1]
        assert q['affected_known_positions'] == [i for i in recoverable if origins[i] in affected_origins]
        for role, oid in q['observation_ids'].items():
            obs = {'source': reference_view(base['candidate_forms'][role]), 'query': reference_view(forms)}
            assert public['observations'][oid] == obs and oid == 'observation'+payload_hash(obs)
            seen.add(oid)
    assert seen == set(public['observations']) and len(seen) <= 400
    assert sum(len(q['observation_ids']) for q in gold['queries']) == 400
    query_map = {q['query_id']: q for q in gold['queries']}
    panel_map = {p['panel_id']: p for p in public['panels']}
    assert len(panel_map) == len(gold['panels']) == 240
    for panel in gold['panels']:
        q = query_map[panel['query_id']]
        scenario = panel['scenario']
        roles = list(q['observation_ids'])
        if scenario == 'absent':
            roles.remove('parent')
        if scenario == 'duplicate':
            roles.append('parent_copy')
        roles.sort(key=lambda role: (h(f'{q["query_id"]}|{scenario}|{role}'), role))
        members = [{'slot_id': f'slot{i}', 'observation_id': q['observation_ids']['parent' if role == 'parent_copy' else role]}
                   for i, role in enumerate(roles)]
        assert panel['profile'] == q['profile'] and panel['slot_roles'] == {f'slot{i}': role for i, role in enumerate(roles)}
        assert panel_map[panel['panel_id']]['candidates'] == members
        assert panel['panel_id'] == 'panel'+payload_hash(members)


def independent_metrics(pairs, origins, forms, positions):
    selected = [(qi, si) for qi, si in pairs if qi in positions]
    correct = [(qi, si) for qi, si in selected if origins[qi] == si]
    same = [(qi, si) for qi, si in selected if origins[qi] is not None and forms[origins[qi]] == forms[si]]
    return dict(denominator=len(positions), returned=len(selected), origin_exact=len(correct), origin_wrong=len(selected)-len(correct),
                true_symbol_compatible=len(same), true_symbol_wrong=len(selected)-len(same), unmatched=len(positions)-len(selected))


def check_assessment(public, gold, predictions, assessment):
    rows = {(r['branch'], r['query_id']): r for r in assessment['query_rows']}
    assert len(rows) == 240
    for branch, pred in predictions.items():
        for q in gold['queries']:
            row = rows[(branch, q['query_id'])]
            oid = q['observation_ids']['parent']
            obs = public['observations'][oid]
            p = pred['predictions'][oid]
            source = [t['form'] for t in obs['source']['tokens']]
            assert row['profile'] == q['profile'] and row['query_tokens'] == 72 and row['source_tokens'] == 72
            assert row['qualifies'] == p['alignment']['qualifies']
            for policy in ('representative', 'forced'):
                pairs = p['ambiguity'][policy+'_matches']
                for scope, positions in [('all_query_tokens', list(range(72))), ('recoverable', q['recoverable_positions']),
                                         ('affected_known', q['affected_known_positions']), ('singleton_symbol', q['singleton_symbol_positions']),
                                         ('repeated_symbol', q['repeated_symbol_positions'])]:
                    assert row['metrics'][policy][scope] == independent_metrics(pairs, q['origins'], source, positions)
    panel_rows = {(r['branch'], r['panel_id']): r for r in assessment['panel_rows']}
    assert len(panel_rows) == 720
    for branch, output in predictions.items():
        by_id = {p['panel_id']: p for p in output['panels']}
        for panel in gold['panels']:
            row = panel_rows[(branch, panel['panel_id'])]
            decision = by_id[panel['panel_id']]['decision']
            role = panel['slot_roles'].get(decision['nominated'])
            assert row == {'branch': branch, 'query_id': panel['query_id'], 'profile': panel['profile'], 'scenario': panel['scenario'],
                           'panel_id': panel['panel_id'], 'decision': decision, 'nominated_role': role,
                           'abstained': decision['nominated'] is None, 'correct_parent': role == 'parent',
                           'nonparent_nomination': role not in (None, 'parent', 'parent_copy')}
    assert len(assessment['summaries']) == 21
    for g in assessment['summaries']:
        def select(row):
            return row['branch'] == g['branch'] and (g['profile'] == 'ALL' or row['profile'] == g['profile'] or
                    g['profile'] == 'PRIMARY' and row['profile'] in ('light','moderate'))
        selected = [r for r in rows.values() if select(r)]
        assert g['queries'] == len(selected) and g['qualified_parent_pairs'] == sum(r['qualifies'] for r in selected)
        assert g['query_tokens'] == g['source_tokens'] == len(selected)*72
        for policy, scopes in g['metrics'].items():
            for scope, metrics in scopes.items():
                for k, v in metrics.items():
                    assert v == sum(r['metrics'][policy][scope][k] for r in selected)
        for scenario, count in g['panel_summary'].items():
            ps = [p for p in panel_rows.values() if select(p) and p['scenario'] == scenario]
            assert count == {'panels': len(ps), 'parent_nominations': sum(p['correct_parent'] for p in ps),
                             'nonparent_nominations': sum(p['nonparent_nomination'] for p in ps), 'abstentions': sum(p['abstained'] for p in ps)}
    clean = next(g for g in assessment['summaries'] if g['branch'] == 'clean' and g['profile'] == 'PRIMARY')
    m = clean['metrics']['forced']['recoverable']
    s = clean['panel_summary']
    expected = {'primary_present_32_of_32': s['present']['parent_nominations'] == 32,
                'primary_absent_zero_of_32_nominations': s['absent']['abstentions'] == 32,
                'primary_duplicate_32_of_32_abstentions': s['duplicate']['abstentions'] == 32,
                'forced_origin_precision_at_least_99_percent': m['returned'] > 0 and 100*m['origin_exact'] >= 99*m['returned'],
                'forced_recoverable_coverage_at_least_90_percent': m['denominator'] > 0 and 10*m['returned'] >= 9*m['denominator']}
    assert assessment['synthetic_transfer_gate'] == {'checks': expected, 'passed': all(expected.values())}
    assert assessment['full_token_denominator_per_branch'] == 80*72


def check_natural_audit(audit):
    articles = read('runs/000015_kamri_dataset_audit/report.json')['articles']
    pending = [set(a['component']) for a in articles]
    changed = True
    while changed:
        changed = False
        for i in range(len(pending)):
            for j in range(i+1, len(pending)):
                if pending[i] & pending[j]:
                    pending[i] |= pending.pop(j)
                    changed = True
                    break
            if changed:
                break
    assert {tuple(sorted(g)) for g in pending} == {tuple(r['connected_components']) for r in audit['connected_group_ledger']}
    assert audit['tracked_article_editions'] == len(articles) == 25
    assert audit['tracked_connected_groups'] == len(pending)
    for row in audit['connected_group_ledger']:
        selected = [a for a in articles if set(a['component']) & set(row['connected_components'])]
        assert row['article_entries'] == [a['entry'] for a in selected]
        assert row['article_titles'] == [a['title'] for a in selected]
        assert row['annotation_units'] == sum(a['units'] for a in selected)
        assert row['exposed'] and not row['eligible_for_untouched_pilot'] and row['independently_reviewed_passage_units_admitted'] == 0
    future = read('runs/000021_kamri_calibration_evidence/future_panel.json')
    counts = Counter(tuple(sorted(u['connected_group'])) for u in future['units'])
    assert audit['development_panel'] == [{'connected_components': list(g), 'units': n} for g, n in sorted(counts.items())]
    assert audit['development_units'] == 19 and audit['development_groups'] == 5
    handoff = read('runs/000025_kamri_review_handoff/report.json')
    assert handoff['independent_reviews_completed'] == 0
    assert audit['dossier_ids'] == [r['nominee_id'] for r in handoff['records']] and audit['full_dated_post_dossiers'] == 2
    assert audit['capacity_requirements'] == read('experiments/mixed_edit_transfer_v36.json')['natural_capacity_rule']
    assert audit['unexposed_reviewed_connected_works_available'] == 0 and not audit['immediate_untouched_benchmark_feasible']
    assert audit['remaining_unexposed_components_in_v14_inventory'] == []
    for key in ['new_network_requests','natural_targets_rescored','source_identities_admitted','semantic_labels_admitted',
                'independent_reviews_admitted','untouched_test_units_admitted']:
        assert audit[key] == 0
    assert audit['scientific_acceptance'] is audit['semantic_evaluation_metrics'] is None


def main():
    manifest = check_hashes(ROOT/RUN)
    pre = read('data/v36/preflight_revision1.json')
    original_pre = read('data/v36/preflight.json')
    for path, expected in original_pre['code_hashes'].items():
        snapshot = 'data/v36/preparation_failure/'+('src_' if path == 'src/fl_decipher/mixed_edit_transfer_v36.py' else '')+Path(path).name
        actual = sha(snapshot) if (ROOT/snapshot).exists() else sha(path)
        assert actual == expected, path
    cfg = read('experiments/mixed_edit_transfer_v36.json')
    prep = read('data/v36/preparation_receipt.json')
    bench = read('benchmarks/mixed_edit_transfer_v36.json')
    receipt = read(RUN+'/prediction_receipt.json')
    assert cfg['registered_at_utc'] < pre['sealed_at_utc'] < prep['prepared_at_utc'] < bench['frozen_at_utc'] < manifest['started_at_utc'] < receipt['all_predictions_frozen_at_utc'] < manifest['finished_at_utc']
    public, gold, variants = read('data/v36/public_observations.json'), read('data/v36/oracle.json'), read('data/v36/model_variants.json')
    check_generator(public, gold, variants, cfg)
    outputs = {}
    for name in cfg['branches']:
        print(f'Independent integer-DAG replay: {name}.', flush=True)
        outputs[name] = read(f'{RUN}/predictions_{name}.json')
        assert outputs[name] == reference_predict(public, variants['models'][name])
        r = receipt['branches'][name]
        assert r['predictions_sha256'] == sha(f'{RUN}/predictions_{name}.json')
        assert r['model_payload_before'] == r['model_payload_after'] == payload_hash(variants['models'][name])
        assert manifest['started_at_utc'] < r['frozen_at_utc'] <= receipt['all_predictions_frozen_at_utc']
    assert receipt['oracle_used_for_prediction'] is False
    assessment = read(RUN+'/assessment.json')
    check_assessment(public, gold, outputs, assessment)
    audit = read(RUN+'/natural_evidence_audit.json')
    check_natural_audit(audit)
    report = read(RUN+'/report.json')
    assert report['synthetic_transfer_gate'] == assessment['synthetic_transfer_gate'] and report['summaries'] == assessment['summaries']
    assert report['full_token_denominator_per_branch'] == 5760 and report['alignments'] == 1200 and report['panel_decisions'] == 720
    assert report['distinct_alignments_computed'] == len(public['observations'])*3
    assert report['synthetic_feature_expansion_stopped'] and not report['immediate_untouched_natural_benchmark_feasible']
    for k in ['new_network_requests','natural_targets_rescored','source_identities_admitted','semantic_labels_admitted',
              'independent_reviews_admitted','untouched_test_units_admitted','unexposed_reviewed_connected_works_available']:
        assert report[k] == 0
    assert report['scientific_acceptance'] is report['semantic_evaluation_metrics'] is None
    prior = []
    for p in sorted((ROOT/'runs').glob('000*/manifest.json')):
        if p.parent != ROOT/RUN:
            check_hashes(p.parent)
            prior.append(p.parent.name)
    assert len(prior) == 35
    for p in (ROOT/'reports').glob('*_deliverable_seal.json'):
        for path, expected in json.loads(p.read_text()).get('deliverable_hashes', {}).items():
            assert sha(path) == expected, path
    verified = {'state': 'verified', 'run_manifest_sha256': sha(RUN+'/manifest.json'), 'alignments_verified': 1200,
                'panel_decisions_verified': 720, 'independent_integer_dag_replay': True, 'independent_generator_invariants': True,
                'independent_metric_accounting': True, 'natural_inventory_reconstructed': True,
                'synthetic_transfer_gate_passed': assessment['synthetic_transfer_gate']['passed'], 'prior_runs_preserved': prior,
                'natural_scientific_acceptance': None, 'semantic_labels_admitted': 0}
    path = ROOT/'reports/000036_verification.json'
    if path.exists():
        assert {k: v for k, v in json.loads(path.read_text()).items() if k != 'verified_at_utc'} == verified
    else:
        with path.open('x') as f:
            json.dump(verified | {'verified_at_utc': datetime.now(timezone.utc).isoformat()}, f, indent=2)
            f.write('\n')
    print(json.dumps(verified, indent=2))


if __name__ == '__main__':
    main()
