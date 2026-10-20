"""Prepare, attempt exactly one GET, then inspect its saved response offline."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
from fl_decipher.native_probe_v60 import command, inventory, observation, summarize

ROOT = Path(__file__).resolve().parents[1]
CFG = 'experiments/native_probe_v60.json'
DATA = 'data/v60'
DEST = ROOT / DATA / 'acquisition/search'
RUN = 'runs/000060_native_probe'
CODE = ['src/fl_decipher/native_probe_v60.py', 'scripts/native_probe_v60.py', 'tests/test_native_probe_v60.py']


def utc(): return datetime.now(timezone.utc).isoformat()
def read(p): return json.loads((ROOT / p).read_text())
def sha(p): return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()
def write(p, obj):
    path = ROOT / p; path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as f: json.dump(obj, f, indent=2, ensure_ascii=False); f.write('\n')
def data_bytes(name):
    path = DEST / name
    return path.read_bytes() if path.exists() else b''


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('phase', choices=['prepare', 'probe', 'inspect'])
    args = parser.parse_args(); cfg = read(CFG); contract = cfg['probe_contract']
    if args.phase == 'prepare':
        assert not (ROOT / DATA).exists() and not (ROOT / RUN).exists()
        prior = read('experiments/native_discovery_v59a.json')['future_probe_contract']
        assert contract == prior and read('runs/000059_native_discovery/report.json')['uniform_saved_declaration_gate']
        assert contract['url'] == 'https://physicsworld.com/?s=ANITA' and cfg['network_attempt_budget'] == 1
        for p, h in cfg['input_hashes'].items(): assert sha(p) == h, p
        write(DATA + '/preflight.json', {'sealed_at_utc': utc(), 'hashes': cfg['input_hashes'] | {p: sha(p) for p in CODE + [CFG]},
            'registered_command': command(DEST, contract), 'research_attempt_budget': 1})
        print(json.dumps({'state': 'prepared', 'network_attempt_budget': 1, 'url': contract['url']})); return
    pre = read(DATA + '/preflight.json')
    for p, h in pre['hashes'].items(): assert sha(p) == h, p
    if args.phase == 'probe':
        assert not DEST.exists() and not (ROOT / DATA / 'intent.json').exists()
        DEST.mkdir(parents=True, exist_ok=False); cmd = command(DEST, contract)
        assert cmd == pre['registered_command']
        write(DATA + '/intent.json', {'started_at_utc': utc(), 'preflight_sha256': sha(DATA + '/preflight.json'),
              'request_method': 'GET', 'request_url': contract['url'], 'command': cmd, 'attempt_index': 0,
              'attempt_budget': 1, 'redirect_budget': 0, 'retry_budget': 0})
        error = None
        try:
            result = subprocess.run(cmd, capture_output=True)
            stdout, stderr, code = result.stdout, result.stderr, result.returncode
        except OSError as exc:
            stdout, stderr, code = b'', str(exc).encode(), None; error = type(exc).__name__
        (DEST / 'curl_stdout.bin').write_bytes(stdout); (DEST / 'curl_stderr.bin').write_bytes(stderr)
        try: telemetry = json.loads(stdout)
        except (ValueError, TypeError): telemetry = {}
        if not isinstance(telemetry, dict): telemetry = {}
        artifacts = {p.name: {'sha256': hashlib.sha256(p.read_bytes()).hexdigest(), 'bytes': p.stat().st_size}
                     for p in DEST.iterdir() if p.is_file()}
        complete = bool(code == 0 and isinstance(telemetry.get('http_code'), int) and 100 <= telemetry['http_code'] <= 599
                        and 'body.bin' in artifacts and artifacts['body.bin']['bytes'] <= contract['max_body_bytes'])
        receipt = {'attempt_index': 0, 'requested_url': contract['url'], 'request_method': 'GET', 'command': cmd,
            'started_at_utc': read(DATA + '/intent.json')['started_at_utc'], 'finished_at_utc': utc(),
            'curl_returncode': code, 'spawn_error': error, 'http_status': telemetry.get('http_code'),
            'final_url': telemetry.get('url_effective'), 'num_redirects': telemetry.get('num_redirects'),
            'content_type': telemetry.get('content_type'), 'transport_complete': complete,
            'body_representation': 'curl transfer/content-decoded response body (--compressed)', 'artifacts': artifacts}
        write(DATA + '/acquisition/search/receipt.json', receipt)
        print(json.dumps({'state': 'attempt_recorded', 'http_status': receipt['http_status'], 'curl_returncode': code,
              'body_bytes': artifacts.get('body.bin', {}).get('bytes'), 'num_redirects': receipt['num_redirects']})); return
    assert not (ROOT / RUN).exists()
    receipt = read(DATA + '/acquisition/search/receipt.json')
    for name, info in receipt['artifacts'].items():
        assert sha(str((DEST / name).relative_to(ROOT))) == info['sha256'] and (DEST / name).stat().st_size == info['bytes']
    raw = data_bytes('body.bin'); headers = data_bytes('headers.txt')
    layout = inventory(raw, contract['url'], cfg['query'])
    observed = observation(raw, headers, receipt, contract, cfg['challenge_signatures'])
    write(DATA + '/layout.json', layout); write(DATA + '/observation.json', observed)
    report = summarize(layout, observed, receipt)
    write(RUN + '/report.json', report)
    files = sorted(str(p.relative_to(ROOT)) for p in (ROOT / DATA).rglob('*') if p.is_file())
    write(RUN + '/manifest.json', {'experiment_id': 'native_probe_v60', 'state': 'completed', 'finished_at_utc': utc(),
        'input_hashes': cfg['input_hashes'] | {CFG: sha(CFG)}, 'code_hashes': {p: sha(p) for p in CODE},
        'output_hashes': {'report.json': sha(RUN + '/report.json')} | {str(Path('../../') / p): sha(p) for p in files},
        'verifier_written_after_probe': True})
    print(json.dumps(report, indent=2))


if __name__ == '__main__': main()
