"""Independent generation/learning and maximum-LCS verification of indel paths."""
from pathlib import Path
from datetime import datetime,timezone
from collections import Counter
import hashlib,json,sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from verify_synthetic_mechanisms_v31 import text_view

def read(p):return json.loads((ROOT/p).read_text())
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def digest(s):return hashlib.sha256(s.encode('utf-8'))
def rid(kind,*xs):return kind+digest('|'.join(['v32',kind]+list(map(str,xs)))).hexdigest()[:20]
def ralias(key,cls,bit=0):return 'aliascode'+digest(f'v32|alias|{key}|{cls}|{bit}').hexdigest()[:20]
def rbarrier(i):return 'copiedanchor'+str((i//17)%3)


def reference_training(cfg):
    units=[]
    for key in cfg['training_keys']:
        for passage in range(cfg['training_passages_per_key']):
            symbols=[]
            for cycle in range(cfg['training_cycles']):
                order=[i for _,i in sorted((digest(f'v32|train|{key}|{passage}|{cycle}|{i}').digest(),i) for i in range(cfg['trained_classes']))]
                symbols.extend(order)
            source=[];query=[]
            for i,cls in enumerate(symbols):
                source.append('symbol'+str(cls));query.append(ralias(key,cls))
                if i%cfg['barrier_period']==cfg['barrier_period']-1:source.append(rbarrier(i));query.append(rbarrier(i))
            units.append({'unit_id':rid('train',key,passage),'source':text_view(source),'query':text_view(query),'aligned_positions':[[i,i] for i in range(len(source))]})
    return {'units':units}


def reference_learn(data,min_units=2):
    observations=[]
    for u in data['units']:
        for qi,si in u['aligned_positions']:
            q=u['query']['tokens'][qi];s=u['source']['tokens'][si]
            if q['blocked'] or s['blocked']:continue
            observations.append((q['form'],s['form'],{'unit_id':u['unit_id'],'query_index':qi,'source_index':si,
                                  'query_span':[q['start'],q['end']],'source_span':[s['start'],s['end']]}))
    ledger={};entries={}
    for form in sorted({q for q,s,o in observations}):
        selected=[(s,o) for q,s,o in observations if q==form];outcomes=[]
        for s in sorted({s for s,o in selected}):
            obs=[o for t,o in selected if t==s];outcomes.append({'source_form':s,'units':sorted({o['unit_id'] for o in obs}),'occurrences':obs})
        units=sorted({o['unit_id'] for s,o in selected})
        status='conflict' if len(outcomes)!=1 else 'insufficient_support' if len(units)<min_units else 'admitted'
        ledger[form]={'outcomes':outcomes,'status':status}
        if status=='admitted':entries[form]={'source_form':outcomes[0]['source_form'],'support_units':units}
    return {'entries':entries,'ledger':ledger,'minimum_training_units':min_units}


def reference_decode(q,model):
    result=[]
    for i,t in enumerate(q['tokens']):
        mapped=model['entries'].get(t['form']);source=None
        if t['blocked']:status='blocked'
        elif mapped is not None:status='mapped';source=mapped['source_form']
        elif t['form'] in model['ledger']:status=model['ledger'][t['form']]['status']
        else:status='unseen'
        result.append({'token_index':i,'source_form':source,'status':status})
    return result


def reference_potential(decoded,q,cs):
    known=len([t for t in decoded if t['source_form'] is not None]);n=len(q['tokens']);eligible=False
    for c in cs:
        bound=min(known,len([t for t in c['tokens'] if not t['blocked']]))
        if bound>=24 and bound*5>=n*4 and bound*5>=len(c['tokens'])*4:eligible=True
    return {'query_tokens':n,'known_tokens':known,'status_counts':dict(Counter(t['status'] for t in decoded)),'potentially_available':eligible}


def reference_anonymous(fs):
    first=[fs.index(f) for f in fs];roots=sorted(set(first))
    return [roots.index(i) for i in first]


def reference_tests(cfg,model):
    views={};cases=[];bases=[];queries=[];gold=[];certs=[]
    for gi,group in enumerate(cfg['groups']):
        keys=cfg['unseen_keys'] if group=='unseen_key' else cfg['training_keys']
        for key in keys:
            for passage in range(cfg['test_passages']):
                base=f'g{gi}k{key}p{passage}';n=cfg['test_length'];source=[]
                for i in range(n):
                    cls=int.from_bytes(digest(f'v32|test|{passage}|{i}').digest(),'big')%cfg['trained_classes']
                    if group=='sparse_unknown' and i%11==10:cls=24+i%8
                    elif group=='dense_unknown' and i%3==0:cls=24+i%8
                    source.append(rbarrier(i) if i%cfg['barrier_period']==cfg['barrier_period']-1 else f'symbol{cls}')
                positions=[i for i,f in enumerate(source) if not f.startswith('copiedanchor')]
                order=[i for _,i in sorted((digest(f'v32|shuffle|{base}|{i}').digest(),i) for i in positions)]
                shuffled=source.copy()
                for j,i in enumerate(positions):shuffled[i]=source[order[j]]
                different=[];frame=[];impostor=[]
                for i,f in enumerate(source):
                    if f.startswith('copiedanchor'):different.append(f);frame.append(f);impostor.append(f);continue
                    different.append('symbol'+str(int.from_bytes(digest(f'v32|negative|{base}|{i}').digest(),'big')%32))
                    frame.append(f'frame{base}at{i}');c=int(f[6:]);impostor.append('symbol'+str((c+1)%24 if c<24 else 24+(c-23)%8))
                raw={'parent':source,'shuffle':shuffled,'different':different,'frame':frame,'impostor':impostor,'duplicate':source.copy()}
                ids={role:rid('view',base,role) for role in raw}
                for role,fs in raw.items():views[ids[role]]=text_view(fs)
                bases.append({'base_id':base,'group':group,'key':key,'passage':passage,'view_ids':ids,'shuffle_order':order})
                certs.append({'base_id':base,'parent_view_id':ids['parent'],'impostor_view_id':ids['impostor'],
                              'anonymous_profile_equal':reference_anonymous(source)==reference_anonymous(impostor),
                              'anonymous_profile':reference_anonymous(source),'duplicate_bytes_equal':source==raw['duplicate']})
                for mechanism in cfg['mechanisms']:
                    origins=[];i=0
                    while i<n:
                        if mechanism=='deletion' and i%7==6:i+=1;continue
                        if mechanism=='reordering' and i%7==6 and i+1<n:origins.extend([i+1,i]);i+=2;continue
                        origins.append(i);i+=1
                    fs=[];lineage=[];parities=[];insertions=[]
                    for i in origins:
                        f=source[i];block=f.startswith('copiedanchor');bit=sum(source[j]==f for j in range(i))%2 if mechanism=='contextual' else 0
                        fs.append(f if block else ralias(key,int(f[6:]),bit));lineage.append(i);parities.append(None if block else bit)
                        if mechanism=='insertion' and i%7==6:
                            insertions.append({'query_index':len(fs),'source_index':i});fs.append(f'inserted{base}at{i}');lineage.append(None);parities.append(None)
                    qid=rid('query',base,mechanism);views[qid]=text_view(fs)
                    queries.append({'query_view_id':qid,'base_id':base,'group':group,'key':key,'passage':passage,'mechanism':mechanism,
                                    'origins':lineage,'alias_parities':parities,'insertions':insertions,'deleted_indices':[i for i in range(n) if i not in lineage]})
                    common=[(1,'shuffle'),(2,'different'),(3,'frame')]
                    for scenario in cfg['scenarios']:
                        slots=common if scenario=='absent' else [(0,'impostor' if scenario=='impostor_only' else 'parent')]+common
                        if scenario=='parent_plus_impostor':slots=slots+[(4,'impostor')]
                        if scenario=='duplicate_parent':slots=slots+[(4,'duplicate')]
                        cid=rid('case',base,mechanism,scenario)
                        cases.append({'case_id':cid,'query_view_id':qid,'candidates':[{'slot_id':f'slot{i}','view_id':ids[role]} for i,role in slots]})
                        gold.append({'case_id':cid,'query_view_id':qid,'base_id':base,'group':group,'mechanism':mechanism,'scenario':scenario,
                                     'true_parent_slot':None if scenario in ('absent','impostor_only') else 'slot0'})
    decoded={q['query_view_id']:reference_decode(views[q['query_view_id']],model) for q in queries};availability={};parent_lookup={b['base_id']:b for b in bases}
    for q in queries:
        qid=q['query_view_id'];cs=[views[i] for i in parent_lookup[q['base_id']]['view_ids'].values()]
        availability[qid]=reference_potential(decoded[qid],views[qid],cs)
    return {'views':views,'cases':cases},{'bases':bases,'queries':queries,'cases':gold},{'decoded_queries':decoded,'availability':availability,'equivalence_certificates':certs}


def reference_align(q,c,decoded):
    n=len(q['tokens']);m=len(c['tokens']);best=[[0]*(m+1) for _ in range(n+1)];paths=[[1]*(m+1) for _ in range(n+1)]
    for i in range(1,n+1):
        for j in range(1,m+1):
            allowed=decoded[i-1]['source_form'] is not None and not c['tokens'][j-1]['blocked'] and decoded[i-1]['source_form']==c['tokens'][j-1]['form']
            scores=[best[i-1][j],best[i][j-1]]
            if allowed:scores.append(best[i-1][j-1]+1)
            value=max(scores);best[i][j]=value
            paths[i][j]=(paths[i-1][j] if scores[0]==value else 0)+(paths[i][j-1] if scores[1]==value else 0)
            if allowed and scores[2]==value:paths[i][j]+=paths[i-1][j-1]
    trace=[];i=n;j=m
    while i+j:
        allowed=i>0 and j>0 and decoded[i-1]['source_form'] is not None and not c['tokens'][j-1]['blocked'] and decoded[i-1]['source_form']==c['tokens'][j-1]['form']
        if allowed and best[i-1][j-1]+1==best[i][j]:trace.append([i-1,j-1]);i-=1;j-=1
        elif i>0 and best[i-1][j]==best[i][j]:trace.append([i-1,None]);i-=1
        else:trace.append([None,j-1]);j-=1
    trace=list(reversed(trace));matches=best[n][m]
    assert [a for a,b in trace if a is not None]==list(range(n)) and [b for a,b in trace if b is not None]==list(range(m))
    assert sum(a is not None and b is not None for a,b in trace)==matches
    return {'matched_tokens':matches,'score':matches,'edit_cost':n+m-2*matches,'optimal_operation_paths':paths[n][m],
            'trace':trace,'query_coverage':[matches,n],'candidate_coverage':[matches,m],
            'qualifies':matches>=24 and matches*5>=n*4 and matches*5>=m*4}


def reference_decision(rows):
    maximum=max([r['score'] for r in rows],default=0);tied=sorted(r['unit_id'] for r in rows if r['score']==maximum)
    good=len([r for r in rows if r['score']==maximum and r['qualifies']])>0
    chosen=tied[0] if len(tied)==1 and good else None
    return {'nominated':chosen,'top_score':maximum,'top_unit_ids':tied,
            'reason':'unique_supported_coverage' if chosen else 'top_tie' if good else 'insufficient_supported_coverage'}


def reference_predict(public,model):
    decoded={qid:reference_decode(public['views'][qid],model) for qid in dict.fromkeys(c['query_view_id'] for c in public['cases'])};pairs={};panels=[]
    for c in public['cases']:
        qid=c['query_view_id'];rows=[]
        for v in c['candidates']:
            vid=v['view_id'];pid=qid+'::'+vid
            if pid not in pairs:pairs[pid]={'query_view_id':qid,'candidate_view_id':vid,**reference_align(public['views'][qid],public['views'][vid],decoded[qid])}
            r=pairs[pid];rows.append({'unit_id':v['slot_id'],'score':r['score'],'qualifies':r['qualifies'],'pair_id':pid})
        panels.append({'case_id':c['case_id'],'scores':rows,'decision':reference_decision(rows)})
    return {'decoded_queries':decoded,'pair_scores':pairs,'panels':panels}


def reference_assess(public,oracle,availability,predictions):
    ps={p['case_id']:p for p in predictions['panels']};parents={b['base_id']:b['view_ids']['parent'] for b in oracle['bases']};outcomes=[];paired=[]
    for c in oracle['cases']:
        nom=ps[c['case_id']]['decision']['nominated'];outcome='abstain' if nom is None else 'correct_parent' if nom==c['true_parent_slot'] else 'non_parent'
        outcomes.append({'case_id':c['case_id'],'query_view_id':c['query_view_id'],'group':c['group'],'mechanism':c['mechanism'],'scenario':c['scenario'],
                         'available':availability['availability'][c['query_view_id']]['potentially_available'],'nominated':nom,'outcome':outcome})
    for q in oracle['queries']:
        qid=q['query_view_id'];p=predictions['pair_scores'][qid+'::'+parents[q['base_id']]];pairs=[(a,b) for a,b in p['trace'] if a is not None and b is not None]
        exact=len([1 for a,b in pairs if q['origins'][a]==b])
        paired.append({'query_view_id':qid,'group':q['group'],'mechanism':q['mechanism'],'available':availability['availability'][qid]['potentially_available'],
                       'qualifies':p['qualifies'],'returned_matches':len(pairs),'exact_origin_matches':exact,'optimal_operation_paths':p['optimal_operation_paths']})
    def counts(rows):
        counts=Counter(c['outcome'] for c in rows)
        return {'panels':len(rows),'correct_parent_nominations':counts['correct_parent'],'non_parent_nominations':counts['non_parent'],'abstentions':counts['abstain']}
    grouped={}
    for group in dict.fromkeys(q['group'] for q in oracle['queries']):
        grouped[group]={}
        for mechanism in dict.fromkeys(q['mechanism'] for q in oracle['queries']):
            qs=[q for q in paired if (q['group'],q['mechanism'])==(group,mechanism)];good=[q for q in qs if q['qualifies']]
            cs=[c for c in outcomes if (c['group'],c['mechanism'],c['scenario'])==(group,mechanism,'present')]
            grouped[group][mechanism]={'queries':len(qs),'potentially_available':len([q for q in qs if q['available']]),'parent_pair_qualifications':len(good),
              'present':counts(cs),'qualified_parent_returned_matches':sum(q['returned_matches'] for q in good),'qualified_parent_exact_origin_matches':sum(q['exact_origin_matches'] for q in good),
              'all_parent_returned_matches':sum(q['returned_matches'] for q in qs),'all_parent_exact_origin_matches':sum(q['exact_origin_matches'] for q in qs)}
    scenarios={s:counts([c for c in outcomes if c['scenario']==s]) for s in dict.fromkeys(c['scenario'] for c in outcomes)}
    supported=[c for c in outcomes if c['group']=='seen' and c['mechanism'] in ('bijective','insertion','deletion','reordering')]
    present=[c for c in supported if c['scenario']=='present'];plus=[c for c in supported if c['scenario']=='parent_plus_impostor'];reject=[c for c in outcomes if c['scenario'] in ('absent','impostor_only')]
    unknown=[c for c in outcomes if c['group'] in ('dense_unknown','unseen_key')]
    no_unmapped=True
    for p in predictions['pair_scores'].values():
        for i,j in p['trace']:
            if i is not None and j is not None:
                predicted=predictions['decoded_queries'][p['query_view_id']][i]['source_form'];t=public['views'][p['candidate_view_id']]['tokens'][j]
                assert predicted==t['form'] and not t['blocked'];no_unmapped=no_unmapped and predicted is not None
    req={'all_96_supported_present_recovered':len(present)==96 and counts(present)['correct_parent_nominations']==96,
         'all_96_supported_plus_impostor_recovered':len(plus)==96 and counts(plus)['correct_parent_nominations']==96,
         'zero_non_parent_nominations_in_840_rejections':len(reject)==840 and counts(reject)['abstentions']==840,
         'all_420_duplicate_panels_abstain':scenarios['duplicate_parent']['panels']==420 and scenarios['duplicate_parent']['abstentions']==420,
         'all_900_dense_unknown_and_unseen_key_panels_abstain':len(unknown)==900 and counts(unknown)['abstentions']==900,
         'all_unmapped_tokens_abstain':no_unmapped}
    good=[q for q in paired if q['qualifies']]
    metrics={'by_group_mechanism':grouped,'by_scenario':scenarios,'supported_present':counts(present),'supported_plus_impostor':counts(plus),'rejection_panels':counts(reject),
             'dense_unknown_and_unseen_key':counts(unknown),'unavailable_panels':counts([c for c in outcomes if not c['available']]),
             'qualified_parent_pairs':len(good),'qualified_parent_returned_matches':sum(q['returned_matches'] for q in good),'qualified_parent_exact_origin_matches':sum(q['exact_origin_matches'] for q in good),
             'qualified_parent_pairs_with_multiple_operation_paths':len([q for q in good if q['optimal_operation_paths']>1]),
             'unmapped_query_token_count':sum(1 for rows in predictions['decoded_queries'].values() for t in rows if t['source_form'] is None)}
    return {'case_outcomes':outcomes,'parent_pair_alignment':paired,'metrics':metrics,'synthetic_transfer_gate':{'requirements':req,'passed':all(req.values())}}


def main():
    from verify_correspondence_v6 import check_hashes
    cfg=read('experiments/synthetic_transfer_v32.json');pre=read('data/v32/preflight.json');bench=read('benchmarks/synthetic_transfer_v32.json')
    out=ROOT/'runs/000032_synthetic_transfer';manifest=check_hashes(out)
    for hashes in [cfg['input_hashes'],pre['input_hashes'],pre['code_hashes'],bench['input_hashes']]:
        for p,h in hashes.items():assert sha(p)==h,p
    assert [cfg[k] for k in ['training_passages_per_key','training_cycles','trained_classes','source_classes','test_passages','test_length','barrier_period','minimum_training_units','minimum_matches']]==[2,3,24,32,6,64,17,2,24]
    assert cfg['training_keys']==[11,29,47,83] and cfg['unseen_keys']==[101,131] and cfg['coverage']==[4,5]
    assert cfg['groups']==['seen','sparse_unknown','dense_unknown','unseen_key'] and cfg['mechanisms']==['bijective','insertion','deletion','contextual','reordering']
    assert cfg['scenarios']==['present','absent','impostor_only','parent_plus_impostor','duplicate_parent']
    assert [cfg[k] for k in ['parent_denominator','query_denominator','panel_denominator']]==[84,420,2100]
    assert manifest['code_hashes']==pre['code_hashes']
    tr=read('data/v32/training_receipt.json');fm=read('data/v32/frozen_mapping.json');prep=read('data/v32/test_preparation_receipt.json');pr=read('runs/000032_synthetic_transfer/prediction_receipt.json')
    assert cfg['registered_at_utc']<pre['sealed_at_utc']<tr['prepared_at_utc']<fm['learned_at_utc']<prep['prepared_at_utc']<bench['frozen_at_utc']<manifest['started_at_utc']<pr['predictions_frozen_at_utc']<manifest['finished_at_utc']
    data=reference_training(cfg);assert data==read('data/v32/training.json')
    model=reference_learn(data);assert model==fm['model'] and len(model['entries'])==96
    assert tr['training_sha256']==fm['training_sha256']==sha('data/v32/training.json') and fm['training_receipt_sha256']==sha('data/v32/training_receipt.json')
    assert tr['tests_generated']==0 and tr['units']==8 and prep['pair_alignments_computed']==0
    assert prep['mapping_sha256']==pr['mapping_file_sha256']==sha('data/v32/frozen_mapping.json')
    for p,h in prep['output_hashes'].items():assert sha(p)==h,p
    public,oracle,availability=reference_tests(cfg,model)
    for p,v in [('public_cases',public),('oracle',oracle),('availability',availability)]:assert read('data/v32/'+p+'.json')==v,p
    expected=reference_predict(public,model);assert read('runs/000032_synthetic_transfer/predictions.json')==expected
    assert expected['decoded_queries']==availability['decoded_queries']
    assert pr['oracle_used_for_predictions'] is False and pr['predictions_sha256']==sha('runs/000032_synthetic_transfer/predictions.json')
    payload=hashlib.sha256(json.dumps(model,sort_keys=True).encode()).hexdigest();assert pr['model_payload_sha256_before']==pr['model_payload_sha256_after']==payload
    assert pr['panels']==2100 and pr['pair_alignments']==2520
    assessment=reference_assess(public,oracle,availability,expected);assert read('runs/000032_synthetic_transfer/assessment.json')==assessment
    engineering={'training_model_precedes_tests':True,'mapping_unchanged':True,'all_2100_panels_scored':len(expected['panels'])==2100,
                 'all_2520_pair_paths_accounted':len(expected['pair_scores'])==2520,
                 'all_84_equivalent_and_duplicate_controls':len(availability['equivalence_certificates'])==84 and all(c['anonymous_profile_equal'] and c['duplicate_bytes_equal'] for c in availability['equivalence_certificates'])}
    report=read('runs/000032_synthetic_transfer/report.json')
    assert report=={'experiment_id':cfg['experiment_id'],'engineering_integrity':engineering,'engineering_integrity_passed':all(engineering.values()),
                   'synthetic_transfer_gate_passed':assessment['synthetic_transfer_gate']['passed'],'training_units':8,'mapping_entries':96,'parents':84,'queries':420,'panels':2100,'pair_alignments':2520,
                   'metrics':assessment['metrics'],'scientific_acceptance':None,'semantic_evaluation_metrics':None,'source_identities_admitted':0,'semantic_labels_admitted':0,
                   'independent_reviews_admitted':0,'untouched_test_units_admitted':0,'natural_targets_rescored':0,'new_network_requests':0,'model_executed':False,
                   'scope':'Supervised symbolic mapping transfer and indel alignment on fixed synthetic fixtures; no natural-language admission'}
    preserved=[]
    for p in sorted((ROOT/'runs').glob('*/manifest.json')):
        if p.parent!=out:check_hashes(p.parent);preserved.append(p.parent.name)
    assert len(preserved)==31
    for p in (ROOT/'reports').glob('*_deliverable_seal.json'):
        for n,h in json.loads(p.read_text()).get('deliverable_hashes',{}).items():assert sha(n)==h,n
    receipt={'state':'verified','run_manifest_sha256':sha('runs/000032_synthetic_transfer/manifest.json'),'training_units_verified':8,'mapping_entries_verified':96,
             'parents_verified':84,'queries_verified':420,'panels_verified':2100,'pair_alignments_verified':2520,
             'engineering_integrity_passed':all(engineering.values()),'synthetic_transfer_gate_passed':assessment['synthetic_transfer_gate']['passed'],
             'prior_runs_preserved':preserved,'semantic_labels_admitted':0,'scientific_acceptance':None}
    target=ROOT/'reports/000032_verification.json'
    if target.exists():assert {k:v for k,v in json.loads(target.read_text()).items() if k!='verified_at_utc'}==receipt
    else:
        receipt['verified_at_utc']=datetime.now(timezone.utc).isoformat();target.write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt,indent=2))


if __name__=='__main__':main()
