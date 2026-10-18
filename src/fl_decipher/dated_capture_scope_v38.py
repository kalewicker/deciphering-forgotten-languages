"""Dated-material gates and exact observable text scope; no semantic model."""
import base64
from email.utils import parsedate_to_datetime
import hashlib
import re
import unicodedata

from fl_decipher.capture_review_v23 import select_archive, extract_post


def archive_selection(raw, cfg):
    result = select_archive(raw, {'fl_url': cfg['fl_url'], 'archive_cutoff': cfg['archive_cutoff']})
    if result['eligible'] and (result['record']['original'] != cfg['fl_url'] or
                               not re.fullmatch(r'[A-Z2-7]{32}', result['record']['digest'])):
        return {**result, 'eligible': False, 'reason': 'exact_original_or_digest_format_failure', 'replay_url': None}
    return result


def normalized(text):
    return ' '.join(unicodedata.normalize('NFC', text).casefold().split())


def literal_hits(query, text):
    """Map normalized substring hits back to exact enclosing source-token spans."""
    pieces, mapping, at = [], [], 0
    for m in re.finditer(r'\S+', text):
        word = normalized(m.group())
        if pieces:
            at += 1
        pieces.append(word)
        mapping.append((at, at+len(word), m.start(), m.end()))
        at += len(word)
    haystack = ' '.join(pieces)
    assert haystack == normalized(text)
    needle = normalized(query)
    if not needle:
        return []
    result, start = [], 0
    while (found := haystack.find(needle, start)) >= 0:
        stop = found+len(needle)
        included = [r for r in mapping if r[0] < stop and r[1] > found]
        assert included
        a, b = included[0][2], included[-1][3]
        witness = text[a:b]
        assert needle in normalized(witness)
        result.append({'normalized_span': [found, stop], 'source_span': [a, b], 'source_quote': witness})
        start = found+1
    return result


def indexed_export(parent, lower=28, upper=88):
    matches = list(re.finditer(r'(?:^|(?<=\s))L(\d+):[ \t]?', parent))
    rows, texts, offset = [], [], 0
    for i, m in enumerate(matches):
        number = int(m.group(1))
        if not lower <= number <= upper:
            continue
        start, end = m.end(), matches[i+1].start() if i+1 < len(matches) else len(parent)
        raw = parent[start:end]
        # Browser link wrappers are derivatives, not raw HTML or original offsets.
        cleaned = re.sub('\ue200cite\ue202([^\ue201]+)\ue201', lambda x: x.group(1).split('†')[1] if '†' in x.group(1) else '', raw).strip()
        if texts:
            offset += 1
        rows.append({'reported_line': number, 'parent_span': [start, end], 'parent_quote': raw,
                     'derived_span': [offset, offset+len(cleaned)], 'derived_text': cleaned})
        texts.append(cleaned)
        offset += len(cleaned)
    assert rows and rows[0]['reported_line'] == lower and rows[-1]['reported_line'] == upper
    assert len({r['reported_line'] for r in rows}) == len(rows)
    return {'text': '\n'.join(texts), 'lineage': rows, 'representation': 'indexed_line_derivative',
            'raw_post': False, 'complete_post_proven': False, 'fixed_line_scope': [lower, upper]}


def dated_gate(cfg, metadata_receipt, metadata_raw, replay_receipt, replay_raw, headers):
    selection = archive_selection(metadata_raw, cfg) if metadata_receipt['transport_complete'] else {
        'eligible': False, 'reason': 'metadata_transport_unavailable', 'record': None, 'replay_url': None}
    extract = extract_post(replay_raw, replay_receipt, cfg, selection) if selection['eligible'] else {
        'eligible': False, 'requirements': {}, 'text': None, 'unmet': ['eligible_cdx_selection_missing']}
    blocks = [b for b in re.split(r'\r?\n\r?\n', headers) if re.match(r'HTTP/\S+\s+\d+', b)]
    final_headers = blocks[-1] if blocks else ''
    values = re.findall(r'^memento-datetime:\s*(.+?)\s*$', final_headers, re.I | re.M)
    date = None
    if values:
        try:
            date = parsedate_to_datetime(values[-1]).strftime('%Y%m%d%H%M%S')
        except (ValueError, TypeError, OverflowError):
            pass
    sha1 = base64.b32encode(hashlib.sha1(replay_raw).digest()).decode().rstrip('=') if replay_receipt['transport_complete'] else None
    record = selection['record']
    checks = {'metadata_transport_complete': metadata_receipt['transport_complete'], 'single_exact_cdx_record': selection['eligible'],
              'replay_transport_complete': replay_receipt['transport_complete'],
              'post_body_and_identity_gate': extract['eligible'],
              'memento_timestamp_matches': bool(record and date == record['timestamp']),
              'decoded_body_matches_cdx_digest': bool(record and sha1 == record['digest'])}
    return {'selection': selection, 'checks': checks, 'passed': all(checks.values()),
            'memento_timestamp': date, 'decoded_body_sha1_base32': sha1,
            'cdx_digest': record['digest'] if record else None,
            'digest_representation': 'Saved curl content-decoded body; encoding-layer mismatch not repaired',
            'post_extraction': extract}


def quote_spans(text):
    result = []
    for m in re.finditer(r'"([^\"]+)"|“([^”]+)”', text, re.S):
        group = 1 if m.group(1) is not None else 2
        if m.group(group).strip():
            result.append({'quote_id': f'quote{len(result):02d}', 'span': [m.start(group), m.end(group)], 'text': m.group(group),
                           'language_or_meaning_admitted': False})
    return result


def observable_scope(target, pages, anchors):
    quotes = []
    for q in quote_spans(target):
        hits = [{'page': p['page'], **hit} for p in pages for hit in literal_hits(q['text'], p['text'])]
        quotes.append({**q, 'source_hits': hits, 'literal_source_presence': bool(hits)})
    controls = []
    for p in pages:
        first = next(line for line in p['text'].splitlines() if line.strip())
        hits = literal_hits(first, p['text'])
        controls.append({'page': p['page'], 'query': first, 'own_page_hits': hits, 'passed': bool(hits)})
    absent_marker = 'flv38literalabsencecontrol20261018'
    absent = [{'page': p['page'], **hit} for p in pages for hit in literal_hits(absent_marker, p['text'])]
    def count(anchor, text):
        return len(list(re.finditer(r'(?<!\w)'+re.escape(normalized(anchor))+r'(?!\w)', normalized(text))))
    anchor_rows = [{'anchor': a, 'target_count': count(a, target),
                    'source_page_counts': [{'page': p['page'], 'count': count(a, p['text'])} for p in pages],
                    'source_total': sum(count(a, p['text']) for p in pages)} for a in anchors]
    citation = 'http://arxiv.org/abs/hep-ph/0209057v1'
    return {'quote_denominator': len(quotes), 'quotes_with_literal_source_presence': sum(q['literal_source_presence'] for q in quotes),
            'quotes': quotes, 'positive_controls': controls, 'positive_controls_passed': sum(c['passed'] for c in controls),
            'negative_control': {'query': absent_marker, 'source_hits': absent, 'passed': not absent}, 'anchors': anchor_rows,
            'exact_citation_hits_in_target': literal_hits(citation, target),
            'opaque_passages_scored': 0, 'semantic_evaluation_metrics': None, 'source_relationship': 'unresolved',
            'whole_post_source_coverage': 'unresolved', 'independent_review': False}
