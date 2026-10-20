"""Purpose-limited archive material admission; E63's result remains unchanged."""
import hashlib
import re
from urllib.parse import urlsplit
from bs4 import BeautifulSoup, NavigableString
from fl_decipher.new_material_v63 import recover
from fl_decipher.source_intake_v37 import citation


def norm(value): return ' '.join(value.casefold().split())


def adjudicate(raw, headers, receipt, selection, original_cfg):
    legacy = recover(raw, headers, receipt, selection, original_cfg)
    soup = BeautifulSoup(raw, 'html.parser'); tags = list(soup.find_all(True)); indices = {id(t):i for i,t in enumerate(tags)}
    def links(selector):
        return [{'dom_tag_index':indices[id(t)], 'href':t['href'], 'text':t.get_text(' ',strip=True)} for t in soup.select(selector)]
    identities = {'html_titles':[t.get_text(' ',strip=True) for t in soup.select('title')],
        'post_titles':[t.get_text(' ',strip=True) for t in soup.select('.post-title')],
        'title_links':links('.post-title a[href]'), 'bookmarks':links('a[rel~=bookmark][href]'),
        'canonical_urls':[t.get('href','') for t in soup.select('link[rel~=canonical]')],
        'og_urls':[t.get('content','') for t in soup.select('meta[property="og:url"]')]}
    expected_url = original_cfg['fl_url']; expected_title = original_cfg['nominee']['title']
    fields = identities['canonical_urls'] + identities['og_urls']
    allowed = {expected_url, expected_url.removesuffix('?m=0')}
    checks = {k:v for k,v in legacy['checks'].items() if k != 'all_native_identity_fields_bound'}
    checks.update({'one_exact_post_title': [norm(t) for t in identities['post_titles']] == [norm(expected_title)],
        'one_exact_html_title': [norm(t) for t in identities['html_titles']] == [norm('Forgotten Languages Full: '+expected_title)],
        'one_exact_title_permalink':len(identities['title_links']) == 1 and identities['title_links'][0]['href'] == expected_url and norm(identities['title_links'][0]['text']) == norm(expected_title),
        'one_exact_bookmark_permalink':len(identities['bookmarks']) == 1 and identities['bookmarks'][0]['href'] == expected_url,
        'no_conflicting_identity_metadata':all(value in allowed for value in fields)})
    allowed_use = all(checks.values())
    return {'policy_id':'archive_admission_v64', 'policy_developed_after_e63_failure':True,
        'e63_gate_recomputed':legacy['passed'], 'e63_unmet_recomputed':legacy['unmet'], 'e63_identity_check_recomputed':legacy['checks']['all_native_identity_fields_bound'],
        'legacy_checks':legacy['checks'], 'identity_inventory':identities,
        'identity_metadata_status':'absent' if not fields else 'consistent' if checks['no_conflicting_identity_metadata'] else 'conflicting',
        'purpose_checks':checks, 'limited_admission':allowed_use,
        'allowed_use':'offline_citation_metadata_inspection' if allowed_use else None,
        'decision':'admitted_for_offline_metadata_only' if allowed_use else 'not_admitted',
        'unmet':[k for k,v in checks.items() if not v],
        'independent_review':False, 'publication_year_wording_authenticated':False,
        'current_wording_authenticated':False, 'source_identity_or_meaning_admitted':False,
        'untouched_test_eligible':False, 'source_acquisition_authorized':False}


def export_body(raw, decision, selection, original_url):
    if not decision['limited_admission']: return None
    soup = BeautifulSoup(raw, 'html.parser'); bodies = soup.select('div.post-body')
    if len(bodies) != 1: raise ValueError('unique body required')
    for node in bodies[0].select('script,style,noscript'): node.decompose()
    text = bodies[0].get_text(' ',strip=True)
    return {'representation':'archive_bound_development_post_body', 'original_url':original_url,
        'capture_timestamp':selection['record']['timestamp'], 'parent_sha256':hashlib.sha256(raw).hexdigest(),
        'scope':'exactly one div.post-body', 'transformations':['remove script/style/noscript descendants only','BeautifulSoup get_text separator space and strip=True'],
        'text':text, 'text_sha256':hashlib.sha256(text.encode()).hexdigest(), 'unicode_characters':len(text),
        'permitted_use':'offline_citation_metadata_inspection', 'exposure_status':'exposed_development_material',
        'publication_year_wording_authenticated':False, 'semantic_training_eligible':False, 'untouched_test_eligible':False}


def recognized_url(url, label=''):
    try:
        parsed = urlsplit(url)
        if parsed.scheme not in ('http','https') or not parsed.hostname or parsed.username is not None or parsed.password is not None or parsed.port not in (None,80 if parsed.scheme=='http' else 443): return None
        return citation(url,label)
    except (ValueError,TypeError): return None


def inspect_citations(raw, decision, known_urls):
    if not decision['limited_admission']: return None
    soup = BeautifulSoup(raw, 'html.parser'); body = soup.select('div.post-body')
    if len(body) != 1: raise ValueError('unique body required')
    indices = {id(t):i for i,t in enumerate(soup.find_all(True))}
    text_indices = {id(t):i for i,t in enumerate(n for n in body[0].descendants if isinstance(n,NavigableString))}
    known = {c['identifier'] for u in known_urls if (c:=recognized_url(u))}; rows=[]; first={}
    def add(url,label,origin):
        c = recognized_url(url,label); identifier = c['identifier'] if c else None; duplicate = first.get(identifier) if identifier else None
        i = len(rows)
        if identifier and identifier not in first: first[identifier]=i
        rows.append({'occurrence_id':i,'url':url,'label':label,'origin':origin,'recognized_metadata':c,
            'reason':'recognized_scholarly_url' if c else 'not_supported_scholarly_url',
            'duplicate_identifier_of_occurrence':duplicate,
            'prior_registry_status':'identifier_recorded' if identifier in known else 'identifier_not_recorded_in_frozen_inventory' if identifier else 'not_applicable',
            'selected_for_acquisition':False,'source_identity_admitted':False})
    for node in body[0].descendants:
        if any(getattr(p,'name',None) in ('script','style','noscript') for p in node.parents): continue
        if getattr(node,'name',None)=='a' and node.get('href'):
            add(node['href'],node.get_text(' ',strip=True),{'channel':'href_attribute','dom_tag_index':indices[id(node)]})
        elif isinstance(node,NavigableString) and not any(getattr(p,'name',None)=='a' for p in node.parents):
            for match in re.finditer(r'https?://[^\s<>"\)\]]+',str(node)):
                add(match.group(),'',{'channel':'literal_text_url','body_text_node_index':text_indices[id(node)],'node_unicode_span':list(match.span())})
    return {'raw_parent_sha256':hashlib.sha256(raw).hexdigest(), 'scope':'unique post-body; exclude script/style/noscript; hrefs and literal text URLs only',
        'url_occurrence_denominator':len(rows),'occurrences':rows,
        'recognized_identifier_count':len(first),'recognized_identifiers':list(first),
        'known_identifier_matches':sorted(set(first)&known),
        'source_candidates_selected':0,'new_connected_works_confirmed':0,'independent_reviews_admitted':0,
        'identifier_absence_is_not_independence':True,'network_requests':0}
