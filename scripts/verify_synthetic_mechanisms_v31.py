"""Independent generator, lineage checks and pairwise-equality scoring replay."""
from pathlib import Path
from datetime import datetime,timezone
from collections import Counter
import hashlib,json,sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from verify_paragraph_patterns_v30 import oracle_index,oracle_row,oracle_decision

def read(p):return json.loads((ROOT/p).read_text())
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def hashed(s):return hashlib.sha256(s.encode('utf-8'))
def label(k,*parts):return k+hashed('|'.join(['v31',k]+list(map(str,parts)))).hexdigest()[:20]


def text_view(forms):
    text=' '.join(forms);offset=0;ts=[]
    for f in forms:
        assert f.isascii() and f.isalnum()
        ts.append({'start':offset,'end':offset+len(f),'form':f,'blocked':f in ['copiedanchor0','copiedanchor1','copiedanchor2']})
        assert text[offset:offset+len(f)]==f;offset+=len(f)+1
    return {'text':text,'tokens':ts}


def reference_profile(unit):
    index=oracle_index(unit)
    return [{'signature':list(k),'occurrences':len(index[k])} for k in sorted(index)]


def reference_prepare(cfg):
    views={};cases=[];bases=[];queries=[];gold=[];worlds=[]
    for p,spec in enumerate(cfg['profiles']):
        for key in cfg['keys']:
            base=f'p{p:02d}k{key}';n=spec['length'];period=spec['barrier_period'];source=[]
            for i in range(n):
                if (i+1)%period==0:f='copiedanchor'+str((i//period)%3)
                else:
                    if spec['kind']=='hash':cls=int.from_bytes(hashed(f'v31|profile|{p}|{i}').digest(),'big')%spec['vocabulary']
                    elif spec['kind']=='unique':cls=i
                    elif spec['kind']=='one_repeat':cls=0 if i%3==0 else i+100
                    elif spec['kind']=='short':cls=(0,1,0,2,1,3,4,5)[i]
                    else:raise AssertionError(spec)
                    f='sourcep'+str(p)+'k'+str(key)+'word'+str(cls)
                source.append(f)
            blocked=[f in ['copiedanchor0','copiedanchor1','copiedanchor2'] for f in source]
            table={f:['opaquecode'+hashed('|'.join(['v31','alias',str(p),str(key),f,str(bit)])).hexdigest()[:20] for bit in range(2)] for f in sorted(set(source)) if not f.startswith('copiedanchor')}
            assert len(set(v for pair in table.values() for v in pair))==2*len(table)
            pos=[i for i in range(n) if not blocked[i]]
            order=[i for _,i in sorted((hashed(f'v31|shuffle|{base}|{i}').digest(),i) for i in pos)]
            sf=source.copy()
            for j,i in enumerate(pos):sf[i]=source[order[j]]
            imp={f:'impostorcode'+hashed(f'v31|impostor|{base}|{f}').hexdigest()[:20] for f in sorted(set(source)) if not f.startswith('copiedanchor')}
            raw={'parent':source,
                 'unique':[f if blocked[i] else f'unique{base}at{i}' for i,f in enumerate(source)],
                 'shuffle':sf,
                 'different':[f if blocked[i] else f'negative{base}class{int.from_bytes(hashed(f"v31|negative|{base}|{i}").digest(),"big")%12}' for i,f in enumerate(source)],
                 'impostor':[f if blocked[i] else imp[f] for i,f in enumerate(source)],
                 'frame':[f if blocked[i] else f'frame{base}at{i}' for i,f in enumerate(source)]}
            ids={role:label('view',base,role) for role in raw}
            for role,forms in raw.items():views[ids[role]]=text_view(forms)
            bases.append({'base_id':base,'profile_index':p,'profile_id':spec['id'],'key':key,'view_ids':ids,'alias_table':table,'shuffle_order':order,'impostor_aliases':imp})
            for mechanism in cfg['mechanisms']:
                origins=[];i=0
                while i<n:
                    if mechanism=='deletion' and (i+1)%7==0:i+=1;continue
                    if mechanism=='reordering' and i%7==6 and i+1<n:origins.extend([i+1,i]);i+=2;continue
                    origins.append(i);i+=1
                fs=[];lineage=[];bits=[];insertions=[]
                for i in origins:
                    f=source[i];bit=sum(source[j]==f for j in range(i))%2 if mechanism=='contextual' else 0
                    fs.append(f if blocked[i] else table[f][bit]);lineage.append(i);bits.append(None if blocked[i] else bit)
                    if mechanism=='insertion' and i%7==6:
                        insertions.append({'query_index':len(fs),'source_index':i});fs.append(f'insertedp{p}k{key}at{i}');lineage.append(None);bits.append(None)
                qid=label('query',base,mechanism);views[qid]=text_view(fs)
                removed=[i for i in range(n) if i not in lineage]
                queries.append({'query_view_id':qid,'base_id':base,'mechanism':mechanism,'origins':lineage,'alias_parities':bits,'insertions':insertions,'deleted_indices':removed})
                case_ids={}
                layouts={'present':[(0,'parent'),(1,'unique'),(2,'shuffle'),(3,'different')],
                         'absent':[(1,'unique'),(2,'shuffle'),(3,'different')],
                         'collision':[(0,'parent'),(1,'unique'),(2,'shuffle'),(3,'different'),(4,'impostor')],
                         'impostor_only':[(0,'impostor'),(1,'unique'),(2,'shuffle'),(3,'different')],
                         'anchor_frame':[(0,'frame'),(1,'unique'),(2,'shuffle'),(3,'different')]}
                for scenario in cfg['scenarios']:
                    cid=label('case',base,mechanism,scenario);case_ids[scenario]=cid
                    cases.append({'case_id':cid,'query_view_id':qid,'candidates':[{'slot_id':f'slot{i}','view_id':ids[role]} for i,role in layouts[scenario]]})
                    gold.append({'case_id':cid,'query_view_id':qid,'base_id':base,'mechanism':mechanism,'scenario':scenario,'true_parent_slot':'slot0' if scenario in ['present','collision'] else None})
                worlds.append({'query_view_id':qid,'present_case_id':case_ids['present'],'impostor_case_id':case_ids['impostor_only']})
    public={'views':views,'cases':cases};oracle={'bases':bases,'queries':queries,'cases':gold,'paired_worlds':worlds}
    cached={i:oracle_index(v) for i,v in views.items()}
    availability={'views':{i:{'fingerprint_types':len(cached[i]),'feature_available':len(cached[i])>=2} for i in views},'query_counts':{},'equivalence_certificates':[]}
    for mechanism in cfg['mechanisms']:
        selected=[q for q in queries if q['mechanism']==mechanism]
        availability['query_counts'][mechanism]={'all_queries':len(selected),'feature_available':sum(availability['views'][q['query_view_id']]['feature_available'] for q in selected)}
    for b in bases:
        pa=reference_profile(views[b['view_ids']['parent']]);pb=reference_profile(views[b['view_ids']['impostor']])
        availability['equivalence_certificates'].append({'base_id':b['base_id'],'parent_view_id':b['view_ids']['parent'],'impostor_view_id':b['view_ids']['impostor'],'profile_equal':pa==pb,'profile':pa})
    return public,oracle,availability


def reference_predict(public):
    features={i:oracle_index(v) for i,v in public['views'].items()};pairs={};panels=[]
    for c in public['cases']:
        q=c['query_view_id'];rows=[]
        for s in c['candidates']:
            v=s['view_id'];pid=q+'::'+v
            if pid not in pairs:pairs[pid]={'query_view_id':q,'candidate_view_id':v,**oracle_row(features[q],features[v],{'unit_id':v,'work':'synthetic'})}
            r=pairs[pid];rows.append({'unit_id':s['slot_id'],'score':r['score'],'qualifies':r['qualifies'],'pair_id':pid})
        panels.append({'case_id':c['case_id'],'scores':rows,'decision':oracle_decision(rows)})
    return {'pair_scores':pairs,'panels':panels}


def reference_assess(public,oracle,availability,predictions):
    case_predictions={c['case_id']:c for c in predictions['panels']};parent_ids={b['base_id']:b['view_ids']['parent'] for b in oracle['bases']}
    paired=[];cases=[];worlds=[]
    for q in oracle['queries']:
        qid=q['query_view_id'];p=predictions['pair_scores'][qid+'::'+parent_ids[q['base_id']]]
        paired.append({'query_view_id':qid,'mechanism':q['mechanism'],'base_id':q['base_id'],'feature_available':availability['views'][qid]['feature_available'],'parent_pair_score':p['score'],'parent_pair_qualifies':p['qualifies']})
    for g in oracle['cases']:
        nom=case_predictions[g['case_id']]['decision']['nominated']
        outcome='abstain' if nom is None else 'correct_parent' if nom==g['true_parent_slot'] else 'non_parent'
        cases.append({'case_id':g['case_id'],'mechanism':g['mechanism'],'scenario':g['scenario'],'feature_available':availability['views'][g['query_view_id']]['feature_available'],
                      'true_parent_slot':g['true_parent_slot'],'nominated':nom,'outcome':outcome})
    mechanisms={};scenarios={}
    for kind in dict.fromkeys(q['mechanism'] for q in oracle['queries']):
        qs=[q for q in paired if q['mechanism']==kind];prs=[c for c in cases if c['mechanism']==kind and c['scenario']=='present']
        mechanisms[kind]={'queries':len(qs),'feature_available':len([q for q in qs if q['feature_available']]),
                         'parent_pair_qualifications':len([q for q in qs if q['parent_pair_qualifies']]),
                         'available_parent_pair_qualifications':len([q for q in qs if q['feature_available'] and q['parent_pair_qualifies']]),
                         'present_parent_recoveries':len([c for c in prs if c['outcome']=='correct_parent']),
                         'available_present_parent_recoveries':len([c for c in prs if c['feature_available'] and c['outcome']=='correct_parent']),
                         'present_non_parent_nominations':len([c for c in prs if c['outcome']=='non_parent']),
                         'present_abstentions':len([c for c in prs if c['outcome']=='abstain'])}
    for kind in dict.fromkeys(c['scenario'] for c in cases):
        cs=[c for c in cases if c['scenario']==kind];counts=Counter(c['outcome'] for c in cs)
        scenarios[kind]={'panels':len(cs),'feature_available':len([c for c in cs if c['feature_available']]),
                        'correct_parent_nominations':counts['correct_parent'],'non_parent_nominations':counts['non_parent'],'abstentions':counts['abstain'],
                        'frame_selections':len([c for c in cs if c['nominated']=='slot0']) if kind=='anchor_frame' else 0}
    publics={c['case_id']:c for c in public['cases']};profiles={i:reference_profile(v) for i,v in public['views'].items()}
    for w in oracle['paired_worlds']:
        a,b=publics[w['present_case_id']],publics[w['impostor_case_id']];ap,bp=case_predictions[a['case_id']],case_predictions[b['case_id']]
        left=[(c['slot_id'],profiles[c['view_id']]) for c in a['candidates']];right=[(c['slot_id'],profiles[c['view_id']]) for c in b['candidates']]
        ls=[(s['unit_id'],s['score'],s['qualifies']) for s in ap['scores']];rs=[(s['unit_id'],s['score'],s['qualifies']) for s in bp['scores']]
        worlds.append(w|{'features_equal':left==right,'scores_equal':ls==rs,'decisions_equal':ap['decision']==bp['decision'],
                         'slot0_nominated_in_both':ap['decision']['nominated']==bp['decision']['nominated']=='slot0'})
    unavailable=[c for c in cases if not c['feature_available']];rejections=[c for c in cases if c['scenario'] in ('absent','impostor_only','anchor_frame')]
    bij=mechanisms['bijective']
    requirements={'available_bijective_pairs_qualify':bij['feature_available']!=0 and bij['feature_available']==bij['available_parent_pair_qualifications'],
                  'available_bijective_present_recovered':bij['feature_available']!=0 and bij['feature_available']==bij['available_present_parent_recoveries'],
                  'all_600_rejection_panels_abstain':len(rejections)==600 and not any(c['nominated'] is not None for c in rejections),
                  'all_200_collision_panels_abstain':scenarios['collision']['panels']==200 and scenarios['collision']['abstentions']==200,
                  'all_feature_unavailable_panels_abstain':not any(c['nominated'] is not None for c in unavailable)}
    engineering={'all_1000_panels_scored':len(cases)==1000 and len(predictions['panels'])==1000,
                 'all_40_equivalence_certificates':len(availability['equivalence_certificates'])==40 and all(c['profile_equal'] for c in availability['equivalence_certificates']),
                 'all_200_paired_features_equal':len(worlds)==200 and all(w['features_equal'] for w in worlds),
                 'all_200_paired_decisions_equal':len(worlds)==200 and all(w['scores_equal'] and w['decisions_equal'] for w in worlds)}
    metrics={'by_mechanism':mechanisms,'by_scenario':scenarios,'unavailable_panels':len(unavailable),
             'unavailable_panel_abstentions':len([c for c in unavailable if c['nominated'] is None]),'rejection_panels':len(rejections),
             'rejection_panel_nominations':len([c for c in rejections if c['nominated'] is not None]),'paired_world_slot0_nominations':len([w for w in worlds if w['slot0_nominated_in_both']])}
    return {'paired_sensitivity':paired,'case_outcomes':cases,'paired_worlds':worlds,'metrics':metrics,
            'admission_gate':{'requirements':requirements,'passed':all(requirements.values())},'engineering_calibration':{'requirements':engineering,'passed':all(engineering.values())}}


def main():
    from verify_correspondence_v6 import check_hashes
    cfg=read('experiments/synthetic_mechanisms_v31.json');pre=read('data/v31/preflight.json');bench=read('benchmarks/synthetic_mechanisms_v31.json')
    out=ROOT/'runs/000031_synthetic_mechanisms';manifest=check_hashes(out)
    for hashes in [cfg['input_hashes'],pre['input_hashes'],pre['code_hashes'],bench['input_hashes']]:
        for name,h in hashes.items():assert sha(name)==h,name
    assert cfg['keys']==[11,29,47,83] and len(cfg['profiles'])==10
    assert cfg['mechanisms']==['bijective','insertion','deletion','contextual','reordering']
    assert cfg['scenarios']==['present','absent','collision','impostor_only','anchor_frame']
    assert [cfg[k] for k in ['parent_denominator','query_denominator','panel_denominator']]==[40,200,1000]
    assert cfg['baseline_parameters']=={'window_tokens':10,'min_distinct_types':4,'min_repeated_types':2,'min_shared_types':2}
    assert manifest['code_hashes']==pre['code_hashes']
    prep=read('data/v31/preparation_receipt.json');pr=read('runs/000031_synthetic_mechanisms/prediction_receipt.json')
    assert cfg['registered_at_utc']<pre['sealed_at_utc']<prep['prepared_at_utc']<bench['frozen_at_utc']<manifest['started_at_utc']<pr['predictions_frozen_at_utc']<manifest['finished_at_utc']
    for p,h in prep['output_hashes'].items():assert sha(p)==h,p
    assert prep['pair_scores_computed']==0 and pr['oracle_used_for_predictions'] is False
    public,oracle,availability=reference_prepare(cfg)
    for name,data in [('public_cases',public),('oracle',oracle),('availability',availability)]:assert read('data/v31/'+name+'.json')==data,name
    assert len(public['cases'])==1000 and len(oracle['queries'])==200 and len(oracle['bases'])==40
    expected=reference_predict(public);assert read('runs/000031_synthetic_mechanisms/predictions.json')==expected
    assert pr['predictions_sha256']==sha('runs/000031_synthetic_mechanisms/predictions.json') and pr['panels']==1000 and pr['distinct_pairs']==len(expected['pair_scores'])
    assessment=reference_assess(public,oracle,availability,expected);assert read('runs/000031_synthetic_mechanisms/assessment.json')==assessment
    report=read('runs/000031_synthetic_mechanisms/report.json')
    assert report=={'experiment_id':cfg['experiment_id'],'engineering_calibration_passed':assessment['engineering_calibration']['passed'],
                   'synthetic_candidate_admission_passed':assessment['admission_gate']['passed'],'parents':40,'queries':200,'panels':1000,
                   'distinct_pair_scores':len(expected['pair_scores']),'metrics':assessment['metrics'],'oracle_used_for_predictions':False,
                   'scientific_acceptance':None,'semantic_evaluation_metrics':None,'source_identities_admitted':0,'semantic_labels_admitted':0,
                   'independent_reviews_admitted':0,'untouched_test_units_admitted':0,'natural_targets_rescored':0,'new_network_requests':0,'model_executed':False,
                   'scope':'Known synthetic lineage and fixed v30 features only; no natural-source or meaning admission'}
    preserved=[]
    for path in sorted((ROOT/'runs').glob('*/manifest.json')):
        if path.parent!=out:check_hashes(path.parent);preserved.append(path.parent.name)
    assert len(preserved)==30
    for p in (ROOT/'reports').glob('*_deliverable_seal.json'):
        for name,h in json.loads(p.read_text()).get('deliverable_hashes',{}).items():assert sha(name)==h,name
    receipt={'state':'verified','run_manifest_sha256':sha('runs/000031_synthetic_mechanisms/manifest.json'),
             'synthetic_parents_verified':40,'queries_verified':200,'panels_verified':1000,'pair_scores_verified':len(expected['pair_scores']),
             'equivalence_certificates_verified':40,'paired_worlds_verified':200,'engineering_calibration_passed':assessment['engineering_calibration']['passed'],
             'synthetic_candidate_admission_passed':assessment['admission_gate']['passed'],'prior_runs_preserved':preserved,'semantic_labels_admitted':0,'scientific_acceptance':None}
    target=ROOT/'reports/000031_verification.json'
    if target.exists():assert {k:v for k,v in json.loads(target.read_text()).items() if k!='verified_at_utc'}==receipt
    else:
        receipt['verified_at_utc']=datetime.now(timezone.utc).isoformat();target.write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt,indent=2))


if __name__=='__main__':main()
