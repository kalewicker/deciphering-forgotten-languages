"""Replay E69's recorded two searches and empty native slot; zero network calls."""
from datetime import datetime,timezone
import hashlib
import ipaddress
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit,urlunsplit
from fl_decipher.dated_capture_scope_v38 import literal_hits,normalized
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from verify_correspondence_v6 import check_hashes

def read(p):return json.loads((ROOT/p).read_text())
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def safe(url):
    try:
        p=urlsplit(url);host=p.hostname
        if p.scheme!='https' or not host or p.username is not None or p.password is not None or p.port not in [None,443] or any(c.isspace() for c in url):return None
        if host=='localhost' or '.' not in host or host.endswith(('.localhost','.local','.internal')):return None
        try:
            if not ipaddress.ip_address(host).is_global:return None
        except ValueError:pass
        return urlunsplit((p.scheme,p.netloc,p.path,p.query,''))
    except (ValueError,TypeError):return None


def main():
    run=ROOT/'runs/000069_quotation_attribution';check_hashes(run)
    cfg=read('experiments/quotation_attribution_v69.json');pre=read('data/v69/preflight.json');manifest=read('runs/000069_quotation_attribution/manifest.json')
    for p,h in pre['hashes'].items():assert sha(p)==h,p
    for p,h in cfg['input_hashes'].items():assert pre['hashes'][p]==h
    assert pre['hashes']['experiments/quotation_attribution_v69.json']==sha('experiments/quotation_attribution_v69.json')
    assert read('runs/000068_passage_presence/manifest.json')['finished_at_utc']<cfg['registered_at_utc']<pre['sealed_at_utc']<manifest['finished_at_utc']
    assert cfg['tool']=='web.run' and cfg['search_call_budget']==2 and cfg['native_route_budget']==1
    assert cfg['request_limits']=={'connect_timeout_seconds':8,'total_timeout_seconds':30,'max_redirects':0,'max_body_bytes':20971520,'user_agent':'FL-Decipher registered quote-attribution pilot v69'}
    assert cfg['maximum_pdf_pages']==200 and cfg['maximum_source_characters']==1000000
    inventory=read(cfg['target_inventory']);block=inventory['blocks'][1];body=read(cfg['target_export'])['text']
    assert block['block_id']==1 and block['run_id']==4 and block['body_span']==[790,915] and body[790:915]==block['text'] and len(block['text'].split())==18
    phrases=[block['text'],' '.join(block['text'].split()[:12])]
    requests=[{'search_query':[{'q':'"'+p+'"'}],'response_length':'long'} for p in phrases]
    target={'block_id':1,'run_id':4,'body_span':[790,915],'text':block['text'],'text_sha256':hashlib.sha256(block['text'].encode()).hexdigest(),
        'selection_after_prior_exposure':True,'selection_ledger':[{'block_id':b['block_id'],'run_id':b['run_id'],'body_span':b['body_span'],'selected':b['block_id']==1,
            'reason':'fixed_first_previously_exposed_English_block' if b['block_id']==1 else 'not_registered_target'} for b in inventory['blocks']],
        'phrases':phrases,'requests':requests}
    assert read('data/v69/target.json')==target and cfg['search_requests']==requests
    known={safe(u) for u in read(cfg['known_exposure'])['urls']};seen=set();calls=[];selected=None
    finish_times=[];witness_count=0
    for qi in range(2):
        intent=read(f'data/v69/search/intent{qi}.json');saved=read(f'data/v69/search/response{qi}.json')
        assert intent['query_index']==saved['query_index']==qi and intent['tool']==saved['tool']=='web.run'
        assert intent['request_arguments']==saved['request_arguments']==requests[qi]
        start=datetime.strptime(saved['started_at_utc'],'%Y-%m-%d %H:%M:%S UTC').replace(tzinfo=timezone.utc)
        finish=datetime.strptime(saved['finished_at_utc'],'%Y-%m-%d %H:%M:%S UTC').replace(tzinfo=timezone.utc)
        assert datetime.fromisoformat(pre['sealed_at_utc'])<datetime.fromisoformat(intent['started_at_utc'])<=start<=finish<datetime.fromisoformat(manifest['finished_at_utc'])
        finish_times.append(finish)
        assert saved['error'] is None and isinstance(saved['response'],str)
        text=saved['response'];lines=text.splitlines(keepends=True);headers=[];offset=0
        for i,line in enumerate(lines):
            stripped=line.rstrip('\r\n');marker=stripped.rfind(' (http')
            if marker>=0 and stripped.endswith(')') and i+1<len(lines) and 'wordlim' in lines[i+1]:
                title=stripped[:marker];url=stripped[marker+2:-1]
                assert not any(c.isspace() for c in url)
                headers.append((offset,title,url))
            offset+=len(line)
        marker_count=len(re.findall(r'\[wordlim(?::|\s)',text));supported=marker_count==len(headers);assert supported
        entries=[]
        for rank,(begin,title,original) in enumerate(headers):
            end=headers[rank+1][0] if rank+1<len(headers) else len(text);result_text=text[begin:end]
            snippet_start=sum(len(line) for line in result_text.splitlines(keepends=True)[:2]);snippet=result_text[snippet_start:]
            def guarded(query):
                needle=normalized(query);hay=normalized(snippet);out=[]
                for h in literal_hits(query,snippet):
                    a,b=h['normalized_span']
                    if re.match(r'\w',needle[0]) and a and re.match(r'\w',hay[a-1]):continue
                    if re.match(r'\w',needle[-1]) and b<len(hay) and re.match(r'\w',hay[b]):continue
                    out.append(h)
                return out
            ph=guarded(phrases[qi]);full=guarded(block['text']);url=safe(original);host=urlsplit(url).hostname if url else ''
            echo=bool('forgottenlanguages' in host or host.endswith(('.blogspot.com','.blogger.com')) or host in ['blogspot.com','blogger.com']
                or normalized(cfg['echo_title_prefix']) in normalized(result_text) or 'quantum-semantic-fields-and-universals' in result_text.casefold())
            duplicate=bool(url and url in seen)
            if url:seen.add(url)
            eligible=bool(supported and url and ph and not echo and not duplicate)
            reason='unsupported_response_boundaries' if not supported else 'unsafe_or_non_https_url' if url is None else 'recognizable_fl_echo' if echo else 'duplicate_returned_url' if duplicate else 'registered_query_phrase_not_visible' if not ph else 'native_slot_already_filled' if selected else 'selected_first_eligible_query_phrase_lead'
            witnesses=[]
            for kind,hits in [('registered_query_phrase',ph),('complete_target',full)]:
                for h in hits:
                    w={'kind':kind,**h,'source_span':[snippet_start+h['source_span'][0],snippet_start+h['source_span'][1]],
                        'normalized_coordinate_scope':'snippet_after_two_header_lines','response_span':[begin+snippet_start+h['source_span'][0],begin+snippet_start+h['source_span'][1]]}
                    assert text[slice(*w['response_span'])]==w['source_quote']
                    witnesses.append(w);witness_count+=1
            entries.append({'rank':rank,'title':title,'url':original,'response_span':[begin,end],'response_text':result_text,
                'response_text_sha256':hashlib.sha256(result_text.encode()).hexdigest(),'snippet_span':[snippet_start,len(result_text)],'capture_url':url,
                'query_phrase_visible':bool(ph),'complete_target_visible':bool(full),'witnesses':witnesses,'recognizable_fl_echo':echo,'duplicate_returned_url':duplicate,
                'recorded_url_in_frozen_registry':bool(url and url in known),'eligible_query_phrase_lead':eligible,'decision_reason':reason,'nominated':reason=='selected_first_eligible_query_phrase_lead'})
            if reason=='selected_first_eligible_query_phrase_lead':selected={'query_index':qi,'rank':rank,'url':url,'original_returned_url':original,'title':title,'complete_target_visible_in_discovery':bool(full)}
        calls.append({'query_index':qi,'response_text':text,'response_text_sha256':hashlib.sha256(text.encode()).hexdigest(),
            'response_format_supported':supported,'wordlim_marker_count':marker_count,'attributable_hits':len(headers),'hits':entries})
    selection=read('data/v69/selection.json');when=datetime.fromisoformat(selection['selected_at_utc']);assert all(t<when for t in finish_times)
    assert selection=={'selected_at_utc':selection['selected_at_utc'],'calls':calls,'selected':selected,'search_call_denominator':2,'native_slot_denominator':1,
        'search_engine_exact_matching_observable':False,'independence_or_untouched_status_established':False,'source_identity_admitted':False}
    assert selected is None and [len(c['hits']) for c in calls]==[12,4]
    assert sum(h['complete_target_visible'] for c in calls for h in c['hits'])==3
    assert all(h['recognizable_fl_echo'] for c in calls for h in c['hits'] if h['query_phrase_visible'])
    cap=read('data/v69/capture_preflight.json');assert when<datetime.fromisoformat(cap['sealed_at_utc']) and cap['selected_url'] is None
    for p,h in cap['hashes'].items():assert sha(p)==h
    native={'attempted':False,'representation':'unavailable','representation_ready':False,'reason':'empty_native_nomination_slot','raw_parent_sha256':None,
        'text':None,'pages':[],'native_observation':None,'presence':None,'rendered':[]}
    assert read('data/v69/native_export.json')==native and not (ROOT/'data/v69/acquisition').exists() and not (ROOT/'data/v69/native_intent.json').exists()
    expected_report={'experiment_id':'quotation_attribution_v69','development_selection_after_prior_exposure':True,'target_block_id':1,'target_body_span':[790,915],'target_token_count':18,
        'search_tool_calls':2,'search_queries':2,'search_call_denominator':2,'attributable_hits_per_call':[12,4],'response_formats_supported':[True,True],
        'returned_complete_target_hit_count':3,'returned_query_phrase_hit_count':3,'recognizable_fl_echo_count':3,
        'native_slot_denominator':1,'selected_url':None,'selected_query_index':None,'native_routes_attempted':0,'native_application_responses':0,
        'native_representation':'unavailable','native_representation_ready':False,'native_complete_target_visible':False,'native_complete_target_occurrences':None,
        'native_controls_passed':None,'native_pdf_visual_gate_passed':None,'outcome':'no_eligible_external_lead','extra_search_or_source_requests':0,'opaque_passage_comparisons':0,
        'semantic_or_source_identity_admissions':0,'original_quote_author_authenticated':False,'publication_year_wording_authenticated':False,'new_connected_works_confirmed':0,
        'independent_reviews_admitted':0,'untouched_test_units_admitted':0,'natural_benchmark_capacity_met':False,'e68_negative_result_preserved':True,
        'e66_metadata_gate_preserved_value':False,'historical_e63_gate_value':False,'anita_route_reopened':False}
    assert read('runs/000069_quotation_attribution/report.json')==expected_report
    assert sorted(p.name for p in (ROOT/'data/v69/search').iterdir())==['intent0.json','intent1.json','response0.json','response1.json']
    actual={str(p.relative_to(ROOT)) for p in (ROOT/'data/v69').rglob('*') if p.is_file()}
    recorded={str((run/p).resolve().relative_to(ROOT)) for p in manifest['output_hashes'] if p.startswith('../../data/v69/')};assert actual==recorded
    old=read('runs/000068_passage_presence/report.json');assert old['primary_queries_present']==old['secondary_queries_present']==0 and old['primary_query_denominator']==16 and old['secondary_query_denominator']==1000
    assert read('data/v66/metadata_assessment.json')['passed'] is False and read('data/v63/target_gate.json')['passed'] is False
    prior=[]
    for p in sorted((ROOT/'runs').glob('0000*/manifest.json')):
        if p.parent==run:continue
        assert int(p.parent.name.split('_')[0])<=68;check_hashes(p.parent);prior.append(p.parent.name)
    assert len(prior)==68
    for p in (ROOT/'reports').glob('*_deliverable_seal.json'):
        for name,h in json.loads(p.read_text()).get('deliverable_hashes',{}).items():assert sha(name)==h,name
    result={'state':'verified','manifest_sha256':sha('runs/000069_quotation_attribution/manifest.json'),
        'fixed_target_two_requests_full_responses_all_boundaries_witnesses_and_empty_capture_replayed':True,'production_v69_functions_not_imported':True,
        'shared_components':['sealed E38 literal_hits and normalization','Python urllib and ipaddress URL primitives'],
        'search_call_denominator':2,'recorded_search_calls':2,'attributable_hits_per_call':[12,4],'result_rows_verified':16,'response_local_witnesses_verified':witness_count,
        'complete_target_result_rows':3,'recognizable_fl_echo_result_rows':3,'eligible_external_leads':0,'native_route_denominator':1,'native_routes_attempted':0,
        'native_controls_not_run':True,'original_quote_author_authenticated':False,'search_engine_exact_query_enforcement_observable':False,
        'archived_output_files':len(actual),'verification_network_requests':0,'independent_scientific_review':False,'semantics_or_source_identity_validated':False,
        'e68_negative_result_preserved':True,'e66_metadata_gate_preserved_value':False,'historical_e63_gate_value':False,'prior_runs_preserved':prior}
    out=ROOT/'reports/000069_verification.json'
    if out.exists():assert {k:v for k,v in read(str(out.relative_to(ROOT))).items() if k!='verified_at_utc'}==result
    else:
        with out.open('x') as f:json.dump(result|{'verified_at_utc':datetime.now(timezone.utc).isoformat()},f,indent=2);f.write('\n')
    print(json.dumps({k:v for k,v in result.items() if k!='prior_runs_preserved'}|{'prior_runs_preserved':len(prior)},indent=2))


if __name__=='__main__':main()
