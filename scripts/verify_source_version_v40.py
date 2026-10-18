"""Read-only, separately implemented checks of v40 evidence; no acquisition."""
from datetime import datetime, timezone
import gzip
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import sys
import tarfile
from bs4 import BeautifulSoup
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from verify_correspondence_v6 import check_hashes


def read(path):
    return json.loads((ROOT / path).read_text())


def sha(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def main():
    run = ROOT / 'runs/000040_source_version'
    check_hashes(run)
    cfg = read('experiments/source_version_v40.json')
    pre = read('data/v40/preflight.json')
    assert cfg['request_budget'] == 2
    for path, expected in pre['hashes'].items():
        assert sha(path) == expected, path
    for path, expected in cfg['input_hashes'].items():
        assert pre['hashes'][path] == expected
    assert sha('experiments/source_version_v40.json') == pre['hashes']['experiments/source_version_v40.json']
    assert sorted(p.name for p in (ROOT / 'data/v40/acquisition').iterdir()) == ['metadata', 'source']
    receipts = {}
    previous_time = pre['sealed_at_utc']
    assert cfg['registered_at_utc'] < previous_time
    expected_urls = ['https://arxiv.org/abs/1809.09615v1', 'https://arxiv.org/src/1809.09615v1']
    for route, url in zip(cfg['routes'], expected_urls, strict=True):
        assert route['url'] == url
        key = route['id']
        r = read(f'data/v40/acquisition/{key}/receipt.json')
        receipts[key] = r
        assert previous_time < r['started_at_utc'] <= r['finished_at_utc']
        previous_time = r['finished_at_utc']
        assert r['requested_url'] == r['final_url'] == url and r['attempted']
        assert r['curl_returncode'] == 0 and r['http_status'] == 200 and r['transport_complete']
        cmd = r['command']
        assert cmd[0] == 'curl' and cmd[-1] == url
        assert not any(x in cmd for x in ['--retry', '--insecure', '-k'])
        for option, value in [('--connect-timeout', '8'), ('--max-time', '20'), ('--max-redirs', '3'),
                              ('--proto', '=https'), ('--proto-redir', '=https')]:
            assert cmd[cmd.index(option) + 1] == value
        maximum = 4194304 if key == 'metadata' else 20971520
        assert r['max_body_bytes'] == maximum and cmd[cmd.index('--max-filesize') + 1] == str(maximum)
        for name, item in r['artifacts'].items():
            path = f'data/v40/acquisition/{key}/{name}'
            assert sha(path) == item['sha256'] and (ROOT / path).stat().st_size == item['bytes']
        assert r['artifacts']['body.bin']['bytes'] <= maximum
    html = BeautifulSoup((ROOT / 'data/v40/acquisition/metadata/body.bin').read_bytes(), 'html.parser')
    observed = read('data/v40/metadata_observations.json')
    assert observed['html_title'] == html.title.get_text()
    assert observed['meta_tags'] == [dict(tag.attrs) for tag in html.select('meta')]
    assert observed['canonical_links'] == [dict(tag.attrs) for tag in html.select('link[rel=canonical]')]
    assert observed['version_links'] == [dict(tag.attrs) for tag in html.select('a[href]') if '1809.09615v' in tag.get('href', '')]
    history = [tag.get_text(' ', strip=True) for tag in html.select('.submission-history')]
    assert history == observed['submission_history'] and len(history) == 1
    assert re.findall(r'\[v\d+\]', history[0]) == ['[v1]']
    assert 'Tue, 25 Sep 2018 17:56:31 UTC' in history[0]
    assert html.select_one('meta[property="og:url"]')['content'] == expected_urls[0]
    assert '[1809.09615v1]' in html.title.get_text()
    assert html.select_one('meta[name="citation_arxiv_id"]')['content'] == '1809.09615'
    assert (ROOT / 'data/v40/metadata_visible.txt').read_text() == html.get_text('\n', strip=True)
    with gzip.GzipFile(fileobj=io.BytesIO((ROOT / 'data/v40/acquisition/source/body.bin').read_bytes())) as gz:
        raw = gz.read(67108865)
    assert len(raw) <= 67108864
    with tarfile.open(fileobj=io.BytesIO(raw), mode='r:') as archive:
        members = archive.getmembers()
        assert len(members) <= 1000 and len({m.name for m in members}) == len(members)
        content = {}
        for m in members:
            assert not m.name.startswith('/') and '..' not in PurePosixPath(m.name).parts
            assert '\\' not in m.name and not re.match(r'^[A-Za-z]:', m.name)
            assert m.isfile() and 0 <= m.size <= 4194304
            content[m.name] = archive.extractfile(m).read()
            assert len(content[m.name]) == m.size
    source = read('data/v40/source_observations.json')
    assert source['available'] and source['transport_complete'] and source['format'] == 'gzip-tar'
    assert source['expanded_bytes'] == len(raw) and source['member_count'] == len(members) == 8
    assert sum(len(v) for v in content.values()) <= 67108864
    assert source['members'] == [{'name': name, 'bytes': len(value), 'sha256': hashlib.sha256(value).hexdigest()}
                                 for name, value in sorted(content.items())]
    assert [r['name'] for r in source['tex_files']] == sorted(n for n in content if n.lower().endswith(('.tex', '.ltx')))
    for item in source['tex_files']:
        text = content[item['name']].decode(item['encoding'])
        assert text == (ROOT / item['decoded_text']).read_text() and len(text) == item['characters']
        expected = []
        for match in re.finditer(r'\\(?:documentclass|begin\{document\}|date|today|maketitle)\b', text):
            # begin-document ends in a brace, so include it separately below.
            if match.group() == '\\begin{document}':
                continue
            start = text.rfind('\n', 0, match.start()) + 1
            end = text.find('\n', match.end()) + 1 or len(text)
            prefix = text[start:match.start()]
            assert '%' not in prefix  # Actual v40 witnesses have no ambiguous comment prefixes.
            expected.append((match.start(), match.end(), match.group()))
        expected += [(m.start(), m.end(), m.group()) for m in re.finditer(r'\\begin\{document\}', text)]
        actual = []
        for row in item['date_witnesses']:
            a, b = row['span']; x, y = row['line_span']
            assert text[a:b] == row['command'] and text[x:y] == row['line_text']
            assert row['line'] == text.count('\n', 0, a) + 1
            actual.append((a, b, row['command']))
        assert sorted(expected) == sorted(actual)
    review = read('data/v40/manual_review.json')
    tex = content['anita_evts.tex'].decode('utf-8')
    assert re.sub(r'\s+', ' ', re.search(r'\\title\{([^}]+)\}', tex).group(1)).strip() == html.select_one('meta[name="citation_title"]')['content']
    assert tex[5119:5132] == '\\date{\\today}'
    assert tex.index('\\begin{document}') < 5119 < tex.index('\\maketitle')
    assert tex.count('\\date') == tex.count('\\today') == tex.count('\\maketitle') == 1
    assert not re.search(r'\\(?:if\w*|else|fi|catcode)\b', tex[:tex.index('\\maketitle')])
    assert '\\today' not in content['aasdefs.sty'].decode() and '\\date' not in content['aasdefs.sty'].decode()
    assert review['source_date_witness'] == {'path': 'data/v40/tex/member0004.txt', 'member': 'anita_evts.tex', 'span': [5119, 5132], 'line': 98, 'text': '\\date{\\today}'}
    assert review['mechanism_supported'] and not review['exact_build_chain_authenticated']
    pdf = PdfReader(ROOT / cfg['preserved_pdf'])
    saved = read('data/v40/preserved_pdf_metadata.json')
    assert saved['sha256'] == sha(cfg['preserved_pdf']) and saved['pages'] == len(pdf.pages) == 15
    assert saved['metadata'] == {str(k): str(v) for k, v in pdf.metadata.items()}
    assert saved['first_page_text'] == pdf.pages[0].extract_text()
    assert saved['metadata']['/CreationDate'] == saved['metadata']['/ModDate'] == 'D:20250307191020Z'
    assert '(Dated: March 7, 2025)' in saved['first_page_text']
    report = read('runs/000040_source_version/report.json')
    assert report['outcome'] == 'render_time_date_mechanism_supported_historical_bytes_unproven'
    assert report['requests_attempted'] == report['request_denominator'] == report['requests_complete'] == 2
    assert report['registered_routes_observed'] == 2 and report['source_members'] == 8 and report['tex_files'] == 1
    for obj in [report, review, saved]:
        assert not obj['historical_bytes_authenticated']
    for key in ['quoted_blocks_rescored', 'semantic_labels_admitted', 'source_identities_admitted',
                'independent_reviews_admitted', 'untouched_test_units_admitted', 'external_messages_sent']:
        assert report[key] == 0
    assert report['scientific_acceptance'] is report['semantic_evaluation_metrics'] is None
    previous = []
    for path in sorted((ROOT / 'runs').glob('000*/manifest.json')):
        if path.parent != run:
            check_hashes(path.parent)
            previous.append(path.parent.name)
    assert len(previous) == 39
    for path in (ROOT / 'reports').glob('*_deliverable_seal.json'):
        for name, expected in json.loads(path.read_text()).get('deliverable_hashes', {}).items():
            assert sha(name) == expected
    result = {'state': 'verified', 'manifest_sha256': sha('runs/000040_source_version/manifest.json'),
              'request_and_preflight_hashes_verified': True, 'source_inventory_and_witnesses_verified': True,
              'html_and_pdf_observations_reextracted': True, 'shared_libraries': ['BeautifulSoup', 'pypdf', 'tarfile', 'gzip'],
              'independent_scientific_review': False, 'historical_bytes_authenticated': False,
              'prior_runs_preserved': previous}
    out = ROOT / 'reports/000040_verification.json'
    if out.exists():
        assert {k: v for k, v in json.loads(out.read_text()).items() if k != 'verified_at_utc'} == result
    else:
        with out.open('x') as stream:
            json.dump(result | {'verified_at_utc': datetime.now(timezone.utc).isoformat()}, stream, indent=2)
            stream.write('\n')
    print(json.dumps({'state': 'verified', 'prior_runs_preserved': len(previous),
                      'historical_bytes_authenticated': False}, indent=2))


if __name__ == '__main__':
    main()
