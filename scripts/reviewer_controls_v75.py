"""Prepare, run once, or assess the fixed literal-clue reviewer control batch."""
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

from automated_packet_review_v72 import ROOT, digest, write
from fl_decipher.reviewer_controls_v75 import cases_from_appendix, assess

DATA = ROOT / 'data/v75'
RUN = ROOT / 'runs/000075_reviewer_controls'


def prepare():
    DATA.mkdir()
    RUN.mkdir()
    workspace = Path(tempfile.mkdtemp(prefix='fl-review-v75-', dir='/private/tmp'))
    with zipfile.ZipFile(ROOT / 'data/v25/packets/western_esoterism.zip') as archive:
        for n in ['fl_post.txt', 'publisher_window.txt']:
            (workspace / n).write_bytes(archive.read(n))
    appendix = json.loads((ROOT / 'data/v26/evidence_spans.json').read_text())
    cases, oracle = cases_from_appendix(appendix)
    texts = {'fl': (workspace / 'fl_post.txt').read_bytes().decode('utf-8'),
             'source': (workspace / 'publisher_window.txt').read_bytes().decode('utf-8')}
    for c in cases:
        for side in ['fl', 'source']:
            s = c[side + '_span']
            assert texts[side][s['start']:s['end']] == s['text']
    write(DATA / 'clue_inventory.json', {'claim_rule': 'Both spans contain all listed whole anchors in given order after NFC/casefold and whitespace collapse.', 'cases': cases})
    write(DATA / 'oracle.json', {'cases': oracle, 'created_at_utc': datetime.now(timezone.utc).isoformat()})
    template = {'reviewer': {'name': None, 'kind': 'automated', 'identifier': None, 'prior_exposure': None},
                'completed_at_utc': None, 'review_completed': False,
                'judgments': [{'case_id': c['case_id'], 'disposition': None, 'fl_span': c['fl_span'],
                               'source_span': c['source_span'], 'explanation': None} for c in cases],
                'limitations': []}
    write(DATA / 'return_template.json', template)
    for n in ['clue_inventory.json', 'return_template.json']:
        shutil.copy2(DATA / n, workspace / n)
    material = {'scope': 'Literal verification in exact supplied text only; no source/semantic admission.',
                'members': {n: {'sha256': digest(workspace / n), 'bytes': (workspace / n).stat().st_size}
                            for n in ['fl_post.txt', 'publisher_window.txt', 'clue_inventory.json', 'return_template.json']},
                'text_code_point_lengths': {'fl_post.txt': len(texts['fl']), 'publisher_window.txt': len(texts['source'])}}
    write(DATA / 'review_material_manifest.json', material)
    shutil.copy2(DATA / 'review_material_manifest.json', workspace / 'review_material_manifest.json')
    review_id = 'fl-literal-v75-' + str(uuid.uuid4())
    prompt = (ROOT / 'experiments/reviewer_controls_v75_prompt.md').read_text().replace('{review_id}', review_id)
    (DATA / 'review_prompt.txt').write_text(prompt)
    old = json.loads((ROOT / 'data/v74/preflight.json').read_text())
    config = [s.replace(old['workspace'], str(workspace)) for s in old['config']]
    cli = shutil.which('codex')
    assert cli
    args = [cli, '--no-daemon', 'exec', '--ignore-user-config', '--ephemeral', '--strict-config',
            '--skip-git-repo-check', '--json', '-C', str(workspace), '-o', str(DATA / 'return_raw.json')]
    for setting in config:
        args += ['-c', setting]
    args.append('-')
    protected = dict(old['protected_probe_paths'])
    protected.update({'history': str(ROOT / 'reports/000074_interpretation.md'),
                      'other_tmp': '/private/tmp/fl-v74-export-path', 'oracle': str(DATA / 'oracle.json')})
    assert all(Path(p).is_file() for p in protected.values())
    inputs = ['experiments/reviewer_controls_v75.md', 'experiments/reviewer_controls_v75_prompt.md',
              'scripts/reviewer_controls_v75.py', 'src/fl_decipher/reviewer_controls_v75.py',
              'scripts/inventory_review_v74.py', 'scripts/automated_packet_review_v72.py',
              'data/v74/preflight.json', 'data/v25/packets/western_esoterism.zip',
              'data/v26/evidence_spans.json', 'reports/000074_deliverable_seal.json']
    inputs += [str(p.relative_to(ROOT)) for p in DATA.iterdir() if p.is_file()]
    cfg = {'experiment_id': 'reviewer_controls_v75', 'registered_at_utc': datetime.now(timezone.utc).isoformat(),
           'review_id': review_id, 'model_attempt_budget': 1, 'timeout_seconds': 900,
           'case_ids': [c['case_id'] for c in cases], 'genuine_denominator': 3, 'false_denominator': 2,
           'workspace': str(workspace), 'config': config, 'cli_args': args, 'protected_probe_paths': protected,
           'cli_version': subprocess.check_output([cli, '--version'], text=True).strip(),
           'input_hashes': {p: digest(ROOT / p) for p in inputs},
           'material_copy_hashes': {str(p.relative_to(workspace)): digest(p) for p in workspace.iterdir() if p.is_file()}}
    write(ROOT / 'experiments/reviewer_controls_v75.json', {k: v for k, v in cfg.items()
          if k not in ['workspace', 'config', 'cli_args', 'protected_probe_paths']})
    cfg['input_hashes']['experiments/reviewer_controls_v75.json'] = digest(ROOT / 'experiments/reviewer_controls_v75.json')
    write(DATA / 'preflight.json', cfg)
    print(json.dumps({'state': 'prepared', 'case_count': len(cases), 'review_id': review_id}))


def run():
    # Reuse the sealed E74 one-shot executor with only its output-root binding
    # changed in this process. It reads the new frozen preflight and touches no
    # E74 evidence or historical source file. Its probe supports an oracle canary.
    import inventory_review_v74 as execution
    execution.DATA = DATA
    execution.run()


def assessment():
    cfg = json.loads((DATA / 'preflight.json').read_text())
    for p, h in cfg['input_hashes'].items():
        assert digest(ROOT / p) == h, p
    raw = DATA / 'return_raw.json'
    write(DATA / 'prediction_receipt.json', {'frozen_at_utc': datetime.now(timezone.utc).isoformat(),
          'return_sha256': digest(raw), 'events_sha256': digest(DATA / 'events.jsonl')})
    # The immutable prediction receipt is written before loading the oracle.
    cases = json.loads((DATA / 'clue_inventory.json').read_text())['cases']
    oracle = json.loads((DATA / 'oracle.json').read_text())['cases']
    with zipfile.ZipFile(ROOT / 'data/v25/packets/western_esoterism.zip') as archive:
        texts = {'fl': archive.read('fl_post.txt').decode('utf-8'),
                 'source': archive.read('publisher_window.txt').decode('utf-8')}
    try:
        value = json.loads(raw.read_text())
    except ValueError:
        value = None
    result = assess(value, cases, oracle, texts, cfg['review_id'])
    result.update({'experiment_id': 'reviewer_controls_v75', 'assessed_at_utc': datetime.now(timezone.utc).isoformat(),
                   'source_identity_admitted': False, 'opaque_meanings_admitted': 0,
                   'independent_reviews_admitted': 0, 'untouched_test_units_admitted': 0,
                   'natural_benchmark_qualifying_works': 0, 'natural_benchmark_required_works': 4})
    write(RUN / 'report.json', result)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['prepare', 'run', 'assess'])
    mode = parser.parse_args().mode
    {'prepare': prepare, 'run': run, 'assess': assessment}[mode]()
