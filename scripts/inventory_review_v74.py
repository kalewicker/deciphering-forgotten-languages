"""Prepare and execute the one fixed, memory-disabled inventory-assisted review."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import uuid
import zipfile

from automated_packet_review_v72 import ROOT, digest, write

DATA = ROOT / 'data/v74'
RUN = ROOT / 'runs/000074_inventory_review'


def prepare():
    DATA.mkdir()
    RUN.mkdir()
    workspace = Path(tempfile.mkdtemp(prefix='fl-review-v74-', dir='/private/tmp'))
    packet = ROOT / 'data/v25/packets/western_esoterism.zip'
    with zipfile.ZipFile(packet) as archive:
        names = archive.namelist()
        assert len(names) == len(set(names)) == 11
        assert all(not Path(n).is_absolute() and '..' not in Path(n).parts for n in names)
        archive.extractall(workspace)
    manifest = json.loads((workspace / 'material_manifest.json').read_text())
    assert manifest['nominee_id'] == 'western_esoterism'
    assert manifest['publisher_pages_one_based'] == list(range(90, 95))
    assert set(names) == set(manifest['members']) | {'material_manifest.json', 'review_return_template.json'}
    for name, record in manifest['members'].items():
        assert (workspace / name).stat().st_size == record['bytes']
        assert digest(workspace / name) == record['sha256']
    texts = {n: (workspace / n).read_bytes().decode('utf-8') for n in manifest['text_code_point_lengths']}
    assert {n: len(t) for n, t in texts.items()} == manifest['text_code_point_lengths']
    template = json.loads((workspace / 'review_return_template.json').read_text())
    assert template['packet_manifest_sha256'] == digest(workspace / 'material_manifest.json')
    appendix = json.loads((ROOT / 'data/v26/evidence_spans.json').read_text())
    rows = [r for r in appendix['pairs'] if r['packet'] == 'western_esoterism']
    assert [r['id'] for r in rows] == ['W1', 'W2', 'W3', 'W4', 'W5']
    descriptions = [
        'Presence of the displayed expression in the two supplied spans.',
        'Presence and order of the three displayed personal names; compare spelling and spacing explicitly.',
        'Presence of the displayed label in the body spans, first of an ordered three-clue sequence.',
        'Presence of the displayed name with its case difference, between W3 and W5.',
        'Presence of the displayed label with its case difference, after W3 and W4.']
    clues = []
    for row, description in zip(rows, descriptions, strict=True):
        for side, name in [('fl', 'fl_post.txt'), ('source', 'publisher_window.txt')]:
            s = row[side + '_span']
            assert texts[name][s['start']:s['end']] == s['text']
        clues.append({k: row[k] for k in ['id', 'fl_span', 'source_span', 'pdf_page']}
                     | {'observable_question': description})
    inventory = {'nominee_id': 'western_esoterism', 'prior_annotations_disclosed': True,
                 'source_relationship_or_meanings_validated': False,
                 'scope': 'Five dependent observable clues in one exposed work; conclusions and earlier review outputs excluded.',
                 'clues': clues}
    write(DATA / 'clue_inventory.json', inventory)
    shutil.copy2(DATA / 'clue_inventory.json', workspace / 'clue_inventory.json')
    outer = {'review': template, 'clue_dispositions': [
        {'clue_id': c['id'], 'disposition': None, 'evidence_pair_indices': [],
         'counterexample_indices': [], 'candidate_relationship_implication': None,
         'limitations': None} for c in clues]}
    write(DATA / 'assisted_return_template.json', outer)
    shutil.copy2(DATA / 'assisted_return_template.json', workspace / 'assisted_return_template.json')
    review_id = 'fl-western-v74-' + str(uuid.uuid4())
    prompt = (ROOT / 'experiments/inventory_review_v74_prompt.md').read_text().replace('{review_id}', review_id)
    (DATA / 'review_prompt.txt').write_text(prompt)
    cli = shutil.which('codex')
    assert cli
    fs = {':root': 'read', '/Users/kalewicker': 'deny', '/private/tmp': 'deny',
          str(workspace): 'read', '/Users/kalewicker/.codex/memories': 'deny',
          '/Users/kalewicker/.codex/sessions': 'deny'}
    table = '{' + ', '.join(json.dumps(k) + '=' + json.dumps(v) for k, v in fs.items()) + '}'
    config = ['default_permissions="fl_review"', 'permissions.fl_review.filesystem=' + table,
              'permissions.fl_review.network.enabled=false', 'approval_policy="never"',
              'memories.use_memories=false', 'memories.generate_memories=false',
              'features.memories=false', 'features.hooks=false', 'features.plugins=false',
              'features.apps=false', 'features.multi_agent=false', 'features.shell_snapshot=false',
              'features.browser_use=false', 'features.computer_use=false',
              'web_search="disabled"', 'project_doc_max_bytes=0']
    args = [cli, '--no-daemon', 'exec', '--ignore-user-config', '--ephemeral', '--strict-config',
            '--skip-git-repo-check', '--json', '-C', str(workspace), '-o', str(DATA / 'return_raw.json')]
    for setting in config:
        args += ['-c', setting]
    for page in range(90, 95):
        args += ['--image', str(workspace / f'pages/page_{page:03}.png')]
    args.append('-')
    protected = {'memory': '/Users/kalewicker/.codex/memories/MEMORY.md',
                 'summary': '/Users/kalewicker/.codex/memories/memory_summary.md',
                 'session': next(Path('/Users/kalewicker/.codex/sessions').glob('**/*.jsonl')).as_posix(),
                 'history': str(ROOT / 'reports/000073_interpretation.md'),
                 'other_tmp': '/private/tmp/fl-v73-export-path'}
    assert all(Path(p).is_file() for p in protected.values())
    inputs = ['experiments/inventory_review_v74.md', 'experiments/inventory_review_v74_prompt.md',
              'scripts/inventory_review_v74.py', 'scripts/automated_packet_review_v72.py',
              'data/v25/packets/western_esoterism.zip', 'data/v26/evidence_spans.json',
              'reports/000073_deliverable_seal.json', 'data/v74/clue_inventory.json',
              'data/v74/assisted_return_template.json', 'data/v74/review_prompt.txt']
    cfg = {'experiment_id': 'inventory_review_v74', 'registered_at_utc': datetime.now(timezone.utc).isoformat(),
           'review_id': review_id, 'nominee_id': 'western_esoterism', 'clue_ids': [c['id'] for c in clues],
           'model_attempt_budget': 1, 'timeout_seconds': 900, 'inventory_assisted': True,
           'cli_version': subprocess.check_output([cli, '--version'], text=True).strip(),
           'workspace': str(workspace), 'cli_args': args, 'config': config,
           'protected_probe_paths': protected,
           'material_copy_hashes': {str(p.relative_to(workspace)): digest(p)
                                    for p in sorted(workspace.rglob('*')) if p.is_file()},
           'input_hashes': {p: digest(ROOT / p) for p in inputs}}
    write(ROOT / 'experiments/inventory_review_v74.json', {k: v for k, v in cfg.items()
        if k not in ['workspace', 'cli_args', 'config', 'protected_probe_paths']})
    cfg['input_hashes']['experiments/inventory_review_v74.json'] = digest(ROOT / 'experiments/inventory_review_v74.json')
    write(DATA / 'preflight.json', cfg)
    print(json.dumps({'state': 'prepared', 'review_id': review_id, 'clue_ids': cfg['clue_ids']}))


def run():
    cfg = json.loads((DATA / 'preflight.json').read_text())
    for p, h in cfg['input_hashes'].items():
        assert digest(ROOT / p) == h, p
    for p, h in cfg['material_copy_hashes'].items():
        assert digest(Path(cfg['workspace']) / p) == h, p
    assert not (DATA / 'attempt_started.json').exists(), 'One review attempt already started'
    probe = '''import json
result={}
with open('clue_inventory.json','rb') as stream:stream.read(1)
result['inventory_readable']=True
for name,path in PROTECTED.items():
 try:
  with open(path,'rb') as stream:stream.read(1)
  result[name+'_readable']=True
 except PermissionError:result[name+'_readable']=False
try:
 with open('write_probe','x') as stream:stream.write('probe')
 result['workspace_writable']=True
except PermissionError:result['workspace_writable']=False
print(json.dumps(result))
'''.replace('PROTECTED', repr(cfg['protected_probe_paths']))
    args = [cfg['cli_args'][0], 'sandbox', '-C', cfg['workspace'], '-P', 'fl_review']
    for setting in cfg['config'][:3]:
        args += ['-c', setting]
    args += ['--', '/usr/bin/python3', '-c', probe]
    result = subprocess.run(args, capture_output=True, text=True, timeout=30)
    write(DATA / 'isolation_probe.json', {'args': args, 'exit_code': result.returncode,
        'stdout': result.stdout, 'stderr': result.stderr, 'recorded_at_utc': datetime.now(timezone.utc).isoformat()})
    assert result.returncode == 0, 'Probe failed; no review launched'
    expected = {'inventory_readable': True, 'workspace_writable': False}
    expected.update({k + '_readable': False for k in cfg['protected_probe_paths']})
    assert json.loads(result.stdout) == expected, 'Protected file readable; no review launched'
    write(DATA / 'attempt_started.json', {'started_at_utc': datetime.now(timezone.utc).isoformat(),
                                        'preflight_sha256': digest(DATA / 'preflight.json')})
    with (DATA / 'events.jsonl').open('xb') as stdout, (DATA / 'stderr.txt').open('xb') as stderr:
        try:
            result = subprocess.run(cfg['cli_args'], input=(DATA / 'review_prompt.txt').read_bytes(),
                                    stdout=stdout, stderr=stderr, timeout=cfg['timeout_seconds'], cwd=cfg['workspace'])
            code, timed_out = result.returncode, False
        except subprocess.TimeoutExpired:
            code, timed_out = None, True
    write(DATA / 'attempt_finished.json', {'finished_at_utc': datetime.now(timezone.utc).isoformat(),
        'exit_code': code, 'timed_out': timed_out, 'return_present': (DATA / 'return_raw.json').exists()})
    print(json.dumps({'exit_code': code, 'timed_out': timed_out, 'return_present': (DATA / 'return_raw.json').exists()}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['prepare', 'run'])
    args = parser.parse_args()
    prepare() if args.mode == 'prepare' else run()
