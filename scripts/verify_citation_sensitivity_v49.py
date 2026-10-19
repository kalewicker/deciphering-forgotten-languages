"""Rebuild masks with a character grammar; verify filtered draws and full DP."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from verify_correspondence_v6 import check_hashes
from verify_scaffold_specificity_v47 import extract, scores, scan


def read(p): return json.loads((ROOT / p).read_text())
def sha(p): return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()


def numeric_bracket_inside(value):
    at = 0; n = len(value)
    while True:
        while at < n and value[at].isspace(): at += 1
        start = at
        while at < n and '0' <= value[at] <= '9': at += 1
        if start == at: return False
        while at < n and value[at].isspace(): at += 1
        if at == n: return True
        if value[at] not in ',;-–−': return False
        at += 1


def rebuild_masks(text, units, boundary):
    u = units[boundary['page'] - 1]; a, b = u['span']; local = text[a:b]
    offset = boundary['page_offset']; needle = boundary['needle']
    assert local.count(needle) == 1 and local[offset:offset + len(needle)] == needle
    start = a + offset
    ledger = [{'reason': 'reference_tail', 'span': [start, len(text)], 'boundary_page': boundary['page'], 'boundary_page_offset': offset}]
    candidates = []
    for u in units:
        x, y = u['span']; page = text[x:y]
        for at, char in enumerate(page):
            if char != '[': continue
            end = page.find(']', at + 1)
            if end < 0 or not numeric_bracket_inside(page[at + 1:end]): continue
            span = [x + at, x + end + 1]; before = span[1] <= start
            candidates.append({'page': u['page'], 'page_span': [at, end + 1], 'span': span, 'text': page[at:end + 1],
                'treatment': 'inline_numeric_bracket' if before else 'covered_by_reference_tail'})
            if before: ledger.append({'reason': 'inline_numeric_bracket', 'span': span, 'page': u['page'], 'page_span': [at, end + 1]})
    union = []
    for a, b in sorted(r['span'] for r in ledger):
        if union and a <= union[-1][1]: union[-1][1] = max(union[-1][1], b)
        else: union.append([a, b])
    return {'reference_start': start, 'ledger': ledger, 'bracket_candidates': candidates, 'masks': union}


def main():
    run = ROOT / 'runs/000049_citation_sensitivity'; check_hashes(run)
    cfg = read('experiments/citation_sensitivity_v49.json'); pre = read('data/v49/preflight.json')
    manifest = read('runs/000049_citation_sensitivity/manifest.json')
    for p, h in pre['hashes'].items(): assert sha(p) == h, p
    for p, h in cfg['input_hashes'].items(): assert pre['hashes'][p] == h
    assert pre['hashes']['experiments/citation_sensitivity_v49.json'] == sha('experiments/citation_sensitivity_v49.json')
    assert cfg['registered_at_utc'] < pre['sealed_at_utc'] < manifest['finished_at_utc']
    assert (cfg['request_budget'], cfg['numeric_budget'], cfg['reference_lcs'], cfg['minimum_shared_numeric_types'], cfg['parent_draws_per_shuffle_family']) == (0, 11, 6, 3, 16)
    assert cfg['seed'] == read('experiments/scaffold_specificity_v47.json')['seed']
    assert cfg['bracket_pattern'] == r'\[\s*[0-9]+(?:\s*[,;\-–−]\s*[0-9]+)*\s*\]'
    # Exercise the separate character grammar before using it on the source scope.
    for s in ['1', ' 2,\n3 ', '4–7', '8−9', '10-11', '12; 13']: assert numeric_bracket_inside(s)
    for s in ['', '1.3', 'NASA', '1,', '1 2', '[1', '١']: assert not numeric_bracket_inside(s)
    ref = read('data/v49/reference.json'); parent_ref = read('data/v47/reference.json')
    old_report = read('runs/000047_scaffold_specificity/report.json')
    assert ref == {'target_inventory': parent_ref['target_inventory'], 'publisher_observed': parent_ref['publisher_observed'],
                   'publisher_controls': parent_ref['publisher_controls'], 'v47_comparators': old_report['comparators']}
    target = read('data/v38/target_export.json')['text']; scope = read('data/v46/scope.json')
    ti = extract(target, scope['target_units'], scope['target_masks'], False)
    assert ti == parent_ref['target_inventory'] == read('data/v46/inventory.json')['target']
    left = ti['anchors']; ts = scores(left, left); assert ts['ordered_lcs'] == ts['source_count'] == ts['bag_capacity'] == 10
    assert ref['publisher_observed']['ordered_lcs'] == 6 and ref['publisher_observed']['source_count'] == 11
    summaries = []; retention = []; total_windows = 0
    audit = read('data/v48/selection.json')['occurrences']; assert len(audit) == 13
    for spec in cfg['sources']:
        export = read(spec['export']); assert sha(spec['pdf']) == export['source_pdf_sha256']
        assert export.get('material_available', True) is True and len(export['pages']) == spec['pages']
        us = []; texts = []; offset = 0
        for i, p in enumerate(export['pages']):
            assert p['page'] == i + 1 and hashlib.sha256(p['text'].encode()).hexdigest() == p['text_sha256']
            us.append({'unit': i, 'page': i + 1, 'span': [offset, offset + len(p['text'])], 'text_length': len(p['text'])})
            texts.append(p['text']); offset += len(p['text']) + 1
        text = '\n'.join(texts); full = extract(text, us, [], True)
        assert read(spec['inventory']) == {'units': us, 'joined_text_sha256': hashlib.sha256(text.encode()).hexdigest(), 'inventory': full}
        for page in spec['reference_scope_image_pages']:
            p = export['pages'][page - 1]; assert sha(p['image']) == p['image_sha256']
        p = export['pages'][spec['boundary']['page'] - 1]
        assert p['image_sha256'] == spec['boundary_image_sha256']
        masks = rebuild_masks(text, us, spec['boundary'])
        assert read(f"data/v49/{spec['id']}_scope.json") == {'units': us, **masks}
        right = []; removed = []
        for r in full['anchors']:
            if any(r['span'][0] < b and r['span'][1] > a for a, b in masks['masks']): removed.append(r)
            else: right.append(r | {'original_anchor_index': r['anchor_index'], 'anchor_index': len(right)})
        assert read(f"data/v49/{spec['id']}_inventory.json") == {'anchors': right, 'removed_anchors': removed}
        assert len(right) + len(removed) == len(full['anchors'])
        mapping = {r['original_anchor_index']: r['anchor_index'] for r in right}
        assert len(mapping) == len(right)
        for r in right:
            assert text[slice(*r['span'])] == r['value'] == export['pages'][r['page'] - 1]['text'][slice(*r['page_span'])]
            assert not any(r['span'][0] < b and r['span'][1] > a for a, b in masks['masks'])
        observed = {'whole': scores(left, right), 'window_scan': scan(left, right, 11)}
        a = read(f"data/v49/{spec['id']}_assessment.json"); assert a['observed'] == observed
        parent = read(spec['assessment']); cases = a['controls']
        all_ids = list(range(len(full['anchors']))); groups = [[r['anchor_index'] for r in full['anchors'] if r['unit'] == u] for u in range(len(us))]
        perm = lambda count, family, draw: sorted(range(count), key=lambda i: (hashlib.sha256(f"{cfg['seed']}|{family}|{draw}|{i}".encode()).digest(), i))
        expected = [('reverse', None, all_ids[::-1], None), ('within_paragraph_reverse', None, [i for g in groups for i in g[::-1]], list(range(len(us))))]
        for draw in range(16):
            expected.append(('anchor_shuffle', draw, perm(len(all_ids), 'anchor_shuffle', draw), None))
            blocks = perm(len(us), 'paragraph_shuffle', draw)
            expected.append(('paragraph_shuffle', draw, [i for u in blocks for i in groups[u]], blocks))
        assert len(parent['controls']) == len(cases) == len(expected) == 34
        for index, (c, old, (family, draw, original_order, blocks)) in enumerate(zip(cases, parent['controls'], expected, strict=True)):
            assert (old['family'], old['draw'], old['anchor_order'], old['unit_order']) == (family, draw, original_order, blocks)
            order = [mapping[i] for i in original_order if i in mapping]; rows = [right[i] for i in order]
            assert (c['parent_control_index'], c['family'], c['draw'], c['anchor_order'], c['unit_order']) == (index, family, draw, order, blocks)
            assert c['index_inventory_preserved'] and sorted(order) == list(range(len(right)))
            assert c['bag_preserved'] and Counter(r['key'] for r in rows) == Counter(r['key'] for r in right)
            assert c['index_identity'] == (order == list(range(len(right))))
            assert c['key_identity'] == ([r['key'] for r in rows] == [r['key'] for r in right])
            assert c['whole'] == scores(left, rows) and c['window_scan'] == scan(left, rows, 11)
        sc = scores(right, right); assert sc['ordered_lcs'] == sc['source_count'] == sc['bag_capacity']
        for w in [observed['window_scan']] + [c['window_scan'] for c in cases]:
            assert w['window_count'] == max(0, observed['whole']['source_count'] - 10)
            total_windows += w['window_count']
        assert a['functional_checks_passed'] is True
        maximum = observed['window_scan']['maximum_lcs']; eligible = maximum is not None
        maxima = {f: max(c['window_scan']['maximum_lcs'] for c in cases if c['family'] == f) for f in dict.fromkeys(c['family'] for c in cases)} if eligible else {}
        order_eligible = eligible and observed['whole']['shared_distinct'] >= 3
        decision = {'length_comparison_eligible': eligible, 'publisher_strictly_exceeds': 6 > maximum if eligible else None,
            'numeric_family_maxima': maxima, 'within_paper_order_eligible': order_eligible,
            'within_paper_order_separated': all(maximum > n for n in maxima.values()) if order_eligible else None,
            'control_ties': sum(c['window_scan']['maximum_lcs'] == maximum for c in cases) if eligible else None,
            'controls_greater': sum(c['window_scan']['maximum_lcs'] > maximum for c in cases) if eligible else None}
        assert a['decision'] == decision
        old = next(r for r in old_report['comparators'] if r['id'] == spec['id'])
        summaries.append({'id': spec['id'], 'pages': len(us), 'reference_start': masks['reference_start'],
            'inline_numeric_bracket_masks': len(masks['ledger']) - 1, 'reference_tail_characters': len(text) - masks['reference_start'],
            'original_mixed_anchor_count': len(full['anchors']), 'retained_mixed_anchor_count': len(right), 'removed_mixed_anchor_count': len(removed),
            'whole': observed['whole'], 'window_count': observed['window_scan']['window_count'], 'maximum_window_lcs': maximum,
            'maximizing_starts': observed['window_scan']['maximizing_starts'], 'control_denominator': 34,
            'index_identity_controls': sum(c['index_identity'] for c in cases), 'key_identity_controls': sum(c['key_identity'] for c in cases),
            'functional_checks_passed': True, 'v47_whole': old['whole'], 'v47_maximum_window_lcs': old['maximum_window_lcs'], **decision})
        for r in audit:
            if r['source_id'] != spec['id']: continue
            assert full['anchors'][r['anchor_index']]['span'] == r['span']
            reasons = sorted({m['reason'] for m in masks['ledger'] if r['span'][0] < m['span'][1] and r['span'][1] > m['span'][0]})
            kept = r['anchor_index'] in mapping; assert kept == (not reasons)
            retention.append({'occurrence_id': r['occurrence_id'], 'source_id': spec['id'], 'value': r['value'],
                              'page': r['page'], 'span': r['span'], 'retained': kept, 'mask_reasons': reasons})
    assert read('data/v49/audited_occurrence_retention.json') == retention and len(retention) == 13
    report = read('runs/000049_citation_sensitivity/report.json')
    assert report['comparators'] == summaries and report['comparator_denominator'] == len(summaries) == 2
    eligible = all(s['length_comparison_eligible'] for s in summaries)
    gate = all(s['publisher_strictly_exceeds'] for s in summaries) if eligible else None
    assert report['specificity_comparison_eligible'] == eligible and report['registered_specificity_gate'] == gate
    assert report['outcome'] == ('publisher_exceeds_both_masked_windows' if gate is True else 'publisher_not_strictly_specific_after_masking' if gate is False else 'unavailable')
    assert report['functional_checks_passed'] and report['reference_lcs'] == 6 and report['numeric_budget'] == 11
    assert report['prior_audited_occurrences'] == 13 and report['prior_audited_occurrences_retained'] == sum(r['retained'] for r in retention)
    assert report['prior_audited_occurrences_removed'] == sum(not r['retained'] for r in retention)
    assert report['opaque_residual_structural_assays'] == 2
    for k in ['network_requests', 'new_pdf_extractions', 'new_page_renders', 'new_random_control_draws', 'opaque_lexical_or_semantic_scores',
              'semantic_labels_admitted', 'source_identities_admitted', 'independent_reviews_admitted', 'untouched_test_units_admitted', 'external_messages_sent']: assert report[k] == 0
    assert report['scientific_acceptance'] is report['semantic_evaluation_metrics'] is None
    prior = []
    for path in sorted((ROOT / 'runs').glob('000*/manifest.json')):
        if path.parent != run: check_hashes(path.parent); prior.append(path.parent.name)
    assert len(prior) == 48
    for path in (ROOT / 'reports').glob('*_deliverable_seal.json'):
        for p, h in json.loads(path.read_text()).get('deliverable_hashes', {}).items(): assert sha(p) == h
    result = {'state': 'verified', 'manifest_sha256': sha('runs/000049_citation_sensitivity/manifest.json'),
        'citation_masks_reconstructed_with_character_grammar': True, 'all_retained_and_removed_anchors_verified': True,
        'original_control_draws_reconstructed_and_filtered': 68, 'windows_verified_with_full_table_lcs': total_windows,
        'all_13_audited_occurrence_retention_rows_verified': True, 'prior_scores_unchanged': True,
        'independent_scientific_review': False, 'semantics_or_source_identity_validated': False, 'prior_runs_preserved': prior}
    out = ROOT / 'reports/000049_verification.json'
    if out.exists(): assert {k: v for k, v in json.loads(out.read_text()).items() if k != 'verified_at_utc'} == result
    else:
        with out.open('x') as stream: json.dump(result | {'verified_at_utc': datetime.now(timezone.utc).isoformat()}, stream, indent=2); stream.write('\n')
    print(json.dumps({'state': 'verified', 'prior_runs_preserved': len(prior), 'windows_verified': total_windows, 'specificity_gate': gate}, indent=2))


if __name__ == '__main__': main()
