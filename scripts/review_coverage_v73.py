"""Read-only documentation overlap audit; requires frozen local review artifacts."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import re
import unicodedata
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads((ROOT / path).read_text())


def audit():
    cfg = read('experiments/review_coverage_v73.json')
    for path, expected in cfg['input_hashes'].items():
        assert sha256((ROOT / path).read_bytes()).hexdigest() == expected, path
    with zipfile.ZipFile(ROOT / cfg['packet']) as archive:
        manifest_bytes = archive.read('material_manifest.json')
        manifest = json.loads(manifest_bytes)
        for name, entry in manifest['members'].items():
            raw = archive.read(name)
            assert len(raw) == entry['bytes'] and sha256(raw).hexdigest() == entry['sha256']
        texts = {n: archive.read(n).decode('utf-8') for n in manifest['text_code_point_lengths']}
        assert {n: len(t) for n, t in texts.items()} == manifest['text_code_point_lengths']
    earlier = read(cfg['earlier_appendix'])
    returned = read(cfg['review_return'])
    assert returned['packet_manifest_sha256'] == sha256(manifest_bytes).hexdigest()
    for name, text in texts.items():
        assert sha256(text.encode()).hexdigest() == earlier['text_sha256']['risk_math'][name]
    old_pairs = [r for r in earlier['pairs'] if r['packet'] == 'risk_math']
    old_blocks = [r for r in earlier['unmatched_english_blocks'] if r['packet'] == 'risk_math']
    assert [r['id'] for r in old_pairs] == cfg['old_pair_ids']
    assert [r['id'] for r in old_blocks] == cfg['old_block_ids']
    span_records = []
    for i, row in enumerate(returned['language_observations']):
        span_records.append({'id': f'language_observations:{i}:fl', 'side': 'fl', 'span': row['fl_span']})
    for family in ('evidence_pairs', 'counterexamples'):
        for i, row in enumerate(returned[family]):
            for side in ('fl', 'source'):
                span_records.append({'id': f'{family}:{i}:{side}', 'side': side, 'span': row[side + '_span']})
    bindings_checked = 0

    def bind(side, span):
        nonlocal bindings_checked
        text = texts['fl_post.txt' if side == 'fl' else 'publisher_window.txt']
        assert type(span['start']) is int and type(span['end']) is int
        assert 0 <= span['start'] < span['end'] <= len(text)
        assert text[span['start']:span['end']] == span['text']
        bindings_checked += 1

    for r in span_records:
        bind(r['side'], r['span'])
    for r in old_pairs:
        bind('fl', r['fl_span'])
        bind('source', r['source_span'])
    for r in old_blocks:
        bind('fl', r['fl_span'])

    def contains(outer, inner):
        return outer['start'] <= inner['start'] and inner['end'] <= outer['end']

    pair_ledger = []
    for old in old_pairs:
        row = {'id': old['id'], 'old_basis': old['basis'], 'old_fl_span': old['fl_span'],
               'old_source_span': old['source_span']}
        for side in ('fl', 'source'):
            row[side + '_enclosure_witnesses'] = [r['id'] for r in span_records
                if r['side'] == side and contains(r['span'], old[side + '_span'])]
        row['joint_witnesses'] = [f'{family}:{i}' for family in ('evidence_pairs', 'counterexamples')
            for i, new in enumerate(returned[family])
            if contains(new['fl_span'], old['fl_span']) and contains(new['source_span'], old['source_span'])]
        pair_ledger.append(row)
    block_ledger = [{'id': old['id'], 'old_fl_span': old['fl_span'],
                     'enclosure_witnesses': [r['id'] for r in span_records if r['side'] == 'fl'
                                            and contains(r['span'], old['fl_span'])]} for old in old_blocks]

    def strings(value, path='$'):
        if isinstance(value, str):
            yield path, value
        elif isinstance(value, dict):
            for key, item in value.items():
                yield from strings(item, path + '.' + key)
        elif isinstance(value, list):
            for i, item in enumerate(value):
                yield from strings(item, path + f'[{i}]')

    spelling_ledger = []
    for cue in cfg['spelling_cues']:
        key = unicodedata.normalize('NFC', cue).casefold()
        pattern = re.compile(r'(?<!\w)' + re.escape(key) + r'(?!\w)')
        matches = [{'json_path': p, 'normalized_offsets': [m.start(), m.end()]}
                   for p, text in strings(returned)
                   for m in pattern.finditer(unicodedata.normalize('NFC', text).casefold())]
        spelling_ledger.append({'cue': cue, 'mentions': matches})

    def overlaps(a, b):
        return max(a['start'], b['start']) < min(a['end'], b['end'])

    new_pairs = [{'id': f'evidence_pairs:{i}', 'basis': row['basis'],
                  'relationship': row['relationship'], 'fl_span': row['fl_span'],
                  'source_span': row['source_span'],
                  'two_sided_old_overlap_ids': [old['id'] for old in old_pairs
                      if overlaps(row['fl_span'], old['fl_span'])
                      and overlaps(row['source_span'], old['source_span'])]}
                 for i, row in enumerate(returned['evidence_pairs'])]
    for path, pointer in cfg['preserved_gate_fields']:
        value = read(path)
        for part in pointer.split('/')[1:]:
            value = value[part]
        assert value is False, (path, pointer)
    return {
        'experiment_id': 'review_coverage_v73', 'audit_type': 'retrospective_documentation_overlap',
        'old_pair_denominator': len(old_pairs),
        'pairs_with_fl_enclosure': sum(bool(r['fl_enclosure_witnesses']) for r in pair_ledger),
        'pairs_with_source_enclosure': sum(bool(r['source_enclosure_witnesses']) for r in pair_ledger),
        'jointly_enclosed_old_pairs': sum(bool(r['joint_witnesses']) for r in pair_ledger),
        'old_block_denominator': len(old_blocks),
        'old_blocks_with_exact_span_enclosure': sum(bool(r['enclosure_witnesses']) for r in block_ledger),
        'spelling_cue_denominator': len(spelling_ledger),
        'spelling_cues_explicitly_mentioned': sum(bool(r['mentions']) for r in spelling_ledger),
        'new_evidence_pair_denominator': len(new_pairs),
        'new_pairs_without_two_sided_old_overlap': sum(not r['two_sided_old_overlap_ids'] for r in new_pairs),
        'quoted_span_records_checked': bindings_checked,
        'pair_ledger': pair_ledger, 'block_ledger': block_ledger,
        'spelling_ledger': spelling_ledger, 'new_pair_ledger': new_pairs,
        'natural_rescores': 0, 'model_calls': 0, 'network_requests': 0,
        'source_identities_admitted': 0, 'opaque_meanings_admitted': 0,
        'independent_reviews_admitted': 0, 'untouched_test_units_admitted': 0,
        'natural_benchmark_qualifying_works': 0, 'natural_benchmark_required_works': 4,
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    result = audit()
    if args.verify:
        assert json.loads(args.output.read_text()) == result
    else:
        with args.output.open('x') as stream:
            json.dump(result, stream, indent=2)
            stream.write('\n')
    print(json.dumps({k: v for k, v in result.items() if not k.endswith('_ledger')}, indent=2))
