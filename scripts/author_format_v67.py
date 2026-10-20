"""Replay saved metadata under a new name grammar, then at most one PDF GET."""
import argparse
from datetime import datetime,timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
from fl_decipher.author_format_v67 import assess_metadata,assess_first_page
from fl_decipher.arxiv_feasibility_v66 import select
from fl_decipher.routing_v53 import capture,header_blocks
from fl_decipher.source_intake_v37 import citation

ROOT=Path(__file__).resolve().parents[1]
CFG='experiments/author_format_v67.json'
RUN='runs/000067_author_format'
CODE=['src/fl_decipher/author_format_v67.py','scripts/author_format_v67.py','tests/test_author_format_v67.py']
def read(p):return json.loads((ROOT/p).read_text())
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def utc():return datetime.now(timezone.utc).isoformat()
def write(p,obj):
    path=ROOT/p;path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x') as f:json.dump(obj,f,indent=2,ensure_ascii=False);f.write('\n')
def check():
    for p,h in read('data/v67/preflight.json')['hashes'].items():assert sha(p)==h,p


def main():
    parser=argparse.ArgumentParser();parser.add_argument('phase',choices=['prepare','acquire','finish']);args=parser.parse_args();cfg=read(CFG);prior_cfg=read(cfg['prior_config'])
    if args.phase=='prepare':
        assert not (ROOT/'data/v67').exists() and not (ROOT/RUN).exists()
        for p,h in cfg['input_hashes'].items():assert sha(p)==h,p
        assert cfg['pdf_url']==prior_cfg['pdf_url'] and cfg['route_budget']==cfg['maximum_application_responses']==1
        choice=select(read('data/v65/reference_inventory.json'));assert choice==read('data/v66/selection.json')
        assert read('data/v66/source_export.json')['attempted'] is False
        write('data/v67/preflight.json',{'sealed_at_utc':utc(),'hashes':cfg['input_hashes']|{p:sha(p) for p in CODE+[CFG]},
              'python_version':platform.python_version(),'packages':{n:importlib.metadata.version(n) for n in ['beautifulsoup4','pypdf','pypdfium2','Pillow']}})
        result=assess_metadata((ROOT/cfg['raw_metadata']).read_bytes(),read(cfg['metadata_receipt']),prior_cfg,read(cfg['frozen_assessment']))
        write('data/v67/metadata_assessment.json',result);write('data/v67/selection.json',choice)
        known={c['identifier'] for u in read(cfg['known_exposure'])['urls'] if (c:=citation(u))}
        write('data/v67/exposure.json',{'identifier':choice['identifier'],'frozen_registry_url_count':len(read(cfg['known_exposure'])['urls']),
            'identifier_recorded':choice['identifier'] in known,'registry_scope_incomplete':True,
            'development_exposure':['E65 preparatory reference inspection','E66 native metadata capture','E67 correction and conditional PDF acquisition'],
            'new_connected_work_confirmed':False,'independence_or_untouched_status_established':False})
        print(json.dumps({'state':'prepared','corrected_metadata_passed':result['passed'],'unchanged_e66_gate':result['e66_metadata_replay']['passed'],'maximum_new_requests':1},indent=2));return
    check()
    if args.phase=='acquire':
        assert not (ROOT/'data/v67/acquisition').exists() and not (ROOT/'data/v67/pdf_intent.json').exists() and not (ROOT/'data/v67/source_export.json').exists()
        meta=read('data/v67/metadata_assessment.json')
        result={'attempted':False,'reason':'corrected_metadata_gate_failed','pdf_sha256':None,'pdf_magic':False,'parseable':False,'first_page':None,'identity_assessment':None}
        if meta['passed']:
            write('data/v67/pdf_intent.json',{'started_at_utc':utc(),'url':cfg['pdf_url'],'limits':cfg['request_limits'],'condition':'corrected_metadata_all_checks_passed'})
            receipt=capture(ROOT/'data/v67/acquisition',{'id':'pdf','og_url':cfg['pdf_url']},cfg['request_limits'])
            path=ROOT/'data/v67/acquisition/pdf/body.bin';raw=path.read_bytes() if path.exists() else b''
            result.update({'attempted':True,'reason':'pdf_transport_or_format_unavailable','pdf_sha256':hashlib.sha256(raw).hexdigest() if path.exists() else None,'pdf_magic':raw.startswith(b'%PDF-')})
            if receipt['transport_complete'] and result['pdf_magic']:
                try:
                    from pypdf import PdfReader
                    import pypdfium2 as pdfium
                    reader=PdfReader(path);doc=pdfium.PdfDocument(raw)
                    pages=len(reader.pages);other=len(doc);result.update({'parseable':True,'pypdf_page_count':pages,'pypdfium_page_count':other})
                    if 0<pages<=prior_cfg['maximum_pdf_pages'] and pages==other:
                        text=reader.pages[0].extract_text();image='data/v67/first_page.png';page=doc[0];bitmap=page.render(scale=1.5)
                        bitmap.to_pil().save(ROOT/image);bitmap.close();page.close()
                        result['first_page']={'page':1,'text':text,'text_sha256':hashlib.sha256(text.encode()).hexdigest(),'image':image,'image_sha256':sha(image),'render_scale':1.5}
                        result['identity_assessment']=assess_first_page(text,pages,other,receipt,prior_cfg,meta['parsed_author'])
                        result['reason']='first_page_machine_checks_passed' if result['identity_assessment']['passed'] else 'first_page_identity_failed'
                    else:result['reason']='page_bound_or_parser_count_failure'
                    doc.close()
                except Exception as error:
                    result['reason']='pdf_parse_or_render_failure';result['error']=f'{type(error).__name__}: {error}'
        write('data/v67/source_export.json',result)
        print(json.dumps({k:v for k,v in result.items() if k!='first_page'},indent=2));return
    assert not (ROOT/RUN).exists()
    meta=read('data/v67/metadata_assessment.json');source=read('data/v67/source_export.json')
    visual=read('data/v67/visual_review.json') if source['first_page'] else None
    if visual:
        assert visual['image_sha256']==source['first_page']['image_sha256'] and visual['source_pdf_sha256']==source['pdf_sha256']
        assert visual['page']==1 and visual['independent_review'] is False
        assert set(visual['fields'])=={'title','author','version'} and all(v in ['pass','fail','unresolved'] for v in visual['fields'].values())
    available=bool(meta['passed'] and source['identity_assessment'] and source['identity_assessment']['passed'] and visual and all(v=='pass' for v in visual['fields'].values()))
    receipts=list((ROOT/'data/v67/acquisition').glob('*/receipt.json'))
    responses=sum(len(header_blocks(p.read_bytes())['responses']) for p in (ROOT/'data/v67').rglob('headers.txt'))
    assert len(receipts)<=cfg['route_budget'] and responses<=cfg['maximum_application_responses']
    state='version_addressed_development_pdf_available' if available else 'corrected_metadata_failed' if not meta['passed'] else 'pdf_identity_unavailable'
    if receipts and not read('data/v67/acquisition/pdf/receipt.json')['transport_complete']:state='pdf_acquisition_unavailable'
    report={'experiment_id':'author_format_v67','correction_after_observed_failure':True,'source_slot_denominator':1,'selected_identifier':read('data/v67/selection.json')['identifier'],
        'citation_declared_version':None,'prospective_edition_policy':'v1','e66_metadata_gate_preserved_value':meta['e66_metadata_replay']['passed'],
        'corrected_metadata_checks_passed':sum(meta['checks'].values()),'corrected_metadata_check_denominator':len(meta['checks']),
        'corrected_metadata_gate_passed':meta['passed'],'corrected_metadata_gate_unmet':meta['unmet'],'canonical_author':meta['parsed_author'],
        'pdf_attempted':source['attempted'],'pdf_status':source['reason'],'pdf_sha256':source['pdf_sha256'],
        'pdf_page_count':source.get('pypdf_page_count'),'first_page_machine_checks_passed':source['identity_assessment']['passed'] if source['identity_assessment'] else None,
        'visual_identity_fields':visual['fields'] if visual else None,'version_addressed_development_pdf_available':available,'evidence_path_state':state,
        'routes_attempted':len(receipts),'application_responses':responses,'new_metadata_requests':0,'new_discovery_requests':0,
        'source_candidates_selected':1,'first_pages_identity_audited':1 if visual else 0,'full_paper_visually_reviewed':False,'actual_fl_source_edition_established':False,
        'opaque_text_comparisons':0,'lexical_or_alignment_scores':0,'semantic_or_source_identity_admissions':0,'new_connected_works_confirmed':0,
        'independent_reviews_admitted':0,'untouched_test_units_admitted':0,'natural_benchmark_capacity_met':False,
        'historical_e63_outcome_preserved':True,'historical_e63_gate_value':False,'anita_route_reopened':False}
    write(RUN+'/report.json',report)
    files=sorted(str(p.relative_to(ROOT)) for p in (ROOT/'data/v67').rglob('*') if p.is_file())
    write(RUN+'/manifest.json',{'experiment_id':'author_format_v67','state':'completed','finished_at_utc':utc(),
        'input_hashes':cfg['input_hashes']|{CFG:sha(CFG)},'code_hashes':{p:sha(p) for p in CODE},
        'output_hashes':{'report.json':sha(RUN+'/report.json')}|{str(Path('../../')/p):sha(p) for p in files},'verifier_written_after_acquisition':True})
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
