"""Replay E60 bytes and accounting without importing its production functions."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from fl_decipher.additional_intake_v55 import article_key
from fl_decipher.native_discovery_v59 import audit as declaration_audit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from verify_correspondence_v6 import check_hashes


def read(p): return json.loads((ROOT / p).read_text())
def sha(p): return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()


def replay_layout(raw, url, query):
    soup = BeautifulSoup(raw, 'html.parser'); tags = soup.select('*'); positions = {id(t): i for i, t in enumerate(tags)}
    def item(t):
        parents = []; parent = t.parent
        while parent is not None:
            if parent.name != '[document]': parents.insert(0, {'tag': parent.name, 'id': parent.get('id'), 'classes': parent.get('class', [])})
            parent = parent.parent
        return {'dom_tag_index': positions[id(t)], 'tag': t.name, 'text': t.get_text(' ', strip=True), 'ancestors': parents}
    bases = [{'dom_tag_index': positions[id(t)], 'href': t['href']} for t in soup.select('base[href]')]
    anchors = []
    for t in soup.select('a[href]'):
        resolved = key = None
        if bases: reason = 'base_href_present'
        else:
            try:
                resolved = urljoin(url, t['href']); key = article_key(resolved)
                reason = 'strict_article_url_only_not_search_hit' if key else 'not_strict_article_url'
            except (ValueError, TypeError): reason = 'malformed_href'
        anchors.append({'anchor_index': len(anchors), **item(t), 'href': t['href'], 'resolved_url': resolved,
            'article_key_diagnostic': key, 'diagnostic_reason': reason, 'search_hit_attributed': False})
    values = []
    for fi, f in enumerate(soup.select('form')):
        for ci, c in enumerate(f.select('input,button,select,textarea')):
            if c.name == 'input' and c.get('name') == 's' and c.get('type', 'text').lower() in ['text', 'search']:
                values.append({'form_index': fi, 'control_index': ci, 'value': c.get('value', '')})
    declarations = declaration_audit(raw, url, query)
    return {'html_titles': [item(t) for t in soup.select('title')], 'headings_h1_h2': [item(t) for t in soup.select('h1,h2')],
        'base_hrefs': bases, 'search_forms': declarations['search_forms'], 'search_actions': declarations['search_actions'],
        'json_ld_errors': declarations['json_ld_errors'], 'search_input_values': values, 'anchors': anchors,
        'all_anchor_occurrences_retained': True, 'link_resolution_supported': len(bases) == 0,
        'search_result_container_selector': None, 'search_result_attribution_validated': False}


def replay_headers(raw):
    responses = []; ignored = []
    for block in re.split(r'\r?\n\r?\n', raw.decode('iso-8859-1')):
        lines = block.splitlines()
        if not lines: continue
        match = re.fullmatch(r'HTTP/\S+\s+(\d{3})(?:\s+(.*))?', lines[0])
        if not match: continue
        status = int(match[1]); reason = match[2] or ''
        row = {'status': status, 'reason': reason, 'locations': [], 'content_types': []}
        for line in lines[1:]:
            if ':' not in line: continue
            name, value = line.split(':', 1)
            if name.lower() == 'location': row['locations'].append(value.strip())
            if name.lower() == 'content-type': row['content_types'].append(value.strip())
        (ignored if status < 200 or reason.strip().lower() == 'connection established' else responses).append(row)
    return {'responses': responses, 'ignored_transport_or_informational': ignored}


def main():
    cfg = read('experiments/native_probe_v60.json'); pre = read('data/v60/preflight.json'); intent = read('data/v60/intent.json')
    receipt = read('data/v60/acquisition/search/receipt.json'); report = read('runs/000060_native_probe/report.json')
    manifest = read('runs/000060_native_probe/manifest.json'); contract = cfg['probe_contract']; url = contract['url']
    check_hashes(ROOT / 'runs/000060_native_probe')
    assert cfg['network_attempt_budget'] == pre['research_attempt_budget'] == intent['attempt_budget'] == 1
    assert cfg['probe_contract'] == read('experiments/native_discovery_v59a.json')['future_probe_contract']
    assert url == 'https://physicsworld.com/?s=ANITA' and cfg['query'] == 'ANITA'
    for p, h in pre['hashes'].items(): assert sha(p) == h, p
    for p, h in cfg['input_hashes'].items(): assert pre['hashes'][p] == h
    assert pre['hashes']['experiments/native_probe_v60.json'] == sha('experiments/native_probe_v60.json')
    assert cfg['registered_at_utc'] < pre['sealed_at_utc'] < intent['started_at_utc'] == receipt['started_at_utc'] < receipt['finished_at_utc'] < manifest['finished_at_utc']
    assert intent['preflight_sha256'] == sha('data/v60/preflight.json')
    assert intent['request_method'] == receipt['request_method'] == 'GET'
    assert intent['request_url'] == receipt['requested_url'] == url
    assert intent['attempt_index'] == receipt['attempt_index'] == intent['redirect_budget'] == intent['retry_budget'] == 0
    dest = ROOT / 'data/v60/acquisition/search'
    expected_command = ['curl', '--disable', '--silent', '--show-error', '--compressed', '--request', 'GET', '--proto', '=https',
        '--retry', '0', '--max-redirs', '0', '--connect-timeout', '8', '--max-time', '20', '--max-filesize', '4194304',
        '--user-agent', 'FL-Decipher registered native-search layout probe v60', '--output', str(dest / 'body.bin'),
        '--dump-header', str(dest / 'headers.txt'), '--write-out', '%{json}', url]
    assert pre['registered_command'] == intent['command'] == receipt['command'] == expected_command
    artifacts = {p.name: {'sha256': hashlib.sha256(p.read_bytes()).hexdigest(), 'bytes': p.stat().st_size}
                 for p in dest.iterdir() if p.is_file() and p.name != 'receipt.json'}
    assert receipt['artifacts'] == artifacts
    assert sorted(p.name for p in (ROOT / 'data/v60').iterdir()) == ['acquisition', 'intent.json', 'layout.json', 'observation.json', 'preflight.json']
    assert sorted(p.name for p in dest.parent.iterdir()) == ['search']
    raw = (dest / 'body.bin').read_bytes() if (dest / 'body.bin').exists() else b''
    headers = (dest / 'headers.txt').read_bytes() if (dest / 'headers.txt').exists() else b''
    try: telemetry = json.loads((dest / 'curl_stdout.bin').read_bytes())
    except (ValueError, TypeError): telemetry = {}
    if not isinstance(telemetry, dict): telemetry = {}
    for k, t in [('http_status', 'http_code'), ('final_url', 'url_effective'), ('num_redirects', 'num_redirects'), ('content_type', 'content_type')]:
        assert receipt[k] == telemetry.get(t), k
    if 'method' in telemetry: assert telemetry['method'] == 'GET'
    if 'exitcode' in telemetry: assert receipt['curl_returncode'] == telemetry['exitcode']
    complete = (receipt['curl_returncode'] == 0 and isinstance(telemetry.get('http_code'), int) and 100 <= telemetry['http_code'] <= 599
                and 'body.bin' in artifacts and len(raw) <= contract['max_body_bytes'])
    assert receipt['transport_complete'] == complete
    layout = replay_layout(raw, url, cfg['query']); assert layout == read('data/v60/layout.json')
    header_inventory = replay_headers(headers); responses = header_inventory['responses']
    media = lambda v: (v or '').split(';')[0].strip().lower()
    text = BeautifulSoup(raw, 'html.parser').get_text(' ', strip=True).casefold(); challenges = [s for s in cfg['challenge_signatures'] if s in text]
    checks = {'transport_complete': complete, 'http_200': receipt['http_status'] == 200,
        'exact_request_url_retained': receipt['final_url'] == url, 'no_redirects': receipt['num_redirects'] == 0,
        'one_consistent_application_response': len(responses) == 1 and responses[0]['status'] == receipt['http_status'] and not responses[0]['locations'],
        'html_content_type': media(receipt['content_type']) == 'text/html' and bool(responses) and bool(responses[-1]['content_types']) and all(media(v) == 'text/html' for v in responses[-1]['content_types']),
        'body_within_limit': 0 < len(raw) <= contract['max_body_bytes'], 'no_registered_challenge_text': not challenges}
    obs = {'header_inventory': header_inventory, 'checks': checks, 'challenge_signatures_found': challenges,
           'complete_direct_html_observation': all(checks.values()), 'native_search_function_validated': False}
    assert obs == read('data/v60/observation.json')
    keys = [a['article_key_diagnostic'] for a in layout['anchors'] if a['article_key_diagnostic']]
    expected = {'experiment_id': 'native_probe_v60', 'probe_slot_denominator': 1, 'probe_attempts': 1,
        'recorded_application_responses': len(responses), 'http_status': receipt['http_status'], 'curl_returncode': receipt['curl_returncode'],
        'complete_direct_html_observation': all(checks.values()), 'failed_checks': [k for k,v in checks.items() if not v],
        'html_title_count': len(layout['html_titles']), 'h1_h2_count': len(layout['headings_h1_h2']), 'search_form_count': len(layout['search_forms']),
        'search_action_count': len(layout['search_actions']), 'base_href_count': len(layout['base_hrefs']), 'anchor_occurrences': len(layout['anchors']),
        'strict_article_url_occurrences_diagnostic_only': len(keys), 'unique_strict_article_urls_diagnostic_only': len(set(keys)),
        'duplicate_strict_article_url_occurrences': len(keys)-len(set(keys)), 'query_echo_in_search_input': any(r['value']=='ANITA' for r in layout['search_input_values']),
        'search_result_container_selector': None, 'search_hits_attributed': 0, 'native_search_function_validated': False,
        'candidate_nominations': 0, 'article_captures': 0, 'pagination_requests': 0, 'query_replacements': 0,
        'alignment_or_semantic_scores': 0, 'opaque_meanings_or_source_identities_admitted': 0, 'independent_reviews_admitted': 0,
        'untouched_test_units_admitted': 0, 'natural_benchmark_qualifying_works': 0, 'previous_results_preserved': True}
    assert report == expected
    assert len(responses) <= contract['maximum_application_responses'] == 1
    prior = []
    for path in sorted((ROOT / 'runs').glob('0000*/manifest.json')):
        if path.parent.name == '000060_native_probe': continue
        assert int(path.parent.name.split('_')[0]) <= 59
        check_hashes(path.parent); prior.append(path.parent.name)
    assert len(prior) == 59
    for path in (ROOT / 'reports').glob('*_deliverable_seal.json'):
        for p,h in json.loads(path.read_text()).get('deliverable_hashes', {}).items(): assert sha(p) == h, p
    result = {'state': 'verified', 'manifest_sha256': sha('runs/000060_native_probe/manifest.json'),
        'request_intent_receipt_telemetry_and_budget_verified': True, 'attempts': 1, 'recorded_application_responses': len(responses),
        'body_sha256': hashlib.sha256(raw).hexdigest(), 'body_bytes': len(raw), 'all_static_anchor_occurrences_replayed': len(layout['anchors']),
        'direct_html_observation_gate': all(checks.values()), 'production_v60_functions_not_imported': True,
        'shared_html_parser': 'BeautifulSoup html.parser', 'shared_sealed_helpers': ['E55 article_key', 'E59 declaration audit'],
        'native_search_function_validated': False, 'search_result_attribution_validated': False, 'verification_network_requests': 0,
        'independent_scientific_review': False, 'semantics_or_source_identity_validated': False, 'prior_runs_preserved': prior}
    out = ROOT / 'reports/000060_verification.json'
    if out.exists(): assert {k:v for k,v in json.loads(out.read_text()).items() if k != 'verified_at_utc'} == result
    else:
        with out.open('x') as f: json.dump(result | {'verified_at_utc': datetime.now(timezone.utc).isoformat()}, f, indent=2); f.write('\n')
    print(json.dumps({k:v for k,v in result.items() if k != 'prior_runs_preserved'} | {'prior_runs_preserved':len(prior)},indent=2))


if __name__ == '__main__': main()
