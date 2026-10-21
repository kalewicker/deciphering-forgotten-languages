"""Independent known-truth reconstruction by exhaustive ordered occurrences."""
from datetime import datetime, timezone
from hashlib import sha256
from itertools import product
import json
from pathlib import Path
import unicodedata
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def verify():
    read = lambda p: json.loads((ROOT / p).read_text())
    digest = lambda p: sha256((ROOT / p).read_bytes()).hexdigest()
    cfg = read('data/v75/preflight.json')
    for p, h in cfg['input_hashes'].items():
        assert digest(p) == h, p
    public = read('experiments/reviewer_controls_v75.json')
    assert all(public[k] == cfg[k] for k in public if k != 'input_hashes')
    assert public['input_hashes'] == {p: h for p, h in cfg['input_hashes'].items()
                                    if p != 'experiments/reviewer_controls_v75.json'}
    normalize = lambda t: ' '.join(unicodedata.normalize('NFC', t).casefold().split())

    def chains(text, anchors):
        text = normalize(text)
        choices = []
        for anchor in anchors:
            needle = normalize(anchor)
            occurrences, start = [], 0
            while True:
                i = text.find(needle, start)
                if i < 0:
                    break
                end = i + len(needle)
                boundary = lambda c: c.isalnum() or c == '_'
                if (i == 0 or not boundary(text[i - 1])) and (end == len(text) or not boundary(text[end])):
                    occurrences.append((i, end))
                start = i + 1
            choices.append(occurrences)
        return [p for p in product(*choices) if all(a[1] <= b[0] for a, b in zip(p, p[1:]))]

    old = read('data/v26/evidence_spans.json')
    by_id = {r['id']: r for r in old['pairs'] if r['packet'] == 'western_esoterism'}
    names = ['Giovanni Pico della Mirandola', 'Marselio Ficino', 'Posidonius']
    specs = [('expression', 'W1', 'W1', ['fatum/providentia']), ('names_order', 'W2', 'W2', names),
             ('name_case', 'W4', 'W4', ['zazel']), ('wrong_source_label', 'W3', 'W5', ['Daemonium Saturni']),
             ('reversed_names', 'W2', 'W2', list(reversed(names)))]
    specs = sorted(specs, key=lambda s: sha256(('v75-review-controls-fixed|' + s[0]).encode()).digest())
    cases = read('data/v75/clue_inventory.json')['cases']
    oracle = read('data/v75/oracle.json')['cases']
    assert len(cases) == len(oracle) == 5
    expected = {}
    for i, (spec, c, o) in enumerate(zip(specs, cases, oracle, strict=True), 1):
        tag, fl_id, source_id, anchors = spec
        assert c == {'case_id': f'C{i:02}', 'fl_span': by_id[fl_id]['fl_span'],
                     'source_span': by_id[source_id]['source_span'], 'anchors': anchors}
        verdict = 'supported' if all(chains(c[side + '_span']['text'], anchors)
                                     for side in ['fl', 'source']) else 'rejected'
        assert o['case_id'] == c['case_id'] and o['construction'] == tag and o['expected'] == verdict
        for side, witness in zip(['fl', 'source'], o['normalized_matching_witnesses'], strict=True):
            text = normalize(c[side + '_span']['text'])
            assert len(witness) <= len(anchors)
            for anchor, (a, b) in zip(anchors, witness):
                assert text[a:b] == normalize(anchor)
            assert all(a[1] <= b[0] for a, b in zip(witness, witness[1:]))
        expected[c['case_id']] = verdict
    assert list(expected.values()).count('supported') == 3
    with zipfile.ZipFile(ROOT / 'data/v25/packets/western_esoterism.zip') as archive:
        text_bytes = {n: archive.read(n) for n in ['fl_post.txt', 'publisher_window.txt']}
    texts = {'fl': text_bytes['fl_post.txt'].decode('utf-8'),
             'source': text_bytes['publisher_window.txt'].decode('utf-8')}
    for c in cases:
        for side in ['fl', 'source']:
            s = c[side + '_span']
            assert texts[side][s['start']:s['end']] == s['text']
    supplied = {n: sha256(raw).hexdigest() for n, raw in text_bytes.items()}
    for n in ['clue_inventory.json', 'return_template.json', 'review_material_manifest.json']:
        supplied[n] = digest('data/v75/' + n)
    assert supplied == cfg['material_copy_hashes'] and len(supplied) == 5
    assert not any('oracle' in n or 'answer' in n for n in supplied)
    manifest = read('data/v75/review_material_manifest.json')
    for n, entry in manifest['members'].items():
        raw = text_bytes[n] if n in text_bytes else (ROOT / 'data/v75' / n).read_bytes()
        assert len(raw) == entry['bytes'] and sha256(raw).hexdigest() == entry['sha256']
    assert manifest['text_code_point_lengths'] == {n: len(raw.decode('utf-8')) for n, raw in text_bytes.items()}
    try:
        value = read('data/v75/return_raw.json')
    except ValueError:
        value = {}
    result = read('runs/000075_reviewer_controls/report.json')
    judgments = value.get('judgments', []) if isinstance(value, dict) else []
    assert isinstance(judgments, list), 'Malformed return retained; requires explicit malformed-accounting review'
    mapping = {j['case_id']: j for j in judgments if isinstance(j, dict)
               and isinstance(j.get('case_id'), str) and j['case_id'] in expected}
    reconstructed = [{'case_id': cid, 'expected': truth, 'observed': mapping.get(cid, {}).get('disposition'),
                      'correct': mapping.get(cid, {}).get('disposition') == truth} for cid, truth in expected.items()]
    assert reconstructed == result['ledger']
    metrics = {'case_denominator': 5, 'genuine_denominator': 3, 'false_denominator': 2,
               'genuine_supported': sum(r['correct'] for r in reconstructed if r['expected'] == 'supported'),
               'false_rejected': sum(r['correct'] for r in reconstructed if r['expected'] == 'rejected'),
               'false_supported': sum(r['observed'] == 'supported' for r in reconstructed if r['expected'] == 'rejected'),
               'uncertain_or_missing': sum(r['observed'] in ('uncertain', None) for r in reconstructed)}
    assert all(result[k] == v for k, v in metrics.items())
    # Independently verify the valid-document path; bad documents remain failed.
    span_count = 0
    if result['schema_and_quotes_complete']:
        assert result['errors'] == [] and set(value) == {'reviewer', 'completed_at_utc', 'review_completed', 'judgments', 'limitations'}
        assert value['review_completed'] is True and value['reviewer']['kind'] == 'automated'
        assert value['reviewer']['identifier'] == cfg['review_id']
        assert sorted(j['case_id'] for j in judgments) == sorted(expected)
        for j in judgments:
            c = next(c for c in cases if c['case_id'] == j['case_id'])
            assert set(j) == {'case_id', 'disposition', 'fl_span', 'source_span', 'explanation'}
            assert isinstance(j['explanation'], str) and j['explanation'].strip()
            for side in ['fl', 'source']:
                s = j[side + '_span']
                assert s == c[side + '_span']
                assert ''.join(texts[side][i] for i in range(s['start'], s['end'])) == s['text']
                span_count += 1
    else:
        assert result['errors'] and result['literal_control_gate'] is False
    assert result['literal_control_gate'] == (result['schema_and_quotes_complete'] and all(r['correct'] for r in reconstructed))
    probe = read('data/v75/isolation_probe.json')
    wanted = {'inventory_readable': True, 'workspace_writable': False}
    wanted.update({k + '_readable': False for k in cfg['protected_probe_paths']})
    assert probe['exit_code'] == 0 and json.loads(probe['stdout']) == wanted
    assert wanted['oracle_readable'] is False
    start, finish = read('data/v75/attempt_started.json'), read('data/v75/attempt_finished.json')
    prediction = read('data/v75/prediction_receipt.json')
    assert start['preflight_sha256'] == digest('data/v75/preflight.json')
    assert prediction['return_sha256'] == digest('data/v75/return_raw.json')
    assert prediction['events_sha256'] == digest('data/v75/events.jsonl')
    stamps = [cfg['registered_at_utc'], probe['recorded_at_utc'], start['started_at_utc'],
              finish['finished_at_utc'], prediction['frozen_at_utc'], result['assessed_at_utc']]
    dates = [datetime.fromisoformat(s) for s in stamps]
    assert dates == sorted(dates) and (dates[3] - dates[2]).total_seconds() <= 900
    assert cfg['model_attempt_budget'] == 1 and finish['exit_code'] == 0 and finish['timed_out'] is False
    assert all(s in cfg['config'] for s in ['memories.use_memories=false', 'memories.generate_memories=false',
        'features.memories=false', 'project_doc_max_bytes=0', 'permissions.fl_review.network.enabled=false', 'web_search="disabled"'])
    assert all(s in cfg['cli_args'] for s in ['exec', '--ephemeral', '--ignore-user-config'])
    assert not any(s in cfg['cli_args'] for s in ['resume', 'fork', '--image'])
    events = [json.loads(s) for s in (ROOT / 'data/v75/events.jsonl').read_text().splitlines()]
    assert sum(e['type'] == 'thread.started' for e in events) == 1
    assert sum(e['type'] == 'turn.started' for e in events) == 1 and events[-1]['type'] == 'turn.completed'
    final = [e['item']['text'] for e in events if e['type'] == 'item.completed'
             and e.get('item', {}).get('type') == 'agent_message'][-1]
    assert json.loads(final) == value
    return {'experiment_id': 'reviewer_controls_v75', 'state': 'verified',
            'primary_predicate_and_assessor_not_imported': True,
            'independent_truth_method': 'Enumerate all ordered occurrence combinations',
            **metrics, 'quote_records_verified': span_count,
            'private_oracle_read_denied': True, 'model_attempts': 1,
            'predictions_sealed_before_assessment': True,
            'registered_literal_control_gate': result['literal_control_gate'],
            'independent_scientific_review': False, 'source_identity_admitted': False,
            'opaque_meanings_admitted': 0, 'untouched_test_units_admitted': 0,
            'verified_at_utc': datetime.now(timezone.utc).isoformat()}


if __name__ == '__main__':
    print(json.dumps(verify(), indent=2))
