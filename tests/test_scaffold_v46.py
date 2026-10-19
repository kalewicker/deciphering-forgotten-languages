from itertools import product
import unittest
from fl_decipher.scaffold_v46 import anchors, controls, lcs, merged, metrics, quote_masks, residuals, source_units


class ScaffoldTests(unittest.TestCase):
    def test_masks_preserve_original_boundaries_and_remove_quoted_anchors(self):
        text = 'ANITA 96 "NASA 40" X96 100.000 100,000 4σ .3'
        result = anchors(text, [{'unit': 0, 'span': [0, len(text)]}], quote_masks(text))
        self.assertEqual([r['value'] for r in result['anchors']], ['ANITA', '96', '100.000', '100,000'])
        self.assertEqual(merged([[2, 4], [0, 2]], 8), [[0, 4]])
        self.assertEqual(residuals([[0, 4]], 8), [[4, 8]])
        # Masking part of an identifier cannot create a standalone number.
        self.assertEqual(anchors('X96', [{'unit': 0, 'span': [0, 3]}], [[0, 1]])['anchors'], [])

    def test_lcs_matches_exhaustive_subsequences_including_repeated_keys(self):
        def subs(values):
            return {tuple(x for i, x in enumerate(values) if mask & (1 << i)) for mask in range(1 << len(values))}
        for left in product('ab', repeat=4):
            for right in product('ab', repeat=4):
                self.assertEqual(lcs(left, right), max(map(len, subs(left) & subs(right))))

    def test_bag_preserving_controls_keep_all_draws_and_zero_anchor_units(self):
        rows = [{'anchor_index': i, 'unit': i // 2, 'key': 'upper:ANITA', 'kind': 'upper'} for i in range(4)]
        cases = controls(rows, 3, 'fixture', 16)
        self.assertEqual(len(cases), 34)
        for c in cases:
            self.assertEqual(sorted(c['anchor_order']), list(range(4)))
            self.assertTrue(c['key_identity'])
            if c['unit_order'] is not None:
                self.assertEqual(sorted(c['unit_order']), list(range(3)))
        self.assertEqual(cases, controls(rows, 3, 'fixture', 16))

    def test_source_scope_is_structural_and_ambiguous_mapping_fails(self):
        raw = b'<html><body><article id="p"><div class="entry-content"><p>ANITA 96</p><form><p>NASA 40</p></form></div></article></body></html>'
        body = 'ANITA 96 NASA 40'
        units, masks = source_units(raw, body, 'article#p > div.entry-content')
        self.assertEqual(len(units), 1); self.assertEqual(masks, [])
        bad = raw.replace(b'NASA 40', b'ANITA 96')
        with self.assertRaisesRegex(ValueError, 'ambiguous'):
            source_units(bad, 'ANITA 96 ANITA 96', 'article#p > div.entry-content')

    def test_order_length_cannot_exceed_bag_capacity_or_invent_an_alignment(self):
        a = [{'key': 'number:' + x, 'kind': 'number'} for x in ['1', '2', '3']]
        r = metrics(a, list(reversed(a)))
        self.assertEqual(r['number']['bag_capacity'], 3)
        self.assertEqual(r['number']['ordered_lcs'], 1)
        self.assertEqual(r['upper']['ordered_lcs'], 0)
        with self.assertRaises(ValueError):
            quote_masks('“unclosed NASA 96')
