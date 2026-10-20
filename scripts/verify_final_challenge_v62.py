"""Offline replay of the final batch using alternate native/scope/DP implementations."""
from collections import Counter
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import re
import sys
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from verify_correspondence_v6 import check_hashes
from verify_additional_intake_v55 import capture_check,article
from verify_publisher_intake_v50 import topic
from verify_cohort_scope_v52 import reconstruct as scope_replay
from verify_offline_intake_v54 import observations,decision
from verify_routing_v53 import key,title,reconstruct as route_replay
from verify_panel_scaffold_v56 import representation as rep_replay,assessment as assessment_replay
from verify_native_probe_v60 import replay_headers


def read(p):return json.loads((ROOT/p).read_text())
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def adjusted(raw,receipt,spec,rule,body,scope,checks,route):
    out=decision(raw,receipt,spec,rule,body,scope,checks,route)
    for b in out['og_url_bindings']:
        if b['binding']=='saved_v53_redirect':b['binding']='saved_v62_redirect'
    out.update(route_evidence_origin='v62' if route is not None else None,exposure_status='development_data; all saved search/link exposures retained')
    return out


def main():
    run=ROOT/'runs/000062_final_challenge';check_hashes(run)
    cfg=read('experiments/final_challenge_v62.json');pre=read('data/v62/preflight.json');selection=read('data/v62/selection.json')
    capture_pre=read('data/v62/capture_preflight.json');manifest=read('runs/000062_final_challenge/manifest.json');report=read('runs/000062_final_challenge/report.json')
    for p,h in pre['hashes'].items():assert sha(p)==h,p
    for p,h in cfg['input_hashes'].items():assert pre['hashes'][p]==h
    assert pre['hashes']['experiments/final_challenge_v62.json']==sha('experiments/final_challenge_v62.json')
    assert cfg['registered_at_utc']<pre['sealed_at_utc']<selection['selected_at_utc']<capture_pre['sealed_at_utc']<manifest['finished_at_utc']
    assert cfg['candidate_slots']==cfg['native_route_budget']==cfg['conditional_alias_route_budget']==2
    assert cfg['new_search_request_budget']==0 and cfg['maximum_application_responses']==16 and cfg['stop_after_fixed_batch']
    assert cfg['minimum_window_bag_capacity']==6 and cfg['numeric_window_cap']==11
    old=read('experiments/hard_comparator_v58.json');assert cfg['eligibility_rule']==old['eligibility_rule']
    assert cfg['request_limits']==old['request_limits']|{'user_agent':'FL-Decipher registered final comparator challenge v62'}
    panel=read('experiments/panel_scaffold_v56.json')
    assert cfg['comparison_rule']=={k:panel[k] for k in ['numeric_budget','seed','draws_per_shuffle_family','minimum_shared_numeric_types','control_families']}
    source=read('data/v61/attribution.json');prior=source['exposure_registry'];seen=set();rows=[];selected=[]
    for c in source['cards']:
        k=article(c['resolved_url']) if c['resolved_url'] else None;assert k==c['strict_article_key']
        duplicate=k is not None and k in seen
        if k:seen.add(k)
        topical=topic((c['title'] or '')+'\n'+' '.join(t['text'] for t in c['snippets']))
        reason=('unattributed_card' if not c['structurally_attributed'] else 'invalid_article_url' if not c['strict_url_usable'] else
                'duplicate_returned_url' if duplicate else 'previously_captured_url' if k in prior['captured_article_keys'] else
                'topic_terms_missing' if not topical else 'slot_cap' if len(selected)==2 else 'selected_first_eligible')
        row={'card_index':c['card_index'],'url':c['resolved_url'],'title':c['title'],'article_key':k,'prior_exposure_tags':prior['article_exposures'].get(k,[]),
             'topical':topical,'decision_reason':reason,'nominated':reason=='selected_first_eligible'}
        rows.append(row)
        if row['nominated']:selected.append(row)
    slots=[{'slot_id':f's{i:02d}','nominee':selected[i] if i<len(selected) else None} for i in range(2)]
    assert {k:v for k,v in selection.items() if k!='selected_at_utc'}=={'card_denominator':len(rows),'cards':rows,'occupied_slots':len(selected),'slots':slots}
    assert capture_pre['selection_sha256']==sha('data/v62/selection.json')
    assert capture_pre['requests']==[{'slot_id':s['slot_id'],'url':s['nominee']['url']} for s in slots if s['nominee']]
    left=read('data/v56/target.json')['inventory']['anchors'];target=Counter(r['key'] for r in left if r['kind']=='number')
    results=[];aliases=0;responses=0;expected_natives=[];expected_aliases=[];scored_windows=0
    for slot in slots:
        sid=slot['slot_id'];n=slot['nominee']
        if n is None:
            results.append({'slot_id':sid,'occupied':False,'native_eligible':False,'unmet':['empty_nomination_slot'],
                'capacity':{'qualifying_comparator':False,'status':'empty_slot'},'comparison':None});continue
        expected_natives.append(sid)
        spec={'id':sid,'url':n['url'],'expected_title':re.sub(r'\s+[–—|\-]\s+Physics World\s*$','',n['title']),'v50_ready_unchanged':None}
        assert read(f'data/v62/{sid}_spec.json')==spec
        intent=read(f'data/v62/{sid}_native_intent.json')
        assert intent['capture_preflight_sha256']==sha('data/v62/capture_preflight.json') and intent['url']==spec['url']
        assert capture_pre['sealed_at_utc']<intent['started_at_utc']
        base=f'data/v62/acquisition/{sid}'
        receipt,raw,headers=capture_check(base,spec['url'],sid,cfg['request_limits'],intent['started_at_utc'],manifest['finished_at_utc'])
        responses+=len(replay_headers(headers)['responses'])
        soup=BeautifulSoup(raw,'html.parser')
        for t in soup.select('script,style,noscript,template,svg,canvas'):t.decompose()
        bodies=soup.select('body');body=bodies[0].get_text(' ',strip=True) if len(bodies)==1 else ''
        scope,checks=scope_replay(raw,body,cfg['eligibility_rule']['source_selector']);assert scope==read(f'data/v62/{sid}_scope.json')
        preliminary=adjusted(raw,receipt,spec,cfg['eligibility_rule'],body,scope,checks,None)
        assert preliminary==read(f'data/v62/{sid}_preliminary.json')
        meta=observations(raw);expected=key(spec['url']);canon=[r['value'] for r in meta['urls'] if r['channel']=='canonical'];og=[r['value'] for r in meta['urls'] if r['channel']=='og_url']
        different=list(dict.fromkeys(u for u in og if key(u)!=expected))
        titles_ok={'html_title','og_title','article_headline'}<={r['channel'] for r in meta['titles']} and not meta['json_ld_parse_errors'] and all(title(r['value'])==title(spec['expected_title']) for r in meta['titles'])
        native_ok=bool(receipt['transport_complete'] and expected and key(receipt['final_url'])==expected and canon and all(key(u)==expected for u in canon) and titles_ok)
        observed_permitted=bool(native_ok and len(different)==1 and key(different[0]) is not None)
        observed={'request_url':different[0] if observed_permitted else None,'reason':'one_safe_observed_alternate' if observed_permitted else 'all_og_urls_direct' if og and not different else 'native_identity_or_alternate_unavailable',
                  'observed_og_urls':og,'distinct_noncanonical_values':different,'native_identity_and_titles_pass':native_ok}
        others=all(v for k,v in preliminary['checks'].items() if k!='all_og_urls_bound');permitted=observed_permitted and others
        plan=read(f'data/v62/{sid}_alias_plan.json')
        paths=sorted(str(p.relative_to(ROOT)) for p in (ROOT/base).iterdir() if p.is_file())
        assert plan['native_input_hashes']=={p:sha(p) for p in paths}
        assert receipt['finished_at_utc']<=plan['sealed_at_utc']<manifest['finished_at_utc']
        assert {k:v for k,v in plan.items() if k not in ['sealed_at_utc','native_input_hashes']}=={'observed_alias_plan':observed,'all_other_native_checks_pass':others,
            'request_url':observed['request_url'] if permitted else None,'reason':'sole_unbound_og_url_can_be_checked' if permitted else 'no_alias_needed_or_other_native_gate_failed'}
        route=None
        if permitted:
            expected_aliases.append(sid);aliases+=1
            rs={'id':sid,'og_url':observed['request_url'],'canonical_url':spec['url'],'expected_title':spec['expected_title'],'old_body_sha256':hashlib.sha256(raw).hexdigest(),'v50_ready_unchanged':None}
            assert rs==read(f'data/v62/{sid}_route_spec.json')
            ai=read(f'data/v62/{sid}_alias_intent.json');assert ai['alias_plan_sha256']==sha(f'data/v62/{sid}_alias_plan.json') and ai['url']==rs['og_url'] and ai['started_at_utc']>plan['sealed_at_utc']
            ar,ab,ah=capture_check(f'data/v62/alias_acquisition/{sid}',rs['og_url'],sid,cfg['request_limits'],ai['started_at_utc'],manifest['finished_at_utc'])
            route=route_replay(ab,ah,ar,rs);assert route==read(f'data/v62/{sid}_route.json');responses+=len(replay_headers(ah)['responses'])
        native=adjusted(raw,receipt,spec,cfg['eligibility_rule'],body,scope,checks,route);assert native==read(f'data/v62/{sid}_decision.json')
        rep=rep_replay(scope) if native['development_capture_eligible'] else None;assert rep==read(f'data/v62/{sid}_representation.json')
        screen={'status':'not_evaluated_native_ineligible','numeric_representation_available':None,'numeric_anchor_count':None,'numeric_budget':11,
            'minimum_window_bag_capacity':6,'windows':None,'maximum_window_bag_capacity':None,'meets_capacity_requirement':None,'qualifying_comparator':False}
        if native['development_capture_eligible']:
            available=rep is not None and rep['available'];screen['numeric_representation_available']=available
            if not available:screen.update(status='representation_unavailable',meets_capacity_requirement=False)
            else:
                nums=[r for r in rep['inventory']['anchors'] if r['kind']=='number'];width=min(len(nums),11);windows=[]
                for start in range(len(nums)-width+1):
                    part=nums[start:start+width];counts=Counter(r['key'] for r in part)
                    windows.append({'numeric_span':[start,start+width],'anchor_indices':[r['anchor_index'] for r in part],'bag_capacity':sum(min(counts[k],target[k]) for k in target)})
                maximum=max(w['bag_capacity'] for w in windows)
                screen.update(status='evaluated',numeric_anchor_count=len(nums),windows=windows,maximum_window_bag_capacity=maximum,meets_capacity_requirement=maximum>=6,qualifying_comparator=maximum>=6)
        assert screen==read(f'data/v62/{sid}_capacity.json')
        comparison=None
        if screen['qualifying_comparator']:
            a=assessment_replay(left,rep,cfg['comparison_rule']);v=a['observed']['capped_scan']['maximum_lcs'];functional=a['functional_checks_passed']
            comparison={'assessment':a,'reference_score_unchanged':6,'reference_strictly_exceeds_candidate':6>v if functional else None,'candidate_ties_reference':v==6 if functional else None,'candidate_exceeds_reference':v>6 if functional else None}
            scored_windows+=a['observed']['capped_scan']['window_count']+sum(c['capped_scan']['window_count'] for c in a['controls'])
        assert comparison==read(f'data/v62/{sid}_comparison.json')
        results.append({'slot_id':sid,'occupied':True,'url':spec['url'],'http_status':receipt['http_status'],'curl_returncode':receipt['curl_returncode'],
            'native_eligible':native['development_capture_eligible'],'unmet':native['unmet'],'publication_dates':native['parsed_publication_dates'],'alias_attempted':route is not None,
            'paragraph_runs':native['paragraph_run_count'],'paragraph_run_characters':native['paragraph_run_characters'],'capacity':screen,'comparison':comparison})
    capable=[s for s in results if s['capacity']['qualifying_comparator']];compared=[s for s in capable if s['comparison'] is not None]
    functional=bool(compared) and len(compared)==len(capable) and all(s['comparison']['assessment']['functional_checks_passed'] for s in compared)
    expected={'experiment_id':'final_challenge_v62','nomination_slot_denominator':2,'occupied_slots':len(selected),'empty_slots':2-len(selected),
        'native_eligible_candidates':sum(s['native_eligible'] for s in results),'capacity_screens_evaluated':sum(s['capacity']['status']=='evaluated' for s in results),
        'qualifying_comparators':len(capable),'registered_feasibility_gate':bool(capable),'both_slots_qualified':len(capable)==2,'comparisons_evaluated':len(compared),
        'reference_specificity_gate_among_capable':all(s['comparison']['reference_strictly_exceeds_candidate'] for s in compared) if functional else None,
        'closure':'closed_after_fixed_comparison' if capable else 'closed_feasibility_limited','discovery_route_closed':True,'additional_batches_authorized':0,
        'new_search_requests':0,'pagination_requests':0,'source_identities_admitted':0,'opaque_meanings_admitted':0,'independent_reviews_admitted':0,'untouched_test_units_admitted':0,
        'natural_benchmark_capacity_met':False,'previous_results_preserved':True,'slot_results':results,'native_routes_attempted':len(selected),'conditional_alias_routes_attempted':aliases,
        'recorded_application_responses':responses,'maximum_application_responses':16,'minimum_window_bag_capacity':6,'numeric_window_cap':11,'reference_score_unchanged':6,
        'reference_assessment_sha256':sha('data/v56/reference_v42_assessment.json')}
    assert report==expected and responses<=16
    for folder,ids in [('acquisition',expected_natives),('alias_acquisition',expected_aliases)]:
        path=ROOT/'data/v62'/folder;assert sorted(p.name for p in path.iterdir())==ids if path.exists() else not ids
    assert not (ROOT/'data/v62/discovery').exists()
    previous=[]
    for p in sorted((ROOT/'runs').glob('0000*/manifest.json')):
        if p.parent==run:continue
        assert int(p.parent.name.split('_')[0])<=61;check_hashes(p.parent);previous.append(p.parent.name)
    assert len(previous)==61
    for p in (ROOT/'reports').glob('*_deliverable_seal.json'):
        for name,h in json.loads(p.read_text()).get('deliverable_hashes',{}).items():assert sha(name)==h,name
    result={'state':'verified','manifest_sha256':sha('runs/000062_final_challenge/manifest.json'),'selection_native_gates_alias_condition_and_closure_replayed':True,
        'slot_denominator':2,'occupied_slots':len(selected),'native_routes':len(selected),'alias_routes':aliases,'application_responses':responses,
        'qualifying_comparators':len(capable),'numeric_capacity_screens_evaluated':expected['capacity_screens_evaluated'],'full_table_dp_windows_verified':scored_windows,
        'closure':expected['closure'],'production_v62_functions_not_imported':True,'shared_html_parser':'BeautifulSoup html.parser',
        'verification_network_requests':0,'independent_scientific_review':False,'semantics_or_source_identity_validated':False,'prior_runs_preserved':previous}
    out=ROOT/'reports/000062_verification.json'
    if out.exists():assert {k:v for k,v in json.loads(out.read_text()).items() if k!='verified_at_utc'}==result
    else:
        with out.open('x') as f:json.dump(result|{'verified_at_utc':datetime.now(timezone.utc).isoformat()},f,indent=2);f.write('\n')
    print(json.dumps({k:v for k,v in result.items() if k!='prior_runs_preserved'}|{'prior_runs_preserved':len(previous)},indent=2))


if __name__=='__main__':main()
