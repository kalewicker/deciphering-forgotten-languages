"""Literal-token residual reuse; no unknown-language meanings are inferred."""
from collections import defaultdict
from .source_specificity_v26 import tokens,aggregate,decide


def context(text,spans,flank=40):
    ts=tokens(text);a=min(s['start'] for s in spans);b=max(s['end'] for s in spans)
    hits=[i for i,t in enumerate(ts) if t['end']>a and t['start']<b]
    assert hits
    first=max(0,min(hits)-flank);stop=min(len(ts),max(hits)+1+flank)
    left,right=ts[first]['start'],ts[stop-1]['end']
    return {'text':text[left:right],'fl_char_start':left,'fl_char_end':right,
            'fl_token_start':first,'fl_token_end':stop,'token_count':stop-first,
            'reported_cluster_start':a,'reported_cluster_end':b}


def windows(document,width=160,stride=80):
    ts=tokens(document['text']);assert ts
    last=max(0,len(ts)-width);starts=list(range(0,last+1,stride))
    if last not in starts:starts.append(last)
    result=[]
    for start in starts:
        stop=min(len(ts),start+width);a,b=ts[start]['start'],ts[stop-1]['end']
        result.append({'window_id':f'{document["id"]}:{start:06d}','document_id':document['id'],
                       'source_group':document['source_group'],'token_start':start,'token_end':stop,
                       'char_start':a,'char_end':b,'token_count':stop-start,'text':document['text'][a:b]})
    return result


def seed_index(ts,blocked):
    result=defaultdict(list)
    for i in range(len(ts)-3):
        gram=tuple(t['form'] for t in ts[i:i+4])
        if (not any(w in blocked for w in gram) and len(set(gram))>=3
                and sum(sum(c.isalpha() for c in w)>=4 for w in gram)>=2):
            result[gram].append(i)
    return result


def score(query,source,blocked):
    qt,st=tokens(query),tokens(source);qi,si=seed_index(qt,blocked),seed_index(st,blocked)
    common=sorted(set(qi)&set(si));runs=set()
    for gram in common:
        for q in qi[gram]:
            for s in si[gram]:
                a,c=q,s;b,d=q+4,s+4
                while a and c and qt[a-1]['form']==st[c-1]['form'] and qt[a-1]['form'] not in blocked:
                    a-=1;c-=1
                while b<len(qt) and d<len(st) and qt[b]['form']==st[d]['form'] and qt[b]['form'] not in blocked:
                    b+=1;d+=1
                runs.add((a,b,c,d))
    matches=[]
    for a,b,c,d in sorted(runs,key=lambda x:(-(x[1]-x[0]),x[0],x[2],x[1],x[3])):
        qa,qb,sa,sb=qt[a]['start'],qt[b-1]['end'],st[c]['start'],st[d-1]['end']
        matches.append({'token_count':b-a,'query_span':{'start':qa,'end':qb,'text':query[qa:qb]},
                        'source_span':{'start':sa,'end':sb,'text':source[sa:sb]}})
    longest=max((m['token_count'] for m in matches),default=0)
    return {'score':[longest,len(common)],'qualifies':longest>=8,'matches':matches}


def evaluate(frozen):
    ledgers=[];controls=[];decisions=[];blocked=set(frozen['blocked_tokens'])
    byid={d['id']:d for d in frozen['documents']}
    for q in frozen['queries']:
        rows=[{k:w[k] for k in ['window_id','document_id','source_group']}|score(q['text'],w['text'],blocked) for w in frozen['windows']]
        docs=aggregate(rows)
        ledgers.append({'query_id':q['id'],'window_scores':rows,'document_rankings':docs})
        absent=[d for d in docs if byid[d['document_id']]['parent_work']!=q['packet']]
        for c in frozen['controls']:
            if c['query_id']==q['id']:
                controls.append({'control_id':c['control_id'],'query_id':q['id'],'kind':c['kind'],**score(q['text'],c['text'],blocked)})
        selected=[c for c in controls if c['query_id']==q['id']]
        natural=decide(docs);removed=decide(absent)
        decisions.append({'query_id':q['id'],'expected_page_id':q['expected_page_id'],'natural':natural,
                          'source_work_absent':removed,'nominated_page_retrieved':natural['nominated']==q['expected_page_id'],
                          'positive_copy_qualifies':next(c['qualifies'] for c in selected if c['kind']=='query_copy'),
                          'anchor_frame_qualifies':next(c['qualifies'] for c in selected if c['kind']=='anchor_frame')})
    requirements={'all_three_expected_pages_uniquely_qualify':all(d['nominated_page_retrieved'] for d in decisions),
                  'zero_source_work_absent_nominations':not any(d['source_work_absent']['nominated'] for d in decisions),
                  'zero_anchor_frame_qualifications':not any(d['anchor_frame_qualifies'] for d in decisions),
                  'all_three_positive_context_copies_qualify':all(d['positive_copy_qualifies'] for d in decisions)}
    return {'query_ledgers':ledgers,'control_scores':controls,'decisions':decisions,
            'gate':{'requirements':requirements,'passed':all(requirements.values())}}
