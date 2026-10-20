"""Offline purpose-limited adjudication and metadata inventory over sealed E63 bytes."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from fl_decipher.archive_admission_v64 import adjudicate, export_body, inspect_citations
from fl_decipher.dated_capture_scope_v38 import archive_selection

ROOT=Path(__file__).resolve().parents[1]
CFG='experiments/archive_admission_v64.json'
RUN='runs/000064_archive_admission'
CODE=['src/fl_decipher/archive_admission_v64.py','scripts/archive_admission_v64.py','tests/test_archive_admission_v64.py']


def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def read(p):return json.loads((ROOT/p).read_text())
def utc():return datetime.now(timezone.utc).isoformat()
def write(p,obj):
    path=ROOT/p;path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x') as f:json.dump(obj,f,indent=2,ensure_ascii=False);f.write('\n')


def main():
    cfg=read(CFG);assert not (ROOT/'data/v64').exists() and not (ROOT/RUN).exists()
    assert cfg['network_request_budget']==0 and cfg['policy_developed_after_observed_failure'] is True
    for p,h in cfg['input_hashes'].items():assert sha(p)==h,p
    write('data/v64/preflight.json',{'sealed_at_utc':utc(),'hashes':cfg['input_hashes']|{p:sha(p) for p in CODE+[CFG]}})
    original=read('experiments/new_material_v63.json')
    for name in ['metadata','replay']:
        base=f'data/v63/acquisition/{name}';r=read(base+'/receipt.json')
        for member,info in r['artifacts'].items():assert sha(base+'/'+member)==info['sha256'] and (ROOT/base/member).stat().st_size==info['bytes']
        assert r['transport_complete'] is True and r['http_status']==200 and r['curl_returncode']==0
    meta=read('data/v63/acquisition/metadata/receipt.json')
    assert meta['requested_url']==meta['final_url']==original['cdx_url']
    selection=archive_selection((ROOT/'data/v63/acquisition/metadata/body.bin').read_bytes(),original)
    assert selection==read('data/v63/archive_selection.json') and selection['eligible']
    receipt=read('data/v63/acquisition/replay/receipt.json');assert receipt['requested_url']==selection['replay_url']
    raw=(ROOT/cfg['raw']).read_bytes();headers=(ROOT/cfg['headers']).read_bytes()
    decision=adjudicate(raw,headers,receipt,selection,original);old=read('data/v63/target_gate.json')
    assert decision['legacy_checks']==old['checks'] and decision['e63_gate_recomputed']==old['passed'] is False
    assert decision['e63_unmet_recomputed']==old['unmet']
    export=export_body(raw,decision,selection,original['fl_url'])
    inventory=inspect_citations(raw,decision,read('data/v63_registration/known_exposure.json')['urls'])
    write('data/v64/admission_decision.json',decision);write('data/v64/post_export.json',export);write('data/v64/citation_inventory.json',inventory)
    report={'experiment_id':'archive_admission_v64','research_network_requests':0,'material_denominator':1,
        'e63_original_gate_unchanged':False,'development_policy_after_observed_failure':True,
        'limited_admission':decision['limited_admission'],'allowed_use':decision['allowed_use'],
        'html_identity_metadata_status':decision['identity_metadata_status'],
        'title_permalink_count':len(decision['identity_inventory']['title_links']),'bookmark_permalink_count':len(decision['identity_inventory']['bookmarks']),
        'purpose_checks_passed':sum(decision['purpose_checks'].values()),'purpose_check_denominator':len(decision['purpose_checks']),
        'post_export_characters':export['unicode_characters'] if export else None,
        'url_occurrences':inventory['url_occurrence_denominator'] if inventory else None,
        'recognized_identifier_count':inventory['recognized_identifier_count'] if inventory else None,
        'recognized_identifiers':inventory['recognized_identifiers'] if inventory else None,
        'known_identifier_matches':inventory['known_identifier_matches'] if inventory else None,
        'source_candidates_selected':0,'source_requests':0,'opaque_text_comparisons':0,'alignment_or_lexical_scores':0,
        'semantic_or_source_identity_admissions':0,'new_connected_works_confirmed':0,'independent_reviews_admitted':0,'untouched_test_units_admitted':0,
        'natural_benchmark_capacity_met':False,'publication_year_wording_authenticated':False,'anita_route_reopened':False,'previous_results_preserved':True}
    write(RUN+'/report.json',report)
    files=sorted(str(p.relative_to(ROOT)) for p in (ROOT/'data/v64').rglob('*') if p.is_file())
    write(RUN+'/manifest.json',{'experiment_id':'archive_admission_v64','state':'completed','finished_at_utc':utc(),
        'input_hashes':cfg['input_hashes']|{CFG:sha(CFG)},'code_hashes':{p:sha(p) for p in CODE},
        'output_hashes':{'report.json':sha(RUN+'/report.json')}|{str(Path('../../')/p):sha(p) for p in files},'verifier_written_after_adjudication':True})
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
