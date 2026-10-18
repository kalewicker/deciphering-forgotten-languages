"""Fixed eight-page PDF primitives; source PDFs and previous extracts unchanged."""
from pathlib import Path
from collections import Counter
from datetime import datetime,timezone
import hashlib,json,sys
import pdfplumber

ROOT=Path(__file__).resolve().parents[1]


def h(raw):return hashlib.sha256(raw).hexdigest()


def extract(work,number,page):
    wordlist=page.extract_words(x_tolerance=3,y_tolerance=3,use_text_flow=False,keep_blank_chars=False,
                              extra_attrs=['size'],split_at_punctuation=False,expand_ligatures=False)
    words=[{'word_index':i,'text':w['text'],'upright':bool(w.get('upright',True)),
            **{key:round(float(w[key]),6) for key in ['x0','x1','top','bottom','size']}} for i,w in enumerate(wordlist)]
    edges=[{'edge_index':i,**{k:round(float(e[k]),6) for k in ['x0','x1','top','bottom']}}
           for i,e in enumerate(page.edges) if e.get('orientation')=='h']
    sizes=Counter(round(float(c['size']),3) for c in page.chars if c['text'].strip())
    modal=max(sizes,key=lambda size:(sizes[size],size))
    return {'id':f'{work}:pdf:{number:03d}','work':work,'pdf_page_one_based':number,
            'width':round(float(page.width),6),'height':round(float(page.height),6),
            'modal_font_size':modal,'words':words,'horizontal_edges':edges}


def main():
    cfg=json.loads((ROOT/'experiments/kamri_block_audit_v28.json').read_text());pre=json.loads((ROOT/'data/v28/preflight.json').read_text())
    for hashes in [pre['input_hashes'],pre['code_hashes']]:
        for p,sha in hashes.items():assert h((ROOT/p).read_bytes())==sha,p
    assert pdfplumber.__version__==cfg['pdfplumber_version']
    out=ROOT/'data/v28/pdf_geometry.json';assert not out.exists()
    result={'extracted_at_utc':datetime.now(timezone.utc).isoformat(),'state':'running','runtime':sys.executable,
            'pdfplumber_version':pdfplumber.__version__,'pages':[],'error':None}
    try:
        for work in cfg['works']:
            with pdfplumber.open(ROOT/work['pdf']) as doc:
                for number in work['pages']:result['pages'].append(extract(work['id'],number,doc.pages[number-1]))
        result['state']='completed'
    except Exception as error:
        result['state']='failed';result['error']=f'{type(error).__name__}: {error}'
        out.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n');raise
    out.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps({'state':result['state'],'pages':len(result['pages']),'words':sum(len(p['words']) for p in result['pages'])}))


if __name__=='__main__':main()
