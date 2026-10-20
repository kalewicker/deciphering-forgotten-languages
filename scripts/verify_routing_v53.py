"""Check saved route evidence without requests or the production assessor."""
from datetime import datetime, timezone
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


def key(value):
    try:
        u = urlparse(value)
        assert u.scheme == 'https' and u.hostname == 'physicsworld.com'
        assert u.port in (None, 443) and u.username is u.password is None
        assert not any([u.params, u.query, u.fragment])
        parts = u.path.strip('/').split('/')
        assert len(parts) in (1, 2) and (len(parts) == 1 or parts[0] == 'a')
        assert re.fullmatch('[a-z0-9]+(-[a-z0-9]+)*', parts[-1])
        assert u.path == '/' + '/'.join(parts) + ('/' if u.path.endswith('/') else '')
        return u.path.rstrip('/')
    except (AssertionError, ValueError, TypeError, AttributeError): return None


def title(value):
    pieces = re.split(r'\s+[–—|\-]\s+', value)
    if len(pieces) > 1 and pieces[-1].strip() == 'Physics World': value = re.sub(r'\s+[–—|\-]\s+Physics World\s*$', '', value)
    return ' '.join(unicodedata.normalize('NFC', value).casefold().split())


def reconstruct(raw, headers, receipt, spec):
    blocks = {'responses': [], 'ignored_transport_or_informational': []}
    for section in re.split(r'\r?\n\r?\n', headers.decode('iso-8859-1')):
        lines = section.splitlines()
        if not lines or not lines[0].startswith('HTTP/'): continue
        head = lines[0].split(maxsplit=2)
        status = int(head[1]); reason = head[2] if len(head) == 3 else ''
        fields = [line.split(':', 1) for line in lines[1:] if ':' in line]
        block = {'status': status, 'reason': reason,
                 'locations': [v.strip() for n, v in fields if n.casefold() == 'location'],
                 'content_types': [v.strip() for n, v in fields if n.casefold() == 'content-type']}
        ignored = status < 200 or reason.strip().casefold() == 'connection established'
        blocks['ignored_transport_or_informational' if ignored else 'responses'].append(block)
    chain = []; next_url = spec['og_url']; responses = blocks['responses']; valid = len(responses) > 0
    for i, block in enumerate(responses):
        location = None
        if i + 1 < len(responses):
            if block['status'] in [301, 302, 303, 307, 308] and len(block['locations']) == 1:
                location = urljoin(next_url, block['locations'][0])
            else: valid = False
        chain.append(dict(url=next_url, **block, resolved_location=location))
        if location is not None: next_url = location
    consistent = bool(valid and isinstance(receipt['num_redirects'], int) and len(responses) == receipt['num_redirects'] + 1
        and responses[-1]['status'] == receipt['http_status'] == 200 and not responses[-1]['locations']
        and key(next_url) is not None and key(next_url) == key(receipt['final_url'])
        and all(key(r['url']) is not None for r in chain))
    soup = BeautifulSoup(raw, 'html.parser'); urls = []; titles = []
    for node in soup.find_all('link'):
        if 'canonical' in node.get('rel', []): urls.append({'channel': 'canonical', 'value': node.get('href', '')})
    for node in soup.find_all('meta', attrs={'property': 'og:url'}): urls.append({'channel': 'og_url', 'value': node.get('content', '')})
    for node in soup.find_all('title'): titles.append({'channel': 'html_title', 'value': node.get_text(' ', strip=True)})
    for node in soup.find_all('meta', attrs={'property': 'og:title'}): titles.append({'channel': 'og_title', 'value': node.get('content', '')})
    errors = []
    for i, node in enumerate(soup.find_all('script', attrs={'type': 'application/ld+json'})):
        try: document = json.loads(node.string or node.get_text())
        except (ValueError, TypeError): errors.append(i); continue
        stack = [document]
        while stack:
            item = stack.pop()
            if isinstance(item, list): stack.extend(reversed(item))
            if not isinstance(item, dict): continue
            kind = item.get('@type', [])
            kinds = [kind] if isinstance(kind, str) else kind
            if isinstance(kinds, list) and set(t for t in kinds if isinstance(t, str)) & {'Article', 'NewsArticle'}:
                value = item.get('headline')
                titles.append({'channel': 'article_headline', 'value': value if isinstance(value, str) else ''})
            stack.extend(reversed(list(item.values())))
    metadata = {'urls': urls, 'titles': titles, 'json_ld_parse_errors': errors,
                'h1_inventory': [t.get_text(' ', strip=True) for t in soup.find_all('h1')],
                'publication_values': [t.get('content', '') for t in soup.find_all('meta', attrs={'property': 'article:published_time'})]}
    canon = [u['value'] for u in urls if u['channel'] == 'canonical']; expected = key(spec['canonical_url'])
    checks = {'complete_200': receipt['transport_complete'],
        'html_content_type': 'text/html' in (receipt['content_type'] or '').lower(),
        'consistent_publisher_chain': consistent,
        'canonical_matches_frozen': bool(expected and canon and all(key(u) == expected for u in canon)),
        'three_title_channels_match_frozen': {'html_title', 'og_title', 'article_headline'} <= {t['channel'] for t in titles}
            and not errors and all(title(t['value']) == title(spec['expected_title']) for t in titles)}
    category = 'unresolved'
    if all(checks.values()):
        if receipt['num_redirects'] > 0 and key(receipt['final_url']) == expected: category = 'observed_redirect_to_canonical'
        elif receipt['num_redirects'] == 0 and key(receipt['final_url']) == key(spec['og_url']): category = 'observed_served_alias'
    return {'id': spec['id'], 'requested_url': spec['og_url'], 'expected_canonical_url': spec['canonical_url'],
        'final_url': receipt['final_url'], 'http_status': receipt['http_status'], 'curl_returncode': receipt['curl_returncode'],
        'num_redirects': receipt['num_redirects'], 'header_inventory': blocks, 'chain': chain, 'metadata': metadata,
        'checks': checks, 'category': category, 'current_alias_supported': category != 'unresolved',
        'body_bytes_equal_old_capture': hashlib.sha256(raw).hexdigest() == spec['old_body_sha256'],
        'v50_ready_unchanged': spec['v50_ready_unchanged']}


def main():
    run = ROOT / 'runs/000053_routing'; check_hashes(run)
    cfg = read('experiments/routing_v53.json'); pre = read('data/v53/preflight.json')
    manifest = read('runs/000053_routing/manifest.json'); report = read('runs/000053_routing/report.json')
    assert cfg['route_budget'] == len(cfg['routes']) == report['route_denominator'] == report['routes_attempted'] == 4
    assert cfg['maximum_application_requests_including_redirects'] == 16
    assert cfg['limits'] == {'connect_timeout_seconds': 8, 'total_timeout_seconds': 20, 'max_redirects': 3,
                            'max_body_bytes': 4194304, 'user_agent': 'FL-Decipher registered routing audit v53'}
    assert [r['id'] for r in cfg['routes']] == ['q00s00', 'q00s01', 'q01s00', 'q01s01']
    for p, h in pre['hashes'].items(): assert sha(p) == h, p
    for p, h in cfg['input_hashes'].items(): assert pre['hashes'][p] == h
    assert pre['hashes']['experiments/routing_v53.json'] == sha('experiments/routing_v53.json')
    assert cfg['registered_at_utc'] < pre['sealed_at_utc'] < manifest['finished_at_utc']
    assert sorted(p.name for p in (ROOT / 'data/v53/acquisition').iterdir()) == sorted(r['id'] for r in cfg['routes'])
    rows = []; receipts = []; previous_time = pre['sealed_at_utc']
    intake = read('runs/000050_publisher_intake/report.json')
    assert intake['ready_captures'] == 1 and intake['intake_capacity_met'] is False
    for spec in cfg['routes']:
        base = f"data/v53/acquisition/{spec['id']}"; dest = ROOT / base; receipt = read(base + '/receipt.json')
        assert previous_time <= receipt['started_at_utc'] <= receipt['finished_at_utc'] <= manifest['finished_at_utc']
        previous_time = receipt['finished_at_utc']; receipts.append(receipt)
        assert receipt['id'] == spec['id'] and receipt['requested_url'] == spec['og_url']
        expected_cmd = ['curl', '--disable', '--silent', '--show-error', '--location', '--compressed',
                       '--proto', '=https', '--proto-redir', '=https', '--retry', '0', '--connect-timeout', '8',
                       '--max-time', '20', '--max-redirs', '3', '--max-filesize', '4194304', '--user-agent', cfg['limits']['user_agent'],
                       '--output', str(dest / 'body.bin'), '--dump-header', str(dest / 'headers.txt'),
                       '--write-out', '%{json}', spec['og_url']]
        assert receipt['command'] == expected_cmd
        try: telemetry = read(base + '/curl_stdout.bin')
        except (ValueError, TypeError): telemetry = {}
        assert (receipt['final_url'], receipt['http_status'], receipt['num_redirects'], receipt['content_type']) == (
            telemetry.get('url_effective'), telemetry.get('http_code'), telemetry.get('num_redirects'), telemetry.get('content_type'))
        files = {p.name for p in dest.iterdir() if p.name != 'receipt.json'}
        assert files == set(receipt['artifacts'])
        for name, info in receipt['artifacts'].items():
            assert info == {'sha256': sha(base + '/' + name), 'bytes': (dest / name).stat().st_size}
        complete = receipt['curl_returncode'] == 0 and receipt['http_status'] == 200 and 'body.bin' in files and (dest / 'body.bin').stat().st_size <= 4194304
        assert receipt['transport_complete'] == complete
        body = (dest / 'body.bin').read_bytes() if 'body.bin' in files else b''
        headers = (dest / 'headers.txt').read_bytes() if 'headers.txt' in files else b''
        row = reconstruct(body, headers, receipt, spec)
        assert read(f"data/v53/{spec['id']}_route.json") == row; rows.append(row)
        old = read(spec['old_identity'])
        assert [u['value'] for u in old['identity_inventory'] if u['channel'] == 'og_url'] == [spec['og_url']]
        assert [u['value'] for u in old['identity_inventory'] if u['channel'] == 'canonical'] == [spec['canonical_url']]
        assert old['identity_urls_agree'] is False and sha(spec['old_raw']) == spec['old_body_sha256']
        assert spec['v50_ready_unchanged'] == next(r['ready_for_future_registration'] for r in intake['slot_results'] if r['slot_id'] == spec['id'])
    assert report['routes'] == rows
    supported = sum(r['current_alias_supported'] for r in rows)
    assert report['current_alias_supported'] == supported and report['unresolved_routes'] == 4 - supported
    assert report['all_four_current_alias_gate'] == (supported == 4)
    assert report['redirect_routes'] == sum(r['category'] == 'observed_redirect_to_canonical' for r in rows)
    assert report['served_alias_routes'] == sum(r['category'] == 'observed_served_alias' for r in rows)
    assert report['v50_ready_captures_unchanged'] == 1 and report['v50_intake_capacity_met_unchanged'] is False
    for name in ['historical_routing_authenticated', 'prior_strict_url_diagnostics_rewritten']: assert report[name] is False
    for name in ['new_candidate_readiness_admissions', 'new_structural_scores', 'new_semantic_scores', 'source_identities_admitted',
                 'independent_reviews_admitted', 'untouched_test_units_admitted']: assert report[name] == 0
    assert report['scientific_acceptance'] is report['semantic_evaluation_metrics'] is None
    prior = []
    for path in sorted((ROOT / 'runs').glob('000*/manifest.json')):
        if path.parent != run: check_hashes(path.parent); prior.append(path.parent.name)
    assert len(prior) == 52
    for seal in (ROOT / 'reports').glob('*_deliverable_seal.json'):
        for p, h in json.loads(seal.read_text()).get('deliverable_hashes', {}).items(): assert sha(p) == h, p
    result = {'state': 'verified', 'manifest_sha256': sha('runs/000053_routing/manifest.json'),
        'routes_verified': len(rows), 'current_alias_supported': supported,
        'recorded_redirects': sum(r['num_redirects'] or 0 for r in receipts),
        'recorded_application_responses': sum(len(r['chain']) for r in rows),
        'route_evidence_reconstructed_without_production_assessor': True,
        'commands_limits_timing_artifacts_and_telemetry_checked': True,
        'prior_diagnostics_and_readiness_preserved': True, 'prior_runs_preserved': prior,
        'shared_html_parser': 'BeautifulSoup html.parser', 'verification_network_requests': 0,
        'historical_routing_authenticated': False, 'independent_scientific_review': False,
        'semantics_or_source_identity_validated': False}
    out = ROOT / 'reports/000053_verification.json'
    if out.exists(): assert {k: v for k, v in json.loads(out.read_text()).items() if k != 'verified_at_utc'} == result
    else:
        with out.open('x') as stream: json.dump(result | {'verified_at_utc': datetime.now(timezone.utc).isoformat()}, stream, indent=2); stream.write('\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'prior_runs_preserved'} | {'prior_runs_preserved': len(prior)}, indent=2))


if __name__ == '__main__': main()
