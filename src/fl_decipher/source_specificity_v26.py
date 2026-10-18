"""Frozen ordered-anchor retrieval and explicit synthetic failure controls."""
from itertools import combinations
import re
import unicodedata


def tokens(text):
    result=[];start=None
    for i,c in enumerate(text+' '):
        word=c.isalnum() or unicodedata.category(c).startswith('M')
        if word and start is None:
            start=i
        if not word and start is not None:
            raw=text[start:i]
            if any(x.isalnum() for x in raw):
                result.append({'start':start,'end':i,'form':unicodedata.normalize('NFC',raw).casefold()})
            start=None
    return result


def occurrences(text,anchors):
    ts=tokens(text);forms=[t['form'] for t in ts];result=[]
    for anchor in anchors:
        target=[t['form'] for t in tokens(anchor)]
        if not target:
            raise ValueError('empty anchor')
        rows=[]
        for i in range(len(ts)-len(target)+1):
            if forms[i:i+len(target)] == target:
                a,b=ts[i]['start'],ts[i+len(target)-1]['end']
                rows.append({'start':a,'end':b,'text':text[a:b]})
        result.append(rows)
    return result


def ordered_length(matches):
    # Best (earliest) end for each attainable chain length; descending update
    # prevents using one registered anchor label twice in the same chain.
    ends=[0]+[None]*len(matches)
    for rows in matches:
        for length in range(len(matches)-1,-1,-1):
            if ends[length] is None:
                continue
            possible=[r['end'] for r in rows if r['start'] >= ends[length]]
            if possible:
                candidate=min(possible)
                ends[length+1]=candidate if ends[length+1] is None else min(ends[length+1],candidate)
    return max(i for i,end in enumerate(ends) if end is not None)


def score(text,anchors):
    matches=occurrences(text,anchors);count=sum(bool(r) for r in matches);order=ordered_length(matches)
    return {'score':[count,order],'qualifies':count == order == len(anchors),'occurrences':matches}


def windows(document,width):
    ws=list(re.finditer(r'\S+',document['text']));size=len(ws)
    if not size:
        raise ValueError('empty source document')
    last=max(0,size-width);starts=list(range(0,last+1,max(1,width//2)))
    if last not in starts:
        starts.append(last)
    result=[]
    for start in starts:
        stop=min(start+width,size);a,b=ws[start].start(),ws[stop-1].end()
        result.append({'window_id':f'{document["id"]}:{start:06d}', 'document_id':document['id'],
                       'source_group':document['source_group'],'word_start':start,'word_end':stop,
                       'char_start':a,'char_end':b,'word_count':stop-start,'text':document['text'][a:b]})
    return result


def frame(anchors,width,reverse=False):
    ordered=list(reversed(anchors)) if reverse else anchors
    words=sum(len(a.split()) for a in ordered);padding=width-words
    if padding < 0:
        raise ValueError('frame width too small')
    gap=padding//(len(ordered)+1);parts=[]
    for a in ordered:
        parts.extend(['xqframe']*gap);parts.extend(a.split())
    parts.extend(['xqframe']*(width-len(parts)))
    return ' '.join(parts)


def masked(text,anchors):
    spans=[(r['start'],r['end']) for rows in occurrences(text,anchors) for r in rows]
    replace=[t for t in tokens(text) if any(a<=t['start'] and t['end']<=b for a,b in spans)]
    for t in reversed(replace):
        text=text[:t['start']]+'xqmasked'+text[t['end']:]
    return text


def corrected_spellings(text):
    substitutions={'possibile':'possible','possibilites':'possibilities'}
    for t in reversed(tokens(text)):
        if t['form'] in substitutions:
            text=text[:t['start']]+substitutions[t['form']]+text[t['end']:]
    return text


def aggregate(scored):
    bydoc={}
    for row in scored:
        d=bydoc.setdefault(row['document_id'],{'document_id':row['document_id'],'source_group':row['source_group'],
                                               'score':None,'best_window_ids':[],'qualifies':False})
        if d['score'] is None or row['score'] > d['score']:
            d.update(score=row['score'],best_window_ids=[row['window_id']],qualifies=row['qualifies'])
        elif row['score'] == d['score']:
            d['best_window_ids'].append(row['window_id'])
    return sorted(bydoc.values(),key=lambda r:(-r['score'][0],-r['score'][1],r['document_id']))


def decide(documents):
    if not documents:
        return {'nominated':None,'top_document_ids':[],'top_score':None,'reason':'empty_panel'}
    top=max(d['score'] for d in documents);tied=sorted(d['document_id'] for d in documents if d['score']==top)
    full=any(d['qualifies'] for d in documents if d['score']==top)
    selected=tied[0] if full and len(tied)==1 else None
    return {'nominated':selected,'top_document_ids':tied,'top_score':top,
            'reason':'unique_full_coverage' if selected else 'top_tie' if full else 'incomplete_anchor_coverage'}


def evaluate(frozen):
    ledgers=[];primaries=[];controls=[]
    for query in frozen['queries']:
        scored=[]
        for window in frozen['windows'][query['packet']]:
            scored.append({k:window[k] for k in ['window_id','document_id','source_group']}|
                          score(window['text'],query['anchors']))
        documents=aggregate(scored)
        ledger={'query_id':query['id'],'primary':query['primary'],'nominated_document_id':query['document_id'],
                'window_scores':scored,'document_rankings':documents,'natural_decision':decide(documents)}
        ledgers.append(ledger)
        if not query['primary']:
            continue
        views=[v for v in frozen['controls'] if v['query_id']==query['id']]
        for view in views:
            controls.append({'control_id':view['control_id'],'query_id':query['id'],'kind':view['kind'],
                             **score(view['text'],query['anchors'])})
        lure=next(c for c in controls if c['query_id']==query['id'] and c['kind']=='ordered_frame')
        lure_doc={'document_id':lure['control_id'],'source_group':'synthetic_lure',
                  'score':lure['score'],'qualifies':lure['qualifies'],'best_window_ids':[lure['control_id']]}
        absent=[d for d in documents if d['document_id']!=query['document_id']]
        decisions={'natural':decide(documents),'source_absent':decide(absent),
                   'source_present_plus_frame':decide(documents+[lure_doc]),
                   'source_absent_plus_frame':decide(absent+[lure_doc])}
        primaries.append({'query_id':query['id'],'packet':query['packet'],'nominated_document_id':query['document_id'],
                          'decisions':decisions,'natural_localizes_nominee':decisions['natural']['nominated']==query['document_id'],
                          'source_absent_natural_nomination':decisions['source_absent']['nominated'] is not None,
                          'source_absent_frame_false_nomination':decisions['source_absent_plus_frame']['nominated']==lure['control_id']})
    gates={'all_three_natural_localizations':sum(r['natural_localizes_nominee'] for r in primaries)==3,
           'zero_source_absent_natural_nominations':not any(r['source_absent_natural_nomination'] for r in primaries),
           'zero_source_absent_frame_false_nominations':not any(r['source_absent_frame_false_nomination'] for r in primaries)}
    return {'query_ledgers':ledgers,'primary_decisions':primaries,'control_scores':controls,
            'gate':{'requirements':gates,'passed':all(gates.values())}}
