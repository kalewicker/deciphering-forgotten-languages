"""Fixed-witness context dossier; no alignment, translation or new overlap search."""
import re
from bs4 import BeautifulSoup
from .dated_capture_scope_v38 import literal_hits


def parts(text, start, stop, offset):
    if not 0 <= start < stop <= len(text):
        raise ValueError('invalid witness interval')
    rows = []
    for name, a, b in [('prefix', 0, start), ('fixed_shared_span', start, stop), ('suffix', stop, len(text))]:
        rows.append({'part': name, 'local_span': [a, b], 'global_span': [a + offset, b + offset], 'text': text[a:b]})
    assert ''.join(r['text'] for r in rows) == text
    return rows


def body_paragraphs(raw):
    soup = BeautifulSoup(raw, 'html.parser')
    for tag in soup.select('script,style,noscript,template,svg,canvas'):
        tag.decompose()
    bodies = soup.select('body')
    if len(bodies) != 1:
        raise ValueError('not one publisher body')
    body = bodies[0]
    return body.get_text(' ', strip=True), [p.get_text(' ', strip=True) for p in body.select('p')]


def occurrences(fragment, text):
    return [[m.start(), m.end()] for m in re.finditer(re.escape(fragment), text)] if fragment else []


def build(raw, source, target, quote, witness, context_characters=160):
    if target[slice(*quote['span'])] != quote['text']:
        raise ValueError('changed target quote')
    qa, qb = witness['query_char_span']; sa, sb = witness['source_char_span']
    if (quote['text'][qa:qb] != witness['query_fragment'] or source[sa:sb] != witness['source_fragment']
            or witness['target_char_span'] != [quote['span'][0] + qa, quote['span'][0] + qb]):
        raise ValueError('changed fixed witness')
    reproduced, paragraphs = body_paragraphs(raw)
    if reproduced != source:
        raise ValueError('publisher body differs from frozen v42 export')
    candidates = []
    for i, paragraph in enumerate(paragraphs):
        for a, b in occurrences(paragraph, source):
            if a <= sa < sb <= b:
                candidates.append({'paragraph_index': i, 'body_span': [a, b], 'text': paragraph})
    if len(candidates) != 1:
        return {'status': 'unavailable_paragraph_identity', 'paragraph_candidates': candidates,
                'context_checks': None, 'source_partition': None, 'target_partition': None}
    selected = candidates[0]; index = selected['paragraph_index']; start = selected['body_span'][0]
    target_parts = parts(quote['text'], qa, qb, quote['span'][0])
    source_parts = parts(selected['text'], sa - start, sb - start, start)
    window = [{'paragraph_index': i, 'text': paragraphs[i], 'body_spans': occurrences(paragraphs[i], source)}
              for i in range(max(0, index - 1), min(len(paragraphs), index + 2))]
    a = max(0, quote['span'][0] - context_characters)
    b = min(len(target), quote['span'][1] + context_characters)
    checks = []
    scopes = {'publisher_paragraph': selected['text'], 'publisher_body': source, 'target_quote': quote['text']}
    queries = [('target_prefix', target_parts[0]['text'], ['publisher_paragraph', 'publisher_body']),
               ('target_suffix', target_parts[2]['text'], ['publisher_paragraph', 'publisher_body']),
               ('beacon_phrase', 'Giselian beacon', ['target_quote', 'publisher_paragraph', 'publisher_body']),
               ('reported_name', 'Alan Watson', ['publisher_paragraph']),
               ('fixed_shared_fragment', witness['query_fragment'], ['target_quote', 'publisher_paragraph', 'publisher_body'])]
    for name, query, scope_names in queries:
        for scope in scope_names:
            found = literal_hits(query, scopes[scope]) if query.strip() else None
            checks.append({'check_id': name + ':' + scope, 'query': query, 'scope': scope,
                           'scope_offset': {'publisher_body': 0, 'publisher_paragraph': start, 'target_quote': quote['span'][0]}[scope],
                           'present': bool(found) if found is not None else None, 'hits': found})
    return {'status': 'context_available', 'paragraph_candidates': candidates, 'selected_paragraph': selected,
            'publisher_window': window, 'target_context': {'span': [a, b], 'text': target[a:b],
                'quote_span_within_context': [quote['span'][0] - a, quote['span'][1] - a]},
            'target_partition': target_parts, 'source_partition': source_parts, 'context_checks': checks,
            'partition_reassembly_passed': True, 'fixed_witness_unchanged': True,
            'opaque_passages_scored': 0, 'original_attribution_authenticated': False}


def fenced(text):
    length = max([len(m.group()) for m in re.finditer(r'`+', text)] + [2]) + 1
    fence = '`' * length
    return fence + 'text\n' + text + '\n' + fence + '\n'


def render(dossier):
    out = '# Quote02 context dossier\n\nLocal source-disclosed evidence; not independent review or translation.\n'
    if dossier['status'] != 'context_available':
        return out + '\nParagraph identity unavailable; no context interpretation admitted.\n'
    for name, rows in [('Frozen target quotation', dossier['target_partition']), ('Publisher paragraph', dossier['source_partition'])]:
        out += '\n## ' + name + '\n'
        for row in rows:
            out += '\n### ' + row['part'] + ' ' + str(row['global_span']) + '\n\n' + fenced(row['text'])
    out += '\n## Publisher context, one neighboring paragraph each side\n'
    for row in dossier['publisher_window']:
        out += '\nParagraph ' + str(row['paragraph_index']) + ':\n\n' + fenced(row['text'])
    out += '\n## Target character context (opaque surroundings unscored)\n\n' + fenced(dossier['target_context']['text'])
    out += '\n## Fixed literal checks\n\n| Check | Present |\n|---|---|\n'
    for c in dossier['context_checks']:
        out += '| ' + c['check_id'] + ' | ' + str(c['present']) + ' |\n'
    out += '\nOutside-witness text may contain shorter overlaps; no exhaustive non-overlap or copying-direction claim.\n'
    return out
