"""Prepare or execute exactly one memory-disabled Codex packet review."""
import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import uuid
import zipfile

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data/v72'
RUN = ROOT / 'runs/000072_automated_packet_review'
PACKET = ROOT / 'data/v25/packets/risk_math.zip'


def digest(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def write(path, obj):
    with Path(path).open('x') as stream:
        json.dump(obj, stream, indent=2)
        stream.write('\n')


def prepare():
    DATA.mkdir()
    RUN.mkdir()
    workspace = Path(tempfile.mkdtemp(prefix='fl-review-v72-', dir='/private/tmp'))
    with zipfile.ZipFile(PACKET) as archive:
        names = archive.namelist()
        assert len(names) == len(set(names)) == 9
        for name in names:
            assert not Path(name).is_absolute() and '..' not in Path(name).parts
        archive.extractall(workspace)
    manifest_bytes = (workspace / 'material_manifest.json').read_bytes()
    manifest = json.loads(manifest_bytes)
    assert manifest['nominee_id'] == 'risk_math'
    assert manifest['publisher_pages_one_based'] == [1, 2, 3]
    assert set(names) == set(manifest['members']) | {
        'material_manifest.json', 'review_return_template.json'}
    for name, entry in manifest['members'].items():
        content = (workspace / name).read_bytes()
        assert len(content) == entry['bytes'] and sha256(content).hexdigest() == entry['sha256']
    for name, length in manifest['text_code_point_lengths'].items():
        assert len((workspace / name).read_bytes().decode('utf-8')) == length
    template = json.loads((workspace / 'review_return_template.json').read_text())
    assert template['packet_manifest_sha256'] == sha256(manifest_bytes).hexdigest()
    review_id = 'fl-risk-v72-' + str(uuid.uuid4())
    prompt = (ROOT / 'experiments/automated_packet_review_v72_prompt.md').read_text().replace(
        '{review_id}', review_id)
    (DATA / 'review_prompt.txt').write_text(prompt)
    cli = shutil.which('codex')
    assert cli
    filesystem = '{":root"="read", "/Users/kalewicker"="deny", ' + (
        '"/private/tmp"="deny", "' + str(workspace) + '"="read"}')
    config = [
        'default_permissions="fl_review"',
        'permissions.fl_review.filesystem=' + filesystem,
        'permissions.fl_review.network.enabled=false',
        'approval_policy="never"',
        'memories.use_memories=false', 'memories.generate_memories=false',
        'features.memories=false', 'features.hooks=false',
        'features.plugins=false', 'features.apps=false',
        'features.multi_agent=false', 'features.shell_snapshot=false',
        'features.browser_use=false', 'features.computer_use=false',
        'web_search="disabled"', 'project_doc_max_bytes=0',
    ]
    args = [cli, '--no-daemon', 'exec', '--ignore-user-config', '--ephemeral',
            '--strict-config', '--skip-git-repo-check', '--json', '-C', str(workspace),
            '-o', str(DATA / 'review_return_raw.txt')]
    for setting in config:
        args.extend(['-c', setting])
    for page in (1, 2, 3):
        args.extend(['--image', str(workspace / f'pages/page_{page:03}.png')])
    args.append('-')
    inputs = [
        'experiments/automated_packet_review_v72.md',
        'experiments/automated_packet_review_v72_prompt.md',
        'scripts/automated_packet_review_v72.py',
        'data/v25/packets/risk_math.zip', 'reports/000025_deliverable_seal.json',
        'reports/000071_deliverable_seal.json', 'data/v72/review_prompt.txt']
    registration = {
        'experiment_id': 'automated_packet_review_v72',
        'registered_at_utc': datetime.now(timezone.utc).isoformat(),
        'review_id': review_id, 'workspace': str(workspace),
        'cli_version': subprocess.check_output([cli, '--version'], text=True).strip(),
        'cli_args': args, 'config': config,
        'model_review_attempt_budget': 1, 'timeout_seconds': 900,
        'input_hashes': {p: digest(ROOT / p) for p in inputs},
        'material_copy_hashes': {p: digest(workspace / p) for p in names},
        'independent_scientific_review_admitted': False,
        'benchmark_requirement_unchanged': True,
    }
    write(ROOT / 'experiments/automated_packet_review_v72.json', {
        k: v for k, v in registration.items() if k not in ('workspace', 'cli_args', 'config')})
    registration['input_hashes']['experiments/automated_packet_review_v72.json'] = digest(
        ROOT / 'experiments/automated_packet_review_v72.json')
    write(DATA / 'preflight.json', registration)
    print(json.dumps({'state': 'prepared', 'review_id': review_id, 'workspace': str(workspace)}))


def run():
    cfg = json.loads((DATA / 'preflight.json').read_text())
    for path, expected in cfg['input_hashes'].items():
        assert digest(ROOT / path) == expected, path
    workspace = Path(cfg['workspace'])
    for path, expected in cfg['material_copy_hashes'].items():
        assert digest(workspace / path) == expected, path
    assert not (DATA / 'attempt_started.json').exists(), 'One attempt already started'
    cli = cfg['cli_args'][0]
    # Only return booleans. Never print memory/project contents if restrictions fail.
    probe = '''import json,pathlib
result={}
for name,path in [('packet','material_manifest.json'),
 ('memory','/Users/kalewicker/.codex/memories/MEMORY.md'),
 ('history','/Users/kalewicker/Documents/forgotten languages/reports/000071_interpretation.md'),
 ('other_tmp','/private/tmp/fl-v71-export-path')]:
 try:
  with open(path,'rb') as stream:stream.read(1)
  result[name+'_readable']=True
 except PermissionError:result[name+'_readable']=False
try:
 with open('write_probe','x') as stream:stream.write('probe')
 result['packet_writable']=True
except PermissionError:result['packet_writable']=False
print(json.dumps(result))
'''
    probe_args = [cli, 'sandbox', '-C', str(workspace), '-P', 'fl_review']
    for setting in cfg['config'][:3]:
        probe_args.extend(['-c', setting])
    probe_args.extend(['--', '/usr/bin/python3', '-c', probe])
    result = subprocess.run(probe_args, capture_output=True, text=True, timeout=30)
    write(DATA / 'isolation_probe.json', {
        'args': probe_args, 'exit_code': result.returncode,
        'stdout': result.stdout, 'stderr': result.stderr,
        'recorded_at_utc': datetime.now(timezone.utc).isoformat()})
    assert result.returncode == 0, 'Isolation probe failed; no reviewer launched'
    observed = json.loads(result.stdout)
    assert observed == {'packet_readable': True, 'memory_readable': False,
                        'history_readable': False, 'other_tmp_readable': False,
                        'packet_writable': False}, observed
    write(DATA / 'attempt_started.json', {
        'started_at_utc': datetime.now(timezone.utc).isoformat(),
        'preflight_sha256': digest(DATA / 'preflight.json')})
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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['prepare', 'run'])
    args = parser.parse_args()
    prepare() if args.mode == 'prepare' else run()
