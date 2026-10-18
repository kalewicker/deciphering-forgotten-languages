"""Offline verification of the one-query discovery ledger; performs no search."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys
import unicodedata
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from verify_correspondence_v6 import check_hashes


def read(path):
    return json.loads((ROOT / path).read_text())


def sha(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def norm(text):
    return ' '.join(unicodedata.normalize('NFC', text).casefold().split())


def main():
    run = ROOT / 'runs/000041_quotation_discovery'
    check_hashes(run)
    cfg = read('experiments/quotation_discovery_v41.json')
    pre = read('data/v41/preflight.json')
    saved = read('data/v41/search_response.json')
    ledger = read('data/v41/discovery_ledger.json')
    for path, expected in pre['hashes'].items():
        assert sha(path) == expected, path
    assert all(pre['hashes'][p] == h for p, h in cfg['input_hashes'].items())
    assert pre['hashes']['experiments/quotation_discovery_v41.json'] == sha('experiments/quotation_discovery_v41.json')
    q = cfg['quote']
    assert q == read('data/v39/frozen_queries.json')['queries'][0] and q['quote_id'] == 'quote00'
    assert read('data/v38/target_export.json')['text'][slice(*q['span'])] == q['text']
    expected_args = {'search_query': [{'q': '"' + q['text'] + '"'}], 'response_length': 'long'}
    assert cfg['request_arguments'] == pre['registered_request'] == saved['request_arguments'] == expected_args
    assert cfg['request_budget'] == ledger['request_denominator'] == ledger['request_attempts'] == 1
    assert saved['tool'] == 'web.run' and saved['error'] is None
    assert datetime.fromisoformat(cfg['registered_at_utc']) < datetime.fromisoformat(pre['sealed_at_utc'])
    start = datetime.strptime(saved['started_at_utc'], '%Y-%m-%d %H:%M:%S UTC').replace(tzinfo=timezone.utc)
    stop = datetime.strptime(saved['finished_at_utc'], '%Y-%m-%d %H:%M:%S UTC').replace(tzinfo=timezone.utc)
    assert datetime.fromisoformat(pre['sealed_at_utc']) < start <= stop
    text = saved['response']
    assert isinstance(text, str) and ledger['response_available']
    # Locate service result markers line by line, independently of the creation regex.
    lines = text.splitlines(keepends=True)
    offset = 0; headers = []
    for i, line in enumerate(lines):
        if i + 1 < len(lines) and '[wordlim:' in lines[i + 1]:
            marker = line.rstrip('\n').rfind(' (http')
            if marker >= 0 and line.rstrip('\n').endswith(')'):
                title = line[:marker]
                url = line.rstrip('\n')[marker + 2:-1]
                headers.append((offset, title, url))
        offset += len(line)
    assert len(headers) == ledger['attributable_hits'] == len(ledger['hit_ledger']) == 7
    eligible = []; visible = 0
    for i, (row, (begin, title, url)) in enumerate(zip(ledger['hit_ledger'], headers, strict=True)):
        end = headers[i + 1][0] if i + 1 < len(headers) else len(text)
        block = text[begin:end]
        assert row['rank'] == i and row['title'] == title and row['url'] == url
        assert row['response_span'] == [begin, end]
        assert row['response_text_sha256'] == hashlib.sha256(block.encode()).hexdigest()
        haystack = norm(block); needle = norm(q['text'])
        starts = [m.start() for m in re.finditer('(?=' + re.escape(needle) + ')', haystack)]
        assert len(row['hits']) == len(starts) and row['complete_quote_visible'] == bool(starts)
        visible += bool(starts)
        for hit, pos in zip(row['hits'], starts, strict=True):
            assert hit['normalized_span'] == [pos, pos + len(needle)]
            a, b = hit['source_span']
            assert block[a:b] == hit['source_quote'] and needle in norm(block[a:b])
            assert hit['response_span'] == [begin + a, begin + b]
            assert text[slice(*hit['response_span'])] == hit['source_quote']
            assert (a == 0 or block[a - 1].isspace()) and (b == len(block) or block[b].isspace())
        host = urlparse(url).hostname
        external = not (host == 'forgottenlanguages.org' or host.endswith('.forgottenlanguages.org'))
        repost = host == 'blog.seniorennet.be' and 'https://mysteriousuniverse.org/' in block
        assert row['external_non_fl'] == external and row['recognizable_repost'] == repost
        if repost:
            witness = row['repost_credit_witness']
            assert text[slice(*witness['span'])] == witness['text'] == 'https://mysteriousuniverse.org/'
        passes = bool(starts) and external and not repost
        assert row['eligible_external_lead'] == passes
        if passes:
            eligible.append(i)
    assert visible == ledger['returned_complete_quote_hit_count'] == 4
    assert eligible == [0] and ledger['eligible_external_lead_count'] == len(eligible)
    assert ledger['selected_rank'] == eligible[0] and ledger['lead_limit'] == 1
    assert [r['rank'] for r in ledger['hit_ledger'] if r['nominated']] == eligible[:1]
    expected_reasons = ['selected_first_external_complete_quote', 'existing_fl_target',
                        'recognizable_external_repost', 'recognizable_external_repost',
                        'complete_quote_not_visible', 'other_fl_page', 'complete_quote_not_visible']
    assert [r['decision_reason'] for r in ledger['hit_ledger']] == expected_reasons
    date = ledger['displayed_publication_date_witness']
    assert text[slice(*date['span'])] == date['text'] == '17 Jul 2018' and not date['historical_date_authenticated']
    assert not ledger['page_opened'] and not ledger['raw_page_captured'] and not ledger['source_identity_admitted']
    report = read('runs/000041_quotation_discovery/report.json')
    assert report['search_tool_calls'] == report['request_denominator'] == report['search_queries'] == 1
    assert report['attributable_hits'] == 7 and report['returned_complete_quote_hit_count'] == 4
    assert report['eligible_external_lead_count'] == 1 and report['selected_rank'] == 0
    assert report['selected_url'] == ledger['hit_ledger'][0]['url']
    assert report['selected_title'] == ledger['hit_ledger'][0]['title']
    for key in ['additional_page_or_source_requests', 'quoted_blocks_rescored', 'semantic_labels_admitted',
                'source_identities_admitted', 'independent_reviews_admitted', 'untouched_test_units_admitted', 'external_messages_sent']:
        assert report[key] == 0
    assert not report['raw_source_capture_available'] and not report['historical_date_authenticated']
    assert report['scientific_acceptance'] is report['semantic_evaluation_metrics'] is None
    previous = []
    for path in sorted((ROOT / 'runs').glob('000*/manifest.json')):
        if path.parent != run:
            check_hashes(path.parent); previous.append(path.parent.name)
    assert len(previous) == 40
    for path in (ROOT / 'reports').glob('*_deliverable_seal.json'):
        for name, expected in json.loads(path.read_text()).get('deliverable_hashes', {}).items():
            assert sha(name) == expected
    result = {'state': 'verified', 'manifest_sha256': sha('runs/000041_quotation_discovery/manifest.json'),
              'request_and_quote_freeze_verified': True, 'returned_hit_boundaries_and_witnesses_verified': True,
              'lead_selection_verified': True, 'search_engine_exact_match_enforcement_observable': False,
              'independent_scientific_review': False, 'raw_source_or_original_quote_origin_authenticated': False,
              'prior_runs_preserved': previous}
    out = ROOT / 'reports/000041_verification.json'
    if out.exists():
        assert {k: v for k, v in json.loads(out.read_text()).items() if k != 'verified_at_utc'} == result
    else:
        with out.open('x') as stream:
            json.dump(result | {'verified_at_utc': datetime.now(timezone.utc).isoformat()}, stream, indent=2)
            stream.write('\n')
    print(json.dumps({'state': 'verified', 'prior_runs_preserved': len(previous), 'selected_url': report['selected_url']}, indent=2))


if __name__ == '__main__':
    main()
