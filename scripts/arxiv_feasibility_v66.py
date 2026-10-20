"""Run the two-route maximum cited-work acquisition; never overwrite a phase."""
import argparse
from datetime import datetime,timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
from fl_decipher.arxiv_feasibility_v66 import select,metadata,first_page_checks
from fl_decipher.routing_v53 import capture,header_blocks
from fl_decipher.source_intake_v37 import citation

ROOT=Path(__file__).resolve().parents[1]
CFG='experiments/arxiv_feasibility_v66.json'
RUN='runs/000066_arxiv_feasibility'
CODE=['src/fl_decipher/arxiv_feasibility_v66.py','scripts/arxiv_feasibility_v66.py','tests/test_arxiv_feasibility_v66.py']
def read(p):return json.loads((ROOT/p).read_text())
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def utc():return datetime.now(timezone.utc).isoformat()
def write(p,obj):
    path=ROOT/p;path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x') as f:json.dump(obj,f,indent=2,ensure_ascii=False);f.write('\n')
def check():
    for p,h in read('data/v66/preflight.json')['hashes'].items():assert sha(p)==h,p

def acquire(name,url,limits):
    write(f'data/v66/{name}_intent.json',{'started_at_utc':utc(),'url':url,'limits':limits})
    return capture(ROOT/'data/v66/acquisition',{'id':name,'og_url':url},limits)

def body(name):
    p=ROOT/f'data/v66/acquisition/{name}/body.bin'
    return p.read_bytes() if p.exists() else b''


def main():
    parser=argparse.ArgumentParser();parser.add_argument('phase',choices=['prepare','acquire','finish']);args=parser.parse_args();cfg=read(CFG)
    if args.phase=='prepare':
        assert not (ROOT/'data/v66').exists() and not (ROOT/RUN).exists()
        for p,h in cfg['input_hashes'].items():assert sha(p)==h,p
        choice=select(read(cfg['inventory']));assert choice and choice['identifier']=='arxiv:'+cfg['base_id']
        write('data/v66/preflight.json',{'sealed_at_utc':utc(),'hashes':cfg['input_hashes']|{p:sha(p) for p in CODE+[CFG]},
              'python_version':platform.python_version(),'packages':{n:importlib.metadata.version(n) for n in ['beautifulsoup4','pypdf','pypdfium2','Pillow']}})
        write('data/v66/selection.json',choice)
        known={c['identifier'] for u in read(cfg['known_exposure'])['urls'] if (c:=citation(u))}
        write('data/v66/exposure.json',{'identifier':choice['identifier'],'frozen_registry_url_count':len(read(cfg['known_exposure'])['urls']),
              'identifier_recorded':choice['identifier'] in known,'registry_scope_incomplete':True,'development_exposure':['E65 preparatory reference inspection','E66 selected acquisition'],
              'new_connected_work_confirmed':False,'independence_or_untouched_status_established':False})
        print('Prepared one source slot, two conditional routes, zero redirects/retries.');return
    check()
    if args.phase=='acquire':
        assert not (ROOT/'data/v66/acquisition').exists() and not (ROOT/'data/v66/metadata_intent.json').exists()
        mr=acquire('metadata',cfg['metadata_url'],cfg['request_limits'])
        decision=metadata(body('metadata'),mr,cfg);write('data/v66/metadata_assessment.json',decision)
        source={'attempted':False,'reason':'metadata_gate_failed','pdf_magic':False,'parseable':False,'identity_assessment':None,'first_page':None,'pdf_sha256':None}
        if decision['passed']:
            limits=cfg['request_limits']|{'max_body_bytes':cfg['pdf_max_body_bytes']}
            pr=acquire('pdf',cfg['pdf_url'],limits);raw=body('pdf')
            source.update({'attempted':True,'reason':'pdf_transport_or_format_unavailable','pdf_magic':raw.startswith(b'%PDF-'),
                           'pdf_sha256':hashlib.sha256(raw).hexdigest() if raw else None})
            if pr['transport_complete'] and source['pdf_magic']:
                try:
                    from pypdf import PdfReader
                    import pypdfium2 as pdfium
                    reader=PdfReader(ROOT/'data/v66/acquisition/pdf/body.bin');doc=pdfium.PdfDocument(raw)
                    pages=len(reader.pages);other=len(doc);source.update({'parseable':True,'pypdf_page_count':pages,'pypdfium_page_count':other})
                    if 0<pages<=cfg['maximum_pdf_pages'] and pages==other:
                        text=reader.pages[0].extract_text();image='data/v66/first_page.png'
                        page=doc[0];bitmap=page.render(scale=1.5);bitmap.to_pil().save(ROOT/image)
                        bitmap.close();page.close()
                        source['first_page']={'page':1,'text':text,'text_sha256':hashlib.sha256(text.encode()).hexdigest(),'image':image,'image_sha256':sha(image),'render_scale':1.5}
                        source['identity_assessment']=first_page_checks(text,pages,other,pr,cfg,decision['native_authors'])
                        source['reason']='first_page_checks_passed_awaiting_visual_audit' if source['identity_assessment']['passed'] else 'first_page_identity_failed'
                    else:source['reason']='page_bound_or_parser_count_failure'
                    doc.close()
                except Exception as error:
                    source['reason']='pdf_parse_or_render_failure';source['error']=f'{type(error).__name__}: {error}'
        write('data/v66/source_export.json',source)
        print(json.dumps({'metadata_passed':decision['passed'],'metadata_unmet':decision['unmet'],'pdf':{k:v for k,v in source.items() if k!='first_page'}},indent=2));return
    assert not (ROOT/RUN).exists()
    decision=read('data/v66/metadata_assessment.json');source=read('data/v66/source_export.json')
    visual=read('data/v66/visual_review.json') if source['first_page'] else None
    if visual:
        assert visual['image_sha256']==source['first_page']['image_sha256'] and visual['page']==1 and visual['independent_review'] is False
    available=bool(decision['passed'] and source['identity_assessment'] and source['identity_assessment']['passed'] and visual and visual['identity_fields_visible_and_match'])
    responses=sum(len(header_blocks(p.read_bytes())['responses']) for p in (ROOT/'data/v66').rglob('headers.txt'))
    routes=len(list((ROOT/'data/v66/acquisition').glob('*/receipt.json')))
    assert routes<=cfg['route_budget'] and responses<=cfg['maximum_application_responses']
    report={'experiment_id':'arxiv_feasibility_v66','source_slot_denominator':1,'selected_identifier':read('data/v66/selection.json')['identifier'],
        'reference_id':read('data/v66/selection.json')['reference_id'],'citation_declared_version':None,'prospective_edition_policy':'v1',
        'metadata_gate_passed':decision['passed'],'metadata_gate_unmet':decision['unmet'],'native_titles':decision['native_titles'],
        'native_authors':decision['native_authors'],'version_history_rows':len(decision['history_rows']),
        'native_v1_submission_time':next((r['submitted_at_utc'] for r in decision['history_rows'] if r['version']==1),None),
        'pdf_attempted':source['attempted'],'pdf_status':source['reason'],'version_addressed_development_pdf_available':available,
        'evidence_path_state':'version_addressed_development_pdf_available' if available else 'acquisition_unavailable' if not read('data/v66/acquisition/metadata/receipt.json')['transport_complete'] else 'metadata_mismatch' if not decision['passed'] else 'pdf_identity_unavailable',
        'routes_attempted':routes,'application_responses':responses,'new_discovery_requests':0,'source_candidates_selected':1,
        'first_pages_identity_audited':1 if visual else 0,'full_paper_visually_reviewed':False,'actual_fl_source_edition_established':False,
        'opaque_text_comparisons':0,'lexical_or_alignment_scores':0,'semantic_or_source_identity_admissions':0,'new_connected_works_confirmed':0,
        'independent_reviews_admitted':0,'untouched_test_units_admitted':0,'natural_benchmark_capacity_met':False,
        'historical_e63_outcome_preserved':True,'historical_e63_gate_value':False,'anita_route_reopened':False}
    write(RUN+'/report.json',report)
    files=sorted(str(p.relative_to(ROOT)) for p in (ROOT/'data/v66').rglob('*') if p.is_file())
    write(RUN+'/manifest.json',{'experiment_id':'arxiv_feasibility_v66','state':'completed','finished_at_utc':utc(),
        'input_hashes':cfg['input_hashes']|{CFG:sha(CFG)},'code_hashes':{p:sha(p) for p in CODE},
        'output_hashes':{'report.json':sha(RUN+'/report.json')}|{str(Path('../../')/p):sha(p) for p in files},'verifier_written_after_acquisition':True})
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
