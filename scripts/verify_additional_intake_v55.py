"""Offline replay of snapshot, two search slots, captures and cumulative capacity."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys
from urllib.parse import urljoin
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from verify_correspondence_v6 import check_hashes
from verify_cohort_scope_v52 import reconstruct as scope_replay
from verify_offline_intake_v54 import observations, decision
from verify_routing_v53 import key, title, reconstruct as route_replay
from verify_publisher_intake_v50 import topic


def read(p): return json.loads((ROOT / p).read_text())
def sha(p): return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()
def article(url):
    path = key(url)
    return 'https://physicsworld.com' + path + '/' if path and path.startswith('/a/') else None


def search_text(response):
    if isinstance(response, str): return response
    if isinstance(response, dict) and isinstance(response.get('content'), list):
        blocks = response['content']
        if all(isinstance(b, dict) and b.get('type') == 'text' and isinstance(b.get('text'), str) for b in blocks):
            return '\n'.join(b['text'] for b in blocks)
    return None


def reconstruct_prior(prior):
    exposures = {k: set(v) for k, v in read('data/v50_registration/prior_urls.json')['article_exposures'].items()}
    def add(url, tag):
        value = article(url)
        if value: exposures.setdefault(value, set()).add(tag)
    for query in read('data/v50/selection.json')['queries']:
        for row in query['hits']: add(row['url'], 'v50_search_result')
    expected_pages = [{'path': p['raw'], 'url': p['url']} for p in read('experiments/cohort_scope_v52.json')['pages']]
    expected_pages += [{'path': f"data/v53/acquisition/{p['id']}/body.bin", 'url': p['canonical_url']} for p in read('experiments/routing_v53.json')['routes']]
    assert prior['pages'] == expected_pages and len(expected_pages) == 9
    for page in expected_pages:
        raw = (ROOT / page['path']).read_bytes(); add(page['url'], page['path'] + ':captured_page')
        soup = BeautifulSoup(raw, 'html.parser')
        for link in soup.select('a[href]'): add(urljoin(page['url'], link['href']), page['path'] + ':link')
        for item in observations(raw)['urls']: add(item['value'], page['path'] + ':identity')
    assert prior['article_exposures'] == {k: sorted(v) for k, v in sorted(exposures.items())}
    assert prior['excluded_article_keys'] == sorted(exposures)
    for p, h in prior['input_hashes'].items(): assert sha(p) == h


def reconstruct_selection(cfg, pre, prior):
    queries = []; slots = []; seen = set(); previous = pre['sealed_at_utc']
    saved_selection = read('data/v55/selection.json')
    for i in range(2):
        intent = read(f'data/v55/discovery/query{i:02d}_intent.json'); saved = read(f'data/v55/discovery/query{i:02d}_response.json')
        assert intent['query_index'] == saved['query_index'] == i and intent['tool'] == saved['tool'] == 'web.run'
        assert intent['request_arguments'] == saved['request_arguments'] == cfg['search_requests'][i]
        assert previous < intent['started_at_utc'] <= saved['finished_at_utc'] < saved_selection['selected_at_utc']
        previous = saved['finished_at_utc']
        text = search_text(saved['response']) if saved['error'] is None else None
        headers = []; offset = 0
        if text is not None:
            lines = text.splitlines(keepends=True)
            for n, line in enumerate(lines):
                raw_line = line.rstrip('\r\n'); at = raw_line.rfind(' (http')
                if at > 0 and raw_line.endswith(')') and n + 1 < len(lines) and 'wordlim' in lines[n + 1]:
                    url = raw_line[at + 2:-1]
                    if not any(c.isspace() for c in url): headers.append((offset, raw_line[:at], url))
                offset += len(line)
        rows = []; chosen = None
        for rank, (start, label, url) in enumerate(headers):
            end = headers[rank + 1][0] if rank + 1 < len(headers) else len(text)
            block = text[start:end]; value = article(url); duplicate = value is not None and value in seen
            if value: seen.add(value)
            topical = topic(label + '\n' + block)
            reason = ('invalid_article_url' if value is None else 'duplicate_returned_url' if duplicate else
                      'prior_recorded_url_exposure' if value in prior['excluded_article_keys'] else
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
    for kind in ['intent', 'response']: assert len(list((ROOT / 'data/v55/discovery').glob(f'*_{kind}.json'))) == 2
    return saved_selection


def capture_check(base, url, sid, limits, earliest, latest):
    receipt = read(base + '/receipt.json'); dest = ROOT / base
    assert receipt['id'] == sid and receipt['requested_url'] == url
    assert earliest < receipt['started_at_utc'] <= receipt['finished_at_utc'] < latest
    cmd = ['curl', '--disable', '--silent', '--show-error', '--location', '--compressed', '--proto', '=https', '--proto-redir', '=https',
        '--retry', '0', '--connect-timeout', '8', '--max-time', '20', '--max-redirs', '3', '--max-filesize', '4194304',
        '--user-agent', limits['user_agent'], '--output', str(dest / 'body.bin'), '--dump-header', str(dest / 'headers.txt'), '--write-out', '%{json}', url]
    assert receipt['command'] == cmd
    files = {p.name for p in dest.iterdir() if p.name != 'receipt.json'}; assert files == set(receipt['artifacts'])
    for name, info in receipt['artifacts'].items(): assert info == {'sha256': sha(base + '/' + name), 'bytes': (dest / name).stat().st_size}
    try: telemetry = read(base + '/curl_stdout.bin')
    except (ValueError, TypeError): telemetry = {}
    for field, source in [('final_url', 'url_effective'), ('http_status', 'http_code'), ('num_redirects', 'num_redirects'), ('content_type', 'content_type')]:
        assert receipt[field] == telemetry.get(source)
    complete = receipt['curl_returncode'] == 0 and receipt['http_status'] == 200 and 'body.bin' in files and (dest / 'body.bin').stat().st_size <= 4194304
    assert receipt['transport_complete'] == complete
    raw = (dest / 'body.bin').read_bytes() if 'body.bin' in files else b''
    headers = (dest / 'headers.txt').read_bytes() if 'headers.txt' in files else b''
    return receipt, raw, headers


def main():
    run = ROOT / 'runs/000055_additional_intake'; check_hashes(run)
    cfg = read('experiments/additional_intake_v55.json'); pre = read('data/v55/preflight.json')
    report = read('runs/000055_additional_intake/report.json'); manifest = read('runs/000055_additional_intake/manifest.json')
    for p, h in pre['hashes'].items(): assert sha(p) == h, p
    for p, h in cfg['input_hashes'].items(): assert pre['hashes'][p] == h
    assert pre['hashes']['experiments/additional_intake_v55.json'] == sha('experiments/additional_intake_v55.json')
    assert cfg['registered_at_utc'] < pre['sealed_at_utc'] < manifest['finished_at_utc']
    assert cfg['search_call_budget'] == cfg['nomination_slots'] == cfg['native_route_budget'] == cfg['alias_route_budget'] == 2
    assert cfg['slots_per_query'] == 1 and cfg['maximum_application_requests_including_redirects'] == 16
    queries = ['site:physicsworld.com/a/ ANITA Antarctic neutrino balloon after:1999-12-31 before:2018-10-01',
               'site:physicsworld.com/a/ Antarctic neutrino detector IceCube after:1999-12-31 before:2018-10-01']
    assert cfg['search_requests'] == pre['registered_search_requests'] == [{'search_query': [{'q': q}], 'response_length': 'long'} for q in queries]
    original = read('experiments/offline_intake_v54.json')
    for k, v in cfg['eligibility_rule'].items(): assert original[k] == v
    assert cfg['request_limits'] == {'connect_timeout_seconds': 8, 'total_timeout_seconds': 20, 'max_redirects': 3,
        'max_body_bytes': 4194304, 'user_agent': 'FL-Decipher registered additional intake v55'}
    prior = read(cfg['prior_snapshot']); reconstruct_prior(prior); assert prior['created_at_utc'] < cfg['registered_at_utc']
    selection = reconstruct_selection(cfg, pre, prior); capture_pre = read('data/v55/capture_preflight.json')
    for p, h in capture_pre['hashes'].items(): assert sha(p) == h
    assert selection['selected_at_utc'] < capture_pre['sealed_at_utc']
    assert capture_pre['requests'] == [{'slot_id': s['slot_id'], 'url': s['nominee']['url']} for s in selection['slots'] if s['nominee']]
    results = []; aliases = 0; app_responses = 0; expected_native = []; expected_alias = []; leaves = 0
    for slot in selection['slots']:
        sid = slot['slot_id']; nominee = slot['nominee']
        if nominee is None:
            results.append({'slot_id': sid, 'occupied': False, 'development_capture_eligible': False, 'unmet': ['empty_nomination_slot']}); continue
        expected_native.append(sid)
        expected_title = re.sub(r'\s+[–—|\-]\s+Physics World\s*$', '', nominee['title'])
        spec = {'id': sid, 'url': nominee['url'], 'expected_title': expected_title, 'v50_ready_unchanged': None}
        assert spec == read(f'data/v55/{sid}_spec.json') and article(spec['url']) not in prior['excluded_article_keys']
        base = f'data/v55/acquisition/{sid}'
        receipt, raw, headers = capture_check(base, spec['url'], sid, cfg['request_limits'], capture_pre['sealed_at_utc'], manifest['finished_at_utc'])
        app_responses += len([s for s in headers.decode('iso-8859-1').splitlines() if re.match(r'HTTP/\S+\s+[2-5][0-9]{2}', s) and 'connection established' not in s.lower()])
        soup = BeautifulSoup(raw, 'html.parser')
        for tag in soup.select('script,style,noscript,template,svg,canvas'): tag.decompose()
        bodies = soup.select('body'); body = bodies[0].get_text(' ', strip=True) if len(bodies) == 1 else ''
        scope, checks = scope_replay(raw, body, cfg['eligibility_rule']['source_selector'])
        assert scope == read(f'data/v55/{sid}_scope.json'); leaves += len(scope['container_leaves'])
        meta = observations(raw); expected = key(spec['url']); canon = [u['value'] for u in meta['urls'] if u['channel'] == 'canonical']
        og = [u['value'] for u in meta['urls'] if u['channel'] == 'og_url']; different = list(dict.fromkeys(u for u in og if key(u) != expected))
        titles_ok = {'html_title', 'og_title', 'article_headline'} <= {t['channel'] for t in meta['titles']} and not meta['json_ld_parse_errors'] and all(title(t['value']) == title(expected_title) for t in meta['titles'])
        native_ok = bool(receipt['transport_complete'] and expected and key(receipt['final_url']) == expected and canon and all(key(u) == expected for u in canon) and titles_ok)
        permitted = bool(native_ok and len(different) == 1 and key(different[0]) is not None)
        plan = read(f'data/v55/{sid}_alias_plan.json')
        assert plan['request_url'] == (different[0] if permitted else None)
        assert plan['observed_og_urls'] == og and plan['distinct_noncanonical_values'] == different and plan['native_identity_and_titles_pass'] == native_ok
        assert plan['reason'] == ('one_safe_observed_alternate' if permitted else 'all_og_urls_direct' if og and not different else 'native_identity_or_alternate_unavailable')
        native_paths = sorted(str(p.relative_to(ROOT)) for p in (ROOT / base).iterdir() if p.is_file())
        assert plan['native_input_hashes'] == {p: sha(p) for p in native_paths}
        assert receipt['finished_at_utc'] <= plan['sealed_at_utc'] < manifest['finished_at_utc']
        route = None
        if permitted:
            expected_alias.append(sid); aliases += 1
            route_spec = {'id': sid, 'og_url': different[0], 'canonical_url': spec['url'], 'expected_title': expected_title,
                          'old_body_sha256': hashlib.sha256(raw).hexdigest(), 'v50_ready_unchanged': None}
            assert read(f'data/v55/{sid}_route_spec.json') == route_spec
            ar, ab, ah = capture_check(f'data/v55/alias_acquisition/{sid}', different[0], sid, cfg['request_limits'], plan['sealed_at_utc'], manifest['finished_at_utc'])
            route = route_replay(ab, ah, ar, route_spec); assert route == read(f'data/v55/{sid}_route.json')
            app_responses += len(route['chain'])
        obs = decision(raw, receipt, spec, cfg['eligibility_rule'], body, scope, checks, route)
        for binding in obs['og_url_bindings']:
            if binding['binding'] == 'saved_v53_redirect': binding['binding'] = 'saved_v55_redirect'
        obs['route_evidence_origin'] = 'v55' if route is not None else None
        obs['exposure_status'] = 'development_data_after_this_intake; no complete prior-familiarity guarantee'
        assert obs == read(f'data/v55/{sid}_decision.json')
        results.append({'slot_id': sid, 'occupied': True, 'url': spec['url'], 'expected_title': expected_title,
            'http_status': receipt['http_status'], 'curl_returncode': receipt['curl_returncode'], 'alias_attempted': route is not None,
            'development_capture_eligible': obs['development_capture_eligible'], 'unmet': obs['unmet'],
            'publication_dates': obs['parsed_publication_dates'], 'paragraph_runs': obs['paragraph_run_count'], 'paragraph_run_characters': obs['paragraph_run_characters']})
    for folder, expected_ids in [('acquisition', expected_native), ('alias_acquisition', expected_alias)]:
        assert sorted(p.parent.name for p in (ROOT / 'data/v55' / folder).glob('*/receipt.json')) == sorted(expected_ids)
    assert report['slot_results'] == results and report['search_tool_calls'] == report['search_queries'] == 2
    assert report['occupied_slots'] == report['native_routes_attempted'] == len(expected_native) <= 2
    assert report['alias_routes_attempted'] == aliases <= 2 and report['empty_slots'] == 2 - len(expected_native)
    assert report['recorded_application_responses'] == app_responses <= 16
    old = read('runs/000054_offline_intake/report.json'); old_eligible = old['eligible_candidate_ids']
    assert old['eligible_development_candidates'] == 2 and old['development_intake_capacity_met'] is False
    new_ids = ['v55:' + r['slot_id'] for r in results if r['development_capture_eligible']]
    ids = ['v50:' + x for x in old_eligible] + new_ids
    assert report['new_cohort_slot_denominator'] == 2 and report['new_eligible_candidates'] == len(new_ids)
    assert report['cumulative_slot_denominator'] == 6 and report['capacity_required'] == 4 and report['reference_counted_as_candidate'] is False
    assert report['cumulative_eligible_ids'] == ids and report['cumulative_eligible_candidates'] == len(ids)
    assert report['cumulative_capture_capacity_met'] == (len(ids) >= 4) and report['candidate_shortage'] == max(0, 4 - len(ids))
    assert report['v50_ready_captures_unchanged'] == 1 and report['v54_eligible_candidates_unchanged'] == 2
    assert report['v50_and_v54_original_capacity_failures_preserved'] is True and report['natural_benchmark_capacity_met'] is False
    for k in ['natural_benchmark_qualifying_works_from_intake', 'scaffold_or_alignment_scores', 'opaque_lexical_or_semantic_scores',
              'source_identities_admitted', 'independent_reviews_admitted', 'untouched_test_units_admitted', 'external_messages_sent']: assert report[k] == 0
    assert report['scientific_acceptance'] is report['semantic_evaluation_metrics'] is None
    previous = []
    for p in sorted((ROOT / 'runs').glob('000*/manifest.json')):
        if p.parent != run: check_hashes(p.parent); previous.append(p.parent.name)
    assert len(previous) == 54
    for seal in (ROOT / 'reports').glob('*_deliverable_seal.json'):
        for p, h in json.loads(seal.read_text()).get('deliverable_hashes', {}).items(): assert sha(p) == h, p
    result = {'state': 'verified', 'manifest_sha256': sha('runs/000055_additional_intake/manifest.json'),
        'prior_snapshot_article_urls': len(prior['excluded_article_keys']), 'search_calls_verified': 2,
        'attributable_hits': [q['attributable_hits'] for q in selection['queries']],
        'native_routes_verified': len(expected_native), 'alias_routes_verified': aliases,
        'recorded_application_responses': app_responses, 'container_leaves_reconstructed': leaves,
        'new_eligible_candidates': len(new_ids), 'cumulative_eligible_candidates': len(ids), 'cumulative_slot_denominator': 6,
        'prior_snapshot_selection_requests_scope_and_decisions_reconstructed': True,
        'production_nomination_and_evaluator_not_used': True, 'verification_network_requests': 0,
        'shared_html_parser': 'BeautifulSoup html.parser', 'independent_scientific_review': False,
        'semantics_or_source_identity_validated': False, 'prior_runs_preserved': previous}
    out = ROOT / 'reports/000055_verification.json'
    if out.exists(): assert {k: v for k, v in json.loads(out.read_text()).items() if k != 'verified_at_utc'} == result
    else:
        with out.open('x') as stream: json.dump(result | {'verified_at_utc': datetime.now(timezone.utc).isoformat()}, stream, indent=2); stream.write('\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'prior_runs_preserved'} | {'prior_runs_preserved': len(previous)}, indent=2))


if __name__ == '__main__': main()
