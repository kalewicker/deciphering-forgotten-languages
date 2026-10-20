"""Offline declarations only: no requests and no inferred WordPress endpoints."""
import json
from urllib.parse import urlencode, urljoin, urlsplit
from bs4 import BeautifulSoup

ROOT_URL = 'https://physicsworld.com/'
TEMPLATE = ROOT_URL + '?s={search_term_string}'
QUERY_INPUT = {'@type': 'PropertyValueSpecification', 'valueRequired': True, 'valueName': 'search_term_string'}


def root_url(value):
    try:
        u = urlsplit(value)
        if (u.scheme == 'https' and u.hostname == 'physicsworld.com' and u.port in (None, 443)
                and u.username is None and u.password is None and u.path in ('', '/')
                and '?' not in value and '#' not in value):
            return ROOT_URL
    except ValueError:
        pass
    return None


def request_url(query):
    if not isinstance(query, str) or not query.strip(): raise ValueError('nonempty literal query required')
    return ROOT_URL + '?' + urlencode({'s': query})


def walk(value, path='$'):
    if isinstance(value, dict):
        yield path, value
        for k, v in value.items(): yield from walk(v, path + '.' + k)
    elif isinstance(value, list):
        for i, v in enumerate(value): yield from walk(v, f'{path}[{i}]')


def typed(obj, name):
    return name in (obj.get('@type') if isinstance(obj.get('@type'), list) else [obj.get('@type')])


def audit(raw, page_url, query):
    soup = BeautifulSoup(raw, 'html.parser')
    forms = []
    for index, form in enumerate(soup.find_all('form')):
        controls = form.find_all(['input', 'button', 'select', 'textarea'])
        if not any(c.get('name') == 's' for c in controls): continue
        info = {'form_index': index, 'action': form.get('action', ''), 'method': form.get('method', 'get').lower(),
                'controls': [{'tag': c.name, 'name': c.get('name'), 'type': c.get('type', 'text' if c.name == 'input' else 'submit' if c.name == 'button' else ''),
                              'disabled': c.has_attr('disabled') or c.find_parent('fieldset', disabled=True) is not None,
                              'form_attribute': c.get('form'), 'overrides': any(c.has_attr(k) for k in ['formaction', 'formmethod'])} for c in controls]}
        named = [c for c in info['controls'] if c['name']]
        search = [c for c in named if c['name'] == 's']
        checks = {
            'safe_explicit_root_action': bool(info['action']) and root_url(urljoin(page_url, info['action'])) is not None,
            'method_get': info['method'] == 'get',
            'only_one_named_search_control': len(named) == len(search) == 1,
            'search_control_supported': len(search) == 1 and search[0]['tag'] == 'input' and search[0]['type'].lower() in ('text', 'search') and not search[0]['disabled'],
            'no_control_overrides': not any(c['overrides'] or c['form_attribute'] is not None for c in info['controls']),
            'no_external_associated_controls': not (form.get('id') and soup.find(attrs={'form': form['id']})),
            'no_base_href': soup.find('base', href=True) is None,
        }
        info.update(checks=checks, supported=all(checks.values()))
        info['proposed_request_url'] = request_url(query) if info['supported'] else None
        forms.append(info)
    actions = []; errors = []
    for index, script in enumerate(soup.find_all('script', type='application/ld+json')):
        try: obj = json.loads(script.get_text())
        except (ValueError, TypeError): errors.append({'script_index': index, 'error': 'invalid_json'}); continue
        for path, node in walk(obj):
            if not typed(node, 'SearchAction'): continue
            target = node.get('target'); template = target.get('urlTemplate') if isinstance(target, dict) else target
            supported = isinstance(target, dict) and typed(target, 'EntryPoint') and template == TEMPLATE and node.get('query-input') == QUERY_INPUT
            actions.append({'script_index': index, 'json_path': path, 'url_template': template,
                            'query_input': node.get('query-input'), 'supported': supported,
                            'proposed_request_url': request_url(query) if supported else None})
    links = []
    for index, link in enumerate(soup.find_all('link')):
        rel = link.get('rel', []); href = link.get('href', ''); mime = link.get('type')
        if 'https://api.w.org/' in rel: category = 'api_root_not_search_endpoint'
        elif 'oembed' in (mime or ''): category = 'oembed_article_endpoint_not_discovery'
        elif 'alternate' in rel and mime == 'application/json': category = 'article_json_not_search_endpoint'
        else: continue
        links.append({'link_index': index, 'rel': rel, 'href': href, 'type': mime, 'category': category})
    supported = bool(forms) and bool(actions) and not errors and all(f['supported'] for f in forms) and all(a['supported'] for a in actions)
    return {'search_forms': forms, 'search_actions': actions, 'json_ld_errors': errors, 'api_links_not_selected': links,
            'route_declarations_agree': supported, 'proposed_request_url': request_url(query) if supported else None,
            'live_transport_tested': False, 'search_response_parser_tested': False}


def summary(rows, query):
    passed = sum(r['route_declarations_agree'] for r in rows)
    all_pass = bool(rows) and passed == len(rows)
    return {'experiment_id': 'native_discovery_v59', 'capture_denominator': len(rows), 'supported_captures': passed,
            'search_form_count': sum(len(r['search_forms']) for r in rows), 'search_action_count': sum(len(r['search_actions']) for r in rows),
            'api_links_not_selected': sum(len(r['api_links_not_selected']) for r in rows),
            'uniform_saved_declaration_gate': all_pass, 'proposed_request_url': request_url(query) if all_pass else None,
            'research_network_requests': 0, 'live_transport_tested': False, 'search_response_parser_tested': False,
            'new_candidates_admitted': 0, 'alignment_or_semantic_scores': 0, 'independent_reviews_admitted': 0,
            'untouched_test_units_admitted': 0, 'opaque_meanings_or_source_identities_admitted': 0,
            'previous_results_preserved': True}
