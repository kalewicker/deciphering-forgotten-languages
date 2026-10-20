"""Freeze, nominate, capture/check/compare, then close this discovery route."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
from fl_decipher.final_challenge_v62 import nominate,conditional_alias,capacity,compare,closeout
from fl_decipher.additional_intake_v55 import body_text
from fl_decipher.offline_intake_v54 import evaluate
from fl_decipher.panel_scaffold_v56 import representation
from fl_decipher.cohort_scope_v52 import extract_scope
from fl_decipher.routing_v53 import capture,assess,header_blocks
from fl_decipher.publisher_intake_v50 import service_title

ROOT=Path(__file__).resolve().parents[1]
CFG='experiments/final_challenge_v62.json'
RUN='runs/000062_final_challenge'
CODE=['src/fl_decipher/final_challenge_v62.py','scripts/final_challenge_v62.py','tests/test_final_challenge_v62.py']


def utc():return datetime.now(timezone.utc).isoformat()
def read(p):return json.loads((ROOT/p).read_text())
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def write(p,obj):
    path=ROOT/p;path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x') as f:json.dump(obj,f,indent=2,ensure_ascii=False);f.write('\n')
def bytes_if(p):return (ROOT/p).read_bytes() if (ROOT/p).exists() else b''
def native(raw,receipt,spec,rule,route=None):
    out=evaluate(raw,receipt,spec,rule,body_text(raw),route)
    for binding in out['og_url_bindings']:
        if binding['binding']=='saved_v53_redirect':binding['binding']='saved_v62_redirect'
    out['route_evidence_origin']='v62' if route is not None else None
    out['exposure_status']='development_data; all saved search/link exposures retained'
    return out


def main():
    parser=argparse.ArgumentParser();parser.add_argument('phase',choices=['prepare','select','execute']);args=parser.parse_args();cfg=read(CFG)
    if args.phase=='prepare':
        assert not (ROOT/'data/v62').exists() and not (ROOT/RUN).exists()
        for p,h in cfg['input_hashes'].items():assert sha(p)==h,p
        assert cfg['new_search_request_budget']==0 and cfg['candidate_slots']==2
        write('data/v62/preflight.json',{'sealed_at_utc':utc(),'hashes':cfg['input_hashes']|{p:sha(p) for p in CODE+[CFG]}})
        print(json.dumps({'state':'prepared','candidate_slots':2,'new_search_requests':0,'maximum_native_routes':2,'maximum_conditional_alias_routes':2}));return
    for p,h in read('data/v62/preflight.json')['hashes'].items():assert sha(p)==h,p
    if args.phase=='select':
        result=nominate(read('data/v61/attribution.json'))
        write('data/v62/selection.json',{'selected_at_utc':utc(),**result});print(json.dumps(result,indent=2));return
    selection=read('data/v62/selection.json');assert not (ROOT/RUN).exists()
    assert not (ROOT/'data/v62/capture_preflight.json').exists() and not (ROOT/'data/v62/acquisition').exists()
    write('data/v62/capture_preflight.json',{'sealed_at_utc':utc(),'selection_sha256':sha('data/v62/selection.json'),
        'requests':[{'slot_id':s['slot_id'],'url':s['nominee']['url']} for s in selection['slots'] if s['nominee']]})
    target=read('data/v56/target.json')['inventory']['anchors'];slots=[];aliases=0
    for slot in selection['slots']:
        sid=slot['slot_id'];nominee=slot['nominee']
        if nominee is None:
            slots.append({'slot_id':sid,'occupied':False,'native_eligible':False,'unmet':['empty_nomination_slot'],
                'capacity':{'qualifying_comparator':False,'status':'empty_slot'},'comparison':None});continue
        spec={'id':sid,'url':nominee['url'],'expected_title':service_title(nominee['title']),'v50_ready_unchanged':None}
        write(f'data/v62/{sid}_spec.json',spec)
        write(f'data/v62/{sid}_native_intent.json',{'started_at_utc':utc(),'url':spec['url'],'capture_preflight_sha256':sha('data/v62/capture_preflight.json')})
        receipt=capture(ROOT/'data/v62/acquisition',{'id':sid,'og_url':spec['url']},cfg['request_limits'])
        base=f'data/v62/acquisition/{sid}';raw=bytes_if(base+'/body.bin')
        try:scope=extract_scope(raw,body_text(raw),cfg['eligibility_rule']['source_selector'])
        except (ValueError,AssertionError):scope=None
        write(f'data/v62/{sid}_scope.json',scope)
        preliminary=native(raw,receipt,spec,cfg['eligibility_rule']);write(f'data/v62/{sid}_preliminary.json',preliminary)
        plan=conditional_alias(raw,receipt,spec,preliminary)
        inputs=sorted(str(p.relative_to(ROOT)) for p in (ROOT/base).iterdir() if p.is_file())
        write(f'data/v62/{sid}_alias_plan.json',{'sealed_at_utc':utc(),'native_input_hashes':{p:sha(p) for p in inputs},**plan})
        route=None
        if plan['request_url'] is not None:
            route_spec={'id':sid,'og_url':plan['request_url'],'canonical_url':spec['url'],'expected_title':spec['expected_title'],
                'old_body_sha256':hashlib.sha256(raw).hexdigest(),'v50_ready_unchanged':None}
            write(f'data/v62/{sid}_route_spec.json',route_spec)
            write(f'data/v62/{sid}_alias_intent.json',{'started_at_utc':utc(),'url':plan['request_url'],'alias_plan_sha256':sha(f'data/v62/{sid}_alias_plan.json')})
            ar=capture(ROOT/'data/v62/alias_acquisition',{'id':sid,'og_url':plan['request_url']},cfg['request_limits']);ab=f'data/v62/alias_acquisition/{sid}'
            route=assess(bytes_if(ab+'/body.bin'),bytes_if(ab+'/headers.txt'),ar,route_spec)
            write(f'data/v62/{sid}_route.json',route);aliases+=1
        decision=native(raw,receipt,spec,cfg['eligibility_rule'],route);write(f'data/v62/{sid}_decision.json',decision)
        rep=representation(scope) if decision['development_capture_eligible'] and scope is not None else None
        screen=capacity(decision,rep,target);comparison=compare(target,rep,screen,cfg['comparison_rule'])
        write(f'data/v62/{sid}_representation.json',rep);write(f'data/v62/{sid}_capacity.json',screen);write(f'data/v62/{sid}_comparison.json',comparison)
        row={'slot_id':sid,'occupied':True,'url':spec['url'],'http_status':receipt['http_status'],'curl_returncode':receipt['curl_returncode'],
            'native_eligible':decision['development_capture_eligible'],'unmet':decision['unmet'],'publication_dates':decision['parsed_publication_dates'],
            'alias_attempted':route is not None,'paragraph_runs':decision['paragraph_run_count'],'paragraph_run_characters':decision['paragraph_run_characters'],
            'capacity':screen,'comparison':comparison}
        slots.append(row);print(json.dumps(row),flush=True)
    responses=sum(len(header_blocks(p.read_bytes())['responses']) for p in (ROOT/'data/v62').rglob('headers.txt'))
    report=closeout(slots)|{'slot_results':slots,'native_routes_attempted':selection['occupied_slots'],'conditional_alias_routes_attempted':aliases,
        'recorded_application_responses':responses,'maximum_application_responses':16,'minimum_window_bag_capacity':6,'numeric_window_cap':11,
        'reference_score_unchanged':6,'reference_assessment_sha256':sha('data/v56/reference_v42_assessment.json')}
    assert responses<=16 and aliases<=2
    write(RUN+'/report.json',report)
    files=sorted(str(p.relative_to(ROOT)) for p in (ROOT/'data/v62').rglob('*') if p.is_file())
    write(RUN+'/manifest.json',{'experiment_id':'final_challenge_v62','state':'completed','finished_at_utc':utc(),
        'input_hashes':cfg['input_hashes']|{CFG:sha(CFG)},'code_hashes':{p:sha(p) for p in CODE},
        'output_hashes':{'report.json':sha(RUN+'/report.json')}|{str(Path('../../')/p):sha(p) for p in files},'verifier_written_after_batch':True})
    print(json.dumps({k:v for k,v in report.items() if k!='slot_results'},indent=2))


if __name__=='__main__':main()
