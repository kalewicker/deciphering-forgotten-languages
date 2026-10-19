"""Registered citation masks, fixed parent draws and exhaustive numeric scans."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from fl_decipher.citation_sensitivity_v49 import BRACKET_PATTERN, citation_masks, filter_controls, filter_inventory
from fl_decipher.scaffold_v46 import anchors, metrics
from fl_decipher.scaffold_specificity_v47 import decisions, paper_inventory, paper_scope, windows

ROOT = Path(__file__).resolve().parents[1]
CODE = ['src/fl_decipher/citation_sensitivity_v49.py', 'scripts/run_citation_sensitivity_v49.py', 'tests/test_citation_sensitivity_v49.py']


def read(p): return json.loads((ROOT / p).read_text())
def sha(p): return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()
def write(p, value):
    path = ROOT / p; path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as stream: json.dump(value, stream, indent=2, ensure_ascii=False); stream.write('\n')


def main():
    cfgpath = 'experiments/citation_sensitivity_v49.json'; cfg = read(cfgpath)
    assert not (ROOT / 'data/v49').exists() and not (ROOT / 'runs/000049_citation_sensitivity').exists()
    for p, h in cfg['input_hashes'].items(): assert sha(p) == h, p
    assert cfg['bracket_pattern'] == BRACKET_PATTERN
    write('data/v49/preflight.json', {'sealed_at_utc': datetime.now(timezone.utc).isoformat(),
          'hashes': cfg['input_hashes'] | {p: sha(p) for p in CODE + [cfgpath]}})
    ref = read('data/v47/reference.json'); target = read('data/v38/target_export.json')['text']
    scope = read('data/v46/scope.json'); ti = anchors(target, scope['target_units'], scope['target_masks'])
    assert ti == ref['target_inventory'] == read('data/v46/inventory.json')['target']
    left = ti['anchors']; assert ref['publisher_observed']['ordered_lcs'] == cfg['reference_lcs'] == 6
    assert ref['publisher_observed']['source_count'] == cfg['numeric_budget'] == 11
    selfcopy_target = metrics(left, left)['number']; assert selfcopy_target['ordered_lcs'] == selfcopy_target['source_count'] == 10
    old_report = read('runs/000047_scaffold_specificity/report.json')
    write('data/v49/reference.json', {'target_inventory': ti, 'publisher_observed': ref['publisher_observed'],
          'publisher_controls': ref['publisher_controls'], 'v47_comparators': old_report['comparators']})
    summaries = []; audit_retention = []
    audit = read('data/v48/selection.json')['occurrences']
    for spec in cfg['sources']:
        export = read(spec['export']); text, us = paper_scope(export, sha(spec['pdf']), spec['pages'])
        old_inv = read(spec['inventory']); full = paper_inventory(text, us)
        assert old_inv == {'units': us, 'joined_text_sha256': hashlib.sha256(text.encode()).hexdigest(), 'inventory': full}
        boundary_page = export['pages'][spec['boundary']['page'] - 1]
        assert sha(boundary_page['image']) == spec['boundary_image_sha256'] == boundary_page['image_sha256']
        mask = citation_masks(text, us, spec['boundary']); inv = filter_inventory(full['anchors'], mask['masks']); right = inv['anchors']
        write(f"data/v49/{spec['id']}_scope.json", {'units': us, **mask})
        write(f"data/v49/{spec['id']}_inventory.json", inv)
        parent = read(spec['assessment']); cases = filter_controls(full['anchors'], right, parent['controls']); assert len(cases) == 34
        observed = {'whole': metrics(left, right)['number'], 'window_scan': windows(left, right, cfg['numeric_budget'])}
        for c in cases:
            ordered = [right[i] for i in c['anchor_order']]
            c['whole'] = metrics(left, ordered)['number']; c['window_scan'] = windows(left, ordered, cfg['numeric_budget'])
        sc = metrics(right, right)['number']
        functional = (sc['ordered_lcs'] == sc['source_count'] == sc['bag_capacity']
            and all(c['bag_preserved'] and c['index_inventory_preserved'] for c in cases)
            and len(right) + len(inv['removed_anchors']) == len(full['anchors'])
            and all(not (r['span'][0] < b and r['span'][1] > a) for r in right for a, b in mask['masks'])
            and all(s['window_count'] == max(0, observed['whole']['source_count'] - 10) for s in [observed['window_scan']] + [c['window_scan'] for c in cases]))
        decision = decisions(cfg['reference_lcs'], observed, cases, functional, cfg['minimum_shared_numeric_types'])
        write(f"data/v49/{spec['id']}_assessment.json", {'observed': observed, 'controls': cases, 'functional_checks_passed': functional, 'decision': decision})
        old = next(r for r in old_report['comparators'] if r['id'] == spec['id'])
        summaries.append({'id': spec['id'], 'pages': len(us), 'reference_start': mask['reference_start'],
            'inline_numeric_bracket_masks': len(mask['ledger']) - 1, 'reference_tail_characters': len(text) - mask['reference_start'],
            'original_mixed_anchor_count': len(full['anchors']), 'retained_mixed_anchor_count': len(right),
            'removed_mixed_anchor_count': len(inv['removed_anchors']), 'whole': observed['whole'],
            'window_count': observed['window_scan']['window_count'], 'maximum_window_lcs': observed['window_scan']['maximum_lcs'],
            'maximizing_starts': observed['window_scan']['maximizing_starts'], 'control_denominator': 34,
            'index_identity_controls': sum(c['index_identity'] for c in cases), 'key_identity_controls': sum(c['key_identity'] for c in cases),
            'functional_checks_passed': functional, 'v47_whole': old['whole'], 'v47_maximum_window_lcs': old['maximum_window_lcs'], **decision})
        retained_ids = {r['original_anchor_index'] for r in right}
        for r in audit:
            if r['source_id'] != spec['id']: continue
            reasons = sorted({m['reason'] for m in mask['ledger'] if r['span'][0] < m['span'][1] and r['span'][1] > m['span'][0]})
            audit_retention.append({'occurrence_id': r['occurrence_id'], 'source_id': spec['id'], 'value': r['value'],
                'page': r['page'], 'span': r['span'], 'retained': r['anchor_index'] in retained_ids, 'mask_reasons': reasons})
    assert len(audit_retention) == 13
    write('data/v49/audited_occurrence_retention.json', audit_retention)
    eligible = all(s['length_comparison_eligible'] for s in summaries)
    gate = all(s['publisher_strictly_exceeds'] for s in summaries) if eligible else None
    report = {'experiment_id': 'citation_sensitivity_v49', 'outcome': 'publisher_exceeds_both_masked_windows' if gate is True else 'publisher_not_strictly_specific_after_masking' if gate is False else 'unavailable',
        'reference_lcs': 6, 'numeric_budget': 11, 'comparator_denominator': 2, 'comparators': summaries,
        'functional_checks_passed': all(s['functional_checks_passed'] for s in summaries),
        'specificity_comparison_eligible': eligible, 'registered_specificity_gate': gate,
        'prior_audited_occurrences': 13, 'prior_audited_occurrences_retained': sum(r['retained'] for r in audit_retention),
        'prior_audited_occurrences_removed': sum(not r['retained'] for r in audit_retention),
        'network_requests': 0, 'new_pdf_extractions': 0, 'new_page_renders': 0, 'new_random_control_draws': 0,
        'opaque_residual_structural_assays': 2, 'opaque_lexical_or_semantic_scores': 0, 'semantic_labels_admitted': 0,
        'source_identities_admitted': 0, 'independent_reviews_admitted': 0, 'untouched_test_units_admitted': 0,
        'external_messages_sent': 0, 'scientific_acceptance': None, 'semantic_evaluation_metrics': None}
    write('runs/000049_citation_sensitivity/report.json', report)
    outputs = sorted(str(p.relative_to(ROOT)) for p in (ROOT / 'data/v49').glob('*.json'))
    write('runs/000049_citation_sensitivity/manifest.json', {'experiment_id': report['experiment_id'], 'state': 'completed',
        'finished_at_utc': datetime.now(timezone.utc).isoformat(), 'outcome': report['outcome'],
        'input_hashes': cfg['input_hashes'] | {cfgpath: sha(cfgpath)}, 'code_hashes': {p: sha(p) for p in CODE},
        'output_hashes': {'report.json': sha('runs/000049_citation_sensitivity/report.json')} |
            {str(Path('../../') / p): sha(p) for p in outputs}, 'verifier_written_after_scoring': True})
    print(json.dumps(report, indent=2))


if __name__ == '__main__': main()
