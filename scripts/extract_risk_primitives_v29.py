"""Pinned runtime extraction, including unchanged-image raster separator scan."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib,json,sys
import pdfplumber,PIL
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from fl_decipher.risk_layout_v29 import raster_rules


def main():
    cfg=json.loads((ROOT/'experiments/risk_layout_derivative_v29.json').read_text())
    pre=json.loads((ROOT/'data/v29/preflight.json').read_text())
    for hashes in [pre['input_hashes'],pre['code_hashes']]:
        for p,h in hashes.items():assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h,p
    assert (pdfplumber.__version__,PIL.__version__)==(cfg['pdfplumber_version'],cfg['pillow_version'])
    out=ROOT/'data/v29/primitives.json';assert not out.exists()
    result={'state':'running','extracted_at_utc':datetime.now(timezone.utc).isoformat(),'runtime':sys.executable,'pages':[]}
    try:
        with pdfplumber.open(ROOT/cfg['pdf']) as doc:
            for spec in cfg['pages']:
                p=doc.pages[spec['pdf_page_one_based']-1];chars=[];offset=0
                for i,c in enumerate(p.chars):
                    chars.append({'index':i,'text':c['text'],'native_start':offset,'native_end':offset+len(c['text']),
                                  'matrix':[round(float(v),6) for v in c['matrix']], 'fontname':c['fontname'],'upright':bool(c['upright']),
                                  **{k:round(float(c[k]),6) for k in ['x0','x1','top','bottom','size']}})
                    offset+=len(c['text'])
                with Image.open(ROOT/spec['image']) as im:
                    im=im.convert('L');w,h=im.size
                    rules=raster_rules(im.tobytes(),w,h,float(p.width),float(p.height))
                result['pages'].append({'id':spec['id'],'pdf_page_one_based':spec['pdf_page_one_based'],'width':float(p.width),'height':float(p.height),
                                        'image':spec['image'],'image_width':w,'image_height':h,'chars':chars,'raster_rules':rules})
        result['state']='completed'
    except Exception as error:
        result.update(state='failed',error=f'{type(error).__name__}: {error}')
        out.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n');raise
    out.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps({'state':result['state'],'pages':len(result['pages']),'glyphs':sum(len(p['chars']) for p in result['pages'])}))


if __name__=='__main__':main()
