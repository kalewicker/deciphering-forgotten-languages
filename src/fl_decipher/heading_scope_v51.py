"""Static title and text-leaf accounting; never revises intake eligibility."""
from collections import Counter
import hashlib
import json
import re
from bs4 import BeautifulSoup
from bs4.element import CData, NavigableString
from fl_decipher.publisher_intake_v50 import article_key, norm, service_title

ARTICLE_TYPES = {'Article', 'NewsArticle', 'BlogPosting', 'ReportageNewsArticle'}
CATEGORIES = [('form', {'form', 'button', 'input', 'label'}), ('table', {'table', 'thead', 'tbody', 'tr', 'td', 'th'}),
              ('figure', {'figure', 'figcaption'}), ('blockquote', {'blockquote'}), ('list', {'ul', 'ol', 'li'}),
              ('heading', {'h1', 'h2', 'h3', 'h4', 'h5', 'h6'})]


def digest(text): return hashlib.sha256(text.encode()).hexdigest()


def article_nodes(value, path='$'):
    out = []
    if isinstance(value, dict):
        types = value.get('@type', []); types = [types] if isinstance(types, str) else types
        if isinstance(types, list) and any(t in ARTICLE_TYPES for t in types if isinstance(t, str)):
            out.append({'json_path': path, 'types': types, 'headline': value.get('headline'), 'url': value.get('url'), '@id': value.get('@id')})
        for k, v in value.items(): out.extend(article_nodes(v, path + '[' + json.dumps(k) + ']'))
    elif isinstance(value, list):
        for i, v in enumerate(value): out.extend(article_nodes(v, path + f'[{i}]'))
    return out


def audit(raw, expected, requested_url, final_url, selector):
    soup = BeautifulSoup(raw, 'html.parser'); tags = soup.find_all(True); ordinal = {id(t): i for i, t in enumerate(tags)}
    title_rows = []; json_records = []; json_errors = []
    def record(channel, tag, value, location=None):
        title_rows.append({'channel': channel, 'dom_index': ordinal[id(tag)], 'tag': tag.name, 'value': value,
            'ancestor_tags': [p.name for p in tag.parents if getattr(p, 'name', None) and p.name != '[document]'],
            'location': location, 'nonempty': isinstance(value, str) and bool(value.strip()),
            'matches_expected': isinstance(value, str) and norm(service_title(value)) == norm(expected)})
    for tag in soup.select('title'): record('html_title', tag, tag.get_text(' ', strip=True))
    for tag in soup.find_all('meta'):
        for attr, key, channel in [('property', 'og:title', 'og_title'), ('name', 'twitter:title', 'twitter_title'), ('name', 'title', 'name_title')]:
            if tag.get(attr) == key: record(channel, tag, tag.get('content', ''))
    for script in soup.select('script[type="application/ld+json"]'):
        try: nodes = article_nodes(json.loads(script.get_text()))
        except (ValueError, TypeError) as e:
            json_errors.append({'dom_index': ordinal[id(script)], 'error': type(e).__name__}); continue
        for node in nodes:
            json_records.append({'dom_index': ordinal[id(script)], **node})
            record('article_headline', script, node['headline'], node['json_path'])
    identities = [{'channel': 'canonical', 'value': t.get('href', '')} for t in soup.select('link[rel=canonical]')]
    identities += [{'channel': 'og_url', 'value': t.get('content', '')} for t in soup.select('meta[property="og:url"]')]
    for row in identities: row['matches_nominee'] = article_key(row['value']) == article_key(requested_url) and article_key(requested_url) is not None
    published = [t.get('content', '') for t in soup.select('meta[property="article:published_time"]')]
    modified = [t.get('content', '') for t in soup.select('meta[property="article:modified_time"]')]
    for tag in soup.select('script,style,noscript,template,svg,canvas'): tag.decompose()
    bodies = soup.select('body'); containers = soup.select(selector)
    if len(bodies) != 1 or len(containers) != 1: raise ValueError('ambiguous body/container')
    body = bodies[0]; container = containers[0]; body_text = body.get_text(' ', strip=True)
    for tag in body.select('h1,h2,h3,h4,h5,h6'): record('heading_' + tag.name, tag, tag.get_text(' ', strip=True))
    for tag in body.select('.entry-title,.post-title,[itemprop=headline]'): record('title_element', tag, tag.get_text(' ', strip=True))
    for tag in body.find_all(True):
        for attr in ['alt', 'title', 'aria-label']:
            if tag.has_attr(attr): record('body_attribute_' + attr, tag, tag[attr], attr)
        if norm(tag.get_text(' ', strip=True)) == norm(expected): record('body_exact_title_element', tag, tag.get_text(' ', strip=True))
    units = []
    for i, p in enumerate(container.find_all('p', recursive=False)):
        text = p.get_text(' ', strip=True); count = body_text.count(text) if text else 0; start = body_text.find(text) if count == 1 else None
        units.append({'unit': i, 'text': text, 'span': [start, start + len(text)] if start is not None else None, 'body_mapping_count': count})
    leaves = []
    for node in container.descendants:
        if type(node) not in (NavigableString, CData) or not str(node).strip(): continue
        owner = node
        while owner.parent is not container: owner = owner.parent
        included = getattr(owner, 'name', None) == 'p'
        ancestors = []; p = node.parent
        while p is not container: ancestors.append(p.name); p = p.parent
        category = 'direct_p' if included else next((name for name, names in CATEGORIES if set(ancestors) & names), 'other')
        leaves.append({'leaf_index': len(leaves), 'text': str(node), 'stripped_text': str(node).strip(),
            'parent_dom_index': ordinal[id(node.parent)], 'parent_tag': node.parent.name,
            'direct_child_tag': getattr(owner, 'name', None), 'ancestor_tags_to_container': ancestors,
            'included_in_direct_p': included, 'category': category})
    full = container.get_text(' ', strip=True); direct = ' '.join(u['text'] for u in units if u['text'])
    assert ' '.join(r['stripped_text'] for r in leaves) == full
    assert ' '.join(r['stripped_text'] for r in leaves if r['included_in_direct_p']) == direct
    families = {'html_title', 'og_title', 'twitter_title', 'article_headline'}
    meta = [r for r in title_rows if r['channel'] in families and r['nonempty']]
    nonempty_families = sorted({r['channel'] for r in meta})
    identity_agrees = (all(r['matches_nominee'] for r in identities) and {'canonical', 'og_url'} <= {r['channel'] for r in identities}
                       and article_key(final_url) == article_key(requested_url) and article_key(requested_url) is not None)
    excluded = [r for r in leaves if not r['included_in_direct_p']]
    return {'expected_title': expected, 'title_inventory': title_rows, 'article_jsonld_records': json_records, 'jsonld_errors': json_errors,
        'identity_inventory': identities, 'publication_values': published, 'modification_values': modified,
        'nonempty_metadata_title_families': nonempty_families, 'metadata_title_values_agree': bool(meta) and all(r['matches_expected'] for r in meta),
        'identity_urls_agree': identity_agrees,
        'descriptive_metadata_agreement': len(nonempty_families) >= 2 and all(r['matches_expected'] for r in meta) and identity_agrees,
        'h1_count': len(body.select('h1')), 'all_document_h1_count': len(soup.select('h1')),
        'body_title_occurrences': [{'span': [m.start(), m.end()], 'text': m.group()} for m in re.finditer(re.escape(expected), body_text)],
        'body_text': body_text, 'body_text_sha256': digest(body_text), 'paragraph_units': units,
        'container_text': full, 'container_text_sha256': digest(full), 'direct_p_text': direct, 'direct_p_text_sha256': digest(direct),
        'text_leaves': leaves, 'leaf_count': len(leaves), 'included_leaf_count': len(leaves) - len(excluded), 'excluded_leaf_count': len(excluded),
        'excluded_category_counts': dict(sorted(Counter(r['category'] for r in excluded).items())),
        'excluded_category_characters': {k: sum(len(r['stripped_text']) for r in excluded if r['category'] == k) for k in sorted({r['category'] for r in excluded})},
        'all_static_container_text_in_direct_p': not excluded}
