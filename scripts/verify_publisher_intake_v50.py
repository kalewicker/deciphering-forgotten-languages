"""Offline intake replay: requests, first-appearance selection and native scopes."""
from datetime import date, datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys
import unicodedata
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from verify_correspondence_v6 import check_hashes


def read(p): return json.loads((ROOT / p).read_text())
def sha(p): return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()
def norm(s): return ' '.join(unicodedata.normalize('NFC', s).casefold().split())


def key(url):
    if not isinstance(url, str): return None
    try:
        p = urlparse(url); parts = p.path.rstrip('/').split('/')
        # A second trailing slash is not an accepted article URL.
        good = (p.scheme == 'https' and p.netloc in ['physicsworld.com', 'physicsworld.com:443'] and not p.params
                and not p.query and not p.fragment and len(parts) == 3 and parts[:2] == ['', 'a'] and parts[2]
                and not any(c.isspace() for c in p.path) and not p.path.endswith('//'))
        return 'https://physicsworld.com/a/' + parts[2] + '/' if good else None
    except ValueError: return None


def topic(s):
    words = set(re.findall(r'\b\w+\b', norm(s)))
    return bool(words.intersection({'neutrino', 'neutrinos'}) and words.intersection({'anita', 'antarctic', 'antarctica'}))


def main():
    run = ROOT / 'runs/000050_publisher_intake'; check_hashes(run)
    cfg = read('experiments/publisher_intake_v50.json'); pre = read('data/v50/preflight.json')
    manifest = read('runs/000050_publisher_intake/manifest.json')
    for p, h in pre['hashes'].items(): assert sha(p) == h, p
    for p, h in cfg['input_hashes'].items(): assert pre['hashes'][p] == h
    assert pre['hashes']['experiments/publisher_intake_v50.json'] == sha('experiments/publisher_intake_v50.json')
    assert cfg['registered_at_utc'] < pre['sealed_at_utc'] < manifest['finished_at_utc']
    assert cfg['search_call_budget'] == cfg['slots_per_query'] == 2 and cfg['nomination_slots'] == cfg['native_route_budget'] == 4
    assert cfg['date_min'] == '2000-01-01' and cfg['date_max'] == '2018-09-30'
    queries = ['site:physicsworld.com/a/ ANITA neutrino after:1999-12-31 before:2018-10-01',
               'site:physicsworld.com/a/ Antarctic neutrino radio after:1999-12-31 before:2018-10-01']
    assert cfg['search_requests'] == pre['registered_search_requests'] == [{'search_query': [{'q': q}], 'response_length': 'long'} for q in queries]
    snapshot = read(cfg['prior_snapshot']); exposures = {}
    for p, h in snapshot['input_hashes'].items(): assert sha(p) == h
    def add(url, tag):
        k = key(url)
        if k: exposures.setdefault(k, set()).add(tag)
    for url in read('data/v37/known_exposure.json')['urls']: add(url, 'v37_known_url_snapshot')
    for r in read('data/v41/discovery_ledger.json')['hit_ledger']: add(r['url'], 'v41_search_result')
    for url in read('data/v42/page_observations.json')['identity_urls']: add(url, 'v42_captured_identity')
    original_source = 'https://physicsworld.com/a/mysterious-radio-signals-could-be-from-new-type-of-neutrino/'
    soup = BeautifulSoup((ROOT / 'data/v42/acquisition/source/body.bin').read_bytes(), 'html.parser')
    for tag in soup.find_all('a', href=True): add(urljoin(original_source, tag['href']), 'v42_saved_html_link')
    add(original_source, 'v42_previously_captured_source')
    assert snapshot['article_exposures'] == {k: sorted(v) for k, v in sorted(exposures.items())}
    assert snapshot['captured_article_keys'] == [original_source] and snapshot['created_at_utc'] < cfg['registered_at_utc']
    selection = read('data/v50/selection.json'); seen = set(); expected_queries = []; slots = []
    prior_finish = None
    for index in range(2):
        intent = read(f'data/v50/discovery/query{index:02d}_intent.json'); saved = read(f'data/v50/discovery/query{index:02d}_response.json')
        assert intent['query_index'] == saved['query_index'] == index and intent['tool'] == saved['tool'] == 'web.run'
        assert intent['request_arguments'] == saved['request_arguments'] == cfg['search_requests'][index]
        start = datetime.fromisoformat(intent['started_at_utc']); finish = datetime.fromisoformat(saved['finished_at_utc'])
        assert datetime.fromisoformat(pre['sealed_at_utc']) < start <= finish < datetime.fromisoformat(selection['selected_at_utc'])
        if prior_finish is not None: assert prior_finish < start
        prior_finish = finish
        text = saved['response']; assert isinstance(text, str) and saved['error'] is None
        lines = text.splitlines(keepends=True); offset = 0; headers = []
        for i, line in enumerate(lines):
            line = line.rstrip('\r\n'); at = line.rfind(' (http')
            if at > 0 and line.endswith(')') and i + 1 < len(lines) and 'wordlim' in lines[i + 1]:
                url = line[at + 2:-1]
                if not any(c.isspace() for c in url): headers.append((offset, line[:at], url))
            offset += len(lines[i])
        rows = []; chosen = []
        for rank, (start, title, url) in enumerate(headers):
            end = headers[rank + 1][0] if rank + 1 < len(headers) else len(text); block = text[start:end]
            k = key(url); duplicate = k is not None and k in seen
            if k: seen.add(k)
            topical = topic(title + '\n' + block)
            reason = ('invalid_article_url' if k is None else 'duplicate_returned_url' if duplicate else 'already_captured_source' if k == original_source else
                      'topic_terms_missing' if not topical else 'query_slot_cap' if len(chosen) == 2 else 'selected_first_eligible')
            row = {'rank': rank, 'title': title, 'url': url, 'response_span': [start, end], 'response_text': block,
                   'response_text_sha256': hashlib.sha256(block.encode()).hexdigest(), 'article_key': k,
                   'prior_exposure_tags': snapshot['article_exposures'].get(k, []) if k else [], 'topical': topical,
                   'decision_reason': reason, 'nominated': reason == 'selected_first_eligible'}
            rows.append(row)
            if row['nominated']: chosen.append(row)
        expected_queries.append({'query_index': index, 'response_format_supported': True, 'attributable_hits': len(rows), 'hits': rows})
        for slot in range(2):
            r = chosen[slot] if slot < len(chosen) else None
            slots.append({'slot_id': f'q{index:02d}s{slot:02d}', 'query_index': index, 'slot_index': slot,
                          'nominee': {k: r[k] for k in ['rank', 'title', 'url', 'article_key', 'prior_exposure_tags']} if r else None})
    assert selection['queries'] == expected_queries and selection['slots'] == slots
    occupied = sum(s['nominee'] is not None for s in slots); assert selection['occupied_slots'] == occupied
    assert len(list((ROOT / 'data/v50/discovery').glob('*_intent.json'))) == len(list((ROOT / 'data/v50/discovery').glob('*_response.json'))) == 2
    capture = read('data/v50/capture_preflight.json')
    for p, h in capture['hashes'].items(): assert sha(p) == h
    assert selection['selected_at_utc'] < capture['sealed_at_utc']
    assert capture['requests'] == [{'slot_id': s['slot_id'], 'url': s['nominee']['url']} for s in slots if s['nominee']]
    assert len(list((ROOT / 'data/v50/acquisition').glob('*/receipt.json'))) == occupied <= 4
    results = []
    for slot in slots:
        if slot['nominee'] is None:
            results.append({'slot_id': slot['slot_id'], 'occupied': False, 'native_attempted': False, 'ready_for_future_registration': False,
                            'unmet': ['empty_nomination_slot']}); continue
        sid = slot['slot_id']; nominee = slot['nominee']; dest = ROOT / 'data/v50/acquisition' / sid
        receipt = read(f'data/v50/acquisition/{sid}/receipt.json'); obs = read(f'data/v50/observations/{sid}.json')
        assert receipt['attempted'] and receipt['requested_url'] == nominee['url'] and receipt['route_id'] == sid and receipt['kind'] == 'native'
        assert datetime.fromisoformat(capture['sealed_at_utc']) < datetime.fromisoformat(receipt['started_at_utc']) <= datetime.fromisoformat(receipt['finished_at_utc'])
        limits = cfg['request_limits']; maximum = limits['fl_metadata_max_bytes']; cmd = receipt['command']
        assert (limits['connect_timeout_seconds'], limits['total_timeout_seconds'], limits['max_redirects'], maximum) == (8, 20, 3, 4194304)
        assert cmd == ['curl', '--disable', '--silent', '--show-error', '--location', '--compressed', '--proto', '=https', '--proto-redir', '=https',
                       '--connect-timeout', '8', '--max-time', '20', '--max-redirs', '3', '--max-filesize', '4194304', '--user-agent', limits['user_agent'],
                       '--output', str(dest/'body.bin'), '--dump-header', str(dest/'headers.txt'), '--write-out', '%{url_effective}\n%{http_code}', nominee['url']]
        for name, artifact in receipt['artifacts'].items():
            p = dest/name; assert str(p) == artifact['path'] and p.stat().st_size == artifact['bytes'] and hashlib.sha256(p.read_bytes()).hexdigest() == artifact['sha256']
        transport = receipt['curl_returncode'] == 0 and receipt['http_status'] == 200 and 'body.bin' in receipt['artifacts'] and receipt['artifacts']['body.bin']['bytes'] <= maximum
        assert receipt['transport_complete'] == transport
        raw = (dest/'body.bin').read_bytes() if (dest/'body.bin').exists() else b''; soup = BeautifulSoup(raw, 'html.parser')
        headings = [t.get_text(' ', strip=True) for t in soup.select('h1')]
        urls = [t.get('href', '') for t in soup.select('link[rel=canonical]')] + [t.get('content', '') for t in soup.select('meta[property="og:url"]')]
        published = [t.get('content', '') for t in soup.select('meta[property="article:published_time"]')]
        modified = [t.get('content', '') for t in soup.select('meta[property="article:modified_time"]')]
        parsed = []; dates_valid = bool(published)
        for value in published:
            try: parsed.append((date.fromisoformat(value) if len(value) == 10 else datetime.fromisoformat(value).date()).isoformat())
            except (TypeError, ValueError): dates_valid = False
        dates_valid = dates_valid and len(set(parsed)) == 1
        for t in soup.select('script,style,noscript,template,svg,canvas'): t.decompose()
        bodies = soup.select('body'); containers = soup.select(cfg['source_selector']); body = bodies[0].get_text(' ', strip=True) if len(bodies) == 1 else ''
        units = []; mapping = True
        if len(containers) == 1:
            for i, paragraph in enumerate(containers[0].find_all('p', recursive=False)):
                text = paragraph.get_text(' ', strip=True); count = body.count(text) if text else 0
                if text and count != 1: mapping = False
                start = body.find(text) if text and count == 1 else None
                units.append({'unit': i, 'text': text, 'span': [start, start + len(text)] if start is not None else None, 'body_mapping_count': count})
        title = nominee['title']
        for suffix in [' – Physics World', ' — Physics World', ' | Physics World', ' - Physics World']:
            if title.endswith(suffix): title = title[:-len(suffix)]; break
        nonempty = sum(bool(u['text']) for u in units); characters = sum(len(u['text']) for u in units)
        checks = {'transport_complete': transport, 'html_markup': b'<html' in raw.lower(), 'single_body': len(bodies) == 1,
            'final_url_matches': key(receipt['final_url']) == key(nominee['url']), 'publisher_identity_matches': any(key(u) == key(nominee['url']) for u in urls),
            'single_matching_h1': len(headings) == 1 and norm(headings[0]) == norm(title),
            'no_challenge_text': not any(s in body.casefold() for s in cfg['challenge_signatures']), 'single_article_container': len(containers) == 1,
            'unique_nonempty_paragraph_mapping': mapping, 'minimum_paragraphs': nonempty >= cfg['minimum_paragraphs'],
            'minimum_paragraph_characters': characters >= cfg['minimum_paragraph_characters'], 'publication_date_agrees': dates_valid,
            'publication_date_in_window': dates_valid and cfg['date_min'] <= parsed[0] <= cfg['date_max'],
            'native_topic_terms': topic(' '.join(headings) + ' ' + ' '.join(u['text'] for u in units))}
        expected = {'ready_for_future_registration': all(checks.values()), 'checks': checks, 'unmet': [k for k, v in checks.items() if not v],
            'headings': headings, 'identity_urls': urls, 'published_time_values': published, 'parsed_publication_dates': parsed,
            'modified_time_values': modified, 'body_text': body, 'body_text_sha256': hashlib.sha256(body.encode()).hexdigest(),
            'paragraph_units': units, 'paragraph_count': len(units), 'nonempty_paragraph_count': nonempty, 'paragraph_characters': characters,
            'historical_bytes_authenticated': False, 'false_parent_certified': False, 'independent_source_group_admitted': False}
        assert obs == expected
        results.append({'slot_id': sid, 'occupied': True, 'native_attempted': True, 'url': nominee['url'], 'title': nominee['title'],
            'prior_exposure_tags': nominee['prior_exposure_tags'], 'http_status': receipt['http_status'], 'curl_returncode': receipt['curl_returncode'],
            'ready_for_future_registration': all(checks.values()), 'unmet': expected['unmet'], 'publication_dates': parsed,
            'paragraph_count': len(units), 'nonempty_paragraph_count': nonempty, 'paragraph_characters': characters})
    report = read('runs/000050_publisher_intake/report.json'); ready = sum(r['ready_for_future_registration'] for r in results)
    assert report['slot_results'] == results and report['ready_captures'] == ready and report['intake_capacity_met'] == (ready == 4)
    assert report['outcome'] == ('four_ready_captures' if ready == 4 else 'partial_intake' if ready else 'no_ready_captures')
    assert report['occupied_slots'] == report['native_routes_attempted'] == occupied and report['empty_slots'] == 4 - occupied
    assert report['search_tool_calls'] == report['search_queries'] == 2 and report['nomination_slot_denominator'] == report['native_route_budget'] == 4
    for k in ['additional_source_or_page_requests', 'scaffold_or_alignment_scores', 'opaque_lexical_or_semantic_scores', 'semantic_labels_admitted',
              'source_identities_admitted', 'independent_reviews_admitted', 'untouched_test_units_admitted', 'independent_source_groups_admitted', 'certified_false_parents', 'external_messages_sent']: assert report[k] == 0
    assert report['scientific_acceptance'] is report['semantic_evaluation_metrics'] is None
    previous = []
    for path in sorted((ROOT / 'runs').glob('000*/manifest.json')):
        if path.parent != run: check_hashes(path.parent); previous.append(path.parent.name)
    assert len(previous) == 49
    for path in (ROOT / 'reports').glob('*_deliverable_seal.json'):
        for p, h in json.loads(path.read_text()).get('deliverable_hashes', {}).items(): assert sha(p) == h
    result = {'state': 'verified', 'manifest_sha256': sha('runs/000050_publisher_intake/manifest.json'),
        'both_search_calls_and_all_returned_hit_blocks_verified': True, 'first_appearance_selection_and_all_four_slots_verified': True,
        'all_native_request_receipts_and_critical_scope_checks_verified': True, 'shared_html_parser': 'BeautifulSoup html.parser',
        'search_engine_date_filter_enforcement_observable': False, 'independent_scientific_review': False,
        'semantics_or_source_identity_validated': False, 'prior_runs_preserved': previous}
    out = ROOT / 'reports/000050_verification.json'
    if out.exists(): assert {k: v for k, v in json.loads(out.read_text()).items() if k != 'verified_at_utc'} == result
    else:
        with out.open('x') as stream: json.dump(result | {'verified_at_utc': datetime.now(timezone.utc).isoformat()}, stream, indent=2); stream.write('\n')
    print(json.dumps({'state': 'verified', 'prior_runs_preserved': len(previous), 'native_routes': occupied, 'ready_captures': ready, 'capacity_met': ready == 4}, indent=2))


if __name__ == '__main__': main()
