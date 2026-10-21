import copy
import unittest

from fl_decipher.inventory_review_v74 import validate_assisted, EXPOSURE_ERROR
from fl_decipher.review_handoff_v25 import sha, template


class AssistedReviewTests(unittest.TestCase):
    def setUp(self):
        self.texts = {'fl': '😀 alpha beta gamma\n', 'source': 'delta epsilon zeta\n'}
        self.manifest = {'nominee_id': 'fixture', 'members': {
            'fl_post.txt': {'sha256': sha(self.texts['fl'].encode())},
            'publisher_window.txt': {'sha256': sha(self.texts['source'].encode())}}}
        self.manifest_sha = 'a' * 64
        def span(side, word):
            text = self.texts[side]
            start = text.index(word)
            return {'start': start, 'end': start + len(word), 'text': word}
        self.inventory = {'clues': [
            {'id': 'C1', 'fl_span': span('fl', 'alpha'), 'source_span': span('source', 'delta')},
            {'id': 'C2', 'fl_span': span('fl', 'beta'), 'source_span': span('source', 'epsilon')}]}
        review = template('fixture', self.manifest_sha)
        review.update({'reviewer': {'name': 'Fixture', 'kind': 'automated', 'identifier': 'fixture-run',
            'independent_of_prior_predictions': False, 'prior_exposure': 'Supplied clue inventory.'},
            'review_completed': True, 'completed_at_utc': '2026-10-21T00:00:00+00:00',
            'statement_boundaries_checked': True, 'language_observations': [
                {'fl_span': span('fl', 'alpha'), 'language': 'unknown', 'certainty': 'unknown',
                 'notes': 'No interpretation is known.'}],
            'evidence_pairs': [{'fl_span': c['fl_span'], 'source_span': c['source_span'],
                 'basis': 'other', 'relationship': 'uncertain', 'notes': 'Fixture only.'}
                 for c in self.inventory['clues']],
            'uncertainty_notes': ['No semantic inference.']})
        self.value = {'review': review, 'clue_dispositions': [
            {'clue_id': c['id'], 'disposition': 'uncertain', 'evidence_pair_indices': [i],
             'counterexample_indices': [], 'candidate_relationship_implication': 'Unestablished.',
             'limitations': 'Only observable fixture spans.'} for i, c in enumerate(self.inventory['clues'])]}

    def check(self, value=None):
        return validate_assisted(value or self.value, self.inventory, self.manifest, self.manifest_sha, self.texts)

    def test_uncertain_assisted_completion_keeps_original_independence_gate_failed(self):
        result = self.check()
        self.assertTrue(result['assisted_documentation_complete'])
        self.assertEqual(result['original_independent_return_validation']['errors'], [EXPOSURE_ERROR])
        self.assertFalse(result['original_independent_return_validation']['structurally_valid'])
        self.assertFalse(result['source_identity_admitted'])
        self.assertEqual(result['independent_reviews_admitted'], 0)

    def test_missing_and_duplicate_clues_fail(self):
        for rows in [self.value['clue_dispositions'][:1], [self.value['clue_dispositions'][0]] * 2]:
            value = copy.deepcopy(self.value)
            value['clue_dispositions'] = rows
            self.assertFalse(self.check(value)['assisted_documentation_complete'])
        value = copy.deepcopy(self.value)
        value['clue_dispositions'][0]['clue_id'] = []
        self.assertFalse(self.check(value)['assisted_documentation_complete'])

    def test_exposure_cannot_be_changed_to_pass_old_gate(self):
        value = copy.deepcopy(self.value)
        value['review']['reviewer']['independent_of_prior_predictions'] = True
        result = self.check(value)
        self.assertTrue(result['original_independent_return_validation']['structurally_valid'])
        self.assertFalse(result['assisted_documentation_complete'])

    def test_wrong_clue_reference_and_bool_index_fail(self):
        for indices in [[1], [True], [], [-1], [99]]:
            value = copy.deepcopy(self.value)
            value['clue_dispositions'][0]['evidence_pair_indices'] = indices
            self.assertFalse(self.check(value)['assisted_documentation_complete'])

    def test_unicode_offset_error_is_not_hidden_by_assisted_policy(self):
        value = copy.deepcopy(self.value)
        value['review']['evidence_pairs'][0]['fl_span']['start'] += 1
        self.assertFalse(self.check(value)['assisted_documentation_complete'])

    def test_uncited_claim_fields_and_invalid_disposition_fail(self):
        for key, replacement in [('disposition', 'accepted'), ('limitations', ''),
                                 ('candidate_relationship_implication', None)]:
            value = copy.deepcopy(self.value)
            value['clue_dispositions'][0][key] = replacement
            self.assertFalse(self.check(value)['assisted_documentation_complete'])
        value = copy.deepcopy(self.value)
        value['semantic_acceptance'] = True
        self.assertFalse(self.check(value)['assisted_documentation_complete'])


if __name__ == '__main__':
    unittest.main()
