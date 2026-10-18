"""Independent graph traversal, extraction, token and raw-evidence audit."""
from datetime import datetime, timezone
from pathlib import Path
import json
import re
from bs4 import BeautifulSoup
from fl_decipher.corpus import digest, dump_json
from fl_decipher.text import sentences
from verify_correspondence_v6 import check_hashes

ROOT = Path(__file__).resolve().parents[1]


def read(p):
    return json.loads(p.read_text())


def main():
    out = ROOT/'runs/000014_kamri_source_feasibility'; m = check_hashes(out)
    b = read(ROOT/'benchmarks/kamri_feasibility_v14.json'); l = read(ROOT/b['ledger'])
    cfg = read(ROOT/'experiments/kamri_feasibility_v14.json')
    report = read(out/'report.json'); inv = read(ROOT/'data/v14/inventory_components.json')
    audit = read(ROOT/'data/v14/component_audit.json'); log = read(ROOT/'data/v14/discovery/search_log.json')
    assert l['registration_sha256'] == cfg['registration_sha256'] == digest((ROOT/cfg['registration']).read_bytes())
    assert l['selected_works'] == l['selected_components'] == l['selected_queries'] == cfg['selected_query_denominator'] == 1
    assert l['reference_eligible_queries'] == l['evaluated_queries'] == 0 and l['metrics'] is None
    assert not l['model_executed'] and not m['model_executed'] and not l['semantic_gold'] and l['new_supported_lexical_entries']==0
    assert all(report[k]==v for k,v in l.items())
    assert l['references_sealed_at_utc'] <= m['started_at_utc'] <= m['finished_at_utc']
    assert not any((out/p).exists() for p in ('predictions.json','raw_scores.json','thresholds.json','permutations.json'))
    assert sorted(p['entry'] for p in inv['posts']) == list(range(1,25))
    edges = {}
    for p in inv['posts']:
        for x in p['works']:
            edges.setdefault(x,set()).update(p['works'])
    unseen = set(edges); groups = []
    while unseen:
        pending = [min(unseen)]; found = set()
        while pending:
            node = pending.pop()
            if node in found:
                continue
            found.add(node); pending.extend(edges[node]-found)
        unseen -= found; groups.append(sorted(found))
    groups.sort()
    assert groups == audit['components'] and len(groups)==14 and len(edges)==22
    historical = set()
    for p, sha in audit['historical_document_hashes'].items():
        assert digest((ROOT/p).read_bytes())==sha
        historical.add(read(ROOT/p)['source_group'])
    prior = read(ROOT/'benchmarks/inputs/provenance_v13_acquisition.json')
    historical.update(r['component'] for r in prior['records'])
    assert set(audit['historical_groups'])==historical
    exposed = set(historical)
    for g in historical:
        exposed.update(inv['prior_component_aliases'].get(g,[]))
    assert [g for g in groups if not exposed.intersection(g)] == audit['unused_before_v14'] == [['religious_architecture']]
    assert all((set(g)&exposed) or g==['religious_architecture'] for g in groups)
    assert l['remaining_unexposed_components_in_inventory_after_v14']==[]
    assert not audit['historical_title_mentions']
    for p in audit['historical_document_hashes']:
        assert 'religious architecture' not in ' '.join(read(ROOT/p)['text'].lower().split())
    lex = read(ROOT/'runs/000001_kamri_excerpt_baseline/lexicon.json')
    lex_groups={g for v in lex.values() for c in v['candidates'] for g in c['independent_groups']}
    assert sorted(lex_groups)==audit['lexicon_groups'] and 'religious_architecture' not in lex_groups
    assert len(log['source_queries'])==3 and len(log['source_routes'])==4
    known = [r['url'] for r in log['source_routes'] if r['url']]
    assert len(known)==len(set(known))==3
    assert sum(r['url'] is None for r in log['source_routes'])==1
    assert l['raw_source_requests']==3 and l['raw_metadata_requests']==1
    receipts=[read(ROOT/p) for p in l['source_attempt_receipts']]
    assert len(receipts)==3 and {r['requested_url'] for r in receipts}==set(known)
    for r in receipts+[read(ROOT/'data/v14/metadata/jstor_book/receipt.json')]:
        assert cfg['registration_file_mtime_utc']<r['started_at_utc']<=r['finished_at_utc']
        for info in r['artifacts'].values():
            p=Path(info['path']); assert p.stat().st_size==info['bytes'] and digest(p.read_bytes())==info['sha256']
    raw=ROOT/'data/v14/acquisition'
    assert read(raw/'architecture_pdf/receipt.json')['http_status']==403
    assert not (raw/'architecture_pdf/body.bin').read_bytes().startswith(b'%PDF')
    assert read(raw/'architecture_publisher/receipt.json')['http_status']==202 and not (raw/'architecture_publisher/body.bin').read_bytes()
    assert read(raw/'architecture_cambridge/receipt.json')['http_status']==200
    s=BeautifulSoup((raw/'architecture_cambridge/body.bin').read_bytes(),'html.parser')
    assert '2013' in s.get_text() and 'Amsterdam University Press' in s.get_text() and 'Oskar Verkaaik' in s.get_text()
    summary=s.select_one('div.summary'); summary.find('h2').decompose()
    st=summary.get_text(' ',strip=True)
    assert st==(ROOT/'data/v14/source_opening.txt').read_text()
    review=read(ROOT/'data/v14/source_review_before_fl.json')
    assert review['text_sha256']==digest(st.encode()) and review['source_words']==len(st.split())==380
    assert review['reviewed_at_utc'] < datetime.fromtimestamp((ROOT/log['fl_index_response']).stat().st_mtime,timezone.utc).isoformat()
    raw_fl=' '.join((ROOT/'data/v14/fl_indexed_opening.txt').read_text().split())
    parts=re.findall(r'[^.!?]*[.!?]',raw_fl); selected=[]
    for p in parts:
        if len(' '.join(selected+[p.strip()]).split())>180:
            break
        selected.append(p.strip())
    ft=' '.join(selected)
    fd=read(ROOT/b['documents']['fl_religious_architecture_v14']['path'])
    sd=read(ROOT/b['documents']['source_religious_architecture_v14']['path'])
    assert fd['text']==ft and sd['text']==st and len(ft.split())==174
    assert fd['snapshot']['acquisition_kind']=='indexed_web_excerpt' and fd['snapshot']['http_status'] is None
    assert sd['snapshot']['acquisition_kind']=='raw_http_attempt' and sd['snapshot']['http_status']==200
    result=l['records'][0]; assert result['lead_provisional'] and result['references'] is result['lexical_accuracy'] is result['controls'] is None
    fa,sa=sentences(ft),sentences(st)
    assert result['length_diagnostic']['fl']==[len(a.tokens) for a in fa]
    assert result['length_diagnostic']['source']==[len(a.tokens) for a in sa]
    assert len(fa)==len(sa)==12 and all(len(a.tokens)!=len(b.tokens) for a,b in zip(fa,sa,strict=True))
    tokens=[(j,t) for j,a in enumerate(fa) for t in a.tokens]
    assert len(tokens)==len(result['fl_tokens'])==174
    assert len({t['uid'] for t in result['fl_tokens']})==174
    for x,(j,t) in zip(result['fl_tokens'],tokens,strict=True):
        assert x['atom_index']==j and x['span']==[t.start,t.end] and x['form']==t.normalized
    assert result['roster_surface_uids']==[x['uid'] for x in result['fl_tokens'] if x['form'] in ('warċa','mirnaķ','misndin')]
    for p in audit['historical_document_hashes']:
        d=read(ROOT/p)
        if d['kind']=='fl':
            assert not {a.text for a in fa if len(a.tokens)>=8}.intersection(a.text for a in sentences(d['text']))
    req=result['gate']['requirements']
    assert req['correspondence_reviewed'] is False and all(v for k,v in req.items() if k!='correspondence_reviewed')
    assert not result['gate']['eligible'] and result['gate']['unmet']==['correspondence_reviewed']
    ref=read(ROOT/l['reference_review'])
    assert not ref['reviewed_correspondence_available'] and not ref['model_used_for_reference_review'] and not ref['semantic_gold']
    for p,sha in b['input_hashes'].items():
        assert digest((ROOT/p).read_bytes())==sha,p
    previous=[]
    for p in sorted((ROOT/'runs').glob('0000*')):
        if p==out:
            continue
        check_hashes(p); previous.append({'run_id':p.name,'manifest_sha256':digest((p/'manifest.json').read_bytes())})
    assert len(previous)==13
    receipt={'state':'verified','run_id':out.name,'manifest_sha256':digest((out/'manifest.json').read_bytes()),
        'selected_queries':1,'selected_tokens':174,'source_words':380,'reference_eligible_queries':0,
        'model_executed':False,'accuracy_available':False,'inventory_posts':24,'source_work_nodes':22,
        'components':14,'unused_components_before_v14':1,'unused_components_after_v14':0,
        'previous_runs':previous,
        'checks':['independent adjacency traversal agrees with frozen source-component boundaries',
            'all selected work/query/token denominators retained and references unavailable',
            'raw receipts, deterministic publisher extraction, edition and source-first timestamp',
            'independent full-sentence FL cap, every selected token span and no long exact duplicate',
            'three searches and four conservatively charged source routes; unknown XML URL disclosed',
            'no fabricated correspondence, scorer artifacts or promoted meanings',
            'input/code/output hashes and all thirteen historical runs preserved'],
        'limitations':['Publisher preview only, no full chapter/PDF','Single-analyst unresolved correspondence, not independent semantic gold',
            'Failed XML link destination not returned; counted conservatively','Exposure exhaustion applies only to the public 24-post inventory and declared persisted inputs']}
    dump_json(ROOT/'reports/000014_verification.json',receipt)
    print(json.dumps({k:v for k,v in receipt.items() if k not in ('previous_runs','checks')},indent=2))


if __name__=='__main__':
    main()
