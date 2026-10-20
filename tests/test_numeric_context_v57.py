import unittest
from fl_decipher.numeric_context_v57 import occurrences, literal_cues, summarize


class NumericContextTests(unittest.TestCase):
    def test_repeated_keys_include_masked_outside_and_boundary_occurrences(self):
        text = '40 40 X40 40'; units = [{'unit': 0, 'span': [0, 8]}]
        inv = [{'kind': 'number', 'key': 'number:40', 'value': '40', 'span': [0, 2], 'anchor_index': 0}]
        rows = occurrences(text, 'target', ['number:40'], units, [{'reason': 'quote', 'span': [3, 5]}], inv, 120, 64)
        self.assertEqual([r['status'] for r in rows], ['retained', 'masked', 'boundary_rejected', 'outside_selected_scope'])
        self.assertEqual(len({r['occurrence_id'] for r in rows}), 4)
        self.assertTrue(all(text[slice(*r['context_span'])] == r['context_text'] for r in rows))

    def test_full_candidate_spelling_prevents_substring_and_decimal_rescue(self):
        rows = occurrences('140 40.0 .40', 'source', ['number:40'], [], [], [], 5, 64)
        self.assertEqual(len(rows), 1); self.assertTrue(rows[0]['boundary_rejected'])

    def test_unit_and_range_markers_are_literal_and_clipped_to_original_unit(self):
        text = '180- 1200 MHz'; cues = literal_cues(text, [0, 3], len(text), 64)
        self.assertEqual(cues['numeric_range_surface']['text'], text)
        self.assertEqual(cues['numeric_range_surface']['unit']['text'], 'MHz')
        self.assertIsNone(literal_cues('40 km', [0, 2], 2, 64)['direct_unit_marker'])
        self.assertIsNone(literal_cues('1.3 million cubic kilometres', [0, 3], 28, 64)['direct_unit_marker'])
        self.assertEqual(literal_cues('180°', [0, 3], 4, 64)['direct_unit_marker']['text'], '°')

    def test_stale_or_missing_retained_inventory_fails(self):
        with self.assertRaises(ValueError): occurrences('40', 'source', ['number:40'], [{'unit': 0, 'span': [0, 2]}], [], [], 120, 64)

    def fixture(self):
        text = '40 km'
        inv = [{'kind': 'number', 'key': 'number:40', 'value': '40', 'span': [0, 2], 'anchor_index': 0}]
        rows = occurrences(text, 'target', ['number:40'], [{'unit': 0, 'span': [0, 5]}], [], inv, 120, 64)
        review = {'occurrence_id': rows[0]['occurrence_id'], 'glyph_status': 'not_visually_checked', 'quantity_correspondence': 'unresolved',
            'opaque_meaning_admitted': False, 'context_class': 'opaque_context_unresolved', 'evidence': [{'span': [3, 5], 'text': 'km'}], 'note': 'Literal marker only.'}
        return rows, review, {'target': text, 'source': ''}

    def test_review_requires_complete_exact_evidence_and_no_semantic_promotion(self):
        rows, review, texts = self.fixture(); result = summarize(rows, [review], texts)
        self.assertIsNone(result['quantity_correspondence_gate']); self.assertEqual(result['source_target_pairs_selected'], 0)
        for change in [{'context_class': 'distance_or_length'}, {'glyph_status': 'literal_match'}, {'quantity_correspondence': 'verified'},
                       {'opaque_meaning_admitted': True}, {'evidence': [{'span': [3, 5], 'text': 'm'}]}]:
            with self.assertRaises(ValueError): summarize(rows, [review | change], texts)
        with self.assertRaises(ValueError): summarize(rows, [], texts)

    def test_same_key_with_multiple_unit_markers_does_not_select_a_pair(self):
        text = '180° 180-1200 MHz'
        inv = [{'kind': 'number', 'key': 'number:180', 'value': '180', 'span': span, 'anchor_index': i} for i, span in enumerate([[0, 3], [5, 8]])]
        rows = occurrences(text, 'target', ['number:180'], [{'unit': 0, 'span': [0, len(text)]}], [], inv, 120, 64)
        reviews = [{'occurrence_id': r['occurrence_id'], 'glyph_status': 'not_visually_checked', 'quantity_correspondence': 'unresolved',
            'opaque_meaning_admitted': False, 'context_class': 'opaque_context_unresolved', 'evidence': [{'span': r['span'], 'text': '180'}], 'note': 'No pair selected.'} for r in rows]
        result = summarize(rows, reviews, {'target': text, 'source': ''})
        self.assertEqual(result['by_key'][0]['target']['literal_unit_markers'], ['MHz', '°'])
        self.assertEqual(result['source_target_pairs_selected'], 0)


if __name__ == '__main__': unittest.main()
