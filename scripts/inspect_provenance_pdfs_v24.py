"""Fixed five-page visual/text equivalence, with whole-document text diagnostic."""
from pathlib import Path
import hashlib
import json
import sys
import pypdf
import pypdfium2 as pdfium

ROOT = Path(__file__).resolve().parents[1]


def h(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    cfg = json.loads((ROOT/'experiments/kamri_provenance_v24.json').read_text())
    seal = json.loads((ROOT/'data/v24/preflight.json').read_text())
    for p, digest in seal['input_hashes'].items() | seal['code_hashes'].items():
        assert h((ROOT/p).read_bytes()) == digest, p
    out = ROOT/'data/v24/pdf_comparison.json'
    assert not out.exists()
    qa = ROOT/'data/v24/qa';qa.mkdir(exist_ok=False)
    result = {'runtime': sys.executable, 'pypdf_version': pypdf.__version__, 'pdfium_version': str(pdfium.PDFIUM_INFO),
              'page_counts': [], 'raw_hashes': [], 'pages': [], 'all_page_text_equal': None,
              'whole_document_visual_equivalence_established': False, 'window_gate': False, 'error': None}
    try:
        paths = [ROOT/cfg['western'][key] for key in ['old_pdf', 'new_pdf']]
        result['raw_hashes'] = [h(p.read_bytes()) for p in paths]
        readers = [pypdf.PdfReader(p) for p in paths]
        result['page_counts'] = [len(r.pages) for r in readers]
        result['metadata'] = [dict(r.metadata or {}) for r in readers]
        texts = [[p.extract_text() for p in r.pages] for r in readers]
        result['all_page_text_equal'] = texts[0] == texts[1]
        result['all_page_text_hashes'] = [h(json.dumps(t, ensure_ascii=False).encode()) for t in texts]
        documents = [pdfium.PdfDocument(str(p)) for p in paths]
        for number in cfg['western']['pages_one_based']:
            record = {'page_one_based': number, 'sides': []}
            for side, reader, document, text in zip(['old', 'new'], readers, documents, texts, strict=True):
                page = document[number-1];bitmap = page.render(scale=1.5)
                rgb = bitmap.to_pil().convert('RGB');png = qa/f'{side}_{number:03d}.png';rgb.save(png)
                textpath = qa/f'{side}_{number:03d}.txt';textpath.write_text(text[number-1])
                content = reader.pages[number-1].get_contents()
                record['sides'].append({'side': side, 'dimensions': list(page.get_size()), 'pixel_size': list(rgb.size),
                    'pixels_sha256': h(rgb.tobytes()), 'image': str(png.relative_to(ROOT)), 'image_sha256': h(png.read_bytes()),
                    'text_path': str(textpath.relative_to(ROOT)), 'text_sha256': h(text[number-1].encode()),
                    'text_nonempty': bool(text[number-1].strip()), 'content_sha256': h(content.get_data() if content else b'')})
                bitmap.close();page.close()
            a, b = record['sides']
            record.update(text_equal=a['text_sha256'] == b['text_sha256'], text_nonempty=a['text_nonempty'] and b['text_nonempty'],
                          dimensions_equal=a['dimensions'] == b['dimensions'],
                          pixels_equal=a['pixel_size'] == b['pixel_size'] and a['pixels_sha256'] == b['pixels_sha256'],
                          decoded_content_streams_equal=a['content_sha256'] == b['content_sha256'])
            result['pages'].append(record)
        for d in documents:
            d.close()
        result['window_gate'] = (result['page_counts'][0] == result['page_counts'][1] and len(result['pages']) == 5
             and all(r['text_equal'] and r['text_nonempty'] and r['dimensions_equal'] and r['pixels_equal'] for r in result['pages']))
    except Exception as error:
        result['error'] = f'{type(error).__name__}: {error}'
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False)+'\n')
    print(json.dumps({k: result[k] for k in ['page_counts', 'all_page_text_equal', 'window_gate', 'error']}))


if __name__ == '__main__':
    main()
