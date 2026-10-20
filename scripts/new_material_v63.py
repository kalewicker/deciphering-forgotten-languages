"""One fresh-material recovery pilot: archive index, exact replay, optional cited source."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
from fl_decipher.new_material_v63 import choose_post,recover,sources
from fl_decipher.dated_capture_scope_v38 import archive_selection
from fl_decipher.source_intake_v37 import source_material
from fl_decipher.routing_v53 import capture,header_blocks

ROOT=Path(__file__).resolve().parents[1]
CFG='experiments/new_material_v63.json'
RUN='runs/000063_new_material'
CODE=['src/fl_decipher/new_material_v63.py','scripts/new_material_v63.py','tests/test_new_material_v63.py']


def utc():return datetime.now(timezone.utc).isoformat()
def read(p):return json.loads((ROOT/p).read_text())
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def write(p,obj):
    path=ROOT/p;path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x') as f:json.dump(obj,f,indent=2,ensure_ascii=False);f.write('\n')
def raw(name,member='body.bin'):
    p=ROOT/'data/v63/acquisition'/name/member
    return p.read_bytes() if p.exists() else b''
def acquire(name,url,limits,reason):
    write(f'data/v63/{name}_intent.json',{'started_at_utc':utc(),'url':url,'reason':reason,'limits':limits})
    return capture(ROOT/'data/v63/acquisition',{'id':name,'og_url':url},limits)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('phase',choices=['prepare','execute']);args=parser.parse_args();cfg=read(CFG)
    if args.phase=='prepare':
        assert not (ROOT/'data/v63').exists() and not (ROOT/RUN).exists()
        for p,h in cfg['input_hashes'].items():assert sha(p)==h,p
        assert choose_post(read('data/v37/nominations.json'))==cfg['nominee']
        write('data/v63/preflight.json',{'sealed_at_utc':utc(),'hashes':cfg['input_hashes']|{p:sha(p) for p in CODE+[CFG]}})
        print(json.dumps({'state':'prepared','post_id':cfg['nominee']['post_id'],'maximum_routes':3,'new_discovery_calls':0}));return
    for p,h in read('data/v63/preflight.json')['hashes'].items():assert sha(p)==h,p
    assert not (ROOT/'data/v63/metadata_intent.json').exists() and not (ROOT/'data/v63/acquisition').exists() and not (ROOT/RUN).exists()
    mr=acquire('metadata',cfg['cdx_url'],cfg['request_limits'],'single exact-original archive record at frozen cutoff')
    selection=archive_selection(raw('metadata'),cfg) if mr['transport_complete'] else {'eligible':False,'reason':'metadata_transport_unavailable','record':None,'replay_url':None}
    write('data/v63/archive_selection.json',selection)
    target=None;citations=None;material=None;routes=1;selected=None
    if selection['eligible']:
        rr=acquire('replay',selection['replay_url'],cfg['request_limits'],'exact archive-selected replay; no alternate original or timestamp');routes+=1
        target=recover(raw('replay'),raw('replay','headers.txt'),rr,selection,cfg)
        write('data/v63/target_gate.json',target)
        if target['passed']:
            citations=sources(raw('replay'),read('data/v63_registration/known_exposure.json')['urls']);selected=citations['selected']
            write('data/v63/citation_selection.json',citations)
            if selected is not None:
                limits=cfg['request_limits']|{'max_body_bytes':cfg['source_max_body_bytes']}
                sr=acquire('source',selected['request_url'],limits,'first unrecorded explicit arXiv citation; raw source only');routes+=1
                material=source_material(raw('source'),sr);write('data/v63/source_material.json',material)
    if target is None:write('data/v63/target_gate.json',None)
    if citations is None:write('data/v63/citation_selection.json',None)
    if material is None:write('data/v63/source_material.json',None)
    responses=sum(len(header_blocks(p.read_bytes())['responses']) for p in (ROOT/'data/v63').rglob('headers.txt'))
    recovered=target is not None and target['passed'];pdf=material is not None and material['representation']=='raw_pdf_unreviewed'
    report={'experiment_id':'new_material_v63','post_slot_denominator':1,'source_slot_denominator':1,'selected_post_id':cfg['nominee']['post_id'],
        'selected_post_url':cfg['fl_url'],'archive_record_eligible':selection['eligible'],'archive_record_reason':selection['reason'],
        'archival_target_recovered':recovered,'target_capture_timestamp':target['capture_timestamp'] if target else None,
        'target_gate_unmet':target['unmet'] if target else ['eligible_archive_record_missing'],
        'source_identifier_selected':selected['identifier'] if selected else None,'source_candidate_selected':selected is not None,
        'unreviewed_source_pdf_saved':pdf,'source_representation':material['representation'] if material else None,
        'source_prose_or_edition_verified':False,'novel_connected_work_confirmed':False,'independent_review_route_available':False,
        'qualifying_untouched_reviewed_works':0,'natural_benchmark_capacity_met':False,
        'routes_attempted':routes,'application_responses':responses,'new_discovery_requests':0,
        'evidence_path_state':'archival_target_and_unreviewed_source_saved' if recovered and pdf else 'archival_target_only' if recovered else 'post_recovery_unavailable',
        'opaque_text_comparisons':0,'lexical_or_alignment_scores':0,'semantic_or_source_identity_admissions':0,'independent_reviews_admitted':0,
        'untouched_test_units_admitted':0,'anita_route_reopened':False,'prior_failures_preserved':True}
    assert routes<=3 and responses<=12
    write(RUN+'/report.json',report)
    files=sorted(str(p.relative_to(ROOT)) for p in (ROOT/'data/v63').rglob('*') if p.is_file())
    write(RUN+'/manifest.json',{'experiment_id':'new_material_v63','state':'completed','finished_at_utc':utc(),
        'input_hashes':cfg['input_hashes']|{CFG:sha(CFG)},'code_hashes':{p:sha(p) for p in CODE},
        'output_hashes':{'report.json':sha(RUN+'/report.json')}|{str(Path('../../')/p):sha(p) for p in files},'verifier_written_after_pilot':True})
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
