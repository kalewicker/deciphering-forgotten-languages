"""Apply the registered development intake rule to all five frozen pages, offline."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from fl_decipher.cohort_scope_v52 import extract_scope
from fl_decipher.offline_intake_v54 import evaluate
from fl_decipher.routing_v53 import assess

ROOT = Path(__file__).resolve().parents[1]
CFG = 'experiments/offline_intake_v54.json'
RUN = 'runs/000054_offline_intake'
CODE = ['src/fl_decipher/offline_intake_v54.py', 'scripts/run_offline_intake_v54.py', 'tests/test_offline_intake_v54.py']


def read(p): return json.loads((ROOT / p).read_text())
def sha(p): return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()
def utc(): return datetime.now(timezone.utc).isoformat()
def write(p, value):
    path = ROOT / p; path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as stream: json.dump(value, stream, indent=2, ensure_ascii=False); stream.write('\n')


def main():
    cfg = read(CFG)
    assert not (ROOT / 'data/v54').exists() and not (ROOT / RUN).exists()
    assert cfg['network_request_budget'] == 0 and cfg['candidate_denominator'] == cfg['candidate_capacity_required'] == 4
    assert len(cfg['pages']) == 5 and cfg['pages'][0]['id'] == 'reference_v42'
    for p, h in cfg['input_hashes'].items(): assert sha(p) == h, p
    write('data/v54/preflight.json', {'sealed_at_utc': utc(), 'hashes': cfg['input_hashes'] | {p: sha(p) for p in CODE + [CFG]}})
    old = read('runs/000050_publisher_intake/report.json')
    assert old['ready_captures'] == 1 and old['intake_capacity_met'] is False
    route_cfg = read('experiments/routing_v53.json'); rows = []
    for spec in cfg['pages']:
        raw = (ROOT / spec['raw']).read_bytes(); receipt = read(spec['receipt'])
        assert receipt['artifacts']['body.bin']['sha256'] == sha(spec['raw'])
        assert receipt['artifacts']['body.bin']['bytes'] == len(raw)
        body = read(spec['observation'])[spec['body_field']]
        scope = extract_scope(raw, body, cfg['source_selector'])
        assert scope == read(spec['scope'])
        route = None
        if spec['route']:
            route_spec = next(r for r in route_cfg['routes'] if r['id'] == spec['id'])
            base = f"data/v53/acquisition/{spec['id']}"
            route = assess((ROOT / base / 'body.bin').read_bytes(), (ROOT / base / 'headers.txt').read_bytes(), read(base + '/receipt.json'), route_spec)
            assert route == read(spec['route'])
        row = evaluate(raw, receipt, spec, cfg, body, route)
        assert row['scope_error'] is None
        write(f"data/v54/{spec['id']}_decision.json", row); rows.append(row)
    candidates = rows[1:]; eligible = [r['id'] for r in candidates if r['development_capture_eligible']]
    count = len(eligible); capacity = count >= cfg['candidate_capacity_required']
    report = {'experiment_id': 'offline_intake_v54', 'page_denominator': 5,
        'candidate_denominator': 4, 'candidate_capacity_required': 4, 'eligible_development_candidates': count,
        'eligible_candidate_ids': eligible, 'development_intake_capacity_met': capacity,
        'candidate_shortage': max(0, 4 - count), 'reference_eligible_separate': rows[0]['development_capture_eligible'],
        'pages': rows, 'v50_ready_captures_unchanged': 1, 'v50_intake_capacity_met_unchanged': False,
        'newly_eligible_vs_v50_ids': [r['id'] for r in candidates if r['development_capture_eligible'] and not r['v50_ready_unchanged']],
        'previously_ready_now_ineligible_ids': [r['id'] for r in candidates if not r['development_capture_eligible'] and r['v50_ready_unchanged']],
        'natural_benchmark_qualifying_works_from_intake': 0, 'natural_benchmark_capacity_met': False,
        'metadata_scope_audit_sequence_closed': True, 'network_requests': 0, 'browser_renders': 0,
        'new_structural_scores': 0, 'new_lexical_or_semantic_scores': 0, 'accepted_source_identities': 0,
        'independent_reviews_admitted': 0, 'untouched_test_units_admitted': 0,
        'scientific_acceptance': None, 'semantic_evaluation_metrics': None}
    write(RUN + '/report.json', report)
    outputs = sorted(str(p.relative_to(ROOT)) for p in (ROOT / 'data/v54').glob('*.json'))
    write(RUN + '/manifest.json', {'experiment_id': 'offline_intake_v54', 'state': 'completed', 'finished_at_utc': utc(),
        'input_hashes': cfg['input_hashes'] | {CFG: sha(CFG)}, 'code_hashes': {p: sha(p) for p in CODE},
        'output_hashes': {'report.json': sha(RUN + '/report.json')} | {str(Path('../../') / p): sha(p) for p in outputs},
        'verifier_written_after_decision': True})
    print(json.dumps({k: v for k, v in report.items() if k != 'pages'}, indent=2))
    for row in rows: print(row['id'], row['development_capture_eligible'], row['unmet'], row['paragraph_run_count'], row['paragraph_run_characters'])


if __name__ == '__main__': main()
