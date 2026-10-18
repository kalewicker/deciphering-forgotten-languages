"""Independent offline tokenizer/substring/subsequence/candidate/control replay."""
from pathlib import Path
from itertools import groupby,combinations
import hashlib
import json
import re
import unicodedata
from datetime import datetime,timezone
from verify_correspondence_v6 import check_hashes

ROOT=Path(__file__).resolve().parents[1]


def sha(raw):return hashlib.sha256(raw).hexdigest()
def read(path):return json.loads((ROOT/path).read_text())


def lex(text):
    items=[]
    for word,part in groupby(enumerate(text),lambda p:p[1].isalnum() or unicodedata.category(p[1])[0]=='M'):
        run=list(part)
        if word and any(c.isalnum() for _,c in run):
            a,b=run[0][0],run[-1][0]+1
            items.append((unicodedata.normalize('NFC',text[a:b]).casefold(),a,b))
    return items


def reference_score(text,anchors):
    source=lex(text);found=[]
    for anchor in anchors:
        target=[x[0] for x in lex(anchor)];matches=[]
        assert target
        for start in range(len(source)-len(target)+1):
            if all(source[start+j][0]==t for j,t in enumerate(target)):
                a,b=source[start][1],source[start+len(target)-1][2]
                matches.append({'start':a,'end':b,'text':text[a:b]})
        found.append(matches)
    def possible(indices,last=0):
        if not indices:return True
        return any(possible(indices[1:],m['end']) for m in found[indices[0]] if m['start']>=last)
    order=next(size for size in range(len(anchors),-1,-1) if any(possible(indices) for indices in combinations(range(len(anchors)),size)))
    count=sum(len(m)>0 for m in found)
    return {'score':[count,order],'qualifies':count==order==len(anchors),'occurrences':found}


def reference_windows(document,width):
    words=[(m.start(),m.end()) for m in re.finditer(r'\S+',document['text'])]
    size=len(words);assert size
    endstart=max(0,size-width);starts=set(range(0,endstart+1,max(1,width//2)))|{endstart}
    result=[]
    for start in sorted(starts):
        stop=min(size,start+width);a,b=words[start][0],words[stop-1][1]
        result.append({'window_id':f'{document["id"]}:{start:06d}','document_id':document['id'],
                       'source_group':document['source_group'],'word_start':start,'word_end':stop,
                       'char_start':a,'char_end':b,'word_count':stop-start,'text':document['text'][a:b]})
    return result


def reference_aggregate(rows):
    result=[]
    for key in sorted({r['document_id'] for r in rows}):
        subset=[r for r in rows if r['document_id']==key];maximum=max(r['score'] for r in subset)
        best=[r for r in subset if r['score']==maximum]
        result.append({'document_id':key,'source_group':subset[0]['source_group'],'score':maximum,
                       'best_window_ids':[r['window_id'] for r in best],'qualifies':best[0]['qualifies']})
    return sorted(result,key=lambda r:(-r['score'][0],-r['score'][1],r['document_id']))


def reference_decision(documents):
    if not documents:return {'nominated':None,'top_document_ids':[],'top_score':None,'reason':'empty_panel'}
    maximum=max(r['score'] for r in documents);winners=[r for r in documents if r['score']==maximum]
    names=sorted(r['document_id'] for r in winners);full=any(r['qualifies'] for r in winners)
    selected=names[0] if len(names)==1 and full else None
    return {'nominated':selected,'top_document_ids':names,'top_score':maximum,
            'reason':'unique_full_coverage' if selected else 'top_tie' if full else 'incomplete_anchor_coverage'}


def replace_tokens(text,replacements):
    result=[];last=0
    for a,b,value in sorted(replacements):
        result.extend([text[last:a],value]);last=b
    return ''.join(result)+text[last:]


def reference_control(text,query,width,kind):
    anchors=query['anchors']
    if kind in ['ordered_frame','reversed_frame']:
        phrases=anchors if kind=='ordered_frame' else list(reversed(anchors))
        count=sum(len(p.split()) for p in phrases);padding=(width-count)//(len(phrases)+1)
        words=[]
        for phrase in phrases:words+=['xqframe']*padding+phrase.split()
        return ' '.join(words+['xqframe']*(width-len(words)))
    if kind=='anchor_masked':
        covered=[m for group in reference_score(text,anchors)['occurrences'] for m in group]
        repl=[(a,b,'xqmasked') for _,a,b in lex(text) if any(m['start']<=a and b<=m['end'] for m in covered)]
        return replace_tokens(text,repl)
    assert kind=='spelling_corrected' and query['id']=='R_spellings'
    mapping={'possibile':'possible','possibilites':'possibilities'}
    return replace_tokens(text,[(a,b,mapping[t]) for t,a,b in lex(text) if t in mapping])


def reference_evaluate(frozen):
    queries=[];primaries=[];controls=[]
    for q in frozen['queries']:
        scores=[{k:w[k] for k in ['window_id','document_id','source_group']}|reference_score(w['text'],q['anchors']) for w in frozen['windows'][q['packet']]]
        docs=reference_aggregate(scores)
        queries.append({'query_id':q['id'],'primary':q['primary'],'nominated_document_id':q['document_id'],
                        'window_scores':scores,'document_rankings':docs,'natural_decision':reference_decision(docs)})
        if not q['primary']:continue
        for c in frozen['controls']:
            if c['query_id']==q['id']:
                controls.append({'control_id':c['control_id'],'query_id':q['id'],'kind':c['kind'],**reference_score(c['text'],q['anchors'])})
        lure=next(c for c in controls if c['query_id']==q['id'] and c['kind']=='ordered_frame')
        lure_doc={'document_id':lure['control_id'],'source_group':'synthetic_lure','score':lure['score'],
                  'qualifies':lure['qualifies'],'best_window_ids':[lure['control_id']]}
        other=[d for d in docs if d['document_id']!=q['document_id']]
        decisions={'natural':reference_decision(docs),'source_absent':reference_decision(other),
                   'source_present_plus_frame':reference_decision(docs+[lure_doc]),
                   'source_absent_plus_frame':reference_decision(other+[lure_doc])}
        primaries.append({'query_id':q['id'],'packet':q['packet'],'nominated_document_id':q['document_id'],'decisions':decisions,
                          'natural_localizes_nominee':decisions['natural']['nominated']==q['document_id'],
                          'source_absent_natural_nomination':decisions['source_absent']['nominated'] is not None,
                          'source_absent_frame_false_nomination':decisions['source_absent_plus_frame']['nominated']==lure['control_id']})
    requirements={'all_three_natural_localizations':sum(r['natural_localizes_nominee'] for r in primaries)==3,
                  'zero_source_absent_natural_nominations':sum(r['source_absent_natural_nomination'] for r in primaries)==0,
                  'zero_source_absent_frame_false_nominations':sum(r['source_absent_frame_false_nomination'] for r in primaries)==0}
    return {'query_ledgers':queries,'primary_decisions':primaries,'control_scores':controls,
            'gate':{'requirements':requirements,'passed':all(requirements.values())}}


def main():
    cfg=read('experiments/kamri_source_specificity_v26.json');pre=read('data/v26/preflight.json')
    benchmark=read('benchmarks/kamri_source_specificity_v26.json');frozen=read('data/v26/frozen.json')
    out=ROOT/'runs/000026_kamri_source_specificity';m=check_hashes(out);report=read('runs/000026_kamri_source_specificity/report.json')
    for hashes in [cfg['input_hashes'],pre['input_hashes'],pre['code_hashes'],benchmark['input_hashes']]:
        for p,h in hashes.items():assert sha((ROOT/p).read_bytes())==h,p
    assert cfg['registered_at_utc']<pre['sealed_at_utc']<frozen['prepared_at_utc']<=benchmark['frozen_at_utc']<m['started_at_utc']<m['finished_at_utc']
    assert frozen['queries']==cfg['queries'] and m['code_hashes']==pre['code_hashes']
    assert [q['id'] for q in cfg['queries']]==['W_names','W_saturn','R_spellings','W_latin','R_common','R_vocabulary']
    assert [q['primary'] for q in cfg['queries']]==[True,True,True,False,False,False]
    assert cfg['window_widths']=={'western_esoterism':1930,'risk_math':1211}
    assert cfg['expected_window_counts']=={'western_esoterism':61,'risk_math':98}
    assert len(frozen['documents'])==cfg['document_denominator']==11
    assert len({d['source_group'] for d in frozen['documents']})==cfg['source_group_label_denominator']==10
    assert len(frozen['controls'])==cfg['control_view_denominator']==10
    appendix=read('data/v26/evidence_spans.json');assert sha((ROOT/'data/v26/evidence_spans.json').read_bytes())==cfg['appendix_sha256']
    packet_text={}
    for packet,files in appendix['text_sha256'].items():
        packet_text[packet]={}
        for name,h in files.items():
            raw=(ROOT/'data/v25/packets'/packet/name).read_bytes();assert sha(raw)==h;packet_text[packet][name]=raw.decode('utf-8')
    assert [r['id'] for r in appendix['pairs']]==['W1','W2','W3','W4','W5','R1','R2','R3','R4']
    for r in appendix['pairs']:
        for field,name in [('fl_span','fl_post.txt'),('source_span','publisher_window.txt')]:
            s=r[field];t=packet_text[r['packet']][name]
            assert type(s['start']) is int and type(s['end']) is int and 0<=s['start']<s['end']<=len(t)
            assert t[s['start']:s['end']]==s['text']
    checks=[]
    assert [r['id'] for r in appendix['unmatched_english_blocks']]==['R5','R6','R7','R8']
    for r in appendix['unmatched_english_blocks']:
        s=r['fl_span'];t=packet_text[r['packet']]['fl_post.txt'];source=packet_text[r['packet']]['publisher_window.txt']
        assert t[s['start']:s['end']]==s['text'] and (s['text'] in source)==r['exact_block_found_in_source_window'] is False
        checks.append({'id':r['id'],'fl_span_valid':True,'exact_block_found_in_fixed_source_window':False,
                       'claim_scope':'verbatim-string absence only; no semantic coverage or legal assertion checked'})
    assert frozen['appendix_audit']=={'pairs_verified':9,'unmatched_blocks_verified':4,'text_hashes_verified':4,
                                     'unmatched_block_checks':checks,'independent_review_admitted':False}
    for n,d in zip(cfg['documents'],frozen['documents'],strict=True):
        raw=(ROOT/n['path']).read_text();text=raw if n['format']=='packet_text' else json.loads(raw)['text']
        assert d==n|{'text':text,'text_sha256':sha(text.encode()),'whitespace_words':len(re.findall(r'\S+',text))}
    for packet,width in cfg['window_widths'].items():
        expected=[w for d in frozen['documents'] for w in reference_windows(d,width)]
        assert frozen['windows'][packet]==expected and len(expected)==cfg['expected_window_counts'][packet]
    expected_controls=[]
    for q in cfg['queries'][:3]:
        source=next(d['text'] for d in frozen['documents'] if d['id']==q['document_id'])
        kinds=['ordered_frame','reversed_frame','anchor_masked']+(['spelling_corrected'] if q['id']=='R_spellings' else [])
        for kind in kinds:
            text=reference_control(source,q,cfg['window_widths'][q['packet']],kind)
            expected_controls.append({'control_id':q['id']+':'+kind,'query_id':q['id'],'kind':kind,'text':text,
                                      'text_sha256':sha(text.encode()),'whitespace_words':len(text.split())})
    assert frozen['controls']==expected_controls
    assert frozen['counts']=={'documents':11,'source_group_labels':10,'queries':6,'primary_queries':3,'positive_work_denominator':2,
                              'windows_per_family':{'western_esoterism':61,'risk_math':98},'control_views':10}
    replay=reference_evaluate(frozen)
    for name,data in replay.items():assert read(f'runs/000026_kamri_source_specificity/{name}.json')==data,name
    assert report['primary_decisions']==replay['primary_decisions'] and report['gate']==replay['gate']
    assert report['counts']==frozen['counts'] and report['appendix_audit']==frozen['appendix_audit']
    assert report['natural_localizations']==sum(r['natural_localizes_nominee'] for r in replay['primary_decisions'])
    assert report['source_absent_natural_nominations']==sum(r['source_absent_natural_nomination'] for r in replay['primary_decisions'])
    assert report['source_absent_frame_false_nominations']==sum(r['source_absent_frame_false_nomination'] for r in replay['primary_decisions'])
    assert report['natural_window_scores']==sum(len(q['window_scores']) for q in replay['query_ledgers'])==477
    for k in ['source_identity_claims_admitted','semantic_labels_admitted','independent_reviews_admitted','untouched_test_units_admitted','new_network_requests']:
        assert report[k]==0,k
    assert report['semantic_evaluation_metrics'] is report['primary_gap_lead'] is None
    assert report['target_rescored'] is report['translation_model_executed'] is report['new_lexical_induction_executed'] is False
    assert report['model_executed'] is True
    assert m['outcome']==('restricted_gate_passed' if replay['gate']['passed'] else 'source_specificity_gate_failed')
    prior=[]
    for p in sorted((ROOT/'runs').glob('*/manifest.json')):
        if p.parent!=out:check_hashes(p.parent);prior.append(p.parent.name)
    assert len(prior)==25
    for p in (ROOT/'reports').glob('*_deliverable_seal.json'):
        for name,h in json.loads(p.read_text()).get('deliverable_hashes',{}).items():assert sha((ROOT/name).read_bytes())==h,name
    intake=ROOT/'data/review_intake/2026-10-15_automated_findings_9f36fea04dbf'
    for name,h in json.loads((intake/'seal.json').read_text())['files'].items():assert sha((intake/name).read_bytes())==h
    receipt={'state':'verified','run_manifest_sha256':sha((out/'manifest.json').read_bytes()),
             'primary_queries_verified':3,'natural_window_scores_verified':477,'control_views_verified':10,
             'primary_decisions_verified':12,'appendix_paired_spans_verified':9,'appendix_unmatched_blocks_verified':4,
             'gate':replay['gate'],'prior_runs_preserved':prior,'semantic_labels_admitted':0,'independent_reviews_admitted':0}
    target=ROOT/'reports/000026_verification.json'
    if target.exists():
        saved=json.loads(target.read_text());assert {k:v for k,v in saved.items() if k!='verified_at_utc'}==receipt
    else:
        receipt['verified_at_utc']=datetime.now(timezone.utc).isoformat();target.write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt,indent=2))


if __name__=='__main__':main()
