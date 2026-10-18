"""Fresh registered fixtures and readouts; the v32/v35 model is imported unchanged."""
from collections import Counter, defaultdict
from copy import deepcopy
import hashlib
import json

from fl_decipher.synthetic_transfer_v32 import alias, view, decode
from fl_decipher.adjacent_transposition_v35 import predict

NAMESPACE = 'v36|fresh-context-20261018'
PROFILES = {
    'identity': ([], [], [], []),
    'light': ([6, 26], [10, 30], [12, 40], [15, 45]),
    'moderate': ([6, 26, 46, 66], [10, 30, 50, 62], [8, 20, 40, 58], [15, 31, 47, 63]),
    'dense_unknown': ([6, 14, 26, 34, 46, 54, 66, 70], [2, 10, 22, 30, 42, 50, 60, 64],
                      [8, 20, 40, 58], [3, 11, 19, 27, 39, 43, 55, 67]),
    'block_mismatch': ([6, 26, 46, 66], [10, 30, 50, 62], [8, 20, 40, 58], [15, 31, 47, 63]),
}


def digest(text):
    return hashlib.sha256(text.encode()).hexdigest()


def payload_hash(value):
    return digest(json.dumps(value, sort_keys=True, separators=(',', ':')))


def context(key, passage, kind='parent'):
    return [f'copiedanchor{[17, 35, 53].index(i)}' if i in (17, 35, 53)
            else f'symbol{int(digest(f"{NAMESPACE}|{kind}|{key}|{passage}|{i}"), 16) % 24}'
            for i in range(72)]


def candidates(source, key, passage):
    sibling = source.copy()
    pair = next(((i, j) for i, j in [(1, 61), (2, 62), (3, 63), (4, 64)] if source[i] != source[j]), None)
    if pair:
        i, j = pair
        sibling[i], sibling[j] = sibling[j], sibling[i]
    substitutions = source.copy()
    for i in [1, 9, 21, 29, 41, 49, 61, 69]:
        substitutions[i] = f'symbol{(int(source[i][6:]) + 1) % 24}'
    positions = [i for i in range(72) if i not in (17, 35, 53)]
    shuffled = source.copy()
    order = sorted(positions, key=lambda i: (digest(f'{NAMESPACE}|shuffle|{key}|{passage}|{i}'), i))
    for i, j in zip(positions, order, strict=True):
        shuffled[i] = source[j]
    return {'parent': source, 'near_swap': sibling, 'near_substitution': substitutions,
            'histogram_shuffle': shuffled, 'unrelated': context(key, passage, 'unrelated')}, pair


def query(source, key, passage, profile):
    deletions, unknowns, swaps, insertions = PROFILES[profile]
    order = list(range(len(source)))
    for i in swaps:
        order[i], order[i+1] = order[i+1], order[i]
    if profile == 'block_mismatch':
        order[38:46] = order[38:46][::-1]
    order = [i for i in order if i not in deletions]
    forms, origins = [], []
    for i in order:
        form = source[i]
        forms.append(form if form.startswith('copiedanchor') else alias(key, int(form[6:]), int(i in unknowns)))
        origins.append(i)
        if i in insertions:
            forms.append(f'v36insertk{key}p{passage}{profile.replace("_", "")}at{i}')
            origins.append(None)
    affected = set(unknowns) | {j for i in swaps for j in (i, i+1)}
    if profile == 'block_mismatch':
        affected.update(range(38, 46))
    return forms, {'origins': origins, 'deleted_indices': deletions, 'unknown_origins': unknowns,
                   'swap_left_indices': swaps, 'insertion_after_origins': insertions,
                   'affected_origins': sorted(affected), 'block_reversal': profile == 'block_mismatch'}


def model_variants(model, keys):
    variants = {name: deepcopy(model) for name in ('clean', 'sparse', 'dense')}
    changes = {}
    for name, classes in [('sparse', range(2)), ('dense', range(8))]:
        rows = []
        for key in keys:
            for symbol in classes:
                form = alias(key, symbol)
                before = variants[name]['entries'][form]['source_form']
                after = f'symbol{(symbol+1) % len(classes)}'
                variants[name]['entries'][form]['source_form'] = after
                rows.append({'alias': form, 'before': before, 'after': after})
        changes[name] = rows
    assert variants['clean'] == model
    return variants, changes


def prepare(cfg, model):
    observations, panels, gold_queries, gold_panels, bases = {}, [], [], [], []
    for key in cfg['keys']:
        for passage in cfg['passages']:
            source = context(key, passage)
            sources, pair = candidates(source, key, passage)
            bases.append({'key': key, 'passage': passage, 'source': source,
                          'candidate_forms': sources, 'near_swap_indices': pair,
                          'near_swap_byte_collision': pair is None})
            for profile in cfg['profiles']:
                qid = f'k{key}p{passage}{profile}'
                forms, edits = query(source, key, passage, profile)
                ids = {}
                for role, sf in sources.items():
                    obs = {'source': view(sf), 'query': view(forms)}
                    oid = 'observation' + payload_hash(obs)
                    assert oid not in observations or observations[oid] == obs
                    observations[oid] = obs
                    ids[role] = oid
                decoded = decode(view(forms), model)
                recoverable = [i for i, (origin, row) in enumerate(zip(edits['origins'], decoded, strict=True))
                               if origin is not None and row['source_form'] is not None]
                counts = Counter(source)
                singleton = [i for i in recoverable if counts[source[edits['origins'][i]]] == 1]
                affected = [i for i in recoverable if edits['origins'][i] in edits['affected_origins']]
                gold_queries.append({'query_id': qid, 'key': key, 'passage': passage, 'profile': profile,
                                     'observation_ids': ids, **edits, 'recoverable_positions': recoverable,
                                     'singleton_symbol_positions': singleton,
                                     'repeated_symbol_positions': sorted(set(recoverable)-set(singleton)),
                                     'affected_known_positions': affected})
                for scenario in ('present', 'absent', 'duplicate'):
                    roles = list(sources) if scenario != 'absent' else [r for r in sources if r != 'parent']
                    if scenario == 'duplicate':
                        roles.append('parent_copy')
                    roles.sort(key=lambda role: (digest(f'{qid}|{scenario}|{role}'), role))
                    members = [{'slot_id': f'slot{i}', 'observation_id': ids['parent' if role == 'parent_copy' else role]}
                               for i, role in enumerate(roles)]
                    pid = 'panel' + payload_hash(members)
                    panels.append({'panel_id': pid, 'candidates': members})
                    gold_panels.append({'panel_id': pid, 'query_id': qid, 'profile': profile, 'scenario': scenario,
                                        'slot_roles': dict(zip((m['slot_id'] for m in members), roles, strict=True))})
    variants, changes = model_variants(model, cfg['keys'])
    return {'observations': observations, 'panels': panels}, {'bases': bases, 'queries': gold_queries, 'panels': gold_panels}, {
        'models': variants, 'injected_changes': changes, 'original_mapping_payload_sha256': payload_hash(model)}


def metrics(pairs, gold, source, positions):
    positions = set(positions)
    selected = [(qi, si) for qi, si in pairs if qi in positions]
    exact = sum(gold[qi] is not None and gold[qi] == si for qi, si in selected)
    compatible = sum(gold[qi] is not None and source[gold[qi]] == source[si] for qi, si in selected)
    return {'denominator': len(positions), 'returned': len(selected), 'origin_exact': exact,
            'origin_wrong': len(selected)-exact, 'true_symbol_compatible': compatible,
            'true_symbol_wrong': len(selected)-compatible, 'unmatched': len(positions)-len(selected)}


def assess(public, oracle, outputs):
    rows, panels = [], []
    by_qid = {q['query_id']: q for q in oracle['queries']}
    groups = {}
    for branch, output in outputs.items():
        for gold in oracle['queries']:
            oid = gold['observation_ids']['parent']
            obs = public['observations'][oid]
            pred = output['predictions'][oid]
            source = [t['form'] for t in obs['source']['tokens']]
            n = len(obs['query']['tokens'])
            strata = {'all_query_tokens': list(range(n)), 'recoverable': gold['recoverable_positions'],
                      'affected_known': gold['affected_known_positions'], 'singleton_symbol': gold['singleton_symbol_positions'],
                      'repeated_symbol': gold['repeated_symbol_positions']}
            scored = {policy: {scope: metrics(pred['ambiguity'][field], gold['origins'], source, positions)
                              for scope, positions in strata.items()}
                      for policy, field in [('representative', 'representative_matches'), ('forced', 'forced_matches')]}
            row = {'branch': branch, 'query_id': gold['query_id'], 'profile': gold['profile'],
                   'source_tokens': len(source), 'query_tokens': n, 'qualifies': pred['alignment']['qualifies'],
                   'metrics': scored}
            rows.append(row)
            for group_name in (gold['profile'], 'ALL', 'PRIMARY' if gold['profile'] in ('light', 'moderate') else None):
                if group_name is None:
                    continue
                g = groups.setdefault((branch, group_name), {'branch': branch, 'profile': group_name, 'queries': 0,
                                                            'source_tokens': 0, 'query_tokens': 0, 'qualified_parent_pairs': 0,
                                                            'metrics': {p: {s: {k: 0 for k in v} for s, v in scopes.items()}
                                                                        for p, scopes in scored.items()}})
                g['queries'] += 1
                g['source_tokens'] += len(source)
                g['query_tokens'] += n
                g['qualified_parent_pairs'] += pred['alignment']['qualifies']
                for policy, scopes in scored.items():
                    for scope, metric in scopes.items():
                        for k, v in metric.items():
                            g['metrics'][policy][scope][k] += v
        by_pid = {p['panel_id']: p for p in output['panels']}
        for gold in oracle['panels']:
            decision = by_pid[gold['panel_id']]['decision']
            nomination = decision['nominated']
            role = gold['slot_roles'].get(nomination)
            panels.append({'branch': branch, 'query_id': gold['query_id'], 'profile': gold['profile'],
                           'scenario': gold['scenario'], 'panel_id': gold['panel_id'], 'decision': decision,
                           'nominated_role': role, 'abstained': nomination is None,
                           'correct_parent': role == 'parent', 'nonparent_nomination': role not in (None, 'parent', 'parent_copy')})
    primary = [p for p in panels if p['branch'] == 'clean' and p['profile'] in ('light', 'moderate')]
    forced = groups[('clean', 'PRIMARY')]['metrics']['forced']['recoverable']
    checks = {
        'primary_present_32_of_32': sum(p['correct_parent'] for p in primary if p['scenario'] == 'present') == 32,
        'primary_absent_zero_of_32_nominations': sum(not p['abstained'] for p in primary if p['scenario'] == 'absent') == 0,
        'primary_duplicate_32_of_32_abstentions': sum(p['abstained'] for p in primary if p['scenario'] == 'duplicate') == 32,
        'forced_origin_precision_at_least_99_percent': forced['returned'] > 0 and 100*forced['origin_exact'] >= 99*forced['returned'],
        'forced_recoverable_coverage_at_least_90_percent': forced['denominator'] > 0 and 10*forced['returned'] >= 9*forced['denominator'],
    }
    summaries = []
    for (branch, profile), g in groups.items():
        selected = [p for p in panels if p['branch'] == branch and (profile == 'ALL' or
                    profile == 'PRIMARY' and p['profile'] in ('light', 'moderate') or p['profile'] == profile)]
        g['panel_summary'] = {scenario: {'panels': sum(p['scenario'] == scenario for p in selected),
                                       'parent_nominations': sum(p['correct_parent'] for p in selected if p['scenario'] == scenario),
                                       'nonparent_nominations': sum(p['nonparent_nomination'] for p in selected if p['scenario'] == scenario),
                                       'abstentions': sum(p['abstained'] for p in selected if p['scenario'] == scenario)}
                              for scenario in ('present', 'absent', 'duplicate')}
        summaries.append(g)
    return {'query_rows': rows, 'panel_rows': panels, 'summaries': summaries,
            'synthetic_transfer_gate': {'checks': checks, 'passed': all(checks.values())},
            'full_token_denominator_per_branch': sum(len(public['observations'][q['observation_ids']['parent']]['query']['tokens']) for q in by_qid.values())}
