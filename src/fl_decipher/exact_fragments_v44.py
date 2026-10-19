"""Maximal contiguous exact-token runs with original Unicode coordinates."""
import re
import unicodedata


def token_rows(text):
    return [{'normalized': unicodedata.normalize('NFC', m.group()).casefold(),
             'span': [m.start(), m.end()]} for m in re.finditer(r'\S+', text)]


def audit(query, source, minimum_tokens=8, target_offset=0):
    if minimum_tokens < 1:
        raise ValueError('minimum_tokens must be positive')
    qt = token_rows(query)
    if source is None:
        return {'available': False, 'query_token_count': len(qt), 'source_token_count': None,
                'minimum_tokens': minimum_tokens, 'longest_run_tokens': None, 'runs': None,
                'qualifying_run_count': None, 'qualifying_overlap_present': None,
                'covered_query_token_indices': None, 'covered_query_tokens': None}
    st = token_rows(source)
    q = [r['normalized'] for r in qt]; s = [r['normalized'] for r in st]
    longest = 0; runs = []; covered = set()
    for i, word in enumerate(q):
        for j, other in enumerate(s):
            if word != other or (i > 0 and j > 0 and q[i - 1] == s[j - 1]):
                continue
            length = 1
            while i + length < len(q) and j + length < len(s) and q[i + length] == s[j + length]:
                length += 1
            longest = max(longest, length)
            if length < minimum_tokens:
                continue
            qa, qb = qt[i]['span'][0], qt[i + length - 1]['span'][1]
            sa, sb = st[j]['span'][0], st[j + length - 1]['span'][1]
            runs.append({'query_token_span': [i, i + length], 'source_token_span': [j, j + length],
                         'query_char_span': [qa, qb], 'source_char_span': [sa, sb],
                         'target_char_span': [qa + target_offset, qb + target_offset],
                         'token_count': length, 'normalized_tokens': q[i:i + length],
                         'query_fragment': query[qa:qb], 'source_fragment': source[sa:sb]})
            covered.update(range(i, i + length))
    return {'available': True, 'query_token_count': len(qt), 'source_token_count': len(st),
            'minimum_tokens': minimum_tokens, 'longest_run_tokens': longest, 'runs': runs,
            'qualifying_run_count': len(runs), 'qualifying_overlap_present': bool(runs),
            'covered_query_token_indices': sorted(covered), 'covered_query_tokens': len(covered)}
