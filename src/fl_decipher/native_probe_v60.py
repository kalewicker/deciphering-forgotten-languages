"""One direct response and a static inventory; never nominate or follow links."""
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from fl_decipher.additional_intake_v55 import article_key
from fl_decipher.native_discovery_v59 import audit
from fl_decipher.routing_v53 import header_blocks


def command(dest, contract):
    return ['curl', '--disable', '--silent', '--show-error', '--compressed', '--request', 'GET',
            '--proto', '=https', '--retry', '0', '--max-redirs', '0',
            '--connect-timeout', str(contract['connect_timeout_seconds']), '--max-time', str(contract['total_timeout_seconds']),
            '--max-filesize', str(contract['max_body_bytes']), '--user-agent', contract['user_agent'],
            '--output', str(dest / 'body.bin'), '--dump-header', str(dest / 'headers.txt'), '--write-out', '%{json}', contract['url']]


def inventory(raw, request_url, query):
    soup = BeautifulSoup(raw, 'html.parser')
    tags = list(soup.find_all(True)); positions = {id(tag): i for i, tag in enumerate(tags)}
    def context(tag):
        return [{'tag': p.name, 'id': p.get('id'), 'classes': p.get('class', [])}
                for p in reversed(list(tag.parents)) if p.name != '[document]']
    def item(tag):
        return {'dom_tag_index': positions[id(tag)], 'tag': tag.name, 'text': tag.get_text(' ', strip=True), 'ancestors': context(tag)}
    bases = [{'dom_tag_index': positions[id(tag)], 'href': tag['href']} for tag in soup.find_all('base', href=True)]
    anchors = []
    for i, tag in enumerate(soup.find_all('a', href=True)):
        resolved = None; key = None; reason = 'base_href_present'
        if not bases:
            try: resolved = urljoin(request_url, tag['href']); key = article_key(resolved); reason = 'strict_article_url_only_not_search_hit' if key else 'not_strict_article_url'
            except (ValueError, TypeError): reason = 'malformed_href'
        anchors.append({'anchor_index': i, **item(tag), 'href': tag['href'], 'resolved_url': resolved,
                        'article_key_diagnostic': key, 'diagnostic_reason': reason, 'search_hit_attributed': False})
    values = []
    for fi, form in enumerate(soup.find_all('form')):
        for ci, control in enumerate(form.find_all(['input', 'button', 'select', 'textarea'])):
            if control.name == 'input' and control.get('name') == 's' and control.get('type', 'text').lower() in ['text', 'search']:
                values.append({'form_index': fi, 'control_index': ci, 'value': control.get('value', '')})
    declarations = audit(raw, request_url, query)
    return {'html_titles': [item(t) for t in soup.find_all('title')], 'headings_h1_h2': [item(t) for t in soup.find_all(['h1', 'h2'])],
            'base_hrefs': bases, 'search_forms': declarations['search_forms'], 'search_actions': declarations['search_actions'],
            'json_ld_errors': declarations['json_ld_errors'], 'search_input_values': values, 'anchors': anchors,
            'all_anchor_occurrences_retained': True, 'link_resolution_supported': not bases,
            'search_result_container_selector': None, 'search_result_attribution_validated': False}


def observation(raw, headers, receipt, contract, signatures):
    parsed = header_blocks(headers); responses = parsed['responses']
    text = BeautifulSoup(raw, 'html.parser').get_text(' ', strip=True).casefold()
    challenges = [s for s in signatures if s in text]
    checks = {'transport_complete': receipt['transport_complete'] is True,
              'http_200': receipt['http_status'] == 200,
              'exact_request_url_retained': receipt['final_url'] == contract['url'],
              'no_redirects': receipt['num_redirects'] == 0,
              'one_consistent_application_response': len(responses) == 1 and responses[0]['status'] == receipt['http_status'] and not responses[0]['locations'],
              'html_content_type': (receipt['content_type'] or '').split(';')[0].strip().lower() == 'text/html' and bool(responses)
                  and bool(responses[-1]['content_types']) and all(v.split(';')[0].strip().lower() == 'text/html' for v in responses[-1]['content_types']),
              'body_within_limit': 0 < len(raw) <= contract['max_body_bytes'], 'no_registered_challenge_text': not challenges}
    return {'header_inventory': parsed, 'checks': checks, 'challenge_signatures_found': challenges,
            'complete_direct_html_observation': all(checks.values()), 'native_search_function_validated': False}


def summarize(layout, observed, receipt):
    anchors = layout['anchors']; keys = [r['article_key_diagnostic'] for r in anchors if r['article_key_diagnostic']]
    return {'experiment_id': 'native_probe_v60', 'probe_slot_denominator': 1, 'probe_attempts': 1,
        'recorded_application_responses': len(observed['header_inventory']['responses']),
        'http_status': receipt['http_status'], 'curl_returncode': receipt['curl_returncode'],
        'complete_direct_html_observation': observed['complete_direct_html_observation'],
        'failed_checks': [k for k, v in observed['checks'].items() if not v],
        'html_title_count': len(layout['html_titles']), 'h1_h2_count': len(layout['headings_h1_h2']),
        'search_form_count': len(layout['search_forms']), 'search_action_count': len(layout['search_actions']),
        'base_href_count': len(layout['base_hrefs']), 'anchor_occurrences': len(anchors),
        'strict_article_url_occurrences_diagnostic_only': len(keys), 'unique_strict_article_urls_diagnostic_only': len(set(keys)),
        'duplicate_strict_article_url_occurrences': len(keys) - len(set(keys)),
        'query_echo_in_search_input': any(r['value'] == 'ANITA' for r in layout['search_input_values']),
        'search_result_container_selector': None, 'search_hits_attributed': 0, 'native_search_function_validated': False,
        'candidate_nominations': 0, 'article_captures': 0, 'pagination_requests': 0, 'query_replacements': 0,
        'alignment_or_semantic_scores': 0, 'opaque_meanings_or_source_identities_admitted': 0,
        'independent_reviews_admitted': 0, 'untouched_test_units_admitted': 0, 'natural_benchmark_qualifying_works': 0,
        'previous_results_preserved': True}
