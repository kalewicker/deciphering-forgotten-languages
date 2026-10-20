"""Freeze and audit the single saved E60 response; no acquisition phase."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from fl_decipher.result_attribution_v61 import attribute, summarize

ROOT = Path(__file__).resolve().parents[1]
CFG = 'experiments/result_attribution_v61.json'
RUN = 'runs/000061_result_attribution'
CODE = ['src/fl_decipher/result_attribution_v61.py', 'scripts/result_attribution_v61.py', 'tests/test_result_attribution_v61.py']


def read(p): return json.loads((ROOT / p).read_text())
def sha(p): return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()
def utc(): return datetime.now(timezone.utc).isoformat()
def write(p, obj):
    path = ROOT / p; path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as f: json.dump(obj, f, indent=2, ensure_ascii=False); f.write('\n')


def main():
    cfg = read(CFG)
    assert not (ROOT / 'data/v61').exists() and not (ROOT / RUN).exists()
    assert cfg['network_request_budget'] == 0
    for p,h in cfg['input_hashes'].items(): assert sha(p) == h, p
    write('data/v61/preflight.json', {'sealed_at_utc': utc(), 'hashes': cfg['input_hashes'] | {p:sha(p) for p in CODE + [CFG]}})
    raw = (ROOT / cfg['raw']).read_bytes(); receipt = read(cfg['receipt'])
    assert read('data/v60/observation.json')['complete_direct_html_observation'] is True
    assert receipt['artifacts']['body.bin']['sha256'] == sha(cfg['raw']) and receipt['artifacts']['body.bin']['bytes'] == len(raw)
    result = attribute(raw, cfg['url'], cfg['schema'], read(cfg['prior_registry']))
    old = read('data/v60/layout.json')['anchors']; ledger = result['anchor_ledger']
    assert len(old) == len(ledger) == 115
    for a,b in zip(old,ledger):
        for k in ['anchor_index','dom_tag_index','href','text','resolved_url']: assert a[k] == b[k], (a['anchor_index'],k)
        assert a['article_key_diagnostic'] == b['strict_article_key']
    write('data/v61/attribution.json', result)
    report = summarize(result); write(RUN + '/report.json', report)
    files = sorted(str(p.relative_to(ROOT)) for p in (ROOT / 'data/v61').rglob('*.json'))
    write(RUN + '/manifest.json', {'experiment_id': 'result_attribution_v61', 'state': 'completed', 'finished_at_utc': utc(),
        'input_hashes': cfg['input_hashes'] | {CFG:sha(CFG)}, 'code_hashes': {p:sha(p) for p in CODE},
        'output_hashes': {'report.json':sha(RUN + '/report.json')} | {str(Path('../../') / p):sha(p) for p in files},
        'verifier_written_after_audit': True})
    print(json.dumps(report, indent=2))


if __name__ == '__main__': main()
