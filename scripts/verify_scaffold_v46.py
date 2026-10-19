"""Reconstruct masks/anchors/controls and verify lengths by full-table LCS DP."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from verify_correspondence_v6 import check_hashes


def read(p): return json.loads((ROOT / p).read_text())
def sha(p): return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()


def union(intervals):
    result = []
    for a, b in sorted(intervals):
        if result and a <= result[-1][1]: result[-1][1] = max(b, result[-1][1])
        elif a != b: result.append([a, b])
    return result


def extract(text, units, masks):
    rows = []; excluded = []
    for m in re.finditer(r'([0-9]+(?:[.,][0-9]+)*)|([A-Z]{2,})', text):
        a, b = m.span(); kind = 'number' if m.group(1) is not None else 'upper'
        ids = [u['unit'] for u in units if u['span'] and u['span'][0] <= a < b <= u['span'][1]]
        if not ids or any(x < b and y > a for x, y in masks): continue
        assert len(ids) == 1
        before = text[a - 1] if a else ''; after = text[b] if b < len(text) else ''
        bad = any(c and (c.isalnum() or c == '_') for c in [before, after])
        bad = bad or (kind == 'number' and bool(before) and before in '.,')
        if bad:
            excluded.append({'kind': kind, 'value': m.group(), 'span': [a, b], 'reason': 'word_or_leading_decimal_boundary'})
        else:
            rows.append({'kind': kind, 'value': m.group(), 'key': kind + ':' + m.group(),
                         'span': [a, b], 'unit': ids[0], 'anchor_index': len(rows)})
    return rows, excluded


def lcs_dp(a, b):
    grid = [[0] * (len(b) + 1) for _ in range(len(a) + 1)]
    for i, x in enumerate(a, 1):
        for j, y in enumerate(b, 1):
            grid[i][j] = grid[i - 1][j - 1] + 1 if x == y else max(grid[i - 1][j], grid[i][j - 1])
    return grid[-1][-1]


def scores(left, right):
    result = {}
    for kind in ['number', 'upper', 'combined']:
        a = [r['key'] for r in left if kind == 'combined' or r['kind'] == kind]
        b = [r['key'] for r in right if kind == 'combined' or r['kind'] == kind]
        ca, cb = Counter(a), Counter(b)
        result[kind] = {'target_count': len(a), 'source_count': len(b), 'shared_distinct': len(set(a) & set(b)),
                        'bag_capacity': sum(min(ca[k], cb[k]) for k in ca.keys() & cb.keys()), 'ordered_lcs': lcs_dp(a, b)}
    return result


def main():
    run = ROOT / 'runs/000046_scaffold'; check_hashes(run)
    cfg = read('experiments/scaffold_v46.json'); pre = read('data/v46/preflight.json')
    manifest = read('runs/000046_scaffold/manifest.json')
    for p, h in pre['hashes'].items(): assert sha(p) == h, p
    assert all(pre['hashes'][p] == h for p, h in cfg['input_hashes'].items())
    assert pre['hashes']['experiments/scaffold_v46.json'] == sha('experiments/scaffold_v46.json')
    assert cfg['registered_at_utc'] < pre['sealed_at_utc'] < manifest['finished_at_utc']
    assert cfg['request_budget'] == 0 and cfg['draws_per_shuffle_family'] == 16 and cfg['minimum_shared_numeric_types'] == 3
    scope = read('data/v46/scope.json'); inv = read('data/v46/inventory.json'); a = read('data/v46/assessment.json')
    target = read('data/v38/target_export.json')['text']; source = (ROOT / 'data/v42/visible_page.txt').read_text()
    assert source == read('data/v42/page_observations.json')['text']
    quotes = read('data/v39/frozen_queries.json')['queries']; assert len(quotes) == 8
    for q in quotes: assert target[slice(*q['span'])] == q['text']
    assert target.count(cfg['bibliography_marker']) == 1 and target.index(cfg['bibliography_marker']) == cfg['bibliography_start'] == 7332
    tm = [{'reason': 'title_header', 'span': [0, quotes[0]['span'][0]]}]
    tm += [{'reason': q['quote_id'], 'span': q['span']} for q in quotes]
    tm += [{'reason': 'bibliography', 'span': [7332, len(target)]}]
    assert scope['target_mask_ledger'] == tm and scope['target_masks'] == union([r['span'] for r in tm])
    complement = []; cursor = 0
    for x, y in scope['target_masks']:
        if cursor < x: complement.append([cursor, x])
        cursor = y
    if cursor < len(target): complement.append([cursor, len(target)])
    assert scope['target_units'] == [{'unit': i, 'span': span} for i, span in enumerate(complement)]
    soup = BeautifulSoup((ROOT / 'data/v42/acquisition/source/body.bin').read_bytes(), 'html.parser')
    for tag in soup.select('script,style,noscript,template,svg,canvas'): tag.decompose()
    assert soup.select_one('body').get_text(' ', strip=True) == source
    containers = soup.select(cfg['source_selector']); assert len(containers) == 1
    ps = containers[0].find_all('p', recursive=False); assert len(ps) == cfg['expected_source_paragraphs'] == 14
    units = []; masks = []
    for i, p in enumerate(ps):
        text = p.get_text(' ', strip=True); starts = [m.start() for m in re.finditer(re.escape(text), source)] if text else []
        assert not text or len(starts) == 1
        span = [starts[0], starts[0] + len(text)] if starts else None
        units.append({'unit': i, 'span': span, 'text': text})
        curly = list(re.finditer('“[^“”]*”', text)); straight = list(re.finditer(r'"[^"]*"', text))
        assert len(curly) == text.count('“') == text.count('”') and len(straight) * 2 == text.count('"')
        for m in curly + straight:
            masks.append({'unit': i, 'span': [span[0] + m.start(), span[0] + m.end()], 'reason': 'publisher_quoted_speech'})
    assert scope['source_selector'] == cfg['source_selector'] and scope['source_units'] == units
    assert scope['source_mask_ledger'] == masks and scope['source_masks'] == union([r['span'] for r in masks])
    for label, text, us, ms in [('target', target, scope['target_units'], scope['target_masks']), ('source', source, units, scope['source_masks'])]:
        rows, excluded = extract(text, us, ms)
        assert rows == inv[label]['anchors']
        sort = lambda items: sorted(items, key=lambda r: (r['span'], r['kind']))
        assert sort(excluded) == sort(inv[label]['excluded_boundary_candidates'])
        for row in rows: assert text[slice(*row['span'])] == row['value']
    left, right = inv['target']['anchors'], inv['source']['anchors']; observed = scores(left, right)
    assert a['observed'] == observed
    groups = [[r['anchor_index'] for r in right if r['unit'] == u] for u in range(14)]
    perm = lambda count, family, draw: sorted(range(count), key=lambda i: (hashlib.sha256(f"{cfg['seed']}|{family}|{draw}|{i}".encode()).digest(), i))
    ids = list(range(len(right)))
    expected = [('reverse', None, ids[::-1], None), ('within_paragraph_reverse', None, [i for g in groups for i in g[::-1]], list(range(14)))]
    for draw in range(16):
        expected.append(('anchor_shuffle', draw, perm(len(right), 'anchor_shuffle', draw), None))
        blocks = perm(14, 'paragraph_shuffle', draw)
        expected.append(('paragraph_shuffle', draw, [i for u in blocks for i in groups[u]], blocks))
    assert len(a['controls']) == len(expected) == 34
    for c, (family, draw, order, blocks) in zip(a['controls'], expected, strict=True):
        assert (c['family'], c['draw'], c['anchor_order'], c['unit_order']) == (family, draw, order, blocks)
        assert sorted(order) == ids and c['index_inventory_preserved'] and c['bag_preserved']
        transformed = [right[i] for i in order]
        assert Counter(r['key'] for r in transformed) == Counter(r['key'] for r in right)
        assert c['scores'] == scores(left, transformed)
        assert c['index_identity'] == (order == ids) and c['key_identity'] == ([r['key'] for r in transformed] == [r['key'] for r in right])
    assert a['mask_checks'] == {'target': True, 'source': True} and a['selfcopy_checks'] == {'target': True, 'source': True}
    for rows in [left, right]:
        for value in scores(rows, rows).values(): assert value['ordered_lcs'] == value['target_count'] == value['source_count'] == value['bag_capacity']
    maxima = {f: max(c['scores']['number']['ordered_lcs'] for c in a['controls'] if c['family'] == f) for f in cfg['control_families']}
    separation = {f: observed['number']['ordered_lcs'] > n for f, n in maxima.items()}
    assert a['numeric_family_maxima'] == maxima and a['numeric_family_separation'] == separation
    report = read('runs/000046_scaffold/report.json')
    assert report['observed'] == observed and report['numeric_family_maxima'] == maxima and report['numeric_family_separation'] == separation
    assert report['functional_checks_passed'] and report['numeric_gate_eligible'] == (observed['number']['shared_distinct'] >= 3)
    assert report['registered_order_separation_gate'] == all(separation.values()) is True
    for k, n in [('known_english_quote_masks', 8), ('target_residual_units', 8), ('source_paragraph_units', 14), ('source_quote_masks', 6),
                 ('target_anchor_count', len(left)), ('source_anchor_count', len(right)), ('control_denominator', 34), ('source_reextractions_from_frozen_bytes', 1),
                 ('opaque_residual_structural_assays', 1)]: assert report[k] == n
    for field, expected_n in [('numeric_control_ties', sum(c['scores']['number']['ordered_lcs'] == observed['number']['ordered_lcs'] for c in a['controls'])),
                              ('numeric_controls_greater', sum(c['scores']['number']['ordered_lcs'] > observed['number']['ordered_lcs'] for c in a['controls'])),
                              ('index_identity_controls', sum(c['index_identity'] for c in a['controls'])), ('key_identity_controls', sum(c['key_identity'] for c in a['controls']))]: assert report[field] == expected_n
    for k in ['network_requests', 'opaque_lexical_or_semantic_scores', 'semantic_labels_admitted', 'source_identities_admitted', 'independent_reviews_admitted', 'untouched_test_units_admitted', 'external_messages_sent']: assert report[k] == 0
    assert report['semantic_evaluation_metrics'] is report['scientific_acceptance'] is None
    previous = []
    for path in sorted((ROOT / 'runs').glob('000*/manifest.json')):
        if path.parent != run: check_hashes(path.parent); previous.append(path.parent.name)
    assert len(previous) == 45
    for path in (ROOT / 'reports').glob('*_deliverable_seal.json'):
        for p, h in json.loads(path.read_text()).get('deliverable_hashes', {}).items(): assert sha(p) == h
    result = {'state': 'verified', 'manifest_sha256': sha('runs/000046_scaffold/manifest.json'), 'masks_and_every_anchor_reconstructed': True,
              'all_34_controls_and_full_table_lcs_verified': True, 'shared_html_parser': 'BeautifulSoup html.parser',
              'independent_scientific_review': False, 'semantics_or_source_identity_validated': False, 'prior_runs_preserved': previous}
    out = ROOT / 'reports/000046_verification.json'
    if out.exists(): assert {k: v for k, v in json.loads(out.read_text()).items() if k != 'verified_at_utc'} == result
    else:
        with out.open('x') as stream: json.dump(result | {'verified_at_utc': datetime.now(timezone.utc).isoformat()}, stream, indent=2); stream.write('\n')
    print(json.dumps({'state': 'verified', 'prior_runs_preserved': len(previous), 'numeric_lcs': observed['number']['ordered_lcs'], 'maximum_control': max(maxima.values())}, indent=2))


if __name__ == '__main__': main()
