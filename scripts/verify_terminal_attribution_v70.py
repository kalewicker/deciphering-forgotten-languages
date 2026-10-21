"""Replay the observed terminal batch without importing production v70 functions."""
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import re
import sys
from fl_decipher.dated_capture_scope_v38 import literal_hits,normalized
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from verify_correspondence_v6 import check_hashes
from verify_quotation_attribution_v69 import safe

def read(p):return json.loads((ROOT/p).read_text())
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()


def main():
    run=ROOT/'runs/000070_terminal_attribution';check_hashes(run)
    cfg=read('experiments/terminal_attribution_v70.json');pre=read('data/v70/preflight.json');manifest=read('runs/000070_terminal_attribution/manifest.json')
    for p,h in pre['hashes'].items():assert sha(p)==h,p
    for p,h in cfg['input_hashes'].items():assert pre['hashes'][p]==h
    assert pre['hashes']['experiments/terminal_attribution_v70.json']==sha('experiments/terminal_attribution_v70.json')
    assert read('runs/000069_quotation_attribution/manifest.json')['finished_at_utc']<cfg['registered_at_utc']<pre['sealed_at_utc']<manifest['finished_at_utc']
    assert cfg['search_call_budget']==4 and cfg['native_route_budget']==2 and cfg['tool']=='web.run'
    assert cfg['request_limits']=={'connect_timeout_seconds':8,'total_timeout_seconds':30,'max_redirects':0,'max_body_bytes':20971520,'user_agent':'FL-Decipher registered terminal attribution batch v70'}
    assert cfg['maximum_pdf_pages']==200 and cfg['maximum_source_characters']==1000000
    inv=read(cfg['target_inventory']);body=read(cfg['target_export'])['text'];targets=[]
    for bid,rid,span,count in [(3,6,[1140,1543],60),(5,8,[2315,2626],48)]:
        b=inv['blocks'][bid];assert b['block_id']==bid and b['run_id']==rid and b['body_span']==span and body[slice(*span)]==b['text'] and len(b['text'].split())==count
        words=b['text'].split();phrases=[' '.join(words[:12]),' '.join(words[-12:])]
        targets.append({'slot_id':f'b{bid:02d}','block_id':bid,'run_id':rid,'body_span':span,'text':b['text'],'text_sha256':hashlib.sha256(b['text'].encode()).hexdigest(),
            'token_count':count,'phrases':phrases,'requests':[{'search_query':[{'q':'"'+q+'"'}],'response_length':'long'} for q in phrases]})
    batch={'targets':targets,'selection_after_prior_exposure':True,
        'block_ledger':[{'block_id':b['block_id'],'run_id':b['run_id'],'body_span':b['body_span'],'selected':b['block_id'] in [3,5],
            'reason':'fixed_next_exposed_English_block' if b['block_id'] in [3,5] else 'earlier_closed_E69_target' if b['block_id']==1 else 'not_registered_target'} for b in inv['blocks']],
        'requests':[r for t in targets for r in t['requests']]}
    assert read('data/v70/targets.json')==batch and cfg['search_requests']==batch['requests']
    known={safe(u) for u in read(cfg['known_exposure'])['urls']};slots=[];all_finishes=[];all_counts=[];all_markers=[];all_supported=[];typed_witnesses=0
    for ti,t in enumerate(targets):
        seen=set();calls=[];selected=None
        for local in range(2):
            qi=ti*2+local;intent=read(f'data/v70/search/intent{qi}.json');saved=read(f'data/v70/search/response{qi}.json')
            assert intent['query_index']==saved['query_index']==qi and intent['tool']==saved['tool']=='web.run'
            assert intent['request_arguments']==saved['request_arguments']==batch['requests'][qi]
            start=datetime.strptime(saved['started_at_utc'],'%Y-%m-%d %H:%M:%S UTC').replace(tzinfo=timezone.utc);finish=datetime.strptime(saved['finished_at_utc'],'%Y-%m-%d %H:%M:%S UTC').replace(tzinfo=timezone.utc)
            assert datetime.fromisoformat(pre['sealed_at_utc'])<datetime.fromisoformat(intent['started_at_utc'])<=start<=finish<datetime.fromisoformat(manifest['finished_at_utc'])
            all_finishes.append(finish);assert saved['error'] is None and isinstance(saved['response'],str)
            text=saved['response'];lines=text.splitlines(keepends=True);headers=[];offset=0
            for i,line in enumerate(lines):
                line0=line.rstrip('\r\n');separator=line0.rfind(' (http')
                if separator>0 and line0.endswith(')') and i+1<len(lines) and 'wordlim' in lines[i+1]:
                    url=line0[separator+2:-1]
                    if not any(c.isspace() for c in url):headers.append((offset,line0[:separator],url))
                offset+=len(line)
            markers=len(re.findall(r'\[wordlim(?::|\s)',text));supported=markers==len(headers);entries=[]
            for rank,(begin,title,original) in enumerate(headers):
                end=headers[rank+1][0] if rank+1<len(headers) else len(text);block=text[begin:end]
                snippet_start=sum(len(v) for v in block.splitlines(keepends=True)[:2]);snippet=block[snippet_start:]
                def guarded(query):
                    needle=normalized(query);hay=normalized(snippet);out=[]
                    for h in literal_hits(query,snippet):
                        a,b=h['normalized_span']
                        if re.match(r'\w',needle[0]) and a and re.match(r'\w',hay[a-1]):continue
                        if re.match(r'\w',needle[-1]) and b<len(hay) and re.match(r'\w',hay[b]):continue
                        out.append(h)
                    return out
                phrase=guarded(t['phrases'][local]);full=guarded(t['text']);url=safe(original);host=urlsplit_host(url)
                echo=bool('forgottenlanguages' in host or host.endswith(('.blogspot.com','.blogger.com')) or host in ['blogspot.com','blogger.com'] or normalized(cfg['echo_title_prefix']) in normalized(block) or 'quantum-semantic-fields-and-universals' in block.casefold())
                duplicate=bool(url and url in seen)
                if url:seen.add(url)
                eligible=bool(supported and url and phrase and not echo and not duplicate)
                reason='unsupported_response_boundaries' if not supported else 'unsafe_or_non_https_url' if url is None else 'recognizable_fl_echo' if echo else 'duplicate_returned_url' if duplicate else 'registered_query_phrase_not_visible' if not phrase else 'native_slot_already_filled' if selected else 'selected_first_eligible_query_phrase_lead'
                witnesses=[]
                for kind,hits in [('registered_query_phrase',phrase),('complete_target',full)]:
                    for h in hits:
                        w={'kind':kind,**h,'source_span':[snippet_start+h['source_span'][0],snippet_start+h['source_span'][1]],'normalized_coordinate_scope':'snippet_after_two_header_lines',
                            'response_span':[begin+snippet_start+h['source_span'][0],begin+snippet_start+h['source_span'][1]]}
                        assert text[slice(*w['response_span'])]==w['source_quote'];witnesses.append(w);typed_witnesses+=1
                entries.append({'rank':rank,'title':title,'url':original,'response_span':[begin,end],'response_text':block,'response_text_sha256':hashlib.sha256(block.encode()).hexdigest(),
                    'snippet_span':[snippet_start,len(block)],'capture_url':url,'query_phrase_visible':bool(phrase),'complete_target_visible':bool(full),'witnesses':witnesses,
                    'recognizable_fl_echo':echo,'duplicate_returned_url':duplicate,'recorded_url_in_frozen_registry':bool(url and url in known),'eligible_query_phrase_lead':eligible,'decision_reason':reason,'nominated':reason=='selected_first_eligible_query_phrase_lead'})
                if reason=='selected_first_eligible_query_phrase_lead':selected={'query_index':local,'rank':rank,'url':url,'original_returned_url':original,'title':title,'complete_target_visible_in_discovery':bool(full)}
            calls.append({'query_index':local,'response_text':text,'response_text_sha256':hashlib.sha256(text.encode()).hexdigest(),'response_format_supported':supported,'wordlim_marker_count':markers,'attributable_hits':len(headers),'hits':entries})
            all_counts.append(len(headers));all_markers.append(markers);all_supported.append(supported)
        assert selected is None
        led={'calls':calls,'selected':None,'search_call_denominator':2,'native_slot_denominator':1,'search_engine_exact_matching_observable':False,'independence_or_untouched_status_established':False,'source_identity_admitted':False}
        slots.append({'slot_id':t['slot_id'],'block_id':t['block_id'],'global_query_indices':[ti*2,ti*2+1],'ledger':led,'capture_owner_slot':None,'reuses_capture':False})
    selection=read('data/v70/selection.json');stamp=datetime.fromisoformat(selection['selected_at_utc']);assert all(f<stamp for f in all_finishes)
    assert selection=={'selected_at_utc':selection['selected_at_utc'],'slots':slots,'native_slot_denominator':2,'unique_capture_urls':[],'maximum_unique_captures':2}
    assert all_counts==[12,11,12,4] and all_markers==[12,12,12,4] and all_supported==[True,False,True,True]
    # Preserve the titleless URL result; do not infer a title or repair the gate.
    response1=read('data/v70/search/response1.json')['response']
    assert '\n (https://www.raptureofchurch.com/MoodyBibleCommentary/OldTestament/Genesis.htm)\n' in response1
    cap=read('data/v70/capture_preflight.json');assert stamp<datetime.fromisoformat(cap['sealed_at_utc']) and cap['capture_urls']==[]
    for p,h in cap['hashes'].items():assert sha(p)==h
    rows=[{'slot_id':t['slot_id'],'block_id':t['block_id'],'source_available':False,'presence':None,'pdf_visual_gate_passed':None,'complete_target_criterion_passed':False} for t in targets]
    assert read('data/v70/native_export.json')=={'sources':{},'slots_machine_assessments':rows} and read('data/v70/slot_outcomes.json')==rows
    assert not (ROOT/'data/v70/acquisition').exists() and not (ROOT/'data/v70/b03_intent.json').exists() and not (ROOT/'data/v70/b05_intent.json').exists()
    report={'experiment_id':'terminal_attribution_v70','development_selection_after_prior_exposure':True,'terminal_batch':True,'target_blocks':[3,5],
        'search_tool_calls':4,'search_call_denominator':4,'attributable_hits_per_call':all_counts,'native_slot_denominator':2,'native_routes_attempted':0,'native_application_responses':0,
        'slot_results':[{'slot_id':t['slot_id'],'block_id':t['block_id'],'selected':None,'capture_owner_slot':None,'reuses_capture':False,'source_available':False,'complete_target_visible':None,'native_controls_passed':None,'complete_target_criterion_passed':False} for t in targets],
        'native_complete_target_successes':0,'wording_discovery_route_closed':True,'outcome':'closed_feasibility_limited','opaque_source_identity_or_meaning_admitted':False,
        'extra_search_or_source_requests':0,'original_quote_author_authenticated':False,'publication_year_wording_authenticated':False,'new_connected_works_confirmed':0,
        'independent_reviews_admitted':0,'untouched_test_units_admitted':0,'natural_benchmark_capacity_met':False,'e69_no_external_lead_preserved':True,'e68_negative_result_preserved':True,
        'e66_metadata_gate_preserved_value':False,'historical_e63_gate_value':False,'anita_route_reopened':False}
    assert read('runs/000070_terminal_attribution/report.json')==report
    assert sorted(p.name for p in (ROOT/'data/v70/search').iterdir())==[f'intent{i}.json' for i in range(4)]+[f'response{i}.json' for i in range(4)]
    actual={str(p.relative_to(ROOT)) for p in (ROOT/'data/v70').rglob('*') if p.is_file()};recorded={str((run/p).resolve().relative_to(ROOT)) for p in manifest['output_hashes'] if p.startswith('../../data/v70/')};assert actual==recorded
    assert read('runs/000069_quotation_attribution/report.json')['outcome']=='no_eligible_external_lead'
    old=read('runs/000068_passage_presence/report.json');assert old['primary_queries_present']==old['secondary_queries_present']==0
    assert read('data/v66/metadata_assessment.json')['passed'] is False and read('data/v63/target_gate.json')['passed'] is False
    prior=[]
    for p in sorted((ROOT/'runs').glob('0000*/manifest.json')):
        if p.parent==run:continue
        assert int(p.parent.name.split('_')[0])<=69;check_hashes(p.parent);prior.append(p.parent.name)
    assert len(prior)==69
    for p in (ROOT/'reports').glob('*_deliverable_seal.json'):
        for name,h in json.loads(p.read_text()).get('deliverable_hashes',{}).items():assert sha(name)==h,name
    result={'state':'verified','manifest_sha256':sha('runs/000070_terminal_attribution/manifest.json'),
        'fixed_blocks_four_requests_all_parsed_boundaries_witnesses_empty_slots_and_terminal_closure_replayed':True,'production_v70_functions_not_imported':True,
        'shared_components':['sealed E38 literal_hits and normalization','sealed independent E69 URL-safety replay'],
        'recorded_search_calls':4,'search_call_denominator':4,'parsed_result_rows_per_call':all_counts,'wordlim_markers_per_call':all_markers,'response_formats_supported':all_supported,
        'parsed_header_rows':sum(all_counts),'rows_in_supported_responses':sum(n for n,s in zip(all_counts,all_supported) if s),
        'titleless_result_header_preserved_without_repair':True,'typed_witnesses_verified':typed_witnesses,'native_slot_denominator':2,'native_routes_attempted':0,
        'native_controls_not_run':True,'terminal_outcome':'closed_feasibility_limited','wording_discovery_route_closed':True,
        'archived_output_files':len(actual),'verification_network_requests':0,'independent_scientific_review':False,'semantics_or_source_identity_validated':False,'prior_runs_preserved':prior}
    out=ROOT/'reports/000070_verification.json'
    if out.exists():assert {k:v for k,v in read(str(out.relative_to(ROOT))).items() if k!='verified_at_utc'}==result
    else:
        with out.open('x') as f:json.dump(result|{'verified_at_utc':datetime.now(timezone.utc).isoformat()},f,indent=2);f.write('\n')
    print(json.dumps({k:v for k,v in result.items() if k!='prior_runs_preserved'}|{'prior_runs_preserved':len(prior)},indent=2))


def urlsplit_host(url):
    from urllib.parse import urlsplit
    return (urlsplit(url).hostname or '') if url else ''


if __name__=='__main__':main()
