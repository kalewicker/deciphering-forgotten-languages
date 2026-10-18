"""Independent acquisition/selection/denominator audit and historical preservation."""
from pathlib import Path
import json
import re
from fl_decipher.corpus import digest, dump_json
from fl_decipher.natural_v12 import NOMINATIONS
from fl_decipher.text import sentences
from verify_correspondence_v6 import check_hashes

ROOT=Path(__file__).resolve().parents[1]


def read(p):
    return json.loads(p.read_text())


def independent_opening(text, numbered):
    if numbered:
        text='\n'.join(re.sub(r'^\s*\d+\.\s*','',line) for line in text.splitlines())
    text=' '.join(text.split());parts=re.findall(r'[^.!?]*[.!?]',text)
    selected=[]
    for part in parts:
        part=part.strip()
        if len((' '.join(selected+[part])).split())>180:break
        selected.append(part)
    return ' '.join(selected)


def main():
    out=ROOT/'runs/000012_kamri_natural_acquisition';m=check_hashes(out)
    b=read(ROOT/'benchmarks/kamri_natural_v12.json');cfg=read(ROOT/'experiments/kamri_natural_v12.json')
    ledger=read(ROOT/b['ledger']);report=read(out/'report.json')
    assert cfg['nominations']==NOMINATIONS and cfg['configuration_materialized_after_acquisition']
    assert cfg['registration_sha256']==ledger['registration_sha256']==digest((ROOT/cfg['registration']).read_bytes())
    assert b['selected_work_denominator']==b['selected_query_denominator']==ledger['selected_works']==ledger['selected_queries']==report['selected_works']==report['selected_queries']==2
    assert ledger['selected_components']==report['selected_components']==2
    assert ledger['fl_indexed_queries_acquired']==2 and ledger['fl_raw_queries_acquired']==0
    assert report['results']==ledger['records']
    assert len(report['results'])==2 and [r['id'] for r in report['results']]==[n['id'] for n in NOMINATIONS]
    assert ledger['reference_eligible_queries']==report['reference_eligible_queries']==report['evaluated_queries']==ledger['evaluated_queries']==0
    assert ledger['metrics'] is None and report['metrics'] is None
    assert not ledger['model_executed'] and not report['model_executed'] and not m['model_executed']
    assert report['new_supported_lexical_entries']==0 and not report['semantic_gold']
    assert not any((out/name).exists() for name in ['predictions.json','raw_scores.json','thresholds.json'])
    assert ledger['references_sealed_at_utc']<=m['started_at_utc']<=m['finished_at_utc']
    for path,sha in b['input_hashes'].items():assert digest((ROOT/path).read_bytes())==sha,path
    for r,n in zip(report['results'],NOMINATIONS,strict=True):
        assert r['component']==n['component'] and r['fl_url']==n['fl_url']
        assert not r['gate']['eligible'] and not all(r['gate']['requirements'].values())
        assert r['gate']['unmet']==[k for k,v in r['gate']['requirements'].items() if not v]
        assert r['references'] is None and r['lexical_accuracy'] is None and r['controls'] is None
        doc=read(ROOT/b['documents'][r['fl_id']]['path'])
        assert doc['snapshot']['acquisition_kind']=='indexed_web_excerpt' and doc['snapshot']['http_status'] is None and doc['snapshot']['final_url'] is None
        assert doc['text_sha256']==digest(doc['text'].encode())
        original=Path(doc['snapshot']['artifact']).read_text()
        assert independent_opening(original,r['id']=='liber_azazel')==doc['text']
        assert 0<r['fl_whitespace_words']==len(doc['text'].split())<=180
        fa=sentences(doc['text']);assert r['fl_atom_count']==len(fa)
        tokens=[(i,t) for i,a in enumerate(fa) for t in a.tokens]
        assert len(r['fl_tokens'])==len(tokens)==len({x['uid'] for x in r['fl_tokens']})
        for x,(i,t) in zip(r['fl_tokens'],tokens,strict=True):
            assert x['span']==[t.start,t.end] and x['atom_index']==i and x['form']==t.normalized
        assert r['roster_surface_uids']==[x['uid'] for x in r['fl_tokens'] if x['form'] in ('warċa','mirnaķ','misndin')]
    raw=ROOT/'data/v12/acquisition'
    receipts=[read(ROOT/p) for p in ledger['source_attempt_receipts']]
    assert len(receipts)==ledger['raw_requests']==6 and len({x['requested_url'] for x in receipts})==ledger['distinct_direct_source_routes']==5
    for r in receipts:
        assert cfg['registration_file_mtime_utc']<r['started_at_utc']<=r['finished_at_utc']
        for info in r['artifacts'].values():
            p=Path(info['path']);assert p.stat().st_size==info['bytes'] and digest(p.read_bytes())==info['sha256']
    assert read(raw/'liber_azazel_1/receipt.json')['http_status']==200
    assert b'boundless' not in (raw/'liber_azazel_1/body.bin').read_bytes().lower()
    assert read(raw/'liber_azazel_2/receipt.json')['http_status']==404
    assert not (raw/'liber_azazel_2/body.bin').read_bytes().startswith(b'%PDF')
    for key in ['liber_azazel_3','liber_azazel_3_escalated']:
        assert read(raw/key/'receipt.json')['curl_returncode']==6
    assert read(raw/'vile_darkness_1/receipt.json')['http_status']==200
    ia=read(raw/'vile_darkness_2/body.bin');assert ia['is_dark'] is True and not ia.get('files')
    preview=read(ROOT/'data/v12/quarantined_preview.json');assert not preview['reference_eligible'] and not preview['source_scope_complete'] and not preview['used_for_predictions']
    novelty=read(ROOT/'benchmarks/inputs/natural_v12_novelty.json')
    lexicon=read(ROOT/cfg['frozen_lexicon'])
    groups={g for item in lexicon.values() for c in item['candidates'] for g in c['independent_groups']}
    assert set(novelty['lexicon_groups'])==groups
    for n in novelty['records']:
        assert n['component'] not in groups and not n['historical_title_mentions'] and not n['long_exact_fl_duplicates'] and n['novel_in_declared_corpus']
    log=read(ROOT/'data/v12/discovery/search_log.json')
    for work in NOMINATIONS:
        assert len([q for q in log['initial_queries'] if q['work']==work['id']])==2
        assert len([q for q in log['fl_index_queries'] if q['work']==work['id']])==1
        assert len({r['requested_url'] for r in receipts if r['requested_url'] in work['source_routes']})<=3
    previous=[]
    for p in sorted((ROOT/'runs').glob('0000*')):
        if p==out:continue
        check_hashes(p);previous.append({'run_id':p.name,'manifest_sha256':digest((p/'manifest.json').read_bytes())})
    assert len(previous)==11
    result={'state':'verified','run_id':m['run_id'],'manifest_sha256':digest((out/'manifest.json').read_bytes()),
            'selected_works':2,'selected_components':2,'selected_queries':2,'indexed_fl_queries':2,'raw_fl_queries':0,
            'reference_eligible_queries':0,'evaluated_queries':0,'accuracy_available':False,'model_executed':False,
            'previous_runs':previous,'checks':['registration/ledger/config/raw/input/code/output hashes',
                'fixed two-work denominator, finite queries/routes and transparent sandbox retry',
                'independent opening/full-sentence/180-word selection and every selected FL token span',
                'HTTP 404, current raw prose absence, repeated DNS failure, and dark archive metadata',
                'quarantine and unmet provenance/reference gates; missing metrics remain null',
                'new components absent from persisted lexical support and declared historical groups',
                'no scorer/prediction/threshold artifacts; experiments 1–11 unchanged']}
    dump_json(ROOT/'reports/000012_verification.json',result)
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    main()
