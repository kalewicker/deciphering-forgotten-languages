"""Offline independent reconstruction of the fixed-witness context dossier."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from verify_correspondence_v6 import check_hashes
from verify_native_quote_v42 import hits


def read(path):
    return json.loads((ROOT / path).read_text())


def sha(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def locate(fragment, text):
    rows = []; at = 0
    if not fragment:
        return rows
    while (at := text.find(fragment, at)) >= 0:
        rows.append([at, at + len(fragment)]); at += len(fragment)
    return rows


def main():
    run = ROOT / 'runs/000045_context_dossier'
    check_hashes(run)
    cfg = read('experiments/context_dossier_v45.json'); pre = read('data/v45/preflight.json')
    manifest = read('runs/000045_context_dossier/manifest.json')
    for path, expected in pre['hashes'].items():
        assert sha(path) == expected, path
    assert all(pre['hashes'][p] == h for p, h in cfg['input_hashes'].items())
    assert pre['hashes']['experiments/context_dossier_v45.json'] == sha('experiments/context_dossier_v45.json')
    assert cfg['registered_at_utc'] < pre['sealed_at_utc'] < manifest['finished_at_utc']
    assert cfg['request_budget'] == 0 and cfg['quote_id'] == 'quote02' and cfg['target_context_characters'] == 160
    selection = read('data/v45/fixed_selection.json')
    q = read('data/v39/frozen_queries.json')['queries'][2]
    w = read('data/v44/assessment.json')['queries'][0]['runs'][0]
    assert selection == {'quote': q, 'witness': w} and w['token_count'] == 22
    source = (ROOT / cfg['source_text']).read_text(); target = read('data/v38/target_export.json')['text']
    assert source == read('data/v42/page_observations.json')['text']
    assert target[slice(*q['span'])] == q['text']
    assert target[slice(*w['target_char_span'])] == w['query_fragment'] == q['text'][slice(*w['query_char_span'])]
    assert source[slice(*w['source_char_span'])] == w['source_fragment']
    soup = BeautifulSoup((ROOT / cfg['raw_html']).read_bytes(), 'html.parser')
    for tag in soup.select('script,style,noscript,template,svg,canvas'):
        tag.decompose()
    bodies = soup.select('body'); assert len(bodies) == 1
    assert bodies[0].get_text(' ', strip=True) == source
    paragraphs = [p.get_text(' ', strip=True) for p in bodies[0].select('p')]
    candidates = []
    for i, text in enumerate(paragraphs):
        for a, b in locate(text, source):
            if a <= w['source_char_span'][0] < w['source_char_span'][1] <= b:
                candidates.append({'paragraph_index': i, 'body_span': [a, b], 'text': text})
    d = read('data/v45/dossier.json')
    assert d['status'] == 'context_available' and d['paragraph_candidates'] == candidates and len(candidates) == 1
    selected = candidates[0]; assert d['selected_paragraph'] == selected and selected['paragraph_index'] == 16
    assert selected['body_span'] == [7109, 7437]
    for field, text, offset, span in [('target_partition', q['text'], q['span'][0], w['query_char_span']),
                                      ('source_partition', selected['text'], selected['body_span'][0],
                                       [v - selected['body_span'][0] for v in w['source_char_span']])]:
        expected_spans = [[0, span[0]], span, [span[1], len(text)]]
        assert [r['part'] for r in d[field]] == ['prefix', 'fixed_shared_span', 'suffix']
        for row, (a, b) in zip(d[field], expected_spans, strict=True):
            assert row['local_span'] == [a, b] and row['global_span'] == [offset + a, offset + b]
            assert row['text'] == text[a:b]
        assert ''.join(r['text'] for r in d[field]) == text
    assert [len(r['text']) for r in d['target_partition']] == [112, 127, 166]
    assert [len(r['text']) for r in d['source_partition']] == [201, 127, 0]
    index = selected['paragraph_index']
    expected_window = [{'paragraph_index': i, 'text': paragraphs[i], 'body_spans': locate(paragraphs[i], source)}
                       for i in range(max(0, index - 1), min(len(paragraphs), index + 2))]
    assert d['publisher_window'] == expected_window
    a = max(0, q['span'][0] - 160); b = min(len(target), q['span'][1] + 160)
    assert d['target_context'] == {'span': [a, b], 'text': target[a:b], 'quote_span_within_context': [q['span'][0] - a, q['span'][1] - a]}
    scopes = {'target_quote': q['text'], 'publisher_paragraph': selected['text'], 'publisher_body': source}
    offsets = {'target_quote': q['span'][0], 'publisher_paragraph': selected['body_span'][0], 'publisher_body': 0}
    queries = {'target_prefix': d['target_partition'][0]['text'], 'target_suffix': d['target_partition'][2]['text'],
               'beacon_phrase': 'Giselian beacon', 'reported_name': 'Alan Watson', 'fixed_shared_fragment': w['query_fragment']}
    assert [c['check_id'] for c in d['context_checks']] == cfg['literal_check_ids'] and len(d['context_checks']) == 11
    for c in d['context_checks']:
        label, scope = c['check_id'].split(':')
        assert c['query'] == queries[label] and c['scope'] == scope and c['scope_offset'] == offsets[scope]
        hits(c['query'], scopes[scope], c['hits'])
        assert c['present'] == bool(c['hits'])
    expected_flags = [False, False, False, False, True, False, False, True, True, True, True]
    assert [c['present'] for c in d['context_checks']] == expected_flags
    assert d['partition_reassembly_passed'] and d['fixed_witness_unchanged']
    assert d['opaque_passages_scored'] == 0 and not d['original_attribution_authenticated']
    markdown = (ROOT / 'data/v45/dossier.md').read_text()
    assert all(row['text'] in markdown for row in d['target_partition'] + d['source_partition'] + d['publisher_window'])
    assert d['target_context']['text'] in markdown
    review = read('data/v45/context_review.json'); report = read('runs/000045_context_dossier/report.json')
    assert review['speaker_as_reported'] == 'Alan Watson' and review['target_first_person_wording_observed']
    assert 'Alan Watson' in selected['text'] and q['text'].startswith("I don't think") and 'I do agree' in q['text']
    assert not review['original_attribution_authenticated'] and not review['copying_direction_established']
    assert report['case_denominator'] == 1 and report['fixed_witness_tokens'] == 22 and not report['fixed_witness_changed']
    assert report['context_available'] and report['literal_check_denominator'] == report['literal_checks_available'] == 11
    assert report['publisher_paragraph_index'] == 16 and report['partition_reassembly_passed']
    assert report['source_reextractions_from_frozen_bytes'] == 1 and not report['original_attribution_authenticated']
    for k in ['network_requests', 'new_overlap_assessments', 'opaque_passages_scored', 'semantic_labels_admitted',
              'source_identities_admitted', 'independent_reviews_admitted', 'untouched_test_units_admitted', 'external_messages_sent']:
        assert report[k] == 0
    assert report['semantic_evaluation_metrics'] is report['scientific_acceptance'] is None
    previous = []
    for path in sorted((ROOT / 'runs').glob('000*/manifest.json')):
        if path.parent != run:
            check_hashes(path.parent); previous.append(path.parent.name)
    assert len(previous) == 44
    for path in (ROOT / 'reports').glob('*_deliverable_seal.json'):
        for p, expected in json.loads(path.read_text()).get('deliverable_hashes', {}).items():
            assert sha(p) == expected
    result = {'state': 'verified', 'manifest_sha256': sha('runs/000045_context_dossier/manifest.json'),
              'fixed_witness_and_inputs_verified': True, 'body_reproduction_and_unique_paragraph_verified': True,
              'partitions_windows_and_all_literal_checks_verified': True, 'shared_html_parser': 'BeautifulSoup html.parser',
              'independent_scientific_review': False, 'opaque_semantics_or_original_attribution_authenticated': False,
              'prior_runs_preserved': previous}
    out = ROOT / 'reports/000045_verification.json'
    if out.exists():
        assert {k: v for k, v in json.loads(out.read_text()).items() if k != 'verified_at_utc'} == result
    else:
        with out.open('x') as stream:
            json.dump(result | {'verified_at_utc': datetime.now(timezone.utc).isoformat()}, stream, indent=2); stream.write('\n')
    print(json.dumps({'state': 'verified', 'prior_runs_preserved': len(previous), 'publisher_paragraph': index, 'literal_checks': 11}, indent=2))


if __name__ == '__main__':
    main()
