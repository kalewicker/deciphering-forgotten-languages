"""Two new slots under the E54 checks; new route evidence has explicit provenance."""
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from fl_decipher.publisher_intake_v50 import response_text, result_headers, topical
from fl_decipher.routing_v53 import metadata, publisher_key, title_key
from fl_decipher.offline_intake_v54 import evaluate


def article_key(url):
    key = publisher_key(url)
    return 'https://physicsworld.com' + key + '/' if key and key.startswith('/a/') else None


def prior_inventory(previous, selection, pages):
    exposures = {k: set(v) for k, v in previous['article_exposures'].items()}
    def add(url, tag):
        key = article_key(url)
        if key: exposures.setdefault(key, set()).add(tag)
    for query in selection['queries']:
        for hit in query['hits']: add(hit['url'], 'v50_search_result')
    for page in pages:
        add(page['url'], page['path'] + ':captured_page')
        soup = BeautifulSoup(page['raw'], 'html.parser')
        for node in soup.find_all('a', href=True): add(urljoin(page['url'], node['href']), page['path'] + ':link')
        for item in metadata(page['raw'])['urls']: add(item['value'], page['path'] + ':identity')
    return {'scope': 'Exact article URLs in the listed prior registry, v50 results and nine saved HTML captures; not complete analyst exposure or source grouping',
            'article_exposures': {k: sorted(v) for k, v in sorted(exposures.items())},
            'excluded_article_keys': sorted(exposures)}


def nominate(responses, prior):
    seen = set(); queries = []; slots = []
    for i, saved in enumerate(responses):
        text = response_text(saved['response']) if saved['error'] is None else None
        hits = result_headers(text) if text is not None else []; chosen = None
        for row in hits:
            key = article_key(row['url']); duplicate = key is not None and key in seen
            if key: seen.add(key)
            tags = prior['article_exposures'].get(key, [])
            topic = topical(row['title'] + '\n' + row['response_text'])
            reason = ('invalid_article_url' if key is None else 'duplicate_returned_url' if duplicate else
                      'prior_recorded_url_exposure' if key in prior['excluded_article_keys'] else
                      'topic_terms_missing' if not topic else 'query_slot_cap' if chosen is not None else 'selected_first_eligible')
            row.update(article_key=key, prior_exposure_tags=tags, topical=topic, decision_reason=reason,
                       nominated=reason == 'selected_first_eligible')
            if row['nominated']: chosen = row
        queries.append({'query_index': i, 'response_format_supported': text is not None, 'attributable_hits': len(hits), 'hits': hits})
        slots.append({'slot_id': f'q{i:02d}s00', 'query_index': i, 'nominee':
            {k: chosen[k] for k in ['rank', 'title', 'url', 'article_key', 'prior_exposure_tags']} if chosen else None})
    return {'queries': queries, 'slots': slots, 'occupied_slots': sum(s['nominee'] is not None for s in slots)}


def body_text(raw):
    soup = BeautifulSoup(raw, 'html.parser')
    for tag in soup.select('script,style,noscript,template,svg,canvas'): tag.decompose()
    bodies = soup.select('body')
    return bodies[0].get_text(' ', strip=True) if len(bodies) == 1 else ''


def alias_plan(raw, receipt, spec):
    meta = metadata(raw); expected = publisher_key(spec['url'])
    canon = [r['value'] for r in meta['urls'] if r['channel'] == 'canonical']
    og = [r['value'] for r in meta['urls'] if r['channel'] == 'og_url']
    different = list(dict.fromkeys(u for u in og if publisher_key(u) != expected))
    title_ok = ({'html_title', 'og_title', 'article_headline'} <= {r['channel'] for r in meta['titles']}
                and not meta['json_ld_parse_errors']
                and all(title_key(r['value']) == title_key(spec['expected_title']) for r in meta['titles']))
    identity_ok = bool(receipt['transport_complete'] and expected and publisher_key(receipt['final_url']) == expected
                       and canon and all(publisher_key(u) == expected for u in canon) and title_ok)
    permitted = bool(identity_ok and len(different) == 1 and publisher_key(different[0]) is not None)
    return {'request_url': different[0] if permitted else None,
            'reason': 'one_safe_observed_alternate' if permitted else 'all_og_urls_direct' if og and not different else 'native_identity_or_alternate_unavailable',
            'observed_og_urls': og, 'distinct_noncanonical_values': different, 'native_identity_and_titles_pass': identity_ok}


def prospective_decision(raw, receipt, spec, cfg, route=None):
    result = evaluate(raw, receipt, spec, cfg, body_text(raw), route)
    for binding in result['og_url_bindings']:
        if binding['binding'] == 'saved_v53_redirect': binding['binding'] = 'saved_v55_redirect'
    result['route_evidence_origin'] = 'v55' if route is not None else None
    result['exposure_status'] = 'development_data_after_this_intake; no complete prior-familiarity guarantee'
    return result


def capacity(old_eligible, rows):
    new = ['v55:' + r['slot_id'] for r in rows if r['development_capture_eligible']]
    ids = ['v50:' + x for x in old_eligible] + new
    return {'new_cohort_slot_denominator': 2, 'new_eligible_candidates': len(new),
            'cumulative_slot_denominator': 6, 'cumulative_eligible_ids': ids,
            'cumulative_eligible_candidates': len(ids), 'capacity_required': 4,
            'cumulative_capture_capacity_met': len(ids) >= 4, 'candidate_shortage': max(0, 4 - len(ids)),
            'reference_counted_as_candidate': False}
