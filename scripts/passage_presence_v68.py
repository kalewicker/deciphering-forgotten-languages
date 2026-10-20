"""Zero-network fixed passage screen: freeze target, extract, match, review, finish."""
import argparse
from datetime import datetime,timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
from fl_decipher.passage_presence_v68 import target_scope,source_scope,assess,WIDTH,MARKER

ROOT=Path(__file__).resolve().parents[1]
CFG='experiments/passage_presence_v68.json'
RUN='runs/000068_passage_presence'
CODE=['src/fl_decipher/passage_presence_v68.py','scripts/passage_presence_v68.py','tests/test_passage_presence_v68.py']
def read(p):return json.loads((ROOT/p).read_text())
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def utc():return datetime.now(timezone.utc).isoformat()
def write(p,obj):
    path=ROOT/p;path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x') as f:json.dump(obj,f,indent=2,ensure_ascii=False);f.write('\n')
def check():
    for p,h in read('data/v68/preflight.json')['hashes'].items():assert sha(p)==h,p


def main():
    parser=argparse.ArgumentParser();parser.add_argument('phase',choices=['prepare','execute','finish']);args=parser.parse_args();cfg=read(CFG)
    if args.phase=='prepare':
        assert not (ROOT/'data/v68').exists() and not (ROOT/RUN).exists()
        for p,h in cfg['input_hashes'].items():assert sha(p)==h,p
        assert cfg['network_request_budget']==0 and cfg['window_tokens']==WIDTH==12 and cfg['negative_marker']==MARKER
        assert read('runs/000067_author_format/report.json')['version_addressed_development_pdf_available'] is True
        write('data/v68/preflight.json',{'sealed_at_utc':utc(),'hashes':cfg['input_hashes']|{p:sha(p) for p in CODE+[CFG]},
            'python_version':platform.python_version(),'packages':{n:importlib.metadata.version(n) for n in ['beautifulsoup4','pypdf','pypdfium2','Pillow']}})
        scope=target_scope((ROOT/cfg['target_raw']).read_bytes(),read(cfg['target_export']),read(cfg['owner_inventory']))
        write('data/v68/target_inventory.json',scope)
        print(json.dumps({'state':'prepared','target_blocks':len(scope['blocks']),'whole_block_queries':len(scope['blocks']),
            'secondary_queries':sum(q['kind']=='window12' for q in scope['queries']),'queries_frozen_before_full_pdf_extraction':True},indent=2));return
    check()
    if args.phase=='execute':
        assert not (ROOT/'data/v68/execution_intent.json').exists() and not (ROOT/'data/v68/source_export.json').exists()
        write('data/v68/execution_intent.json',{'started_at_utc':utc(),'target_inventory_sha256':sha('data/v68/target_inventory.json'),'pdf_sha256':sha(cfg['pdf']),'network_requests':0})
        from pypdf import PdfReader
        import pypdfium2 as pdfium
        pages=[];error=None;count=None;other=None
        try:
            reader=PdfReader(ROOT/cfg['pdf']);doc=pdfium.PdfDocument(str(ROOT/cfg['pdf']));count=len(reader.pages);other=len(doc);doc.close()
            if count!=other or count!=cfg['expected_pdf_pages']:raise ValueError('fixed page count or parser agreement failed')
            for i,page in enumerate(reader.pages):pages.append({'page':i+1,'text':page.extract_text()})
        except Exception as failure:error=f'{type(failure).__name__}: {failure}'
        source=source_scope(pages);old_first=read('data/v67/source_export.json')['first_page']['text']
        first_agrees=bool(pages and pages[0]['text']==old_first)
        ready=bool(error is None and len(pages)==cfg['expected_pdf_pages'] and all(p['text'].strip() for p in pages) and first_agrees)
        export={'pdf_sha256':sha(cfg['pdf']),'extractor':'pypdf extract_text() defaults; unmodified page strings','pypdf_page_count':count,'pypdfium_page_count':other,
            'expected_pages':cfg['expected_pdf_pages'],'first_page_matches_e67':first_agrees,'representation_ready':ready,'failure_reason':error,'source':source}
        write('data/v68/source_export.json',export)
        target=read('data/v68/target_inventory.json');assessment=assess(target,source) if ready else None
        write('data/v68/assessment.json',assessment)
        image_rows=[];render_error=None
        wanted=sorted({1,cfg['expected_pdf_pages']}|set(assessment['source_hit_pages'])) if assessment is not None else []
        try:
            if wanted:
                doc=pdfium.PdfDocument(str(ROOT/cfg['pdf']))
                for page_number in wanted:
                    image=f'data/v68/rendered/page{page_number:03d}.png';path=ROOT/image;path.parent.mkdir(parents=True,exist_ok=True)
                    assert not path.exists();page=doc[page_number-1];bitmap=page.render(scale=1.2);bitmap.to_pil().save(path);bitmap.close();page.close()
                    image_rows.append({'page':page_number,'image':image,'image_sha256':sha(image),'render_scale':1.2,
                        'reason':'fixed_first_or_last' if page_number in [1,cfg['expected_pdf_pages']] else 'target_hit_page'})
                doc.close()
        except Exception as failure:render_error=f'{type(failure).__name__}: {failure}'
        write('data/v68/render_inventory.json',{'required_pages':wanted,'rendered':image_rows,'failure_reason':render_error})
        print(json.dumps({'representation_ready':ready,'source_pages':len(pages),'source_tokens':len(source['tokens']),
            'controls_passed':assessment['controls_passed'] if assessment else None,
            'whole_blocks_present':sum(r['present'] for r in assessment['results'] if r['kind']=='whole_block') if assessment else None,
            'secondary_queries_present':sum(r['present'] for r in assessment['results'] if r['kind']=='window12') if assessment else None,
            'rendered_pages':[r['page'] for r in image_rows]},indent=2));return
    assert not (ROOT/RUN).exists()
    intent=read('data/v68/execution_intent.json');assert intent['target_inventory_sha256']==sha('data/v68/target_inventory.json') and intent['pdf_sha256']==sha(cfg['pdf'])
    target=read('data/v68/target_inventory.json');source=read('data/v68/source_export.json');assessment=read('data/v68/assessment.json');renders=read('data/v68/render_inventory.json')
    visual=read('data/v68/visual_review.json') if renders['rendered'] else None
    if visual:
        assert visual['source_pdf_sha256']==sha(cfg['pdf']) and visual['independent_review'] is False
        assert [r['page'] for r in visual['pages']]==[r['page'] for r in renders['rendered']]
        for v,r in zip(visual['pages'],renders['rendered'],strict=True):assert v['image_sha256']==r['image_sha256']
    visual_ok=bool(visual and renders['failure_reason'] is None and [r['page'] for r in renders['rendered']]==renders['required_pages']
        and all(v['legibility']=='pass' and v['target_hit_text_consistency'] in ['pass','not_applicable_no_target_hits'] for v in visual['pages']))
    ready=bool(source['representation_ready'] and assessment is not None and assessment['controls_passed'] and visual_ok)
    rows=assessment['results'] if assessment else []
    report={'experiment_id':'passage_presence_v68','development_screen':True,'material_pair_denominator':1,'network_requests':0,
        'source_identifier':'arxiv:0812.0349v1','source_pdf_sha256':sha(cfg['pdf']),'source_pages_expected':cfg['expected_pdf_pages'],'source_pages_extracted':len(source['source']['pages']),
        'source_unicode_characters':source['source']['document_characters'],'source_tokens':len(source['source']['tokens']),
        'source_representation_ready':source['representation_ready'],'owner_runs_accounted':len(target['ledger']),'target_blocks':len(target['blocks']),
        'primary_query_denominator':len(target['blocks']),'primary_queries_present':sum(r['present'] for r in rows if r['kind']=='whole_block') if assessment else None,
        'secondary_window_tokens':12,'secondary_query_denominator':sum(q['kind']=='window12' for q in target['queries']),
        'secondary_queries_present':sum(r['present'] for r in rows if r['kind']=='window12') if assessment else None,
        'short_blocks_without_secondary_queries':sum(b['token_count']<12 for b in target['blocks']),
        'total_target_hit_occurrences':sum(len(r['hits']) for r in rows) if assessment else None,'target_hit_pages':assessment['source_hit_pages'] if assessment else None,
        'positive_control_denominator':cfg['expected_pdf_pages'],'positive_controls_passed':sum(c['passed'] for c in assessment['positive_controls']) if assessment else None,
        'negative_control_denominator':cfg['expected_pdf_pages'],'negative_controls_passed':sum(c['passed'] for c in assessment['negative_controls']) if assessment else None,
        'controls_passed':assessment['controls_passed'] if assessment else None,'visually_inspected_pages':[p['page'] for p in visual['pages']] if visual else [],
        'visual_gate_passed':visual_ok,'screen_readout_ready':ready,'outcome':'literal_presence_observed' if ready and any(r['present'] for r in rows) else 'no_registered_literal_presence' if ready else 'readout_unavailable_or_failed_checks',
        'semantic_or_source_identity_admissions':0,'new_connected_works_confirmed':0,'independent_reviews_admitted':0,'untouched_test_units_admitted':0,
        'natural_benchmark_capacity_met':False,'actual_fl_source_edition_established':False,'e66_metadata_gate_preserved_value':False,
        'historical_e63_outcome_preserved':True,'historical_e63_gate_value':False,'anita_route_reopened':False}
    write(RUN+'/report.json',report)
    files=sorted(str(p.relative_to(ROOT)) for p in (ROOT/'data/v68').rglob('*') if p.is_file())
    write(RUN+'/manifest.json',{'experiment_id':'passage_presence_v68','state':'completed','finished_at_utc':utc(),
        'input_hashes':cfg['input_hashes']|{CFG:sha(CFG)},'code_hashes':{p:sha(p) for p in CODE},
        'output_hashes':{'report.json':sha(RUN+'/report.json')}|{str(Path('../../')/p):sha(p) for p in files},'verifier_written_after_screen':True})
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
