import unittest
from fl_decipher.exact_fragments_v44 import audit, token_rows


class ExactFragmentTests(unittest.TestCase):
    def test_ties_and_repeated_occurrences_do_not_inflate_coverage(self):
        r = audit('a b c Z a b c', 'q a b c r a b c s', 3)
        self.assertEqual(r['qualifying_run_count'], 4)
        self.assertEqual(r['longest_run_tokens'], 3)
        self.assertEqual(r['covered_query_tokens'], 6)
        self.assertEqual(r['covered_query_token_indices'], [0, 1, 2, 4, 5, 6])

    def test_overlaps_and_threshold_boundary_are_retained(self):
        r = audit('a a a', 'a a a a', 2)
        self.assertEqual([x['token_count'] for x in r['runs']], [3, 3, 2, 2])
        self.assertEqual(r['covered_query_tokens'], 3)
        self.assertFalse(audit('a b c', 'a b c', 4)['qualifying_overlap_present'])

    def test_no_gap_punctuation_or_apostrophe_repair(self):
        self.assertFalse(audit("don't stop now", 'don’t stop now', 3)['qualifying_overlap_present'])
        self.assertFalse(audit('red blue green', 'red inserted blue green', 3)['qualifying_overlap_present'])
        self.assertFalse(audit('red blue green.', 'red blue green', 3)['qualifying_overlap_present'])
        self.assertEqual(audit('red blue green', 'green blue red', 3)['longest_run_tokens'], 1)

    def test_unicode_normalization_preserves_raw_witness_coordinates(self):
        query = 'e\u0301 Straße'; source = 'X É\tSTRASSE Y'
        r = audit(query, source, 2, target_offset=17)
        run = r['runs'][0]
        self.assertEqual(run['query_fragment'], query[slice(*run['query_char_span'])])
        self.assertEqual(run['source_fragment'], source[slice(*run['source_char_span'])])
        self.assertEqual(run['target_char_span'], [17, 17 + len(query)])
        self.assertEqual(run['normalized_tokens'], ['é', 'strasse'])

    def test_unavailable_is_not_absent_and_empty_query_stays_empty(self):
        r = audit('a b c', None, 2)
        self.assertFalse(r['available'])
        self.assertIsNone(r['qualifying_overlap_present'])
        self.assertIsNone(r['runs'])
        self.assertEqual(audit('', 'a b c', 2)['longest_run_tokens'], 0)
        self.assertEqual(token_rows('  a\tb '), [{'normalized': 'a', 'span': [2, 3]}, {'normalized': 'b', 'span': [4, 5]}])
