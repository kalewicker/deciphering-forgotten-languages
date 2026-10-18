"""Finite capture provenance and neutral review materials; no correspondence model."""
from pathlib import Path
from urllib.parse import urlparse
import json
import re
import subprocess
import unicodedata
from bs4 import BeautifulSoup
from .corpus import digest, dump_json
from .natural_v12 import utc


def resource_key(url):
    if not isinstance(url, str):
        return None
    p = urlparse(url)
    if p.scheme not in ('http', 'https') or p.username is not None or p.password is not None:
        return None
    try:
        if p.port not in (None, 80 if p.scheme == 'http' else 443):
            return None
    except ValueError:
        return None
    return (p.hostname, p.path.rstrip('/'), p.query)


def select_archive(raw, nominee):
    try:
        data = json.loads(raw)
        expected = ['timestamp', 'original', 'statuscode', 'mimetype', 'digest']
        if not isinstance(data, list) or len(data) != 2 or data[0] != expected or len(data[1]) != 5:
            return {'eligible': False, 'reason': 'absent_or_ambiguous_metadata', 'record': None, 'replay_url': None}
        record = dict(zip(expected, data[1], strict=True))
        if not all(isinstance(v, str) for v in record.values()):
            return {'eligible': False, 'reason': 'invalid_metadata_fields', 'record': None, 'replay_url': None}
        good = (bool(re.fullmatch(r'\d{14}', record['timestamp'])) and record['timestamp'] <= nominee['archive_cutoff']
                and record['statuscode'] == '200' and record['mimetype'] == 'text/html'
                and resource_key(record['original']) == resource_key(nominee['fl_url']))
        return {'eligible': good, 'reason': None if good else 'metadata_identity_or_cutoff_failure', 'record': record,
                'replay_url': 'https://web.archive.org/web/'+record['timestamp']+'id_/'+record['original'] if good else None}
    except (ValueError, TypeError, KeyError):
        return {'eligible': False, 'reason': 'invalid_metadata_json', 'record': None, 'replay_url': None}


def request(root, key, url, limits, kind):
    dest = root/key;dest.mkdir(parents=True, exist_ok=False)
    maximum = limits['pdf_max_bytes'] if kind == 'source' else limits['fl_metadata_max_bytes']
    cmd = ['curl', '--disable', '--silent', '--show-error', '--location', '--compressed', '--proto', '=https', '--proto-redir', '=https',
           '--connect-timeout', str(limits['connect_timeout_seconds']), '--max-time', str(limits['total_timeout_seconds']),
           '--max-redirs', str(limits['max_redirects']), '--max-filesize', str(maximum), '--user-agent', limits['user_agent'],
           '--output', str(dest/'body.bin'), '--dump-header', str(dest/'headers.txt'), '--write-out', '%{url_effective}\n%{http_code}', url]
    started = utc();r = subprocess.run(cmd, capture_output=True)
    parts = r.stdout.decode(errors='replace').rsplit('\n', 1)
    status = int(parts[-1]) if len(parts) == 2 and parts[-1].isdigit() else None
    artifacts = {}
    for p in [dest/'body.bin', dest/'headers.txt']:
        if p.exists():
            artifacts[p.name] = {'path': str(p.resolve()), 'sha256': digest(p.read_bytes()), 'bytes': p.stat().st_size}
    receipt = {'route_id': key, 'attempted': True, 'requested_url': url, 'kind': kind,
               'started_at_utc': started, 'finished_at_utc': utc(), 'http_status': status, 'curl_returncode': r.returncode,
               'final_url': parts[0] if len(parts) == 2 else None, 'stderr': r.stderr.decode(errors='replace'),
               'command': cmd, 'max_body_bytes': maximum, 'artifacts': artifacts,
               'body_representation': 'curl transfer/content-decoded response body (--compressed)',
               'transport_complete': r.returncode == 0 and status == 200 and 'body.bin' in artifacts and artifacts['body.bin']['bytes'] <= maximum}
    dump_json(dest/'receipt.json', receipt)
    return receipt


def skipped(root, key, kind, reason):
    dest = root/key;dest.mkdir(parents=True, exist_ok=False)
    receipt = {'route_id': key, 'attempted': False, 'kind': kind, 'reason': reason, 'requested_url': None,
               'recorded_at_utc': utc(), 'transport_complete': False, 'artifacts': {}}
    dump_json(dest/'receipt.json', receipt)
    return receipt


def normalize_title(value):
    return ' '.join(unicodedata.normalize('NFC', value).casefold().split())


def extract_post(raw, receipt, nominee, selection=None):
    if not receipt['transport_complete']:
        return {'eligible': False, 'unmet': ['transport_complete'], 'text': None, 'current_raw_fl': False, 'archival_raw_fl': False}
    soup = BeautifulSoup(raw, 'html.parser')
    html_title = soup.title.get_text(' ', strip=True) if soup.title else ''
    headings = [x.get_text(' ', strip=True) for x in soup.select('.post-title')]
    body = soup.select('div.post-body')
    identity_urls = [receipt.get('final_url') or '']
    identity_urls += [x.get('href', '') for x in soup.select('link[rel="canonical"]')]
    identity_urls += [x.get('content', '') for x in soup.select('meta[property="og:url"]')]
    archived = selection is not None
    final_archive = urlparse(receipt.get('final_url') or '')
    marker = '/web/'+selection['record']['timestamp']+'id_/' if archived and selection['eligible'] else None
    replay_original = final_archive.path[len(marker):] if marker and final_archive.path.startswith(marker) else None
    if replay_original:
        identity_urls.append(replay_original)
    archive_bound = not archived or (selection['eligible'] and final_archive.hostname == 'web.archive.org'
                                      and replay_original is not None
                                      and resource_key(replay_original) == resource_key(nominee['fl_url'])
                                      and resource_key(selection['record']['original']) == resource_key(nominee['fl_url']))
    req = {'single_post_body': len(body) == 1,
           'page_title_matches': any(normalize_title(nominee['fl_title']) in normalize_title(t) for t in [html_title, *headings]),
           'native_permalink_bound': any(resource_key(u) == resource_key(nominee['fl_url']) for u in identity_urls),
           'archive_timestamp_original_bound': bool(archive_bound),
           'no_challenge_signatures': not any(x in raw.decode(errors='replace').lower() for x in ['cf-chl-', 'verify you are human', 'checking your browser', 'enable javascript and cookies to continue'])}
    text = None
    if len(body) == 1:
        for node in body[0].select('script,style,noscript'):
            node.decompose()
        text = body[0].get_text(' ', strip=True)
    req['body_prose_nonempty'] = bool(text)
    eligible = all(req.values())
    return {'eligible': eligible, 'requirements': req, 'unmet': [k for k, v in req.items() if not v],
            'html_title': html_title, 'post_titles': headings, 'identity_urls': identity_urls,
            'text': text if eligible else None, 'text_sha256': digest(text.encode()) if eligible else None,
            'current_raw_fl': eligible and not archived, 'archival_raw_fl': eligible and archived,
            'capture_timestamp': selection['record']['timestamp'] if archived and selection['eligible'] else None,
            'transformations': ['Exactly one div.post-body', 'Remove script/style/noscript only; headings and superscripts retained',
                                'BeautifulSoup visible prose joined with spaces; no language, word, alias or alignment labels']}


def review_form(nominee):
    return {'nominee_id': nominee['id'], 'reviewer_name': None, 'independent_of_prior_predictions': None,
            'source_identity_checked': None, 'language_scope_checked': None, 'statement_boundaries_checked': None,
            'full_post_source_coverage': None, 'span_correspondences': [], 'word_correspondences': [],
            'counterexamples': [], 'uncertainty_notes': [], 'review_completed': False,
            'semantic_training_eligible': False, 'untouched_test_eligible': False}
