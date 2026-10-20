"""Replay E68 via independent DOM construction and normalized-string search."""
from bisect import bisect_right
from datetime import datetime,timezone
import hashlib
from io import BytesIO
import json
from pathlib import Path
import re
import sys
import unicodedata
from bs4 import BeautifulSoup,NavigableString,Tag
from pypdf import PdfReader
import pypdfium2 as pdfium
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from verify_correspondence_v6 import check_hashes

def read(p):return json.loads((ROOT/p).read_text())
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def norm(s):return unicodedata.normalize('NFC',s).casefold()


def main():
    run=ROOT/'runs/000068_passage_presence';check_hashes(run)
    cfg=read('experiments/passage_presence_v68.json');pre=read('data/v68/preflight.json');manifest=read('runs/000068_passage_presence/manifest.json');intent=read('data/v68/execution_intent.json')
    for p,h in pre['hashes'].items():assert sha(p)==h,p
    for p,h in cfg['input_hashes'].items():assert pre['hashes'][p]==h
    assert pre['hashes']['experiments/passage_presence_v68.json']==sha('experiments/passage_presence_v68.json')
    assert read('runs/000067_author_format/manifest.json')['finished_at_utc']<cfg['registered_at_utc']<pre['sealed_at_utc']<intent['started_at_utc']<manifest['finished_at_utc']
    assert cfg['network_request_budget']==0 and cfg['expected_pdf_pages']==15 and cfg['window_tokens']==12 and cfg['negative_marker']=='flv68absencecontrol20261020'
    assert intent['target_inventory_sha256']==sha('data/v68/target_inventory.json') and intent['pdf_sha256']==sha(cfg['pdf']) and intent['network_requests']==0
    raw=(ROOT/cfg['target_raw']).read_bytes();soup=BeautifulSoup(raw,'html.parser');indices={id(t):i for i,t in enumerate(soup.select('*'))}
    bodies=soup.select('div.post-body');assert len(bodies)==1;body=bodies[0];children=list(body.children)
    for t in body.find_all(['script','style','noscript']):t.decompose()
    runs=[];pieces=[];at=0
    for ci,child in enumerate(children):
        if child.parent is not body:continue
        if isinstance(child,Tag):text=child.get_text(' ',strip=True)
        elif type(child) in body.MAIN_CONTENT_STRING_TYPES:text=str(child).strip()
        else:continue
        if not text:continue
        start=at+bool(pieces);at=start+len(text);pieces.append(text)
        runs.append({'run_id':len(runs),'direct_child_index':ci,'owner_tag':child.name if isinstance(child,Tag) else None,
            'owner_dom_tag_index':indices[id(child)] if isinstance(child,Tag) else None,'span':[start,at],'text':text})
    body_text=' '.join(pieces);export=read(cfg['target_export']);old_inventory=read(cfg['owner_inventory'])
    assert body_text==body.get_text(' ',strip=True)==export['text'] and sha(cfg['target_raw'])==export['parent_sha256']
    assert hashlib.sha256(body_text.encode()).hexdigest()==export['text_sha256']
    for got,old in zip(runs,old_inventory['runs'],strict=True):
        for k,v in got.items():assert old[k]==v,k
    starts=[r['run_id'] for r in runs if r['owner_tag']=='div' and r['text'].startswith('Aissen, Judith (2003).')]
    assert len(starts)==1 and starts==old_inventory['boundary_match_run_ids'];boundary=starts[0]
    ledger=[];blocks=[];queries=[]
    for r in runs:
        owner=children[r['direct_child_index']];included=r['run_id']<boundary and isinstance(owner,Tag) and owner.name=='div' and owner.get('align','').lower()=='justify'
        ledger.append({'run_id':r['run_id'],'owner_dom_tag_index':r['owner_dom_tag_index'],'body_span':r['span'],'included':included,
            'reason':'included_structural_prose_block' if included else 'at_or_after_reference_boundary' if r['run_id']>=boundary else 'pre_reference_non_prose_owner','block_id':len(blocks) if included else None})
        if not included:continue
        ts=list(re.finditer(r'\S+',r['text']));bid=len(blocks)
        blocks.append({'block_id':bid,'run_id':r['run_id'],'body_span':r['span'],'text':r['text'],'token_count':len(ts),'secondary_query_count':max(0,len(ts)-11)})
        choices=[('whole_block',0,len(ts))]+[('window12',i,i+12) for i in range(max(0,len(ts)-11))]
        for kind,a,b in choices:
            x=r['span'][0]+ts[a].start();y=r['span'][0]+ts[b-1].end()
            queries.append({'query_id':len(queries),'block_id':bid,'run_id':r['run_id'],'kind':kind,'block_token_span':[a,b],'body_span':[x,y],
                'text':body_text[x:y],'normalized_tokens':[norm(t.group()) for t in ts[a:b]]})
    target={'raw_parent_sha256':export['parent_sha256'],'body_text_sha256':export['text_sha256'],'boundary_run_id':boundary,'width':12,'ledger':ledger,'blocks':blocks,'queries':queries}
    assert read('data/v68/target_inventory.json')==target
    reader=PdfReader(ROOT/cfg['pdf']);doc=pdfium.PdfDocument(str(ROOT/cfg['pdf']));assert len(reader.pages)==len(doc)==15
    page_texts=[p.extract_text() for p in reader.pages];assert all(t.strip() for t in page_texts)
    assert page_texts[0]==read('data/v67/source_export.json')['first_page']['text']
    document='\n'.join(page_texts);page_starts=[];at=0;page_rows=[];token_at=0
    for i,text in enumerate(page_texts):
        page_starts.append(at);nt=len(re.findall(r'\S+',text))
        page_rows.append({'page':i+1,'text':text,'text_sha256':hashlib.sha256(text.encode()).hexdigest(),'unicode_characters':len(text),
            'document_span':[at,at+len(text)],'token_span':[token_at,token_at+nt]})
        at+=len(text)+1;token_at+=nt
    source_tokens=[]
    for m in re.finditer(r'\S+',document):
        page_index=bisect_right(page_starts,m.start())-1
        source_tokens.append({'page':page_index+1,'page_span':[m.start()-page_starts[page_index],m.end()-page_starts[page_index]],
            'document_span':list(m.span()),'literal':m.group(),'normalized':norm(m.group())})
    source={'pages':page_rows,'document_characters':len(document),'document_sha256':hashlib.sha256(document.encode()).hexdigest(),'tokens':source_tokens,'separator':'single newline between unchanged page strings'}
    expected_export={'pdf_sha256':sha(cfg['pdf']),'extractor':'pypdf extract_text() defaults; unmodified page strings','pypdf_page_count':15,'pypdfium_page_count':15,
        'expected_pages':15,'first_page_matches_e67':True,'representation_ready':True,'failure_reason':None,'source':source}
    assert read('data/v68/source_export.json')==expected_export
    # Use string find plus token-boundary tables, not production's 12-gram index.
    values=[t['normalized'] for t in source_tokens];hay=' '.join(values);start_to_token={};end_to_token={};pos=0
    for i,value in enumerate(values):start_to_token[pos]=i;pos+=len(value);end_to_token[pos]=i+1;pos+=1
    def hits(q):
        assert q;needle=' '.join(q);result=[];cursor=0
        while (found:=hay.find(needle,cursor))>=0:
            end=found+len(needle);cursor=found+1
            if found not in start_to_token or end not in end_to_token:continue
            a=start_to_token[found];b=end_to_token[end];assert values[a:b]==q
            selected=source_tokens[a:b];spans=[]
            for t in selected:
                if not spans or spans[-1]['page']!=t['page']:spans.append({'page':t['page'],'span':list(t['page_span'])})
                else:spans[-1]['span'][1]=t['page_span'][1]
            for s in spans:s['quote']=page_texts[s['page']-1][slice(*s['span'])]
            result.append({'source_token_span':[a,b],'document_span':[selected[0]['document_span'][0],selected[-1]['document_span'][1]],'page_spans':spans})
        return result
    results=[]
    for q in queries:
        found=hits(q['normalized_tokens']);results.append({'query_id':q['query_id'],'block_id':q['block_id'],'kind':q['kind'],'hits':found,'present':bool(found)})
    marker=cfg['negative_marker'];collision=any(marker in v for v in values) or any(marker in norm(b['text']) for b in blocks)
    positives=[];negatives=[]
    for p in page_rows:
        a,b=p['token_span'];prefix=values[a:min(b,a+12)];found=hits(prefix)
        positives.append({'page':p['page'],'normalized_tokens':prefix,'hits':found,'passed':any(h['source_token_span']==[a,a+len(prefix)] for h in found)})
        negative=prefix+[marker];found=hits(negative);negatives.append({'page':p['page'],'normalized_tokens':negative,'hits':found,'passed':not collision and not found})
    per_block=[]
    for b in blocks:
        rs=[r for r in results if r['block_id']==b['block_id']]
        per_block.append({'block_id':b['block_id'],'run_id':b['run_id'],'token_count':b['token_count'],
            'whole_block_present':any(r['present'] for r in rs if r['kind']=='whole_block'),'secondary_query_count':sum(r['kind']=='window12' for r in rs),
            'secondary_queries_present':sum(r['present'] for r in rs if r['kind']=='window12')})
    hit_pages=sorted({p['page'] for r in results for h in r['hits'] for p in h['page_spans']})
    assessment={'results':results,'positive_controls':positives,'negative_controls':negatives,'marker_collision':collision,
        'controls_passed':all(r['passed'] for r in positives+negatives),'per_block':per_block,'source_hit_pages':hit_pages}
    assert read('data/v68/assessment.json')==assessment and assessment['controls_passed']
    renders=read('data/v68/render_inventory.json');wanted=sorted({1,15}|set(hit_pages));assert renders['required_pages']==wanted and renders['failure_reason'] is None
    expected_renders=[]
    for n in wanted:
        page=doc[n-1];bitmap=page.render(scale=1.2);buf=BytesIO();bitmap.to_pil().save(buf,format='PNG');bitmap.close();page.close()
        image=f'data/v68/rendered/page{n:03d}.png';assert buf.getvalue()==(ROOT/image).read_bytes()
        expected_renders.append({'page':n,'image':image,'image_sha256':sha(image),'render_scale':1.2,'reason':'fixed_first_or_last' if n in [1,15] else 'target_hit_page'})
    doc.close();assert renders['rendered']==expected_renders
    visual=read('data/v68/visual_review.json');assert intent['started_at_utc']<visual['reviewed_at_utc']<manifest['finished_at_utc']
    assert visual['source_pdf_sha256']==sha(cfg['pdf']) and visual['independent_review'] is False and visual['unrendered_pages_visually_reviewed'] is False
    for v,r in zip(visual['pages'],expected_renders,strict=True):
        assert v['page']==r['page'] and v['image_sha256']==r['image_sha256'] and v['legibility']=='pass' and v['target_hit_text_consistency']=='not_applicable_no_target_hits'
    assert not hit_pages and not any(r['present'] for r in results)
    expected_report={'experiment_id':'passage_presence_v68','development_screen':True,'material_pair_denominator':1,'network_requests':0,
        'source_identifier':'arxiv:0812.0349v1','source_pdf_sha256':sha(cfg['pdf']),'source_pages_expected':15,'source_pages_extracted':15,
        'source_unicode_characters':len(document),'source_tokens':len(values),'source_representation_ready':True,'owner_runs_accounted':len(ledger),'target_blocks':len(blocks),
        'primary_query_denominator':len(blocks),'primary_queries_present':0,'secondary_window_tokens':12,'secondary_query_denominator':sum(q['kind']=='window12' for q in queries),
        'secondary_queries_present':0,'short_blocks_without_secondary_queries':sum(b['token_count']<12 for b in blocks),'total_target_hit_occurrences':0,'target_hit_pages':[],
        'positive_control_denominator':15,'positive_controls_passed':sum(r['passed'] for r in positives),'negative_control_denominator':15,'negative_controls_passed':sum(r['passed'] for r in negatives),
        'controls_passed':True,'visually_inspected_pages':wanted,'visual_gate_passed':True,'screen_readout_ready':True,'outcome':'no_registered_literal_presence',
        'semantic_or_source_identity_admissions':0,'new_connected_works_confirmed':0,'independent_reviews_admitted':0,'untouched_test_units_admitted':0,'natural_benchmark_capacity_met':False,
        'actual_fl_source_edition_established':False,'e66_metadata_gate_preserved_value':False,'historical_e63_outcome_preserved':True,'historical_e63_gate_value':False,'anita_route_reopened':False}
    assert read('runs/000068_passage_presence/report.json')==expected_report
    assert not (ROOT/'data/v68/acquisition').exists()
    actual={str(p.relative_to(ROOT)) for p in (ROOT/'data/v68').rglob('*') if p.is_file()}
    recorded={str((run/p).resolve().relative_to(ROOT)) for p in manifest['output_hashes'] if p.startswith('../../data/v68/')};assert actual==recorded
    assert read('data/v66/metadata_assessment.json')['passed'] is False and read('data/v63/target_gate.json')['passed'] is False
    prior=[]
    for p in sorted((ROOT/'runs').glob('0000*/manifest.json')):
        if p.parent==run:continue
        assert int(p.parent.name.split('_')[0])<=67;check_hashes(p.parent);prior.append(p.parent.name)
    assert len(prior)==67
    for p in (ROOT/'reports').glob('*_deliverable_seal.json'):
        for name,h in json.loads(p.read_text()).get('deliverable_hashes',{}).items():assert sha(name)==h,name
    receipt={'state':'verified','manifest_sha256':sha('runs/000068_passage_presence/manifest.json'),
        'independent_dom_full_pdf_tokens_all_queries_controls_and_spans_replayed':True,'production_v68_functions_not_imported':True,
        'alternative_matcher':'normalized string search with token-boundary offset tables; no 12-gram index',
        'shared_components':['BeautifulSoup html.parser','Unicode NFC and casefold','pypdf extract_text defaults','pypdfium2 rendering/page count'],
        'target_blocks':len(blocks),'whole_block_queries_verified':len(blocks),'secondary_queries_verified':len(queries)-len(blocks),'source_pages':15,'source_tokens':len(values),
        'positive_controls_verified':15,'negative_controls_verified':15,'total_query_rows_verified':len(queries)+30,
        'primary_queries_present':0,'secondary_queries_present':0,'all_registered_render_bytes_reproduced':True,'visual_judgments_independently_verified':False,
        'archived_output_files':len(actual),'verification_network_requests':0,'independent_scientific_review':False,'semantics_or_source_identity_validated':False,
        'e66_metadata_gate_preserved_value':False,'historical_e63_gate_value':False,'prior_runs_preserved':prior}
    out=ROOT/'reports/000068_verification.json'
    if out.exists():assert {k:v for k,v in read(str(out.relative_to(ROOT))).items() if k!='verified_at_utc'}==receipt
    else:
        with out.open('x') as f:json.dump(receipt|{'verified_at_utc':datetime.now(timezone.utc).isoformat()},f,indent=2);f.write('\n')
    print(json.dumps({k:v for k,v in receipt.items() if k!='prior_runs_preserved'}|{'prior_runs_preserved':len(prior)},indent=2))


if __name__=='__main__':main()
