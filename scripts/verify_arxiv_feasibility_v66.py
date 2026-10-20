"""Replay E66's observed one-route stop without importing production E66 gates."""
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import re
import sys
import unicodedata
from bs4 import BeautifulSoup
from fl_decipher.source_intake_v37 import citation
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from verify_correspondence_v6 import check_hashes
from verify_native_probe_v60 import replay_headers

def read(p):return json.loads((ROOT/p).read_text())
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def norm(s):return ' '.join(unicodedata.normalize('NFC',s).lower().split())


def main():
    run=ROOT/'runs/000066_arxiv_feasibility';check_hashes(run)
    cfg=read('experiments/arxiv_feasibility_v66.json');pre=read('data/v66/preflight.json');manifest=read('runs/000066_arxiv_feasibility/manifest.json')
    for p,h in pre['hashes'].items():assert sha(p)==h,p
    for p,h in cfg['input_hashes'].items():assert pre['hashes'][p]==h
    assert pre['hashes']['experiments/arxiv_feasibility_v66.json']==sha('experiments/arxiv_feasibility_v66.json')
    assert read('runs/000065_textual_references/manifest.json')['finished_at_utc']<cfg['registered_at_utc']<pre['sealed_at_utc']<manifest['finished_at_utc']
    assert cfg['base_id']=='0812.0349' and cfg['route_budget']==cfg['maximum_application_responses']==2
    assert cfg['metadata_url']=='https://arxiv.org/abs/0812.0349v1' and cfg['pdf_url']=='https://arxiv.org/pdf/0812.0349v1'
    assert cfg['request_limits']=={'connect_timeout_seconds':8,'total_timeout_seconds':30,'max_redirects':0,'max_body_bytes':4194304,'user_agent':'FL-Decipher registered cited-work feasibility v66'}
    assert cfg['maximum_pdf_pages']==40 and cfg['pdf_max_body_bytes']==20971520
    inv=read(cfg['inventory']);pairs=[(r,inv['identifier_occurrences'][i]) for r in inv['references'] for i in r['identifier_occurrence_ids'] if inv['identifier_occurrences'][i]['kind']=='arxiv' and inv['identifier_occurrences'][i]['identifier']]
    assert pairs
    ref,occ=pairs[0]
    choice={'identifier':occ['identifier'],'reference_id':ref['reference_id'],'occurrence_id':occ['occurrence_id'],
        'citation_span':ref['span'],'identifier_span':occ['token_span'],'citation_text':ref['text'],'citation_declared_version':occ['declared_version'],
        'edition_policy':'prospectively_choose_v1_if_native_history_verifies'}
    assert read('data/v66/selection.json')==choice and choice['identifier']=='arxiv:'+cfg['base_id'] and choice['citation_declared_version'] is None
    known=read(cfg['known_exposure'])['urls'];known_ids={c['identifier'] for u in known if (c:=citation(u))}
    assert read('data/v66/exposure.json')=={'identifier':choice['identifier'],'frozen_registry_url_count':len(known),'identifier_recorded':choice['identifier'] in known_ids,
        'registry_scope_incomplete':True,'development_exposure':['E65 preparatory reference inspection','E66 selected acquisition'],
        'new_connected_work_confirmed':False,'independence_or_untouched_status_established':False}
    base=ROOT/'data/v66/acquisition/metadata';receipt=read('data/v66/acquisition/metadata/receipt.json');intent=read('data/v66/metadata_intent.json')
    assert intent['url']==cfg['metadata_url'] and intent['limits']==cfg['request_limits']
    assert pre['sealed_at_utc']<intent['started_at_utc']<=receipt['started_at_utc']<receipt['finished_at_utc']<manifest['finished_at_utc']
    limits=cfg['request_limits']
    command=['curl','--disable','--silent','--show-error','--location','--compressed','--proto','=https','--proto-redir','=https','--retry','0',
        '--connect-timeout','8','--max-time','30','--max-redirs','0','--max-filesize','4194304','--user-agent',limits['user_agent'],
        '--output',str(base/'body.bin'),'--dump-header',str(base/'headers.txt'),'--write-out','%{json}',cfg['metadata_url']]
    assert receipt['command']==command and receipt['requested_url']==cfg['metadata_url'] and receipt['id']=='metadata'
    artifacts={p.name:{'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in base.iterdir() if p.name!='receipt.json'}
    assert receipt['artifacts']==artifacts
    telemetry=json.loads((base/'curl_stdout.bin').read_bytes())
    for k,v in [('http_status','http_code'),('final_url','url_effective'),('num_redirects','num_redirects'),('content_type','content_type')]:assert receipt[k]==telemetry[v]
    complete=receipt['curl_returncode']==0 and receipt['http_status']==200 and 'body.bin' in artifacts and artifacts['body.bin']['bytes']<=limits['max_body_bytes']
    assert receipt['transport_complete']==complete
    headers=replay_headers((base/'headers.txt').read_bytes());responses=headers['responses']
    assert len(responses)==1 and responses[0]['status']==200 and not responses[0]['locations']
    raw=(base/'body.bin').read_bytes();soup=BeautifulSoup(raw,'html.parser')
    fields={name:[t.get('content','') for t in soup.select('meta') if t.get('name')==name] for name in ['citation_title','citation_author','citation_arxiv_id','citation_date']}
    history=[t.get_text(' ',strip=True) for t in soup.select('.submission-history')];rows=[];all_labels=[]
    for ci,text in enumerate(history):
        all_labels.extend(int(v) for v in re.findall(r'\[v(\d+)\]',text))
        for m in re.finditer(r'\[v(\d+)\]\s+([A-Za-z]{3},\s+\d{1,2}\s+[A-Za-z]{3}\s+\d{4}\s+\d{2}:\d{2}:\d{2}\s+UTC)',text):
            stamp=datetime.strptime(m[2],'%a, %d %b %Y %H:%M:%S UTC').replace(tzinfo=timezone.utc)
            assert stamp.strftime('%a')==m[2][:3]
            rows.append({'container_index':ci,'version':int(m[1]),'literal_date':m[2],'submitted_at_utc':stamp.isoformat()})
    valid_history=len(history)==1 and len(rows)==len(all_labels)>0 and sorted(all_labels)==list(range(1,len(rows)+1))
    ordered=sorted(rows,key=lambda r:r['version']);valid_history=valid_history and [r['submitted_at_utc'] for r in ordered]==sorted(r['submitted_at_utc'] for r in rows)
    v1=next(r for r in rows if r['version']==1)
    titles=fields['citation_title'];authors=fields['citation_author'];ids=fields['citation_arxiv_id'];dates=fields['citation_date']
    date=datetime.strptime(dates[0],'%Y/%m/%d').date().isoformat() if len(dates)==1 else None
    words=norm(authors[0]).split() if len(authors)==1 else []
    author_check=bool(len(words)>=2 and words[-1]==cfg['author_family'] and words[0].startswith(cfg['author_initial']))
    checks={'complete_exact_native_html':bool(complete and receipt['http_status']==200 and receipt['num_redirects']==0 and receipt['final_url']==cfg['metadata_url'] and receipt['content_type'].split(';')[0].strip().lower()=='text/html'),
        'single_matching_title':len(titles)==1 and norm(titles[0])==norm(cfg['expected_title']),
        'single_compatible_author':author_check,'single_matching_arxiv_identifier':len(ids)==1 and ids[0] in [cfg['base_id'],cfg['base_id']+'v1'],
        'complete_consistent_version_history':valid_history,
        'v1_cited_year_and_before_post_date':bool(valid_history and v1['submitted_at_utc'][:4]==str(cfg['citation_year']) and v1['submitted_at_utc'][:10]<cfg['post_date_cutoff']),
        'single_citation_date_in_cited_year':bool(date and date[:4]==str(cfg['citation_year']))}
    expected={'checks':checks,'passed':all(checks.values()),'unmet':[k for k,v in checks.items() if not v],
        'native_titles':titles,'native_authors':authors,'native_arxiv_ids':ids,'native_citation_dates':dates,'parsed_citation_date':date,
        'history_container_texts':history,'history_rows':rows,'selected_edition':None,'citation_version_unspecified':True,'actual_fl_source_edition_established':False}
    assert read('data/v66/metadata_assessment.json')==expected
    assert checks['single_compatible_author'] is False and sum(checks.values())==6 and authors==['Weinstein, Steven']
    assert read('data/v66/source_export.json')=={'attempted':False,'reason':'metadata_gate_failed','pdf_magic':False,'parseable':False,'identity_assessment':None,'first_page':None,'pdf_sha256':None}
    assert not (ROOT/'data/v66/pdf_intent.json').exists() and [p.name for p in (ROOT/'data/v66/acquisition').iterdir()]==['metadata']
    # Bind every final report field to the observed one-slot, one-route stop.
    report={'experiment_id':'arxiv_feasibility_v66','source_slot_denominator':1,'selected_identifier':choice['identifier'],'reference_id':choice['reference_id'],
        'citation_declared_version':None,'prospective_edition_policy':'v1','metadata_gate_passed':False,'metadata_gate_unmet':['single_compatible_author'],
        'native_titles':titles,'native_authors':authors,'version_history_rows':len(rows),'native_v1_submission_time':v1['submitted_at_utc'],
        'pdf_attempted':False,'pdf_status':'metadata_gate_failed','version_addressed_development_pdf_available':False,'evidence_path_state':'metadata_mismatch',
        'routes_attempted':1,'application_responses':1,'new_discovery_requests':0,'source_candidates_selected':1,'first_pages_identity_audited':0,
        'full_paper_visually_reviewed':False,'actual_fl_source_edition_established':False,'opaque_text_comparisons':0,'lexical_or_alignment_scores':0,
        'semantic_or_source_identity_admissions':0,'new_connected_works_confirmed':0,'independent_reviews_admitted':0,'untouched_test_units_admitted':0,
        'natural_benchmark_capacity_met':False,'historical_e63_outcome_preserved':True,'historical_e63_gate_value':False,'anita_route_reopened':False}
    assert read('runs/000066_arxiv_feasibility/report.json')==report
    actual_files={str(p.relative_to(ROOT)) for p in (ROOT/'data/v66').rglob('*') if p.is_file()}
    recorded_files={str((run/p).resolve().relative_to(ROOT)) for p in manifest['output_hashes'] if p.startswith('../../data/v66/')}
    assert actual_files==recorded_files
    assert read('data/v63/target_gate.json')['passed'] is False and read('data/v64/admission_decision.json')['limited_admission'] is True
    prior=[]
    for p in sorted((ROOT/'runs').glob('0000*/manifest.json')):
        if p.parent==run:continue
        assert int(p.parent.name.split('_')[0])<=65;check_hashes(p.parent);prior.append(p.parent.name)
    assert len(prior)==65
    for p in (ROOT/'reports').glob('*_deliverable_seal.json'):
        for name,h in json.loads(p.read_text()).get('deliverable_hashes',{}).items():assert sha(name)==h,name
    result={'state':'verified','manifest_sha256':sha('runs/000066_arxiv_feasibility/manifest.json'),
        'selection_receipts_budget_timing_complete_metadata_and_skip_replayed':True,'production_v66_gate_functions_not_imported':True,
        'shared_components':['BeautifulSoup html.parser','sealed E37 URL recognizer','sealed v60 header replay'],
        'metadata_checks_passed':6,'metadata_check_denominator':7,'author_metadata_literal':authors[0],
        'failure_is_given_name_first_parser_limitation':True,'author_person_mismatch_established':False,
        'routes_attempted':1,'application_responses':1,'pdf_request_skipped':True,'raw_metadata_sha256':sha('data/v66/acquisition/metadata/body.bin'),
        'archived_output_files':len(actual_files),'historical_e63_outcome_preserved':True,'historical_e63_gate_value':False,
        'verification_network_requests':0,'independent_scientific_review':False,'semantics_or_source_identity_validated':False,'prior_runs_preserved':prior}
    out=ROOT/'reports/000066_verification.json'
    if out.exists():assert {k:v for k,v in read(str(out.relative_to(ROOT))).items() if k!='verified_at_utc'}==result
    else:
        with out.open('x') as f:json.dump(result|{'verified_at_utc':datetime.now(timezone.utc).isoformat()},f,indent=2);f.write('\n')
    print(json.dumps({k:v for k,v in result.items() if k!='prior_runs_preserved'}|{'prior_runs_preserved':len(prior)},indent=2))


if __name__=='__main__':main()
