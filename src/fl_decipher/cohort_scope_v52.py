"""Body-coordinate structural channels, without anchor or semantic scoring."""
from collections import Counter
import hashlib
from bs4 import BeautifulSoup
from bs4.element import CData, NavigableString

PRIORITY = [('form', {'form', 'button', 'input', 'label'}), ('table', {'table', 'thead', 'tbody', 'tr', 'td', 'th'}),
            ('figure', {'figure', 'figcaption'}), ('blockquote', {'blockquote'}), ('list', {'ul', 'ol', 'li'}),
            ('heading', {'h1', 'h2', 'h3', 'h4', 'h5', 'h6'}), ('paragraph', {'p'})]


def digest(s): return hashlib.sha256(s.encode()).hexdigest()


def extract_scope(raw, expected_body, selector):
    soup = BeautifulSoup(raw, 'html.parser'); tags = soup.find_all(True); ordinals = {id(t): i for i, t in enumerate(tags)}
    for t in soup.select('script,style,noscript,template,svg,canvas'): t.decompose()
    bodies = soup.select('body'); containers = soup.select(selector)
    if len(bodies) != 1 or len(containers) != 1: raise ValueError('body/container identity unavailable')
    body, container = bodies[0], containers[0]
    body_text = body.get_text(' ', strip=True)
    if body_text != expected_body: raise ValueError('frozen body mismatch')
    body_leaves = []; positions = {}; cursor = 0
    for node in body.descendants:
        if type(node) not in (NavigableString, CData) or not str(node).strip(): continue
        text = str(node).strip()
        if body_leaves: cursor += 1
        row = {'body_leaf_index': len(body_leaves), 'parent_dom_index': ordinals[id(node.parent)],
               'text': str(node), 'stripped_text': text, 'body_span': [cursor, cursor + len(text)]}
        positions[id(node)] = row; body_leaves.append(row); cursor += len(text)
    if ' '.join(r['stripped_text'] for r in body_leaves) != body_text: raise ValueError('body leaf serialization mismatch')
    leaves = []
    for node in container.descendants:
        if id(node) not in positions: continue
        ancestors = []; p = node.parent
        while p is not container: ancestors.append(p); p = p.parent
        names = {p.name for p in ancestors}
        channel, matching = next(((c, ts) for c, ts in PRIORITY if names & ts), ('other', set()))
        owner = next((p for p in reversed(ancestors) if p.name in matching), ancestors[-1] if ancestors else container)
        direct_child = ancestors[-1] if ancestors else None
        leaves.append({'leaf_index': len(leaves), **positions[id(node)], 'parent_tag': node.parent.name,
            'ancestor_tags_to_container': [p.name for p in ancestors], 'direct_child_tag': direct_child.name if direct_child else None,
            'old_direct_p_included': direct_child is not None and direct_child.name == 'p',
            'channel': channel, 'owner_dom_index': ordinals[id(owner)], 'owner_tag': owner.name})
    paragraphs = []
    for p in container.find_all('p'):
        nodes = [n for n in p.descendants if id(n) in positions]; text = p.get_text(' ', strip=True)
        span = [positions[id(nodes[0])]['body_span'][0], positions[id(nodes[-1])]['body_span'][1]] if nodes else None
        paragraphs.append({'paragraph_index': len(paragraphs), 'dom_index': ordinals[id(p)], 'direct_child': p.parent is container,
            'text': text, 'body_span': span, 'body_span_text_matches': (body_text[slice(*span)] == text) if span else text == '',
            'descendant_body_leaf_indices': [positions[id(n)]['body_leaf_index'] for n in nodes],
            'nested_p_descendants': len(p.find_all('p'))})
    legacy = []
    for p in container.find_all('p', recursive=False):
        text = p.get_text(' ', strip=True); count = body_text.count(text) if text else 0; at = body_text.find(text) if count == 1 else None
        legacy.append({'unit': len(legacy), 'text': text, 'span': [at, at + len(text)] if at is not None else None, 'body_mapping_count': count})
    runs = []
    for row in leaves:
        if row['channel'] != 'paragraph': continue
        at, end = row['body_span']
        extend = (bool(runs) and runs[-1]['owner_dom_index'] == row['owner_dom_index']
                  and runs[-1]['leaf_indices'][-1] + 1 == row['leaf_index'] and runs[-1]['body_span'][1] + 1 == at)
        if extend:
            runs[-1]['leaf_indices'].append(row['leaf_index']); runs[-1]['body_span'][1] = end
        else:
            runs.append({'unit': len(runs), 'owner_dom_index': row['owner_dom_index'], 'body_span': [at, end], 'leaf_indices': [row['leaf_index']]})
    for r in runs: r['text'] = body_text[slice(*r['body_span'])]
    full = container.get_text(' ', strip=True); old = ' '.join(p['text'] for p in legacy if p['text'])
    assert ' '.join(r['stripped_text'] for r in leaves) == full
    assert ' '.join(r['stripped_text'] for r in leaves if r['old_direct_p_included']) == old
    return {'body_text_sha256': digest(body_text), 'body_text': body_text, 'body_leaves': body_leaves,
        'container_text': full, 'container_text_sha256': digest(full), 'legacy_direct_paragraphs': legacy,
        'legacy_direct_p_text': old, 'legacy_direct_p_text_sha256': digest(old), 'container_leaves': leaves,
        'paragraph_inventory': paragraphs, 'paragraph_runs': runs,
        'channel_leaf_counts': dict(sorted(Counter(r['channel'] for r in leaves).items())),
        'channel_characters': {c: sum(len(r['stripped_text']) for r in leaves if r['channel'] == c) for c in sorted({r['channel'] for r in leaves})},
        'added_paragraph_leaf_indices': [r['leaf_index'] for r in leaves if r['channel'] == 'paragraph' and not r['old_direct_p_included']],
        'removed_legacy_leaf_indices': [r['leaf_index'] for r in leaves if r['old_direct_p_included'] and r['channel'] != 'paragraph']}


def accounting(scope):
    body = scope['body_text']; leaves = scope['container_leaves']; runs = scope['paragraph_runs']
    selected = [r['leaf_index'] for r in leaves if r['channel'] == 'paragraph']
    covered = [i for r in runs for i in r['leaf_indices']]
    return {'every_body_leaf_span_exact': all(body[slice(*r['body_span'])] == r['stripped_text'] for r in scope['body_leaves']),
        'every_container_leaf_span_exact': all(body[slice(*r['body_span'])] == r['stripped_text'] for r in leaves),
        'paragraph_inventory_spans_exact': all(p['body_span_text_matches'] for p in scope['paragraph_inventory']),
        'paragraph_runs_cover_selected_leaves_once': selected == covered and len(covered) == len(set(covered)),
        'run_spans_ordered_disjoint': all(a['body_span'][1] <= b['body_span'][0] for a, b in zip(runs, runs[1:])),
        'every_run_matches_original_span': all(body[slice(*r['body_span'])] == r['text'] == ' '.join(leaves[i]['stripped_text'] for i in r['leaf_indices']) for r in runs),
        'all_channel_leaves_accounted': sum(scope['channel_leaf_counts'].values()) == len(leaves),
        'all_channel_characters_accounted': sum(scope['channel_characters'].values()) == sum(len(r['stripped_text']) for r in leaves),
        'no_form_leaf_in_paragraph_runs': all(leaves[i]['channel'] != 'form' for i in covered)}
