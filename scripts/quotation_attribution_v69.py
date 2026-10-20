"""Freeze two quote searches, retain all responses, optionally capture one lead."""
import argparse
from datetime import datetime,timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path
from fl_decipher.quotation_attribution_v69 import freeze_target,ledger,html_view,native_presence,MARKER
from fl_decipher.routing_v53 import capture,header_blocks

ROOT=Path(__file__).resolve().parents[1]
CFG='experiments/quotation_attribution_v69.json'
RUN='runs/000069_quotation_attribution'
CODE=['src/fl_decipher/quotation_attribution_v69.py','scripts/quotation_attribution_v69.py','tests/test_quotation_attribution_v69.py']
def read(p):return json.loads((ROOT/p).read_text())
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def utc():return datetime.now(timezone.utc).isoformat()
def write(p,obj):
    path=ROOT/p;path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x') as f:json.dump(obj,f,indent=2,ensure_ascii=False);f.write('\n')
def check():
    for p,h in read('data/v69/preflight.json')['hashes'].items():assert sha(p)==h,p


def main():
    parser=argparse.ArgumentParser();parser.add_argument('phase',choices=['prepare','select','capture','finish']);args=parser.parse_args();cfg=read(CFG)
    if args.phase=='prepare':
        assert not (ROOT/'data/v69').exists() and not (ROOT/RUN).exists()
        for p,h in cfg['input_hashes'].items():assert sha(p)==h,p
        target=freeze_target(read(cfg['target_inventory']),read(cfg['target_export']))
        assert cfg['search_requests']==target['requests'] and cfg['search_call_budget']==2 and cfg['native_route_budget']==1
        write('data/v69/preflight.json',{'sealed_at_utc':utc(),'hashes':cfg['input_hashes']|{p:sha(p) for p in CODE+[CFG]},
            'packages':{n:importlib.metadata.version(n) for n in ['beautifulsoup4','pypdf','pypdfium2','Pillow']}})
        write('data/v69/target.json',target)
        for i,request in enumerate(target['requests']):
            write(f'data/v69/search/intent{i}.json',{'query_index':i,'tool':'web.run','started_at_utc':utc(),'request_arguments':request})
        print(json.dumps({'state':'prepared','selected_block_id':1,'body_span':target['body_span'],'search_requests':target['requests'],'maximum_native_routes':1},indent=2));return
    check();target=read('data/v69/target.json')
    if args.phase=='select':
        assert not (ROOT/'data/v69/selection.json').exists()
        responses=[]
        for i in range(2):
            intent=read(f'data/v69/search/intent{i}.json');saved=read(f'data/v69/search/response{i}.json')
            assert saved['query_index']==i and saved['tool']=='web.run' and saved['request_arguments']==intent['request_arguments']==cfg['search_requests'][i]
            responses.append(saved)
        result=ledger(responses,target,read(cfg['known_exposure'])['urls'],cfg['echo_title_prefix'])
        write('data/v69/selection.json',{'selected_at_utc':utc(),**result})
        print(json.dumps({'attributable_hits':[c['attributable_hits'] for c in result['calls']], 'formats_supported':[c['response_format_supported'] for c in result['calls']], 'selected':result['selected']},indent=2));return
    if args.phase=='capture':
        assert not (ROOT/'data/v69/native_export.json').exists() and not (ROOT/'data/v69/acquisition').exists()
        selection=read('data/v69/selection.json');chosen=selection['selected']
        write('data/v69/capture_preflight.json',{'sealed_at_utc':utc(),'hashes':{p:sha(p) for p in ['data/v69/selection.json','data/v69/search/response0.json','data/v69/search/response1.json']},'selected_url':chosen['url'] if chosen else None})
        export={'attempted':False,'representation':'unavailable','representation_ready':False,'reason':'empty_native_nomination_slot','raw_parent_sha256':None,'text':None,'pages':[], 'native_observation':None,'presence':None,'rendered':[]}
        if chosen:
            write('data/v69/native_intent.json',{'started_at_utc':utc(),'url':chosen['url'],'limits':cfg['request_limits']})
            receipt=capture(ROOT/'data/v69/acquisition',{'id':'native','og_url':chosen['url']},cfg['request_limits'])
            path=ROOT/'data/v69/acquisition/native/body.bin';raw=path.read_bytes() if path.exists() else b''
            export.update({'attempted':True,'reason':'native_transport_or_format_unavailable','raw_parent_sha256':hashlib.sha256(raw).hexdigest() if path.exists() else None})
            transport=receipt['transport_complete'] and receipt['final_url']==chosen['url'] and receipt['num_redirects']==0
            mime=(receipt['content_type'] or '').split(';')[0].strip().lower()
            if transport and mime=='text/html':
                view=html_view(raw);export['native_observation']={k:v for k,v in view.items() if k!='text'}
                if view['body_count']==1 and view['text'] and view['no_challenge'] and len(view['text'])<=cfg['maximum_source_characters']:
                    export.update({'representation':'current_raw_html_broad_body','representation_ready':True,'reason':'native_html_saved','text':view['text']})
            elif transport and mime=='application/pdf' and raw.startswith(b'%PDF-'):
                try:
                    from pypdf import PdfReader
                    import pypdfium2 as pdfium
                    reader=PdfReader(path);doc=pdfium.PdfDocument(raw);count=len(reader.pages);other=len(doc)
                    export['native_observation']={'pypdf_pages':count,'pypdfium_pages':other}
                    if not (0<count<=cfg['maximum_pdf_pages'] and count==other):raise ValueError('PDF page bounds or counts failed')
                    pages=[];offset=0;parts=[]
                    for i,page in enumerate(reader.pages):
                        text=page.extract_text();start=offset+bool(parts);offset=start+len(text)
                        pages.append({'page':i+1,'text':text,'text_sha256':hashlib.sha256(text.encode()).hexdigest(),'document_span':[start,offset]});parts.append(text)
                        if offset>cfg['maximum_source_characters']:raise ValueError('PDF text character bound failed')
                    text='\n'.join(parts)
                    if text.strip():export.update({'representation':'current_raw_pdf_unmodified_page_text','representation_ready':True,'reason':'native_pdf_saved','text':text,'pages':pages})
                    doc.close()
                except Exception as failure:export['reason']='native_pdf_extraction_failed';export['error']=f'{type(failure).__name__}: {failure}'
            if export['representation_ready']:
                export['text_sha256']=hashlib.sha256(export['text'].encode()).hexdigest();export['presence']=native_presence(export['text'],target['text'])
                if export['pages']:
                    import pypdfium2 as pdfium
                    wanted={1}
                    for h in export['presence']['complete_target_hits']:
                        for p in export['pages']:
                            if p['document_span'][0]<h['source_span'][1] and h['source_span'][0]<p['document_span'][1]:wanted.add(p['page'])
                    doc=pdfium.PdfDocument(raw)
                    for n in sorted(wanted):
                        image=f'data/v69/rendered/page{n:03d}.png';dest=ROOT/image;dest.parent.mkdir(parents=True,exist_ok=True)
                        page=doc[n-1];bitmap=page.render(scale=1.2);bitmap.to_pil().save(dest);bitmap.close();page.close()
                        export['rendered'].append({'page':n,'image':image,'image_sha256':sha(image),'render_scale':1.2})
                    doc.close()
        write('data/v69/native_export.json',export)
        print(json.dumps({k:v for k,v in export.items() if k not in ['text','pages','presence']}|{'complete_quote_visible':export['presence']['complete_target_visible'] if export['presence'] else None},indent=2));return
    assert not (ROOT/RUN).exists()
    selection=read('data/v69/selection.json');native=read('data/v69/native_export.json');chosen=selection['selected'];visual=None
    if native['rendered']:
        visual=read('data/v69/visual_review.json');assert visual['source_pdf_sha256']==native['raw_parent_sha256'] and visual['independent_review'] is False
        for a,b in zip(visual['pages'],native['rendered'],strict=True):assert a['page']==b['page'] and a['image_sha256']==b['image_sha256']
    visual_ok=not native['rendered'] or all(p['legibility']=='pass' and p['complete_quote_text_consistency'] in ['pass','not_applicable_no_hits'] for p in visual['pages'])
    presence=native['presence'];ready=bool(native['representation_ready'] and presence and presence['controls_passed'] and visual_ok)
    visible=bool(ready and presence['complete_target_visible'])
    response_count=sum(len(header_blocks(p.read_bytes())['responses']) for p in (ROOT/'data/v69').rglob('headers.txt'))
    assert response_count<=1
    report={'experiment_id':'quotation_attribution_v69','development_selection_after_prior_exposure':True,'target_block_id':1,'target_body_span':target['body_span'],
        'target_token_count':18,'search_tool_calls':2,'search_queries':2,'search_call_denominator':2,
        'attributable_hits_per_call':[c['attributable_hits'] for c in selection['calls']], 'response_formats_supported':[c['response_format_supported'] for c in selection['calls']],
        'returned_complete_target_hit_count':sum(h['complete_target_visible'] for c in selection['calls'] for h in c['hits']),
        'returned_query_phrase_hit_count':sum(h['query_phrase_visible'] for c in selection['calls'] for h in c['hits']),
        'recognizable_fl_echo_count':sum(h['recognizable_fl_echo'] for c in selection['calls'] for h in c['hits']),
        'native_slot_denominator':1,'selected_url':chosen['url'] if chosen else None,'selected_query_index':chosen['query_index'] if chosen else None,
        'native_routes_attempted':int(native['attempted']),'native_application_responses':response_count,
        'native_representation':native['representation'],'native_representation_ready':native['representation_ready'],
        'native_complete_target_visible':visible,'native_complete_target_occurrences':len(presence['complete_target_hits']) if presence else None,
        'native_controls_passed':presence['controls_passed'] if presence else None,'native_pdf_visual_gate_passed':visual_ok if native['rendered'] else None,
        'outcome':'native_complete_quote_observed' if visible else 'native_quote_not_observed' if ready else 'selected_lead_native_unavailable' if chosen else 'no_eligible_external_lead',
        'extra_search_or_source_requests':0,'opaque_passage_comparisons':0,'semantic_or_source_identity_admissions':0,'original_quote_author_authenticated':False,
        'publication_year_wording_authenticated':False,'new_connected_works_confirmed':0,'independent_reviews_admitted':0,'untouched_test_units_admitted':0,
        'natural_benchmark_capacity_met':False,'e68_negative_result_preserved':True,'e66_metadata_gate_preserved_value':False,'historical_e63_gate_value':False,'anita_route_reopened':False}
    write(RUN+'/report.json',report)
    files=sorted(str(p.relative_to(ROOT)) for p in (ROOT/'data/v69').rglob('*') if p.is_file())
    write(RUN+'/manifest.json',{'experiment_id':'quotation_attribution_v69','state':'completed','finished_at_utc':utc(),
        'input_hashes':cfg['input_hashes']|{CFG:sha(CFG)},'code_hashes':{p:sha(p) for p in CODE},
        'output_hashes':{'report.json':sha(RUN+'/report.json')}|{str(Path('../../')/p):sha(p) for p in files},'verifier_written_after_pilot':True})
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
