"""Known-lineage synthetic calibration of the unchanged v30 scorer."""
from collections import Counter
import hashlib
from fl_decipher.paragraph_patterns_v30 import view,fingerprints,scored,decide


def digest(text):return hashlib.sha256(text.encode('utf-8')).hexdigest()
def ident(kind,*parts):return kind+digest('v31|'+kind+'|'+'|'.join(map(str,parts)))[:20]


def source_forms(spec,p,key):
    n=spec['length'];period=spec['barrier_period'];forms=[]
    for i in range(n):
        if (i+1)%period==0:f=f'copiedanchor{(i//period)%3}'
        else:
            if spec['kind']=='hash':c=int(digest(f'v31|profile|{p}|{i}'),16)%spec['vocabulary']
            elif spec['kind']=='unique':c=i
            elif spec['kind']=='one_repeat':c=0 if i%3==0 else 100+i
            elif spec['kind']=='short':c=[0,1,0,2,1,3,4,5][i]
            else:raise ValueError(spec['kind'])
            f=f'sourcep{p}k{key}word{c}'
        forms.append(f)
    return forms


def aliases(forms,p,key):
    table={f:[f'opaquecode{digest(f"v31|alias|{p}|{key}|{f}|{bit}")[:20]}' for bit in [0,1]]
           for f in sorted(set(forms)) if not f.startswith('copiedanchor')}
    values=[v for pair in table.values() for v in pair];assert len(set(values))==len(values)
    return table


def transformed(forms,table,p,key,mechanism):
    origins=list(range(len(forms)))
    if mechanism=='deletion':origins=[i for i in origins if (i+1)%7]
    if mechanism=='reordering':
        for i in range(6,len(origins)-1,7):origins[i],origins[i+1]=origins[i+1],origins[i]
    result=[];lineage=[];parities=[];insertions=[];counts=Counter()
    for i in origins:
        f=forms[i];blocked=f.startswith('copiedanchor');bit=counts[f]%2 if mechanism=='contextual' else 0
        result.append(f if blocked else table[f][bit]);lineage.append(i);parities.append(None if blocked else bit)
        if not blocked:counts[f]+=1
        if mechanism=='insertion' and (i+1)%7==0:
            insertions.append({'query_index':len(result),'source_index':i})
            result.append(f'insertedp{p}k{key}at{i}');lineage.append(None);parities.append(None)
    return result,{'origins':lineage,'alias_parities':parities,'insertions':insertions,
                   'deleted_indices':sorted(set(range(len(forms)))-{i for i in lineage if i is not None})}


def profile(unit):
    return [{'signature':list(k),'occurrences':len(v)} for k,v in sorted(fingerprints(unit).items())]


def prepare(cfg):
    views={};cases=[];bases=[];queries=[];gold_cases=[];worlds=[]
    blocked={f'copiedanchor{i}' for i in range(3)}
    for p,spec in enumerate(cfg['profiles']):
        for key in cfg['keys']:
            base_id=f'p{p:02d}k{key}';forms=source_forms(spec,p,key);table=aliases(forms,p,key)
            raw={};raw['parent']=forms
            raw['unique']=[f if f in blocked else f'unique{base_id}at{i}' for i,f in enumerate(forms)]
            positions=[i for i,f in enumerate(forms) if f not in blocked]
            order=sorted(positions,key=lambda i:(digest(f'v31|shuffle|{base_id}|{i}'),i))
            shuffled=forms[:]
            for destination,origin in zip(positions,order,strict=True):shuffled[destination]=forms[origin]
            raw['shuffle']=shuffled
            raw['different']=[f if f in blocked else f'negative{base_id}class{int(digest(f"v31|negative|{base_id}|{i}"),16)%12}' for i,f in enumerate(forms)]
            imp={f:'impostorcode'+digest(f'v31|impostor|{base_id}|{f}')[:20] for f in sorted(set(forms)) if f not in blocked}
            assert len(set(imp.values()))==len(imp)
            raw['impostor']=[f if f in blocked else imp[f] for f in forms]
            raw['frame']=[f if f in blocked else f'frame{base_id}at{i}' for i,f in enumerate(forms)]
            ids={role:ident('view',base_id,role) for role in raw}
            for role,fs in raw.items():views[ids[role]]=view(' '.join(fs),blocked)
            bases.append({'base_id':base_id,'profile_index':p,'profile_id':spec['id'],'key':key,'view_ids':ids,
                          'alias_table':table,'shuffle_order':order,'impostor_aliases':imp})
            for mechanism in cfg['mechanisms']:
                fs,trace=transformed(forms,table,p,key,mechanism);qid=ident('query',base_id,mechanism)
                views[qid]=view(' '.join(fs),blocked)
                queries.append({'query_view_id':qid,'base_id':base_id,'mechanism':mechanism,**trace})
                panel_ids={}
                for scenario in cfg['scenarios']:
                    common=[{'slot_id':f'slot{i}','view_id':ids[role]} for i,role in [(1,'unique'),(2,'shuffle'),(3,'different')]]
                    if scenario=='present':panel=[{'slot_id':'slot0','view_id':ids['parent']}]+common
                    elif scenario=='absent':panel=common
                    elif scenario=='collision':panel=[{'slot_id':'slot0','view_id':ids['parent']}]+common+[{'slot_id':'slot4','view_id':ids['impostor']}]
                    elif scenario=='impostor_only':panel=[{'slot_id':'slot0','view_id':ids['impostor']}]+common
                    elif scenario=='anchor_frame':panel=[{'slot_id':'slot0','view_id':ids['frame']}]+common
                    else:raise ValueError(scenario)
                    cid=ident('case',base_id,mechanism,scenario);panel_ids[scenario]=cid
                    cases.append({'case_id':cid,'query_view_id':qid,'candidates':panel})
                    gold_cases.append({'case_id':cid,'query_view_id':qid,'base_id':base_id,'mechanism':mechanism,'scenario':scenario,
                                       'true_parent_slot':'slot0' if scenario in ['present','collision'] else None})
                worlds.append({'query_view_id':qid,'present_case_id':panel_ids['present'],'impostor_case_id':panel_ids['impostor_only']})
    public={'views':views,'cases':cases}
    oracle={'bases':bases,'queries':queries,'cases':gold_cases,'paired_worlds':worlds}
    availability={'views':{i:{'fingerprint_types':len(fingerprints(v)),'feature_available':len(fingerprints(v))>=2} for i,v in views.items()},
                  'query_counts':{},'equivalence_certificates':[]}
    for mechanism in cfg['mechanisms']:
        qs=[q for q in queries if q['mechanism']==mechanism]
        availability['query_counts'][mechanism]={'all_queries':len(qs),'feature_available':sum(availability['views'][q['query_view_id']]['feature_available'] for q in qs)}
    for b in bases:
        a=profile(views[b['view_ids']['parent']]);c=profile(views[b['view_ids']['impostor']])
        availability['equivalence_certificates'].append({'base_id':b['base_id'],'parent_view_id':b['view_ids']['parent'],
                      'impostor_view_id':b['view_ids']['impostor'],'profile_equal':a==c,'profile':a})
    return public,oracle,availability


def predict(public):
    # Oracle-free. Repeated query/candidate comparisons share one full witness record.
    indices={i:fingerprints(v) for i,v in public['views'].items()};pairs={};panels=[]
    for case in public['cases']:
        qid=case['query_view_id'];rows=[]
        for c in case['candidates']:
            vid=c['view_id'];pair_id=qid+'::'+vid
            if pair_id not in pairs:
                pairs[pair_id]={'query_view_id':qid,'candidate_view_id':vid,
                                **scored(indices[qid],indices[vid],{'unit_id':vid,'work':'synthetic'})}
            r=pairs[pair_id]
            rows.append({'unit_id':c['slot_id'],'score':r['score'],'qualifies':r['qualifies'],'pair_id':pair_id})
        panels.append({'case_id':case['case_id'],'scores':rows,'decision':decide(rows)})
    return {'pair_scores':pairs,'panels':panels}


def assess(public,oracle,availability,predictions):
    panels={p['case_id']:p for p in predictions['panels']};gold={c['case_id']:c for c in oracle['cases']}
    bases={b['base_id']:b for b in oracle['bases']};paired=[]
    for q in oracle['queries']:
        qid=q['query_view_id'];pid=bases[q['base_id']]['view_ids']['parent'];score=predictions['pair_scores'][qid+'::'+pid]
        paired.append({'query_view_id':qid,'mechanism':q['mechanism'],'base_id':q['base_id'],
                       'feature_available':availability['views'][qid]['feature_available'],'parent_pair_score':score['score'],'parent_pair_qualifies':score['qualifies']})
    cases=[]
    for c in oracle['cases']:
        prediction=panels[c['case_id']]['decision'];nom=prediction['nominated'];correct=nom is not None and nom==c['true_parent_slot']
        cases.append({'case_id':c['case_id'],'mechanism':c['mechanism'],'scenario':c['scenario'],
                      'feature_available':availability['views'][c['query_view_id']]['feature_available'],
                      'true_parent_slot':c['true_parent_slot'],'nominated':nom,
                      'outcome':'correct_parent' if correct else 'abstain' if nom is None else 'non_parent'})
    by_mechanism={}
    for mechanism in dict.fromkeys(q['mechanism'] for q in oracle['queries']):
        qs=[q for q in paired if q['mechanism']==mechanism];prs=[c for c in cases if c['mechanism']==mechanism and c['scenario']=='present']
        by_mechanism[mechanism]={'queries':len(qs),'feature_available':sum(q['feature_available'] for q in qs),
                'parent_pair_qualifications':sum(q['parent_pair_qualifies'] for q in qs),
                'available_parent_pair_qualifications':sum(q['parent_pair_qualifies'] and q['feature_available'] for q in qs),
                'present_parent_recoveries':sum(c['outcome']=='correct_parent' for c in prs),
                'available_present_parent_recoveries':sum(c['outcome']=='correct_parent' and c['feature_available'] for c in prs),
                'present_non_parent_nominations':sum(c['outcome']=='non_parent' for c in prs),'present_abstentions':sum(c['outcome']=='abstain' for c in prs)}
    by_scenario={}
    for scenario in dict.fromkeys(c['scenario'] for c in cases):
        rows=[c for c in cases if c['scenario']==scenario]
        by_scenario[scenario]={'panels':len(rows),'feature_available':sum(c['feature_available'] for c in rows),
                'correct_parent_nominations':sum(c['outcome']=='correct_parent' for c in rows),
                'non_parent_nominations':sum(c['outcome']=='non_parent' for c in rows),'abstentions':sum(c['outcome']=='abstain' for c in rows),
                'frame_selections':sum(c['nominated']=='slot0' for c in rows) if scenario=='anchor_frame' else 0}
    worlds=[]
    for w in oracle['paired_worlds']:
        a=next(c for c in public['cases'] if c['case_id']==w['present_case_id']);b=next(c for c in public['cases'] if c['case_id']==w['impostor_case_id'])
        pa=panels[a['case_id']];pb=panels[b['case_id']]
        fa=[(c['slot_id'],profile(public['views'][c['view_id']])) for c in a['candidates']]
        fb=[(c['slot_id'],profile(public['views'][c['view_id']])) for c in b['candidates']]
        sa=[{k:r[k] for k in ['unit_id','score','qualifies']} for r in pa['scores']]
        sb=[{k:r[k] for k in ['unit_id','score','qualifies']} for r in pb['scores']]
        worlds.append(w|{'features_equal':fa==fb,'scores_equal':sa==sb,'decisions_equal':pa['decision']==pb['decision'],
                         'slot0_nominated_in_both':pa['decision']['nominated']==pb['decision']['nominated']=='slot0'})
    unavailable=[c for c in cases if not c['feature_available']];rejections=[c for c in cases if c['scenario'] in ['absent','impostor_only','anchor_frame']]
    bij=by_mechanism['bijective']
    requirements={'available_bijective_pairs_qualify':bij['feature_available']>0 and bij['available_parent_pair_qualifications']==bij['feature_available'],
                  'available_bijective_present_recovered':bij['feature_available']>0 and bij['available_present_parent_recoveries']==bij['feature_available'],
                  'all_600_rejection_panels_abstain':len(rejections)==600 and all(c['outcome']=='abstain' for c in rejections),
                  'all_200_collision_panels_abstain':by_scenario['collision']['panels']==200 and by_scenario['collision']['abstentions']==200,
                  'all_feature_unavailable_panels_abstain':all(c['outcome']=='abstain' for c in unavailable)}
    engineering={'all_1000_panels_scored':len(cases)==len(predictions['panels'])==1000,
                 'all_40_equivalence_certificates':len(availability['equivalence_certificates'])==40 and all(c['profile_equal'] for c in availability['equivalence_certificates']),
                 'all_200_paired_features_equal':len(worlds)==200 and all(w['features_equal'] for w in worlds),
                 'all_200_paired_decisions_equal':len(worlds)==200 and all(w['scores_equal'] and w['decisions_equal'] for w in worlds)}
    metrics={'by_mechanism':by_mechanism,'by_scenario':by_scenario,'unavailable_panels':len(unavailable),
             'unavailable_panel_abstentions':sum(c['outcome']=='abstain' for c in unavailable),
             'rejection_panels':len(rejections),'rejection_panel_nominations':sum(c['outcome']!='abstain' for c in rejections),
             'paired_world_slot0_nominations':sum(w['slot0_nominated_in_both'] for w in worlds)}
    return {'paired_sensitivity':paired,'case_outcomes':cases,'paired_worlds':worlds,'metrics':metrics,
            'admission_gate':{'requirements':requirements,'passed':all(requirements.values())},
            'engineering_calibration':{'requirements':engineering,'passed':all(engineering.values())}}
