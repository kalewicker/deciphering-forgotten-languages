"""Verify E72 input preservation, isolation probes, first-return binding and spans."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads((ROOT / path).read_text())


def digest(path):
    return sha256((ROOT / path).read_bytes()).hexdigest()


def verify():
    old = read('data/v72/preflight.json')
    cfg = read('data/v72/preflight_revision1.json')
    assert read('experiments/automated_packet_review_v72_revision1.json') == {
        k: v for k, v in cfg.items()
        if k not in ('workspace', 'cli_args', 'config', 'protected_probe_paths')}
    for registration in [old, cfg]:
        for p, h in registration['input_hashes'].items():
            assert digest(p) == h, p
    assert old['review_id'] == cfg['review_id']
    assert old['material_copy_hashes'] == cfg['material_copy_hashes']
    assert old['model_review_attempt_budget'] == cfg['model_review_attempt_budget'] == 1
    assert old['timeout_seconds'] == cfg['timeout_seconds'] == 900
    before = read('data/v72/isolation_probe.json')
    after = read('data/v72/isolation_probe_revision1.json')
    assert before['exit_code'] == after['exit_code'] == 0
    assert json.loads(before['stdout']) == {
        'packet_readable': True, 'memory_readable': True, 'history_readable': False,
        'other_tmp_readable': False, 'packet_writable': False}
    expected = {'packet_readable': True, 'packet_writable': False}
    expected.update({k + '_readable': False for k in cfg['protected_probe_paths']})
    assert json.loads(after['stdout']) == expected
    start = read('data/v72/attempt_started.json')
    finish = read('data/v72/attempt_finished.json')
    assert start['preflight_sha256'] == digest('data/v72/preflight_revision1.json')
    timestamps = [cfg['registered_at_utc'], after['recorded_at_utc'],
                  start['started_at_utc'], finish['finished_at_utc']]
    dates = [datetime.fromisoformat(t) for t in timestamps]
    assert dates == sorted(dates)
    assert datetime.fromisoformat(before['recorded_at_utc']) < dates[0]
    assert finish['exit_code'] == 0 and finish['timed_out'] is False and finish['return_present'] is True
    assert (dates[-1] - dates[-2]).total_seconds() <= cfg['timeout_seconds']
    assert all(x in cfg['cli_args'] for x in ['exec', '--ephemeral', '--ignore-user-config'])
    assert not any(x in cfg['cli_args'] for x in ['resume', 'fork'])
    for setting in ['memories.use_memories=false', 'memories.generate_memories=false',
                    'features.memories=false', 'project_doc_max_bytes=0',
                    'permissions.fl_review.network.enabled=false', 'web_search="disabled"']:
        assert setting in cfg['config']
    with zipfile.ZipFile(ROOT / 'data/v25/packets/risk_math.zip') as archive:
        names = archive.namelist()
        assert len(names) == len(set(names)) == 9
        assert {n: sha256(archive.read(n)).hexdigest() for n in names} == cfg['material_copy_hashes']
        manifest_bytes = archive.read('material_manifest.json')
        material = json.loads(manifest_bytes)
        assert material['publisher_pages_one_based'] == [1, 2, 3]
        for n, entry in material['members'].items():
            raw = archive.read(n)
            assert len(raw) == entry['bytes'] and sha256(raw).hexdigest() == entry['sha256']
        texts = {n: archive.read(n).decode('utf-8') for n in material['text_code_point_lengths']}
        assert {n: len(t) for n, t in texts.items()} == material['text_code_point_lengths']
    returned = read('data/v72/review_return_raw.txt')
    assert returned['nominee_id'] == 'risk_math'
    assert returned['packet_manifest_sha256'] == sha256(manifest_bytes).hexdigest()
    assert returned['reviewer']['kind'] == 'automated'
    assert returned['reviewer']['identifier'] == cfg['review_id']
    assert returned['source_relationship'] == 'uncertain'
    assert returned['review_completed'] is True
    spans = []
    for row in returned['language_observations']:
        spans.append(('fl_post.txt', row['fl_span']))
    for row in returned['evidence_pairs'] + returned['counterexamples']:
        spans.extend([('fl_post.txt', row['fl_span']), ('publisher_window.txt', row['source_span'])])
    for name, span in spans:
        assert type(span['start']) is int and type(span['end']) is int
        assert 0 <= span['start'] < span['end'] <= len(texts[name])
        assert texts[name][span['start']:span['end']] == span['text']
    validation = read('data/v72/validation_v25.json')
    assert validation['structurally_valid'] is True and validation['errors'] == []
    assert validation['return_sha256'] == digest('data/v72/review_return_raw.txt')
    assert validation['independence_externally_verified'] is False
    events = [json.loads(s) for s in (ROOT / 'data/v72/events.jsonl').read_text().splitlines()]
    threads = [e['thread_id'] for e in events if e['type'] == 'thread.started']
    assert len(threads) == 1
    assert sum(e['type'] == 'turn.started' for e in events) == 1
    assert events[-1]['type'] == 'turn.completed'
    commands = [e['item'] for e in events if e['type'] == 'item.completed'
                and e.get('item', {}).get('type') == 'command_execution']
    assert len(commands) == 3 and all(c['exit_code'] == 0 for c in commands)
    # Human-readable report separately assesses these exact commands, not just their status.
    final = [e['item']['text'] for e in events if e['type'] == 'item.completed'
             and e.get('item', {}).get('type') == 'agent_message'][-1]
    assert json.loads(final) == returned
    assert '--image' in cfg['cli_args'] and cfg['cli_args'].count('--image') == 3
    return {
        'experiment_id': 'automated_packet_review_v72', 'state': 'verified',
        'review_id': cfg['review_id'], 'codex_thread_id': threads[0],
        'packet_members_preserved': 9, 'declared_member_hashes_and_lengths_verified': 7,
        'exact_text_lengths_verified': 2, 'exact_spans_verified': len(spans),
        'distinct_exact_spans_verified': len({(n, s['start'], s['end']) for n, s in spans}),
        'initial_isolation_failure_preserved': True, 'corrected_isolation_probe_passed': True,
        'review_attempts': 1, 'completed_tool_commands': len(commands),
        'publisher_images_attached': 3,
        'return_sha256': digest('data/v72/review_return_raw.txt'),
        'v25_structural_validation_passed': True,
        'reviewer_source_relationship': returned['source_relationship'],
        'reviewer_coverage_field': returned['coverage'],
        'accepted_source_coverage': 'unestablished',
        'source_identity_admitted': False, 'opaque_meanings_admitted': 0,
        'independent_scientific_reviews_admitted': 0, 'untouched_test_units_admitted': 0,
        'natural_benchmark_qualifying_works': 0, 'natural_benchmark_required_works': 4,
        'verified_at_utc': datetime.now(timezone.utc).isoformat(),
    }


if __name__ == '__main__':
    print(json.dumps(verify(), indent=2))
