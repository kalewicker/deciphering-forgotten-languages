"""Snapshot-specific, offline reference metadata recovery; no source resolution."""
import hashlib
import re
from bs4 import BeautifulSoup, NavigableString, Tag
from fl_decipher.source_intake_v37 import citation

PREFIX = re.compile(r'(?<!\w)(arxiv(?:\.org)?\s*:\s*|doi\s*:\s*|https?://(?:dx\.)?doi\.org/)', re.I)
BARE_DOI = re.compile(r'(?<![\w./])10\.\d{4,9}/[^\s]+', re.I)
ARXIV = re.compile(r'(\d{4}\.\d{4,5}|[a-z-]+(?:\.[a-z-]+)?/\d{7})(v[1-9]\d*)?', re.I)
DOI = re.compile(r'10\.\d{4,9}/[^\s]+', re.I)
BOUNDARY = 'Aissen, Judith (2003).'


def recover(raw, export, known_urls):
    soup = BeautifulSoup(raw, 'html.parser')
    indices = {id(t): i for i, t in enumerate(soup.select('*'))}
    bodies = soup.select('div.post-body')
    if len(bodies) != 1:
        raise ValueError('requires exactly one post-body')
    body = bodies[0]
    children = list(body.children)
    child_ids = {id(t): i for i, t in enumerate(children)}
    leaves, runs, parts = [], [], []
    offset = 0
    # Match BeautifulSoup get_text's string types; comments/runtime text excluded.
    for node_index, node in enumerate(n for n in body.descendants if isinstance(n, NavigableString)):
        if type(node) not in body.MAIN_CONTENT_STRING_TYPES or any(p.name in ['script', 'style', 'noscript'] for p in node.parents):
            continue
        value = str(node).strip()
        if not value:
            continue
        owner = node
        while owner.parent is not body:
            owner = owner.parent
        child_index = child_ids[id(owner)]
        start = offset + bool(parts)
        end = start + len(value)
        leaf = {'body_text_node_index': node_index, 'span': [start, end], 'text': value,
                'direct_child_index': child_index, 'parent_dom_tag_index': indices[id(node.parent)]}
        leaves.append(leaf)
        if not runs or runs[-1]['direct_child_index'] != child_index:
            runs.append({'run_id': len(runs), 'direct_child_index': child_index,
                         'owner_tag': owner.name if isinstance(owner, Tag) else None,
                         'owner_dom_tag_index': indices[id(owner)] if isinstance(owner, Tag) else None,
                         'span': [start, end], 'leaf_ids': []})
        runs[-1]['span'][1] = end
        runs[-1]['leaf_ids'].append(len(leaves) - 1)
        parts.append(value)
        offset = end
    text = ' '.join(parts)
    parent = hashlib.sha256(raw).hexdigest()
    if text != export['text'] or parent != export['parent_sha256'] or hashlib.sha256(text.encode()).hexdigest() != export['text_sha256']:
        raise ValueError('sealed export mismatch')
    for run in runs:
        run['text'] = text[slice(*run['span'])]
    starts = [r['run_id'] for r in runs if r['owner_tag'] == 'div' and r['text'].startswith(BOUNDARY)]
    tail = runs[starts[0]:] if len(starts) == 1 else []
    refs = []
    for r in tail:
        refs.append({'reference_id': len(refs), 'run_id': r['run_id'], 'span': r['span'], 'text': r['text'],
                     'year_witnesses': [{'literal': m.group(), 'span': [r['span'][0]+m.start(), r['span'][0]+m.end()]} for m in re.finditer(r'(?<!\d)(?:18|19|20)\d{2}(?!\d)', r['text'])],
                     'identifier_occurrence_ids': [], 'resolution_status': 'no_recognized_direct_identifier'})
    candidates = []
    for m in PREFIX.finditer(text):
        token = re.match(r'\S*', text[m.end():]).group().rstrip('.,;)]}')
        candidates.append((m.start(), m.end(), m.end()+len(token), 'arxiv' if m.group().lower().startswith('arxiv') else 'doi'))
    for m in BARE_DOI.finditer(text):
        if not any(a <= m.start() < c for a, _, c, _ in candidates):
            token = m.group().rstrip('.,;)]}')
            candidates.append((m.start(), m.start(), m.start()+len(token), 'doi'))
    known = {c['identifier'] for u in known_urls if (c := citation(u))}
    occurrences, first = [], {}
    for a, b, c, kind in sorted(candidates):
        literal = text[b:c]
        owners = [r for r in runs if r['span'][0] <= a and c <= r['span'][1]]
        match = (ARXIV if kind == 'arxiv' else DOI).fullmatch(literal)
        valid = bool(match) and len(owners) == 1
        identifier = kind+':'+(match.group(1) if kind == 'arxiv' else literal).lower() if valid else None
        version = match.group(2) if valid and kind == 'arxiv' else None
        ref_ids = [r['reference_id'] for r in refs if r['span'][0] <= a and c <= r['span'][1]]
        i = len(occurrences)
        row = {'occurrence_id': i, 'kind': kind, 'span': [a, c], 'token_span': [b, c], 'literal': literal,
               'identifier': identifier, 'declared_version': version, 'version_status': 'explicit' if version else 'unspecified' if kind == 'arxiv' else 'not_applicable',
               'run_id': owners[0]['run_id'] if len(owners) == 1 else None, 'reference_ids': ref_ids,
               'status': 'recognized_syntax_only' if valid else 'cross_run_token' if len(owners) != 1 else 'malformed_identifier',
               'duplicate_of_occurrence': first.get(identifier) if identifier else None,
               'prior_registry_status': 'identifier_recorded' if identifier in known else 'identifier_not_recorded_in_frozen_inventory' if identifier else 'not_applicable'}
        occurrences.append(row)
        if identifier and identifier not in first:
            first[identifier] = i
        for j in ref_ids:
            refs[j]['identifier_occurrence_ids'].append(i)
            if identifier:
                refs[j]['resolution_status'] = 'identifier_syntax_recovered_metadata_unverified'
    return {'raw_parent_sha256': parent, 'text_sha256': export['text_sha256'], 'unicode_characters': len(text),
            'leaves': leaves, 'runs': runs, 'boundary_match_run_ids': starts,
            'tail_status': 'located_exposed_boundary' if len(starts) == 1 else 'unresolved_boundary',
            'references': refs, 'identifier_occurrences': occurrences, 'recognized_identifiers': list(first),
            'known_identifier_matches': sorted(set(first) & known), 'network_requests': 0,
            'source_candidates_selected': 0, 'source_identity_admitted': False, 'untouched_test_eligible': False}
