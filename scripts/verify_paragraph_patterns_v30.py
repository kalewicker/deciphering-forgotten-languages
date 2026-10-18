"""Independent pairwise-equality oracle, registry checks and complete null replay."""
from pathlib import Path
from datetime import datetime,timezone
from fractions import Fraction
from collections import Counter
import hashlib,json,unicodedata

ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads((ROOT/p).read_text())
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()


def lexical(text,blocked):
    runs=[];a=0
    while a<len(text):
        if not (text[a].isalnum() or unicodedata.category(text[a])[0]=='M'):a+=1;continue
        b=a+1
        while b<len(text) and (text[b].isalnum() or unicodedata.category(text[b])[0]=='M'):b+=1
        if any(c.isalnum() for c in text[a:b]):
            f=unicodedata.normalize('NFC',text[a:b]).casefold()
            runs.append({'start':a,'end':b,'form':f,'blocked':f in blocked})
        a=b
    return {'text':text,'tokens':runs}


def oracle_index(unit,spans=True):
    ts=unit['tokens'];index={}
    for start in range(max(0,len(ts)-9)):
        w=ts[start:start+10]
        if sum(t['blocked'] for t in w):continue
        # Partition positions by pairwise token equality, rather than a renaming map.
        first=[next(j for j in range(i+1) if w[j]['form']==w[i]['form']) for i in range(10)]
        roots=sorted(set(first));counts=Counter(first)
        if len(roots)<4 or len([n for n in counts.values() if n>1])<2:continue
        signature=tuple(roots.index(root) for root in first)
        index.setdefault(signature,[])
        if spans:
            a,b=w[0]['start'],w[9]['end']
            index[signature].append({'token_start':start,'token_end':start+10,'start':a,'end':b,'text':unit['text'][a:b]})
    return index


def oracle_row(qi,si,u):
    common=sorted(set(qi).intersection(si))
    return {'unit_id':u['unit_id'],'work':u['work'],'score':len(common),'qualifies':len(common)>=2,
            'shared_fingerprints':[{'signature':list(k),'query_occurrences':qi[k],'source_occurrences':si[k]} for k in common]}


def oracle_decision(rows):
    values=[r['score'] for r in rows];maximum=max(values) if values else 0
    top=sorted([r['unit_id'] for r in rows if r['score']==maximum]);selected=None
    if len(top)==1 and maximum>=2:selected=top[0]
    return {'nominated':selected,'top_score':maximum,'top_unit_ids':top,
            'reason':'unique_qualified' if selected is not None else 'top_tie' if maximum>=2 else 'insufficient_shared_patterns'}


def verify_registry(frozen,cfg):
    reg=frozen['registry'];anchors=read('data/v26/frozen.json')['queries']
    blocked=sorted(set(t['form'] for q in anchors for a in q['anchors'] for t in lexical(a,[])['tokens']))
    assert reg['blocked_forms']==blocked and len(blocked)==19
    html=read('runs/000028_kamri_block_audit/html_maps.json');fl=[]
    for work,m in html.items():
        for b in m['blocks']:
            s=m['flat_text'][b['start']:b['end']];assert s==b['text']
            fl.append({'unit_id':f"fl:{work}:{b['block_id']}",'work':work,'block_id':b['block_id'],
                       'original_start':b['start'],'original_end':b['end'],'role':'paragraph_markup_semantics_unresolved',**lexical(s,blocked)})
    assert reg['fl_units']==fl and len(fl)==55
    providers={p['page_id']:('runs/000028_kamri_block_audit/pdf_maps.json',p['lines']) for p in read('runs/000028_kamri_block_audit/pdf_maps.json') if p['work']=='western_esoterism'}
    providers.update({p['page_id']:('runs/000029_risk_layout_derivative/pages.json',p['lines']) for p in read('runs/000029_risk_layout_derivative/pages.json')})
    sources=[]
    assert len(cfg['source_regions'])==8
    for page,ranges in cfg['source_regions'].items():
        parent,lines=providers[page];used=[]
        for number,r in enumerate(ranges):
            native=list(range(r['start_line'],r['end_line']));assert native
            used.extend(native);text='';pieces=[]
            for j,i in enumerate(native):
                l=lines[i]
                if j:pieces.append({'kind':'join_newline','start':len(text),'end':len(text)+1,'text':'\n'});text+='\n'
                a=len(text);text+=l['text']
                pieces.append({'kind':'source_line','start':a,'end':len(text),'text':l['text'],'parent_line_id':l['line_id'],'parent_start':l.get('start'),'parent_end':l.get('end')})
            sources.append({'unit_id':page+f':u{number:02d}','work':page.split(':')[0],'page_id':page,'role':r['role'],
                            'candidate':r['role'] in cfg['candidate_roles'],'parent_json':parent,'line_indices':native,'pieces':pieces,**lexical(text,blocked)})
        assert used==list(range(len(lines)))
    assert sources==reg['source_units']
    queries=[next(u for u in fl if u['work']==q['work'] and u['block_id']==q['block_id'])|q for q in cfg['queries']]
    assert queries==reg['queries'] and len(queries)==3
    controls=[]
    for q in queries:
        original=q['tokens'];fs=[t['form'] for t in original];flags=[t['blocked'] for t in original]
        labels=dict(zip(sorted(set(fs)),[f'opaqueword{i}' for i in range(len(set(fs)))],strict=True))
        cases=[('opaque',[labels[f] for f in fs],flags),
               ('anchor_frame',[t['form'] if t['blocked'] else f'uniqueunusedfiller{i}' for i,t in enumerate(original)],flags),
               ('reverse',list(reversed(fs)),list(reversed(flags)))]
        for kind,forms,bits in cases:
            v=lexical(' '.join(forms),[]);assert len(v['tokens'])==len(bits)
            for t,bit in zip(v['tokens'],bits,strict=True):t['blocked']=bit
            controls.append({'unit_id':q['id']+':'+kind,'work':'synthetic_'+kind,'kind':kind,**v,'query_id':q['id']})
    assert frozen['controls']==controls
    candidates=[u for u in sources if u['candidate']]
    assert len(frozen['null_orders'])==199
    for d,draw in enumerate(frozen['null_orders']):
        assert draw['draw']==d and set(draw['orders'])=={u['unit_id'] for u in candidates}
        for u in candidates:
            native=[i for i,t in enumerate(u['tokens']) if not t['blocked']]
            keyed=[(hashlib.sha256('|'.join(['v30',str(d),u['unit_id'],str(i)]).encode('utf-8')).digest(),i) for i in native]
            order=[i for _,i in sorted(keyed)];assert draw['orders'][u['unit_id']]==order
    return candidates,queries


def oracle_evaluation(frozen,candidates,queries):
    source_indices={u['unit_id']:oracle_index(u) for u in candidates};qindices={q['id']:oracle_index(q) for q in queries}
    ledgers=[];controls=[]
    for q in queries:
        qi=qindices[q['id']];rows=[oracle_row(qi,source_indices[u['unit_id']],u) for u in candidates]
        absent=[r for r in rows if r['work']!=q['work']];frames={}
        for c in frozen['controls']:
            if c['query_id']!=q['id']:continue
            if c['kind']=='reverse':
                rev=oracle_index(c);rr=[oracle_row(rev,source_indices[u['unit_id']],u) for u in candidates]
                controls.append({'query_id':q['id'],'kind':'reverse_query','scores':rr,'decision':oracle_decision(rr)})
            else:
                row=oracle_row(qi,oracle_index(c),c);frames[c['kind']]=row
                controls.append({'query_id':q['id'],'kind':c['kind'],'score':row,'standalone_decision':oracle_decision([row]),'source_absent_plus_control':oracle_decision(absent+[row])})
        ledgers.append({'query_id':q['id'],'expected_unit_id':q['expected_unit_id'],'eligible_query_fingerprint_types':len(qi),'scores':rows,
                        'natural_decision':oracle_decision(rows),'source_work_absent_decision':oracle_decision(absent),
                        'source_absent_plus_frame':oracle_decision(absent+[frames['anchor_frame']]),'opaque_positive_qualifies':frames['opaque']['qualifies']})
    nulls=[]
    for draw in frozen['null_orders']:
        panel={}
        for u in candidates:
            original=u['tokens'];forms=[t['form'] for t in original];destinations=[i for i,t in enumerate(original) if not t['blocked']]
            for dst,src in zip(destinations,draw['orders'][u['unit_id']],strict=True):forms[dst]=original[src]['form']
            v=u|{'tokens':[t|{'form':f} for t,f in zip(original,forms,strict=True)]}
            panel[u['unit_id']]=set(oracle_index(v,spans=False))
        rows=[]
        for q in queries:
            values=[len(set(qindices[q['id']]).intersection(panel[u['unit_id']])) for u in candidates];maximum=max(values,default=0)
            rows.append({'query_id':q['id'],'unit_scores':values,'maximum':maximum,'top_unit_ids':sorted(candidates[i]['unit_id'] for i in range(len(values)) if values[i]==maximum)})
        nulls.append({'draw':draw['draw'],'query_scores':rows})
    for i,l in enumerate(ledgers):
        obs=l['natural_decision']['top_score'];vs=[n['query_scores'][i]['maximum'] for n in nulls];ge=len([v for v in vs if v>=obs]);fraction=Fraction(ge+1,200)
        l['search_max_null_tail']={'observed_maximum':obs,'null_ge_observed':ge,'exact_ties':vs.count(obs),'numerator':fraction.numerator,'denominator':fraction.denominator,'raw_numerator':ge+1,'raw_denominator':200}
    gates={'all_three_unique_expected_units':all(l['natural_decision']['nominated']==l['expected_unit_id'] for l in ledgers),
           'all_three_search_max_tails_le_0_01':all(l['search_max_null_tail']['raw_numerator']*100<=200 for l in ledgers),
           'zero_source_work_absent_nominations':not any(l['source_work_absent_decision']['nominated'] is not None for l in ledgers),
           'zero_source_absent_frame_nominations':not any(l['source_absent_plus_frame']['nominated'] is not None for l in ledgers),
           'all_three_opaque_positives':all(l['opaque_positive_qualifies'] for l in ledgers)}
    return {'query_ledgers':ledgers,'controls':controls,'nulls':nulls,'gate':{'requirements':gates,'passed':all(gates.values())}}


def main():
    from verify_correspondence_v6 import check_hashes
    cfg=read('experiments/paragraph_patterns_v30.json');pre=read('data/v30/preflight.json');bench=read('benchmarks/paragraph_patterns_v30.json')
    out=ROOT/'runs/000030_paragraph_patterns';manifest=check_hashes(out)
    for hashes in [cfg['input_hashes'],pre['input_hashes'],pre['code_hashes'],bench['input_hashes']]:
        for name,h in hashes.items():assert sha(name)==h,name
    assert [cfg[k] for k in ['window_tokens','min_distinct_types','min_repeated_types','min_shared_types','null_draws','query_denominator','source_work_denominator']]==[10,4,2,2,199,3,2]
    assert cfg['tail_limit']==[1,100] and manifest['code_hashes']==pre['code_hashes']
    frozen=read('data/v30/frozen.json');assert cfg['registered_at_utc']<pre['sealed_at_utc']<frozen['prepared_at_utc']<bench['frozen_at_utc']<manifest['started_at_utc']<manifest['finished_at_utc']
    candidates,queries=verify_registry(frozen,cfg);expected=oracle_evaluation(frozen,candidates,queries)
    for name,data in expected.items():assert read('runs/000030_paragraph_patterns/'+name+'.json')==data,name
    report=read('runs/000030_paragraph_patterns/report.json');ledgers=expected['query_ledgers']
    assert report=={'experiment_id':cfg['experiment_id'],'structural_development_criterion_passed':expected['gate']['passed'],
                    'query_denominator':3,'source_work_denominator':2,'FL_registry_units':55,'source_registry_units':len(frozen['registry']['source_units']),
                    'source_candidates':len(candidates),'natural_comparisons':3*len(candidates),'null_panels':199,'null_comparisons':3*len(candidates)*199,
                    'null_unit_order':[u['unit_id'] for u in candidates],'unique_expected_units':sum(l['natural_decision']['nominated']==l['expected_unit_id'] for l in ledgers),
                    'source_absent_nominations':sum(l['source_work_absent_decision']['nominated'] is not None for l in ledgers),
                    'opaque_positive_qualifications':sum(l['opaque_positive_qualifies'] for l in ledgers),
                    'scientific_acceptance':None,'semantic_evaluation_metrics':None,'source_identities_admitted':0,'semantic_labels_admitted':0,
                    'independent_reviews_admitted':0,'untouched_test_units_admitted':0,'model_executed':False,'target_rescored':False,'new_network_requests':0,
                    'scope':'Exposed paragraph-level substitution-pattern diagnostic; no semantic gold or source-identity acceptance'}
    visual=read('data/v30/boundary_review.json');assert visual['pages_reviewed']==8 and visual['independent_semantic_review'] is False
    views=read('data/v27/page_views.json')['pages'];assert visual['image_hashes']=={p['image']:p['image_sha256'] for p in views}
    assert visual['reviewed_at_utc']<pre['sealed_at_utc']
    preserved=[]
    for p in sorted((ROOT/'runs').glob('*/manifest.json')):
        if p.parent!=out:check_hashes(p.parent);preserved.append(p.parent.name)
    assert len(preserved)==29
    for p in (ROOT/'reports').glob('*_deliverable_seal.json'):
        for name,h in json.loads(p.read_text()).get('deliverable_hashes',{}).items():assert sha(name)==h,name
    receipt={'state':'verified','run_manifest_sha256':sha('runs/000030_paragraph_patterns/manifest.json'),'FL_units_verified':55,
             'source_units_verified':len(frozen['registry']['source_units']),'source_candidates_verified':len(candidates),'query_denominator':3,
             'natural_scores_verified':3*len(candidates),'null_panels_verified':199,'null_scores_verified':3*len(candidates)*199,
             'structural_development_criterion_passed':expected['gate']['passed'],'prior_runs_preserved':preserved,'semantic_labels_admitted':0,'scientific_acceptance':None}
    target=ROOT/'reports/000030_verification.json'
    if target.exists():assert {k:v for k,v in json.loads(target.read_text()).items() if k!='verified_at_utc'}==receipt
    else:
        receipt['verified_at_utc']=datetime.now(timezone.utc).isoformat();target.write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt,indent=2))


if __name__=='__main__':main()
