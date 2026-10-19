import unittest
from fl_decipher.citation_sensitivity_v49 import citation_masks, filter_controls, filter_inventory
from fl_decipher.scaffold_v46 import anchors, controls
from fl_decipher.scaffold_specificity_v47 import windows


def scope(pages):
    units = []; at = 0
    for i, text in enumerate(pages):
        units.append({'unit': i, 'page': i + 1, 'span': [at, at + len(text)]}); at += len(text) + 1
    return '\n'.join(pages), units


class CitationSensitivityTests(unittest.TestCase):
    def test_full_reference_tail_and_every_supported_numeric_bracket(self):
        text, units = scope(['96 [1] [2, 3] [4–6] [7−8] [9-10] [11; 12]\nReferences\n[1] 2007', '[2] 2006'])
        at = text.index('References')
        result = citation_masks(text, units, {'page': 1, 'page_offset': at, 'needle': 'References\n'})
        self.assertEqual(result['reference_start'], at)
        self.assertEqual(len([r for r in result['ledger'] if r['reason'] == 'inline_numeric_bracket']), 6)
        self.assertEqual(len(result['bracket_candidates']), 8)
        self.assertEqual(result['masks'][-1], [at, len(text)])

    def test_page_breaks_and_unsupported_forms_are_not_repaired(self):
        text, us = scope(['[1.3] [NASA] [1,', '2] [ 3,\n4 ] References'])
        offset = text[us[1]['span'][0]:].index('References')
        result = citation_masks(text, us, {'page': 2, 'page_offset': offset, 'needle': 'References'})
        self.assertEqual([r['text'] for r in result['bracket_candidates']], ['[ 3,\n4 ]'])

    def test_exact_boundary_identity_and_original_index_validation(self):
        text, us = scope(['References References'])
        with self.assertRaises(ValueError): citation_masks(text, us, {'page': 1, 'page_offset': 0, 'needle': 'References'})
        with self.assertRaises(ValueError): citation_masks(text, us, {'page': 2, 'page_offset': 0, 'needle': 'References'})
        with self.assertRaises(ValueError): filter_inventory([{'anchor_index': 4}], [])

    def test_filtering_keeps_original_spans_without_creating_identifier_anchors(self):
        text = 'X96 [40] 1.3 NASA 100.000'
        rows = anchors(text, [{'unit': 0, 'span': [0, len(text)]}], [])['anchors']
        inv = filter_inventory(rows, [[0, 1], [4, 8]])
        self.assertEqual([r['value'] for r in inv['anchors']], ['1.3', 'NASA', '100.000'])
        self.assertEqual([r['original_anchor_index'] for r in inv['anchors']], [1, 2, 3])
        self.assertEqual([r['anchor_index'] for r in inv['anchors']], [0, 1, 2])
        self.assertEqual([r['value'] for r in inv['removed_anchors']], ['40'])

    def test_all_original_control_draws_are_filtered_not_regenerated(self):
        original = [{'anchor_index': i, 'unit': i // 2, 'span': [i * 2, i * 2 + 1], 'kind': 'number', 'key': str(i)} for i in range(6)]
        parents = controls(original, 4, 'fixture', 16)
        retained = filter_inventory(original, [[2, 9]])['anchors']
        filtered = filter_controls(original, retained, parents)
        mapping = {r['original_anchor_index']: r['anchor_index'] for r in retained}
        self.assertEqual(len(filtered), 34)
        for index, (c, p) in enumerate(zip(filtered, parents)):
            self.assertEqual(c['parent_control_index'], index)
            self.assertEqual(c['anchor_order'], [mapping[i] for i in p['anchor_order'] if i in mapping])
            self.assertEqual(c['unit_order'], p['unit_order'])
            self.assertTrue(c['bag_preserved'] and c['index_inventory_preserved'])
        reduced_draws = controls(retained, 4, 'fixture', 16)
        self.assertTrue(any(c['anchor_order'] != p['anchor_order'] for c, p in zip(filtered, reduced_draws)))

    def test_identity_and_duplicate_draws_are_retained_after_emptying_pages(self):
        original = [{'anchor_index': i, 'unit': i, 'span': [i * 2, i * 2 + 1], 'kind': 'number', 'key': 'number:1'} for i in range(3)]
        retained = filter_inventory(original, [[2, 5]])['anchors']
        cases = filter_controls(original, retained, controls(original, 4, 'fixture', 16))
        self.assertEqual(len(cases), 34)
        self.assertTrue(all(c['index_identity'] and c['key_identity'] for c in cases))
        self.assertTrue(all(c['unit_order'] is None or sorted(c['unit_order']) == [0, 1, 2, 3] for c in cases))

    def test_removed_nonmatching_anchors_can_increase_best_window_score(self):
        values = ['1', '9', '9', '2']
        source = [{'kind': 'number', 'key': 'number:' + x, 'anchor_index': i, 'span': [i, i + 1]} for i, x in enumerate(values)]
        target = [source[0], source[3]]
        self.assertEqual(windows(target, source, 2)['maximum_lcs'], 1)
        reduced = filter_inventory(source, [[1, 3]])['anchors']
        self.assertEqual(windows(target, reduced, 2)['maximum_lcs'], 2)
