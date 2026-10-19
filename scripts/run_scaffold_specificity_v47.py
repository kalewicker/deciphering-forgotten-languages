"""Frozen cited-paper comparison with exhaustive equal-numeric-budget scans."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from fl_decipher.scaffold_v46 import anchors, controls, merged, metrics, residuals
from fl_decipher.scaffold_specificity_v47 import decisions, numeric, paper_inventory, paper_scope, windows

ROOT = Path(__file__).resolve().parents[1]


def read(p): return json.loads((ROOT / p).read_text())
def sha(p): return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()
def write(p, value):
    path = ROOT / p; path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False); stream.write('\n')


def main():
    cfg = read('experiments/scaffold_specificity_v47.json')
    assert not (ROOT / 'data/v47').exists() and not (ROOT / 'runs/000047_scaffold_specificity').exists()
    for p, h in cfg['input_hashes'].items(): assert sha(p) == h, p
    code = ['scripts/run_scaffold_specificity_v47.py', 'src/fl_decipher/scaffold_specificity_v47.py', 'tests/test_scaffold_specificity_v47.py']
    write('data/v47/preflight.json', {'sealed_at_utc': datetime.now(timezone.utc).isoformat(),
          'hashes': cfg['input_hashes'] | {p: sha(p) for p in code + ['experiments/scaffold_specificity_v47.json']}})
    old_scope = read('data/v46/scope.json'); old_inv = read('data/v46/inventory.json')
    target = read('data/v38/target_export.json')['text']; quotes = read('data/v39/frozen_queries.json')['queries']
    assert len(quotes) == 8
    for q in quotes: assert target[slice(*q['span'])] == q['text']
    spans = [[0, quotes[0]['span'][0]]] + [q['span'] for q in quotes] + [[7332, len(target)]]
    masks = merged(spans, len(target)); units = [{'unit': i, 'span': s} for i, s in enumerate(residuals(masks, len(target)))]
    assert masks == old_scope['target_masks'] and units == old_scope['target_units']
    ti = anchors(target, units, masks); assert ti == old_inv['target']
    left = ti['anchors']; baseline = read('data/v46/assessment.json')
    assert baseline['observed']['number']['source_count'] == cfg['numeric_budget'] == 11
    assert baseline['observed']['number']['ordered_lcs'] == cfg['reference_lcs'] == 6
    assert len(numeric(left)) == 10 and len(baseline['controls']) == 34
    write('data/v47/reference.json', {'target_inventory': ti, 'target_masks': masks, 'target_units': units,
          'publisher_observed': baseline['observed']['number'],
          'publisher_controls': [{'family': c['family'], 'draw': c['draw'], 'scores': c['scores']['number']} for c in baseline['controls']]})
    summaries = []; functional_all = True
    for spec in cfg['comparators']:
        export = read(spec['export']); text, us = paper_scope(export, sha(spec['pdf']), spec['pages'])
        inv = paper_inventory(text, us); right = inv['anchors']
        write(f"data/v47/{spec['id']}_inventory.json", {'units': us, 'joined_text_sha256': hashlib.sha256(text.encode()).hexdigest(), 'inventory': inv})
        observed = {'whole': metrics(left, right)['number'], 'window_scan': windows(left, right, cfg['numeric_budget'])}
        cases = controls(right, len(us), cfg['seed'], cfg['draws_per_shuffle_family'])
        bag = Counter(r['key'] for r in right)
        for c in cases:
            ordered = [right[i] for i in c['anchor_order']]
            c['bag_preserved'] = Counter(r['key'] for r in ordered) == bag
            c['index_inventory_preserved'] = sorted(c['anchor_order']) == list(range(len(right)))
            c['whole'] = metrics(left, ordered)['number']
            c['window_scan'] = windows(left, ordered, cfg['numeric_budget'])
        selfcopy = metrics(right, right)['number']
        functional = (selfcopy['ordered_lcs'] == selfcopy['source_count'] == selfcopy['bag_capacity']
                      and all(c['bag_preserved'] and c['index_inventory_preserved'] for c in cases)
                      and all(text[slice(*r['span'])] == export['pages'][r['page'] - 1]['text'][slice(*r['page_span'])] == r['value'] for r in right)
                      and all(v['window_count'] == max(0, len(numeric(right)) - cfg['numeric_budget'] + 1)
                              for v in [observed['window_scan']] + [c['window_scan'] for c in cases]))
        decision = decisions(cfg['reference_lcs'], observed, cases, functional, cfg['minimum_shared_numeric_types'])
        write(f"data/v47/{spec['id']}_assessment.json", {'observed': observed, 'controls': cases, 'functional_checks_passed': functional, 'decision': decision})
        summaries.append({'id': spec['id'], 'pages': len(us), 'text_characters': len(text),
            'whole': observed['whole'], 'window_count': observed['window_scan']['window_count'],
            'maximum_window_lcs': observed['window_scan']['maximum_lcs'],
            'maximizing_starts': observed['window_scan']['maximizing_starts'],
            'control_denominator': len(cases), 'functional_checks_passed': functional,
            'index_identity_controls': sum(c['index_identity'] for c in cases),
            'key_identity_controls': sum(c['key_identity'] for c in cases), **decision})
        functional_all &= functional
    eligible = functional_all and all(s['length_comparison_eligible'] for s in summaries)
    gate = all(s['publisher_strictly_exceeds'] for s in summaries) if eligible else None
    report = {'experiment_id': 'scaffold_specificity_v47', 'outcome': 'publisher_exceeds_both_windows' if gate is True else 'publisher_not_strictly_specific' if gate is False else 'unavailable',
              'network_requests': 0, 'new_pdf_extractions': 0, 'reference_lcs': cfg['reference_lcs'], 'numeric_budget': cfg['numeric_budget'],
              'comparator_denominator': len(summaries), 'comparators': summaries, 'functional_checks_passed': functional_all,
              'specificity_comparison_eligible': eligible, 'registered_specificity_gate': gate,
              'opaque_residual_structural_assays': 2, 'opaque_lexical_or_semantic_scores': 0,
              'semantic_labels_admitted': 0, 'source_identities_admitted': 0, 'independent_reviews_admitted': 0,
              'untouched_test_units_admitted': 0, 'external_messages_sent': 0,
              'scientific_acceptance': None, 'semantic_evaluation_metrics': None}
    write('runs/000047_scaffold_specificity/report.json', report)
    outputs = sorted(str(p.relative_to(ROOT)) for p in (ROOT / 'data/v47').glob('*.json'))
    write('runs/000047_scaffold_specificity/manifest.json', {'experiment_id': report['experiment_id'], 'state': 'completed',
          'finished_at_utc': datetime.now(timezone.utc).isoformat(), 'outcome': report['outcome'],
          'input_hashes': cfg['input_hashes'] | {'experiments/scaffold_specificity_v47.json': sha('experiments/scaffold_specificity_v47.json')},
          'code_hashes': {p: sha(p) for p in code}, 'artifact_hashes': {},
          'output_hashes': {'report.json': sha('runs/000047_scaffold_specificity/report.json')} |
                           {str(Path('../../') / p): sha(p) for p in outputs}, 'verifier_written_after_scoring': True})
    print(json.dumps(report, indent=2))


if __name__ == '__main__': main()
