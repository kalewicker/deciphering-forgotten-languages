"""Finite same-publisher discovery and capture-scope checks, without scoring."""
from datetime import date, datetime
import hashlib
import re
import unicodedata
from urllib.parse import urlsplit
from bs4 import BeautifulSoup


def norm(text): return ' '.join(unicodedata.normalize('NFC', text).casefold().split())


def article_key(url):
    try:
        p = urlsplit(url)
        if (p.scheme != 'https' or p.hostname != 'physicsworld.com' or p.username is not None
                or p.password is not None or p.port not in (None, 443) or p.query or p.fragment
                or not re.fullmatch(r'/a/[^/\s]+/?', p.path)):
            return None
        return 'https://physicsworld.com' + p.path.rstrip('/') + '/'
    except (ValueError, TypeError):
        return None


def topical(text):
    text = norm(text)
    return bool(re.search(r'\bneutrinos?\b', text) and re.search(r'\b(?:anita|antarctic|antarctica)\b', text))


def response_text(raw):
    if isinstance(raw, str): return raw
    if isinstance(raw, dict) and isinstance(raw.get('content'), list):
        blocks = raw['content']
        if all(isinstance(x, dict) and x.get('type') == 'text' and isinstance(x.get('text'), str) for x in blocks):
            return '\n'.join(x['text'] for x in blocks)
    return None


def result_headers(text):
    lines = text.splitlines(keepends=True); headers = []; offset = 0
    for i, line in enumerate(lines):
        match = re.fullmatch(r'(.+) \((https?://[^\s]+)\)\r?\n?', line)
        if match and i + 1 < len(lines) and 'wordlim' in lines[i + 1]:
            headers.append((offset, match.group(1), match.group(2)))
        offset += len(line)
    rows = []
    for rank, (start, title, url) in enumerate(headers):
        end = headers[rank + 1][0] if rank + 1 < len(headers) else len(text)
        block = text[start:end]
        rows.append({'rank': rank, 'title': title, 'url': url, 'response_span': [start, end],
                     'response_text': block, 'response_text_sha256': hashlib.sha256(block.encode()).hexdigest()})
    return rows


def nominate(responses, prior, slots_per_query):
    seen = set(); queries = []; slots = []
    excluded = set(prior['captured_article_keys']); exposures = prior['article_exposures']
    for index, response in enumerate(responses):
        text = response_text(response['response']) if response['error'] is None else None
        rows = result_headers(text) if text is not None else []
        chosen = []
        for row in rows:
            key = article_key(row['url']); duplicate = key is not None and key in seen
            if key is not None: seen.add(key)
            row['article_key'] = key; row['prior_exposure_tags'] = exposures.get(key, []) if key else []
            row['topical'] = topical(row['title'] + '\n' + row['response_text'])
            reason = ('invalid_article_url' if key is None else 'duplicate_returned_url' if duplicate else
                      'already_captured_source' if key in excluded else 'topic_terms_missing' if not row['topical'] else
                      'query_slot_cap' if len(chosen) >= slots_per_query else 'selected_first_eligible')
            row['decision_reason'] = reason; row['nominated'] = reason == 'selected_first_eligible'
            if row['nominated']: chosen.append(row)
        queries.append({'query_index': index, 'response_format_supported': text is not None, 'attributable_hits': len(rows), 'hits': rows})
        for slot in range(slots_per_query):
            row = chosen[slot] if slot < len(chosen) else None
            slots.append({'slot_id': f'q{index:02d}s{slot:02d}', 'query_index': index, 'slot_index': slot,
                          'nominee': {k: row[k] for k in ['rank', 'title', 'url', 'article_key', 'prior_exposure_tags']} if row else None})
    return {'queries': queries, 'slots': slots, 'occupied_slots': sum(s['nominee'] is not None for s in slots)}


def service_title(title):
    return re.sub(r'\s+[–—|\-]\s+Physics World\s*$', '', title)


def publication_dates(values):
    parsed = []; valid = bool(values)
    for value in values:
        try:
            parsed.append((date.fromisoformat(value) if len(value) == 10 else datetime.fromisoformat(value).date()).isoformat())
        except (ValueError, TypeError): valid = False
    return parsed, valid and len(set(parsed)) == 1


def inspect_page(raw, receipt, nominee, cfg):
    soup = BeautifulSoup(raw, 'html.parser')
    headings = [h.get_text(' ', strip=True) for h in soup.select('h1')]
    urls = [x.get('href', '') for x in soup.select('link[rel=canonical]')]
    urls += [x.get('content', '') for x in soup.select('meta[property="og:url"]')]
    published = [x.get('content', '') for x in soup.select('meta[property="article:published_time"]')]
    modified = [x.get('content', '') for x in soup.select('meta[property="article:modified_time"]')]
    parsed, date_agreement = publication_dates(published)
    for tag in soup.select('script,style,noscript,template,svg,canvas'): tag.decompose()
    bodies = soup.select('body'); containers = soup.select(cfg['source_selector'])
    body = bodies[0].get_text(' ', strip=True) if len(bodies) == 1 else ''
    units = []; mapping = True
    if len(containers) == 1:
        for i, p in enumerate(containers[0].find_all('p', recursive=False)):
            text = p.get_text(' ', strip=True)
            spans = [[m.start(), m.end()] for m in re.finditer(re.escape(text), body)] if text else []
            if text and len(spans) != 1: mapping = False
            units.append({'unit': i, 'text': text, 'span': spans[0] if len(spans) == 1 else None,
                          'body_mapping_count': len(spans)})
    content = ' '.join(u['text'] for u in units)
    key = article_key(nominee['url'])
    checks = {'transport_complete': receipt['transport_complete'], 'html_markup': b'<html' in raw.lower(),
        'single_body': len(bodies) == 1, 'final_url_matches': key is not None and article_key(receipt.get('final_url')) == key,
        'publisher_identity_matches': key is not None and any(article_key(url) == key for url in urls),
        'single_matching_h1': len(headings) == 1 and norm(headings[0]) == norm(service_title(nominee['title'])),
        'no_challenge_text': not any(s in body.casefold() for s in cfg['challenge_signatures']),
        'single_article_container': len(containers) == 1, 'unique_nonempty_paragraph_mapping': mapping,
        'minimum_paragraphs': sum(bool(u['text']) for u in units) >= cfg['minimum_paragraphs'],
        'minimum_paragraph_characters': sum(len(u['text']) for u in units) >= cfg['minimum_paragraph_characters'],
        'publication_date_agrees': date_agreement,
        'publication_date_in_window': date_agreement and cfg['date_min'] <= parsed[0] <= cfg['date_max'],
        'native_topic_terms': topical(' '.join(headings) + ' ' + content)}
    return {'ready_for_future_registration': all(checks.values()), 'checks': checks,
        'unmet': [k for k, v in checks.items() if not v], 'headings': headings, 'identity_urls': urls,
        'published_time_values': published, 'parsed_publication_dates': parsed, 'modified_time_values': modified,
        'body_text': body, 'body_text_sha256': hashlib.sha256(body.encode()).hexdigest(), 'paragraph_units': units,
        'paragraph_count': len(units), 'nonempty_paragraph_count': sum(bool(u['text']) for u in units),
        'paragraph_characters': sum(len(u['text']) for u in units), 'historical_bytes_authenticated': False,
        'false_parent_certified': False, 'independent_source_group_admitted': False}
