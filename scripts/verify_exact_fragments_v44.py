"""Independent suffix-DP reconstruction of maximal English fragment runs."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys
import unicodedata

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from verify_correspondence_v6 import check_hashes


def read(path):
    return json.loads((ROOT / path).read_text())


def sha(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def reference(query, source, cutoff, offset):
    qm = list(re.finditer(r'\S+', query)); sm = list(re.finditer(r'\S+', source))
    q = [unicodedata.normalize('NFC', m.group()).casefold() for m in qm]
    s = [unicodedata.normalize('NFC', m.group()).casefold() for m in sm]
    previous = [0] * (len(s) + 1)
    ends = []; longest = 0
    for i in range(len(q)):
        current = [0] * (len(s) + 1)
        for j in range(len(s)):
            if q[i] != s[j]:
                continue
            length = previous[j] + 1
            current[j + 1] = length
            longest = max(longest, length)
            right_end = i + 1 == len(q) or j + 1 == len(s) or q[i + 1] != s[j + 1]
            if right_end and length >= cutoff:
                ends.append((i - length + 1, j - length + 1, length))
        previous = current
    runs = []; covered = set()
    for i, j, length in sorted(ends):
        qa, qb = qm[i].start(), qm[i + length - 1].end()
        sa, sb = sm[j].start(), sm[j + length - 1].end()
        runs.append({'query_token_span': [i, i + length], 'source_token_span': [j, j + length],
                     'query_char_span': [qa, qb], 'source_char_span': [sa, sb],
                     'target_char_span': [offset + qa, offset + qb], 'token_count': length,
                     'normalized_tokens': q[i:i + length], 'query_fragment': query[qa:qb],
                     'source_fragment': source[sa:sb]})
        covered.update(range(i, i + length))
    return {'available': True, 'query_token_count': len(q), 'source_token_count': len(s),
            'minimum_tokens': cutoff, 'longest_run_tokens': longest, 'runs': runs,
            'qualifying_run_count': len(runs), 'qualifying_overlap_present': bool(runs),
            'covered_query_token_indices': sorted(covered), 'covered_query_tokens': len(covered)}


def main():
    run = ROOT / 'runs/000044_exact_fragments'
    check_hashes(run)
    cfg = read('experiments/exact_fragments_v44.json'); pre = read('data/v44/preflight.json')
    manifest = read('runs/000044_exact_fragments/manifest.json')
    for path, expected in pre['hashes'].items():
        assert sha(path) == expected, path
    assert all(pre['hashes'][p] == h for p, h in cfg['input_hashes'].items())
    assert pre['hashes']['experiments/exact_fragments_v44.json'] == sha('experiments/exact_fragments_v44.json')
    assert cfg['registered_at_utc'] < pre['sealed_at_utc'] < manifest['finished_at_utc']
    assert cfg['request_budget'] == 0 and cfg['minimum_tokens'] == 8
    assert cfg['query_ids'] == [f'quote{i:02d}' for i in range(2, 8)]
    original = read('data/v39/frozen_queries.json')['queries']
    frozen = read('data/v44/frozen_queries.json')
    assert frozen == {'queries': original[2:], 'controls': original[:2], 'minimum_tokens': 8}
    target = read('data/v38/target_export.json')['text']
    for q in original:
        assert target[slice(*q['span'])] == q['text']
    source = (ROOT / cfg['source_text']).read_text()
    assert source == read('data/v42/page_observations.json')['text'] and len(source) == 12072
    assert read('data/v42/page_observations.json')['material_available']
    assessment = read('data/v44/assessment.json')
    assert len(assessment['queries']) == 6
    for q, row in zip(original[2:], assessment['queries'], strict=True):
        expected = reference(q['text'], source, 8, q['span'][0])
        assert row == {'quote_id': q['quote_id'], **expected}
        for r in row['runs']:
            assert target[slice(*r['target_char_span'])] == r['query_fragment']
            assert source[slice(*r['source_char_span'])] == r['source_fragment']
    c = assessment['controls']
    assert c['known_positive'] == reference(original[0]['text'], source, 8, original[0]['span'][0])
    assert c['short_name'] == reference(original[1]['text'], source, 8, original[1]['span'][0])
    assert c['absent_query'] == cfg['absent_query'] and len(c['absent_query'].split()) == 8
    assert c['absent'] == reference(cfg['absent_query'], source, 8, 0)
    reverse = ' '.join(reversed(re.findall(r'\S+', original[0]['text'])))
    assert c['reversed_query'] == reverse and c['reversed_positive'] == reference(reverse, source, 8, 0)
    required = max(8, len(re.findall(r'\S+', original[0]['text'])) - 2)
    assert c['known_positive_minimum'] == required
    passed = {'known_positive': c['known_positive']['longest_run_tokens'] >= required,
              'short_name_below_threshold': not c['short_name']['qualifying_overlap_present'],
              'nonce_absent': c['absent']['longest_run_tokens'] == 0,
              'reversed_positive_below_threshold': not c['reversed_positive']['qualifying_overlap_present']}
    assert c['passed'] == passed and all(passed.values())
    rows = assessment['queries']; report = read('runs/000044_exact_fragments/report.json')
    assert report['minimum_tokens'] == 8 and report['query_denominator'] == 6 and report['source_characters'] == len(source)
    assert report['controls_passed'] == passed and report['primary_readout_valid']
    assert report['queries_with_qualifying_run'] == sum(r['qualifying_overlap_present'] for r in rows) == 1
    assert report['qualifying_run_occurrences'] == sum(r['qualifying_run_count'] for r in rows) == 1
    assert report['covered_query_tokens'] == sum(r['covered_query_tokens'] for r in rows) == 22
    assert report['total_query_tokens'] == sum(r['query_token_count'] for r in rows) == 375
    assert rows[0]['quote_id'] == 'quote02' and rows[0]['longest_run_tokens'] == 22
    assert [r['longest_run_tokens'] for r in rows[1:]] == [2] * 5
    assert report['whole_query_results_revised'] is False
    for k in ['network_requests', 'new_document_extractions', 'opaque_passages_scored', 'semantic_labels_admitted',
              'source_identities_admitted', 'independent_reviews_admitted', 'untouched_test_units_admitted', 'external_messages_sent']:
        assert report[k] == 0
    assert report['semantic_evaluation_metrics'] is report['scientific_acceptance'] is None
    previous = []
    for path in sorted((ROOT / 'runs').glob('000*/manifest.json')):
        if path.parent != run:
            check_hashes(path.parent); previous.append(path.parent.name)
    assert len(previous) == 43
    for path in (ROOT / 'reports').glob('*_deliverable_seal.json'):
        for p, expected in json.loads(path.read_text()).get('deliverable_hashes', {}).items():
            assert sha(p) == expected
    result = {'state': 'verified', 'manifest_sha256': sha('runs/000044_exact_fragments/manifest.json'),
              'frozen_inputs_and_code_verified': True, 'independent_suffix_dp_reproduced_all_runs_and_offsets': True,
              'overlap_union_coverage_and_controls_verified': True, 'independent_scientific_review': False,
              'opaque_semantics_or_original_source_identity_validated': False, 'prior_runs_preserved': previous}
    out = ROOT / 'reports/000044_verification.json'
    if out.exists():
        assert {k: v for k, v in json.loads(out.read_text()).items() if k != 'verified_at_utc'} == result
    else:
        with out.open('x') as stream:
            json.dump(result | {'verified_at_utc': datetime.now(timezone.utc).isoformat()}, stream, indent=2); stream.write('\n')
    print(json.dumps({'state': 'verified', 'prior_runs_preserved': len(previous),
                      'queries_with_8_token_run': report['queries_with_qualifying_run'], 'covered_tokens': report['covered_query_tokens']}, indent=2))


if __name__ == '__main__':
    main()
