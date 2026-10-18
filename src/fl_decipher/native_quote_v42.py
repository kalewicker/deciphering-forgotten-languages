"""Fixed visible-page quotation check; attribution remains a contextual observation."""
import re
from bs4 import BeautifulSoup
from .capture_review_v23 import normalize_title, resource_key
from .dated_capture_scope_v38 import literal_hits


def inspect_page(raw, receipt, cfg):
    if not receipt['transport_complete']:
        return {'material_available': False, 'unmet': ['transport_complete'],
                'text': None, 'quote_present': None, 'quote_hits': None, 'contexts': []}
    soup = BeautifulSoup(raw, 'html.parser')
    headings = [tag.get_text(' ', strip=True) for tag in soup.select('h1')]
    urls = [tag.get('href', '') for tag in soup.select('link[rel=canonical]')]
    urls += [tag.get('content', '') for tag in soup.select('meta[property="og:url"]')]
    metadata = [dict(tag.attrs) for tag in soup.select('meta')]
    times = [dict(tag.attrs) | {'visible_text': tag.get_text(' ', strip=True)} for tag in soup.select('time')]
    bodies = soup.select('body')
    for node in soup.select('script,style,noscript,template,svg,canvas'):
        node.decompose()
    body = bodies[0] if len(bodies) == 1 else None
    text = body.get_text(' ', strip=True) if body else ''
    gate = {
        'transport_complete': True,
        'html_markup': b'<html' in raw.lower(),
        'single_body': len(bodies) == 1,
        'final_url_matches': resource_key(receipt.get('final_url')) == resource_key(cfg['source_url']),
        'publisher_identity_url_matches': any(resource_key(u) == resource_key(cfg['source_url']) for u in urls),
        'single_expected_h1': sum(normalize_title(h) == normalize_title(cfg['expected_title']) for h in headings) == 1,
        'minimum_visible_characters': len(text) >= cfg['minimum_visible_characters'],
        'no_challenge_text': not any(s in text.casefold() for s in cfg['challenge_signatures']),
    }
    available = all(gate.values())
    result = {'material_available': available, 'requirements': gate,
              'unmet': [k for k, v in gate.items() if not v], 'headings': headings,
              'identity_urls': urls, 'metadata': metadata, 'time_elements': times,
              'text': text if available else None, 'quote_present': None, 'quote_hits': None, 'contexts': []}
    if not available:
        return result
    result['quote_hits'] = literal_hits(cfg['quote']['text'], text)
    result['quote_present'] = bool(result['quote_hits'])
    paragraphs = [p.get_text(' ', strip=True) for p in body.select('p')]
    for index, paragraph in enumerate(paragraphs):
        hits = literal_hits(cfg['quote']['text'], paragraph)
        if not hits:
            continue
        window = [{'paragraph_index': j, 'text': paragraphs[j]} for j in range(max(0, index - 1), min(len(paragraphs), index + 2))]
        context = ' '.join(p['text'] for p in window)
        result['contexts'].append({'quote_paragraph_index': index, 'quote_paragraph': paragraph,
            'paragraph_hits': hits, 'body_paragraph_spans': [[m.start(), m.end()] for m in re.finditer(re.escape(paragraph), text)],
            'window': window, 'gorham_name_visible': bool(re.search(r'\bgorham\b', context, re.I)),
            'he_says_visible': 'he says' in context.casefold(), 'attribution_authenticated': False})
    return result
