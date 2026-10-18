"""Independent frozen-query literal accounting; shared PDF extraction explicit."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib
import json
import re
import sys
import zipfile
from pypdf import PdfReader

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from verify_correspondence_v6 import check_hashes
from verify_dated_capture_scope_v38 import check_hits,norm
RUN='runs/000039_quoted_citation'
def read(p):return json.loads((ROOT/p).read_text())
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()


def main():
    check_hashes(ROOT/RUN)
    cfg=read('experiments/quoted_citation_v39.json');pre=read('data/v39/preflight.json')
    receipt=read('data/v39/acquisition/source/receipt.json')
    assert cfg['registered_at_utc']<pre['sealed_at_utc']<receipt['started_at_utc']
    assert receipt['requested_url']==cfg['source_url']=='https://arxiv.org/pdf/1809.09615v1'
    cmd=receipt['command'];assert cmd[0]=='curl' and '--insecure' not in cmd and '-k' not in cmd and '--retry' not in cmd
    assert cmd[cmd.index('--max-time')+1]=='20' and cmd[cmd.index('--max-redirs')+1]=='3'
    assert cmd[cmd.index('--proto')+1]==cmd[cmd.index('--proto-redir')+1]=='=https'
    assert receipt['max_body_bytes']==20971520
    for filename,r in receipt['artifacts'].items():
        p='data/v39/acquisition/source/'+filename
        assert sha(p)==r['sha256'] and (ROOT/p).stat().st_size==r['bytes']
    assert receipt['transport_complete']==(receipt['curl_returncode']==0 and receipt['http_status']==200 and 'body.bin' in receipt['artifacts'] and receipt['artifacts']['body.bin']['bytes']<=20971520)
    old=read(cfg['frozen_queries']);frozen=read('data/v39/frozen_queries.json');target=read(cfg['target'])['text']
    assert frozen['queries']==[{k:q[k] for k in ['quote_id','span','text','language_or_meaning_admitted']} for q in old['quotes']]
    assert [q['quote_id'] for q in frozen['queries']]==cfg['query_ids'] and len(frozen['queries'])==8
    for q in frozen['queries']:assert target[slice(*q['span'])]==q['text']
    export=read('data/v39/source_export.json');a=read('data/v39/assessment.json');report=read(RUN+'/report.json')
    assert export['transport_complete']==receipt['transport_complete']
    if export['material_available']:
        assert all(export[k] for k in ['transport_complete','pdf_magic','parseable','requested_version_visible','within_page_bound'])
        raw=(ROOT/'data/v39/acquisition/source/body.bin').read_bytes();assert raw.startswith(b'%PDF-')
        reader=PdfReader(ROOT/'data/v39/acquisition/source/body.bin')
        assert 0<len(reader.pages)<=100 and len(reader.pages)==len(export['pages'])
        assert re.search(r'(?<!\d)1809\.09615v1(?!\d)',reader.pages[0].extract_text())
        assert export['source_pdf_sha256']==hashlib.sha256(raw).hexdigest()
        for p,page in zip(export['pages'],reader.pages,strict=True):
            assert p['text']==page.extract_text() and p['unicode_scope']==[0,len(p['text'])]
            assert p['text_sha256']==hashlib.sha256(p['text'].encode()).hexdigest() and p['image_sha256']==sha(p['image'])
        qa=read('data/v39/visual_review.json')
        assert qa['reviewed_pages']==list(range(1,len(reader.pages)+1)) and not qa['independent_review']
    assert a['material_available']==export['material_available'] and a['quote_denominator']==8 and a['long_quote_denominator']==7
    assert a['source_page_denominator']==len(export['pages']) and len(a['quotes'])==8
    for original,row in zip(frozen['queries'],a['quotes'],strict=True):
        for k,v in original.items():assert row[k]==v
        if not export['material_available']:
            assert row['literal_source_presence'] is None and row['source_hits'] is None and not row['page_results'];continue
        assert len(row['page_results'])==len(export['pages'])
        expected_hits=[]
        for p,r in zip(export['pages'],row['page_results'],strict=True):
            assert p['page']==r['page'] and r['text_available']==bool(p['text'].strip())
            if p['text'].strip():
                check_hits(row['text'],p['text'],r['hits'])
                assert r['literal_presence']==bool(r['hits'])
                expected_hits += [{'page':p['page'],**h} for h in r['hits']]
            else:assert r['hits'] is r['literal_presence'] is None
        assert row['source_hits']==expected_hits
        expected=True if expected_hits else False if a['source_extraction_complete'] else None
        assert row['literal_source_presence'] is expected
    complete=bool(export['material_available'] and export['pages'] and all(p['text'].strip() for p in export['pages']))
    assert a['source_extraction_complete']==complete
    if export['material_available']:
        assert len(a['positive_controls'])==len(export['pages'])
        for p,c in zip(export['pages'],a['positive_controls'],strict=True):
            first=next((line for line in p['text'].splitlines() if line.strip()),None)
            assert c['page']==p['page'] and c['query']==first
            if first is not None:check_hits(first,p['text'],c['own_page_hits']);assert c['passed']==bool(c['own_page_hits'])
            else:assert c['passed'] is c['own_page_hits'] is None
        assert a['positive_controls_passed']==sum(c['passed'] is True for c in a['positive_controls'])
        negative=a['negative_control'];assert negative['query']=='flv38literalabsencecontrol20261018'
        for p in export['pages']:
            if p['text'].strip():check_hits(negative['query'],p['text'],[{k:v for k,v in h.items() if k!='page'} for h in negative['source_hits'] if h['page']==p['page']])
        assert negative['passed'] is (False if negative['source_hits'] else True if complete else None)
        for anchor,row in zip(cfg['anchors'],a['anchors'],strict=True):
            counts=[{'page':p['page'],'count':len(re.findall(r'(?<!\w)'+re.escape(norm(anchor))+r'(?!\w)',norm(p['text']))) if p['text'].strip() else None} for p in export['pages']]
            assert row['anchor']==anchor and row['source_page_counts']==counts
            assert row['source_observed_total']==sum(c['count'] or 0 for c in counts)
    else:
        assert a['quotes_with_literal_source_presence'] is a['long_quotes_with_literal_presence'] is a['positive_controls_passed'] is None
    long=[r['literal_source_presence'] for r in a['quotes'] if r['quote_id'] in cfg['primary_long_query_ids']]
    expected=True if any(v is True for v in long) else None if any(v is None for v in long) else False
    assert a['primary_long_block_presence'] is expected and a['expanded_name_literal_presence'] is a['quotes'][1]['literal_source_presence']
    assert a['query_outcomes_unavailable']==sum(q['literal_source_presence'] is None for q in a['quotes'])
    if export['material_available']:
        assert a['quotes_with_literal_source_presence']==sum(q['literal_source_presence'] is True for q in a['quotes'])
        assert a['long_quotes_with_literal_presence']==sum(v is True for v in long)
        bundle=ROOT/'data/v39/neutral_review';m=read('data/v39/neutral_review/manifest.json')
        with zipfile.ZipFile(ROOT/'data/v39/neutral_review_packet.zip') as z:
            assert set(z.namelist())==set(m['members'])|{'manifest.json'}
            for name,r in m['members'].items():assert hashlib.sha256(z.read(name)).hexdigest()==r['sha256']==sha(str((bundle/name).relative_to(ROOT)))
            assert z.read('source.pdf')==(ROOT/'data/v39/acquisition/source/body.bin').read_bytes()
            assert z.read('fl_post.txt').decode()==target
    check_hits(cfg['source_identifier'],target,a['selected_identifier_hits_in_target'])
    for rk,ak in [('quotes_with_literal_presence','quotes_with_literal_source_presence'),('long_quotes_with_literal_presence','long_quotes_with_literal_presence'),('primary_long_block_presence','primary_long_block_presence'),('expanded_name_literal_presence','expanded_name_literal_presence'),('query_outcomes_unavailable','query_outcomes_unavailable'),('positive_controls_passed','positive_controls_passed')]:assert report[rk]==a[ak]
    assert report['source_requests']==report['source_route_denominator']==1 and report['quote_denominator']==8 and report['long_quote_denominator']==7
    assert report['source_material_available']==export['material_available'] and report['source_pages']==len(export['pages'])
    assert report['target_recaptured'] is False and report['normalization_or_matcher_changed'] is False
    for k in ['opaque_passages_scored','semantic_labels_admitted','source_identities_admitted','independent_reviews_admitted','untouched_test_units_admitted','external_messages_sent']:assert report[k]==0
    assert report['scientific_acceptance'] is report['semantic_evaluation_metrics'] is None
    previous=[]
    for p in sorted((ROOT/'runs').glob('000*/manifest.json')):
        if p.parent!=ROOT/RUN:check_hashes(p.parent);previous.append(p.parent.name)
    assert len(previous)==38
    for p in (ROOT/'reports').glob('*_deliverable_seal.json'):
        for path,expected in json.loads(p.read_text()).get('deliverable_hashes',{}).items():assert sha(path)==expected
    result={'state':'verified','run_manifest_sha256':sha(RUN+'/manifest.json'),'frozen_eight_queries_preserved':True,
            'independent_literal_counts_and_witnesses':True,'source_reextraction_library_shared':True,'source_route_and_unavailability_accounting_verified':True,
            'primary_long_block_presence':a['primary_long_block_presence'],'prior_runs_preserved':previous,'semantic_or_source_identity_validated':False}
    out=ROOT/'reports/000039_verification.json'
    if out.exists():assert {k:v for k,v in read('reports/000039_verification.json').items() if k!='verified_at_utc'}==result
    else:
        with out.open('x') as f:json.dump(result|{'verified_at_utc':datetime.now(timezone.utc).isoformat()},f,indent=2);f.write('\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
