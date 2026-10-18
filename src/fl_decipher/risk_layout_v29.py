"""Registered character-based Risk derivative; no semantic inference or repairs."""
from collections import Counter
from statistics import median
import re
import unicodedata


def raster_rules(gray, width, height, pdf_width, pdf_height):
    assert len(gray) == width * height
    runs = []
    for y in range(height):
        if 20 * y < 11 * height:
            continue
        x = 0
        while x < width:
            if gray[y * width + x] > 128:
                x += 1
                continue
            start = x
            while x < width and gray[y * width + x] <= 128:
                x += 1
            if 5 * (x - start) >= width and 20 * start <= 7 * width:
                runs.append({'y': y, 'x0': start, 'x1': x})
    groups = []
    for run in runs:
        group = next((g for g in groups if 0 <= run['y'] - g[-1]['y'] <= 2
                      and abs(run['x0'] - g[0]['x0']) <= 2 and abs(run['x1'] - g[0]['x1']) <= 2), None)
        if group is None:
            groups.append([run])
        else:
            group.append(run)
    return [{'pixel_runs': g, 'pixel_box': [min(r['x0'] for r in g), g[0]['y'], max(r['x1'] for r in g), g[-1]['y'] + 1],
             'x0': round(min(r['x0'] for r in g) / width * pdf_width, 6),
             'x1': round(max(r['x1'] for r in g) / width * pdf_width, 6),
             'top': round(g[0]['y'] / height * pdf_height, 6),
             'bottom': round((g[-1]['y'] + 1) / height * pdf_height, 6)} for g in groups]


def orientation(c):
    matrix = c['matrix'][:4]
    if matrix == [1., 0., 0., 1.]:
        return 'upright'
    if matrix == [0., 1., -1., 0.]:
        return 'quarter_turn'
    return 'unknown'


def em(c):
    return c['size'] if orientation(c) != 'quarter_turn' else round(c['x1'] - c['x0'], 6)


def baseline(c, height):
    return round(height - c['matrix'][5], 6) if orientation(c) == 'upright' else c['matrix'][4]


def token_spans(text):
    spans = []
    start = None
    for i, ch in enumerate(text + ' '):
        if ch.isalnum() or unicodedata.category(ch).startswith('M'):
            if start is None:
                start = i
        elif start is not None:
            spans.append((unicodedata.normalize('NFC', text[start:i]).casefold(), start, i))
            start = None
    return spans


def concordance(query, target):
    q = [t[0] for t in token_spans(query)]
    ts = token_spans(target)
    hits = []
    if q:
        for i in range(len(ts) - len(q) + 1):
            if [t[0] for t in ts[i:i + len(q)]] == q:
                a, b = ts[i][1], ts[i + len(q) - 1][2]
                hits.append({'start': a, 'end': b, 'text': target[a:b]})
    return {'status': 'unmapped' if not hits else 'unique' if len(hits) == 1 else 'ambiguous', 'matches': hits}


def citations(text):
    return [{'start': m.start(), 'end': m.end(), 'text': m.group(), 'key': re.sub(r'\s', '', m.group())}
            for m in re.finditer(r'\[\s*\d+(?:\s*,\s*\d+)*\s*\]', text)]


def grouped_chars(page):
    chars, height = page['chars'], page['height']
    groups = []
    for direction in ['upright', 'quarter_turn']:
        selected = sorted((c for c in chars if orientation(c) == direction), key=lambda c: (baseline(c, height), c['index']))
        for c in selected:
            if not groups or groups[-1]['orientation'] != direction or baseline(c, height) - groups[-1]['baseline'] > 2:
                groups.append({'orientation': direction, 'baseline': baseline(c, height), 'indices': []})
            groups[-1]['indices'].append(c['index'])
    for c in chars:
        if orientation(c) == 'unknown':
            groups.append({'orientation': 'unknown', 'baseline': baseline(c, height), 'indices': [c['index']]})
    sizes = [median(em(chars[i]) for i in g['indices']) for g in groups]
    candidates = {}
    for i, g in enumerate(groups):
        candidates[i] = [j for j, t in enumerate(groups) if i != j and g['orientation'] == t['orientation'] == 'upright'
                         and sizes[i] <= .8 * sizes[j] and 0 <= t['baseline'] - g['baseline'] <= 6]
    assignments = {}
    for i, options in candidates.items():
        roots = [j for j in options if not candidates[j]]
        if roots:
            assignments[i] = min(roots, key=lambda j: (groups[j]['baseline'] - groups[i]['baseline'], min(groups[j]['indices'])))
    attachments = [{'from_group': i, 'to_group': j, 'char_indices': groups[i]['indices'][:],
                    'from_baseline': groups[i]['baseline'], 'to_baseline': groups[j]['baseline']} for i, j in assignments.items()]
    merged = []
    for i, group in enumerate(groups):
        if i not in assignments:
            indices = group['indices'][:]
            for j, target in assignments.items():
                if target == i:
                    indices.extend(groups[j]['indices'])
            key = (lambda k: (chars[k]['x0'], k)) if group['orientation'] == 'upright' else (
                (lambda k: (-chars[k]['bottom'], k)) if group['orientation'] == 'quarter_turn' else (lambda k: k))
            merged.append(group | {'original_group': i, 'indices': sorted(indices, key=key)})
    merged.sort(key=lambda g: (['upright', 'quarter_turn', 'unknown'].index(g['orientation']), g['baseline'], min(g['indices'])))
    return merged, attachments


def assemble(page, raw, legacy):
    groups, attachments = grouped_chars(page)
    chars = page['chars']
    native = ''.join(c['text'] for c in chars)
    cursor = 0
    for i, c in enumerate(chars):
        assert c['index'] == i and c['native_start'] == cursor
        cursor += len(c['text'])
        assert c['native_end'] == cursor and native[c['native_start']:c['native_end']] == c['text']
    size_counts = Counter(round(em(c), 3) for c in chars if orientation(c) == 'upright' and c['text'].strip())
    mode = max(size_counts, key=lambda s: (size_counts[s], s))
    selected_rule = min(page['raster_rules'], key=lambda r: (r['top'], r['x0'])) if page['raster_rules'] else None
    lines, pieces, fragments = [], [], []
    offset = 0
    for n, group in enumerate(groups):
        indices = group['indices']
        row = [chars[i] for i in indices]
        line_id = page['id'] + f':line:{n:03d}'
        start = offset
        previous = None
        for c in row:
            if previous is not None:
                gap = c['x0'] - previous['x1'] if group['orientation'] == 'upright' else (
                    previous['top'] - c['bottom'] if group['orientation'] == 'quarter_turn' else 0)
                if gap > .15 * min(em(previous), em(c)) and not previous['text'][-1:].isspace() and not c['text'][:1].isspace():
                    pieces.append({'kind': 'inferred_space', 'start': offset, 'end': offset + 1, 'text': ' ', 'line_id': line_id,
                                   'left_char': previous['index'], 'right_char': c['index'], 'gap': round(gap, 6), 'reason': 'geometric_gap'})
                    fragments.append(' '); offset += 1
            pieces.append({'kind': 'glyph', 'start': offset, 'end': offset + len(c['text']), 'text': c['text'], 'line_id': line_id,
                           'char_index': c['index'], 'native_start': c['native_start'], 'native_end': c['native_end']})
            fragments.append(c['text']); offset += len(c['text'])
            previous = c
        text = ''.join(p['text'] for p in pieces if p['line_id'] == line_id)
        top, bottom = min(c['top'] for c in row), max(c['bottom'] for c in row)
        med = median(em(c) for c in row)
        role = 'body_or_unresolved'
        if group['orientation'] == 'quarter_turn': role = 'rotated_margin_candidate'
        elif group['orientation'] == 'unknown': role = 'orientation_unresolved'
        elif re.fullmatch(r'\d{1,4}', text.strip()) and top >= .85 * page['height']: role = 'page_number_candidate'
        elif selected_rule and top > selected_rule['top']: role = 'footnote_candidate' if med <= .95 * mode else 'below_rule_unresolved'
        elif bottom <= .15 * page['height']: role = 'upper_band_candidate'
        lines.append({'line_id': line_id, 'orientation': group['orientation'], 'baseline': group['baseline'],
                      'original_group': group['original_group'], 'char_indices': indices, 'start': start, 'end': offset, 'text': text,
                      'x0': min(c['x0'] for c in row), 'x1': max(c['x1'] for c in row), 'top': top, 'bottom': bottom,
                      'median_em': med, 'role_hint': role, 'raw_page_concordance': concordance(text, raw),
                      'legacy_window_concordance': concordance(text, legacy)})
        pieces.append({'kind': 'line_separator', 'start': offset, 'end': offset + 1, 'text': '\n', 'line_id': line_id, 'reason': 'synthetic_line_ending'})
        fragments.append('\n'); offset += 1
    text = ''.join(fragments)
    seen = [p['char_index'] for p in pieces if p['kind'] == 'glyph']
    assert sorted(seen) == list(range(len(chars)))
    assert ''.join(chars[i]['text'] for i in sorted(seen)) == native
    cursor = 0
    for p in pieces:
        assert p['start'] == cursor and text[p['start']:p['end']] == p['text']
        cursor = p['end']
    assert cursor == len(text)
    return {'page_id': page['id'], 'pdf_page_one_based': page['pdf_page_one_based'], 'native_glyph_text': native,
            'text': text, 'pieces': pieces, 'lines': lines, 'attachments': attachments, 'modal_em': mode,
            'selected_rule': selected_rule, 'raster_rules': page['raster_rules'], 'exact_native_accounting': True, 'exact_derivative_partition': True,
            'raw_numeric_citations': citations(raw), 'derivative_numeric_citations': citations(text)}


def continuities(pages):
    records = []
    for left, right in zip(pages, pages[1:]):
        lrows = [l for l in left['lines'] if l['role_hint'] == 'body_or_unresolved']
        rrows = [l for l in right['lines'] if l['role_hint'] == 'body_or_unresolved']
        l, r = (lrows[-1] if lrows else None), (rrows[0] if rrows else None)
        lm = re.search(r'([^\W\d_]+)-\s*$', l['text']) if l else None
        rm = re.match(r'\s*([^\W\d_]+)', r['text']) if r else None
        candidate = bool(lm and rm and rm.group(1)[0].islower())
        records.append({'left_page': left['pdf_page_one_based'], 'right_page': right['pdf_page_one_based'],
                        'left_line': l, 'right_line': r, 'continuation_candidate': candidate,
                        'left_fragment': lm.group(1) + '-' if lm else None,
                        'right_fragment': rm.group(1) if rm else None, 'joined_text_created': False})
    return records


def engineering_gate(pages, continuity):
    return {'complete_glyph_and_piece_accounting': len(pages) == 3 and all(p['exact_native_accounting'] and p['exact_derivative_partition'] for p in pages),
            'single_rotated_lane': [sum(l['orientation'] == 'quarter_turn' for l in p['lines']) for p in pages] == [1, 0, 0],
            'two_note_regions': len(pages) == 3 and pages[0]['selected_rule'] is None and all(p['selected_rule'] and any(l['role_hint'] == 'footnote_candidate' for l in p['lines']) for p in pages[1:]),
            'unjoined_page_edge': any(r['left_page'] == 2 and r['right_page'] == 3 and r['continuation_candidate'] and r['left_fragment'] == 'as-' and r['right_fragment'] == 'tronomy' for r in continuity)}
