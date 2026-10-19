from collections import Counter
import hashlib
from itertools import product
import unittest
from fl_decipher.scaffold_v46 import controls
from fl_decipher.scaffold_specificity_v47 import decisions, paper_inventory, paper_scope, windows


def rows(values):
    return [{'anchor_index': i, 'kind': 'number', 'key': 'number:' + x, 'unit': i % 2} for i, x in enumerate(values)]


def export(texts):
    return {'source_pdf_sha256': 'fixture', 'pages': [
        {'page': i + 1, 'text': t, 'text_sha256': hashlib.sha256(t.encode()).hexdigest()} for i, t in enumerate(texts)]}


class SpecificityTests(unittest.TestCase):
    def test_page_offsets_empty_pages_and_literal_boundaries(self):
        e = export(['X96 NASA 1.3', '', '40 100,000 100.000'])
        text, units = paper_scope(e, 'fixture', 3)
        inv = paper_inventory(text, units)
        self.assertEqual(text, 'X96 NASA 1.3\n\n40 100,000 100.000')
        self.assertEqual(len(units), 3)
        self.assertEqual([r['value'] for r in inv['anchors']], ['NASA', '1.3', '40', '100,000', '100.000'])
        for r in inv['anchors']:
            self.assertEqual(text[slice(*r['span'])], e['pages'][r['page'] - 1]['text'][slice(*r['page_span'])])
        self.assertEqual(paper_inventory(*paper_scope(export(['X', '96']), 'fixture', 2))['anchors'][0]['value'], '96')

    def test_page_digest_order_material_and_pdf_identity_fail_closed(self):
        for mutation in ['text', 'page', 'pdf', 'material']:
            e = export(['NASA 96'])
            if mutation == 'text': e['pages'][0]['text'] += 'x'
            if mutation == 'page': e['pages'][0]['page'] = 2
            if mutation == 'pdf': e['source_pdf_sha256'] = 'wrong'
            if mutation == 'material': e['material_available'] = False
            with self.assertRaises(ValueError): paper_scope(e, 'fixture', 1)
        with self.assertRaises(ValueError): paper_scope(export(['a']), 'fixture', 2)

    def test_windows_retain_all_ties_and_short_documents_are_unavailable(self):
        result = windows(rows('aa'), rows('aaaa'), 2)
        self.assertEqual(result['window_count'], 3)
        self.assertEqual(result['maximizing_starts'], [0, 1, 2])
        self.assertEqual([r['anchor_indices'] for r in result['windows']], [[0, 1], [1, 2], [2, 3]])
        short = windows(rows('a'), rows('a'), 2)
        self.assertIsNone(short['maximum_lcs']); self.assertEqual(short['window_count'], 0)
        with self.assertRaises(ValueError): windows([], [], 0)

    def test_all_window_lengths_match_brute_force_subsequences(self):
        def subs(s):
            return {tuple(x for i, x in enumerate(s) if bits & (1 << i)) for bits in range(1 << len(s))}
        for target in product('ab', repeat=3):
            for source in product('ab', repeat=5):
                result = windows(rows(target), rows(source), 3)
                expected = [max(map(len, subs(target) & subs(source[i:i + 3]))) for i in range(3)]
                self.assertEqual([w['scores']['ordered_lcs'] for w in result['windows']], expected)
                self.assertEqual(result['maximum_lcs'], max(expected))

    def test_numeric_projection_after_mixed_permutation_and_empty_blocks(self):
        source = rows('121')
        source.insert(1, {'kind': 'upper', 'key': 'upper:NASA', 'unit': 0})
        for i, r in enumerate(source): r['anchor_index'] = i
        cases = controls(source, 3, 'fixture', 16)
        self.assertEqual(len(cases), 34)
        for c in cases:
            ordered = [source[i] for i in c['anchor_order']]
            self.assertEqual(Counter(r['key'] for r in source), Counter(r['key'] for r in ordered))
            scan = windows(rows('12'), ordered, 2)
            self.assertEqual(scan['window_count'], 2)
            expected = [r['anchor_index'] for r in ordered if r['kind'] == 'number']
            self.assertEqual(scan['windows'][0]['anchor_indices'], expected[:2])
            if c['unit_order'] is not None: self.assertIn(2, c['unit_order'])

    def test_strict_comparison_ties_fail_and_invalid_stays_null(self):
        observed = {'whole': {'shared_distinct': 3}, 'window_scan': {'maximum_lcs': 3}}
        cases = [{'family': 'reverse', 'window_scan': {'maximum_lcs': 3}}] * 34
        d = decisions(3, observed, cases, True, 3)
        self.assertFalse(d['publisher_strictly_exceeds']); self.assertFalse(d['within_paper_order_separated'])
        self.assertEqual(d['control_ties'], 34)
        self.assertIsNone(decisions(3, observed, cases, False, 3)['publisher_strictly_exceeds'])
        observed['window_scan']['maximum_lcs'] = None
        self.assertIsNone(decisions(3, observed, [], True, 3)['within_paper_order_separated'])
