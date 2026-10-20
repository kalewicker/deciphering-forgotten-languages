"""Offline structural attribution of saved search cards; no candidate selection."""
from collections import Counter
from urllib.parse import urljoin, urlsplit
from bs4 import BeautifulSoup
from fl_decipher.additional_intake_v55 import article_key


def clean(value): return ' '.join(value.split())
def safe_listing_url(value):
    try:
        u = urlsplit(value)
        return (u.scheme == 'https' and u.hostname == 'physicsworld.com' and u.port in (None, 443)
                and u.username is None and u.password is None and u.path.startswith('/a/')
                and '?' not in value and '#' not in value)
    except (ValueError, TypeError): return False


def attribute(raw, url, cfg, prior):
    soup = BeautifulSoup(raw, 'html.parser'); tags = list(soup.find_all(True)); positions = {id(t): i for i, t in enumerate(tags)}
    anchors = list(soup.find_all('a', href=True)); anchor_ids = {id(t): i for i, t in enumerate(anchors)}
    mains = soup.select(cfg['main_selector']); containers = soup.select(cfg['container_selector'])
    cards = soup.select(cfg['card_selector']); card_ids = {id(t): i for i, t in enumerate(cards)}
    body = soup.find_all('body'); titles = [clean(t.get_text(' ', strip=True)) for t in soup.find_all('title')]
    headings = [clean(t.get_text(' ', strip=True)) for t in soup.select(cfg['heading_selector'])]
    checks = {'one_search_body': len(body) == 1 and {'search', 'search-results'} <= set(body[0].get('class', [])),
        'one_registered_main': len(mains) == 1, 'one_registered_container': len(containers) == 1,
        'exact_title': titles == [cfg['expected_title']], 'exact_query_heading': headings == [cfg['expected_heading']],
        'no_base_href': not soup.select('base[href]')}
    page_ok = all(checks.values()); rows = []; first_urls = {}
    def node(t): return {'dom_tag_index': positions[id(t)], 'text': t.get_text(' ', strip=True)}
    for index, card in enumerate(cards):
        infos = card.select(':scope > div.listing-block__info')
        title_nodes = card.select(':scope > div.listing-block__info > h3.listing-block__title > a[href]')
        images = card.select(':scope > a.listing-block__image[href]')
        snippets = card.select(':scope > div.listing-block__info > p')
        times = card.select('time,[datetime],.date,.listing-block__date')
        resolved = []
        for link in title_nodes + images:
            try: resolved.append(urljoin(url, link['href']) if checks['no_base_href'] else None)
            except (ValueError, TypeError): resolved.append(None)
        title = clean(title_nodes[0].get_text(' ', strip=True)) if len(title_nodes) == 1 else None
        card_checks = {'page_checks_pass': page_ok, 'direct_child_of_registered_container': len(containers) == 1 and card.parent is containers[0],
            'no_nested_listing_cards': not any(id(p) in card_ids for p in card.parents) and not card.select(cfg['card_selector']),
            'one_info_block': len(infos) == 1, 'one_title_link': len(title_nodes) == 1,
            'one_image_link': len(images) == 1, 'one_nonempty_snippet': len(snippets) == 1 and bool(snippets[0].get_text(' ', strip=True)),
            'nonempty_title': bool(title), 'title_attribute_consistent': len(title_nodes) == 1 and (not title_nodes[0].has_attr('title') or clean(title_nodes[0]['title']) == title),
            'title_image_same_safe_url': len(resolved) == 2 and resolved[0] == resolved[1] and safe_listing_url(resolved[0])}
        attributed = all(card_checks.values()); chosen_url = resolved[0] if len(title_nodes) == 1 and resolved else None
        key = article_key(chosen_url) if chosen_url else None
        duplicate = first_urls.get(chosen_url) if chosen_url else None
        if chosen_url and chosen_url not in first_urls: first_urls[chosen_url] = index
        rows.append({'card_index': index, 'dom_tag_index': positions[id(card)], 'checks': card_checks,
            'structurally_attributed': attributed, 'failed_checks': [k for k,v in card_checks.items() if not v],
            'title': title, 'title_links': [{**node(t), 'anchor_index': anchor_ids[id(t)], 'href': t['href']} for t in title_nodes],
            'image_links': [{**node(t), 'anchor_index': anchor_ids[id(t)], 'href': t['href']} for t in images],
            'snippets': [node(t) for t in snippets], 'date_markers': [{**node(t), 'tag': t.name, 'datetime': t.get('datetime')} for t in times],
            'date_status': 'markers_require_later_validation' if times else 'not_supplied_in_registered_card_channels',
            'resolved_url': chosen_url, 'strict_article_key': key, 'strict_url_usable': bool(attributed and key),
            'strict_url_reason': 'usable_for_future_registration' if attributed and key else 'strict_article_url_rejected' if attributed else 'card_schema_rejected',
            'duplicate_of_card_index': duplicate, 'prior_registry_tags': prior['article_exposures'].get(key, []),
            'previously_captured_in_registry': key in prior['captured_article_keys'] if key else False,
            'exposure_status': 'exposed_development_data', 'article_eligibility_assessed': False, 'nominated': False})
    ledger = []
    for i, a in enumerate(anchors):
        owners = [card_ids[id(p)] for p in a.parents if id(p) in card_ids]
        role = 'outside_listing_cards'; owner = owners[0] if len(owners) == 1 else None
        if len(owners) > 1: role = 'ambiguous_nested_card_ownership'
        elif owner is not None:
            row = rows[owner]
            role = ('rejected_card_link' if not row['structurally_attributed'] else
                    'attributed_title_link' if i in [t['anchor_index'] for t in row['title_links']] else
                    'attributed_image_duplicate' if i in [t['anchor_index'] for t in row['image_links']] else 'supporting_card_link')
        resolved = None
        try: resolved = urljoin(url, a['href']) if checks['no_base_href'] else None
        except (ValueError, TypeError): pass
        key = article_key(resolved) if resolved else None
        ledger.append({'anchor_index': i, 'dom_tag_index': positions[id(a)], 'href': a['href'], 'text': a.get_text(' ', strip=True),
            'resolved_url': resolved, 'strict_article_key': key, 'owner_card_indices': owners, 'role': role,
            'prior_registry_tags': prior['article_exposures'].get(key, []), 'exposure_status': 'exposed_development_data'})
    exposures = {k: list(v) for k,v in prior['article_exposures'].items()}
    for row in ledger:
        if row['strict_article_key']:
            exposures.setdefault(row['strict_article_key'], []).append(f"v60_saved_search:anchor{row['anchor_index']:03d}")
    return {'page_checks': checks, 'page_attribution_supported': page_ok, 'cards': rows, 'anchor_ledger': ledger,
        'exposure_registry': {'scope': 'Frozen v58 registry plus every strict article URL in saved v60 anchors; incomplete lifetime exposure and source grouping',
            'article_exposures': {k: sorted(set(v)) for k,v in sorted(exposures.items())},
            'captured_article_keys': prior['captured_article_keys'], 'all_listing_urls_exposed': sorted({r['resolved_url'] for r in rows if r['resolved_url']})}}


def summarize(result):
    rows = result['cards']; ledger = result['anchor_ledger']; usable = [r for r in rows if r['strict_url_usable']]
    return {'experiment_id': 'result_attribution_v61', 'research_network_requests': 0,
        'page_attribution_supported': result['page_attribution_supported'], 'listing_card_denominator': len(rows),
        'structurally_attributed_cards': sum(r['structurally_attributed'] for r in rows),
        'rejected_card_schemas': sum(not r['structurally_attributed'] for r in rows),
        'strict_url_usable_cards': len(usable), 'unique_strict_article_urls': len({r['strict_article_key'] for r in usable}),
        'strict_url_rejected_attributed_cards': sum(r['structurally_attributed'] and not r['strict_url_usable'] for r in rows),
        'cards_without_date_markers': sum(not r['date_markers'] for r in rows),
        'previously_captured_usable_cards': sum(r['previously_captured_in_registry'] for r in usable),
        'anchor_occurrences_accounted': len(ledger), 'anchor_role_counts': dict(sorted(Counter(r['role'] for r in ledger).items())),
        'nominations': 0, 'article_eligibility_assessments': 0, 'new_article_captures': 0,
        'numeric_or_alignment_scores': 0, 'opaque_meanings_or_source_identities_admitted': 0,
        'independent_reviews_admitted': 0, 'untouched_test_units_admitted': 0,
        'future_challenge': {'candidate_slots': 2, 'minimum_window_bag_capacity': 6, 'numeric_window_cap': 11,
            'status': 'requires_new_registration_before_intake', 'stop_after_fixed_batch': True,
            'if_no_capable_comparator': 'close_this_discovery_route_as_feasibility_limited'},
        'previous_results_preserved': True}
