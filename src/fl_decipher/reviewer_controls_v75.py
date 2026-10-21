"""Known-truth literal predicates and complete-denominator assessment; no semantics."""
from hashlib import sha256
import re
import unicodedata


def normalized(text):
    return ' '.join(unicodedata.normalize('NFC', text).casefold().split())


def ordered_anchors(text, anchors):
    view = normalized(text)
    cursor, chain = 0, []
    for anchor in anchors:
        needle = normalized(anchor)
        if not needle:
            return False, chain
        matches = re.finditer(r'(?<!\w)' + re.escape(needle) + r'(?!\w)', view)
        match = next((m for m in matches if m.start() >= cursor), None)
        if match is None:
            return False, chain
        chain.append([match.start(), match.end()])
        cursor = match.end()
    return True, chain


def cases_from_appendix(appendix):
    rows = {r['id']: r for r in appendix['pairs'] if r['packet'] == 'western_esoterism'}
    names = ['Giovanni Pico della Mirandola', 'Marselio Ficino', 'Posidonius']
    specs = [
        ('expression', 'W1', 'W1', ['fatum/providentia']),
        ('names_order', 'W2', 'W2', names),
        ('name_case', 'W4', 'W4', ['zazel']),
        ('wrong_source_label', 'W3', 'W5', ['Daemonium Saturni']),
        ('reversed_names', 'W2', 'W2', list(reversed(names))),
    ]
    specs.sort(key=lambda x: sha256(('v75-review-controls-fixed|' + x[0]).encode()).digest())
    public, oracle = [], []
    for i, (tag, fl_id, source_id, anchors) in enumerate(specs, 1):
        row = {'case_id': f'C{i:02}', 'fl_span': rows[fl_id]['fl_span'],
               'source_span': rows[source_id]['source_span'], 'anchors': anchors}
        truth = [ordered_anchors(row[side + '_span']['text'], anchors) for side in ['fl', 'source']]
        public.append(row)
        oracle.append({'case_id': row['case_id'], 'construction': tag,
                       'expected': 'supported' if all(t[0] for t in truth) else 'rejected',
                       'normalized_matching_witnesses': [t[1] for t in truth]})
    assert sum(o['expected'] == 'supported' for o in oracle) == 3
    return public, oracle


def assess(value, cases, oracle, texts, expected_id):
    errors = []
    judgments = value.get('judgments', []) if isinstance(value, dict) else []
    if not isinstance(value, dict) or set(value) != {'reviewer', 'completed_at_utc', 'review_completed', 'judgments', 'limitations'}:
        errors.append('return: missing or unrecognized fields')
    reviewer = value.get('reviewer', {}) if isinstance(value, dict) else {}
    if (not isinstance(reviewer, dict) or set(reviewer) != {'name', 'kind', 'identifier', 'prior_exposure'}
            or reviewer.get('kind') != 'automated' or reviewer.get('identifier') != expected_id
            or not all(isinstance(reviewer.get(k), str) and reviewer[k].strip() for k in ['name', 'prior_exposure'])):
        errors.append('reviewer: explicit automated identity/exposure required')
    if not isinstance(judgments, list):
        errors.append('judgments: list required')
        judgments = []
    ids = [j.get('case_id') for j in judgments if isinstance(j, dict)]
    wanted = [c['case_id'] for c in cases]
    if (not all(isinstance(i, str) for i in ids) or len(ids) != len(wanted)
            or len(set(ids)) != len(ids) or set(ids) != set(wanted)):
        errors.append('judgments: each case ID required exactly once')
    case_map = {c['case_id']: c for c in cases}
    by_id = {}
    for j in judgments:
        if not isinstance(j, dict) or set(j) != {'case_id', 'disposition', 'fl_span', 'source_span', 'explanation'}:
            errors.append('judgment: missing or unrecognized fields')
            continue
        cid = j['case_id']
        if not isinstance(cid, str) or cid not in case_map:
            errors.append('judgment: unknown case ID')
            continue
        if j['disposition'] not in ('supported', 'rejected', 'uncertain'):
            errors.append(cid + ': invalid disposition')
        if not isinstance(j['explanation'], str) or not j['explanation'].strip():
            errors.append(cid + ': explanation required')
        for side in ['fl', 'source']:
            s = j[side + '_span']
            if (not isinstance(s, dict) or set(s) != {'start', 'end', 'text'}
                    or type(s.get('start')) is not int or type(s.get('end')) is not int
                    or not 0 <= s['start'] < s['end'] <= len(texts[side])
                    or texts[side][s['start']:s['end']] != s.get('text')
                    or s != case_map[cid][side + '_span']):
                errors.append(cid + ': exact input ' + side + ' span required')
        by_id[cid] = j
    from datetime import datetime
    try:
        stamp = datetime.fromisoformat(value.get('completed_at_utc'))
        assert stamp.tzinfo is not None and stamp.utcoffset().total_seconds() == 0
    except (AttributeError, TypeError, ValueError, AssertionError):
        errors.append('completed_at_utc: explicit UTC required')
    if not isinstance(value, dict) or value.get('review_completed') is not True:
        errors.append('review_completed: completed return required')
    notes = value.get('limitations') if isinstance(value, dict) else None
    if not isinstance(notes, list) or not notes or not all(isinstance(n, str) and n.strip() for n in notes):
        errors.append('limitations: nonempty list required')
    ledger = [{'case_id': o['case_id'], 'expected': o['expected'],
               'observed': by_id.get(o['case_id'], {}).get('disposition'),
               'correct': by_id.get(o['case_id'], {}).get('disposition') == o['expected']} for o in oracle]
    genuine = [r for r in ledger if r['expected'] == 'supported']
    false = [r for r in ledger if r['expected'] == 'rejected']
    return {'schema_and_quotes_complete': not errors, 'errors': errors,
            'case_denominator': len(cases), 'genuine_denominator': len(genuine), 'false_denominator': len(false),
            'genuine_supported': sum(r['correct'] for r in genuine),
            'false_rejected': sum(r['correct'] for r in false),
            'false_supported': sum(r['observed'] == 'supported' for r in false),
            'uncertain_or_missing': sum(r['observed'] in ('uncertain', None) for r in ledger),
            'literal_control_gate': not errors and all(r['correct'] for r in ledger),
            'ledger': ledger}
