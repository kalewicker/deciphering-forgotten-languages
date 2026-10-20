"""Verify this bounded archive recovery without importing production v63 gates."""
import base64
from datetime import datetime,timezone
from email.utils import parsedate_to_datetime
import hashlib
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlencode,urlsplit
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from verify_correspondence_v6 import check_hashes
from verify_native_probe_v60 import replay_headers
from fl_decipher.source_intake_v37 import citation,citation_metadata,source_material


def read(p):return json.loads((ROOT/p).read_text())
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def raw(name,member='body.bin'):
    path=ROOT/'data/v63/acquisition'/name/member
    return path.read_bytes() if path.exists() else b''
def check_capture(name,url,limits,earliest,latest):
    base=ROOT/'data/v63/acquisition'/name;r=read(str((base/'receipt.json').relative_to(ROOT)));intent=read(f'data/v63/{name}_intent.json')
    assert intent['url']==url and intent['limits']==limits and earliest<intent['started_at_utc']<=r['started_at_utc']<r['finished_at_utc']<latest
    cmd=['curl','--disable','--silent','--show-error','--location','--compressed','--proto','=https','--proto-redir','=https','--retry','0',
        '--connect-timeout',str(limits['connect_timeout_seconds']),'--max-time',str(limits['total_timeout_seconds']),
        '--max-redirs',str(limits['max_redirects']),'--max-filesize',str(limits['max_body_bytes']),'--user-agent',limits['user_agent'],
        '--output',str(base/'body.bin'),'--dump-header',str(base/'headers.txt'),'--write-out','%{json}',url]
    assert r['command']==cmd and r['requested_url']==url and r['id']==name
    files={p.name:{'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in base.iterdir() if p.is_file() and p.name!='receipt.json'}
    assert r['artifacts']==files
    try:t=json.loads(raw(name,'curl_stdout.bin'))
    except (ValueError,TypeError):t={}
    for k,v in [('http_status','http_code'),('final_url','url_effective'),('num_redirects','num_redirects'),('content_type','content_type')]:assert r[k]==t.get(v)
    assert r['transport_complete']==(r['curl_returncode']==0 and r['http_status']==200 and 'body.bin' in files and files['body.bin']['bytes']<=limits['max_body_bytes'])
    return r,len(replay_headers(raw(name,'headers.txt'))['responses'])


def main():
    cfg=read('experiments/new_material_v63.json');pre=read('data/v63/preflight.json');manifest=read('runs/000063_new_material/manifest.json');report=read('runs/000063_new_material/report.json')
    check_hashes(ROOT/'runs/000063_new_material')
    for p,h in pre['hashes'].items():assert sha(p)==h,p
    for p,h in cfg['input_hashes'].items():assert pre['hashes'][p]==h
    assert pre['hashes']['experiments/new_material_v63.json']==sha('experiments/new_material_v63.json')
    assert cfg['registered_at_utc']<pre['sealed_at_utc']<manifest['finished_at_utc']
    nominee=next(r for r in read('data/v37/nominations.json')['nominees'] if r['post_id']!='post00')
    assert nominee==cfg['nominee'] and nominee['url']==cfg['fl_url'] and nominee['post_id']=='post01'
    assert cfg['title_prefix']==nominee['title'].split(':',1)[0]
    fields=[('url',cfg['fl_url']),('matchType','exact'),('output','json'),('filter','statuscode:200'),('filter','mimetype:text/html'),('fl','timestamp,original,statuscode,mimetype,digest'),('limit','-1'),('to',cfg['archive_cutoff'])]
    assert cfg['cdx_url']=='https://web.archive.org/cdx/search/cdx?'+urlencode(fields)
    assert cfg['route_budget']==3 and cfg['maximum_application_responses']==12 and cfg['source_max_body_bytes']==20971520
    assert cfg['request_limits']=={'connect_timeout_seconds':8,'total_timeout_seconds':20,'max_redirects':3,'max_body_bytes':4194304,'user_agent':'FL-Decipher registered non-ANITA material pilot v63'}
    known=read('data/v63_registration/known_exposure.json')
    assert known['urls']==sorted(set(read('data/v37/known_exposure.json')['urls']+['https://arxiv.org/pdf/hep-ph/0209057v1','https://arxiv.org/pdf/1809.09615v1']))
    mr,responses=check_capture('metadata',cfg['cdx_url'],cfg['request_limits'],pre['sealed_at_utc'],manifest['finished_at_utc'])
    selection=read('data/v63/archive_selection.json')
    # The observed index succeeded. Reconstruct its exact one-record schema/identity.
    data=json.loads(raw('metadata'));assert mr['transport_complete'] and len(data)==2
    assert data[0]==['timestamp','original','statuscode','mimetype','digest'] and len(data[1])==5
    record=dict(zip(data[0],data[1],strict=True));assert record['original']==cfg['fl_url'] and record['statuscode']=='200' and record['mimetype']=='text/html'
    assert re.fullmatch(r'\d{14}',record['timestamp']) and record['timestamp']<=cfg['archive_cutoff'] and re.fullmatch(r'[A-Z2-7]{32}',record['digest'])
    expected_selection={'eligible':True,'reason':None,'record':record,'replay_url':'https://web.archive.org/web/'+record['timestamp']+'id_/'+record['original']}
    assert selection==expected_selection
    rr,count=check_capture('replay',selection['replay_url'],cfg['request_limits'],mr['finished_at_utc'],manifest['finished_at_utc']);responses+=count
    body=raw('replay');soup=BeautifulSoup(body,'html.parser');bodies=soup.find_all('div',class_='post-body')
    titles=[t.get_text(' ',strip=True) for t in soup.select('title,.post-title')]
    identities=[t.get('href','') for t in soup.find_all('link') if 'canonical' in t.get('rel',[])]+[t.get('content','') for t in soup.find_all('meta',attrs={'property':'og:url'})]
    exp=urlsplit(cfg['fl_url']);identity=bool(identities)
    for value in identities:
        u=urlsplit(value);identity=identity and u.scheme==exp.scheme and u.hostname==exp.hostname and u.path==exp.path and u.query in ('','m=0')
    text=None
    if len(bodies)==1:
        for node in bodies[0].find_all(['script','style','noscript']):node.decompose()
        text=bodies[0].get_text(' ',strip=True)
    blocks=[b for b in re.split(r'\r?\n\r?\n',raw('replay','headers.txt').decode('iso-8859-1')) if re.match(r'HTTP/\S+\s+\d+',b)]
    values=re.findall(r'^memento-datetime:\s*(.+?)\s*$',blocks[-1],re.I|re.M) if blocks else []
    stamp=parsedate_to_datetime(values[0]).strftime('%Y%m%d%H%M%S') if len(values)==1 else None
    digest=base64.b32encode(hashlib.sha1(body).digest()).decode().rstrip('=')
    normalize=lambda s:' '.join(s.casefold().split())
    checks={'archive_selection_eligible':True,'replay_complete_200':rr['transport_complete'] is True,'exact_replay_url':rr['final_url']==selection['replay_url'],
        'single_post_body':len(bodies)==1,'known_title_present':any(normalize(cfg['title_prefix']) in normalize(t) for t in titles),
        'all_native_identity_fields_bound':identity,'body_nonempty':bool(text),'no_challenge':not any(v in body.decode(errors='replace').casefold() for v in ['cf-chl-','verify you are human','checking your browser','enable javascript and cookies to continue']),
        'memento_matches_cdx':stamp==record['timestamp'],'body_digest_matches_cdx':digest==record['digest']}
    passed=all(checks.values())
    expected={'checks':checks,'passed':passed,'unmet':[k for k,v in checks.items() if not v],'titles':titles,'identity_urls':identities,
        'capture_timestamp':record['timestamp'],'memento_timestamp':stamp,'body_sha1_base32':digest,'body_text':text if passed else None,
        'body_text_sha256':hashlib.sha256(text.encode()).hexdigest() if passed else None,'representation':'dated_archival_post_body_export' if passed else 'unavailable_or_rejected',
        'raw_post':passed,'current_post':False,'historical_publication_wording_authenticated':False,'opaque_text_compared':False,'untouched_test_eligible':False}
    assert read('data/v63/target_gate.json')==expected
    # Current outcome stops before citation/source processing; do not call those helpers.
    assert not passed and checks['all_native_identity_fields_bound'] is False
    assert read('data/v63/citation_selection.json') is None and read('data/v63/source_material.json') is None
    assert not (ROOT/'data/v63/source_intent.json').exists() and sorted(p.name for p in (ROOT/'data/v63/acquisition').iterdir())==['metadata','replay']
    expected_report={'experiment_id':'new_material_v63','post_slot_denominator':1,'source_slot_denominator':1,'selected_post_id':'post01','selected_post_url':cfg['fl_url'],
        'archive_record_eligible':True,'archive_record_reason':None,'archival_target_recovered':False,'target_capture_timestamp':record['timestamp'],
        'target_gate_unmet':expected['unmet'],'source_identifier_selected':None,'source_candidate_selected':False,'unreviewed_source_pdf_saved':False,'source_representation':None,
        'source_prose_or_edition_verified':False,'novel_connected_work_confirmed':False,'independent_review_route_available':False,'qualifying_untouched_reviewed_works':0,
        'natural_benchmark_capacity_met':False,'routes_attempted':2,'application_responses':responses,'new_discovery_requests':0,'evidence_path_state':'post_recovery_unavailable',
        'opaque_text_comparisons':0,'lexical_or_alignment_scores':0,'semantic_or_source_identity_admissions':0,'independent_reviews_admitted':0,'untouched_test_units_admitted':0,
        'anita_route_reopened':False,'prior_failures_preserved':True}
    assert report==expected_report and responses<=12
    prior=[]
    for p in sorted((ROOT/'runs').glob('0000*/manifest.json')):
        if p.parent.name=='000063_new_material':continue
        assert int(p.parent.name.split('_')[0])<=62;check_hashes(p.parent);prior.append(p.parent.name)
    assert len(prior)==62
    for p in (ROOT/'reports').glob('*_deliverable_seal.json'):
        for name,h in json.loads(p.read_text()).get('deliverable_hashes',{}).items():assert sha(name)==h,name
    result={'state':'verified','manifest_sha256':sha('runs/000063_new_material/manifest.json'),'original_nomination_and_exact_request_budget_verified':True,
        'route_attempts':2,'application_responses':responses,'raw_replay_sha256':hashlib.sha256(body).hexdigest(),'raw_replay_bytes':len(body),
        'cdx_digest_memento_title_and_body_replayed':True,'canonical_og_fields_present':len(identities),'registered_post_admission_gate':passed,
        'citation_and_source_stages_skipped':True,'production_v63_gate_functions_not_imported':True,'shared_html_parser':'BeautifulSoup html.parser',
        'verification_network_requests':0,'independent_scientific_review':False,'semantics_or_source_identity_validated':False,'prior_runs_preserved':prior}
    out=ROOT/'reports/000063_verification.json'
    if out.exists():assert {k:v for k,v in json.loads(out.read_text()).items() if k!='verified_at_utc'}==result
    else:
        with out.open('x') as f:json.dump(result|{'verified_at_utc':datetime.now(timezone.utc).isoformat()},f,indent=2);f.write('\n')
    print(json.dumps({k:v for k,v in result.items() if k!='prior_runs_preserved'}|{'prior_runs_preserved':len(prior)},indent=2))


if __name__=='__main__':main()
