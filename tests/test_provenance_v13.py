import unittest
from fl_decipher.provenance_v13 import provenance_gate


class ProvenanceGates(unittest.TestCase):
    def setUp(self):
        self.evidence = dict(source_prose=True, authority_verified=True, edition_verified=True,
            source_scope_matches=True, extraction_reviewed=True, passage_reviewed=True, component_novel=True)

    def test_wrong_section_with_verified_authority_stays_ineligible(self):
        self.evidence['source_scope_matches'] = False
        result = provenance_gate(**self.evidence)
        self.assertFalse(result['eligible'])
        self.assertEqual(result['unmet'], ['source_scope_matches'])

    def test_wrong_edition_with_matching_text_stays_ineligible(self):
        self.evidence['edition_verified'] = False
        self.assertFalse(provenance_gate(**self.evidence)['eligible'])

    def test_unknown_authority_with_matching_passage_stays_ineligible(self):
        self.evidence['authority_verified'] = False
        self.assertFalse(provenance_gate(**self.evidence)['eligible'])

    def test_missing_prose_is_not_a_catalogue_success(self):
        self.evidence['source_prose'] = False
        self.assertFalse(provenance_gate(**self.evidence)['eligible'])

    def test_all_gates_must_pass(self):
        for key in self.evidence:
            with self.subTest(key=key):
                failed = self.evidence | {key:False}
                self.assertEqual(provenance_gate(**failed)['unmet'], [key])
        self.assertTrue(provenance_gate(**self.evidence)['eligible'])

    def test_truthy_strings_are_not_evidence(self):
        self.evidence['source_prose'] = 'false'
        with self.assertRaises(ValueError):
            provenance_gate(**self.evidence)
