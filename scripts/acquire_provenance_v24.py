"""One-shot, exactly three registered standard HTTPS client probes."""
from pathlib import Path
import json
import subprocess
import sys
from fl_decipher.provenance_v24 import acquire_child, dump, fingerprint, sha, utc

ROOT = Path(__file__).resolve().parents[1]


def main():
    cfg = json.loads((ROOT/'experiments/kamri_provenance_v24.json').read_text())
    seal = json.loads((ROOT/'data/v24/preflight.json').read_text())
    for p, h in seal['input_hashes'].items() | seal['code_hashes'].items():
        assert sha((ROOT/p).read_bytes()) == h, p
    if len(sys.argv) == 3 and sys.argv[1] == '--route':
        route = next(r for r in cfg['routes'] if r['id'] == sys.argv[2])
        acquire_child(ROOT/'data/v24/acquisition'/route['id'], route, cfg)
        return
    assert len(sys.argv) == 1
    out = ROOT/'data/v24/acquisition';out.mkdir(exist_ok=False)
    for route in cfg['routes']:
        directory = out/route['id'];directory.mkdir()
        started = utc();deadline = False
        try:
            proc = subprocess.run([sys.executable, str(Path(__file__).resolve()), '--route', route['id']],
                                  capture_output=True, timeout=cfg['total_timeout_seconds'])
            code, stdout, stderr = proc.returncode, proc.stdout, proc.stderr
        except subprocess.TimeoutExpired as error:
            deadline = True;code = None;stdout = error.stdout or b'';stderr = error.stderr or b''
        (directory/'stdout.txt').write_bytes(stdout);(directory/'stderr.txt').write_bytes(stderr)
        resultpath = directory/'child_result.json'
        result = json.loads(resultpath.read_text()) if resultpath.exists() else {
            'http_status': None, 'final_url': None, 'read_complete': False,
            'error': 'wall deadline expired' if deadline else 'child process failed'}
        body = directory/'body.bin'
        complete = (not deadline and code == 0 and result['http_status'] == 200
                    and result['read_complete'] and body.exists() and body.stat().st_size <= cfg['max_body_bytes'])
        receipt = {'route_id': route['id'], 'requested_url': route['url'], 'kind': route['kind'],
                   'started_at_utc': started, 'finished_at_utc': utc(), 'attempted': True,
                   'child_returncode': code, 'deadline_expired': deadline, **result,
                   'transport_complete': complete, 'body_representation': 'transfer-decoded entity; content encoding preserved',
                   'artifacts': {p.name: fingerprint(p.read_bytes()) for p in sorted(directory.iterdir()) if p.is_file()}}
        dump(directory/'receipt.json', receipt)
        print(json.dumps({k: receipt[k] for k in ['route_id', 'http_status', 'transport_complete', 'error']}), flush=True)


if __name__ == '__main__':
    main()
