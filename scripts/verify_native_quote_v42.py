"""Offline native-page/quotation accounting, independently reconstructed."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys
import unicodedata
from urllib.parse import urlparse
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from verify_correspondence_v6 import check_hashes


def read(path):
    return json.loads((ROOT / path).read_text())


def sha(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def norm(text):
    return ' '.join(unicodedata.normalize('NFC', text).casefold().split())


def key(url):
    p = urlparse(url)
    assert p.scheme == 'https' and not p.username and not p.password and p.port in (None, 443)
    return p.scheme, p.hostname, p.path.rstrip('/'), p.query


def hits(query, text, rows):
    needle = norm(query); haystack = norm(text)
    positions = [m.start() for m in re.finditer('(?=' + re.escape(needle) + ')', haystack)]
    assert len(rows) == len(positions)
    for row, pos in zip(rows, positions, strict=True):
        assert row['normalized_span'] == [pos, pos + len(needle)]
        a, b = row['source_span']
        assert text[a:b] == row['source_quote'] and needle in norm(text[a:b])
        assert (a == 0 or text[a - 1].isspace()) and (b == len(text) or text[b].isspace())


def main():
    run = ROOT / 'runs/000042_native_quote'
    check_hashes(run)
    cfg = read('experiments/native_quote_v42.json'); pre = read('data/v42/preflight.json')
    r = read('data/v42/acquisition/source/receipt.json'); page = read('data/v42/page_observations.json')
    for path, expected in pre['hashes'].items():
        assert sha(path) == expected, path
    assert all(pre['hashes'][p] == h for p, h in cfg['input_hashes'].items())
    assert pre['hashes']['experiments/native_quote_v42.json'] == sha('experiments/native_quote_v42.json')
    assert cfg['registered_at_utc'] < pre['sealed_at_utc'] < r['started_at_utc'] <= r['finished_at_utc']
    lead = read('data/v41/discovery_ledger.json')
    assert cfg['source_url'] == lead['hit_ledger'][lead['selected_rank']]['url'] == r['requested_url']
    assert cfg['quote'] == read('data/v39/frozen_queries.json')['queries'][0]
    q = cfg['quote']['text']
    assert read('data/v38/target_export.json')['text'][slice(*cfg['quote']['span'])] == q
    assert cfg['request_budget'] == 1
    assert [p.name for p in (ROOT / 'data/v42/acquisition').iterdir()] == ['source']
    cmd = r['command']; assert cmd[0] == 'curl' and cmd[-1] == cfg['source_url'] and r['attempted']
    for name, value in [('--connect-timeout', '8'), ('--max-time', '20'), ('--max-redirs', '3'),
                        ('--max-filesize', '4194304'), ('--proto', '=https'), ('--proto-redir', '=https')]:
        assert cmd[cmd.index(name) + 1] == value
    assert not any(x in cmd for x in ['--insecure', '-k', '--retry', '--cookie', '--user'])
    for name, item in r['artifacts'].items():
        path = 'data/v42/acquisition/source/' + name
        assert sha(path) == item['sha256'] and (ROOT / path).stat().st_size == item['bytes']
    complete = r['curl_returncode'] == 0 and r['http_status'] == 200 and 'body.bin' in r['artifacts'] and r['artifacts']['body.bin']['bytes'] <= 4194304
    assert r['transport_complete'] == complete and r['max_body_bytes'] == 4194304
    if complete:
        raw = (ROOT / 'data/v42/acquisition/source/body.bin').read_bytes()
        soup = BeautifulSoup(raw, 'html.parser')
        headings = [h.get_text(' ', strip=True) for h in soup.select('h1')]
        urls = [tag.get('href', '') for tag in soup.select('link[rel=canonical]')]
        urls += [tag.get('content', '') for tag in soup.select('meta[property="og:url"]')]
        assert page['headings'] == headings and page['identity_urls'] == urls
        assert page['metadata'] == [dict(t.attrs) for t in soup.select('meta')]
        assert page['time_elements'] == [dict(t.attrs) | {'visible_text': t.get_text(' ', strip=True)} for t in soup.select('time')]
        bodies = soup.select('body')
        for tag in soup.select('script,style,noscript,template,svg,canvas'):
            tag.decompose()
        text = bodies[0].get_text(' ', strip=True) if len(bodies) == 1 else ''
        gate = {'transport_complete': True, 'html_markup': b'<html' in raw.lower(), 'single_body': len(bodies) == 1,
                'final_url_matches': key(r['final_url']) == key(cfg['source_url']),
                'publisher_identity_url_matches': any(key(u) == key(cfg['source_url']) for u in urls),
                'single_expected_h1': sum(norm(h) == norm(cfg['expected_title']) for h in headings) == 1,
                'minimum_visible_characters': len(text) >= cfg['minimum_visible_characters'],
                'no_challenge_text': not any(s in text.casefold() for s in cfg['challenge_signatures'])}
        assert page['requirements'] == gate and page['material_available'] == all(gate.values())
        assert page['unmet'] == [k for k, v in gate.items() if not v]
        if page['material_available']:
            assert page['text'] == text == (ROOT / 'data/v42/visible_page.txt').read_text()
            hits(q, text, page['quote_hits'])
            assert page['quote_present'] == bool(page['quote_hits'])
            paragraphs = [p.get_text(' ', strip=True) for p in bodies[0].select('p')]
            expected_ids = [i for i, p in enumerate(paragraphs) if norm(q) in norm(p)]
            assert [c['quote_paragraph_index'] for c in page['contexts']] == expected_ids
            for c, i in zip(page['contexts'], expected_ids, strict=True):
                assert c['quote_paragraph'] == paragraphs[i]
                hits(q, paragraphs[i], c['paragraph_hits'])
                assert c['body_paragraph_spans'] == [[m.start(), m.end()] for m in re.finditer(re.escape(paragraphs[i]), text)]
                expected = [{'paragraph_index': j, 'text': paragraphs[j]} for j in range(max(0, i - 1), min(len(paragraphs), i + 2))]
                assert c['window'] == expected
                context = ' '.join(p['text'] for p in expected)
                assert c['gorham_name_visible'] == bool(re.search(r'\bgorham\b', context, re.I))
                assert c['he_says_visible'] == ('he says' in context.casefold()) and not c['attribution_authenticated']
    else:
        assert not page['material_available'] and page['unmet'] == ['transport_complete']
    if not page['material_available']:
        assert page['text'] is page['quote_present'] is page['quote_hits'] is None and page['contexts'] == []
    review = read('data/v42/context_review.json'); report = read('runs/000042_native_quote/report.json')
    assert page['material_available'] and page['quote_present'] and len(page['quote_hits']) == len(page['contexts']) == 1
    assert review['publisher_attribution_observed'] and not review['interview_or_original_quotation_authenticated']
    context = page['contexts'][0]
    assert 'Gorham says' in context['quote_paragraph'] and 'he says' in context['quote_paragraph']
    assert review['quote_paragraph_index'] == context['quote_paragraph_index'] == 15
    assert review['body_quote_span'] == page['quote_hits'][0]['source_span'] == [6903, 7053]
    assert report['requests_attempted'] == report['request_denominator'] == report['requests_complete'] == 1
    assert report['material_available'] and report['complete_quote_present'] and report['publisher_attribution_observed']
    assert report['body_characters'] == len(page['text']) == 12072 and report['whole_quote_occurrences'] == 1
    for k in ['additional_source_or_search_requests', 'other_quotations_scored', 'semantic_labels_admitted', 'source_identities_admitted',
              'independent_reviews_admitted', 'untouched_test_units_admitted', 'external_messages_sent']:
        assert report[k] == 0
    assert not report['historical_date_authenticated'] and not report['interview_or_original_quotation_authenticated']
    assert report['scientific_acceptance'] is report['semantic_evaluation_metrics'] is None
    previous = []
    for p in sorted((ROOT / 'runs').glob('000*/manifest.json')):
        if p.parent != run:
            check_hashes(p.parent); previous.append(p.parent.name)
    assert len(previous) == 41
    for p in (ROOT / 'reports').glob('*_deliverable_seal.json'):
        for path, expected in json.loads(p.read_text()).get('deliverable_hashes', {}).items():
            assert sha(path) == expected
    result = {'state': 'verified', 'manifest_sha256': sha('runs/000042_native_quote/manifest.json'),
              'raw_request_and_frozen_inputs_verified': True, 'page_gate_and_quote_witnesses_verified': True,
              'context_window_verified': True, 'shared_html_parser': 'BeautifulSoup html.parser',
              'independent_scientific_review': False, 'original_quotation_source_authenticated': False,
              'prior_runs_preserved': previous}
    out = ROOT / 'reports/000042_verification.json'
    if out.exists():
        assert {k: v for k, v in json.loads(out.read_text()).items() if k != 'verified_at_utc'} == result
    else:
        with out.open('x') as stream:
            json.dump(result | {'verified_at_utc': datetime.now(timezone.utc).isoformat()}, stream, indent=2); stream.write('\n')
    print(json.dumps({'state': 'verified', 'prior_runs_preserved': len(previous), 'quote_present': page['quote_present']}, indent=2))


if __name__ == '__main__':
    main()
