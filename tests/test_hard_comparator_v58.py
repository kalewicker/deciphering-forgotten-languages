import unittest
from fl_decipher.hard_comparator_v58 import feasibility, nominate
from fl_decipher.panel_scaffold_v56 import representation


def number(value): return {'kind': 'number', 'key': 'number:' + value}
def rep(values): return {'available': True, 'inventory': {'anchors': [number(v) for v in values]}}
def hit(slug): return f'Antarctic neutrino report (https://physicsworld.com/a/{slug}/)\nref [wordlim: 200]\nANITA neutrinos.\n'


class HardComparatorTests(unittest.TestCase):
    def test_three_distinct_types_are_required_without_duplicate_inflation(self):
        native = {'development_capture_eligible': True, 'unmet': []}; target = [number(x) for x in ['96', '40', '180', '180']]
        failed = feasibility(native, rep(['96', '96', '40', '40']), target, 3)
        self.assertFalse(failed['qualifying_harder_comparator']); self.assertEqual(failed['shared_numeric_key_types'], 2)
        passed = feasibility(native, rep(['96', '40', '180']), target, 3)
        self.assertTrue(passed['qualifying_harder_comparator']); self.assertEqual(passed['shared_numeric_keys'], ['number:96', 'number:40', 'number:180'])

    def test_numeric_overlap_cannot_rescue_native_date_failure(self):
        r = feasibility({'development_capture_eligible': False, 'unmet': ['publication_date_in_window']}, rep(['96', '40', '180']), [number(x) for x in ['96', '40', '180']], 3)
        self.assertTrue(r['meets_numeric_overlap_threshold']); self.assertFalse(r['qualifying_harder_comparator'])
        self.assertEqual(r['unmet'], ['publication_date_in_window'])

    def test_quote_masking_and_literal_punctuation_are_kept(self):
        text = '96 "40" 180 100,000'; scope = {'body_text': text, 'paragraph_runs': [{'unit': 0, 'body_span': [0, len(text)], 'text': text}]}
        r = feasibility({'development_capture_eligible': True, 'unmet': []}, representation(scope), [number(x) for x in ['96', '40', '180', '100.000']], 3)
        self.assertEqual(r['shared_numeric_key_types'], 2); self.assertFalse(r['qualifying_harder_comparator'])

    def test_unavailable_representation_is_retained_as_failure(self):
        native = {'development_capture_eligible': True, 'unmet': []}
        for r in [None, {'available': False, 'inventory': None}]:
            v = feasibility(native, r, [number('96')], 3)
            self.assertIsNone(v['meets_numeric_overlap_threshold']); self.assertFalse(v['qualifying_harder_comparator'])
        with self.assertRaises(ValueError): feasibility(native, rep([]), [], 2)

    def test_search_only_exposure_allowed_captured_excluded_caps_preserved(self):
        captured = 'https://physicsworld.com/a/captured/'; linked = 'https://physicsworld.com/a/linked/'
        prior = {'captured_article_keys': [captured], 'article_exposures': {captured: ['captured'], linked: ['prior_link']}}
        result = nominate([{'error': None, 'response': hit('captured') + hit('linked') + hit('later')},
                           {'error': None, 'response': hit('later') + hit('new')}], prior)
        self.assertEqual([s['nominee']['url'] for s in result['slots']], [linked, 'https://physicsworld.com/a/new/'])
        self.assertEqual(result['slots'][0]['nominee']['prior_exposure_tags'], ['prior_link'])
        self.assertEqual(result['queries'][0]['hits'][0]['decision_reason'], 'previously_captured_url')

    def test_failed_searches_stay_empty_without_substitution(self):
        result = nominate([{'error': 'unavailable', 'response': None}, {'error': None, 'response': {'unsupported': 1}}],
                          {'captured_article_keys': [], 'article_exposures': {}})
        self.assertEqual(result['occupied_slots'], 0); self.assertEqual(len(result['slots']), 2)


if __name__ == '__main__': unittest.main()
