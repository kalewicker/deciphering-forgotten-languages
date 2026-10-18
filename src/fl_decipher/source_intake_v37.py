"""Metadata-only bounded intake helpers. No lexical or correspondence scoring."""
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode
from pathlib import Path
from bs4 import BeautifulSoup, NavigableString
import hashlib
import json
import re

HOST = 'forgottenlanguages-full.forgottenlanguages.org'


def identity(url):
    try:
        p = urlparse(url)
        if p.scheme not in ('http', 'https') or p.username or p.password or not p.hostname:
            return None
        if p.port not in (None, 80, 443):
            return None
        query = urlencode([(k, v) for k, v in parse_qsl(p.query) if k != 'm' and not k.startswith('utm_')])
        return p.hostname.lower(), p.path.rstrip('/'), query
    except ValueError:
        return None


def search_hits(response):
    pattern = r'^([^\n]+) \((https?://[^\s)]+)\)\n[^\n]*\[wordlim: \d+\]'
    return [{'rank': i, 'title': m.group(1).strip(), 'url': m.group(2)}
            for i, m in enumerate(re.finditer(pattern, response, re.MULTILINE))]


def nominate(discoveries, exposed_urls):
    seen = {identity(u) for u in exposed_urls if identity(u)}
    ledger, nominees, slots = [], [], []
    for discovery in discoveries:
        hits = search_hits(discovery['response'])
        selected = []
        for hit in hits:
            p = urlparse(hit['url'])
            is_post = p.hostname == HOST and re.fullmatch(r'/\d{4}/\d{2}/[^/]+\.html', p.path) is not None
            reason = 'not_dated_post_permalink' if not is_post else 'already_exposed_or_duplicate' if identity(hit['url']) in seen else None
            if reason is None and len(selected) >= 2:
                reason = 'outside_two_post_slots'
            row = {'query_index': discovery['query_index'], **hit, 'selected': reason is None, 'exclusion_reason': reason}
            ledger.append(row)
            if reason is None:
                nid = f'post{len(nominees):02d}'
                nominee = {'post_id': nid, 'query_index': discovery['query_index'], 'rank': hit['rank'],
                           'url': hit['url'], 'title': hit['title'].removeprefix('Forgotten Languages Full: '),
                           'search_snippet_exposure': True, 'untouched_test_eligible': False}
                nominees.append(nominee)
                selected.append(nid)
                seen.add(identity(hit['url']))
        slots.extend({'query_index': discovery['query_index'], 'slot': i, 'post_id': selected[i] if i < len(selected) else None,
                      'unfilled_reason': None if i < len(selected) else 'no_eligible_result_within_nomination'} for i in range(2))
    return {'nominees': nominees, 'hit_ledger': ledger, 'slots': slots,
            'queries_with_no_hits': [d['query_index'] for d in discoveries if not search_hits(d['response'])]}


def known_metadata(root):
    paths = set((root/'experiments').glob('*.json')) | set((root/'benchmarks').rglob('*.json'))
    paths |= set((root/'data/normalized').glob('*.json'))
    paths |= {p for p in (root/'data').rglob('*receipt*.json') if 'v37' not in p.parts}
    paths |= {root/'runs/000015_kamri_dataset_audit/report.json', root/'runs/000036_mixed_edit_transfer/natural_evidence_audit.json'}
    urls, titles = set(), set()
    def walk(obj, key=''):
        if isinstance(obj, dict):
            for k, v in obj.items():
                walk(v, k)
        elif isinstance(obj, list):
            for v in obj:
                walk(v, key)
        elif isinstance(obj, str):
            if obj.startswith(('http://', 'https://')) and ('url' in key.lower() or key in ('source', 'fl')):
                urls.add(obj)
            if 'title' in key.lower():
                titles.add(obj)
    for path in sorted(paths):
        walk(json.loads(path.read_text()))
    return {'urls': sorted(urls), 'titles': sorted(titles), 'input_files': [str(p.relative_to(root)) for p in sorted(paths)]}


def citation(url, text=''):
    """Only explicit scholarly links; metadata claims remain provisional."""
    url = url.rstrip('.,;')
    p = urlparse(url)
    if p.scheme not in ('http', 'https') or p.username or p.password:
        return None
    host = (p.hostname or '').lower()
    if host in ('doi.org', 'dx.doi.org') and re.fullmatch(r'/10\.\d{4,9}/\S+', p.path):
        return {'identifier': 'doi:'+p.path[1:].lower(), 'url': urlunparse(p._replace(scheme='https', fragment='')),
                'request_url': urlunparse(p._replace(scheme='https', fragment='')), 'kind': 'doi', 'citation_text': text}
    if host in ('arxiv.org', 'www.arxiv.org'):
        m = re.fullmatch(r'/(?:abs|pdf)/((?:\d{4}\.\d{4,5}|[a-z-]+/\d{7})(?:v\d+)?)(?:\.pdf)?', p.path)
        if m:
            identifier = m.group(1)
            return {'identifier': 'arxiv:'+re.sub(r'v\d+$', '', identifier), 'url': url,
                    'request_url': 'https://arxiv.org/pdf/'+identifier, 'kind': 'arxiv', 'citation_text': text}
    if p.path.lower().endswith('.pdf') and (host.endswith(('.edu', '.ac.uk', '.edu.au')) or
            host in ('www.cambridge.org', 'cambridge.org', 'link.springer.com', 'journals.aps.org', 'www.nature.com', 'pmc.ncbi.nlm.nih.gov')):
        return {'identifier': 'pdf:'+urlunparse(p._replace(scheme='https', fragment='')), 'url': url,
                'request_url': urlunparse(p._replace(scheme='https', fragment='')), 'kind': 'direct_pdf', 'citation_text': text}
    return None


def citation_metadata(content, indexed=False):
    if indexed:
        links = [(m.group(0), '') for m in re.finditer(r'https?://[^\s<>"\)\]]+', content)]
    else:
        soup = BeautifulSoup(content, 'html.parser')
        bodies = soup.select('div.post-body')
        if len(bodies) != 1:
            return {'links': [], 'eligible_citations': [], 'reason': 'not_exactly_one_post_body'}
        # Preserve link order from the actual body; no target/source text comparison.
        links = []
        for node in bodies[0].descendants:
            if getattr(node, 'name', None) == 'a' and node.get('href'):
                links.append((node['href'], node.get_text(' ', strip=True)))
            elif isinstance(node, NavigableString) and not any(getattr(p, 'name', None) == 'a' for p in node.parents):
                links += [(m.group(0), '') for m in re.finditer(r'https?://[^\s<>"\)\]]+', str(node))]
    ledger, eligible, seen = [], [], set()
    for url, text in links:
        c = citation(url, text)
        row = {'url': url, 'citation_text': text, 'eligible': c is not None,
               'reason': None if c else 'not_explicit_scholarly_identifier_or_allowed_pdf'}
        ledger.append(row)
        if c and c['identifier'] not in seen:
            eligible.append(c)
            seen.add(c['identifier'])
    return {'links': ledger, 'eligible_citations': eligible, 'reason': None}


def select_sources(post_records, known):
    old_ids = {c['identifier'] for u in known['urls'] if (c := citation(u))}
    old_keys = {identity(u) for u in known['urls']}
    selected, ledger, seen = [], [], set()
    for post in post_records:
        for c in post['metadata']['eligible_citations']:
            key = c['identifier']
            reason = ('known_exposed_identifier_or_url' if key in old_ids or identity(c['url']) in old_keys else
                      'duplicate_identifier' if key in seen else 'four_work_cap_reached' if len(selected) >= 4 else None)
            ledger.append({'post_id': post['post_id'], **c, 'selected': reason is None, 'exclusion_reason': reason})
            if reason is None:
                selected.append({'source_id': f'source{len(selected):02d}', 'post_id': post['post_id'], **c,
                                 'novelty': 'provisional_identifier_not_in_saved_inventory',
                                 'connected_work_independence_confirmed': False, 'untouched_test_eligible': False})
                seen.add(key)
    return {'selected': selected, 'candidate_ledger': ledger, 'unfilled_source_slots': 4-len(selected)}


def source_material(raw, receipt):
    if not receipt['transport_complete']:
        return {'transport_available': False, 'representation': 'unavailable_or_incomplete', 'source_prose_verified': False,
                'review_ready': False, 'reason': 'transport_failure'}
    pdf = raw.startswith(b'%PDF-')
    if pdf:
        return {'transport_available': True, 'representation': 'raw_pdf_unreviewed', 'source_prose_verified': False,
                'review_ready': False, 'reason': 'edition_and_page_extraction_review_pending'}
    soup = BeautifulSoup(raw, 'html.parser')
    title = soup.title.get_text(' ', strip=True) if soup.title else ''
    return {'transport_available': True, 'representation': 'html_or_other', 'html_title': title,
            'source_prose_verified': False, 'review_ready': False, 'reason': 'landing_or_other_content_requires_prose_and_edition_review'}
