"""Verify E67's saved-byte correction and versioned PDF without production v67."""
from datetime import datetime,timezone
import hashlib
from io import BytesIO
import json
from pathlib import Path
import re
import sys
import unicodedata
from bs4 import BeautifulSoup
from pypdf import PdfReader
import pypdfium2 as pdfium
from fl_decipher.source_intake_v37 import citation
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from verify_correspondence_v6 import check_hashes
from verify_native_probe_v60 import replay_headers

def read(p):return json.loads((ROOT/p).read_text())
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def norm(s):return ' '.join(unicodedata.normalize('NFC',s).casefold().split())


def main():
    run=ROOT/'runs/000067_author_format';check_hashes(run)
    cfg=read('experiments/author_format_v67.json');pre=read('data/v67/preflight.json');manifest=read('runs/000067_author_format/manifest.json')
    for p,h in pre['hashes'].items():assert sha(p)==h,p
    for p,h in cfg['input_hashes'].items():assert pre['hashes'][p]==h
    assert pre['hashes']['experiments/author_format_v67.json']==sha('experiments/author_format_v67.json')
    assert read('runs/000066_arxiv_feasibility/manifest.json')['finished_at_utc']<cfg['registered_at_utc']<pre['sealed_at_utc']<manifest['finished_at_utc']
    assert cfg['correction_after_observed_failure'] is True and cfg['route_budget']==cfg['maximum_application_responses']==1 and cfg['new_metadata_request_budget']==0
    assert cfg['pdf_url']=='https://arxiv.org/pdf/0812.0349v1'
    assert cfg['request_limits']=={'connect_timeout_seconds':8,'total_timeout_seconds':30,'max_redirects':0,'max_body_bytes':20971520,'user_agent':'FL-Decipher registered author-format correction v67'}
    old_cfg=read(cfg['prior_config']);inv=read('data/v65/reference_inventory.json')
    pairs=[(r,inv['identifier_occurrences'][i]) for r in inv['references'] for i in r['identifier_occurrence_ids'] if inv['identifier_occurrences'][i]['kind']=='arxiv' and inv['identifier_occurrences'][i]['identifier']]
    ref,occ=pairs[0]
    choice={'identifier':occ['identifier'],'reference_id':ref['reference_id'],'occurrence_id':occ['occurrence_id'],
        'citation_span':ref['span'],'identifier_span':occ['token_span'],'citation_text':ref['text'],'citation_declared_version':occ['declared_version'],
        'edition_policy':'prospectively_choose_v1_if_native_history_verifies'}
    assert read('data/v67/selection.json')==read('data/v66/selection.json')==choice
    known=read(cfg['known_exposure'])['urls'];known_ids={c['identifier'] for u in known if (c:=citation(u))}
    assert read('data/v67/exposure.json')=={'identifier':choice['identifier'],'frozen_registry_url_count':len(known),'identifier_recorded':choice['identifier'] in known_ids,
        'registry_scope_incomplete':True,'development_exposure':['E65 preparatory reference inspection','E66 native metadata capture','E67 correction and conditional PDF acquisition'],
        'new_connected_work_confirmed':False,'independence_or_untouched_status_established':False}
    raw=(ROOT/cfg['raw_metadata']).read_bytes();soup=BeautifulSoup(raw,'html.parser')
    fields={n:[t.get('content','') for t in soup.find_all('meta') if t.get('name')==n] for n in ['citation_title','citation_author','citation_arxiv_id','citation_date']}
    histories=[t.get_text(' ',strip=True) for t in soup.select('.submission-history')];rows=[];labels=[]
    for ci,text in enumerate(histories):
        labels.extend(int(v) for v in re.findall(r'\[v(\d+)\]',text))
        for m in re.finditer(r'\[v(\d+)\]\s+([A-Za-z]{3},\s+\d{1,2}\s+[A-Za-z]{3}\s+\d{4}\s+\d{2}:\d{2}:\d{2}\s+UTC)',text):
            dt=datetime.strptime(m[2],'%a, %d %b %Y %H:%M:%S UTC').replace(tzinfo=timezone.utc)
            assert dt.strftime('%a')==m[2][:3]
            rows.append({'container_index':ci,'version':int(m[1]),'literal_date':m[2],'submitted_at_utc':dt.isoformat()})
    ordered=sorted(rows,key=lambda r:r['version'])
    history_ok=len(histories)==1 and len(rows)==len(labels)>0 and sorted(labels)==list(range(1,len(rows)+1)) and [r['submitted_at_utc'] for r in ordered]==sorted(r['submitted_at_utc'] for r in ordered)
    v1=[r for r in rows if r['version']==1];titles=fields['citation_title'];authors=fields['citation_author'];ids=fields['citation_arxiv_id'];dates=fields['citation_date']
    date=datetime.strptime(dates[0],'%Y/%m/%d').date().isoformat() if len(dates)==1 else None
    old_receipt=read(cfg['metadata_receipt']);old_words=norm(authors[0]).split() if len(authors)==1 else []
    old_checks={'complete_exact_native_html':bool(old_receipt['transport_complete'] and old_receipt['http_status']==200 and old_receipt['num_redirects']==0 and old_receipt['final_url']==old_cfg['metadata_url'] and old_receipt['content_type'].split(';')[0].strip().lower()=='text/html'),
        'single_matching_title':len(titles)==1 and norm(titles[0])==norm(old_cfg['expected_title']),
        'single_compatible_author':bool(len(old_words)>=2 and old_words[-1]==old_cfg['author_family'] and old_words[0].startswith(old_cfg['author_initial'])),
        'single_matching_arxiv_identifier':len(ids)==1 and ids[0] in [old_cfg['base_id'],old_cfg['base_id']+'v1'],
        'complete_consistent_version_history':history_ok,
        'v1_cited_year_and_before_post_date':bool(history_ok and len(v1)==1 and v1[0]['submitted_at_utc'][:4]==str(old_cfg['citation_year']) and v1[0]['submitted_at_utc'][:10]<old_cfg['post_date_cutoff']),
        'single_citation_date_in_cited_year':bool(date and date[:4]==str(old_cfg['citation_year']))}
    frozen={'checks':old_checks,'passed':all(old_checks.values()),'unmet':[k for k,v in old_checks.items() if not v],
        'native_titles':titles,'native_authors':authors,'native_arxiv_ids':ids,'native_citation_dates':dates,'parsed_citation_date':date,
        'history_container_texts':histories,'history_rows':rows,'selected_edition':None,'citation_version_unspecified':True,'actual_fl_source_edition_established':False}
    assert read(cfg['frozen_assessment'])==frozen and frozen['passed'] is False
    # A full-match grammar independently reconstructs the observed comma form.
    assert len(authors)==1
    name_match=re.fullmatch(r"(?P<family>[a-z]+(?:[-'][a-z]+)*),\s*(?P<given>[a-z]+(?:[-'][a-z]+)*(?:\s+[a-z]+(?:\.)?)*)",norm(authors[0]))
    assert name_match
    name={'family':name_match['family'],'given':[w.rstrip('.') for w in name_match['given'].split()],'form':'family_comma_given'}
    assert not set(name['given']+[name['family']])&{'and','jr','sr','ii','iii','iv'}
    checks={k:v for k,v in old_checks.items() if k!='single_compatible_author'}
    checks['single_unambiguous_compatible_author']=name['family']==old_cfg['author_family'] and name['given'][0].startswith(old_cfg['author_initial'])
    corrected={'e66_metadata_replay':frozen,'parsed_author':name,'native_author_literal':authors[0],
        'checks':checks,'passed':all(checks.values()),'unmet':[k for k,v in checks.items() if not v],
        'correction_after_observed_failure':True,'citation_version_unspecified':True,'actual_fl_source_edition_established':False}
    assert read('data/v67/metadata_assessment.json')==corrected and corrected['passed']
    assert read('data/v66/source_export.json')['attempted'] is False
    base=ROOT/'data/v67/acquisition/pdf';receipt=read('data/v67/acquisition/pdf/receipt.json');intent=read('data/v67/pdf_intent.json')
    assert intent=={'started_at_utc':intent['started_at_utc'],'url':cfg['pdf_url'],'limits':cfg['request_limits'],'condition':'corrected_metadata_all_checks_passed'}
    assert pre['sealed_at_utc']<intent['started_at_utc']<=receipt['started_at_utc']<receipt['finished_at_utc']<manifest['finished_at_utc']
    command=['curl','--disable','--silent','--show-error','--location','--compressed','--proto','=https','--proto-redir','=https','--retry','0',
        '--connect-timeout','8','--max-time','30','--max-redirs','0','--max-filesize','20971520','--user-agent',cfg['request_limits']['user_agent'],
        '--output',str(base/'body.bin'),'--dump-header',str(base/'headers.txt'),'--write-out','%{json}',cfg['pdf_url']]
    assert receipt['command']==command and receipt['requested_url']==cfg['pdf_url'] and receipt['id']=='pdf'
    files={p.name:{'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in base.iterdir() if p.name!='receipt.json'}
    assert receipt['artifacts']==files
    telemetry=json.loads((base/'curl_stdout.bin').read_bytes())
    for k,v in [('http_status','http_code'),('final_url','url_effective'),('num_redirects','num_redirects'),('content_type','content_type')]:assert receipt[k]==telemetry[v]
    complete=receipt['curl_returncode']==0 and receipt['http_status']==200 and 'body.bin' in files and files['body.bin']['bytes']<=cfg['request_limits']['max_body_bytes']
    assert receipt['transport_complete']==complete
    responses=replay_headers((base/'headers.txt').read_bytes())['responses']
    assert len(responses)==1 and responses[0]['status']==200 and not responses[0]['locations']
    pdf=(base/'body.bin').read_bytes();assert pdf.startswith(b'%PDF-')
    reader=PdfReader(base/'body.bin');doc=pdfium.PdfDocument(pdf);count=len(reader.pages);other_count=len(doc)
    assert 0<count<=old_cfg['maximum_pdf_pages'] and count==other_count
    text=reader.pages[0].extract_text();hay=norm(text)
    given=r'\s+'.join(re.escape(w)+(r'\.?' if len(w)==1 else '') for w in name['given']);family=re.escape(name['family']);hits=[]
    for form,pattern in [('given_family',given+r'\s+'+family),('family_comma_given',family+r'\s*,\s*'+given)]:
        for m in re.finditer(r'(?<!\w)'+pattern+r'(?!\w)',hay):hits.append({'form':form,'normalized_span':list(m.span()),'normalized_witness':m.group()})
    hits.sort(key=lambda h:(h['normalized_span'],h['form']))
    pdf_checks={'complete_exact_native_pdf':bool(complete and receipt['http_status']==200 and receipt['num_redirects']==0 and receipt['final_url']==cfg['pdf_url'] and receipt['content_type'].split(';')[0].strip().lower()=='application/pdf'),
        'page_count_bound_and_parsers_agree':0<count<=old_cfg['maximum_pdf_pages'] and count==other_count,
        'version_marker_in_first_page':bool(re.search(r'(?<![\w.])0812\.0349v1(?!\w)',text)),
        'title_in_first_page':norm(old_cfg['expected_title']) in hay,'parsed_complete_metadata_name_in_first_page':bool(hits)}
    page=doc[0];bitmap=page.render(scale=1.5);stream=BytesIO();bitmap.to_pil().save(stream,format='PNG');bitmap.close();page.close();doc.close()
    image='data/v67/first_page.png';assert stream.getvalue()==(ROOT/image).read_bytes()
    first={'page':1,'text':text,'text_sha256':hashlib.sha256(text.encode()).hexdigest(),'image':image,'image_sha256':sha(image),'render_scale':1.5}
    expected_source={'attempted':True,'reason':'first_page_machine_checks_passed','pdf_sha256':sha('data/v67/acquisition/pdf/body.bin'),
        'pdf_magic':True,'parseable':True,'first_page':first,
        'identity_assessment':{'checks':pdf_checks,'passed':all(pdf_checks.values()),'unmet':[k for k,v in pdf_checks.items() if not v],
            'author_witnesses':hits,'witness_coordinate_system':'NFC_casefold_whitespace_normalized_first_page'},
        'pypdf_page_count':count,'pypdfium_page_count':other_count}
    assert read('data/v67/source_export.json')==expected_source and all(pdf_checks.values())
    visual=read('data/v67/visual_review.json')
    assert receipt['finished_at_utc']<visual['reviewed_at_utc']<manifest['finished_at_utc']
    assert visual['image_sha256']==first['image_sha256'] and visual['source_pdf_sha256']==expected_source['pdf_sha256'] and visual['page']==1
    assert visual['fields']=={'title':'pass','author':'pass','version':'pass'} and visual['independent_review'] is False
    assert visual['full_first_page_image_inspected'] is True and visual['first_page_prose_visually_exposed'] is True and visual['full_paper_visually_reviewed'] is False
    expected_report={'experiment_id':'author_format_v67','correction_after_observed_failure':True,'source_slot_denominator':1,'selected_identifier':choice['identifier'],
        'citation_declared_version':None,'prospective_edition_policy':'v1','e66_metadata_gate_preserved_value':False,
        'corrected_metadata_checks_passed':sum(checks.values()),'corrected_metadata_check_denominator':len(checks),'corrected_metadata_gate_passed':True,'corrected_metadata_gate_unmet':[],'canonical_author':name,
        'pdf_attempted':True,'pdf_status':'first_page_machine_checks_passed','pdf_sha256':expected_source['pdf_sha256'],'pdf_page_count':count,
        'first_page_machine_checks_passed':True,'visual_identity_fields':visual['fields'],'version_addressed_development_pdf_available':True,'evidence_path_state':'version_addressed_development_pdf_available',
        'routes_attempted':1,'application_responses':1,'new_metadata_requests':0,'new_discovery_requests':0,'source_candidates_selected':1,'first_pages_identity_audited':1,
        'full_paper_visually_reviewed':False,'actual_fl_source_edition_established':False,'opaque_text_comparisons':0,'lexical_or_alignment_scores':0,'semantic_or_source_identity_admissions':0,
        'new_connected_works_confirmed':0,'independent_reviews_admitted':0,'untouched_test_units_admitted':0,'natural_benchmark_capacity_met':False,
        'historical_e63_outcome_preserved':True,'historical_e63_gate_value':False,'anita_route_reopened':False}
    assert read('runs/000067_author_format/report.json')==expected_report
    assert [p.name for p in (ROOT/'data/v67/acquisition').iterdir()]==['pdf'] and not (ROOT/'data/v67/metadata_intent.json').exists()
    actual_files={str(p.relative_to(ROOT)) for p in (ROOT/'data/v67').rglob('*') if p.is_file()}
    recorded_files={str((run/p).resolve().relative_to(ROOT)) for p in manifest['output_hashes'] if p.startswith('../../data/v67/')}
    assert actual_files==recorded_files
    assert read('data/v63/target_gate.json')['passed'] is False and read('data/v64/admission_decision.json')['limited_admission'] is True
    prior=[]
    for p in sorted((ROOT/'runs').glob('0000*/manifest.json')):
        if p.parent==run:continue
        assert int(p.parent.name.split('_')[0])<=66;check_hashes(p.parent);prior.append(p.parent.name)
    assert len(prior)==66
    for p in (ROOT/'reports').glob('*_deliverable_seal.json'):
        for name_path,h in json.loads(p.read_text()).get('deliverable_hashes',{}).items():assert sha(name_path)==h,name_path
    result={'state':'verified','manifest_sha256':sha('runs/000067_author_format/manifest.json'),
        'saved_metadata_old_failure_corrected_name_pdf_identity_receipts_and_outputs_replayed':True,'production_v67_functions_not_imported':True,
        'shared_components':['BeautifulSoup html.parser','sealed E37 URL recognizer','sealed v60 header replay','pypdf first-page extraction','pypdfium2 rendering and page count'],
        'e66_metadata_gate_preserved_value':False,'six_non_author_metadata_checks_unchanged':True,'corrected_metadata_checks_passed':7,'corrected_metadata_check_denominator':7,
        'pdf_first_page_checks_passed':5,'pdf_first_page_check_denominator':5,'pdf_page_count':count,'pdf_bytes':len(pdf),'pdf_sha256':expected_source['pdf_sha256'],
        'rendered_first_page_bytes_reproduced':True,'visual_review_receipt_bound_to_source_and_image':True,'visual_judgment_independently_verified':False,
        'routes_attempted':1,'application_responses':1,'new_metadata_requests':0,'archived_output_files':len(actual_files),
        'verification_network_requests':0,'independent_scientific_review':False,'semantics_or_source_identity_validated':False,
        'historical_e63_outcome_preserved':True,'historical_e63_gate_value':False,'prior_runs_preserved':prior}
    out=ROOT/'reports/000067_verification.json'
    if out.exists():assert {k:v for k,v in read(str(out.relative_to(ROOT))).items() if k!='verified_at_utc'}==result
    else:
        with out.open('x') as f:json.dump(result|{'verified_at_utc':datetime.now(timezone.utc).isoformat()},f,indent=2);f.write('\n')
    print(json.dumps({k:v for k,v in result.items() if k!='prior_runs_preserved'}|{'prior_runs_preserved':len(prior)},indent=2))


if __name__=='__main__':main()
