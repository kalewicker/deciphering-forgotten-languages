"""Independent raw evidence, provenance scope, denominator, and archive audit."""
from collections import Counter
from pathlib import Path
import json
from bs4 import BeautifulSoup
from fl_decipher.corpus import digest, dump_json
from verify_correspondence_v6 import check_hashes

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads(path.read_text())


def main():
    out = ROOT/'runs/000013_kamri_source_provenance'; manifest = check_hashes(out)
    b = read(ROOT/'benchmarks/kamri_provenance_v13.json')
    cfg = read(ROOT/'experiments/kamri_provenance_v13.json')
    ledger = read(ROOT/b['ledger']); report = read(out/'report.json')
    old = read(ROOT/'benchmarks/inputs/natural_v12_acquisition.json')
    old_b = read(ROOT/'benchmarks/kamri_natural_v12.json')
    assert b['documents'] == old_b['documents']
    assert ledger['registration_sha256'] == cfg['registration_sha256'] == digest((ROOT/cfg['registration']).read_bytes())
    assert cfg['configuration_materialized_after_acquisition'] and not cfg['analyst_blind']
    assert ledger['references_sealed_at_utc'] <= manifest['started_at_utc'] <= manifest['finished_at_utc']
    for k in ('records', 'metrics', 'model_executed', 'reference_eligible_queries', 'evaluated_queries'):
        assert report[k] == ledger[k]
    assert ledger['selected_works'] == ledger['selected_queries'] == ledger['selected_components'] == report['selected_queries'] == 2
    assert ledger['reference_eligible_queries'] == ledger['evaluated_queries'] == report['reference_eligible_queries'] == 0
    assert not ledger['model_executed'] and not manifest['model_executed'] and ledger['metrics'] is None
    assert report['new_supported_lexical_entries'] == 0 and not report['semantic_gold']
    assert not any((out/p).exists() for p in ('predictions.json', 'raw_scores.json', 'permutations.json', 'thresholds.json'))
    assert ledger['inspectable_publisher_work_excerpts'] == report['inspectable_publisher_work_excerpts'] == 1
    assert ledger['eligible_scoped_source_packets'] == 0
    for r, prior in zip(ledger['records'], old['records'], strict=True):
        for k in ('id', 'component', 'fl_url', 'fl_id', 'source_scope', 'fl_whitespace_words', 'fl_atom_count', 'roster_surface_uids'):
            assert r[k] == prior[k]
        assert r['selected_token_count'] == len(prior['fl_tokens'])
        req = r['gate']['requirements']
        assert all(type(v) is bool for v in req.values()) and not all(req.values())
        assert r['gate']['unmet'] == [k for k,v in req.items() if not v]
        assert not r['gate']['eligible'] and not req['source_scope_matches'] and not req['passage_reviewed']
        assert r['references'] is r['lexical_accuracy'] is r['controls'] is None
        info = b['documents'][r['fl_id']]; doc = read(ROOT/info['path'])
        assert digest((ROOT/info['path']).read_bytes()) == info['sha256']
        assert digest(doc['text'].encode()) == info['text_sha256']
    assert sum(r['selected_token_count'] for r in ledger['records']) == 322
    log = read(ROOT/'data/v13/discovery/search_log.json')
    counts = Counter(q['work'] for q in log['queries'])
    assert counts == {'liber_azazel':4, 'vile_darkness':4}
    assert all(len(urls) == len(set(urls)) == 4 for urls in log['source_routes'].values())
    receipts = [read(ROOT/p) for p in ledger['source_attempt_receipts']]
    urls = Counter(r['requested_url'] for r in receipts)
    assert len(receipts) == ledger['raw_requests'] == 9
    assert len(urls) == ledger['distinct_source_routes'] == 8
    assert set(urls) == {u for group in log['source_routes'].values() for u in group}
    assert sorted(urls.values()) == [1]*7 + [2] and urls[log['external_diagnostic_url']] == 2
    previous_urls = {read(ROOT/p)['requested_url'] for p in old['source_attempt_receipts']}
    assert not set(urls).intersection(previous_urls)
    for r in receipts:
        assert cfg['registration_file_mtime_utc'] < r['started_at_utc'] <= r['finished_at_utc']
        for artifact in r['artifacts'].values():
            p = Path(artifact['path'])
            assert p.stat().st_size == artifact['bytes'] and digest(p.read_bytes()) == artifact['sha256']
    raw = ROOT/'data/v13/acquisition'
    for key in ('azazel_site', 'azazel_site_external_diagnostic', 'azazel_church'):
        assert read(raw/key/'receipt.json')['curl_returncode'] == 6
    for key in ('azazel_profile', 'azazel_blog'):
        assert read(raw/key/'receipt.json')['http_status'] == 200
        text = BeautifulSoup((raw/key/'body.bin').read_bytes(), 'html.parser').get_text(' ', strip=True)
        assert 'liber azazel' not in text.lower()
    for key in ('vile_retailer', 'vile_dmsguild'):
        assert read(raw/key/'receipt.json')['http_status'] == 403
    assert read(raw/'vile_publisher/receipt.json')['final_url'] == 'https://company.wizards.com/en'
    capture = read(raw/'vile_library_capture/receipt.json')
    assert capture['http_status'] == 200 and capture['final_url'].startswith('https://web.archive.org/web/20161101210131/http://archive.wizards.com/')
    visible = BeautifulSoup((raw/'vile_library_capture/body.bin').read_bytes(), 'html.parser').get_text('\n', strip=True)
    assert visible == (ROOT/'data/v13/vile_capture_visible.txt').read_text()
    assert 'Book of Vile Darkness\nby Monte Cook' in visible and '12/06/2002' in visible
    assert 'Juiblex, the Faceless Lord' in visible and 'Our sneak peek' in visible and 'Defining Evil' not in visible
    assessment = read(ROOT/'data/v13/publisher_excerpt_assessment.json')
    assert not assessment['reference_eligible'] and not assessment['used_for_predictions']
    assert assessment['capture_final_url'] == capture['final_url']
    assert ledger['records'][0]['gate']['requirements']['authority_verified'] is False
    assert ledger['records'][1]['gate']['requirements']['authority_verified'] is True
    assert ledger['records'][1]['gate']['requirements']['edition_verified'] is True
    for p, sha in b['input_hashes'].items():
        assert digest((ROOT/p).read_bytes()) == sha, p
    previous = []
    for p in sorted((ROOT/'runs').glob('0000*')):
        if p == out:
            continue
        check_hashes(p)
        previous.append({'run_id':p.name, 'manifest_sha256':digest((p/'manifest.json').read_bytes())})
    assert len(previous) == 12
    result = {'state':'verified', 'run_id':out.name, 'manifest_sha256':digest((out/'manifest.json').read_bytes()),
        'selected_queries':2, 'selected_tokens':322, 'reference_eligible_queries':0, 'evaluated_queries':0,
        'inspectable_publisher_work_excerpts':1, 'accuracy_available':False, 'model_executed':False,
        'previous_runs':previous,
        'checks':['raw/input/code/output hashes and registration before raw retrieval',
            'four discovery queries and four source routes per work, one external DNS diagnostic',
            'unchanged FL documents, two selected works/components/queries, 322 selected token identities',
            'primary profile/blog fail to establish Liber Azazel author or provide prose',
            'archived contemporary publisher excerpt verified but wrong passage; scope gate refuses it',
            'retailer 403s and current publisher redirect preserved without challenge bypass',
            'unavailable metrics null, no model invocation or promoted lexical entries',
            'all twelve historical run archives unchanged'],
        'limitations':['Single-analyst provenance/scope assessment; no independent semantic gold', ledger['discovery_logging_limit']]}
    dump_json(ROOT/'reports/000013_verification.json', result)
    print(json.dumps({k:v for k,v in result.items() if k not in ('previous_runs', 'checks')}, indent=2))


if __name__ == '__main__':
    main()
