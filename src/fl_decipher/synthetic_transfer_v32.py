"""Supervised symbolic mapping, then frozen-map global indel alignment."""
from collections import Counter,defaultdict
import hashlib


def h(s):return hashlib.sha256(s.encode()).hexdigest()
def identity(kind,*parts):return kind+h('v32|'+kind+'|'+'|'.join(map(str,parts)))[:20]
def alias(key,cls,parity=0):return 'aliascode'+h(f'v32|alias|{key}|{cls}|{parity}')[:20]
def barrier(i):return f'copiedanchor{(i//17)%3}'


def view(forms):
    text=' '.join(forms);offset=0;tokens=[]
    for f in forms:
        assert f.isalnum() and f.isascii()
        tokens.append({'form':f,'start':offset,'end':offset+len(f),'blocked':f in ['copiedanchor0','copiedanchor1','copiedanchor2']})
        offset+=len(f)+1
    return {'text':text,'tokens':tokens}


def training(cfg):
    units=[]
    for key in cfg['training_keys']:
        for passage in range(cfg['training_passages_per_key']):
            classes=[]
            for cycle in range(cfg['training_cycles']):
                classes.extend(sorted(range(cfg['trained_classes']),key=lambda c:(h(f'v32|train|{key}|{passage}|{cycle}|{c}'),c)))
            source=[];query=[]
            for i,c in enumerate(classes):
                source.append(f'symbol{c}');query.append(alias(key,c))
                if (i+1)%cfg['barrier_period']==0:source.append(barrier(i));query.append(barrier(i))
            assert len(source)==len(query)
            units.append({'unit_id':identity('train',key,passage),'source':view(source),'query':view(query),'aligned_positions':[[i,i] for i in range(len(source))]})
    return {'units':units}


def learn(data,min_units=2):
    ledger=defaultdict(lambda:defaultdict(list))
    for unit in data['units']:
        for qi,si in unit['aligned_positions']:
            q=unit['query']['tokens'][qi];s=unit['source']['tokens'][si]
            if q['blocked'] or s['blocked']:continue
            ledger[q['form']][s['form']].append({'unit_id':unit['unit_id'],'query_index':qi,'source_index':si,
                                                'query_span':[q['start'],q['end']],'source_span':[s['start'],s['end']]})
    records={};entries={}
    for form,outcomes in sorted(ledger.items()):
        rows=[{'source_form':s,'units':sorted({r['unit_id'] for r in obs}),'occurrences':obs} for s,obs in sorted(outcomes.items())]
        units=sorted({r['unit_id'] for obs in outcomes.values() for r in obs})
        status='conflict' if len(rows)>1 else 'admitted' if len(units)>=min_units else 'insufficient_support'
        records[form]={'outcomes':rows,'status':status}
        if status=='admitted':entries[form]={'source_form':rows[0]['source_form'],'support_units':units}
    return {'entries':entries,'ledger':records,'minimum_training_units':min_units}


def make_query(source,key,base,mechanism):
    n=len(source);origins=list(range(n))
    if mechanism=='deletion':origins=[i for i in origins if (i+1)%7]
    elif mechanism=='reordering':
        for i in range(6,n-1,7):origins[i],origins[i+1]=origins[i+1],origins[i]
    forms=[];lineage=[];bits=[];insertions=[];counts=Counter()
    for i in origins:
        f=source[i];blocked=f.startswith('copiedanchor');bit=counts[f]%2 if mechanism=='contextual' else 0
        forms.append(f if blocked else alias(key,int(f.removeprefix('symbol')),bit));lineage.append(i);bits.append(None if blocked else bit)
        if not blocked:counts[f]+=1
        if mechanism=='insertion' and (i+1)%7==0:
            insertions.append({'query_index':len(forms),'source_index':i})
            forms.append(f'inserted{base}at{i}');lineage.append(None);bits.append(None)
    return forms,{'origins':lineage,'alias_parities':bits,'insertions':insertions,'deleted_indices':sorted(set(range(n))-{i for i in lineage if i is not None})}


def decode(query,model):
    rows=[]
    for i,t in enumerate(query['tokens']):
        if t['blocked']:status='blocked';source=None
        elif t['form'] in model['entries']:status='mapped';source=model['entries'][t['form']]['source_form']
        else:status=model['ledger'].get(t['form'],{}).get('status','unseen');source=None
        rows.append({'token_index':i,'source_form':source,'status':status})
    return rows


def potential(decoded,query,candidates):
    known=sum(t['source_form'] is not None for t in decoded);n=len(query['tokens'])
    maxima=[min(known,sum(not t['blocked'] for t in c['tokens'])) for c in candidates]
    available=any(k>=24 and 5*k>=4*n and 5*k>=4*len(c['tokens']) for k,c in zip(maxima,candidates,strict=True))
    return {'query_tokens':n,'known_tokens':known,'status_counts':dict(Counter(t['status'] for t in decoded)),'potentially_available':available}


def anonymous(forms):
    ids={};result=[]
    for f in forms:
        if f not in ids:ids[f]=len(ids)
        result.append(ids[f])
    return result


def prepare_tests(cfg,model):
    views={};cases=[];bases=[];queries=[];gold=[];certificates=[]
    for gi,group in enumerate(cfg['groups']):
        keys=cfg['unseen_keys'] if group=='unseen_key' else cfg['training_keys']
        for key in keys:
            for passage in range(cfg['test_passages']):
                base=f'g{gi}k{key}p{passage}';source=[]
                for i in range(cfg['test_length']):
                    c=int(h(f'v32|test|{passage}|{i}'),16)%cfg['trained_classes']
                    if group=='sparse_unknown' and (i+1)%11==0:c=24+i%8
                    if group=='dense_unknown' and i%3==0:c=24+i%8
                    source.append(barrier(i) if (i+1)%cfg['barrier_period']==0 else f'symbol{c}')
                positions=[i for i,f in enumerate(source) if not f.startswith('copiedanchor')]
                order=sorted(positions,key=lambda i:(h(f'v32|shuffle|{base}|{i}'),i));shuffled=source[:]
                for dst,src in zip(positions,order,strict=True):shuffled[dst]=source[src]
                different=[];frame=[];impostor=[]
                for i,f in enumerate(source):
                    blocked=f.startswith('copiedanchor')
                    different.append(f if blocked else f'symbol{int(h(f"v32|negative|{base}|{i}"),16)%32}')
                    frame.append(f if blocked else f'frame{base}at{i}')
                    if blocked:impostor.append(f)
                    else:
                        c=int(f.removeprefix('symbol'));shift=(c+1)%24 if c<24 else 24+(c-24+1)%8
                        impostor.append(f'symbol{shift}')
                raw={'parent':source,'shuffle':shuffled,'different':different,'frame':frame,'impostor':impostor,'duplicate':source[:]}
                ids={role:identity('view',base,role) for role in raw}
                for role,fs in raw.items():views[ids[role]]=view(fs)
                bases.append({'base_id':base,'group':group,'key':key,'passage':passage,'view_ids':ids,'shuffle_order':order})
                certificates.append({'base_id':base,'parent_view_id':ids['parent'],'impostor_view_id':ids['impostor'],
                                     'anonymous_profile_equal':anonymous(source)==anonymous(impostor),'anonymous_profile':anonymous(source),'duplicate_bytes_equal':source==raw['duplicate']})
                for mechanism in cfg['mechanisms']:
                    fs,trace=make_query(source,key,base,mechanism);qid=identity('query',base,mechanism);views[qid]=view(fs)
                    queries.append({'query_view_id':qid,'base_id':base,'group':group,'key':key,'passage':passage,'mechanism':mechanism,**trace})
                    layouts={'present':[(0,'parent'),(1,'shuffle'),(2,'different'),(3,'frame')],
                             'absent':[(1,'shuffle'),(2,'different'),(3,'frame')],
                             'impostor_only':[(0,'impostor'),(1,'shuffle'),(2,'different'),(3,'frame')],
                             'parent_plus_impostor':[(0,'parent'),(1,'shuffle'),(2,'different'),(3,'frame'),(4,'impostor')],
                             'duplicate_parent':[(0,'parent'),(1,'shuffle'),(2,'different'),(3,'frame'),(4,'duplicate')]}
                    for scenario in cfg['scenarios']:
                        cid=identity('case',base,mechanism,scenario)
                        cases.append({'case_id':cid,'query_view_id':qid,'candidates':[{'slot_id':f'slot{i}','view_id':ids[role]} for i,role in layouts[scenario]]})
                        gold.append({'case_id':cid,'query_view_id':qid,'base_id':base,'group':group,'mechanism':mechanism,'scenario':scenario,
                                     'true_parent_slot':None if scenario in ['absent','impostor_only'] else 'slot0'})
    public={'views':views,'cases':cases};oracle={'bases':bases,'queries':queries,'cases':gold}
    decoded={q['query_view_id']:decode(views[q['query_view_id']],model) for q in queries}
    availability={q['query_view_id']:potential(decoded[q['query_view_id']],views[q['query_view_id']],
                      [views[v] for v in next(b for b in bases if b['base_id']==q['base_id'])['view_ids'].values()]) for q in queries}
    return public,oracle,{'decoded_queries':decoded,'availability':availability,'equivalence_certificates':certificates}


def align(query,candidate,decoded):
    qt=query['tokens'];ct=candidate['tokens'];n=len(qt);m=len(ct)
    cost=[[0]*(m+1) for _ in range(n+1)];ways=[[0]*(m+1) for _ in range(n+1)];back=[['']*(m+1) for _ in range(n+1)]
    for i in range(n+1):cost[i][0]=i;ways[i][0]=1;back[i][0]='q'
    for j in range(m+1):cost[0][j]=j;ways[0][j]=1;back[0][j]='c'
    for i in range(1,n+1):
        predicted=decoded[i-1]['source_form']
        for j in range(1,m+1):
            choices=[(cost[i-1][j]+1,1,'q',ways[i-1][j]),(cost[i][j-1]+1,2,'c',ways[i][j-1])]
            if predicted is not None and not ct[j-1]['blocked'] and predicted==ct[j-1]['form']:
                choices.append((cost[i-1][j-1],0,'m',ways[i-1][j-1]))
            best=min(choices);cost[i][j]=best[0];back[i][j]=best[2];ways[i][j]=sum(c[3] for c in choices if c[0]==best[0])
    trace=[];i=n;j=m
    while i or j:
        step=back[i][j]
        if i and j and step=='m':trace.append([i-1,j-1]);i-=1;j-=1
        elif i and step=='q':trace.append([i-1,None]);i-=1
        else:assert j;trace.append([None,j-1]);j-=1
    trace.reverse();matches=sum(a is not None and b is not None for a,b in trace)
    assert cost[n][m]==n+m-2*matches
    return {'matched_tokens':matches,'score':matches,'edit_cost':cost[n][m],'optimal_operation_paths':ways[n][m],
            'trace':trace,'query_coverage':[matches,n],'candidate_coverage':[matches,m],
            'qualifies':matches>=24 and 5*matches>=4*n and 5*matches>=4*m}


def decision(rows):
    maximum=max((r['score'] for r in rows),default=0);top=sorted(r['unit_id'] for r in rows if r['score']==maximum)
    good=any(r['qualifies'] for r in rows if r['score']==maximum)
    chosen=top[0] if good and len(top)==1 else None
    return {'nominated':chosen,'top_score':maximum,'top_unit_ids':top,
            'reason':'unique_supported_coverage' if chosen else 'top_tie' if good else 'insufficient_supported_coverage'}


def predict(public,model):
    qids=list(dict.fromkeys(c['query_view_id'] for c in public['cases']))
    decoded={i:decode(public['views'][i],model) for i in qids};pairs={};panels=[]
    for c in public['cases']:
        q=c['query_view_id'];rows=[]
        for v in c['candidates']:
            vid=v['view_id'];pid=q+'::'+vid
            if pid not in pairs:pairs[pid]={'query_view_id':q,'candidate_view_id':vid,**align(public['views'][q],public['views'][vid],decoded[q])}
            r=pairs[pid];rows.append({'unit_id':v['slot_id'],'score':r['score'],'qualifies':r['qualifies'],'pair_id':pid})
        panels.append({'case_id':c['case_id'],'scores':rows,'decision':decision(rows)})
    return {'decoded_queries':decoded,'pair_scores':pairs,'panels':panels}


def assess(public,oracle,availability,predictions):
    panels={p['case_id']:p for p in predictions['panels']};bases={b['base_id']:b for b in oracle['bases']};outcomes=[];paired=[]
    for g in oracle['cases']:
        nom=panels[g['case_id']]['decision']['nominated']
        outcome='abstain' if nom is None else 'correct_parent' if nom==g['true_parent_slot'] else 'non_parent'
        outcomes.append({'case_id':g['case_id'],'query_view_id':g['query_view_id'],'group':g['group'],'mechanism':g['mechanism'],'scenario':g['scenario'],
                         'available':availability['availability'][g['query_view_id']]['potentially_available'],'nominated':nom,'outcome':outcome})
    for q in oracle['queries']:
        qid=q['query_view_id'];parent=bases[q['base_id']]['view_ids']['parent'];p=predictions['pair_scores'][qid+'::'+parent]
        matched=[(i,j) for i,j in p['trace'] if i is not None and j is not None]
        exact=sum(q['origins'][i]==j for i,j in matched)
        paired.append({'query_view_id':qid,'group':q['group'],'mechanism':q['mechanism'],
                       'available':availability['availability'][qid]['potentially_available'],'qualifies':p['qualifies'],
                       'returned_matches':len(matched),'exact_origin_matches':exact,'optimal_operation_paths':p['optimal_operation_paths']})
    def counts(rows):
        return {'panels':len(rows),'correct_parent_nominations':sum(c['outcome']=='correct_parent' for c in rows),
                'non_parent_nominations':sum(c['outcome']=='non_parent' for c in rows),'abstentions':sum(c['outcome']=='abstain' for c in rows)}
    grouped={}
    for group in dict.fromkeys(q['group'] for q in oracle['queries']):
        grouped[group]={}
        for mechanism in dict.fromkeys(q['mechanism'] for q in oracle['queries']):
            ps=[p for p in paired if p['group']==group and p['mechanism']==mechanism]
            rs=[c for c in outcomes if c['group']==group and c['mechanism']==mechanism and c['scenario']=='present']
            good=[p for p in ps if p['qualifies']]
            grouped[group][mechanism]={'queries':len(ps),'potentially_available':sum(p['available'] for p in ps),'parent_pair_qualifications':len(good),
                   'present':counts(rs),'qualified_parent_returned_matches':sum(p['returned_matches'] for p in good),
                   'qualified_parent_exact_origin_matches':sum(p['exact_origin_matches'] for p in good),
                   'all_parent_returned_matches':sum(p['returned_matches'] for p in ps),'all_parent_exact_origin_matches':sum(p['exact_origin_matches'] for p in ps)}
    scenarios={s:counts([c for c in outcomes if c['scenario']==s]) for s in dict.fromkeys(c['scenario'] for c in outcomes)}
    supported=[c for c in outcomes if c['group']=='seen' and c['mechanism'] in ['bijective','insertion','deletion','reordering']]
    present=[c for c in supported if c['scenario']=='present'];plus=[c for c in supported if c['scenario']=='parent_plus_impostor']
    rejections=[c for c in outcomes if c['scenario'] in ['absent','impostor_only']]
    unknown=[c for c in outcomes if c['group'] in ['dense_unknown','unseen_key']]
    no_unmapped_matches=all(predictions['decoded_queries'][p['query_view_id']][i]['source_form'] is not None
                          for p in predictions['pair_scores'].values() for i,j in p['trace'] if i is not None and j is not None)
    requirements={'all_96_supported_present_recovered':len(present)==96 and all(c['outcome']=='correct_parent' for c in present),
                  'all_96_supported_plus_impostor_recovered':len(plus)==96 and all(c['outcome']=='correct_parent' for c in plus),
                  'zero_non_parent_nominations_in_840_rejections':len(rejections)==840 and all(c['outcome']=='abstain' for c in rejections),
                  'all_420_duplicate_panels_abstain':scenarios['duplicate_parent']['panels']==420 and scenarios['duplicate_parent']['abstentions']==420,
                  'all_900_dense_unknown_and_unseen_key_panels_abstain':len(unknown)==900 and all(c['outcome']=='abstain' for c in unknown),
                  'all_unmapped_tokens_abstain':no_unmapped_matches}
    qualified=[p for p in paired if p['qualifies']]
    metrics={'by_group_mechanism':grouped,'by_scenario':scenarios,'supported_present':counts(present),'supported_plus_impostor':counts(plus),
             'rejection_panels':counts(rejections),'dense_unknown_and_unseen_key':counts(unknown),
             'unavailable_panels':counts([c for c in outcomes if not c['available']]),
             'qualified_parent_pairs':len(qualified),'qualified_parent_returned_matches':sum(p['returned_matches'] for p in qualified),
             'qualified_parent_exact_origin_matches':sum(p['exact_origin_matches'] for p in qualified),
             'qualified_parent_pairs_with_multiple_operation_paths':sum(p['optimal_operation_paths']>1 for p in qualified),
             'unmapped_query_token_count':sum(t['source_form'] is None for rows in predictions['decoded_queries'].values() for t in rows)}
    return {'case_outcomes':outcomes,'parent_pair_alignment':paired,'metrics':metrics,
            'synthetic_transfer_gate':{'requirements':requirements,'passed':all(requirements.values())}}
