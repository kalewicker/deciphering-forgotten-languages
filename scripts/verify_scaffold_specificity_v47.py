"""Rebuild all PDF anchors, windows and controls using full-table LCS DP."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from verify_correspondence_v6 import check_hashes


def read(p): return json.loads((ROOT / p).read_text())
def sha(p): return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()


def dp(a, b):
    grid = [[0] * (len(b) + 1) for _ in range(len(a) + 1)]
    for i, x in enumerate(a, 1):
        for j, y in enumerate(b, 1):
            grid[i][j] = 1 + grid[i - 1][j - 1] if x == y else max(grid[i - 1][j], grid[i][j - 1])
    return grid[-1][-1]


def scores(left, right):
    a = [r['key'] for r in left if r['kind'] == 'number']
    b = [r['key'] for r in right if r['kind'] == 'number']
    ca, cb = Counter(a), Counter(b)
    return {'target_count': len(a), 'source_count': len(b), 'shared_distinct': len(ca.keys() & cb.keys()),
            'bag_capacity': sum(min(ca[k], cb[k]) for k in ca.keys() & cb.keys()), 'ordered_lcs': dp(a, b)}


def scan(left, right, budget):
    nums = [r for r in right if r['kind'] == 'number']; windows = []
    for start in range(max(0, len(nums) - budget + 1)):
        window = nums[start:start + budget]
        windows.append({'numeric_span': [start, start + budget], 'anchor_indices': [r['anchor_index'] for r in window], 'scores': scores(left, window)})
    lengths = [w['scores']['ordered_lcs'] for w in windows]; maximum = max(lengths) if lengths else None
    return {'numeric_anchor_count': len(nums), 'window_count': len(windows), 'windows': windows,
            'maximum_lcs': maximum, 'maximizing_starts': [i for i, n in enumerate(lengths) if n == maximum]}


def extract(text, units, masks, page_local):
    rows = []; excluded = []
    for kind, pattern in [('number', r'[0-9]+(?:[.,][0-9]+)*'), ('upper', r'[A-Z]{2,}')]:
        for match in re.finditer(pattern, text):
            a, b = match.span()
            scope = [u for u in units if u['span'] is not None and u['span'][0] <= a < b <= u['span'][1]]
            if not scope or any(x < b and y > a for x, y in masks): continue
            assert len(scope) == 1
            before, after = text[a - 1:a] if a else '', text[b:b + 1]
            bad = any(c and (c.isalnum() or c == '_') for c in [before, after])
            bad |= bool(kind == 'number' and before and before in '.,')
            if bad:
                excluded.append({'kind': kind, 'value': match.group(), 'span': [a, b], 'reason': 'word_or_leading_decimal_boundary'})
                continue
            row = {'kind': kind, 'value': match.group(), 'key': kind + ':' + match.group(), 'span': [a, b], 'unit': scope[0]['unit']}
            if page_local:
                row.update(page=scope[0]['page'], page_span=[a - scope[0]['span'][0], b - scope[0]['span'][0]])
            rows.append(row)
    rows.sort(key=lambda r: (r['span'], r['kind']))
    for i, r in enumerate(rows): r['anchor_index'] = i
    return {'anchors': rows, 'excluded_boundary_candidates': excluded}


def main():
    run = ROOT / 'runs/000047_scaffold_specificity'; check_hashes(run)
    cfg = read('experiments/scaffold_specificity_v47.json'); pre = read('data/v47/preflight.json')
    manifest = read('runs/000047_scaffold_specificity/manifest.json')
    for p, h in pre['hashes'].items(): assert sha(p) == h, p
    for p, h in cfg['input_hashes'].items(): assert pre['hashes'][p] == h
    assert cfg['registered_at_utc'] < pre['sealed_at_utc'] < manifest['finished_at_utc']
    assert pre['hashes']['experiments/scaffold_specificity_v47.json'] == sha('experiments/scaffold_specificity_v47.json')
    assert (cfg['request_budget'], cfg['numeric_budget'], cfg['reference_lcs'], cfg['minimum_shared_numeric_types'], cfg['draws_per_shuffle_family']) == (0, 11, 6, 3, 16)
    assert cfg['seed'] == read('experiments/scaffold_v46.json')['seed']
    target = read('data/v38/target_export.json')['text']; quotes = read('data/v39/frozen_queries.json')['queries']
    assert len(quotes) == 8
    for q in quotes: assert target[slice(*q['span'])] == q['text']
    assert target.index('Adrián-Martínez, S. et al.') == 7332
    spans = [[0, quotes[0]['span'][0]]] + [q['span'] for q in quotes] + [[7332, len(target)]]
    masks = []
    for x, y in sorted(spans):
        if masks and x <= masks[-1][1]: masks[-1][1] = max(y, masks[-1][1])
        else: masks.append([x, y])
    units = []; cursor = 0
    for a, b in masks:
        if cursor < a: units.append({'unit': len(units), 'span': [cursor, a]})
        cursor = b
    if cursor < len(target): units.append({'unit': len(units), 'span': [cursor, len(target)]})
    oldscope = read('data/v46/scope.json'); oldinv = read('data/v46/inventory.json'); reference = read('data/v47/reference.json')
    assert units == oldscope['target_units'] == reference['target_units']
    assert masks == oldscope['target_masks'] == reference['target_masks']
    inv = extract(target, units, masks, False)
    assert inv == oldinv['target'] == reference['target_inventory']
    left = inv['anchors']; old = read('data/v46/assessment.json')
    target_selfcopy = scores(left, left)
    assert target_selfcopy['ordered_lcs'] == target_selfcopy['source_count'] == target_selfcopy['bag_capacity'] == 10
    assert scores(left, oldinv['source']['anchors']) == old['observed']['number'] == reference['publisher_observed']
    assert reference['publisher_observed']['ordered_lcs'] == 6 and reference['publisher_observed']['source_count'] == 11
    publisher_controls = []
    for c in old['controls']:
        s = scores(left, [oldinv['source']['anchors'][i] for i in c['anchor_order']])
        assert s == c['scores']['number']
        publisher_controls.append({'family': c['family'], 'draw': c['draw'], 'scores': s})
    assert publisher_controls == reference['publisher_controls'] and len(publisher_controls) == 34
    summaries = []; total_windows = 0
    for spec in cfg['comparators']:
        export = read(spec['export']); assert sha(spec['pdf']) == export['source_pdf_sha256']
        assert export.get('material_available', True) is True
        pages = export['pages']; assert len(pages) == spec['pages']
        texts = []; us = []; offset = 0
        for i, page in enumerate(pages):
            assert page['page'] == i + 1 and hashlib.sha256(page['text'].encode()).hexdigest() == page['text_sha256']
            us.append({'unit': i, 'page': i + 1, 'span': [offset, offset + len(page['text'])], 'text_length': len(page['text'])})
            texts.append(page['text']); offset += len(page['text']) + 1
        text = '\n'.join(texts); inv = extract(text, us, [], True)
        saved = read(f"data/v47/{spec['id']}_inventory.json")
        assert saved == {'units': us, 'joined_text_sha256': hashlib.sha256(text.encode()).hexdigest(), 'inventory': inv}
        right = inv['anchors']
        for r in right: assert text[slice(*r['span'])] == r['value'] == pages[r['page'] - 1]['text'][slice(*r['page_span'])]
        observed = {'whole': scores(left, right), 'window_scan': scan(left, right, 11)}
        a = read(f"data/v47/{spec['id']}_assessment.json"); assert a['observed'] == observed
        cases = a['controls']; ids = list(range(len(right))); groups = [[r['anchor_index'] for r in right if r['unit'] == u] for u in range(len(us))]
        perm = lambda n, f, d: sorted(range(n), key=lambda i: (hashlib.sha256(f"{cfg['seed']}|{f}|{d}|{i}".encode()).digest(), i))
        expected = [('reverse', None, ids[::-1], None), ('within_paragraph_reverse', None, [i for g in groups for i in g[::-1]], list(range(len(us))))]
        for draw in range(16):
            expected.append(('anchor_shuffle', draw, perm(len(right), 'anchor_shuffle', draw), None))
            blocks = perm(len(us), 'paragraph_shuffle', draw)
            expected.append(('paragraph_shuffle', draw, [i for u in blocks for i in groups[u]], blocks))
        assert len(cases) == len(expected) == 34
        for c, (family, draw, order, blocks) in zip(cases, expected, strict=True):
            assert (c['family'], c['draw'], c['anchor_order'], c['unit_order']) == (family, draw, order, blocks)
            assert sorted(order) == ids and c['bag_preserved'] and c['index_inventory_preserved']
            ordered = [right[i] for i in order]
            assert Counter(r['key'] for r in ordered) == Counter(r['key'] for r in right)
            assert c['index_identity'] == (order == ids) and c['key_identity'] == ([r['key'] for r in ordered] == [r['key'] for r in right])
            assert c['whole'] == scores(left, ordered) and c['window_scan'] == scan(left, ordered, 11)
        count = observed['whole']['source_count']; maximum = observed['window_scan']['maximum_lcs']
        selfcopy = scores(right, right); assert selfcopy['ordered_lcs'] == selfcopy['source_count'] == selfcopy['bag_capacity']
        for scan_result in [observed['window_scan']] + [c['window_scan'] for c in cases]:
            assert scan_result['window_count'] == max(0, count - 10)
            total_windows += scan_result['window_count']
        assert a['functional_checks_passed'] is True
        maxima = {f: max(c['window_scan']['maximum_lcs'] for c in cases if c['family'] == f) for f in dict.fromkeys(c['family'] for c in cases)} if maximum is not None else {}
        eligible = maximum is not None; order_eligible = eligible and observed['whole']['shared_distinct'] >= 3
        decision = {'length_comparison_eligible': eligible, 'publisher_strictly_exceeds': 6 > maximum if eligible else None,
                    'numeric_family_maxima': maxima, 'within_paper_order_eligible': order_eligible,
                    'within_paper_order_separated': all(maximum > n for n in maxima.values()) if order_eligible else None,
                    'control_ties': sum(c['window_scan']['maximum_lcs'] == maximum for c in cases) if eligible else None,
                    'controls_greater': sum(c['window_scan']['maximum_lcs'] > maximum for c in cases) if eligible else None}
        assert a['decision'] == decision
        summaries.append({'id': spec['id'], 'pages': len(us), 'text_characters': len(text), 'whole': observed['whole'],
            'window_count': observed['window_scan']['window_count'], 'maximum_window_lcs': maximum, 'maximizing_starts': observed['window_scan']['maximizing_starts'],
            'control_denominator': 34, 'functional_checks_passed': True, 'index_identity_controls': sum(c['index_identity'] for c in cases),
            'key_identity_controls': sum(c['key_identity'] for c in cases), **decision})
    report = read('runs/000047_scaffold_specificity/report.json')
    assert report['comparators'] == summaries and len(summaries) == report['comparator_denominator'] == 2
    eligible = all(s['length_comparison_eligible'] for s in summaries)
    gate = all(s['publisher_strictly_exceeds'] for s in summaries) if eligible else None
    assert report['specificity_comparison_eligible'] == eligible and report['registered_specificity_gate'] == gate
    assert report['outcome'] == ('publisher_exceeds_both_windows' if gate is True else 'publisher_not_strictly_specific' if gate is False else 'unavailable')
    assert report['functional_checks_passed'] and report['reference_lcs'] == 6 and report['numeric_budget'] == 11
    assert report['opaque_residual_structural_assays'] == 2
    for k in ['network_requests', 'new_pdf_extractions', 'opaque_lexical_or_semantic_scores', 'semantic_labels_admitted', 'source_identities_admitted',
              'independent_reviews_admitted', 'untouched_test_units_admitted', 'external_messages_sent']: assert report[k] == 0
    assert report['scientific_acceptance'] is report['semantic_evaluation_metrics'] is None
    previous = []
    for path in sorted((ROOT / 'runs').glob('000*/manifest.json')):
        if path.parent != run: check_hashes(path.parent); previous.append(path.parent.name)
    assert len(previous) == 46
    for path in (ROOT / 'reports').glob('*_deliverable_seal.json'):
        for p, h in json.loads(path.read_text()).get('deliverable_hashes', {}).items(): assert sha(p) == h
    result = {'state': 'verified', 'manifest_sha256': sha('runs/000047_scaffold_specificity/manifest.json'),
              'target_masks_inventory_and_publisher_reference_reproduced': True, 'all_pdf_anchors_and_page_spans_reconstructed': True,
              'controls_verified': 68, 'windows_verified_including_controls': total_windows, 'full_table_lcs_verified': True,
              'saved_pdf_text_not_newly_extracted_or_visually_reviewed': True, 'independent_scientific_review': False,
              'semantics_or_source_identity_validated': False, 'prior_runs_preserved': previous}
    out = ROOT / 'reports/000047_verification.json'
    if out.exists(): assert {k: v for k, v in json.loads(out.read_text()).items() if k != 'verified_at_utc'} == result
    else:
        with out.open('x') as stream: json.dump(result | {'verified_at_utc': datetime.now(timezone.utc).isoformat()}, stream, indent=2); stream.write('\n')
    print(json.dumps({'state': 'verified', 'prior_runs_preserved': len(previous), 'windows_verified': total_windows, 'registered_specificity_gate': gate}, indent=2))


if __name__ == '__main__': main()
