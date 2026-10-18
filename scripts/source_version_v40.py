"""Acquire exactly the two registered routes and preserve read-only observations."""
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from bs4 import BeautifulSoup
from pypdf import PdfReader
from fl_decipher.capture_review_v23 import request
from fl_decipher.source_version_v40 import digest, inventory, date_witnesses

ROOT = Path(__file__).resolve().parents[1]


def now():
    return datetime.now(timezone.utc).isoformat()


def write(path, value):
    path = ROOT / path
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False)
        stream.write('\n')


def main():
    cfg = json.loads((ROOT / 'experiments/source_version_v40.json').read_text())
    code = ['src/fl_decipher/source_version_v40.py', 'scripts/source_version_v40.py',
            'tests/test_source_version_v40.py', 'src/fl_decipher/capture_review_v23.py']
    hashes = dict(cfg['input_hashes'])
    hashes['experiments/source_version_v40.json'] = digest((ROOT / 'experiments/source_version_v40.json').read_bytes())
    hashes.update({p: digest((ROOT / p).read_bytes()) for p in code})
    for path, expected in hashes.items():
        assert digest((ROOT / path).read_bytes()) == expected
    assert not (ROOT / 'data/v40').exists(), 'Never reacquire over prior evidence'
    write('data/v40/preflight.json', {'sealed_at_utc': now(), 'hashes': hashes})
    receipts = {}
    for route in cfg['routes']:
        receipts[route['id']] = request(ROOT / 'data/v40/acquisition', route['id'], route['url'],
                                        cfg['request_limits'], route['kind'])
    metadata = {'transport_complete': receipts['metadata']['transport_complete']}
    if metadata['transport_complete']:
        raw = (ROOT / 'data/v40/acquisition/metadata/body.bin').read_bytes()
        soup = BeautifulSoup(raw, 'html.parser')
        visible = soup.get_text('\n', strip=True)
        with (ROOT / 'data/v40/metadata_visible.txt').open('x') as stream:
            stream.write(visible)
        history = soup.select('.submission-history')
        metadata.update({'html_title': soup.title.get_text() if soup.title else None,
                         'meta_tags': [dict(tag.attrs) for tag in soup.select('meta')],
                         'canonical_links': [dict(tag.attrs) for tag in soup.select('link[rel=canonical]')],
                         'submission_history': [tag.get_text(' ', strip=True) for tag in history],
                         'version_links': [dict(tag.attrs) for tag in soup.select('a[href]') if '1809.09615v' in tag.get('href', '')]})
    write('data/v40/metadata_observations.json', metadata)
    source = {'transport_complete': receipts['source']['transport_complete'], 'available': False,
              'members': [], 'tex_files': []}
    if source['transport_complete']:
        raw = (ROOT / 'data/v40/acquisition/source/body.bin').read_bytes()
        status, files = inventory(raw)
        source.update(status)
        for index, (name, content) in enumerate(sorted(files.items())):
            source['members'].append({'name': name, 'bytes': len(content), 'sha256': digest(content)})
            if name.lower().endswith(('.tex', '.ltx')):
                try:
                    text = content.decode('utf-8'); encoding = 'utf-8'
                except UnicodeDecodeError:
                    text = content.decode('latin-1'); encoding = 'latin-1'
                path = f'data/v40/tex/member{index:04d}.txt'
                out = ROOT / path
                out.parent.mkdir(parents=True, exist_ok=True)
                with out.open('x') as stream:
                    stream.write(text)
                source['tex_files'].append({'name': name, 'decoded_text': path, 'encoding': encoding,
                                           'characters': len(text), 'date_witnesses': date_witnesses(text)})
    write('data/v40/source_observations.json', source)
    pdf = PdfReader(ROOT / cfg['preserved_pdf'])
    write('data/v40/preserved_pdf_metadata.json', {'pdf': cfg['preserved_pdf'],
          'sha256': digest((ROOT / cfg['preserved_pdf']).read_bytes()),
          'pages': len(pdf.pages), 'metadata': {str(k): str(v) for k, v in (pdf.metadata or {}).items()},
          'first_page_text': pdf.pages[0].extract_text(), 'historical_bytes_authenticated': False})
    print(json.dumps({'routes': {k: {'http_status': r['http_status'], 'complete': r['transport_complete']} for k, r in receipts.items()},
                      'source_available': source['available'], 'tex_files': len(source['tex_files'])}, indent=2))


if __name__ == '__main__':
    main()
