"""Independent literal occurrence/witness, capture accounting and archive audit."""
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
import base64
import hashlib
import json
import re
import sys
import unicodedata
import zipfile
from urllib.parse import urlparse
from bs4 import BeautifulSoup

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from verify_correspondence_v6 import check_hashes
RUN = 'runs/000038_dated_capture_scope'
def read(p): return json.loads((ROOT/p).read_text())
def sha(p): return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def norm(s): return re.sub(r'\s+', ' ', unicodedata.normalize('NFC',s).casefold()).strip()


def check_hits(q, text, hits):
    needle, haystack = norm(q), norm(text)
    positions = [m.start() for m in re.finditer('(?='+re.escape(needle)+')',haystack)] if needle else []
    assert len(hits) == len(positions)
    words = list(re.finditer(r'\S+',text))
    for hit, at in zip(hits,positions,strict=True):
        stop = at+len(needle)
        assert hit['normalized_span'] == [at,stop]
        first, last = haystack[:at].count(' '), haystack[:stop-1].count(' ')
        a,b = words[first].start(),words[last].end()
        assert hit['source_span'] == [a,b] and hit['source_quote'] == text[a:b]
        assert needle in norm(text[a:b])


def main():
    check_hashes(ROOT/RUN)
    cfg, pre = read('experiments/dated_capture_scope_v38.json'), read('data/v38/preflight.json')
    assert cfg['registered_at_utc'] < pre['sealed_at_utc']
    receipts = {name:read(f'data/v38/acquisition/{name}/receipt.json') for name in ['metadata','replay']}
    for name,r in receipts.items():
        if not r['attempted']:
            assert name=='replay' and not r['transport_complete']
            continue
        cmd = r['command']
        assert r['started_at_utc'] > pre['sealed_at_utc']
        assert cmd[0]=='curl' and '--retry' not in cmd and '--insecure' not in cmd and '-k' not in cmd
        assert cmd[cmd.index('--proto')+1] == cmd[cmd.index('--proto-redir')+1] == '=https'
        assert cmd[cmd.index('--max-time')+1]=='20' and cmd[cmd.index('--max-redirs')+1]=='3'
        for filename,a in r['artifacts'].items():
            assert a['sha256']==sha(f'data/v38/acquisition/{name}/{filename}')
            assert a['bytes']==(ROOT/f'data/v38/acquisition/{name}/{filename}').stat().st_size
        assert r['transport_complete'] == (r['curl_returncode']==0 and r['http_status']==200 and 'body.bin' in r['artifacts'] and r['artifacts']['body.bin']['bytes']<=4194304)
    selection = read('data/v38/acquisition/selection.json')
    if receipts['metadata']['transport_complete']:
        try:data = read('data/v38/acquisition/metadata/body.bin')
        except (ValueError,TypeError):data = None
        expected_header = ['timestamp','original','statuscode','mimetype','digest']
        valid = isinstance(data,list) and len(data)==2 and data[0]==expected_header and isinstance(data[1],list) and len(data[1])==5 and all(isinstance(x,str) for x in data[1])
        if valid:
            stamp,original,status,mime,digest = data[1]
            valid = bool(re.fullmatch(r'\d{14}',stamp)) and stamp<=cfg['archive_cutoff'] and original==cfg['fl_url'] and status=='200' and mime=='text/html' and bool(re.fullmatch(r'[A-Z2-7]{32}',digest))
        assert selection['eligible'] == valid
    else:
        assert not selection['eligible']
    assert receipts['metadata']['requested_url']==cfg['cdx_url']
    if selection['eligible']:
        assert receipts['replay']['attempted']
        assert selection['replay_url']=='https://web.archive.org/web/'+selection['record']['timestamp']+'id_/'+cfg['fl_url']
        assert receipts['replay']['requested_url']==selection['replay_url']
    else:
        assert not receipts['replay']['attempted']
    gate = read('data/v38/dated_material_gate.json')
    assert gate['selection']==selection and gate['passed']==all(gate['checks'].values())
    assert gate['checks']['metadata_transport_complete']==receipts['metadata']['transport_complete']
    assert gate['checks']['replay_transport_complete']==receipts['replay']['transport_complete']
    assert gate['checks']['single_exact_cdx_record']==selection['eligible']
    date = None
    header_path=ROOT/'data/v38/acquisition/replay/headers.txt'
    if header_path.exists():
        chunks=re.split(r'\r?\n\r?\n',header_path.read_text())
        http=[c for c in chunks if re.match(r'HTTP/\S+\s+\d+',c)]
        values=re.findall(r'^memento-datetime:\s*(.+?)\s*$',http[-1] if http else '',re.I|re.M)
        if values:
            try:date=parsedate_to_datetime(values[-1]).strftime('%Y%m%d%H%M%S')
            except (ValueError,TypeError,OverflowError):pass
    assert gate['memento_timestamp']==date
    assert gate['checks']['memento_timestamp_matches']==bool(selection['record'] and date==selection['record']['timestamp'])
    if receipts['replay']['transport_complete']:
        raw=(ROOT/'data/v38/acquisition/replay/body.bin').read_bytes()
        assert gate['decoded_body_sha1_base32']==base64.b32encode(hashlib.sha1(raw).digest()).decode().rstrip('=')
        soup=BeautifulSoup(raw,'html.parser')
        bodies=soup.select('div.post-body')
        if gate['post_extraction']['eligible']:
            assert len(bodies)==1
            for node in bodies[0].select('script,style,noscript'):node.decompose()
            assert gate['post_extraction']['text']==bodies[0].get_text(' ',strip=True)
            assert norm(cfg['fl_title']) in norm(soup.title.get_text(' ',strip=True)) or any(norm(cfg['fl_title']) in norm(n.get_text(' ',strip=True)) for n in soup.select('.post-title'))
            effective=urlparse(receipts['replay']['final_url'])
            prefix='/web/'+selection['record']['timestamp']+'id_/'
            assert effective.hostname=='web.archive.org' and effective.path.startswith(prefix) and effective.path[len(prefix):]==cfg['fl_url']
    assert gate['checks']['post_body_and_identity_gate']==gate['post_extraction']['eligible']
    assert gate['checks']['decoded_body_matches_cdx_digest']==bool(selection['record'] and gate['decoded_body_sha1_base32']==selection['record']['digest'])
    if not gate['passed']:
        target=read('data/v38/target_export.json')
        parent=(ROOT/cfg['indexed_parent']).read_text()
        assert target['parent_sha256']==sha(cfg['indexed_parent']) and target['representation']=='indexed_line_derivative' and target['raw_post'] is False
        assert target['fixed_line_scope']==[28,88] and len(target['lineage'])==61
        assert [r['reported_line'] for r in target['lineage']]==list(range(28,89))
        pieces=[]
        for r in target['lineage']:
            assert parent[slice(*r['parent_span'])]==r['parent_quote']
            raw=r['parent_quote']
            cleaned=re.sub('\ue200cite\ue202([^\ue201]+)\ue201',lambda m:m.group(1).split('†')[1] if '†' in m.group(1) else '',raw).strip()
            assert r['derived_text']==cleaned==target['text'][slice(*r['derived_span'])]
            pieces.append(cleaned)
        assert target['text']=='\n'.join(pieces)
    else:
        target=read('data/v38/target_export.json')
        assert target['representation']=='dated_archival_post_body_export' and target['text']==gate['post_extraction']['text']
    exported=read('data/v38/source_export.json')
    pdf=PdfReader(ROOT/cfg['source_pdf'])
    assert len(pdf.pages)==len(exported['pages'])==8 and exported['source_pdf_sha256']==sha(cfg['source_pdf'])
    for p,page in zip(exported['pages'],pdf.pages,strict=True):
        assert p['text']==page.extract_text() and p['text_sha256']==hashlib.sha256(p['text'].encode()).hexdigest()
        assert p['unicode_scope']==[0,len(p['text'])] and p['image_sha256']==sha(p['image'])
    qa=read('data/v38/visual_review.json')
    assert qa['reviewed_pages']==list(range(1,9)) and not qa['independent_review']
    scope=read('data/v38/observable_scope.json')
    # Separate quote scanning from execution's regular-expression alternation.
    spans=[];pos=0;text=target['text']
    while pos<len(text):
        if text[pos] in ('"','“'):
            close='"' if text[pos]=='"' else '”'
            end=text.find(close,pos+1)
            if end>=0:
                if text[pos+1:end].strip():spans.append(([pos+1,end],text[pos+1:end]))
                pos=end+1;continue
        pos+=1
    assert len(spans)==scope['quote_denominator']==len(scope['quotes'])
    for (span,q),row in zip(spans,scope['quotes'],strict=True):
        assert row['span']==span and row['text']==q
        for page in exported['pages']:
            check_hits(q,page['text'],[{k:v for k,v in hit.items() if k!='page'} for hit in row['source_hits'] if hit['page']==page['page']])
        assert row['literal_source_presence']==bool(row['source_hits'])
    assert scope['quotes_with_literal_source_presence']==sum(q['literal_source_presence'] for q in scope['quotes'])
    assert len(scope['positive_controls'])==8
    for row,page in zip(scope['positive_controls'],exported['pages'],strict=True):
        assert row['query']==next(s for s in page['text'].splitlines() if s.strip())
        check_hits(row['query'],page['text'],row['own_page_hits'])
        assert row['passed']==bool(row['own_page_hits'])
    negative=scope['negative_control']
    assert negative['query']=='flv38literalabsencecontrol20261018'
    for page in exported['pages']:
        check_hits(negative['query'],page['text'],[{k:v for k,v in h.items() if k!='page'} for h in negative['source_hits'] if h['page']==page['page']])
    assert negative['passed']==(not negative['source_hits'])
    def count(a,t):return len(re.findall(r'(?<!\w)'+re.escape(norm(a))+r'(?!\w)',norm(t)))
    assert [r['anchor'] for r in scope['anchors']]==cfg['anchors']
    for row in scope['anchors']:
        assert row['target_count']==count(row['anchor'],text)
        assert row['source_page_counts']==[{'page':p['page'],'count':count(row['anchor'],p['text'])} for p in exported['pages']]
        assert row['source_total']==sum(r['count'] for r in row['source_page_counts'])
    check_hits('http://arxiv.org/abs/hep-ph/0209057v1',text,scope['exact_citation_hits_in_target'])
    report=read(RUN+'/report.json')
    assert report['dated_material_gate_passed']==gate['passed'] and report['dated_material_checks']==gate['checks']
    assert report['quote_denominator']==scope['quote_denominator'] and report['quotes_with_literal_source_presence']==scope['quotes_with_literal_source_presence']
    assert report['positive_controls_passed']==scope['positive_controls_passed']==sum(r['passed'] for r in scope['positive_controls'])
    assert report['negative_control_passed']==negative['passed'] and report['anchor_observations']==scope['anchors']
    assert report['route_slot_denominator']==2 and report['route_attempts']==sum(r['attempted'] for r in receipts.values())
    for k in ['natural_targets_rescored','opaque_passages_scored','semantic_labels_admitted','source_identities_admitted','independent_reviews_admitted','untouched_test_units_admitted','external_messages_sent','new_source_downloads']:
        assert report[k]==0
    assert report['scientific_acceptance'] is report['semantic_evaluation_metrics'] is None
    bundle=ROOT/'data/v38/scoped_materials'
    bm=read('data/v38/scoped_materials/manifest.json')
    with zipfile.ZipFile(ROOT/'data/v38/scoped_materials.zip') as z:
        assert set(z.namelist())==set(bm['members'])|{'manifest.json'}
        for name,a in bm['members'].items():
            assert hashlib.sha256(z.read(name)).hexdigest()==a['sha256']==sha(str((bundle/name).relative_to(ROOT)))
        assert z.read('source.pdf')==(ROOT/cfg['source_pdf']).read_bytes()
    previous=[]
    for p in sorted((ROOT/'runs').glob('000*/manifest.json')):
        if p.parent!=ROOT/RUN:check_hashes(p.parent);previous.append(p.parent.name)
    assert len(previous)==37
    for p in (ROOT/'reports').glob('*_deliverable_seal.json'):
        for path,expected in json.loads(p.read_text()).get('deliverable_hashes',{}).items():assert sha(path)==expected
    result={'state':'verified','run_manifest_sha256':sha(RUN+'/manifest.json'),'independent_literal_counts_and_witnesses':True,
            'source_text_reextracted':True,'source_extraction_library_shared':True,'dated_material_gate_passed':gate['passed'],
            'route_accounting_and_bundle_verified':True,'prior_runs_preserved':previous,'source_identity_or_meaning_validated':False}
    path=ROOT/'reports/000038_verification.json'
    if path.exists():assert {k:v for k,v in read('reports/000038_verification.json').items() if k!='verified_at_utc'}==result
    else:
        with path.open('x') as f:json.dump(result|{'verified_at_utc':datetime.now(timezone.utc).isoformat()},f,indent=2);f.write('\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
