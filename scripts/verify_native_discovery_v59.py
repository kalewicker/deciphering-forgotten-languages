"""Replay saved declaration evidence without importing the production audit."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
from urllib.parse import urljoin, urlsplit, urlencode
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from verify_correspondence_v6 import check_hashes


def read(p): return json.loads((ROOT / p).read_text())
def sha(p): return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()


def replay(spec, query):
    raw = (ROOT / spec['raw']).read_bytes(); receipt = read(spec['receipt'])
    assert receipt['transport_complete'] is True and receipt['http_status'] == 200
    assert receipt['requested_url'] == spec['url'] and receipt['final_url'] == spec['article_url']
    assert receipt['artifacts']['body.bin']['sha256'] == sha(spec['raw'])
    assert receipt['artifacts']['body.bin']['bytes'] == len(raw)
    soup = BeautifulSoup(raw, 'html.parser'); url = 'https://physicsworld.com/?' + urlencode([('s', query)])
    forms = []
    for i, form in enumerate(soup.select('form')):
        controls = form.select('input,button,select,textarea')
        if not any(c.get('name') == 's' for c in controls): continue
        items = []
        for c in controls:
            items.append({'tag': c.name, 'name': c.get('name'), 'type': c.get('type', {'input': 'text', 'button': 'submit'}.get(c.name, '')),
                'disabled': 'disabled' in c.attrs or any(p.name == 'fieldset' and 'disabled' in p.attrs for p in c.parents),
                'form_attribute': c.get('form'), 'overrides': 'formaction' in c.attrs or 'formmethod' in c.attrs})
        action = form.get('action', ''); method = form.get('method', 'get').lower()
        dest = urljoin(spec['url'], action); parsed = urlsplit(dest)
        safe = bool(action) and parsed.scheme == 'https' and parsed.hostname == 'physicsworld.com' and parsed.port in (None, 443)
        safe = safe and parsed.username is None and parsed.password is None and parsed.path in ('', '/') and '?' not in dest and '#' not in dest
        named = [c for c in items if c['name']]; search = [c for c in named if c['name'] == 's']
        checks = {'safe_explicit_root_action': safe, 'method_get': method == 'get', 'only_one_named_search_control': len(named) == len(search) == 1,
            'search_control_supported': len(search) == 1 and search[0]['tag'] == 'input' and search[0]['type'].lower() in ['search', 'text'] and not search[0]['disabled'],
            'no_control_overrides': all(not c['overrides'] and c['form_attribute'] is None for c in items),
            'no_external_associated_controls': not any(c.get('form') == form.get('id') for c in soup.select('[form]')) if form.get('id') else True,
            'no_base_href': not soup.select('base[href]')}
        forms.append({'form_index': i, 'action': action, 'method': method, 'controls': items, 'checks': checks,
                      'supported': all(checks.values()), 'proposed_request_url': url if all(checks.values()) else None})
    actions = []; errors = []
    for i, script in enumerate(soup.select('script[type="application/ld+json"]')):
        try: obj = json.loads(script.get_text())
        except (ValueError, TypeError): errors.append({'script_index': i, 'error': 'invalid_json'}); continue
        pending = [('$', obj)]
        while pending:
            path, node = pending.pop()
            if isinstance(node, list): pending.extend(reversed([(f'{path}[{j}]', child) for j, child in enumerate(node)]))
            if not isinstance(node, dict): continue
            pending.extend(reversed([(path + '.' + k, child) for k, child in node.items()]))
            kind = node.get('@type'); kinds = kind if isinstance(kind, list) else [kind]
            if 'SearchAction' not in kinds: continue
            target = node.get('target'); template = target.get('urlTemplate') if isinstance(target, dict) else target
            tk = target.get('@type') if isinstance(target, dict) else None; tks = tk if isinstance(tk, list) else [tk]
            needed = {'@type': 'PropertyValueSpecification', 'valueRequired': True, 'valueName': 'search_term_string'}
            ok = isinstance(target, dict) and 'EntryPoint' in tks and template == 'https://physicsworld.com/?s={search_term_string}' and node.get('query-input') == needed
            actions.append({'script_index': i, 'json_path': path, 'url_template': template, 'query_input': node.get('query-input'),
                            'supported': ok, 'proposed_request_url': url if ok else None})
    links = []
    for i, link in enumerate(soup.select('link')):
        rel = link.get('rel', []); mime = link.get('type'); category = None
        if 'https://api.w.org/' in rel: category = 'api_root_not_search_endpoint'
        elif mime and 'oembed' in mime: category = 'oembed_article_endpoint_not_discovery'
        elif mime == 'application/json' and 'alternate' in rel: category = 'article_json_not_search_endpoint'
        if category: links.append({'link_index': i, 'rel': rel, 'href': link.get('href', ''), 'type': mime, 'category': category})
    ok = bool(forms) and bool(actions) and not errors and all(f['supported'] for f in forms) and all(a['supported'] for a in actions)
    return {'capture_id': spec['id'], 'raw_sha256': sha(spec['raw']), 'search_forms': forms, 'search_actions': actions,
        'json_ld_errors': errors, 'api_links_not_selected': links, 'route_declarations_agree': ok, 'proposed_request_url': url if ok else None,
        'live_transport_tested': False, 'search_response_parser_tested': False}


def main():
    run = ROOT / 'runs/000059_native_discovery'; check_hashes(run)
    old = read('experiments/native_discovery_v59.json'); cfg = read('experiments/native_discovery_v59a.json')
    pre0 = read('data/v59/preflight.json'); failure = read('data/v59/failure.json'); pre = read('data/v59a/preflight.json')
    manifest = read('runs/000059_native_discovery/manifest.json'); report = read('runs/000059_native_discovery/report.json')
    for frozen in [pre0, pre]:
        for p, h in frozen['hashes'].items(): assert sha(p) == h, p
    for p, h in cfg['input_hashes'].items(): assert pre['hashes'][p] == h
    assert pre['hashes']['experiments/native_discovery_v59a.json'] == sha('experiments/native_discovery_v59a.json')
    assert old['registered_at_utc'] < pre0['sealed_at_utc'] < failure['recorded_at_utc'] < cfg['registered_at_utc'] < pre['sealed_at_utc'] < manifest['finished_at_utc']
    assert failure['original_preflight_sha256'] == sha('data/v59/preflight.json')
    assert failure['completed_page_audits'] == failure['research_network_requests'] == 0
    assert sorted(p.name for p in (ROOT / 'data/v59').iterdir()) == ['failure.json', 'preflight.json']
    for k in old.keys() - {'input_hashes', 'registered_at_utc'}: assert cfg[k] == old[k], k
    assert cfg['network_request_budget'] == 0 and cfg['query'] == 'ANITA'
    rows = [replay(spec, cfg['query']) for spec in cfg['pages']]
    assert len(rows) == cfg['capture_denominator'] == 11 and len({s['id'] for s in cfg['pages']}) == 11
    for row in rows: assert row == read(f"data/v59a/{row['capture_id']}_declarations.json"), row['capture_id']
    passed = sum(r['route_declarations_agree'] for r in rows)
    expected = {'experiment_id': 'native_discovery_v59', 'capture_denominator': len(rows), 'supported_captures': passed,
        'search_form_count': sum(len(r['search_forms']) for r in rows), 'search_action_count': sum(len(r['search_actions']) for r in rows),
        'api_links_not_selected': sum(len(r['api_links_not_selected']) for r in rows), 'uniform_saved_declaration_gate': passed == len(rows),
        'proposed_request_url': 'https://physicsworld.com/?s=ANITA' if passed == len(rows) else None,
        'research_network_requests': 0, 'live_transport_tested': False, 'search_response_parser_tested': False,
        'new_candidates_admitted': 0, 'alignment_or_semantic_scores': 0, 'independent_reviews_admitted': 0,
        'untouched_test_units_admitted': 0, 'opaque_meanings_or_source_identities_admitted': 0, 'previous_results_preserved': True,
        'execution_version': 'v59a', 'original_attempt_failed_before_audit': True,
        'distinct_article_url_denominator': len({p['article_url'] for p in cfg['pages']}), 'future_probe_contract': cfg['future_probe_contract']}
    assert report == expected
    assert not (ROOT / 'data/v59a/acquisition').exists()
    prior = []
    for path in sorted((ROOT / 'runs').glob('0000*/manifest.json')):
        if path.parent == run: continue
        assert int(path.parent.name.split('_')[0]) <= 58
        check_hashes(path.parent); prior.append(path.parent.name)
    assert len(prior) == 58
    for path in (ROOT / 'reports').glob('*_deliverable_seal.json'):
        for p, h in json.loads(path.read_text()).get('deliverable_hashes', {}).items(): assert sha(p) == h, p
    result = {'state': 'verified', 'manifest_sha256': sha('runs/000059_native_discovery/manifest.json'),
        'capture_declarations_and_full_accounting_replayed': True, 'capture_denominator': len(rows), 'distinct_article_urls': expected['distinct_article_url_denominator'],
        'supported_captures': passed, 'production_audit_not_imported': True, 'shared_html_parser': 'BeautifulSoup html.parser',
        'original_failed_attempt_and_unchanged_inputs_preserved': True, 'research_network_requests': 0,
        'live_transport_tested': False, 'search_response_parser_tested': False,
        'independent_scientific_review': False, 'semantics_or_source_identity_validated': False, 'prior_runs_preserved': prior}
    out = ROOT / 'reports/000059_verification.json'
    if out.exists(): assert {k: v for k, v in json.loads(out.read_text()).items() if k != 'verified_at_utc'} == result
    else:
        with out.open('x') as f: json.dump(result | {'verified_at_utc': datetime.now(timezone.utc).isoformat()}, f, indent=2); f.write('\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'prior_runs_preserved'} | {'prior_runs_preserved': len(prior)}, indent=2))


if __name__ == '__main__': main()
