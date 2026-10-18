"""Independent diagonal-run, context/window and PDF-source replay."""
from pathlib import Path
from itertools import groupby
from datetime import datetime,timezone
import hashlib,json,re,subprocess,sys,unicodedata

ROOT=Path(__file__).resolve().parents[1]


def sha(raw):return hashlib.sha256(raw).hexdigest()
def read(p):return json.loads((ROOT/p).read_text())


def lex(text):
    result=[]
    for flag,items in groupby(enumerate(text),lambda x:x[1].isalnum() or unicodedata.category(x[1])[0]=='M'):
        run=list(items)
        if flag and any(c.isalnum() for _,c in run):
            a,b=run[0][0],run[-1][0]+1;result.append((unicodedata.normalize('NFC',text[a:b]).casefold(),a,b))
    return result


def reference_score(query,source,blocked):
    q,s=lex(query),lex(source);runs=[];shared=set()
    def save(a,b,c,d):
        if b-a<4:return
        seeds=[]
        for i in range(a,b-3):
            gram=tuple(t[0] for t in q[i:i+4])
            if len(set(gram))>=3 and sum(sum(ch.isalpha() for ch in w)>=4 for w in gram)>=2:
                seeds.append(gram)
        if not seeds:return
        shared.update(seeds);qa,qb,sa,sb=q[a][1],q[b-1][2],s[c][1],s[d-1][2]
        runs.append((a,b,c,d,{'token_count':b-a,'query_span':{'start':qa,'end':qb,'text':query[qa:qb]},
                             'source_span':{'start':sa,'end':sb,'text':source[sa:sb]}}))
    # Enumerate equal-token runs along each alignment diagonal. This does not
    # seed/extend from indexed four-grams as the execution implementation does.
    for delta in range(1-len(q),len(s)):
        qi=max(0,-delta);si=qi+delta;startq=startsource=None
        while qi<len(q) and si<len(s):
            same=q[qi][0]==s[si][0] and q[qi][0] not in blocked
            if same and startq is None:startq,startsource=qi,si
            if not same and startq is not None:
                save(startq,qi,startsource,si);startq=startsource=None
            qi+=1;si+=1
        if startq is not None:save(startq,qi,startsource,si)
    runs.sort(key=lambda x:(-(x[1]-x[0]),x[0],x[2],x[1],x[3]))
    matches=[r[4] for r in runs];longest=max([m['token_count'] for m in matches],default=0)
    return {'score':[longest,len(shared)],'qualifies':longest>=8,'matches':matches}


def reference_context(text,spans):
    ts=lex(text);left=min(s['start'] for s in spans);right=max(s['end'] for s in spans)
    intersect=[i for i,(_,a,b) in enumerate(ts) if a<right and b>left]
    a=max(0,intersect[0]-40);b=min(len(ts),intersect[-1]+41);start,end=ts[a][1],ts[b-1][2]
    return {'text':text[start:end],'fl_char_start':start,'fl_char_end':end,'fl_token_start':a,'fl_token_end':b,
            'token_count':b-a,'reported_cluster_start':left,'reported_cluster_end':right}


def reference_windows(document):
    ts=lex(document['text']);assert ts
    final=max(0,len(ts)-160);starts=sorted(set(range(0,final+1,80))|{final});rows=[]
    for start in starts:
        stop=min(len(ts),start+160);a,b=ts[start][1],ts[stop-1][2]
        rows.append({'window_id':f'{document["id"]}:{start:06d}','document_id':document['id'],'source_group':document['source_group'],
                     'token_start':start,'token_end':stop,'char_start':a,'char_end':b,'token_count':stop-start,'text':document['text'][a:b]})
    return rows


def reference_evaluate(frozen):
    from verify_source_specificity_v26 import reference_aggregate,reference_decision
    blocked=set(frozen['blocked_tokens']);ledgers=[];controls=[];decisions=[]
    byid={d['id']:d for d in frozen['documents']}
    for q in frozen['queries']:
        scored=[{k:w[k] for k in ['window_id','document_id','source_group']}|reference_score(q['text'],w['text'],blocked) for w in frozen['windows']]
        docs=reference_aggregate(scored);ledgers.append({'query_id':q['id'],'window_scores':scored,'document_rankings':docs})
        for c in frozen['controls']:
            if c['query_id']==q['id']:controls.append({'control_id':c['control_id'],'query_id':q['id'],'kind':c['kind'],**reference_score(q['text'],c['text'],blocked)})
        these=[c for c in controls if c['query_id']==q['id']]
        natural=reference_decision(docs);absent=reference_decision([d for d in docs if byid[d['document_id']]['parent_work']!=q['packet']])
        decisions.append({'query_id':q['id'],'expected_page_id':q['expected_page_id'],'natural':natural,'source_work_absent':absent,
                          'nominated_page_retrieved':natural['nominated']==q['expected_page_id'],
                          'positive_copy_qualifies':next(c['qualifies'] for c in these if c['kind']=='query_copy'),
                          'anchor_frame_qualifies':next(c['qualifies'] for c in these if c['kind']=='anchor_frame')})
    criteria={'all_three_expected_pages_uniquely_qualify':all(r['nominated_page_retrieved'] for r in decisions),
              'zero_source_work_absent_nominations':not any(r['source_work_absent']['nominated'] for r in decisions),
              'zero_anchor_frame_qualifications':not any(r['anchor_frame_qualifies'] for r in decisions),
              'all_three_positive_context_copies_qualify':all(r['positive_copy_qualifies'] for r in decisions)}
    return {'query_ledgers':ledgers,'control_scores':controls,'decisions':decisions,'gate':{'requirements':criteria,'passed':all(criteria.values())}}


def pdf_replay():
    import pypdf,pypdfium2
    from PIL import Image
    cfg=read('experiments/kamri_residual_context_v27.json');pages=read('data/v27/page_views.json')
    assert pages['state']=='completed' and len(pages['pages'])==8
    assert pypdf.__version__==pages['pypdf_version']==cfg['pypdf_version']
    assert str(pypdfium2.PDFIUM_INFO)==pages['pdfium_version']==cfg['pdfium_version']
    expected=[]
    for work in cfg['pdf_sources']:
        path=ROOT/work['path'];reader=pypdf.PdfReader(path);pdf=pypdfium2.PdfDocument(str(path))
        assert len(reader.pages)==work['page_count']
        for number in work['pages']:
            key=f'{work["id"]}:pdf:{number:03d}';expected.append(key)
            r=next(r for r in pages['pages'] if r['id']==key);text=reader.pages[number-1].extract_text()
            assert r['parent_work']==r['source_group']==work['id'] and r['pdf_path']==work['path'] and r['pdf_page_one_based']==number
            assert r['text']==text and r['text_sha256']==sha(text.encode()) and r['pdf_sha256']==sha(path.read_bytes())
            page=pdf[number-1];bmp=page.render(scale=1.5);rgb=bmp.to_pil().convert('RGB');stored=Image.open(ROOT/r['image']).convert('RGB')
            assert r['pixel_size']==list(rgb.size) and stored.size==rgb.size and stored.tobytes()==rgb.tobytes()
            assert r['pixels_sha256']==sha(rgb.tobytes()) and r['image_sha256']==sha((ROOT/r['image']).read_bytes())
            assert r['dimensions']==list(page.get_size());bmp.close();page.close()
        pdf.close()
    assert [r['id'] for r in pages['pages']]==expected
    print(json.dumps({'pages_replayed':8,'raw_text_and_pixels_verified':True}))


def main():
    from verify_correspondence_v6 import check_hashes
    cfg=read('experiments/kamri_residual_context_v27.json');pre=read('data/v27/preflight.json')
    bench=read('benchmarks/kamri_residual_context_v27.json');frozen=read('data/v27/frozen.json')
    out=ROOT/'runs/000027_kamri_residual_context';m=check_hashes(out);report=read('runs/000027_kamri_residual_context/report.json')
    for hashes in [cfg['input_hashes'],pre['input_hashes'],pre['code_hashes'],bench['input_hashes']]:
        for p,h in hashes.items():assert sha((ROOT/p).read_bytes())==h,p
    assert cfg['registered_at_utc']<pre['sealed_at_utc']<frozen['prepared_at_utc']<=bench['frozen_at_utc']<m['started_at_utc']<m['finished_at_utc']
    assert cfg['flank_tokens']==40 and cfg['window_tokens']==160 and cfg['window_stride']==80
    assert (cfg['seed_tokens'],cfg['seed_min_distinct'],cfg['seed_min_long_words'],cfg['long_word_letters'],cfg['qualification_run_tokens'])==(4,3,2,4,8)
    assert cfg['pdf_sources'][0]['pages']==[90,91,92,93,94] and cfg['pdf_sources'][1]['pages']==[1,2,3]
    assert len(cfg['queries'])==3 and len(cfg['other_documents'])==9
    prior=read('experiments/kamri_source_specificity_v26.json');appendix=read('data/v26/evidence_spans.json')
    blocked=sorted({t[0] for q in prior['queries'] for a in q['anchors'] for t in lex(a)})
    assert frozen['blocked_tokens']==blocked and report['blocked_token_count']==len(blocked)
    pages=read('data/v27/page_views.json');expected=[{k:r[k] for k in ['id','parent_work','source_group','text','text_sha256','pdf_path','pdf_page_one_based']}|{'kind':'raw_pdf_page'} for r in pages['pages']]
    for d in cfg['other_documents']:
        text=read(d['path'])['text'];expected.append(d|{'kind':'historical_normalized_export','parent_work':d['source_group'],'text':text,'text_sha256':sha(text.encode())})
    assert frozen['documents']==expected and len(expected)==17
    assert frozen['windows']==[w for d in expected for w in reference_windows(d)]
    expected_queries=[];expected_controls=[];pairs={r['id']:r for r in appendix['pairs']}
    for q in cfg['queries']:
        raw=(ROOT/f'data/v25/packets/{q["packet"]}/fl_post.txt').read_bytes()
        assert sha(raw)==appendix['text_sha256'][q['packet']]['fl_post.txt']
        data=q|reference_context(raw.decode(),[pairs[key]['fl_span'] for key in q['evidence_ids']]);data['text_sha256']=sha(data['text'].encode());expected_queries.append(data)
        anchors=next(p['anchors'] for p in prior['queries'] if p['id']==q['id'])
        gap=(160-sum(len(a.split()) for a in anchors))//(len(anchors)+1);words=[]
        for anchor in anchors:words+=['xqframe']*gap+anchor.split()
        ordered=' '.join(words+['xqframe']*(160-len(words)))
        views=[('query_copy',data['text']),('anchor_frame',ordered),('query_reversed',' '.join(t[0] for t in reversed(lex(data['text'])))),
               ('legacy_publisher_window',(ROOT/f'data/v25/packets/{q["packet"]}/publisher_window.txt').read_text())]
        for kind,text in views:expected_controls.append({'control_id':q['id']+':'+kind,'query_id':q['id'],'kind':kind,'text':text,'text_sha256':sha(text.encode())})
    assert frozen['queries']==expected_queries and frozen['controls']==expected_controls and len(expected_controls)==12
    count={'documents':17,'raw_pdf_pages':8,'historical_exports':9,'queries':3,'positive_works':2,
           'same_work_alternative_pages_per_query':[4,4,2],'control_views':12,'windows':len(frozen['windows']),'natural_window_scores':3*len(frozen['windows'])}
    assert frozen['counts']==bench['counts']==report['counts']==count
    replay=reference_evaluate(frozen)
    for key,data in replay.items():assert read(f'runs/000027_kamri_residual_context/{key}.json')==data,key
    assert report['gate']==replay['gate']
    summaries=[]
    for q,l,d in zip(frozen['queries'],replay['query_ledgers'],replay['decisions'],strict=True):
        nominated=next(r for r in l['document_rankings'] if r['document_id']==q['expected_page_id'])
        summaries.append({'query_id':q['id'],'query_context_tokens':q['token_count'],'best_natural_score':l['document_rankings'][0]['score'],
                          'expected_page_score':nominated['score'],'natural_qualifying_documents':sum(r['qualifies'] for r in l['document_rankings']),
                          'source_work_absent_nomination':d['source_work_absent']['nominated'],'nominated_page_retrieved':d['nominated_page_retrieved']})
    assert report['query_summary']==summaries
    for key,field in [('expected_pages_retrieved','nominated_page_retrieved'),('positive_context_copies_qualified','positive_copy_qualifies'),('anchor_frames_qualified','anchor_frame_qualifies')]:
        assert report[key]==sum(d[field] for d in replay['decisions'])
    assert report['source_work_absent_nominations']==sum(d['source_work_absent']['nominated'] is not None for d in replay['decisions'])
    for key in ['source_identities_admitted','semantic_labels_admitted','independent_reviews_admitted','untouched_test_units_admitted','new_network_requests']:
        assert report[key]==0,key
    assert report['semantic_evaluation_metrics'] is report['primary_gap_lead'] is None
    assert report['target_rescored'] is report['translation_model_executed'] is report['new_lexical_induction_executed'] is False
    assert report['model_executed'] is True and m['code_hashes']==pre['code_hashes']
    assert m['outcome']==('residual_context_gate_passed' if replay['gate']['passed'] else 'residual_context_gate_failed')
    visual=read('data/v27/visual_review.json');assert visual['pages_reviewed']==8 and visual['independent_semantic_review'] is False
    assert visual['image_hashes']=={r['image']:r['image_sha256'] for r in pages['pages']}
    proc=subprocess.run([cfg['pdf_runtime'],str(Path(__file__).resolve()),'--pdf'],check=True,capture_output=True,text=True)
    pdf_result=json.loads(proc.stdout)
    preserved=[]
    for path in sorted((ROOT/'runs').glob('*/manifest.json')):
        if path.parent!=out:check_hashes(path.parent);preserved.append(path.parent.name)
    assert len(preserved)==26
    for path in (ROOT/'reports').glob('*_deliverable_seal.json'):
        for p,h in json.loads(path.read_text()).get('deliverable_hashes',{}).items():assert sha((ROOT/p).read_bytes())==h,p
    receipt={'state':'verified','run_manifest_sha256':sha((out/'manifest.json').read_bytes()),'natural_window_scores_verified':count['natural_window_scores'],
             'queries_verified':3,'controls_verified':12,'gate':replay['gate'],'pdf_replay':pdf_result,'prior_runs_preserved':preserved,
             'semantic_labels_admitted':0,'independent_reviews_admitted':0}
    path=ROOT/'reports/000027_verification.json'
    if path.exists():
        old=json.loads(path.read_text());assert {k:v for k,v in old.items() if k!='verified_at_utc'}==receipt
    else:
        receipt['verified_at_utc']=datetime.now(timezone.utc).isoformat();path.write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt,indent=2))


if __name__=='__main__':
    if sys.argv[1:]==['--pdf']:pdf_replay()
    else:main()
