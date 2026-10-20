"""Replay archive evidence, new purpose decision, derivative and all citation locators."""
from datetime import datetime,timezone
from email.utils import parsedate_to_datetime
import base64
import hashlib
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit
from bs4 import BeautifulSoup,NavigableString
from fl_decipher.source_intake_v37 import citation

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from verify_correspondence_v6 import check_hashes
from verify_new_material_v63 import check_capture


def read(p):return json.loads((ROOT/p).read_text())
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def norm(value):return ' '.join(value.casefold().split())
def recognize(url,label=''):
    try:
        p=urlsplit(url)
        if p.scheme not in ['http','https'] or not p.hostname or p.username is not None or p.password is not None:return None
        if p.port is not None and p.port != (80 if p.scheme=='http' else 443):return None
        return citation(url,label)
    except (ValueError,TypeError):return None


def main():
    run=ROOT/'runs/000064_archive_admission';check_hashes(run)
    cfg=read('experiments/archive_admission_v64.json');pre=read('data/v64/preflight.json');manifest=read('runs/000064_archive_admission/manifest.json')
    original=read('experiments/new_material_v63.json');old_manifest=read('runs/000063_new_material/manifest.json');old_pre=read('data/v63/preflight.json')
    for p,h in pre['hashes'].items():assert sha(p)==h,p
    for p,h in cfg['input_hashes'].items():assert pre['hashes'][p]==h
    assert pre['hashes']['experiments/archive_admission_v64.json']==sha('experiments/archive_admission_v64.json')
    assert old_manifest['finished_at_utc']<cfg['registered_at_utc']<pre['sealed_at_utc']<manifest['finished_at_utc']
    assert cfg['network_request_budget']==cfg['source_acquisition_budget']==0 and cfg['material_denominator']==1 and cfg['policy_developed_after_observed_failure'] is True
    mr,_=check_capture('metadata',original['cdx_url'],original['request_limits'],old_pre['sealed_at_utc'],old_manifest['finished_at_utc'])
    assert mr['transport_complete'] and mr['requested_url']==mr['final_url']==original['cdx_url']
    cdx=json.loads((ROOT/'data/v63/acquisition/metadata/body.bin').read_bytes())
    assert len(cdx)==2 and cdx[0]==['timestamp','original','statuscode','mimetype','digest'] and len(cdx[1])==5
    record=dict(zip(cdx[0],cdx[1],strict=True));assert record['original']==original['fl_url'] and record['timestamp']<=original['archive_cutoff']
    assert re.fullmatch(r'\d{14}',record['timestamp']) and re.fullmatch(r'[A-Z2-7]{32}',record['digest']) and record['statuscode']=='200' and record['mimetype']=='text/html'
    replay='https://web.archive.org/web/'+record['timestamp']+'id_/'+record['original']
    selection={'eligible':True,'reason':None,'record':record,'replay_url':replay};assert selection==read('data/v63/archive_selection.json')
    receipt,_=check_capture('replay',replay,original['request_limits'],mr['finished_at_utc'],old_manifest['finished_at_utc'])
    raw=(ROOT/cfg['raw']).read_bytes();headers=(ROOT/cfg['headers']).read_bytes();soup=BeautifulSoup(raw,'html.parser')
    tags=soup.select('*');indices={id(t):i for i,t in enumerate(tags)};body=soup.select('div.post-body');assert len(body)==1
    def links(selector):return [{'dom_tag_index':indices[id(t)],'href':t['href'],'text':t.get_text(' ',strip=True)} for t in soup.select(selector)]
    identities={'html_titles':[t.get_text(' ',strip=True) for t in soup.select('title')],'post_titles':[t.get_text(' ',strip=True) for t in soup.select('.post-title')],
        'title_links':links('.post-title a[href]'),'bookmarks':links('a[rel~=bookmark][href]'),
        'canonical_urls':[t.get('href','') for t in soup.select('link[rel~=canonical]')],'og_urls':[t.get('content','') for t in soup.select('meta[property="og:url"]')]}
    fields=identities['canonical_urls']+identities['og_urls']
    original_body=BeautifulSoup(raw,'html.parser').select('div.post-body')[0]
    for t in original_body.find_all(['script','style','noscript']):t.decompose()
    text=original_body.get_text(' ',strip=True)
    blocks=[b for b in re.split(r'\r?\n\r?\n',headers.decode('iso-8859-1')) if re.match(r'HTTP/\S+\s+\d+',b)]
    values=re.findall(r'^memento-datetime:\s*(.+?)\s*$',blocks[-1],re.I|re.M);assert len(values)==1
    stamp=parsedate_to_datetime(values[0]).strftime('%Y%m%d%H%M%S');digest=base64.b32encode(hashlib.sha1(raw).digest()).decode().rstrip('=')
    old_checks={'archive_selection_eligible':True,'replay_complete_200':receipt['transport_complete'] is True,'exact_replay_url':receipt['final_url']==replay,
        'single_post_body':len(body)==1,'known_title_present':any(norm(original['title_prefix']) in norm(t) for t in identities['html_titles']+identities['post_titles']),
        'all_native_identity_fields_bound':bool(fields),'body_nonempty':bool(text),
        'no_challenge':not any(s in raw.decode(errors='replace').casefold() for s in ['cf-chl-','verify you are human','checking your browser','enable javascript and cookies to continue']),
        'memento_matches_cdx':stamp==record['timestamp'],'body_digest_matches_cdx':digest==record['digest']}
    # The actual saved page has no canonical/og fields. Preserve the historical failure.
    assert fields==[] and old_checks==read('data/v63/target_gate.json')['checks'] and read('data/v63/target_gate.json')['passed'] is False
    expected_url=original['fl_url'];expected_title=original['nominee']['title'];allowed={expected_url,expected_url.removesuffix('?m=0')}
    checks={k:v for k,v in old_checks.items() if k!='all_native_identity_fields_bound'}
    checks.update({'one_exact_post_title':[norm(v) for v in identities['post_titles']]==[norm(expected_title)],
        'one_exact_html_title':[norm(v) for v in identities['html_titles']]==[norm('Forgotten Languages Full: '+expected_title)],
        'one_exact_title_permalink':len(identities['title_links'])==1 and identities['title_links'][0]['href']==expected_url and norm(identities['title_links'][0]['text'])==norm(expected_title),
        'one_exact_bookmark_permalink':len(identities['bookmarks'])==1 and identities['bookmarks'][0]['href']==expected_url,
        'no_conflicting_identity_metadata':all(v in allowed for v in fields)})
    admitted=all(checks.values());expected_decision={'policy_id':'archive_admission_v64','policy_developed_after_e63_failure':True,
        'e63_gate_recomputed':False,'e63_unmet_recomputed':['all_native_identity_fields_bound'],'e63_identity_check_recomputed':False,
        'legacy_checks':old_checks,'identity_inventory':identities,'identity_metadata_status':'absent','purpose_checks':checks,'limited_admission':admitted,
        'allowed_use':'offline_citation_metadata_inspection' if admitted else None,'decision':'admitted_for_offline_metadata_only' if admitted else 'not_admitted',
        'unmet':[k for k,v in checks.items() if not v],'independent_review':False,'publication_year_wording_authenticated':False,'current_wording_authenticated':False,
        'source_identity_or_meaning_admitted':False,'untouched_test_eligible':False,'source_acquisition_authorized':False}
    assert read('data/v64/admission_decision.json')==expected_decision and admitted
    expected_export={'representation':'archive_bound_development_post_body','original_url':expected_url,'capture_timestamp':record['timestamp'],
        'parent_sha256':hashlib.sha256(raw).hexdigest(),'scope':'exactly one div.post-body',
        'transformations':['remove script/style/noscript descendants only','BeautifulSoup get_text separator space and strip=True'],
        'text':text,'text_sha256':hashlib.sha256(text.encode()).hexdigest(),'unicode_characters':len(text),'permitted_use':'offline_citation_metadata_inspection',
        'exposure_status':'exposed_development_material','publication_year_wording_authenticated':False,'semantic_training_eligible':False,'untouched_test_eligible':False}
    assert read('data/v64/post_export.json')==expected_export
    descendants=list(body[0].descendants);order={id(n):i for i,n in enumerate(descendants)}
    text_nodes=[n for n in descendants if isinstance(n,NavigableString)];text_ids={id(n):i for i,n in enumerate(text_nodes)}
    excluded=lambda n:any(getattr(p,'name',None) in ['script','style','noscript'] for p in n.parents)
    occurrences=[]
    for a in body[0].find_all('a',href=True):
        if a['href'] and not excluded(a):occurrences.append((order[id(a)],0,a['href'],a.get_text(' ',strip=True),{'channel':'href_attribute','dom_tag_index':indices[id(a)]}))
    for n in text_nodes:
        if excluded(n) or any(getattr(p,'name',None)=='a' for p in n.parents):continue
        for match in re.finditer(r'https?://[^\s<>"\)\]]+',str(n)):
            occurrences.append((order[id(n)],match.start(),match.group(),'',{'channel':'literal_text_url','body_text_node_index':text_ids[id(n)],'node_unicode_span':list(match.span())}))
    occurrences.sort(key=lambda r:r[:2]);known={c['identifier'] for u in read('data/v63_registration/known_exposure.json')['urls'] if (c:=recognize(u))}
    rows=[];first={}
    for _,__,url,label,origin in occurrences:
        c=recognize(url,label);identifier=c['identifier'] if c else None;duplicate=first.get(identifier) if identifier else None;i=len(rows)
        if identifier and identifier not in first:first[identifier]=i
        rows.append({'occurrence_id':i,'url':url,'label':label,'origin':origin,'recognized_metadata':c,'reason':'recognized_scholarly_url' if c else 'not_supported_scholarly_url',
            'duplicate_identifier_of_occurrence':duplicate,'prior_registry_status':'identifier_recorded' if identifier in known else 'identifier_not_recorded_in_frozen_inventory' if identifier else 'not_applicable',
            'selected_for_acquisition':False,'source_identity_admitted':False})
    expected_inventory={'raw_parent_sha256':hashlib.sha256(raw).hexdigest(),'scope':'unique post-body; exclude script/style/noscript; hrefs and literal text URLs only',
        'url_occurrence_denominator':len(rows),'occurrences':rows,'recognized_identifier_count':len(first),'recognized_identifiers':list(first),
        'known_identifier_matches':sorted(set(first)&known),'source_candidates_selected':0,'new_connected_works_confirmed':0,'independent_reviews_admitted':0,
        'identifier_absence_is_not_independence':True,'network_requests':0}
    assert read('data/v64/citation_inventory.json')==expected_inventory
    expected_report={'experiment_id':'archive_admission_v64','research_network_requests':0,'material_denominator':1,'e63_original_gate_unchanged':False,
        'development_policy_after_observed_failure':True,'limited_admission':admitted,'allowed_use':'offline_citation_metadata_inspection',
        'html_identity_metadata_status':'absent','title_permalink_count':len(identities['title_links']),'bookmark_permalink_count':len(identities['bookmarks']),
        'purpose_checks_passed':sum(checks.values()),'purpose_check_denominator':len(checks),'post_export_characters':len(text),'url_occurrences':len(rows),
        'recognized_identifier_count':len(first),'recognized_identifiers':list(first),'known_identifier_matches':sorted(set(first)&known),
        'source_candidates_selected':0,'source_requests':0,'opaque_text_comparisons':0,'alignment_or_lexical_scores':0,'semantic_or_source_identity_admissions':0,
        'new_connected_works_confirmed':0,'independent_reviews_admitted':0,'untouched_test_units_admitted':0,'natural_benchmark_capacity_met':False,
        'publication_year_wording_authenticated':False,'anita_route_reopened':False,'previous_results_preserved':True}
    assert read('runs/000064_archive_admission/report.json')==expected_report
    assert sorted(p.name for p in (ROOT/'data/v64').iterdir())==['admission_decision.json','citation_inventory.json','post_export.json','preflight.json']
    prior=[]
    for p in sorted((ROOT/'runs').glob('0000*/manifest.json')):
        if p.parent==run:continue
        assert int(p.parent.name.split('_')[0])<=63;check_hashes(p.parent);prior.append(p.parent.name)
    assert len(prior)==63
    for p in (ROOT/'reports').glob('*_deliverable_seal.json'):
        for name,h in json.loads(p.read_text()).get('deliverable_hashes',{}).items():assert sha(name)==h,name
    result={'state':'verified','manifest_sha256':sha('runs/000064_archive_admission/manifest.json'),'archive_identity_policy_export_and_all_url_locators_replayed':True,
        'historical_e63_outcome_preserved':True,'historical_e63_gate_value':False,'limited_metadata_admission':admitted,
        'body_export_characters':len(text),'url_occurrences':len(rows),'recognized_scholarly_identifiers':len(first),
        'production_v64_functions_not_imported':True,'shared_components':['BeautifulSoup html.parser','sealed E37 citation recognizer'],
        'verification_network_requests':0,'independent_scientific_review':False,'semantics_or_source_identity_validated':False,'prior_runs_preserved':prior}
    out=ROOT/'reports/000064_verification.json'
    if out.exists():assert {k:v for k,v in json.loads(out.read_text()).items() if k!='verified_at_utc'}==result
    else:
        with out.open('x') as f:json.dump(result|{'verified_at_utc':datetime.now(timezone.utc).isoformat()},f,indent=2);f.write('\n')
    print(json.dumps({k:v for k,v in result.items() if k!='prior_runs_preserved'}|{'prior_runs_preserved':len(prior)},indent=2))


if __name__=='__main__':main()
