import hashlib
import unittest
from fl_decipher.numeric_glyph_context_v48 import select_occurrences, summarize


def fixture():
    text = '40 NASA 40'
    export = {'pages': [{'page': 1, 'text': text, 'text_sha256': hashlib.sha256(text.encode()).hexdigest(), 'image': 'page.png', 'image_sha256': 'pixels'}]}
    rows = [{'kind': 'number', 'key': 'number:40', 'value': '40', 'anchor_index': i, 'unit': 0, 'page': 1,
             'span': span, 'page_span': span} for i, span in enumerate([[0, 2], [8, 10]])]
    inv = {'units': [{'unit': 0, 'page': 1, 'span': [0, len(text)]}], 'inventory': {'anchors': rows}}
    return rows[:1], inv, export


def reviews(selection):
    return [{'occurrence_id': s['occurrence_id'], 'image_sha256': s['image_sha256'], 'glyph_status': 'literal_match',
             'visible_literal': s['value'], 'context': 'prose', 'locator': 'left column', 'context_detail': 'inline citation marker', 'note': 'Digits agree.'} for s in selection]


class NumericGlyphContextTests(unittest.TestCase):
    def select(self):
        return select_occurrences('fixture', *fixture(), {'page.png': 'pixels'}, 120)

    def test_exhaustive_repeats_stable_ids_and_clipped_context(self):
        s = self.select()
        self.assertEqual([r['occurrence_id'] for r in s], ['fixture:0', 'fixture:1'])
        self.assertEqual([r['context_span'] for r in s], [[0, 10], [0, 10]])
        self.assertEqual([r['page_span'] for r in s], [[0, 2], [8, 10]])

    def test_text_image_page_and_global_span_identity_fail_closed(self):
        for kind in ['text', 'image', 'span', 'page']:
            target, inv, export = fixture()
            if kind == 'text': export['pages'][0]['text'] = '41 NASA 40'
            if kind == 'image': export['pages'][0]['image_sha256'] = 'changed'
            if kind == 'span': inv['inventory']['anchors'][0]['span'] = [1, 3]
            if kind == 'page': inv['units'][0]['page'] = 2
            with self.assertRaises(ValueError): select_occurrences('fixture', target, inv, export, {'page.png': 'pixels'}, 120)

    def test_review_coverage_rejects_omission_duplicates_and_new_ids(self):
        s = self.select(); rs = reviews(s)
        for bad in [rs[:1], [rs[0], rs[0]], rs + rs[:1]]:
            with self.assertRaises(ValueError): summarize(s, bad)
        rs[0]['occurrence_id'] = 'new'
        with self.assertRaises(ValueError): summarize(s, rs)

    def test_mismatch_is_retained_and_overrides_uncertainty(self):
        s = self.select(); rs = reviews(s)
        rs[0].update(glyph_status='serialization_mismatch', visible_literal='4.0')
        rs[1].update(glyph_status='unreadable', visible_literal=None)
        result = summarize(s, rs)
        self.assertFalse(result['literal_glyph_agreement_gate'])
        self.assertEqual(result['occurrence_denominator'], 2)
        self.assertEqual(result['glyph_status_counts']['serialization_mismatch'], 1)

    def test_ambiguous_and_unreadable_stay_null_and_context_is_separate(self):
        s = self.select(); rs = reviews(s)
        rs[0].update(glyph_status='ambiguous', visible_literal=None)
        self.assertIsNone(summarize(s, rs)['literal_glyph_agreement_gate'])
        rs[0].update(glyph_status='unreadable', visible_literal=None)
        self.assertIsNone(summarize(s, rs)['literal_glyph_agreement_gate'])
        rs = reviews(s); rs[0]['context'] = 'ambiguous'
        self.assertTrue(summarize(s, rs)['literal_glyph_agreement_gate'])
        self.assertFalse(summarize(s, rs)['all_contexts_resolved'])

    def test_contradictory_or_untraceable_review_is_rejected(self):
        s = self.select()
        for key, value in [('visible_literal', '41'), ('image_sha256', 'changed'), ('context', 'meaning'), ('locator', '')]:
            rs = reviews(s); rs[0][key] = value
            with self.assertRaises(ValueError): summarize(s, rs)
        rs = reviews(s); rs[0]['glyph_status'] = 'serialization_mismatch'
        with self.assertRaises(ValueError): summarize(s, rs)
