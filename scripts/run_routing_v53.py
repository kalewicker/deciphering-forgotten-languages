"""Capture the four exact frozen alternate URL routes once, preserving all failures."""
import hashlib
import json
from pathlib import Path
from fl_decipher.routing_v53 import assess, capture, utc

ROOT = Path(__file__).resolve().parents[1]
CODE = ['src/fl_decipher/routing_v53.py', 'scripts/run_routing_v53.py', 'tests/test_routing_v53.py']
CFG = 'experiments/routing_v53.json'
RUN = 'runs/000053_routing'


def read(p): return json.loads((ROOT / p).read_text())
def sha(p): return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()
def write(p, obj):
    path = ROOT / p; path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as stream: json.dump(obj, stream, indent=2, ensure_ascii=False); stream.write('\n')


def main():
    cfg = read(CFG)
    assert not (ROOT / 'data/v53').exists() and not (ROOT / RUN).exists()
    assert cfg['route_budget'] == len(cfg['routes']) == 4
    for p, h in cfg['input_hashes'].items(): assert sha(p) == h, p
    intake = read('runs/000050_publisher_intake/report.json')
    assert intake['ready_captures'] == 1 and not intake['intake_capacity_met']
    write('data/v53/preflight.json', {'sealed_at_utc': utc(),
          'hashes': cfg['input_hashes'] | {p: sha(p) for p in CODE + [CFG]}})
    rows = []
    for spec in cfg['routes']:
        old = read(spec['old_identity'])['identity_inventory']
        assert [r['value'] for r in old if r['channel'] == 'og_url'] == [spec['og_url']]
        assert [r['value'] for r in old if r['channel'] == 'canonical'] == [spec['canonical_url']]
        assert sha(spec['old_raw']) == spec['old_body_sha256']
        receipt = capture(ROOT / 'data/v53/acquisition', spec, cfg['limits'])
        dest = ROOT / 'data/v53/acquisition' / spec['id']
        body = (dest / 'body.bin').read_bytes() if (dest / 'body.bin').exists() else b''
        headers = (dest / 'headers.txt').read_bytes() if (dest / 'headers.txt').exists() else b''
        row = assess(body, headers, receipt, spec)
        write(f"data/v53/{spec['id']}_route.json", row); rows.append(row)
    supported = sum(r['current_alias_supported'] for r in rows)
    report = {'experiment_id': 'routing_v53', 'route_denominator': 4, 'routes_attempted': len(rows),
        'current_alias_supported': supported, 'unresolved_routes': 4 - supported,
        'redirect_routes': sum(r['category'] == 'observed_redirect_to_canonical' for r in rows),
        'served_alias_routes': sum(r['category'] == 'observed_served_alias' for r in rows),
        'all_four_current_alias_gate': supported == 4, 'routes': rows,
        'v50_ready_captures_unchanged': 1, 'v50_intake_capacity_met_unchanged': False,
        'historical_routing_authenticated': False, 'prior_strict_url_diagnostics_rewritten': False,
        'new_candidate_readiness_admissions': 0, 'new_structural_scores': 0, 'new_semantic_scores': 0,
        'source_identities_admitted': 0, 'independent_reviews_admitted': 0, 'untouched_test_units_admitted': 0,
        'scientific_acceptance': None, 'semantic_evaluation_metrics': None}
    write(RUN + '/report.json', report)
    outputs = sorted(str(p.relative_to(ROOT)) for p in (ROOT / 'data/v53').rglob('*') if p.is_file())
    write(RUN + '/manifest.json', {'experiment_id': 'routing_v53', 'state': 'completed', 'finished_at_utc': utc(),
        'input_hashes': cfg['input_hashes'] | {CFG: sha(CFG)}, 'code_hashes': {p: sha(p) for p in CODE},
        'output_hashes': {'report.json': sha(RUN + '/report.json')} | {str(Path('../../') / p): sha(p) for p in outputs},
        'verifier_written_after_capture': True})
    print(json.dumps({k: v for k, v in report.items() if k != 'routes'}, indent=2))
    for row in rows: print(row['id'], row['category'], row['http_status'], row['num_redirects'])


if __name__ == '__main__': main()
