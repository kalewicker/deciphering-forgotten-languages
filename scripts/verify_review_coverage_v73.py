"""Independent set-of-character-positions reconstruction of E73 documentation coverage."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import re
import unicodedata
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def verify():
    load = lambda p: json.loads((ROOT / p).read_text())
    cfg = load('experiments/review_coverage_v73.json')
    result = load('runs/000073_review_coverage/report.json')
    for p, expected in cfg['input_hashes'].items():
        assert sha256((ROOT / p).read_bytes()).hexdigest() == expected, p
    old, new = load(cfg['earlier_appendix']), load(cfg['review_return'])
    pairs = [p for p in old['pairs'] if p['packet'] == 'risk_math']
    blocks = [p for p in old['unmatched_english_blocks'] if p['packet'] == 'risk_math']
    assert [p['id'] for p in pairs] == cfg['old_pair_ids'] == ['R1', 'R2', 'R3', 'R4']
    assert [p['id'] for p in blocks] == cfg['old_block_ids'] == ['R5', 'R6', 'R7', 'R8']
    positions = lambda s: frozenset(range(s['start'], s['end']))
    recorded = []
    for i, row in enumerate(new['language_observations']):
        recorded.append((f'language_observations:{i}:fl', 'fl', row['fl_span']))
    paired = []
    for kind in ('evidence_pairs', 'counterexamples'):
        for i, row in enumerate(new[kind]):
            paired.append((f'{kind}:{i}', row))
            recorded.extend((f'{kind}:{i}:{side}', side, row[side + '_span']) for side in ('fl', 'source'))
    with zipfile.ZipFile(ROOT / cfg['packet']) as archive:
        texts = {'fl': archive.read('fl_post.txt').decode('utf-8'),
                 'source': archive.read('publisher_window.txt').decode('utf-8')}
    expected_bindings = recorded + [(p['id'] + ':' + side, side, p[side + '_span'])
        for p in pairs for side in ('fl', 'source')] + [(p['id'], 'fl', p['fl_span']) for p in blocks]
    for _, side, span in expected_bindings:
        assert 0 <= span['start'] < span['end'] <= len(texts[side])
        assert ''.join(texts[side][i] for i in sorted(positions(span))) == span['text']
    fl_count = source_count = joint_count = 0
    for p, row in zip(pairs, result['pair_ledger'], strict=True):
        assert p['id'] == row['id']
        for side in ('fl', 'source'):
            witnesses = [rid for rid, rs, span in recorded if rs == side
                         and positions(p[side + '_span']).issubset(positions(span))]
            assert witnesses == row[side + '_enclosure_witnesses']
            if side == 'fl':
                fl_count += bool(witnesses)
            else:
                source_count += bool(witnesses)
        witnesses = [rid for rid, r in paired if all(positions(p[side + '_span']).issubset(
            positions(r[side + '_span'])) for side in ('fl', 'source'))]
        assert witnesses == row['joint_witnesses']
        joint_count += bool(witnesses)
    block_count = 0
    for p, row in zip(blocks, result['block_ledger'], strict=True):
        witnesses = [rid for rid, side, span in recorded if side == 'fl'
                     and positions(p['fl_span']).issubset(positions(span))]
        assert p['id'] == row['id'] and witnesses == row['enclosure_witnesses']
        block_count += bool(witnesses)
    stack, all_words = [new], []
    while stack:
        value = stack.pop()
        if isinstance(value, dict):
            stack.extend(value.values())
        elif isinstance(value, list):
            stack.extend(value)
        elif isinstance(value, str):
            all_words.extend(re.findall(r'\w+', unicodedata.normalize('NFC', value).casefold()))
    for cue, row in zip(cfg['spelling_cues'], result['spelling_ledger'], strict=True):
        assert cue == row['cue'] and all_words.count(cue) == len(row['mentions'])
    for p, row in zip(new['evidence_pairs'], result['new_pair_ledger'], strict=True):
        ids = [q['id'] for q in pairs if all(positions(p[side + '_span']) & positions(
            q[side + '_span']) for side in ('fl', 'source'))]
        assert ids == row['two_sided_old_overlap_ids']
    expected = {'old_pair_denominator': len(pairs), 'pairs_with_fl_enclosure': fl_count,
                'pairs_with_source_enclosure': source_count, 'jointly_enclosed_old_pairs': joint_count,
                'old_block_denominator': len(blocks), 'old_blocks_with_exact_span_enclosure': block_count,
                'spelling_cue_denominator': len(cfg['spelling_cues']),
                'spelling_cues_explicitly_mentioned': sum(bool(all_words.count(c)) for c in cfg['spelling_cues']),
                'quoted_span_records_checked': len(expected_bindings),
                'new_evidence_pair_denominator': len(new['evidence_pairs']),
                'new_pairs_without_two_sided_old_overlap': sum(not r['two_sided_old_overlap_ids'] for r in result['new_pair_ledger'])}
    assert all(result[k] == v for k, v in expected.items())
    # This is an old unequal-phrase observation, not an exact literal pair.
    assert pairs[1]['fl_span']['text'] != pairs[1]['source_span']['text']
    assert all(q['fl_span']['text'] == q['source_span']['text'] for q in pairs[2:])
    for p, pointer in cfg['preserved_gate_fields']:
        value = load(p)
        for part in pointer.split('/')[1:]:
            value = value[part]
        assert value is False
    return {'experiment_id': 'review_coverage_v73', 'state': 'verified',
            'primary_audit_code_not_imported': True,
            'independent_method': 'Explicit character-position sets; whole-word enumeration',
            **expected, 'semantic_recall_measured': False, 'independent_scientific_review': False,
            'verified_at_utc': datetime.now(timezone.utc).isoformat()}


if __name__ == '__main__':
    print(json.dumps(verify(), indent=2))
