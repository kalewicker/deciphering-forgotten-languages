"""Read-only publisher PDF parsing and fixed-window rendering in bundled runtime."""
from pathlib import Path
import json
import sys
import hashlib
from datetime import datetime, timezone
import pypdf
import pypdfium2 as pdfium

ROOT = Path(__file__).resolve().parents[1]

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    cfg = json.loads((ROOT/'experiments/kamri_capture_review_v23.json').read_text())
    out = ROOT/'data/v23/pdf_diagnostics.json'
    if out.exists():
        raise FileExistsError(out)
    results = []
    for n in cfg['nominees']:
        route = ROOT/'data/v23/acquisition'/(n['id']+'_source')
        receipt = json.loads((route/'receipt.json').read_text());body = route/'body.bin'
        r = {'nominee_id': n['id'], 'state': 'unavailable', 'pdf_parse_valid': False, 'source_window_present': False,
             'source_body_sha256': sha(body) if body.exists() else None, 'matches_prior_snapshot': body.exists() and sha(body) == n['source_snapshot_sha256'],
             'page_count': None, 'selected_pages_one_based': n['source_pages_one_based'], 'images': [], 'error': None}
        if receipt['transport_complete'] and body.read_bytes().startswith(b'%PDF-'):
            try:
                reader = pypdf.PdfReader(body)
                r['page_count'] = len(reader.pages);r['pdf_parse_valid'] = True
                r['source_window_present'] = max(n['source_pages_one_based']) <= r['page_count']
                r['state'] = 'parsed' if r['source_window_present'] else 'window_unavailable'
                if r['source_window_present']:
                    directory = ROOT/'data/v23/qa'/n['id'];directory.mkdir(parents=True, exist_ok=False)
                    document = pdfium.PdfDocument(str(body))
                    for number in n['source_pages_one_based']:
                        page = document[number-1];bitmap = page.render(scale=1.5)
                        path = directory/f'page_{number:03d}.png';bitmap.to_pil().save(path)
                        r['images'].append({'page_one_based': number, 'path': str(path.relative_to(ROOT)), 'sha256': sha(path)})
                        bitmap.close();page.close()
                    document.close()
            except Exception as e:
                r['state'] = 'parse_or_render_failed';r['error'] = f'{type(e).__name__}: {e}'
        results.append(r)
    out.write_text(json.dumps({'inspected_at_utc': datetime.now(timezone.utc).isoformat(), 'runtime': sys.executable,
                               'pypdf_version': pypdf.__version__, 'records': results, 'independent_semantic_review': False}, indent=2)+'\n')
    print(json.dumps({'publisher_pdf_diagnostics': results}, indent=2))

if __name__ == '__main__':
    main()
