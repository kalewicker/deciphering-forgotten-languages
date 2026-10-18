"""Read only the eight registered PDF pages; retain raw text and renders."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,sys
import pypdf
import pypdfium2

ROOT=Path(__file__).resolve().parents[1]


def h(raw):return hashlib.sha256(raw).hexdigest()


def main():
    cfg=json.loads((ROOT/'experiments/kamri_residual_context_v27.json').read_text())
    pre=json.loads((ROOT/'data/v27/preflight.json').read_text())
    for hashes in [pre['input_hashes'],pre['code_hashes']]:
        for path,digest in hashes.items():assert h((ROOT/path).read_bytes())==digest,path
    assert pypdf.__version__==cfg['pypdf_version'] and str(pypdfium2.PDFIUM_INFO)==cfg['pdfium_version']
    out=ROOT/'data/v27/page_views.json';assert not out.exists()
    qa=ROOT/'data/v27/qa';qa.mkdir(exist_ok=False)
    receipt={'extracted_at_utc':datetime.now(timezone.utc).isoformat(),'state':'running','runtime':sys.executable,
             'pypdf_version':pypdf.__version__,'pdfium_version':str(pypdfium2.PDFIUM_INFO),'pages':[],'error':None}
    try:
        for work in cfg['pdf_sources']:
            path=ROOT/work['path'];reader=pypdf.PdfReader(path);assert len(reader.pages)==work['page_count']
            pdf=pypdfium2.PdfDocument(str(path))
            for number in work['pages']:
                page=pdf[number-1];bmp=page.render(scale=1.5);rgb=bmp.to_pil().convert('RGB')
                image=qa/f'{work["id"]}_{number:03d}.png';rgb.save(image)
                text=reader.pages[number-1].extract_text();assert isinstance(text,str) and text.strip()
                receipt['pages'].append({'id':f'{work["id"]}:pdf:{number:03d}','parent_work':work['id'],
                    'source_group':work['id'],'pdf_path':work['path'],'pdf_sha256':h(path.read_bytes()),
                    'pdf_page_one_based':number,'text':text,'text_sha256':h(text.encode()),
                    'image':str(image.relative_to(ROOT)),'image_sha256':h(image.read_bytes()),
                    'pixel_size':list(rgb.size),'pixels_sha256':h(rgb.tobytes()),'dimensions':list(page.get_size())})
                bmp.close();page.close()
            pdf.close()
        receipt['state']='completed'
    except Exception as error:
        receipt['state']='failed';receipt['error']=f'{type(error).__name__}: {error}'
        out.write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+'\n');raise
    out.write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps({'state':receipt['state'],'pages_extracted_and_rendered':len(receipt['pages'])}))


if __name__=='__main__':main()
