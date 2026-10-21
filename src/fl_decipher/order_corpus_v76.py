"""Fixed corpus capacity accounting; no language model or semantic labels."""
import unicodedata as ud
from collections import defaultdict


def tokens(text):
    result = []
    start = None
    for i, char in enumerate(text + '\0'):
        category = ud.category(char)[0]
        if start is None:
            if category == 'L':
                start = i
        elif category not in ('L', 'M'):
            raw = text[start:i]
            result.append({'start': start, 'end': i,
                           'form': ud.normalize('NFC', raw).casefold(),
                           'numeric_neighbor': (start > 0 and text[start-1].isdigit()) or
                                               (i < len(text) and text[i].isdigit())})
            start = None
    return result


def annotate(text, mask):
    ts = tokens(text)
    for i, token in enumerate(ts):
        token['blocked'] = token['numeric_neighbor'] or token['form'] in mask
        token['pair_from_previous'] = bool(i and not token['blocked'] and
            not ts[i-1]['blocked'] and text[ts[i-1]['end']:token['start']].isspace())
    return ts


def group_candidates(candidates, group_ids):
    parent = {g: g for g in group_ids}

    def root(g):
        while parent[g] != g:
            g = parent[g]
        return g

    windows = defaultdict(list)
    for row in candidates:
        forms = [t['form'] for t in row['tokens']]
        for i in range(len(forms)-7):
            windows[tuple(forms[i:i+8])].append((row['uid'], row['base_group'], i))
    witnesses = []
    for forms, hits in sorted(windows.items()):
        groups = sorted({h[1] for h in hits})
        if len(groups) < 2:
            continue
        witnesses.append({'forms': list(forms), 'occurrences': [list(h) for h in hits]})
        for g in groups[1:]:
            a, b = sorted([root(groups[0]), root(g)])
            parent[b] = a
    return {g: root(g) for g in group_ids}, witnesses


def account(candidates, group_ids):
    mapping, witnesses = group_candidates(candidates, group_ids)
    seen = {}
    occupied = defaultdict(list)
    for row in sorted(candidates, key=lambda r: r['uid']):
        row['group'] = mapping[row['base_group']]
        forms = tuple(t['form'] for t in row['tokens'])
        if forms in seen:
            row['exclusion'] = 'duplicate_sequence'
            row['duplicate_of'] = seen[forms]
            continue
        seen[forms] = row['uid']
        conflicts = sorted({uid for b in row['bindings']
            for start, end, uid in occupied[b['document_id']]
            if b['start'] < end and start < b['end']})
        if conflicts:
            row['exclusion'] = 'overlapping_saved_span'
            row['overlaps'] = conflicts
            continue
        row['exclusion'] = None
        for b in row['bindings']:
            occupied[b['document_id']].append((b['start'], b['end'], row['uid']))
    groups = []
    for g in sorted(set(mapping.values())):
        kept = [r for r in candidates if r['group'] == g and r['exclusion'] is None]
        pairs = sum(sum(t['pair_from_previous'] for t in r['tokens']) for r in kept)
        groups.append({'group': g, 'base_groups': sorted(k for k, v in mapping.items() if v == g),
                       'retained_units': len(kept),
                       'unmasked_tokens': sum(sum(not t['blocked'] for t in r['tokens']) for r in kept),
                       'pairs': pairs, 'eligible': pairs >= 100 and len(kept) >= 2})
    eligible = [g for g in groups if g['eligible']]
    folds = [{'evaluation_group': g['group'], 'evaluation_pairs': g['pairs'],
              'training_groups': [h['group'] for h in eligible if h != g],
              'training_pairs': sum(h['pairs'] for h in eligible if h != g)} for g in eligible]
    return {'groups': groups, 'folds': folds, 'duplicate_witnesses': witnesses,
            'capacity_pass': len(eligible) >= 4 and all(f['training_pairs'] >= 500 for f in folds)}
