import unittest
from fl_decipher.feasibility_v14 import components, unused_components, eligibility


class ComponentFeasibilityTests(unittest.TestCase):
    def test_companion_work_cannot_escape_exposed_component(self):
        posts = [{'works':['trained','companion']}, {'works':['companion','continuation']}, {'works':['fresh']}]
        self.assertEqual(unused_components(posts, {'trained'}, {}), [['fresh']])

    def test_exposure_alias_keeps_both_related_books_exposed(self):
        posts = [{'works':['vile','exalted']}, {'works':['architecture']}]
        self.assertEqual(unused_components(posts, {'combined_books'}, {'combined_books':['vile','exalted']}), [['architecture']])

    def test_repeated_work_across_posts_is_one_component(self):
        self.assertEqual(components([{'works':['a','b']},{'works':['a']},{'works':['b','c']}]), [['a','b','c']])

    def test_acquisition_cannot_establish_correspondence(self):
        values = dict(component_novel=True, source_prose=True, authority_verified=True,
            edition_verified=True, extraction_reviewed=True, source_scope_matches=True,
            fl_opening_available=True, correspondence_reviewed=False)
        result = eligibility(**values)
        self.assertFalse(result['eligible'])
        self.assertEqual(result['unmet'], ['correspondence_reviewed'])

    def test_missing_evidence_is_not_truthy_metadata(self):
        with self.assertRaises(ValueError):
            eligibility(component_novel=True, source_prose='Open Access', authority_verified=True,
                edition_verified=True, extraction_reviewed=True, source_scope_matches=True,
                fl_opening_available=True, correspondence_reviewed=False)
