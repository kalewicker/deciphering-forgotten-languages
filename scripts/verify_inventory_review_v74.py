"""Independent inventory/quote/attempt accounting; not independent semantic review."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def verify():
    read = lambda p: json.loads((ROOT / p).read_text())
    digest = lambda p: sha256((ROOT / p).read_bytes()).hexdigest()
    cfg = read('data/v74/preflight.json')
    for p, h in cfg['input_hashes'].items():
        assert digest(p) == h, p
    public = read('experiments/inventory_review_v74.json')
    assert all(public[k] == cfg[k] for k in public if k != 'input_hashes')
    assert public['input_hashes'] == {p: h for p, h in cfg['input_hashes'].items()
                                    if p != 'experiments/inventory_review_v74.json'}
    with zipfile.ZipFile(ROOT / 'data/v25/packets/western_esoterism.zip') as archive:
        assert len(archive.namelist()) == len(set(archive.namelist())) == 11
        copied = {n: sha256(archive.read(n)).hexdigest() for n in archive.namelist()}
        raw_manifest = archive.read('material_manifest.json')
        manifest = json.loads(raw_manifest)
        assert manifest['publisher_pages_one_based'] == list(range(90, 95))
        for n, entry in manifest['members'].items():
            raw = archive.read(n)
            assert sha256(raw).hexdigest() == entry['sha256'] and len(raw) == entry['bytes']
        texts = {'fl': archive.read('fl_post.txt').decode('utf-8'),
                 'source': archive.read('publisher_window.txt').decode('utf-8')}
        assert [len(texts['fl']), len(texts['source'])] == [6710, 12009]
        assert json.loads(archive.read('review_return_template.json'))['packet_manifest_sha256'] == sha256(raw_manifest).hexdigest()
    for n in ['clue_inventory.json', 'assisted_return_template.json']:
        copied[n] = digest('data/v74/' + n)
    assert copied == cfg['material_copy_hashes']
    inventory = read('data/v74/clue_inventory.json')
    old = read('data/v26/evidence_spans.json')
    originals = [r for r in old['pairs'] if r['packet'] == 'western_esoterism']
    assert [r['id'] for r in originals] == cfg['clue_ids'] == ['W1', 'W2', 'W3', 'W4', 'W5']
    for c, old_row in zip(inventory['clues'], originals, strict=True):
        assert set(c) == {'id', 'fl_span', 'source_span', 'pdf_page', 'observable_question'}
        for k in ['id', 'fl_span', 'source_span', 'pdf_page']:
            assert c[k] == old_row[k]
    returned = read('data/v74/return_raw.json')
    assert set(returned) == {'review', 'clue_dispositions'}
    review = returned['review']
    assert review == read('data/v74/review_for_v25.json')
    assert review['packet_manifest_sha256'] == sha256(raw_manifest).hexdigest()
    assert review['reviewer']['identifier'] == cfg['review_id']
    assert review['reviewer']['kind'] == 'automated'
    assert review['reviewer']['independent_of_prior_predictions'] is False
    spans = [('fl', r['fl_span']) for r in review['language_observations']]
    for family in ['evidence_pairs', 'counterexamples']:
        spans.extend((side, r[side + '_span']) for r in review[family] for side in ['fl', 'source'])
    for side, span in spans:
        assert type(span['start']) is int and type(span['end']) is int
        assert 0 <= span['start'] < span['end'] <= len(texts[side])
        assert ''.join(texts[side][i] for i in range(span['start'], span['end'])) == span['text']
    dispositions = returned['clue_dispositions']
    assert sorted(r['clue_id'] for r in dispositions) == sorted(cfg['clue_ids'])
    positions = lambda s: set(range(s['start'], s['end']))
    for c in inventory['clues']:
        r = next(row for row in dispositions if row['clue_id'] == c['id'])
        assert set(r) == {'clue_id', 'disposition', 'evidence_pair_indices', 'counterexample_indices',
                          'candidate_relationship_implication', 'limitations'}
        assert r['disposition'] in ('supported', 'rejected', 'uncertain')
        assert all(isinstance(r[k], str) and r[k].strip()
                   for k in ['candidate_relationship_implication', 'limitations'])
        references = [(family, i) for key, family in [('evidence_pair_indices', 'evidence_pairs'),
                      ('counterexample_indices', 'counterexamples')] for i in r[key]]
        assert references
        for family, i in references:
            assert type(i) is int and 0 <= i < len(review[family])
            pair = review[family][i]
            assert all(positions(c[side + '_span']) <= positions(pair[side + '_span']) for side in ['fl', 'source'])
    assisted = read('data/v74/assisted_validation.json')
    assert assisted['assisted_documentation_complete'] is True and assisted['errors'] == []
    legacy = read('data/v74/original_v25_validation.json')
    assert legacy['structurally_valid'] is False and legacy['ready_for_adjudication'] is False
    assert legacy['errors'] == ['reviewer.independent_of_prior_predictions: true declaration required']
    assert legacy['return_sha256'] == digest('data/v74/review_for_v25.json')
    assert legacy['source_identity_admitted'] is False and legacy['semantic_labels_admitted'] == 0
    probe = read('data/v74/isolation_probe.json')
    expected = {'inventory_readable': True, 'workspace_writable': False}
    expected.update({name + '_readable': False for name in cfg['protected_probe_paths']})
    assert probe['exit_code'] == 0 and json.loads(probe['stdout']) == expected
    start, finish = read('data/v74/attempt_started.json'), read('data/v74/attempt_finished.json')
    assert start['preflight_sha256'] == digest('data/v74/preflight.json')
    times = [datetime.fromisoformat(x) for x in [cfg['registered_at_utc'], probe['recorded_at_utc'],
             start['started_at_utc'], finish['finished_at_utc']]]
    assert times == sorted(times) and (times[-1] - times[-2]).total_seconds() <= 900
    assert finish['exit_code'] == 0 and finish['timed_out'] is False and finish['return_present'] is True
    assert cfg['model_attempt_budget'] == 1 and cfg['cli_args'].count('--image') == 5
    assert all(x in cfg['cli_args'] for x in ['exec', '--ephemeral', '--ignore-user-config'])
    assert not any(x in cfg['cli_args'] for x in ['resume', 'fork'])
    assert all(x in cfg['config'] for x in ['memories.use_memories=false',
        'memories.generate_memories=false', 'features.memories=false', 'project_doc_max_bytes=0',
        'permissions.fl_review.network.enabled=false', 'web_search="disabled"'])
    events = [json.loads(s) for s in (ROOT / 'data/v74/events.jsonl').read_text().splitlines()]
    assert sum(e['type'] == 'thread.started' for e in events) == 1
    assert sum(e['type'] == 'turn.started' for e in events) == 1
    assert events[-1]['type'] == 'turn.completed'
    final = [e['item']['text'] for e in events if e['type'] == 'item.completed'
             and e.get('item', {}).get('type') == 'agent_message'][-1]
    assert json.loads(final) == returned
    commands = [e['item'] for e in events if e['type'] == 'item.completed'
                and e.get('item', {}).get('type') == 'command_execution']
    distinct = {(side, s['start'], s['end']) for side, s in spans}
    inventory_pairs = {(c['fl_span']['start'], c['fl_span']['end'], c['source_span']['start'], c['source_span']['end'])
                       for c in inventory['clues']}
    new_pairs = [p for p in review['evidence_pairs'] if
                 (p['fl_span']['start'], p['fl_span']['end'], p['source_span']['start'], p['source_span']['end'])
                 not in inventory_pairs]
    return {'experiment_id': 'inventory_review_v74', 'state': 'verified',
            'primary_assisted_validator_not_imported': True,
            'review_attempts': 1, 'packet_members_preserved': 11, 'clue_denominator': 5,
            'clues_explicitly_disposed': len(dispositions),
            'observable_dispositions': {word: sum(r['disposition'] == word for r in dispositions)
                                       for word in ['supported', 'rejected', 'uncertain']},
            'quoted_span_records_verified': len(spans), 'distinct_quoted_spans_verified': len(distinct),
            'new_evidence_pairs_beyond_disclosed_inventory': len(new_pairs),
            'reviewer_source_relationship_field': review['source_relationship'],
            'reviewer_coverage_field': review['coverage'],
            'assisted_documentation_complete': True, 'original_independence_gate_passed': False,
            'isolation_probe_passed': True, 'images_attached': 5,
            'trace_command_attempts': len(commands),
            'trace_command_failures': sum(c['exit_code'] != 0 for c in commands),
            'return_sha256': digest('data/v74/return_raw.json'),
            'model_identifier': 'CLI default; exact model not independently captured',
            'source_identity_admitted': False, 'opaque_meanings_admitted': 0,
            'independent_reviews_admitted': 0, 'untouched_test_units_admitted': 0,
            'natural_benchmark_qualifying_works': 0, 'natural_benchmark_required_works': 4,
            'verified_at_utc': datetime.now(timezone.utc).isoformat()}


if __name__ == '__main__':
    print(json.dumps(verify(), indent=2))
