"""Freeze raw page views, contexts, candidates and all controls before scoring."""
from pathlib import Path
import json
from fl_decipher.corpus import digest,dump_json
from fl_decipher.natural_v12 import utc
from fl_decipher.source_specificity_v26 import tokens,frame
from fl_decipher.residual_context_v27 import context,windows

ROOT=Path(__file__).resolve().parents[1]


def read(p):return json.loads((ROOT/p).read_text())


def main():
    cfg=read('experiments/kamri_residual_context_v27.json');pre=read('data/v27/preflight.json')
    for hashes in [pre['input_hashes'],pre['code_hashes']]:
        for p,h in hashes.items():assert digest((ROOT/p).read_bytes())==h,p
    out=ROOT/'data/v27/frozen.json';assert not out.exists()
    pages=read('data/v27/page_views.json');assert pages['state']=='completed' and len(pages['pages'])==8
    visual=read('data/v27/visual_review.json');assert visual['pages_reviewed']==8 and visual['independent_semantic_review'] is False
    appendix=read('data/v26/evidence_spans.json');pairs={p['id']:p for p in appendix['pairs']}
    prior=read('experiments/kamri_source_specificity_v26.json')
    blocked=sorted({t['form'] for q in prior['queries'] for a in q['anchors'] for t in tokens(a)})
    documents=[{k:p[k] for k in ['id','parent_work','source_group','text','text_sha256','pdf_path','pdf_page_one_based']}|
               {'kind':'raw_pdf_page'} for p in pages['pages']]
    for n in cfg['other_documents']:
        text=read(n['path'])['text']
        documents.append(n|{'kind':'historical_normalized_export','parent_work':n['source_group'],'text':text,'text_sha256':digest(text.encode())})
    queries=[];controls=[]
    for q in cfg['queries']:
        raw=(ROOT/f'data/v25/packets/{q["packet"]}/fl_post.txt').read_bytes()
        assert digest(raw)==appendix['text_sha256'][q['packet']]['fl_post.txt']
        text=raw.decode('utf-8');spans=[pairs[k]['fl_span'] for k in q['evidence_ids']]
        for s in spans:assert text[s['start']:s['end']]==s['text']
        query=q|context(text,spans,40);query['text_sha256']=digest(query['text'].encode());queries.append(query)
        priorq=next(p for p in prior['queries'] if p['id']==q['id'])
        views=[('query_copy',query['text']),('anchor_frame',frame(priorq['anchors'],160)),
               ('query_reversed',' '.join(t['form'] for t in reversed(tokens(query['text'])))),
               ('legacy_publisher_window',(ROOT/f'data/v25/packets/{q["packet"]}/publisher_window.txt').read_text())]
        for kind,view in views:controls.append({'control_id':q['id']+':'+kind,'query_id':q['id'],'kind':kind,'text':view,'text_sha256':digest(view.encode())})
    frozen={'prepared_at_utc':utc(),'documents':documents,'queries':queries,'blocked_tokens':blocked,
            'windows':[w for d in documents for w in windows(d,160,80)],'controls':controls,
            'counts':{'documents':17,'raw_pdf_pages':8,'historical_exports':9,'queries':3,'positive_works':2,
                      'same_work_alternative_pages_per_query':[4,4,2],'control_views':12}}
    frozen['counts']['windows']=len(frozen['windows']);frozen['counts']['natural_window_scores']=3*len(frozen['windows'])
    assert len(documents)==17 and len(queries)==3 and len(controls)==12
    dump_json(out,frozen)
    paths={p:digest(pth.read_bytes()) for p,pth in [('experiments/kamri_residual_context_v27.json',ROOT/'experiments/kamri_residual_context_v27.json')]}
    paths.update({str(p.relative_to(ROOT)):digest(p.read_bytes()) for p in (ROOT/'data/v27').rglob('*') if p.is_file()})
    bp=ROOT/'benchmarks/kamri_residual_context_v27.json';assert not bp.exists()
    dump_json(bp,{'experiment_id':cfg['experiment_id'],'frozen_at_utc':utc(),'input_hashes':cfg['input_hashes']|paths,'counts':frozen['counts']})
    print(json.dumps({'counts':frozen['counts'],'blocked_tokens':len(blocked),'query_context_tokens':[q['token_count'] for q in queries]},indent=2))


if __name__=='__main__':main()
