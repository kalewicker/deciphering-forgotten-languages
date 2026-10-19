"""Registered residual-scaffold extraction and fixed bag-preserving controls."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from fl_decipher.scaffold_v46 import anchors, controls, merged, metrics, residuals, source_units

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads((ROOT / path).read_text())


def sha(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def write(path, value):
    path = ROOT / path; path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False); stream.write('\n')


def main():
    cfg = read('experiments/scaffold_v46.json')
    assert not (ROOT / 'data/v46').exists()
    for p, expected in cfg['input_hashes'].items():
        assert sha(p) == expected, p
    paths = ['experiments/scaffold_v46.json', 'scripts/run_scaffold_v46.py',
             'src/fl_decipher/scaffold_v46.py', 'tests/test_scaffold_v46.py']
    write('data/v46/preflight.json', {'sealed_at_utc': datetime.now(timezone.utc).isoformat(),
          'hashes': cfg['input_hashes'] | {p: sha(p) for p in paths}})
    target = read('data/v38/target_export.json')['text']
    source = (ROOT / 'data/v42/visible_page.txt').read_text()
    assert source == read('data/v42/page_observations.json')['text'] and read('data/v42/page_observations.json')['material_available']
    quotes = read('data/v39/frozen_queries.json')['queries']; assert len(quotes) == 8
    for q in quotes:
        assert target[slice(*q['span'])] == q['text']
    assert target.count(cfg['bibliography_marker']) == 1 and target.index(cfg['bibliography_marker']) == cfg['bibliography_start']
    tm = [{'reason': 'title_header', 'span': [0, quotes[0]['span'][0]]}]
    tm += [{'reason': q['quote_id'], 'span': q['span']} for q in quotes]
    tm += [{'reason': 'bibliography', 'span': [cfg['bibliography_start'], len(target)]}]
    target_masks = merged([r['span'] for r in tm], len(target))
    tu = [{'unit': i, 'span': span} for i, span in enumerate(residuals(target_masks, len(target)))]
    su, sm = source_units((ROOT / 'data/v42/acquisition/source/body.bin').read_bytes(), source, cfg['source_selector'])
    assert len(su) == cfg['expected_source_paragraphs']
    source_masks = merged([r['span'] for r in sm], len(source))
    write('data/v46/scope.json', {'target_mask_ledger': tm, 'target_masks': target_masks, 'target_units': tu,
          'source_selector': cfg['source_selector'], 'source_units': su, 'source_mask_ledger': sm, 'source_masks': source_masks})
    ti = anchors(target, tu, target_masks); si = anchors(source, su, source_masks)
    write('data/v46/inventory.json', {'target': ti, 'source': si})
    left, right = ti['anchors'], si['anchors']; observed = metrics(left, right)
    cases = controls(right, len(su), cfg['seed'], cfg['draws_per_shuffle_family'])
    original_bag = Counter(r['key'] for r in right)
    for c in cases:
        rows = [right[i] for i in c['anchor_order']]
        c['bag_preserved'] = Counter(r['key'] for r in rows) == original_bag
        c['index_inventory_preserved'] = sorted(c['anchor_order']) == list(range(len(right)))
        c['scores'] = metrics(left, rows)
    selfcopy = {}
    for label, rows in [('target', left), ('source', right)]:
        result = metrics(rows, rows)
        selfcopy[label] = all(r['ordered_lcs'] == r['target_count'] == r['source_count'] == r['bag_capacity'] for r in result.values())
    mask_checks = {}
    for label, rows, masks in [('target', left, target_masks), ('source', right, source_masks)]:
        mask_checks[label] = all(not (r['span'][0] < b and r['span'][1] > a) for r in rows for a, b in masks)
    maxima = {family: max(c['scores']['number']['ordered_lcs'] for c in cases if c['family'] == family)
              for family in cfg['control_families']}
    numeric = observed['number']['ordered_lcs']
    separated = {family: numeric > maximum for family, maximum in maxima.items()}
    functional = all(selfcopy.values()) and all(mask_checks.values()) and all(c['bag_preserved'] and c['index_inventory_preserved'] for c in cases)
    eligible = functional and observed['number']['shared_distinct'] >= cfg['minimum_shared_numeric_types']
    gate = all(separated.values()) if eligible else None
    write('data/v46/assessment.json', {'observed': observed, 'controls': cases, 'selfcopy_checks': selfcopy,
          'mask_checks': mask_checks, 'numeric_family_maxima': maxima, 'numeric_family_separation': separated})
    report = {'experiment_id': 'scaffold_v46', 'outcome': 'order_separation_observed' if gate is True else 'order_not_separated' if gate is False else 'sparse_or_invalid',
        'network_requests': 0, 'source_reextractions_from_frozen_bytes': 1, 'known_english_quote_masks': len(quotes),
        'target_residual_units': len(tu), 'source_paragraph_units': len(su), 'source_quote_masks': len(sm),
        'target_anchor_count': len(left), 'source_anchor_count': len(right), 'control_denominator': len(cases),
        'observed': observed, 'numeric_family_maxima': maxima, 'numeric_family_separation': separated,
        'functional_checks_passed': functional, 'numeric_gate_eligible': eligible, 'registered_order_separation_gate': gate,
        'numeric_control_ties': sum(c['scores']['number']['ordered_lcs'] == numeric for c in cases),
        'numeric_controls_greater': sum(c['scores']['number']['ordered_lcs'] > numeric for c in cases),
        'index_identity_controls': sum(c['index_identity'] for c in cases), 'key_identity_controls': sum(c['key_identity'] for c in cases),
        'opaque_residual_structural_assays': 1, 'opaque_lexical_or_semantic_scores': 0,
        'semantic_labels_admitted': 0, 'source_identities_admitted': 0, 'independent_reviews_admitted': 0,
        'untouched_test_units_admitted': 0, 'external_messages_sent': 0,
        'scientific_acceptance': None, 'semantic_evaluation_metrics': None}
    write('runs/000046_scaffold/report.json', report)
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
