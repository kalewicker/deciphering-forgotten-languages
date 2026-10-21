"""E72 explicit memory/session-deny correction; refuses an unsafe launch."""
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess

from automated_packet_review_v72 import DATA, ROOT, digest, write


def main():
    cfg = json.loads((DATA / 'preflight_revision1.json').read_text())
    for p, h in cfg['input_hashes'].items():
        assert digest(ROOT / p) == h, p
    workspace = Path(cfg['workspace'])
    for p, h in cfg['material_copy_hashes'].items():
        assert digest(workspace / p) == h, p
    assert not (DATA / 'attempt_started.json').exists(), 'Review attempt already started'
    probe = '''import json
checks={}
paths=PROTECTED_PATHS
with open('material_manifest.json','rb') as stream:stream.read(1)
checks['packet_readable']=True
for name,path in paths.items():
 try:
  with open(path,'rb') as stream:stream.read(1)
  checks[name+'_readable']=True
 except PermissionError:checks[name+'_readable']=False
try:
 with open('write_probe','x') as stream:stream.write('probe')
 checks['packet_writable']=True
except PermissionError:checks['packet_writable']=False
print(json.dumps(checks))
'''.replace('PROTECTED_PATHS', repr(cfg['protected_probe_paths']))
    args = [cfg['cli_args'][0], 'sandbox', '-C', str(workspace), '-P', 'fl_review']
    for setting in cfg['config'][:3]:
        args.extend(['-c', setting])
    args.extend(['--', '/usr/bin/python3', '-c', probe])
    result = subprocess.run(args, capture_output=True, text=True, timeout=30)
    write(DATA / 'isolation_probe_revision1.json', {
        'args': args, 'exit_code': result.returncode, 'stdout': result.stdout,
        'stderr': result.stderr, 'recorded_at_utc': datetime.now(timezone.utc).isoformat()})
    assert result.returncode == 0, 'Probe failed; review not launched'
    expected = {'packet_readable': True, 'packet_writable': False}
    expected.update({key + '_readable': False for key in cfg['protected_probe_paths']})
    assert json.loads(result.stdout) == expected, 'Protected file still readable; review not launched'
    write(DATA / 'attempt_started.json', {
        'started_at_utc': datetime.now(timezone.utc).isoformat(),
        'preflight_sha256': digest(DATA / 'preflight_revision1.json')})
    with (DATA / 'events.jsonl').open('xb') as stdout, (DATA / 'stderr.txt').open('xb') as stderr:
        try:
            result = subprocess.run(cfg['cli_args'], input=(DATA / 'review_prompt.txt').read_bytes(),
                                    stdout=stdout, stderr=stderr, timeout=cfg['timeout_seconds'],
                                    cwd=workspace)
            code, timed_out = result.returncode, False
        except subprocess.TimeoutExpired:
            code, timed_out = None, True
    write(DATA / 'attempt_finished.json', {
        'finished_at_utc': datetime.now(timezone.utc).isoformat(),
        'exit_code': code, 'timed_out': timed_out,
        'return_present': (DATA / 'review_return_raw.txt').exists()})
    print(json.dumps({'exit_code': code, 'timed_out': timed_out,
                      'return_present': (DATA / 'review_return_raw.txt').exists()}))


if __name__ == '__main__':
    main()
