"""Offline hash, route, nomination and fail-closed capacity verification."""
from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import urlparse, parse_qsl
import hashlib
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from verify_correspondence_v6 import check_hashes
RUN = 'runs/000037_source_intake'


def read(p):
    return json.loads((ROOT/p).read_text())


def sha(p):
    return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()


def key(url):
    p = urlparse(url)
    return p.hostname, p.path.rstrip('/'), tuple((k,v) for k,v in parse_qsl(p.query) if k != 'm' and not k.startswith('utm_'))


def verify_request(relative, expected_url, kind):
    receipt = read(relative+'/receipt.json')
    assert receipt['attempted'] and receipt['requested_url'] == expected_url and receipt['kind'] == kind
    cmd = receipt['command']
    assert cmd[0] == 'curl' and '--retry' not in cmd and '--insecure' not in cmd and '-k' not in cmd
    assert '--cookie' not in cmd and '--user' not in cmd
    assert cmd[cmd.index('--max-time')+1] == '20' and cmd[cmd.index('--connect-timeout')+1] == '8'
    assert cmd[cmd.index('--max-redirs')+1] == '3' and cmd[cmd.index('--proto')+1] == '=https'
    assert cmd[cmd.index('--proto-redir')+1] == '=https'
    for filename, artifact in receipt['artifacts'].items():
        assert artifact['sha256'] == sha(relative+'/'+filename)
        assert artifact['bytes'] == (ROOT/relative/filename).stat().st_size
    assert receipt['max_body_bytes'] == (20 if kind == 'source' else 4)*1024*1024
    expected_complete = receipt['curl_returncode'] == 0 and receipt['http_status'] == 200 and 'body.bin' in receipt['artifacts'] and receipt['artifacts']['body.bin']['bytes'] <= receipt['max_body_bytes']
    assert receipt['transport_complete'] == expected_complete
    assert receipt['started_at_utc'] > read('data/v37/preflight.json')['sealed_at_utc']
    return receipt


def main():
    check_hashes(ROOT/RUN)
    cfg = read('experiments/source_intake_v37.json')
    pre = read('data/v37/preflight.json')
    revision = read('experiments/source_intake_v37_discovery_revision1.json')
    assert cfg['registered_at_utc'] < revision['registered_at_utc'] < pre['sealed_at_utc']
    for path, expected in revision['input_hashes'].items():
        assert sha(path) == expected
    nominations = read('data/v37/nominations.json')
    old = {key(u) for u in read('data/v37/known_exposure.json')['urls']}
    expected, hit_rows, slots = [], [], []
    empty = []
    for i in range(4):
        d = read(f'data/v37/discovery/query{i}.json')
        assert d['query_index'] == i and d['query'] == cfg['queries'][i]
        assert d['requested_at_utc'] > revision['registered_at_utc']
        matches = list(re.finditer(r'^([^\n]+) \((https?://[^\s)]+)\)\n[^\n]*\[wordlim: \d+\]', d['response'], re.M))
        if not matches:
            empty.append(i)
        chosen = []
        for rank, m in enumerate(matches):
            title, url = m.group(1).strip(), m.group(2)
            parsed = urlparse(url)
            valid = parsed.hostname == 'forgottenlanguages-full.forgottenlanguages.org' and bool(re.fullmatch(r'/\d{4}/\d{2}/[^/]+\.html', parsed.path))
            reason = 'not_dated_post_permalink' if not valid else 'already_exposed_or_duplicate' if key(url) in old else 'outside_two_post_slots' if len(chosen) >= 2 else None
            hit_rows.append({'query_index':i,'rank':rank,'title':title,'url':url,'selected':reason is None,'exclusion_reason':reason})
            if reason is None:
                nid = f'post{len(expected):02d}'
                expected.append({'post_id':nid,'query_index':i,'rank':rank,'url':url,'title':title.removeprefix('Forgotten Languages Full: '),
                                 'search_snippet_exposure':True,'untouched_test_eligible':False})
                chosen.append(nid)
                old.add(key(url))
        slots += [{'query_index':i,'slot':j,'post_id':chosen[j] if j<len(chosen) else None,
                   'unfilled_reason':None if j<len(chosen) else 'no_eligible_result_within_nomination'} for j in range(2)]
    assert nominations == {'nominees': expected,'hit_ledger':hit_rows,'slots':slots,'queries_with_no_hits':empty}
    posts = read('data/v37/post_metadata.json')['records']
    assert len(posts) == len(expected) <= 8
    for n, post in zip(expected, posts, strict=True):
        assert n['post_id'] == post['post_id']
        r = verify_request('data/v37/acquisition/'+n['post_id'], n['url'], 'native')
        assert post['target_prose_compared'] is False
        if post['representation'] == 'indexed_browser_extraction':
            assert not r['transport_complete'] and post['raw_capture_available'] is False
            fallback = read(post['fallback_path'])
            assert fallback['url'] == n['url']
            assert r['finished_at_utc'] < fallback['requested_at_utc']
    selection = read('data/v37/source_selection.json')
    assert len(selection['selected']) <= 4 and selection['unfilled_source_slots'] == 4-len(selection['selected'])
    selected_rows = [r for r in selection['candidate_ledger'] if r['selected']]
    assert len(selected_rows) == len(selection['selected'])
    for row, source in zip(selected_rows, selection['selected'], strict=True):
        assert row['identifier'] == source['identifier'] and row['post_id'] == source['post_id'] and row['request_url'] == source['request_url']
        assert source['novelty'] == 'provisional_identifier_not_in_saved_inventory' and not source['connected_work_independence_confirmed']
        assert not source['untouched_test_eligible']
        r = verify_request('data/v37/source_acquisition/'+source['source_id'], source['request_url'], 'source')
        assert selection['frozen_at_utc'] < r['started_at_utc']
    ledger = read('data/v37/capacity_ledger.json')
    assert ledger['source_slot_denominator'] == 4 and ledger['selected_work_denominator'] == len(selection['selected'])
    assert ledger['unfilled_source_slots'] == 4-len(selection['selected'])
    for row in ledger['records']:
        r = read('data/v37/source_acquisition/'+row['source_id']+'/receipt.json')
        assert row['transport_available'] == r['transport_complete']
        if row['representation'] == 'raw_pdf_unreviewed':
            assert (ROOT/'data/v37/source_acquisition'/row['source_id']/'body.bin').read_bytes().startswith(b'%PDF-')
        assert not row['source_prose_verified'] and not row['review_ready'] and not row['independent_review_completed']
        assert not row['eligible_for_four_work_capacity'] and row['reviewed_nonoverlapping_passages'] == 0
    report = read(RUN+'/report.json')
    assert report['post_nominees'] == report['raw_post_attempts'] == len(posts)
    assert report['unfilled_post_slots'] == sum(s['post_id'] is None for s in slots)
    assert report['queries_with_no_eligible_results'] == empty
    assert report['raw_posts_available'] == sum(p['raw_capture_available'] for p in posts)
    assert report['selected_source_attempts'] == len(selection['selected'])
    assert report['source_transport_available'] == sum(r['transport_available'] for r in ledger['records'])
    assert report['raw_pdfs_available_for_later_review'] == sum(r['representation']=='raw_pdf_unreviewed' for r in ledger['records'])
    assert report['indexed_fallback_opens'] == len(list((ROOT/'data/v37/fallback').glob('*.json'))) <= 8
    assert report['search_executions'] == 8 and report['discovery_queries_distinct'] == 4
    assert report['scientific_acceptance'] is report['semantic_evaluation_metrics'] is None
    assert report['four_work_capacity_gate_passed'] is False
    for k in ['verified_source_prose_units','review_ready_pairs','independent_reviews_completed','qualifying_unexposed_reviewed_works',
              'semantic_labels_admitted','source_identities_admitted','independent_reviews_admitted','untouched_test_units_admitted',
              'natural_targets_rescored','lexicon_updates','external_messages_sent']:
        assert report[k] == 0
    template = read('data/v37/review_return_template.json')
    assert template['review_completed'] is False and template['reviewer_name'] is None and not template['span_correspondences']
    previous = []
    for p in sorted((ROOT/'runs').glob('000*/manifest.json')):
        if p.parent != ROOT/RUN:
            check_hashes(p.parent)
            previous.append(p.parent.name)
    assert len(previous) == 36
    for p in (ROOT/'reports').glob('*_deliverable_seal.json'):
        for path, expected_hash in json.loads(p.read_text()).get('deliverable_hashes', {}).items():
            assert sha(path) == expected_hash
    result = {'state':'verified','verified_at_utc':datetime.now(timezone.utc).isoformat(),'run_manifest_sha256':sha(RUN+'/manifest.json'),
              'independent_post_nomination_reconstruction':True,'route_hash_limits_and_capacity_accounting_verified':True,
              'citation_metadata_parser_shared_with_execution':True,'source_identity_or_semantics_validated':False,
              'prior_runs_preserved':previous,'four_work_capacity_gate_passed':False}
    path = ROOT/'reports/000037_verification.json'
    if path.exists():
        assert {k:v for k,v in read('reports/000037_verification.json').items() if k!='verified_at_utc'} == {k:v for k,v in result.items() if k!='verified_at_utc'}
    else:
        with path.open('x') as f:
            json.dump(result,f,indent=2)
            f.write('\n')
    print(json.dumps(result,indent=2))


if __name__ == '__main__':
    main()
