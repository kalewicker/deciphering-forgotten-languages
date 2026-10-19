"""Offline DOM-channel and leaf-partition replay; no eligibility changes."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys
import unicodedata
from bs4 import BeautifulSoup
from bs4.element import CData, NavigableString, Tag

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from verify_correspondence_v6 import check_hashes
from verify_publisher_intake_v50 import key


def read(p): return json.loads((ROOT / p).read_text())
def sha(p): return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()
def digest(s): return hashlib.sha256(s.encode()).hexdigest()
def norm(s): return ' '.join(unicodedata.normalize('NFC', s).casefold().split())
def strip_suffix(s): return re.sub(r'\s+[–—|\-]\s+Physics World\s*$', '', s)


def main():
    run = ROOT / 'runs/000051_heading_scope'; check_hashes(run)
    cfg = read('experiments/heading_scope_v51.json'); pre = read('data/v51/preflight.json')
    manifest = read('runs/000051_heading_scope/manifest.json')
    for p, h in pre['hashes'].items(): assert sha(p) == h, p
    for p, h in cfg['input_hashes'].items(): assert pre['hashes'][p] == h
    assert pre['hashes']['experiments/heading_scope_v51.json'] == sha('experiments/heading_scope_v51.json')
    assert cfg['registered_at_utc'] < pre['sealed_at_utc'] < manifest['finished_at_utc'] and cfg['request_budget'] == 0
    assert cfg['slot_id'] == 'q01s01'
    slot = next(s for s in read('data/v50/selection.json')['slots'] if s['slot_id'] == cfg['slot_id']); nominee = slot['nominee']
    expected = strip_suffix(nominee['title']); receipt = read(cfg['receipt']); original = read(cfg['observation'])
    assert receipt['requested_url'] == nominee['url'] and receipt['transport_complete']
    assert receipt['artifacts']['body.bin']['sha256'] == sha(cfg['raw'])
    raw = (ROOT / cfg['raw']).read_bytes(); soup = BeautifulSoup(raw, 'html.parser')
    tags = [node for node in soup.descendants if isinstance(node, Tag)]; numbers = {id(tag): i for i, tag in enumerate(tags)}
    titles = []; json_records = []; json_errors = []
    def record(channel, tag, value, location=None):
        titles.append({'channel': channel, 'dom_index': numbers[id(tag)], 'tag': tag.name, 'value': value,
            'ancestor_tags': [p.name for p in tag.parents if isinstance(p, Tag) and p.name != '[document]'], 'location': location,
            'nonempty': isinstance(value, str) and bool(value.strip()),
            'matches_expected': isinstance(value, str) and norm(strip_suffix(value)) == norm(expected)})
    for t in tags:
        if t.name == 'title': record('html_title', t, t.get_text(' ', strip=True))
    for t in tags:
        if t.name != 'meta': continue
        for attr, value, family in [('property', 'og:title', 'og_title'), ('name', 'twitter:title', 'twitter_title'), ('name', 'title', 'name_title')]:
            if t.get(attr) == value: record(family, t, t.get('content', ''))
    for t in tags:
        if t.name != 'script' or t.get('type') != 'application/ld+json': continue
        try: stack = [('$', json.loads(t.get_text()))]
        except (ValueError, TypeError) as e:
            json_errors.append({'dom_index': numbers[id(t)], 'error': type(e).__name__}); continue
        while stack:
            path, value = stack.pop()
            if isinstance(value, dict):
                types = value.get('@type', []); types = [types] if isinstance(types, str) else types
                if isinstance(types, list) and set(x for x in types if isinstance(x, str)) & {'Article', 'NewsArticle', 'BlogPosting', 'ReportageNewsArticle'}:
                    json_records.append({'dom_index': numbers[id(t)], 'json_path': path, 'types': types,
                                         'headline': value.get('headline'), 'url': value.get('url'), '@id': value.get('@id')})
                    record('article_headline', t, value.get('headline'), path)
                stack.extend((path + '[' + json.dumps(k) + ']', v) for k, v in reversed(list(value.items())))
            elif isinstance(value, list): stack.extend((path + f'[{i}]', value[i]) for i in reversed(range(len(value))))
    identities = [{'channel': 'canonical', 'value': t.get('href', '')} for t in soup.select('link[rel=canonical]')]
    identities += [{'channel': 'og_url', 'value': t.get('content', '')} for t in soup.select('meta[property="og:url"]')]
    for r in identities: r['matches_nominee'] = key(r['value']) == key(nominee['url']) and key(nominee['url']) is not None
    publication = [t.get('content', '') for t in soup.select('meta[property="article:published_time"]')]
    modification = [t.get('content', '') for t in soup.select('meta[property="article:modified_time"]')]
    assert publication == original['published_time_values'] and modification == original['modified_time_values']
    for t in soup.select('script,style,noscript,template,svg,canvas'): t.decompose()
    body = soup.select('body'); containers = soup.select(read('experiments/publisher_intake_v50.json')['source_selector'])
    assert len(body) == len(containers) == 1; body = body[0]; container = containers[0]; body_text = body.get_text(' ', strip=True)
    assert body_text == original['body_text'] and digest(body_text) == original['body_text_sha256']
    for t in body.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']): record('heading_' + t.name, t, t.get_text(' ', strip=True))
    for t in body.select('.entry-title,.post-title,[itemprop=headline]'): record('title_element', t, t.get_text(' ', strip=True))
    for t in body.descendants:
        if not isinstance(t, Tag): continue
        for attr in ['alt', 'title', 'aria-label']:
            if attr in t.attrs: record('body_attribute_' + attr, t, t[attr], attr)
        if norm(t.get_text(' ', strip=True)) == norm(expected): record('body_exact_title_element', t, t.get_text(' ', strip=True))
    units = []; leaves = []
    categories = [('form', ['form', 'button', 'input', 'label']), ('table', ['table', 'thead', 'tbody', 'tr', 'td', 'th']),
                  ('figure', ['figure', 'figcaption']), ('blockquote', ['blockquote']), ('list', ['ul', 'ol', 'li']),
                  ('heading', ['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])]
    for child in container.children:
        included = isinstance(child, Tag) and child.name == 'p'
        if included:
            text = child.get_text(' ', strip=True); occurrences = body_text.count(text) if text else 0
            at = body_text.find(text) if occurrences == 1 else None
            units.append({'unit': len(units), 'text': text, 'span': [at, at + len(text)] if at is not None else None, 'body_mapping_count': occurrences})
        nodes = child.descendants if isinstance(child, Tag) else [child]
        for node in nodes:
            if type(node) not in (NavigableString, CData) or not str(node).strip(): continue
            names = []
            for ancestor in node.parents:
                if ancestor is container: break
                names.append(ancestor.name)
            category = 'direct_p' if included else next((c for c, allowed in categories if any(name in allowed for name in names)), 'other')
            leaves.append({'leaf_index': len(leaves), 'text': str(node), 'stripped_text': str(node).strip(),
                'parent_dom_index': numbers[id(node.parent)], 'parent_tag': node.parent.name, 'direct_child_tag': child.name if isinstance(child, Tag) else None,
                'ancestor_tags_to_container': names, 'included_in_direct_p': included, 'category': category})
    assert units == original['paragraph_units']
    full = container.get_text(' ', strip=True); direct = ' '.join(p['text'] for p in units if p['text'])
    assert ' '.join(r['stripped_text'] for r in leaves) == full
    assert ' '.join(r['stripped_text'] for r in leaves if r['included_in_direct_p']) == direct
    witness = []; at = body_text.find(expected)
    while at >= 0:
        witness.append({'span': [at, at + len(expected)], 'text': expected}); at = body_text.find(expected, at + len(expected))
    meta = [r for r in titles if r['channel'] in {'html_title', 'og_title', 'twitter_title', 'article_headline'} and r['nonempty']]
    families = sorted({r['channel'] for r in meta}); titles_agree = bool(meta) and all(r['matches_expected'] for r in meta)
    identities_agree = (all(r['matches_nominee'] for r in identities) and {'canonical', 'og_url'} <= {r['channel'] for r in identities}
                        and key(receipt['final_url']) == key(nominee['url']) and key(nominee['url']) is not None)
    agreement = len(families) >= 2 and all(r['matches_expected'] for r in meta) and identities_agree
    excluded = [r for r in leaves if not r['included_in_direct_p']]
    counts = dict(sorted(Counter(r['category'] for r in excluded).items()))
    characters = {c: sum(len(r['stripped_text']) for r in excluded if r['category'] == c) for c in sorted(counts)}
    a = read('data/v51/audit.json')
    expected_audit = {'expected_title': expected, 'title_inventory': titles, 'article_jsonld_records': json_records, 'jsonld_errors': json_errors,
        'identity_inventory': identities, 'publication_values': publication, 'modification_values': modification,
        'nonempty_metadata_title_families': families, 'metadata_title_values_agree': titles_agree, 'identity_urls_agree': identities_agree,
        'descriptive_metadata_agreement': agreement, 'h1_count': len(body.find_all('h1')), 'all_document_h1_count': len(soup.find_all('h1')),
        'body_title_occurrences': witness, 'body_text': body_text, 'body_text_sha256': digest(body_text), 'paragraph_units': units,
        'container_text': full, 'container_text_sha256': digest(full), 'direct_p_text': direct, 'direct_p_text_sha256': digest(direct),
        'text_leaves': leaves, 'leaf_count': len(leaves), 'included_leaf_count': len(leaves) - len(excluded), 'excluded_leaf_count': len(excluded),
        'excluded_category_counts': counts, 'excluded_category_characters': characters, 'all_static_container_text_in_direct_p': not excluded}
    assert a == expected_audit
    old_report = read('runs/000050_publisher_intake/report.json'); old_result = next(r for r in old_report['slot_results'] if r['slot_id'] == cfg['slot_id'])
    assert old_report['ready_captures'] == 1 and old_report['intake_capacity_met'] is False
    assert old_result['ready_for_future_registration'] is False and old_result['unmet'] == ['single_matching_h1']
    assert original['headings'] == [] and original['checks']['single_matching_h1'] is False and a['all_document_h1_count'] == 0
    report = read('runs/000051_heading_scope/report.json')
    values = {'experiment_id': 'heading_scope_v51', 'outcome': 'metadata_agrees_h1_absent' if agreement else 'metadata_conflicting_or_unresolved',
        'slot_id': cfg['slot_id'], 'candidate_url': nominee['url'], 'candidate_title': expected, 'descriptive_metadata_agreement': agreement,
        'metadata_title_values_agree': titles_agree, 'identity_urls_agree': identities_agree, 'nonempty_metadata_title_families': families,
        'all_document_h1_count': 0, 'matching_title_record_counts': {c: sum(r['matches_expected'] for r in titles if r['channel'] == c) for c in sorted({r['channel'] for r in titles})},
        'body_title_occurrences': len(witness), 'jsonld_errors': len(json_errors), 'direct_paragraph_count': len(units),
        'full_container_characters': len(full), 'direct_p_characters': len(direct), 'leaf_count': len(leaves),
        'included_leaf_count': len(leaves) - len(excluded), 'excluded_leaf_count': len(excluded), 'excluded_category_counts': counts,
        'excluded_category_characters': characters, 'all_static_container_text_in_direct_p': not excluded,
        'v50_candidate_ready_unchanged': False, 'v50_ready_captures_unchanged': 1, 'v50_intake_capacity_met_unchanged': False,
        'network_requests': 0, 'browser_renders': 0, 'new_structural_scores': 0, 'opaque_lexical_or_semantic_scores': 0,
        'semantic_labels_admitted': 0, 'source_identities_admitted': 0, 'independent_reviews_admitted': 0,
        'untouched_test_units_admitted': 0, 'new_candidate_readiness_admissions': 0, 'external_messages_sent': 0,
        'scientific_acceptance': None, 'semantic_evaluation_metrics': None}
    assert report == values
    prior = []
    for path in sorted((ROOT / 'runs').glob('000*/manifest.json')):
        if path.parent != run: check_hashes(path.parent); prior.append(path.parent.name)
    assert len(prior) == 50
    for path in (ROOT / 'reports').glob('*_deliverable_seal.json'):
        for p, h in json.loads(path.read_text()).get('deliverable_hashes', {}).items(): assert sha(p) == h
    result = {'state': 'verified', 'manifest_sha256': sha('runs/000051_heading_scope/manifest.json'),
        'all_title_identity_and_jsonld_records_reconstructed': True, 'all_static_text_leaves_and_inclusion_categories_reconstructed': True,
        'old_body_paragraphs_and_readiness_unchanged': True, 'shared_html_parser': 'BeautifulSoup html.parser',
        'browser_visibility_or_dynamic_layout_validated': False, 'independent_scientific_review': False,
        'semantics_or_source_identity_validated': False, 'prior_runs_preserved': prior}
    out = ROOT / 'reports/000051_verification.json'
    if out.exists(): assert {k: v for k, v in json.loads(out.read_text()).items() if k != 'verified_at_utc'} == result
    else:
        with out.open('x') as stream: json.dump(result | {'verified_at_utc': datetime.now(timezone.utc).isoformat()}, stream, indent=2); stream.write('\n')
    print(json.dumps({'state': 'verified', 'prior_runs_preserved': len(prior), 'h1_count': 0, 'metadata_agreement': agreement,
                      'excluded_static_text_leaves': len(excluded)}, indent=2))


if __name__ == '__main__': main()
