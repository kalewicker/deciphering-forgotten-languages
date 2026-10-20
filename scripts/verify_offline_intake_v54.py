"""Reconstruct prospective decisions with separate metadata/gate implementations."""
from datetime import date, datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys
import unicodedata
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from verify_correspondence_v6 import check_hashes
from verify_cohort_scope_v52 import reconstruct as reconstruct_scope
from verify_routing_v53 import key, title, reconstruct as reconstruct_route


def read(p): return json.loads((ROOT / p).read_text())
def sha(p): return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()


def observations(raw):
    soup = BeautifulSoup(raw, 'html.parser')
    urls = [{'channel': 'canonical', 'value': t.get('href', '')} for t in soup.find_all('link') if 'canonical' in t.get('rel', [])]
    urls += [{'channel': 'og_url', 'value': t.get('content', '')} for t in soup.find_all('meta', attrs={'property': 'og:url'})]
    titles = [{'channel': 'html_title', 'value': t.get_text(' ', strip=True)} for t in soup.find_all('title')]
    titles += [{'channel': 'og_title', 'value': t.get('content', '')} for t in soup.find_all('meta', attrs={'property': 'og:title'})]
    errors = []
    for index, tag in enumerate(soup.find_all('script', attrs={'type': 'application/ld+json'})):
        try: stack = [json.loads(tag.string or tag.get_text())]
        except (ValueError, TypeError): errors.append(index); continue
        while stack:
            node = stack.pop()
            if isinstance(node, list): stack.extend(reversed(node))
            elif isinstance(node, dict):
                types = node.get('@type', []); types = [types] if isinstance(types, str) else types
                if isinstance(types, list) and any(t == 'Article' or t == 'NewsArticle' for t in types):
                    headline = node.get('headline')
                    titles.append({'channel': 'article_headline', 'value': headline if isinstance(headline, str) else ''})
                stack.extend(reversed(list(node.values())))
    return {'urls': urls, 'titles': titles, 'json_ld_parse_errors': errors,
            'h1_inventory': [h.get_text(' ', strip=True) for h in soup.find_all('h1')],
            'publication_values': [m.get('content', '') for m in soup.find_all('meta', attrs={'property': 'article:published_time'})]}


def decision(raw, receipt, spec, cfg, body, scope, accounting, route):
    meta = observations(raw); expected = key(spec['url']); bindings = []
    canon = [u['value'] for u in meta['urls'] if u['channel'] == 'canonical']
    required_checks = ['complete_200', 'html_content_type', 'consistent_publisher_chain',
                       'canonical_matches_frozen', 'three_title_channels_match_frozen']
    for item in meta['urls']:
        if item['channel'] != 'og_url': continue
        u = item['value']; direct = expected is not None and key(u) == expected
        alias = bool(not direct and expected and key(u) is not None and route
            and route.get('current_alias_supported') and all(route.get('checks', {}).get(k) is True for k in required_checks)
            and route.get('requested_url') == u and route.get('expected_canonical_url') == spec['url']
            and key(route.get('final_url')) == expected and route.get('category') == 'observed_redirect_to_canonical'
            and route.get('num_redirects', 0) > 0)
        bindings.append({'url': u, 'binding': 'direct_canonical' if direct else 'saved_v53_redirect' if alias else 'unresolved'})
    dates = []; agree = bool(meta['publication_values'])
    for value in meta['publication_values']:
        try: dates.append((date.fromisoformat(value) if len(value) == 10 else datetime.fromisoformat(value).date()).isoformat())
        except (ValueError, TypeError): agree = False
    agree = agree and len(set(dates)) == 1
    titles = meta['titles']; runs = scope['paragraph_runs']
    topic = ' '.join(t['value'] for t in titles) + ' ' + ' '.join(r['text'] for r in runs)
    topic = ' '.join(unicodedata.normalize('NFC', topic).casefold().split())
    checks = {'complete_200': receipt.get('transport_complete') is True and receipt.get('http_status') == 200 and receipt.get('curl_returncode') == 0,
        'html_markup': b'<html' in raw.lower(),
        'final_url_matches': expected is not None and key(receipt.get('final_url')) == expected,
        'all_canonical_fields_match': bool(expected and canon and all(key(u) == expected for u in canon)),
        'all_og_urls_bound': bool(bindings) and not any(b['binding'] == 'unresolved' for b in bindings),
        'three_metadata_title_channels_agree': {'html_title', 'og_title', 'article_headline'} <= {t['channel'] for t in titles}
            and not meta['json_ld_parse_errors'] and all(title(t['value']) == title(spec['expected_title']) for t in titles),
        'present_h1_values_match': all(title(h) == title(spec['expected_title']) for h in meta['h1_inventory']),
        'scope_and_accounting_valid': bool(accounting) and all(accounting.values()),
        'no_challenge_text': not any(sig in body.casefold() for sig in cfg['challenge_signatures']),
        'minimum_nonempty_paragraph_runs': len(runs) >= cfg['minimum_paragraph_runs'],
        'minimum_run_characters': sum(len(r['text']) for r in runs) >= cfg['minimum_run_characters'],
        'publication_date_agrees': agree, 'publication_date_in_window': agree and cfg['date_min'] <= dates[0] <= cfg['date_max'],
        'native_topic_terms': bool(re.search(r'\bneutrinos?\b', topic) and re.search(r'\b(?:anita|antarctic|antarctica)\b', topic))}
    return {'id': spec['id'], 'development_capture_eligible': all(checks.values()), 'checks': checks,
        'unmet': [k for k, v in checks.items() if not v], 'metadata': meta, 'og_url_bindings': bindings,
        'parsed_publication_dates': dates, 'scope_error': None, 'scope_accounting': accounting,
        'paragraph_run_count': len(runs), 'paragraph_run_characters': sum(len(r['text']) for r in runs),
        'paragraph_run_spans': [r['body_span'] for r in runs], 'body_text_sha256': hashlib.sha256(body.encode()).hexdigest(),
        'v50_ready_unchanged': spec['v50_ready_unchanged'], 'previously_inspected_development_data': True,
        'historical_bytes_authenticated': False, 'independent_source_group_admitted': False,
        'false_parent_certified': False, 'untouched_test_unit_admitted': False}


def main():
    run = ROOT / 'runs/000054_offline_intake'; check_hashes(run)
    cfg = read('experiments/offline_intake_v54.json'); pre = read('data/v54/preflight.json')
    report = read('runs/000054_offline_intake/report.json'); manifest = read('runs/000054_offline_intake/manifest.json')
    for p, h in pre['hashes'].items(): assert sha(p) == h, p
    for p, h in cfg['input_hashes'].items(): assert pre['hashes'][p] == h
    assert pre['hashes']['experiments/offline_intake_v54.json'] == sha('experiments/offline_intake_v54.json')
    assert cfg['registered_at_utc'] < pre['sealed_at_utc'] < manifest['finished_at_utc']
    assert cfg['network_request_budget'] == 0 and cfg['candidate_denominator'] == cfg['candidate_capacity_required'] == 4
    original_cfg = read('experiments/publisher_intake_v50.json')
    assert cfg['minimum_paragraph_runs'] == original_cfg['minimum_paragraphs'] == 3
    assert cfg['minimum_run_characters'] == original_cfg['minimum_paragraph_characters'] == 1000
    for k in ['source_selector', 'date_min', 'date_max', 'challenge_signatures']: assert cfg[k] == original_cfg[k]
    assert [p['id'] for p in cfg['pages']] == ['reference_v42', 'q00s00', 'q00s01', 'q01s00', 'q01s01']
    intake = read('runs/000050_publisher_intake/report.json'); old_pages = read('experiments/cohort_scope_v52.json')['pages']
    route_cfg = read('experiments/routing_v53.json'); rows = []
    for spec, old in zip(cfg['pages'], old_pages):
        for k, v in old.items(): assert spec[k] == v
        raw = (ROOT / spec['raw']).read_bytes(); receipt = read(spec['receipt']); body = read(spec['observation'])[spec['body_field']]
        assert receipt['artifacts']['body.bin']['sha256'] == sha(spec['raw']) and receipt['artifacts']['body.bin']['bytes'] == len(raw)
        scope, checks = reconstruct_scope(raw, body, cfg['source_selector']); assert scope == read(spec['scope'])
        route = None
        if spec['id'] != 'reference_v42':
            assert spec['route'] == f"data/v53/{spec['id']}_route.json"
            route_spec = next(r for r in route_cfg['routes'] if r['id'] == spec['id'])
            base = f"data/v53/acquisition/{spec['id']}"
            route = reconstruct_route((ROOT / base / 'body.bin').read_bytes(), (ROOT / base / 'headers.txt').read_bytes(), read(base + '/receipt.json'), route_spec)
            assert route == read(spec['route'])
            assert spec['v50_ready_unchanged'] == next(r['ready_for_future_registration'] for r in intake['slot_results'] if r['slot_id'] == spec['id'])
        else: assert spec['route'] is spec['v50_ready_unchanged'] is None
        row = decision(raw, receipt, spec, cfg, body, scope, checks, route)
        assert row == read(f"data/v54/{spec['id']}_decision.json"); rows.append(row)
        assert read(spec['identity'])['identity_urls_agree'] == (spec['id'] == 'reference_v42')
    assert report['pages'] == rows and report['page_denominator'] == len(rows) == 5
    candidates = rows[1:]; eligible = [r['id'] for r in candidates if r['development_capture_eligible']]
    assert report['candidate_denominator'] == len(candidates) == report['candidate_capacity_required'] == 4
    assert report['eligible_candidate_ids'] == eligible and report['eligible_development_candidates'] == len(eligible)
    assert report['development_intake_capacity_met'] == (len(eligible) >= 4) and report['candidate_shortage'] == max(0, 4 - len(eligible))
    assert report['reference_eligible_separate'] == rows[0]['development_capture_eligible']
    assert report['v50_ready_captures_unchanged'] == intake['ready_captures'] == 1
    assert report['v50_intake_capacity_met_unchanged'] is intake['intake_capacity_met'] is False
    assert report['newly_eligible_vs_v50_ids'] == [r['id'] for r in candidates if r['development_capture_eligible'] and not r['v50_ready_unchanged']]
    assert report['previously_ready_now_ineligible_ids'] == [r['id'] for r in candidates if not r['development_capture_eligible'] and r['v50_ready_unchanged']]
    assert report['metadata_scope_audit_sequence_closed'] is True and report['natural_benchmark_capacity_met'] is False
    for k in ['natural_benchmark_qualifying_works_from_intake', 'network_requests', 'browser_renders', 'new_structural_scores',
              'new_lexical_or_semantic_scores', 'accepted_source_identities', 'independent_reviews_admitted', 'untouched_test_units_admitted']: assert report[k] == 0
    assert report['scientific_acceptance'] is report['semantic_evaluation_metrics'] is None
    prior = []
    for path in sorted((ROOT / 'runs').glob('000*/manifest.json')):
        if path.parent != run: check_hashes(path.parent); prior.append(path.parent.name)
    assert len(prior) == 53
    for seal in (ROOT / 'reports').glob('*_deliverable_seal.json'):
        for p, h in json.loads(seal.read_text()).get('deliverable_hashes', {}).items(): assert sha(p) == h, p
    result = {'state': 'verified', 'manifest_sha256': sha('runs/000054_offline_intake/manifest.json'),
        'pages_reconstructed': 5, 'candidate_denominator': 4, 'eligible_development_candidates': len(eligible),
        'candidate_shortage': max(0, 4 - len(eligible)), 'reference_counted_as_candidate': False,
        'original_scope_spans_and_current_route_evidence_reconstructed': True,
        'decisions_reconstructed_without_production_evaluator': True, 'old_decisions_preserved': True,
        'shared_html_parser': 'BeautifulSoup html.parser', 'network_requests': 0,
        'independent_scientific_review': False, 'semantics_or_source_identity_validated': False, 'prior_runs_preserved': prior}
    output = ROOT / 'reports/000054_verification.json'
    if output.exists(): assert {k: v for k, v in json.loads(output.read_text()).items() if k != 'verified_at_utc'} == result
    else:
        with output.open('x') as stream: json.dump(result | {'verified_at_utc': datetime.now(timezone.utc).isoformat()}, stream, indent=2); stream.write('\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'prior_runs_preserved'} | {'prior_runs_preserved': len(prior)}, indent=2))


if __name__ == '__main__': main()
