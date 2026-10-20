"""Replay the completed empty-slot discovery result without new requests."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
from urllib.parse import urljoin
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from verify_correspondence_v6 import check_hashes
from verify_routing_v53 import key
from verify_offline_intake_v54 import observations
from verify_publisher_intake_v50 import topic
from verify_additional_intake_v55 import search_text


def read(p): return json.loads((ROOT / p).read_text())
def sha(p): return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()
def article(url):
    path = key(url)
    return 'https://physicsworld.com' + path + '/' if path and path.startswith('/a/') else None


def reconstruct_prior(prior):
    old = read('data/v55_registration/prior_urls.json'); exposures = {k: set(v) for k, v in old['article_exposures'].items()}
    def add(url, tag):
        value = article(url)
        if value: exposures.setdefault(value, set()).add(tag)
    for query in read('data/v55/selection.json')['queries']:
        for hit in query['hits']: add(hit['url'], 'v55_search_result')
    pages = []
    for sid in ['q00s00', 'q01s00']:
        spec = read(f'data/v55/{sid}_spec.json'); path = f'data/v55/acquisition/{sid}/body.bin'
        pages.append({'path': path, 'url': spec['url']}); raw = (ROOT / path).read_bytes()
        add(spec['url'], path + ':captured_page')
        for tag in BeautifulSoup(raw, 'html.parser').select('a[href]'): add(urljoin(spec['url'], tag['href']), path + ':link')
        for entry in observations(raw)['urls']: add(entry['value'], path + ':identity')
    assert prior['pages'] == pages
    assert prior['article_exposures'] == {k: sorted(v) for k, v in sorted(exposures.items())}
    captured = sorted({article(p['url']) for p in old['pages'] + pages})
    assert None not in captured and len(captured) == 7 and prior['captured_article_keys'] == captured
    assert set(captured) <= set(exposures)
    for p, h in prior['input_hashes'].items(): assert sha(p) == h, p


def reconstruct_selection(cfg, pre, prior):
    saved_selection = read('data/v58/selection.json'); previous = pre['sealed_at_utc']; queries = []; slots = []; seen = set()
    for i in range(2):
        intent = read(f'data/v58/discovery/query{i:02d}_intent.json'); saved = read(f'data/v58/discovery/query{i:02d}_response.json')
        assert intent['query_index'] == saved['query_index'] == i and intent['tool'] == saved['tool'] == 'web.run'
        assert intent['request_arguments'] == saved['request_arguments'] == cfg['search_requests'][i]
        assert previous < intent['started_at_utc'] <= saved['finished_at_utc'] < saved_selection['selected_at_utc']
        previous = saved['finished_at_utc']
        text = search_text(saved['response']) if saved['error'] is None else None; headers = []; offset = 0
        if text is not None:
            lines = text.splitlines(keepends=True)
            for n, line in enumerate(lines):
                raw = line.rstrip('\r\n'); at = raw.rfind(' (http')
                if at > 0 and raw.endswith(')') and n + 1 < len(lines) and 'wordlim' in lines[n + 1]:
                    url = raw[at + 2:-1]
                    if not any(c.isspace() for c in url): headers.append((offset, raw[:at], url))
                offset += len(line)
        rows = []; chosen = None
        for rank, (start, label, url) in enumerate(headers):
            end = headers[rank + 1][0] if rank + 1 < len(headers) else len(text); block = text[start:end]
            value = article(url); duplicate = value is not None and value in seen
            if value: seen.add(value)
            topical = topic(label + '\n' + block)
            reason = ('invalid_article_url' if value is None else 'duplicate_returned_url' if duplicate else
                      'previously_captured_url' if value in prior['captured_article_keys'] else
                      'topic_terms_missing' if not topical else 'query_slot_cap' if chosen is not None else 'selected_first_eligible')
            row = {'rank': rank, 'title': label, 'url': url, 'response_span': [start, end], 'response_text': block,
                'response_text_sha256': hashlib.sha256(block.encode()).hexdigest(), 'article_key': value,
                'prior_exposure_tags': prior['article_exposures'].get(value, []), 'topical': topical,
                'decision_reason': reason, 'nominated': reason == 'selected_first_eligible'}
            rows.append(row)
            if row['nominated']: chosen = row
        queries.append({'query_index': i, 'response_format_supported': text is not None, 'attributable_hits': len(rows), 'hits': rows})
        slots.append({'slot_id': f'q{i:02d}s00', 'query_index': i, 'nominee':
            {k: chosen[k] for k in ['rank', 'title', 'url', 'article_key', 'prior_exposure_tags']} if chosen else None})
    assert saved_selection['queries'] == queries and saved_selection['slots'] == slots
    assert saved_selection['occupied_slots'] == sum(s['nominee'] is not None for s in slots)
    for kind in ['intent', 'response']: assert len(list((ROOT / 'data/v58/discovery').glob(f'*_{kind}.json'))) == 2
    return saved_selection


def main():
    run = ROOT / 'runs/000058_hard_comparator'; check_hashes(run)
    cfg = read('experiments/hard_comparator_v58.json'); pre = read('data/v58/preflight.json')
    report = read('runs/000058_hard_comparator/report.json'); manifest = read('runs/000058_hard_comparator/manifest.json')
    for p, h in pre['hashes'].items(): assert sha(p) == h, p
    for p, h in cfg['input_hashes'].items(): assert pre['hashes'][p] == h
    assert pre['hashes']['experiments/hard_comparator_v58.json'] == sha('experiments/hard_comparator_v58.json')
    assert cfg['registered_at_utc'] < pre['sealed_at_utc'] < manifest['finished_at_utc']
    assert cfg['search_call_budget'] == cfg['nomination_slots'] == cfg['native_route_budget'] == cfg['alias_route_budget'] == 2
    assert cfg['slots_per_query'] == 1 and cfg['maximum_application_requests_including_redirects'] == 16 and cfg['minimum_shared_numeric_types'] == 3
    queries = ['site:physicsworld.com/a/ ANITA "96" "40" after:1999-12-31 before:2018-10-01',
               'site:physicsworld.com/a/ Antarctic neutrino "180" "2006" after:1999-12-31 before:2018-10-01']
    assert cfg['search_requests'] == pre['registered_search_requests'] == [{'search_query': [{'q': q}], 'response_length': 'long'} for q in queries]
    original = read('experiments/additional_intake_v55.json')
    assert cfg['eligibility_rule'] == original['eligibility_rule']
    assert cfg['request_limits'] == original['request_limits'] | {'user_agent': 'FL-Decipher registered harder comparator intake v58'}
    prior = read(cfg['prior_snapshot']); reconstruct_prior(prior); assert prior['created_at_utc'] < cfg['registered_at_utc']
    selection = reconstruct_selection(cfg, pre, prior); capture = read('data/v58/capture_preflight.json')
    for p, h in capture['hashes'].items(): assert sha(p) == h
    assert selection['selected_at_utc'] < capture['sealed_at_utc'] < manifest['finished_at_utc']
    assert capture['requests'] == [] and selection['occupied_slots'] == 0
    expected_rows = [{'slot_id': s['slot_id'], 'occupied': False, 'development_capture_eligible': False,
                      'qualifying_harder_comparator': False, 'unmet': ['empty_nomination_slot']} for s in selection['slots']]
    assert report['slot_results'] == expected_rows and len(expected_rows) == report['nomination_slot_denominator'] == 2
    assert report['occupied_slots'] == report['native_routes_attempted'] == report['alias_routes_attempted'] == report['recorded_application_responses'] == 0
    assert report['empty_slots'] == 2 and report['search_tool_calls'] == report['search_queries'] == 2
    # This completed run never reached capture/overlap evaluation; do not claim those branches were live-tested.
    assert not (ROOT / 'data/v58/acquisition').exists() and not (ROOT / 'data/v58/alias_acquisition').exists()
    expected_files = {'preflight.json', 'selection.json', 'capture_preflight.json'} | {f'discovery/query{i:02d}_{kind}.json' for i in range(2) for kind in ['intent', 'response']}
    assert {str(p.relative_to(ROOT / 'data/v58')) for p in (ROOT / 'data/v58').rglob('*') if p.is_file()} == expected_files
    assert report['minimum_shared_numeric_types'] == 3 and report['native_eligible_candidates'] == report['qualifying_harder_comparators'] == 0
    assert report['registered_feasibility_gate'] is report['both_slots_qualified'] is False
    assert report['outcome'] == 'no_qualifying_comparator_within_budget' and report['previous_results_preserved'] is True
    assert report['previous_e56_comparators_unchanged'] == 4
    assert report['natural_benchmark_capacity_met'] is False
    for k in ['natural_benchmark_qualifying_works_from_intake', 'scaffold_or_alignment_scores', 'opaque_lexical_or_semantic_scores',
              'source_identities_admitted', 'independent_reviews_admitted', 'untouched_test_units_admitted', 'external_messages_sent']: assert report[k] == 0
    assert report['scientific_acceptance'] is report['semantic_evaluation_metrics'] is None
    previous = []
    for path in sorted((ROOT / 'runs').glob('000*/manifest.json')):
        if path.parent != run: check_hashes(path.parent); previous.append(path.parent.name)
    assert len(previous) == 57
    for seal in (ROOT / 'reports').glob('*_deliverable_seal.json'):
        for p, h in json.loads(seal.read_text()).get('deliverable_hashes', {}).items(): assert sha(p) == h, p
    reasons = dict(sorted(Counter(h['decision_reason'] for q in selection['queries'] for h in q['hits']).items()))
    result = {'state': 'verified', 'manifest_sha256': sha('runs/000058_hard_comparator/manifest.json'),
        'prior_exposure_urls_verified': len(prior['article_exposures']), 'captured_urls_excluded': len(prior['captured_article_keys']),
        'search_calls_verified': 2, 'attributable_hits': [q['attributable_hits'] for q in selection['queries']],
        'nomination_decision_counts': reasons, 'empty_slots_verified': 2, 'native_or_alias_requests_recorded': 0,
        'new_candidate_numeric_threshold_evaluated': False, 'production_nomination_not_used': True,
        'shared_html_parser': 'BeautifulSoup html.parser', 'verification_network_requests': 0,
        'independent_scientific_review': False, 'semantics_or_source_identity_validated': False, 'prior_runs_preserved': previous}
    out = ROOT / 'reports/000058_verification.json'
    if out.exists(): assert {k: v for k, v in json.loads(out.read_text()).items() if k != 'verified_at_utc'} == result
    else:
        with out.open('x') as stream: json.dump(result | {'verified_at_utc': datetime.now(timezone.utc).isoformat()}, stream, indent=2); stream.write('\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'prior_runs_preserved'} | {'prior_runs_preserved': len(previous)}, indent=2))


if __name__ == '__main__': main()
