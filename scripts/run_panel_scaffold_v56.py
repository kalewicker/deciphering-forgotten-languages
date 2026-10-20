"""Run the registered five-page numeric scaffold panel without new acquisition."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from fl_decipher.cohort_scope_v52 import extract_scope
from fl_decipher.panel_scaffold_v56 import assessment, panel_decision, representation
from fl_decipher.scaffold_v46 import anchors, merged, residuals

ROOT = Path(__file__).resolve().parents[1]
CFG = 'experiments/panel_scaffold_v56.json'
RUN = 'runs/000056_panel_scaffold'
CODE = ['src/fl_decipher/panel_scaffold_v56.py', 'scripts/run_panel_scaffold_v56.py', 'tests/test_panel_scaffold_v56.py']


def read(p): return json.loads((ROOT / p).read_text())
def sha(p): return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()
def utc(): return datetime.now(timezone.utc).isoformat()
def write(p, value):
    path = ROOT / p; path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as stream: json.dump(value, stream, indent=2, ensure_ascii=False); stream.write('\n')


def main():
    cfg = read(CFG)
    assert not (ROOT / 'data/v56').exists() and not (ROOT / RUN).exists()
    for p, h in cfg['input_hashes'].items(): assert sha(p) == h, p
    assert len(cfg['pages']) == 5 and cfg['comparator_denominator'] == 4
    write('data/v56/preflight.json', {'sealed_at_utc': utc(), 'hashes': cfg['input_hashes'] | {p: sha(p) for p in CODE + [CFG]}})
    target = read('data/v38/target_export.json')['text']; queries = read('data/v39/frozen_queries.json')['queries']
    assert len(queries) == 8
    for q in queries: assert target[slice(*q['span'])] == q['text']
    assert target.count(cfg['bibliography_marker']) == 1 and target.index(cfg['bibliography_marker']) == cfg['bibliography_start'] == 7332
    ledger = [{'reason': 'title_header', 'span': [0, queries[0]['span'][0]]}]
    ledger += [{'reason': q['quote_id'], 'span': q['span']} for q in queries]
    ledger += [{'reason': 'bibliography', 'span': [cfg['bibliography_start'], len(target)]}]
    masks = merged([r['span'] for r in ledger], len(target)); units = [{'unit': i, 'span': s} for i, s in enumerate(residuals(masks, len(target)))]
    old_scope = read('data/v46/scope.json'); old_inventory = read('data/v46/inventory.json'); old_assessment = read('data/v46/assessment.json')
    assert ledger == old_scope['target_mask_ledger'] and masks == old_scope['target_masks'] and units == old_scope['target_units']
    inv = anchors(target, units, masks); assert inv == old_inventory['target']; left = inv['anchors']
    write('data/v56/target.json', {'mask_ledger': ledger, 'masks': masks, 'units': units, 'inventory': inv})
    rows = []; assessments = []; continuity = False
    for spec in cfg['pages']:
        saved = read(spec['scope']); receipt = read(spec['receipt']); raw = (ROOT / spec['raw']).read_bytes()
        assert sha(spec['raw']) == receipt['artifacts']['body.bin']['sha256'] and len(raw) == receipt['artifacts']['body.bin']['bytes']
        scope = extract_scope(raw, saved['body_text'], cfg['source_selector']); assert scope == saved
        rep = representation(scope); write(f"data/v56/{spec['id']}_representation.json", rep)
        result = assessment(left, rep, cfg) if rep['available'] else None
        write(f"data/v56/{spec['id']}_assessment.json", result); assessments.append(result)
        if spec['id'] == 'reference_v42':
            assert result is not None
            assert rep['units'] == old_scope['source_units'] and rep['quote_mask_ledger'] == old_scope['source_mask_ledger'] and rep['quote_masks'] == old_scope['source_masks']
            assert rep['inventory'] == old_inventory['source'] and result['observed']['whole'] == old_assessment['observed']['number']
            assert result['observed']['whole']['source_count'] == cfg['numeric_budget'] == 11
            for new, old in zip(result['controls'], old_assessment['controls'], strict=True):
                for k in ['family', 'draw', 'anchor_order', 'unit_order', 'index_identity', 'key_identity', 'bag_preserved', 'index_inventory_preserved']: assert new[k] == old[k]
                assert new['whole'] == old['scores']['number']
            continuity = True
        rows.append({'id': spec['id'], 'url': spec['url'], 'available': rep['available'], 'paragraph_runs': len(rep['units']),
            'paragraph_run_characters': sum(len(u['text']) for u in rep['units']), 'source_quote_masks': len(rep['quote_mask_ledger']),
            'unsupported_quote_units': rep['unsupported_quote_units'],
            'quote_mask_characters': sum(b - a for a, b in rep['quote_masks']),
            'whole': result['observed']['whole'] if result else None,
            'capped_numeric_width': result['observed']['capped_scan']['capped_width'] if result else None,
            'observed_window_count': result['observed']['capped_scan']['window_count'] if result else None,
            'maximum_capped_lcs': result['observed']['capped_scan']['maximum_lcs'] if result else None,
            'maximizing_starts': result['observed']['capped_scan']['maximizing_starts'] if result else None,
            'control_denominator': len(result['controls']) if result else 0,
            **({k: result[k] for k in ['functional_checks_passed', 'numeric_family_maxima', 'within_page_order_eligible',
                'within_page_order_separated', 'control_ties', 'controls_greater', 'index_identity_controls', 'key_identity_controls']} if result else {})})
    decisions = panel_decision(assessments[0], assessments[1:], cfg['minimum_shared_numeric_types'])
    report = {'experiment_id': 'panel_scaffold_v56', 'page_denominator': 5, 'comparator_denominator': 4, 'pages': rows,
        **decisions, 'reference_e46_continuity_verified': continuity, 'numeric_budget': cfg['numeric_budget'],
        'target_numeric_count': sum(r['kind'] == 'number' for r in left), 'target_residual_units': len(units),
        'controls_per_available_page': 34, 'registered_control_budget': 170,
        'controls_evaluated': sum(len(a['controls']) for a in assessments if a is not None),
        'all_observed_and_control_windows_evaluated': sum(a['observed']['capped_scan']['window_count'] + sum(c['capped_scan']['window_count'] for c in a['controls']) for a in assessments if a is not None),
        'network_requests': 0, 'new_acquisitions': 0, 'opaque_lexical_or_semantic_scores': 0,
        'source_identities_admitted': 0, 'independent_reviews_admitted': 0, 'untouched_test_units_admitted': 0,
        'natural_benchmark_capacity_met': False, 'scientific_acceptance': None, 'semantic_evaluation_metrics': None}
    write(RUN + '/report.json', report)
    outputs = sorted(str(p.relative_to(ROOT)) for p in (ROOT / 'data/v56').glob('*.json'))
    write(RUN + '/manifest.json', {'experiment_id': 'panel_scaffold_v56', 'state': 'completed', 'finished_at_utc': utc(),
        'input_hashes': cfg['input_hashes'] | {CFG: sha(CFG)}, 'code_hashes': {p: sha(p) for p in CODE},
        'output_hashes': {'report.json': sha(RUN + '/report.json')} | {str(Path('../../') / p): sha(p) for p in outputs},
        'verifier_written_after_scoring': True})
    print(json.dumps({k: v for k, v in report.items() if k != 'pages'}, indent=2))
    for row in rows: print(json.dumps(row, ensure_ascii=False))


if __name__ == '__main__': main()
