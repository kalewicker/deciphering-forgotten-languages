"""Audit the incoming appendix and freeze all candidate/control texts before scoring."""
from pathlib import Path
import json
import re
from fl_decipher.corpus import digest,dump_json
from fl_decipher.natural_v12 import utc
from fl_decipher.source_specificity_v26 import windows,frame,masked,corrected_spellings

ROOT=Path(__file__).resolve().parents[1]


def main():
    cfg=json.loads((ROOT/'experiments/kamri_source_specificity_v26.json').read_text())
    pre=json.loads((ROOT/'data/v26/preflight.json').read_text())
    for field in ['input_hashes','code_hashes']:
        for p,h in pre[field].items():assert digest((ROOT/p).read_bytes())==h,p
    out=ROOT/'data/v26/frozen.json';assert not out.exists()
    appendix_raw=Path(cfg['appendix_original']).read_bytes();assert digest(appendix_raw)==cfg['appendix_sha256']
    appendix=json.loads(appendix_raw)
    assert [r['id'] for r in appendix['pairs']]==['W1','W2','W3','W4','W5','R1','R2','R3','R4']
    assert [r['id'] for r in appendix['unmatched_english_blocks']]==['R5','R6','R7','R8']
    texts={}
    for key,files in appendix['text_sha256'].items():
        texts[key]={}
        for name,h in files.items():
            raw=(ROOT/'data/v25/packets'/key/name).read_bytes();assert digest(raw)==h
            texts[key][name]=raw.decode('utf-8')
    for r in appendix['pairs']:
        for key,name in [('fl_span','fl_post.txt'),('source_span','publisher_window.txt')]:
            s=r[key];text=texts[r['packet']][name]
            assert type(s['start']) is int and type(s['end']) is int and 0<=s['start']<s['end']<=len(text)
            assert text[s['start']:s['end']]==s['text'],r['id']
    unmatched=[]
    for r in appendix['unmatched_english_blocks']:
        s=r['fl_span'];text=texts[r['packet']]['fl_post.txt'];source=texts[r['packet']]['publisher_window.txt']
        assert 0<=s['start']<s['end']<=len(text) and text[s['start']:s['end']]==s['text']
        found=s['text'] in source;assert found==r['exact_block_found_in_source_window'] is False
        unmatched.append({'id':r['id'],'fl_span_valid':True,'exact_block_found_in_fixed_source_window':found,
                          'claim_scope':'verbatim-string absence only; no semantic coverage or legal assertion checked'})
    copy=ROOT/'data/v26/evidence_spans.json';assert not copy.exists();copy.write_bytes(appendix_raw)
    documents=[]
    for n in cfg['documents']:
        if n['format']=='packet_text':text=(ROOT/n['path']).read_text()
        else:text=json.loads((ROOT/n['path']).read_text())['text']
        documents.append(n|{'text':text,'text_sha256':digest(text.encode()),'whitespace_words':len(re.findall(r'\S+',text))})
    allwindows={key:[w for d in documents for w in windows(d,width)] for key,width in cfg['window_widths'].items()}
    controls=[]
    for q in cfg['queries']:
        if not q['primary']:continue
        source=next(d['text'] for d in documents if d['id']==q['document_id']);width=cfg['window_widths'][q['packet']]
        views=[('ordered_frame',frame(q['anchors'],width)),('reversed_frame',frame(q['anchors'],width,True)),
               ('anchor_masked',masked(source,q['anchors']))]
        if q['id']=='R_spellings':views.append(('spelling_corrected',corrected_spellings(source)))
        for kind,text in views:
            controls.append({'control_id':q['id']+':'+kind,'query_id':q['id'],'kind':kind,'text':text,
                             'text_sha256':digest(text.encode()),'whitespace_words':len(text.split())})
    frozen={'prepared_at_utc':utc(),'queries':cfg['queries'],'documents':documents,'windows':allwindows,'controls':controls,
            'appendix_audit':{'pairs_verified':9,'unmatched_blocks_verified':4,'text_hashes_verified':4,
                             'unmatched_block_checks':unmatched,'independent_review_admitted':False},
            'counts':{'documents':len(documents),'source_group_labels':len({d['source_group'] for d in documents}),
                      'queries':len(cfg['queries']),'primary_queries':3,'positive_work_denominator':2,
                      'windows_per_family':{k:len(v) for k,v in allwindows.items()},'control_views':len(controls)}}
    dump_json(out,frozen)
    paths=cfg['input_hashes']|{'experiments/kamri_source_specificity_v26.json':digest((ROOT/'experiments/kamri_source_specificity_v26.json').read_bytes()),
          'data/v26/preflight.json':digest((ROOT/'data/v26/preflight.json').read_bytes()),
          'data/v26/evidence_spans.json':digest(copy.read_bytes()),'data/v26/frozen.json':digest(out.read_bytes())}
    benchmark={'experiment_id':cfg['experiment_id'],'frozen_at_utc':utc(),'frozen_inputs':'data/v26/frozen.json',
               'input_hashes':paths,'counts':frozen['counts']}
    bp=ROOT/'benchmarks/kamri_source_specificity_v26.json';assert not bp.exists();dump_json(bp,benchmark)
    print(json.dumps({'appendix_audit':frozen['appendix_audit'],'counts':frozen['counts']},indent=2))


if __name__=='__main__':main()
