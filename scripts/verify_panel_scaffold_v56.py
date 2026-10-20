"""Reconstruct masks, anchors and all capped windows using full-table numeric LCS."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from verify_correspondence_v6 import check_hashes
from verify_cohort_scope_v52 import reconstruct as scope_replay
from verify_scaffold_v46 import extract, lcs_dp, union


def read(p): return json.loads((ROOT / p).read_text())
def sha(p): return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()


def score(left, right):
    a = [r['key'] for r in left if r['kind'] == 'number']; b = [r['key'] for r in right if r['kind'] == 'number']
    ca, cb = Counter(a), Counter(b)
    return {'target_count': len(a), 'source_count': len(b), 'shared_distinct': len(set(a) & set(b)),
            'bag_capacity': sum(min(ca[k], cb[k]) for k in ca.keys() & cb.keys()), 'ordered_lcs': lcs_dp(a, b)}


def scan(left, right, budget):
    numeric = [r for r in right if r['kind'] == 'number']; n = len(numeric); width = min(n, budget)
    windows = []
    for start in range(n - width + 1):
        selected = numeric[start:start + width]
        windows.append({'numeric_span': [start, start + width], 'anchor_indices': [r['anchor_index'] for r in selected], 'scores': score(left, selected)})
    maximum = max(w['scores']['ordered_lcs'] for w in windows)
    return {'numeric_anchor_count': n, 'numeric_budget': budget, 'capped_width': width, 'window_count': len(windows),
        'windows': windows, 'maximum_lcs': maximum, 'maximizing_starts': [w['numeric_span'][0] for w in windows if w['scores']['ordered_lcs'] == maximum]}


def inventory(text, units, masks):
    rows, excluded = extract(text, units, masks)
    return {'anchors': rows, 'excluded_boundary_candidates': sorted(excluded, key=lambda r: (r['kind'] != 'number', r['span']))}


def quote_spans(text):
    curly = []; opening = None; good = True
    for at, char in enumerate(text):
        if char == '“':
            if opening is not None: good = False
            opening = at
        if char == '”':
            if opening is None: good = False
            else: curly.append([opening, at + 1]); opening = None
    if opening is not None: good = False
    positions = [i for i, char in enumerate(text) if char == '"']
    if len(positions) % 2: good = False
    if not good: return None
    return curly + [[a, b + 1] for a, b in zip(positions[::2], positions[1::2])]


def representation(scope):
    units = []; ledger = []; unsupported = []; body = scope['body_text']
    for i, run in enumerate(scope['paragraph_runs']):
        a, b = run['body_span']; assert run['unit'] == i and run['text'] == body[a:b] and a < b
        assert not units or a >= units[-1]['span'][1]
        units.append({'unit': i, 'span': [a, b], 'text': run['text']})
        spans = quote_spans(run['text'])
        if spans is None: unsupported.append(i); continue
        for x, y in spans: ledger.append({'unit': i, 'span': [a + x, a + y], 'reason': 'publisher_quoted_speech'})
    masks = union([r['span'] for r in ledger]); available = bool(units) and not unsupported
    return {'available': available, 'units': units, 'quote_mask_ledger': ledger, 'quote_masks': masks,
            'unsupported_quote_units': unsupported, 'inventory': inventory(body, units, masks) if available else None}


def assessment(left, rep, cfg):
    right = rep['inventory']['anchors']; n = len(right); ucount = len(rep['units']); ids = list(range(n))
    groups = [[r['anchor_index'] for r in right if r['unit'] == u] for u in range(ucount)]
    def perm(count, family, draw):
        return sorted(range(count), key=lambda i: (hashlib.sha256(f"{cfg['seed']}|{family}|{draw}|{i}".encode()).digest(), i))
    orders = [('reverse', None, ids[::-1], None),
              ('within_paragraph_reverse', None, [i for group in groups for i in group[::-1]], list(range(ucount)))]
    for draw in range(16):
        orders.append(('anchor_shuffle', draw, perm(n, 'anchor_shuffle', draw), None))
        blocks = perm(ucount, 'paragraph_shuffle', draw)
        orders.append(('paragraph_shuffle', draw, [i for u in blocks for i in groups[u]], blocks))
    cases = []; bag = Counter(r['key'] for r in right)
    for family, draw, order, units in orders:
        rows = [right[i] for i in order]
        cases.append({'family': family, 'draw': draw, 'anchor_order': order, 'unit_order': units,
            'index_identity': order == ids, 'key_identity': [r['key'] for r in rows] == [r['key'] for r in right],
            'index_inventory_preserved': sorted(order) == ids, 'bag_preserved': Counter(r['key'] for r in rows) == bag,
            'whole': score(left, rows), 'capped_scan': scan(left, rows, cfg['numeric_budget'])})
    observed = {'whole': score(left, right), 'capped_scan': scan(left, right, cfg['numeric_budget'])}
    selfcopy = {k: score(rows, rows) for k, rows in [('target', left), ('source', right)]}
    self_ok = all(s['ordered_lcs'] == s['target_count'] == s['source_count'] == s['bag_capacity'] for s in selfcopy.values())
    no_leak = all(not (r['span'][0] < b and r['span'][1] > a) for r in right for a, b in rep['quote_masks'])
    scans = [observed['capped_scan']] + [c['capped_scan'] for c in cases]
    bounds = all(w['scores']['ordered_lcs'] <= w['scores']['bag_capacity'] <= min(w['scores']['target_count'], w['scores']['source_count']) for v in scans for w in v['windows'])
    functional = self_ok and no_leak and bounds and all(c['index_inventory_preserved'] and c['bag_preserved'] for c in cases)
    maxima = {f: max(c['capped_scan']['maximum_lcs'] for c in cases if c['family'] == f) for f in cfg['control_families']}
    value = observed['capped_scan']['maximum_lcs']; eligible = functional and observed['whole']['shared_distinct'] >= 3
    return {'observed': observed, 'controls': cases, 'selfcopy_numeric': selfcopy, 'no_source_quote_mask_leakage': no_leak,
        'functional_checks_passed': functional, 'numeric_family_maxima': maxima, 'within_page_order_eligible': eligible,
        'within_page_order_separated': all(value > maximum for maximum in maxima.values()) if eligible else None,
        'control_ties': sum(c['capped_scan']['maximum_lcs'] == value for c in cases),
        'controls_greater': sum(c['capped_scan']['maximum_lcs'] > value for c in cases),
        'index_identity_controls': sum(c['index_identity'] for c in cases), 'key_identity_controls': sum(c['key_identity'] for c in cases)}


def main():
    run = ROOT / 'runs/000056_panel_scaffold'; check_hashes(run)
    cfg = read('experiments/panel_scaffold_v56.json'); pre = read('data/v56/preflight.json')
    manifest = read('runs/000056_panel_scaffold/manifest.json'); report = read('runs/000056_panel_scaffold/report.json')
    for p, h in pre['hashes'].items(): assert sha(p) == h, p
    for p, h in cfg['input_hashes'].items(): assert pre['hashes'][p] == h
    assert pre['hashes']['experiments/panel_scaffold_v56.json'] == sha('experiments/panel_scaffold_v56.json')
    assert cfg['registered_at_utc'] < pre['sealed_at_utc'] < manifest['finished_at_utc'] and cfg['network_request_budget'] == 0
    assert cfg['numeric_budget'] == 11 and cfg['draws_per_shuffle_family'] == 16 and cfg['minimum_shared_numeric_types'] == 3
    baseline = read('experiments/scaffold_v46.json')
    for k in ['seed', 'control_families', 'bibliography_marker', 'bibliography_start']: assert cfg[k] == baseline[k]
    assert cfg['source_selector'] == read('experiments/offline_intake_v54.json')['source_selector']
    assert [p['id'] for p in cfg['pages']] == ['reference_v42', 'v50_q01s00', 'v50_q01s01', 'v55_q00s00', 'v55_q01s00']
    assert read('runs/000055_additional_intake/report.json')['cumulative_eligible_ids'] == ['v50:q01s00', 'v50:q01s01', 'v55:q00s00', 'v55:q01s00']
    target = read('data/v38/target_export.json')['text']; queries = read('data/v39/frozen_queries.json')['queries']
    assert len(queries) == 8
    for q in queries: assert target[slice(*q['span'])] == q['text']
    assert target.count(cfg['bibliography_marker']) == 1 and target.index(cfg['bibliography_marker']) == 7332
    ledger = [{'reason': 'title_header', 'span': [0, queries[0]['span'][0]]}]
    ledger += [{'reason': q['quote_id'], 'span': q['span']} for q in queries]
    ledger += [{'reason': 'bibliography', 'span': [7332, len(target)]}]
    masks = union([r['span'] for r in ledger]); complement = []; cursor = 0
    for a, b in masks:
        if cursor < a: complement.append([cursor, a])
        cursor = b
    if cursor < len(target): complement.append([cursor, len(target)])
    units = [{'unit': i, 'span': s} for i, s in enumerate(complement)]
    target_inv = inventory(target, units, masks)
    assert read('data/v56/target.json') == {'mask_ledger': ledger, 'masks': masks, 'units': units, 'inventory': target_inv}
    old_scope = read('data/v46/scope.json'); old_inv = read('data/v46/inventory.json'); old_assessment = read('data/v46/assessment.json')
    assert ledger == old_scope['target_mask_ledger'] and masks == old_scope['target_masks'] and units == old_scope['target_units']
    assert target_inv == old_inv['target']; left = target_inv['anchors']; assessments = []; summaries = []; window_total = 0
    for spec in cfg['pages']:
        saved = read(spec['scope']); raw = (ROOT / spec['raw']).read_bytes(); receipt = read(spec['receipt'])
        assert sha(spec['raw']) == receipt['artifacts']['body.bin']['sha256'] and len(raw) == receipt['artifacts']['body.bin']['bytes']
        scope, checks = scope_replay(raw, saved['body_text'], cfg['source_selector']); assert scope == saved and all(checks.values())
        rep = representation(scope); assert rep == read(f"data/v56/{spec['id']}_representation.json")
        if rep['available']:
            for row in rep['inventory']['anchors']: assert scope['body_text'][slice(*row['span'])] == row['value']
        result = assessment(left, rep, cfg) if rep['available'] else None
        assert result == read(f"data/v56/{spec['id']}_assessment.json"); assessments.append(result)
        if result: window_total += result['observed']['capped_scan']['window_count'] + sum(c['capped_scan']['window_count'] for c in result['controls'])
        if spec['id'] == 'reference_v42':
            assert rep['units'] == old_scope['source_units'] and rep['quote_mask_ledger'] == old_scope['source_mask_ledger'] and rep['quote_masks'] == old_scope['source_masks']
            assert rep['inventory'] == old_inv['source'] and result['observed']['whole'] == old_assessment['observed']['number']
            assert result['observed']['whole']['source_count'] == 11
            for current, old in zip(result['controls'], old_assessment['controls'], strict=True):
                for k in ['family', 'draw', 'anchor_order', 'unit_order', 'index_identity', 'key_identity', 'bag_preserved', 'index_inventory_preserved']: assert current[k] == old[k]
                assert current['whole'] == old['scores']['number'] and current['capped_scan']['maximum_lcs'] == current['whole']['ordered_lcs']
        summaries.append({'id': spec['id'], 'url': spec['url'], 'available': rep['available'], 'paragraph_runs': len(rep['units']),
            'paragraph_run_characters': sum(len(u['text']) for u in rep['units']), 'source_quote_masks': len(rep['quote_mask_ledger']),
            'unsupported_quote_units': rep['unsupported_quote_units'], 'quote_mask_characters': sum(b - a for a, b in rep['quote_masks']),
            'whole': result['observed']['whole'] if result else None,
            'capped_numeric_width': result['observed']['capped_scan']['capped_width'] if result else None,
            'observed_window_count': result['observed']['capped_scan']['window_count'] if result else None,
            'maximum_capped_lcs': result['observed']['capped_scan']['maximum_lcs'] if result else None,
            'maximizing_starts': result['observed']['capped_scan']['maximizing_starts'] if result else None,
            'control_denominator': len(result['controls']) if result else 0,
            **({k: result[k] for k in ['functional_checks_passed', 'numeric_family_maxima', 'within_page_order_eligible',
                'within_page_order_separated', 'control_ties', 'controls_greater', 'index_identity_controls', 'key_identity_controls']} if result else {})})
    assert report['pages'] == summaries and report['page_denominator'] == len(summaries) == 5 and report['comparator_denominator'] == cfg['comparator_denominator'] == 4
    eligible = all(a is not None and a['functional_checks_passed'] for a in assessments) and assessments[0]['observed']['whole']['shared_distinct'] >= 3
    primary = all(assessments[0]['observed']['capped_scan']['maximum_lcs'] > a['observed']['capped_scan']['maximum_lcs'] for a in assessments[1:]) if eligible else None
    whole = all(assessments[0]['observed']['whole']['ordered_lcs'] > a['observed']['whole']['ordered_lcs'] for a in assessments[1:]) if eligible else None
    assert report['panel_comparison_eligible'] == eligible and report['registered_capped_specificity_gate'] == primary and report['whole_page_specificity_diagnostic'] == whole
    assert report['reference_e46_continuity_verified'] is True and report['target_numeric_count'] == 10 and report['target_residual_units'] == 8
    assert report['numeric_budget'] == 11 and report['controls_per_available_page'] == 34 and report['registered_control_budget'] == 170
    controls_total = sum(len(a['controls']) for a in assessments if a is not None)
    assert report['controls_evaluated'] == controls_total and report['all_observed_and_control_windows_evaluated'] == window_total
    for k in ['network_requests', 'new_acquisitions', 'opaque_lexical_or_semantic_scores', 'source_identities_admitted', 'independent_reviews_admitted', 'untouched_test_units_admitted']: assert report[k] == 0
    assert report['natural_benchmark_capacity_met'] is False and report['scientific_acceptance'] is report['semantic_evaluation_metrics'] is None
    previous = []
    for path in sorted((ROOT / 'runs').glob('000*/manifest.json')):
        if path.parent != run: check_hashes(path.parent); previous.append(path.parent.name)
    assert len(previous) == 55
    for seal in (ROOT / 'reports').glob('*_deliverable_seal.json'):
        for p, h in json.loads(seal.read_text()).get('deliverable_hashes', {}).items(): assert sha(p) == h, p
    verification = {'state': 'verified', 'manifest_sha256': sha('runs/000056_panel_scaffold/manifest.json'),
        'five_original_scopes_masks_and_every_anchor_reconstructed': True, 'controls_verified': controls_total,
        'observed_and_control_windows_full_table_dp_verified': window_total, 'reference_e46_continuity_verified': True,
        'registered_capped_specificity_gate': primary, 'whole_page_specificity_diagnostic': whole,
        'production_representation_assessment_and_lcs_not_used': True, 'shared_html_parser': 'BeautifulSoup html.parser',
        'verification_network_requests': 0, 'independent_scientific_review': False,
        'semantics_or_source_identity_validated': False, 'prior_runs_preserved': previous}
    out = ROOT / 'reports/000056_verification.json'
    if out.exists(): assert {k: v for k, v in json.loads(out.read_text()).items() if k != 'verified_at_utc'} == verification
    else:
        with out.open('x') as stream: json.dump(verification | {'verified_at_utc': datetime.now(timezone.utc).isoformat()}, stream, indent=2); stream.write('\n')
    print(json.dumps({k: v for k, v in verification.items() if k != 'prior_runs_preserved'} | {'prior_runs_preserved': len(previous)}, indent=2))


if __name__ == '__main__': main()
