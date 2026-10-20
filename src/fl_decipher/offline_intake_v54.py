"""Prospective development-capture eligibility, separate from historical intake."""
from fl_decipher.cohort_scope_v52 import accounting, extract_scope
from fl_decipher.publisher_intake_v50 import publication_dates, topical
from fl_decipher.routing_v53 import metadata, publisher_key, title_key


def alias_matches(url, canonical, evidence):
    """Only exact frozen route bindings can support a non-canonical og:url."""
    required = {'complete_200', 'html_content_type', 'consistent_publisher_chain',
                'canonical_matches_frozen', 'three_title_channels_match_frozen'}
    if not evidence or not evidence.get('current_alias_supported'): return False
    if not all(evidence.get('checks', {}).get(k) is True for k in required): return False
    expected = publisher_key(canonical)
    return bool(expected and publisher_key(url) is not None
                and url == evidence.get('requested_url') and canonical == evidence.get('expected_canonical_url')
                and publisher_key(evidence.get('final_url')) == expected
                and evidence.get('category') == 'observed_redirect_to_canonical'
                and evidence.get('num_redirects', 0) > 0)


def evaluate(raw, receipt, spec, cfg, expected_body, route=None):
    meta = metadata(raw); canonical = publisher_key(spec['url'])
    canon_values = [r['value'] for r in meta['urls'] if r['channel'] == 'canonical']
    og_values = [r['value'] for r in meta['urls'] if r['channel'] == 'og_url']
    titles = meta['titles']; required = {'html_title', 'og_title', 'article_headline'}
    title_ok = (required <= {r['channel'] for r in titles} and not meta['json_ld_parse_errors']
                and all(title_key(r['value']) == title_key(spec['expected_title']) for r in titles))
    og_bindings = []
    for url in og_values:
        direct = canonical is not None and publisher_key(url) == canonical
        alias = not direct and alias_matches(url, spec['url'], route)
        og_bindings.append({'url': url, 'binding': 'direct_canonical' if direct else 'saved_v53_redirect' if alias else 'unresolved'})
    dates, agree = publication_dates(meta['publication_values'])
    scope = None; scope_error = None; scope_checks = {}
    try:
        scope = extract_scope(raw, expected_body, cfg['source_selector']); scope_checks = accounting(scope)
    except (ValueError, AssertionError) as error: scope_error = str(error)
    runs = scope['paragraph_runs'] if scope else []
    body = scope['body_text'] if scope else ''
    # Joining only for whole-word topic screening; no anchors are extracted from this string.
    topic_text = ' '.join(r['value'] for r in titles) + ' ' + ' '.join(r['text'] for r in runs)
    checks = {'complete_200': receipt.get('transport_complete') is True and receipt.get('http_status') == 200
              and receipt.get('curl_returncode') == 0,
        'html_markup': b'<html' in raw.lower(),
        'final_url_matches': canonical is not None and publisher_key(receipt.get('final_url')) == canonical,
        'all_canonical_fields_match': bool(canonical and canon_values and all(publisher_key(u) == canonical for u in canon_values)),
        'all_og_urls_bound': bool(og_bindings) and all(r['binding'] != 'unresolved' for r in og_bindings),
        'three_metadata_title_channels_agree': title_ok,
        'present_h1_values_match': all(title_key(h) == title_key(spec['expected_title']) for h in meta['h1_inventory']),
        'scope_and_accounting_valid': scope is not None and bool(scope_checks) and all(scope_checks.values()),
        'no_challenge_text': scope is not None and not any(s in body.casefold() for s in cfg['challenge_signatures']),
        'minimum_nonempty_paragraph_runs': len(runs) >= cfg['minimum_paragraph_runs'],
        'minimum_run_characters': sum(len(r['text']) for r in runs) >= cfg['minimum_run_characters'],
        'publication_date_agrees': agree,
        'publication_date_in_window': agree and cfg['date_min'] <= dates[0] <= cfg['date_max'],
        'native_topic_terms': topical(topic_text)}
    return {'id': spec['id'], 'development_capture_eligible': all(checks.values()), 'checks': checks,
        'unmet': [k for k, v in checks.items() if not v], 'metadata': meta, 'og_url_bindings': og_bindings,
        'parsed_publication_dates': dates, 'scope_error': scope_error, 'scope_accounting': scope_checks,
        'paragraph_run_count': len(runs), 'paragraph_run_characters': sum(len(r['text']) for r in runs),
        'paragraph_run_spans': [r['body_span'] for r in runs],
        'body_text_sha256': scope['body_text_sha256'] if scope else None,
        'v50_ready_unchanged': spec['v50_ready_unchanged'], 'previously_inspected_development_data': True,
        'historical_bytes_authenticated': False, 'independent_source_group_admitted': False,
        'false_parent_certified': False, 'untouched_test_unit_admitted': False}
