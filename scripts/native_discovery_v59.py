"""Freeze and audit saved declarations. This runner has no acquisition phase."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from fl_decipher.native_discovery_v59 import audit, summary

ROOT = Path(__file__).resolve().parents[1]
CFG = 'experiments/native_discovery_v59.json'
RUN = 'runs/000059_native_discovery'
CODE = ['src/fl_decipher/native_discovery_v59.py', 'scripts/native_discovery_v59.py', 'tests/test_native_discovery_v59.py']


def sha(p): return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()
def utc(): return datetime.now(timezone.utc).isoformat()
def read(p): return json.loads((ROOT / p).read_text())
def write(p, obj):
    path = ROOT / p; path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as stream: json.dump(obj, stream, indent=2, ensure_ascii=False); stream.write('\n')


def main():
    assert not (ROOT / 'data/v59').exists() and not (ROOT / RUN).exists()
    cfg = read(CFG)
    assert cfg['network_request_budget'] == 0 and len(cfg['pages']) == cfg['capture_denominator'] == 11
    for p, h in cfg['input_hashes'].items(): assert sha(p) == h, p
    write('data/v59/preflight.json', {'sealed_at_utc': utc(), 'hashes': cfg['input_hashes'] | {p: sha(p) for p in CODE + [CFG]}})
    rows = []
    for spec in cfg['pages']:
        receipt = read(spec['receipt']); raw = (ROOT / spec['raw']).read_bytes()
        assert receipt['transport_complete'] and receipt['artifacts']['body.bin'] == {'sha256': sha(spec['raw']), 'bytes': len(raw)}
        row = {'capture_id': spec['id'], 'raw_sha256': sha(spec['raw']), **audit(raw, spec['url'], cfg['query'])}
        write(f"data/v59/{spec['id']}_declarations.json", row); rows.append(row)
    result = summary(rows, cfg['query'])
    result['distinct_article_url_denominator'] = len({p['article_url'] for p in cfg['pages']})
    result['future_probe_contract'] = cfg['future_probe_contract']
    write(RUN + '/report.json', result)
    files = sorted(str(p.relative_to(ROOT)) for p in (ROOT / 'data/v59').rglob('*.json'))
    write(RUN + '/manifest.json', {'experiment_id': 'native_discovery_v59', 'state': 'completed', 'finished_at_utc': utc(),
        'input_hashes': cfg['input_hashes'] | {CFG: sha(CFG)}, 'code_hashes': {p: sha(p) for p in CODE},
        'output_hashes': {'report.json': sha(RUN + '/report.json')} | {str(Path('../../') / p): sha(p) for p in files},
        'verifier_written_after_audit': True})
    print(json.dumps(result, indent=2))


if __name__ == '__main__': main()
