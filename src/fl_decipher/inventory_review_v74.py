"""Documentation checks for an explicitly exposed assisted return; no claim admission."""
from .review_handoff_v25 import validate_return

EXPOSURE_ERROR = 'reviewer.independent_of_prior_predictions: true declaration required'
ROW_KEYS = {'clue_id', 'disposition', 'evidence_pair_indices', 'counterexample_indices',
            'candidate_relationship_implication', 'limitations'}


def validate_assisted(value, inventory, manifest, manifest_sha, texts):
    errors = []
    if not isinstance(value, dict) or set(value) != {'review', 'clue_dispositions'}:
        return result(['return: expected exactly review and clue_dispositions'], None)
    review = value['review']
    legacy = validate_return(review, manifest, manifest_sha, texts)
    # Retain the original gate's result. Its independence policy is deliberately
    # stricter than this explicitly exposed documentation workflow.
    errors.extend(e for e in legacy['errors'] if e != EXPOSURE_ERROR)
    if not isinstance(review, dict) or not isinstance(review.get('reviewer'), dict):
        return result(errors + ['reviewer: missing declaration'], legacy)
    if review['reviewer'].get('independent_of_prior_predictions') is not False:
        errors.append('reviewer: assisted prior-annotation exposure requires explicit false')
    if review['reviewer'].get('kind') != 'automated':
        errors.append('reviewer.kind: automated required for this pilot')
    rows = value['clue_dispositions']
    clues = {c['id']: c for c in inventory['clues']}
    if not isinstance(rows, list):
        return result(errors + ['clue_dispositions: expected list'], legacy)
    ids = [r.get('clue_id') for r in rows if isinstance(r, dict)]
    if (not all(isinstance(cid, str) for cid in ids) or len(ids) != len(clues)
            or set(ids) != set(clues) or len(set(ids)) != len(ids)):
        errors.append('clue_dispositions: each frozen clue required exactly once')
    for i, row in enumerate(rows):
        at = f'clue_dispositions[{i}]'
        if not isinstance(row, dict) or set(row) != ROW_KEYS:
            errors.append(at + ': missing or unrecognized fields')
            continue
        if not isinstance(row['clue_id'], str) or row['clue_id'] not in clues:
            errors.append(at + ': unknown clue')
            continue
        if row['disposition'] not in ('supported', 'rejected', 'uncertain'):
            errors.append(at + ': explicit observable disposition required')
        for field in ('candidate_relationship_implication', 'limitations'):
            if not isinstance(row[field], str) or not row[field].strip():
                errors.append(at + '.' + field + ': nonempty explanation required')
        references = 0
        for key, family in [('evidence_pair_indices', 'evidence_pairs'),
                            ('counterexample_indices', 'counterexamples')]:
            indices = row[key]
            pairs = review.get(family)
            if not isinstance(indices, list) or not isinstance(pairs, list):
                errors.append(at + '.' + key + ': expected index list and pair family')
                continue
            for index in indices:
                if type(index) is not int or not 0 <= index < len(pairs):
                    errors.append(at + '.' + key + ': invalid pair index')
                    continue
                pair = pairs[index]
                if not isinstance(pair, dict):
                    errors.append(at + ': invalid cited pair')
                    continue
                for side in ('fl', 'source'):
                    span = pair.get(side + '_span')
                    clue = clues[row['clue_id']][side + '_span']
                    if (not isinstance(span, dict) or type(span.get('start')) is not int
                            or type(span.get('end')) is not int
                            or not span['start'] <= clue['start'] < clue['end'] <= span['end']):
                        errors.append(at + ': cited pair does not enclose clue on ' + side + ' side')
                references += 1
        if references == 0:
            errors.append(at + ': at least one cited paired-span record required')
    return result(errors, legacy)


def result(errors, legacy):
    return {'assisted_documentation_complete': not errors, 'errors': errors,
            'original_independent_return_validation': legacy,
            'source_identity_admitted': False, 'opaque_meanings_admitted': 0,
            'independent_reviews_admitted': 0, 'untouched_test_units_admitted': 0}
