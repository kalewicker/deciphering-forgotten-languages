"""Anchor-masked, opaque-renaming-invariant paragraph diagnostic."""
from collections import Counter
from fractions import Fraction
import hashlib
from fl_decipher.source_specificity_v26 import tokens


def view(text, blocked):
    return {'text':text,'tokens':[t|{'blocked':t['form'] in blocked} for t in tokens(text)]}


def registry(html_maps, pdf_maps, risk_pages, cfg, anchors):
    blocked=sorted({t['form'] for q in anchors for a in q['anchors'] for t in tokens(a)})
    fl=[]
    for work,mapping in html_maps.items():
        for b in mapping['blocks']:
            assert mapping['flat_text'][b['start']:b['end']]==b['text']
            fl.append({'unit_id':f"fl:{work}:{b['block_id']}",'work':work,'block_id':b['block_id'],
                       'original_start':b['start'],'original_end':b['end'],'role':'paragraph_markup_semantics_unresolved',**view(b['text'],blocked)})
    providers={p['page_id']:('runs/000028_kamri_block_audit/pdf_maps.json',p['lines']) for p in pdf_maps if p['work']=='western_esoterism'}
    providers.update({p['page_id']:('runs/000029_risk_layout_derivative/pages.json',p['lines']) for p in risk_pages})
    sources=[]
    for page_id,regions in cfg['source_regions'].items():
        parent,lines=providers[page_id];covered=[]
        for n,r in enumerate(regions):
            selected=lines[r['start_line']:r['end_line']];assert selected
            ids=list(range(r['start_line'],r['end_line']));covered.extend(ids)
            pieces=[];parts=[];offset=0
            for i,line in enumerate(selected):
                if i:
                    pieces.append({'kind':'join_newline','start':offset,'end':offset+1,'text':'\n'});parts.append('\n');offset+=1
                pieces.append({'kind':'source_line','start':offset,'end':offset+len(line['text']),'text':line['text'],
                               'parent_line_id':line['line_id'],'parent_start':line.get('start'),'parent_end':line.get('end')})
                parts.append(line['text']);offset+=len(line['text'])
            sources.append({'unit_id':page_id+f':u{n:02d}','work':page_id.split(':')[0],'page_id':page_id,
                            'role':r['role'],'candidate':r['role'] in cfg['candidate_roles'],'parent_json':parent,
                            'line_indices':ids,'pieces':pieces,**view(''.join(parts),blocked)})
        assert covered==list(range(len(lines))),page_id
    queries=[]
    for spec in cfg['queries']:
        unit=next(u for u in fl if u['work']==spec['work'] and u['block_id']==spec['block_id'])
        assert any(u['unit_id']==spec['expected_unit_id'] and u['candidate'] for u in sources)
        queries.append(unit|spec)
    return {'blocked_forms':blocked,'fl_units':fl,'source_units':sources,'queries':queries}


def control(query, kind):
    original=query['tokens'];forms=[t['form'] for t in original]
    if kind=='opaque':
        labels={f:f'opaqueword{i}' for i,f in enumerate(sorted(set(forms)))}
        forms=[labels[f] for f in forms];flags=[t['blocked'] for t in original]
    elif kind=='anchor_frame':
        forms=[f if t['blocked'] else f'uniqueunusedfiller{i}' for i,(f,t) in enumerate(zip(forms,original,strict=True))]
        flags=[t['blocked'] for t in original]
    elif kind=='reverse':
        forms.reverse();flags=[t['blocked'] for t in reversed(original)]
    else:raise ValueError(kind)
    text=' '.join(forms);ts=tokens(text);assert len(ts)==len(flags)
    return {'unit_id':query['id']+':'+kind,'work':'synthetic_'+kind,'kind':kind,'text':text,
            'tokens':[t|{'blocked':flag} for t,flag in zip(ts,flags,strict=True)]}


def null_order(unit,draw):
    indices=[i for i,t in enumerate(unit['tokens']) if not t['blocked']]
    return sorted(indices,key=lambda i:(hashlib.sha256(f"v30|{draw}|{unit['unit_id']}|{i}".encode()).digest(),i))


def shuffled(unit,order):
    indices=[i for i,t in enumerate(unit['tokens']) if not t['blocked']]
    assert sorted(order)==indices
    ts=[dict(t) for t in unit['tokens']]
    for destination,origin in zip(indices,order,strict=True):ts[destination]['form']=unit['tokens'][origin]['form']
    return unit|{'tokens':ts}


def fingerprints(unit,spans=True):
    ts=unit['tokens'];result={}
    for start in range(len(ts)-9):
        window=ts[start:start+10]
        if any(t['blocked'] for t in window):continue
        labels={};pattern=[]
        for t in window:
            if t['form'] not in labels:labels[t['form']]=len(labels)
            pattern.append(labels[t['form']])
        counts=Counter(pattern)
        if len(counts)<4 or sum(n>=2 for n in counts.values())<2:continue
        signature=tuple(pattern)
        occurrences=result.setdefault(signature,[])
        if spans:
            a,b=window[0]['start'],window[-1]['end']
            occurrences.append({'token_start':start,'token_end':start+10,'start':a,'end':b,'text':unit['text'][a:b]})
    return result


def scored(query_index,source_index,unit,with_witness=True):
    common=sorted(query_index.keys() & source_index.keys())
    row={'unit_id':unit['unit_id'],'work':unit['work'],'score':len(common),'qualifies':len(common)>=2}
    if with_witness:row['shared_fingerprints']=[{'signature':list(s),'query_occurrences':query_index[s],'source_occurrences':source_index[s]} for s in common]
    return row


def decide(rows):
    maximum=max((r['score'] for r in rows),default=0)
    tied=sorted(r['unit_id'] for r in rows if r['score']==maximum)
    nomination=tied[0] if maximum>=2 and len(tied)==1 else None
    return {'nominated':nomination,'top_score':maximum,'top_unit_ids':tied,
            'reason':'unique_qualified' if nomination else 'top_tie' if maximum>=2 else 'insufficient_shared_patterns'}


def evaluate(frozen):
    sources=[u for u in frozen['registry']['source_units'] if u['candidate']];queries=frozen['registry']['queries']
    source_indices={u['unit_id']:fingerprints(u) for u in sources};qindices={q['id']:fingerprints(q) for q in queries}
    ledgers=[];controls=[]
    for q in queries:
        qi=qindices[q['id']];rows=[scored(qi,source_indices[u['unit_id']],u) for u in sources]
        absent=[r for r in rows if r['work']!=q['work']]
        crows={}
        for c in frozen['controls']:
            if c['query_id']!=q['id']:continue
            if c['kind']=='reverse':
                ci=fingerprints(c);reverse_rows=[scored(ci,source_indices[u['unit_id']],u) for u in sources]
                controls.append({'query_id':q['id'],'kind':'reverse_query','scores':reverse_rows,'decision':decide(reverse_rows)})
            else:
                row=scored(qi,fingerprints(c),c);crows[c['kind']]=row
                controls.append({'query_id':q['id'],'kind':c['kind'],'score':row,'standalone_decision':decide([row]),'source_absent_plus_control':decide(absent+[row])})
        ledgers.append({'query_id':q['id'],'expected_unit_id':q['expected_unit_id'],'eligible_query_fingerprint_types':len(qi),
                        'scores':rows,'natural_decision':decide(rows),'source_work_absent_decision':decide(absent),
                        'source_absent_plus_frame':decide(absent+[crows['anchor_frame']]),
                        'opaque_positive_qualifies':crows['opaque']['qualifies']})
    nulls=[]
    for draw in frozen['null_orders']:
        indices={u['unit_id']:fingerprints(shuffled(u,draw['orders'][u['unit_id']]),spans=False) for u in sources}
        qrows=[]
        for q in queries:
            values=[len(qindices[q['id']].keys() & indices[u['unit_id']].keys()) for u in sources]
            maximum=max(values,default=0)
            qrows.append({'query_id':q['id'],'unit_scores':values,'maximum':maximum,
                          'top_unit_ids':sorted(u['unit_id'] for u,v in zip(sources,values,strict=True) if v==maximum)})
        nulls.append({'draw':draw['draw'],'query_scores':qrows})
    for ledger in ledgers:
        observed=ledger['natural_decision']['top_score'];values=[next(q for q in d['query_scores'] if q['query_id']==ledger['query_id'])['maximum'] for d in nulls]
        exceed=sum(v>=observed for v in values);tail=Fraction(exceed+1,len(values)+1)
        ledger['search_max_null_tail']={'observed_maximum':observed,'null_ge_observed':exceed,'exact_ties':sum(v==observed for v in values),
                                        'numerator':tail.numerator,'denominator':tail.denominator,'raw_numerator':exceed+1,'raw_denominator':len(values)+1}
    requirements={'all_three_unique_expected_units':len(ledgers)==3 and all(l['natural_decision']['nominated']==l['expected_unit_id'] for l in ledgers),
                  'all_three_search_max_tails_le_0_01':all(Fraction(l['search_max_null_tail']['numerator'],l['search_max_null_tail']['denominator'])<=Fraction(1,100) for l in ledgers),
                  'zero_source_work_absent_nominations':all(l['source_work_absent_decision']['nominated'] is None for l in ledgers),
                  'zero_source_absent_frame_nominations':all(l['source_absent_plus_frame']['nominated'] is None for l in ledgers),
                  'all_three_opaque_positives':all(l['opaque_positive_qualifies'] for l in ledgers)}
    return {'query_ledgers':ledgers,'controls':controls,'nulls':nulls,'gate':{'requirements':requirements,'passed':all(requirements.values())},
            'null_unit_order':[u['unit_id'] for u in sources]}
