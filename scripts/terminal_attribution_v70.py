"""Final four-search/two-native-slot batch; no replacements or extra calls."""
import argparse
from datetime import datetime,timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path
from fl_decipher.terminal_attribution_v70 import freeze_batch,select_batch,evaluate_slot,terminal_decision
from fl_decipher.quotation_attribution_v69 import html_view
from fl_decipher.routing_v53 import capture,header_blocks

ROOT=Path(__file__).resolve().parents[1]
CFG='experiments/terminal_attribution_v70.json';RUN='runs/000070_terminal_attribution'
CODE=['src/fl_decipher/terminal_attribution_v70.py','scripts/terminal_attribution_v70.py','tests/test_terminal_attribution_v70.py']
def utc():return datetime.now(timezone.utc).isoformat()
def read(p):return json.loads((ROOT/p).read_text())
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def write(p,obj):
    dest=ROOT/p;dest.parent.mkdir(parents=True,exist_ok=True)
    with dest.open('x') as f:json.dump(obj,f,indent=2,ensure_ascii=False);f.write('\n')
def check():
    for p,h in read('data/v70/preflight.json')['hashes'].items():assert sha(p)==h,p


def view(raw,receipt,url,cfg):
    source={'representation':'unavailable','representation_ready':False,'reason':'native_transport_or_format_unavailable','raw_parent_sha256':hashlib.sha256(raw).hexdigest(),
        'text':None,'pages':[],'native_observation':None,'rendered':[]}
    mime=(receipt['content_type'] or '').split(';')[0].strip().lower()
    if not (receipt['transport_complete'] and receipt['final_url']==url and receipt['num_redirects']==0):return source
    if mime=='text/html':
        h=html_view(raw);source['native_observation']={k:v for k,v in h.items() if k!='text'}
        if h['body_count']==1 and h['text'] and h['no_challenge'] and len(h['text'])<=cfg['maximum_source_characters']:
            source.update({'representation':'current_raw_html_broad_body','representation_ready':True,'reason':'native_html_saved','text':h['text']})
    elif mime=='application/pdf' and raw.startswith(b'%PDF-'):
        try:
            from pypdf import PdfReader
            from io import BytesIO
            import pypdfium2 as pdfium
            reader=PdfReader(BytesIO(raw));doc=pdfium.PdfDocument(raw);count=len(reader.pages);other=len(doc);doc.close()
            source['native_observation']={'pypdf_pages':count,'pypdfium_pages':other}
            if not (0<count<=cfg['maximum_pdf_pages'] and count==other):raise ValueError('PDF bounds or counts failed')
            pages=[];parts=[];offset=0
            for i,p in enumerate(reader.pages):
                text=p.extract_text();a=offset+bool(parts);offset=a+len(text);parts.append(text)
                pages.append({'page':i+1,'text':text,'text_sha256':hashlib.sha256(text.encode()).hexdigest(),'document_span':[a,offset]})
                if offset>cfg['maximum_source_characters']:raise ValueError('source character bound failed')
            text='\n'.join(parts)
            if text.strip():source.update({'representation':'current_raw_pdf_unmodified_page_text','representation_ready':True,'reason':'native_pdf_saved','text':text,'pages':pages})
        except Exception as e:source['reason']='native_pdf_extraction_failed';source['error']=f'{type(e).__name__}: {e}'
    if source['representation_ready']:source['text_sha256']=hashlib.sha256(source['text'].encode()).hexdigest()
    return source


def main():
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['prepare','select','capture','finish']);args=p.parse_args();cfg=read(CFG)
    if args.phase=='prepare':
        assert not (ROOT/'data/v70').exists() and not (ROOT/RUN).exists()
        for path,h in cfg['input_hashes'].items():assert sha(path)==h,path
        batch=freeze_batch(read(cfg['target_inventory']),read(cfg['target_export']))
        assert batch['requests']==cfg['search_requests'] and cfg['search_call_budget']==4 and cfg['native_route_budget']==2
        assert [(t['block_id'],t['run_id'],t['body_span'],t['token_count']) for t in batch['targets']]==[(3,6,[1140,1543],60),(5,8,[2315,2626],48)]
        write('data/v70/preflight.json',{'sealed_at_utc':utc(),'hashes':cfg['input_hashes']|{x:sha(x) for x in CODE+[CFG]},
            'packages':{n:importlib.metadata.version(n) for n in ['beautifulsoup4','pypdf','pypdfium2','Pillow']}})
        write('data/v70/targets.json',batch)
        for i,r in enumerate(batch['requests']):write(f'data/v70/search/intent{i}.json',{'query_index':i,'tool':'web.run','started_at_utc':utc(),'request_arguments':r})
        print(json.dumps({'state':'prepared','blocks':[t['block_id'] for t in batch['targets']],'requests':batch['requests'],'terminal_batch':True},indent=2));return
    check();batch=read('data/v70/targets.json')
    if args.phase=='select':
        assert not (ROOT/'data/v70/selection.json').exists();responses=[]
        for i in range(4):
            r=read(f'data/v70/search/response{i}.json');intent=read(f'data/v70/search/intent{i}.json')
            assert r['query_index']==i and r['tool']==intent['tool']=='web.run' and r['request_arguments']==intent['request_arguments']==cfg['search_requests'][i];responses.append(r)
        result=select_batch(responses,batch,read(cfg['known_exposure'])['urls'],cfg['echo_title_prefix'])
        write('data/v70/selection.json',{'selected_at_utc':utc(),**result})
        print(json.dumps({'slots':[{'slot_id':s['slot_id'],'selected':s['ledger']['selected'],'capture_owner_slot':s['capture_owner_slot'],'hits':[c['attributable_hits'] for c in s['ledger']['calls']]} for s in result['slots']]},indent=2));return
    selection=read('data/v70/selection.json')
    if args.phase=='capture':
        assert not (ROOT/'data/v70/acquisition').exists() and not (ROOT/'data/v70/native_export.json').exists()
        bind=['data/v70/selection.json']+[f'data/v70/search/response{i}.json' for i in range(4)]
        write('data/v70/capture_preflight.json',{'sealed_at_utc':utc(),'hashes':{x:sha(x) for x in bind},'capture_urls':selection['unique_capture_urls']})
        sources={}
        for slot in selection['slots']:
            sid=slot['slot_id']
            if slot['capture_owner_slot']!=sid:continue
            chosen=slot['ledger']['selected'];url=chosen['url']
            write(f'data/v70/{sid}_intent.json',{'started_at_utc':utc(),'url':url,'limits':cfg['request_limits']})
            receipt=capture(ROOT/'data/v70/acquisition',{'id':sid,'og_url':url},cfg['request_limits'])
            path=ROOT/f'data/v70/acquisition/{sid}/body.bin';raw=path.read_bytes() if path.exists() else b''
            sources[sid]=view(raw,receipt,url,cfg)
            source=sources[sid]
            assigned=[(t,s) for t,s in zip(batch['targets'],selection['slots'],strict=True) if s['capture_owner_slot']==sid]
            if source['pages']:
                import pypdfium2 as pdfium
                wanted={1}
                for t,s in assigned:
                    evaluated=evaluate_slot(t,source)
                    for h in evaluated['presence']['complete_target_hits']:
                        for page in source['pages']:
                            if page['document_span'][0]<h['source_span'][1] and h['source_span'][0]<page['document_span'][1]:wanted.add(page['page'])
                doc=pdfium.PdfDocument(raw)
                for n in sorted(wanted):
                    image=f'data/v70/rendered/{sid}/page{n:03d}.png';dest=ROOT/image;dest.parent.mkdir(parents=True,exist_ok=True)
                    page=doc[n-1];bitmap=page.render(scale=1.2);bitmap.to_pil().save(dest);bitmap.close();page.close()
                    source['rendered'].append({'page':n,'image':image,'image_sha256':sha(image),'render_scale':1.2})
                doc.close()
            print(json.dumps({'captured':sid,'status':receipt['http_status'],'representation':source['representation'],'assigned_full_target_presence':{t['slot_id']:evaluate_slot(t,source)['complete_target_criterion_passed'] for t,s in assigned}},indent=2),flush=True)
        machine=[evaluate_slot(t,sources.get(s['capture_owner_slot'])) for t,s in zip(batch['targets'],selection['slots'],strict=True)]
        write('data/v70/native_export.json',{'sources':sources,'slots_machine_assessments':machine})
        print(json.dumps({'unique_captures_attempted':len(sources),'machine_full_target_successes':sum(r['complete_target_criterion_passed'] for r in machine),'rendered':{k:v['rendered'] for k,v in sources.items()}},indent=2));return
    assert not (ROOT/RUN).exists()
    native=read('data/v70/native_export.json');sources=native['sources'];visual=read('data/v70/visual_review.json') if any(s['rendered'] for s in sources.values()) else None
    outcomes=[]
    for t,slot in zip(batch['targets'],selection['slots'],strict=True):
        owner=slot['capture_owner_slot'];source=sources.get(owner);visual_ok=True
        if source and source['rendered']:
            review=visual['sources'][owner];assert review['source_pdf_sha256']==source['raw_parent_sha256'] and review['independent_review'] is False
            for a,b in zip(review['pages'],source['rendered'],strict=True):assert a['page']==b['page'] and a['image_sha256']==b['image_sha256']
            visual_ok=all(p['legibility']=='pass' and p['complete_quote_text_consistency_by_slot'][t['slot_id']] in ['pass','not_applicable_no_hits'] for p in review['pages'])
        outcomes.append(evaluate_slot(t,source,visual_ok))
    write('data/v70/slot_outcomes.json',outcomes);decision=terminal_decision(outcomes)
    routes=len(sources);responses=sum(len(header_blocks(p.read_bytes())['responses']) for p in (ROOT/'data/v70').rglob('headers.txt'))
    assert routes<=2 and responses<=2
    report={'experiment_id':'terminal_attribution_v70','development_selection_after_prior_exposure':True,'terminal_batch':True,'target_blocks':[3,5],
        'search_tool_calls':4,'search_call_denominator':4,'attributable_hits_per_call':[c['attributable_hits'] for s in selection['slots'] for c in s['ledger']['calls']],
        'native_slot_denominator':2,'native_routes_attempted':routes,'native_application_responses':responses,
        'slot_results':[{'slot_id':s['slot_id'],'block_id':s['block_id'],'selected':s['ledger']['selected'],'capture_owner_slot':s['capture_owner_slot'],'reuses_capture':s['reuses_capture'],
            'source_available':o['source_available'],'complete_target_visible':o['presence']['complete_target_visible'] if o['presence'] else None,
            'native_controls_passed':o['presence']['controls_passed'] if o['presence'] else None,'complete_target_criterion_passed':o['complete_target_criterion_passed']} for s,o in zip(selection['slots'],outcomes,strict=True)],
        **decision,'extra_search_or_source_requests':0,'original_quote_author_authenticated':False,'publication_year_wording_authenticated':False,
        'new_connected_works_confirmed':0,'independent_reviews_admitted':0,'untouched_test_units_admitted':0,'natural_benchmark_capacity_met':False,
        'e69_no_external_lead_preserved':True,'e68_negative_result_preserved':True,'e66_metadata_gate_preserved_value':False,'historical_e63_gate_value':False,'anita_route_reopened':False}
    write(RUN+'/report.json',report)
    files=sorted(str(p.relative_to(ROOT)) for p in (ROOT/'data/v70').rglob('*') if p.is_file())
    write(RUN+'/manifest.json',{'experiment_id':'terminal_attribution_v70','state':'completed','finished_at_utc':utc(),'input_hashes':cfg['input_hashes']|{CFG:sha(CFG)},
        'code_hashes':{x:sha(x) for x in CODE},'output_hashes':{'report.json':sha(RUN+'/report.json')}|{str(Path('../../')/x):sha(x) for x in files},'verifier_written_after_batch':True})
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
