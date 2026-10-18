"""One fixed source request, full PDF representation and frozen quote readout."""
from datetime import datetime, timezone
from pathlib import Path
import argparse
import hashlib
import json
import re
import shutil
import zipfile
from fl_decipher.capture_review_v23 import request
from fl_decipher.quoted_citation_v39 import frozen_queries, assess_queries
from fl_decipher.dated_capture_scope_v38 import literal_hits

ROOT = Path(__file__).resolve().parents[1]
CFG = 'experiments/quoted_citation_v39.json'
RUN = 'runs/000039_quoted_citation'
def now(): return datetime.now(timezone.utc).isoformat()
def read(p): return json.loads((ROOT/p).read_text())
def sha(p): return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()


def write(p,obj):
    target=ROOT/p
    target.parent.mkdir(parents=True,exist_ok=True)
    with target.open('x') as f:json.dump(obj,f,indent=2);f.write('\n')


def check():
    pre=read('data/v39/preflight.json')
    for field in ('input_hashes','code_hashes'):
        for p,expected in pre[field].items():assert sha(p)==expected,p
    return pre


def seal():
    cfg=read(CFG)
    for p,expected in cfg['input_hashes'].items():assert sha(p)==expected,p
    queries=frozen_queries(read(cfg['target'])['text'],read(cfg['frozen_queries']))
    assert [q['quote_id'] for q in queries]==cfg['query_ids']
    assert not (ROOT/'data/v39/acquisition').exists()
    write('data/v39/frozen_queries.json',{'queries':queries,'target_export_sha256':sha(cfg['target']),'prior_query_ledger_sha256':sha(cfg['frozen_queries'])})
    code=[*list((ROOT/'src/fl_decipher').glob('*.py')),*list((ROOT/'scripts').glob('*.py')),*list((ROOT/'tests').glob('*.py'))]
    write('data/v39/preflight.json',{'sealed_at_utc':now(),'input_hashes':cfg['input_hashes']|{CFG:sha(CFG),'data/v39/frozen_queries.json':sha('data/v39/frozen_queries.json')},
                                    'code_hashes':{str(p.relative_to(ROOT)):sha(p) for p in sorted(code)},'new_source_requests':0,'comparisons_computed':0})
    print('One source and eight unchanged queries sealed before acquisition.')


def acquire():
    check();cfg=read(CFG)
    out=ROOT/'data/v39/acquisition'
    out.mkdir(exist_ok=False)
    receipt=request(out,'source',cfg['source_url'],cfg['request_limits'],'source')
    print(json.dumps({'http':receipt['http_status'],'curl':receipt['curl_returncode'],'complete':receipt['transport_complete']}))


def export_source():
    check();cfg=read(CFG);receipt=read('data/v39/acquisition/source/receipt.json')
    path=ROOT/'data/v39/acquisition/source/body.bin'
    state={'exported_at_utc':now(),'transport_complete':receipt['transport_complete'],'pdf_magic':False,'parseable':False,
           'requested_version_visible':False,'within_page_bound':False,'material_available':False,'pages':[],'failure_reason':None}
    if not receipt['transport_complete']:
        state['failure_reason']='transport_unavailable'
    elif not path.read_bytes().startswith(b'%PDF-'):
        state['failure_reason']='response_not_pdf'
    else:
        state['pdf_magic']=True
        try:
            from pypdf import PdfReader
            import pypdfium2 as pdfium
            reader=PdfReader(path);pdf=pdfium.PdfDocument(str(path))
            state['parseable']=True;state['actual_pdf_pages']=len(reader.pages)
            state['within_page_bound']=0<len(reader.pages)<=cfg['maximum_pdf_pages'] and len(reader.pages)==len(pdf)
            if not state['within_page_bound']:state['failure_reason']='page_bound_or_parser_count_failure'
            else:
                first=reader.pages[0].extract_text()
                state['requested_version_visible']=bool(re.search(r'(?<!\d)1809\.09615v1(?!\d)',first))
                if not state['requested_version_visible']:state['failure_reason']='requested_version_marker_missing'
                else:
                    out=ROOT/'data/v39/source_pages';out.mkdir(exist_ok=False)
                    for i,page in enumerate(reader.pages):
                        text=page.extract_text()
                        image=f'data/v39/source_pages/page{i+1:03d}.png'
                        pdf[i].render(scale=1.4).to_pil().save(ROOT/image)
                        state['pages'].append({'page':i+1,'text':text,'unicode_scope':[0,len(text)],'text_sha256':hashlib.sha256(text.encode()).hexdigest(),
                                               'image':image,'image_sha256':sha(image)})
                    state['material_available']=True
        except (ValueError,TypeError,RuntimeError,OSError) as error:
            state['failure_reason']=f'{type(error).__name__}: {error}'
    if path.exists():state['source_pdf_sha256']=sha('data/v39/acquisition/source/body.bin')
    write('data/v39/source_export.json',state)
    print(json.dumps({k:v for k,v in state.items() if k!='pages'}|{'pages_exported':len(state['pages']),'quote_comparisons_computed':0}))


def assess():
    pre=check();cfg=read(CFG);export=read('data/v39/source_export.json')
    queries=read('data/v39/frozen_queries.json')['queries'];target=read(cfg['target'])
    assert queries==frozen_queries(target['text'],read(cfg['frozen_queries']))
    if export['material_available']:
        qa=read('data/v39/visual_review.json')
        assert qa['reviewed_pages']==[p['page'] for p in export['pages']] and qa['independent_review'] is False
    assessment=assess_queries(queries,export['pages'],cfg['anchors'],export['material_available'])
    assessment['selected_identifier_hits_in_target']=literal_hits(cfg['source_identifier'],target['text'])
    write('data/v39/assessment.json',assessment)
    if export['material_available']:
        bundle=ROOT/'data/v39/neutral_review';bundle.mkdir(exist_ok=False)
        shutil.copyfile(ROOT/'data/v39/acquisition/source/body.bin',bundle/'source.pdf')
        shutil.copyfile(ROOT/'data/v39/acquisition/source/receipt.json',bundle/'source_capture_receipt.json')
        shutil.copyfile(ROOT/cfg['target'],bundle/'target_export.json')
        with (bundle/'fl_post.txt').open('x') as f:f.write(target['text'])
        write('data/v39/neutral_review/source_page_text.json',{'source_pdf_sha256':export['source_pdf_sha256'],
                'pages':[{k:p[k] for k in ('page','text','unicode_scope','text_sha256')} for p in export['pages']]})
        for src,name in [('data/v38/acquisition/replay/receipt.json','target_capture_receipt.json'),('data/v38/acquisition/metadata/body.bin','archive_index.json')]:
            shutil.copyfile(ROOT/src,bundle/name)
        write('data/v39/neutral_review/review_return_template.json',{'reviewer_name':None,'reviewer_role':None,'prior_exposure':None,'independent_of_prior_predictions':None,
              'relationship':'uncertain','whole_post_source_coverage':'uncertain','evidence_spans':[],'counterexamples':[],'review_completed':False,
              'semantic_labels_admitted':0,'source_identity_admitted':False,'untouched_test_admitted':False})
        note=('''# Source-disclosed material-review packet

This is a dated FL post and one explicitly cited paper. Pairing is a citation
lead, not an accepted immediate source or translated passage. The target archive
capture is 2026-01-10 22:21:00 UTC; publication date is distinct. Source PDF bytes
are unchanged and page-local text is unmodified pypdf extraction. Hyphenation,
math and spacing remain; the PDF is the layout reference.

No previous match results, anchor counts, preferred alignments or translations
are included. Source identity is disclosed, so this is not blinded retrieval.
The preparing assistant has inspected the material; it is exposed development
evidence and creates no untouched test unit.

Declare reviewer identity, human/automated role, prior exposure and independence.
Supported, rejected and uncertain findings are welcome. Cite exact file hashes,
half-open Unicode offsets and exact quotes; source text spans additionally need
page number. Record partial coverage, omissions, substitutions, counterexamples
and uncertainty. Shared names, topic words and an English quotation do not
establish meanings for opaque text. Save a new review return, preserving this
packet. No reviewer is assigned or contacted and no completed return is supplied.
''')
        with (bundle/'README.md').open('x') as f:f.write(note)
        members={p.name:{'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in sorted(bundle.iterdir())}
        write('data/v39/neutral_review/manifest.json',{'members':members,'state':'source_disclosed_unreviewed','prior_predictions_included':False})
        with zipfile.ZipFile(ROOT/'data/v39/neutral_review_packet.zip','x',compression=zipfile.ZIP_DEFLATED) as z:
            for p in sorted(bundle.iterdir()):z.write(p,p.name)
    report={'experiment_id':cfg['experiment_id'],'engineering_state':'completed','source_route_denominator':1,'source_requests':1,
            'source_identifier':cfg['source_identifier'],'source_material_available':export['material_available'],'source_failure_reason':export['failure_reason'],
            'source_pages':len(export['pages']),'quote_denominator':8,'quotes_with_literal_presence':assessment['quotes_with_literal_source_presence'],
            'long_quote_denominator':7,'long_quotes_with_literal_presence':assessment['long_quotes_with_literal_presence'],
            'primary_long_block_presence':assessment['primary_long_block_presence'],'expanded_name_literal_presence':assessment['expanded_name_literal_presence'],
            'query_outcomes_unavailable':assessment['query_outcomes_unavailable'],'positive_controls_passed':assessment['positive_controls_passed'],
            'positive_controls_unavailable':assessment['positive_controls_unavailable'],'negative_control_passed':assessment['negative_control']['passed'],
            'selected_identifier_occurrences':len(assessment['selected_identifier_hits_in_target']),
            'target_recaptured':False,'frozen_eight_queries_preserved':True,'normalization_or_matcher_changed':False,
            'opaque_passages_scored':0,'semantic_labels_admitted':0,'source_identities_admitted':0,'independent_reviews_admitted':0,
            'untouched_test_units_admitted':0,'scientific_acceptance':None,'semantic_evaluation_metrics':None,
            'four_work_capacity_gate_passed':False,'source_relationship':'unresolved','whole_post_source_coverage':'unresolved','external_messages_sent':0}
    (ROOT/RUN).mkdir(exist_ok=False);write(RUN+'/report.json',report)
    paths=sorted(p for p in (ROOT/'data/v39').rglob('*') if p.is_file())
    write(RUN+'/manifest.json',{'experiment_id':cfg['experiment_id'],'state':'completed','finished_at_utc':now(),
              'outcome':'literal_quoted_block_found' if report['primary_long_block_presence'] else 'long_block_unavailable' if report['primary_long_block_presence'] is None else 'no_complete_long_quoted_block_found',
              'input_hashes':pre['input_hashes']|{str(p.relative_to(ROOT)):sha(p) for p in paths},'code_hashes':pre['code_hashes'],
              'output_hashes':{'report.json':sha(RUN+'/report.json')}})
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['seal','acquire','export-source','assess'])
    action=parser.parse_args().action
    {'seal':seal,'acquire':acquire,'export-source':export_source,'assess':assess}[action]()
