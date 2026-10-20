"""Bounded current-route capture and metadata comparison; no readiness changes."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import unicodedata
from urllib.parse import urljoin, urlsplit

from bs4 import BeautifulSoup

REDIRECTS = {301, 302, 303, 307, 308}


def utc(): return datetime.now(timezone.utc).isoformat()


def publisher_key(url):
    try:
        p = urlsplit(url)
        if (p.scheme != 'https' or p.hostname != 'physicsworld.com' or p.port not in (None, 443)
                or p.username is not None or p.password is not None or p.query or p.fragment): return None
        if not re.fullmatch(r'/(?:a/)?[a-z0-9]+(?:-[a-z0-9]+)*/?', p.path): return None
        return p.path.rstrip('/')
    except (ValueError, TypeError): return None


def title_key(value):
    value = re.sub(r'\s+[–—|\-]\s+Physics World\s*$', '', value)
    return ' '.join(unicodedata.normalize('NFC', value).casefold().split())


def header_blocks(raw):
    """Keep only routing fields. Proxy CONNECT and informational blocks are separate."""
    responses = []; ignored = []; current = None
    for line in raw.decode('iso-8859-1').splitlines():
        match = re.match(r'^HTTP/\S+\s+(\d{3})(?:\s+(.*))?$', line)
        if match:
            current = {'status': int(match[1]), 'reason': match[2] or '', 'locations': [], 'content_types': []}
            if current['reason'].strip().casefold() == 'connection established' or current['status'] < 200:
                ignored.append(current)
            else: responses.append(current)
        elif current and ':' in line:
            name, value = line.split(':', 1)
            if name.casefold() == 'location': current['locations'].append(value.strip())
            if name.casefold() == 'content-type': current['content_types'].append(value.strip())
        elif not line: current = None
    return {'responses': responses, 'ignored_transport_or_informational': ignored}


def metadata(raw):
    soup = BeautifulSoup(raw, 'html.parser')
    urls = [{'channel': 'canonical', 'value': t.get('href', '')} for t in soup.select('link[rel~=canonical]')]
    urls += [{'channel': 'og_url', 'value': t.get('content', '')} for t in soup.select('meta[property="og:url"]')]
    titles = [{'channel': 'html_title', 'value': t.get_text(' ', strip=True)} for t in soup.select('title')]
    titles += [{'channel': 'og_title', 'value': t.get('content', '')} for t in soup.select('meta[property="og:title"]')]
    errors = []

    def walk(value):
        if isinstance(value, list):
            for item in value: walk(item)
        elif isinstance(value, dict):
            types = value.get('@type', []); types = [types] if isinstance(types, str) else types
            if isinstance(types, list) and any(t in ('Article', 'NewsArticle') for t in types):
                headline = value.get('headline')
                titles.append({'channel': 'article_headline', 'value': headline if isinstance(headline, str) else ''})
            for item in value.values(): walk(item)
    for index, tag in enumerate(soup.select('script[type="application/ld+json"]')):
        try: walk(json.loads(tag.string or tag.get_text()))
        except (ValueError, TypeError): errors.append(index)
    return {'urls': urls, 'titles': titles, 'json_ld_parse_errors': errors,
            'h1_inventory': [t.get_text(' ', strip=True) for t in soup.select('h1')],
            'publication_values': [t.get('content', '') for t in soup.select('meta[property="article:published_time"]')]}


def command(dest, url, limits):
    return ['curl', '--disable', '--silent', '--show-error', '--location', '--compressed',
            '--proto', '=https', '--proto-redir', '=https', '--retry', '0',
            '--connect-timeout', str(limits['connect_timeout_seconds']),
            '--max-time', str(limits['total_timeout_seconds']), '--max-redirs', str(limits['max_redirects']),
            '--max-filesize', str(limits['max_body_bytes']), '--user-agent', limits['user_agent'],
            '--output', str(dest / 'body.bin'), '--dump-header', str(dest / 'headers.txt'),
            '--write-out', '%{json}', url]


def capture(root, spec, limits):
    dest = Path(root) / spec['id']; dest.mkdir(parents=True, exist_ok=False)
    cmd = command(dest, spec['og_url'], limits); started = utc()
    result = subprocess.run(cmd, capture_output=True)
    # Preserve curl's complete telemetry privately; a failed write-out stays a failed observation.
    (dest / 'curl_stdout.bin').write_bytes(result.stdout)
    try: telemetry = json.loads(result.stdout)
    except (ValueError, TypeError): telemetry = {}
    artifacts = {p.name: {'sha256': hashlib.sha256(p.read_bytes()).hexdigest(), 'bytes': p.stat().st_size}
                 for p in dest.iterdir() if p.is_file()}
    complete = (result.returncode == 0 and telemetry.get('http_code') == 200 and 'body.bin' in artifacts
                and artifacts['body.bin']['bytes'] <= limits['max_body_bytes'])
    receipt = {'id': spec['id'], 'requested_url': spec['og_url'], 'started_at_utc': started,
               'finished_at_utc': utc(), 'command': cmd, 'curl_returncode': result.returncode,
               'stderr': result.stderr.decode(errors='replace'), 'final_url': telemetry.get('url_effective'),
               'http_status': telemetry.get('http_code'), 'num_redirects': telemetry.get('num_redirects'),
               'content_type': telemetry.get('content_type'), 'transport_complete': complete,
               'body_representation': 'curl transfer/content-decoded response body (--compressed)', 'artifacts': artifacts}
    with (dest / 'receipt.json').open('x') as stream: json.dump(receipt, stream, indent=2); stream.write('\n')
    return receipt


def assess(raw, headers, receipt, spec):
    blocks = header_blocks(headers); responses = blocks['responses']; current = spec['og_url']; chain = []
    valid = bool(responses)
    for index, block in enumerate(responses):
        target = None
        if index < len(responses) - 1:
            if block['status'] not in REDIRECTS or len(block['locations']) != 1: valid = False
            else: target = urljoin(current, block['locations'][0])
        chain.append({'url': current, **block, 'resolved_location': target})
        if target is not None: current = target
    valid = bool(valid and receipt['num_redirects'] == len(responses) - 1
                 and responses[-1]['status'] == receipt['http_status'] == 200
                 and not responses[-1]['locations']
                 and publisher_key(current) is not None and publisher_key(current) == publisher_key(receipt['final_url'])
                 and all(publisher_key(r['url']) is not None for r in chain))
    meta = metadata(raw)
    canonical = [r['value'] for r in meta['urls'] if r['channel'] == 'canonical']
    expected = publisher_key(spec['canonical_url'])
    canonical_match = bool(expected and canonical and all(publisher_key(u) == expected for u in canonical))
    required = {'html_title', 'og_title', 'article_headline'}
    title_match = (required <= {r['channel'] for r in meta['titles']} and not meta['json_ld_parse_errors']
                   and all(title_key(r['value']) == title_key(spec['expected_title']) for r in meta['titles']))
    checks = {'complete_200': receipt['transport_complete'], 'html_content_type':
              'text/html' in (receipt['content_type'] or '').lower(), 'consistent_publisher_chain': valid,
              'canonical_matches_frozen': canonical_match, 'three_title_channels_match_frozen': title_match}
    category = 'unresolved'
    if all(checks.values()):
        if receipt['num_redirects'] > 0 and publisher_key(receipt['final_url']) == expected:
            category = 'observed_redirect_to_canonical'
        elif receipt['num_redirects'] == 0 and publisher_key(receipt['final_url']) == publisher_key(spec['og_url']):
            category = 'observed_served_alias'
    return {'id': spec['id'], 'requested_url': spec['og_url'], 'expected_canonical_url': spec['canonical_url'],
            'final_url': receipt['final_url'], 'http_status': receipt['http_status'], 'curl_returncode': receipt['curl_returncode'],
            'num_redirects': receipt['num_redirects'], 'header_inventory': blocks, 'chain': chain, 'metadata': meta,
            'checks': checks, 'category': category, 'current_alias_supported': category != 'unresolved',
            'body_bytes_equal_old_capture': hashlib.sha256(raw).hexdigest() == spec['old_body_sha256'],
            'v50_ready_unchanged': spec['v50_ready_unchanged']}
