import unittest
from fl_decipher.panel_scaffold_v56 import representation, capped_scan, assessment, panel_decision


def rows(values):
    return [{'anchor_index': i, 'key': 'number:' + v, 'kind': 'number', 'value': v, 'unit': 0, 'span': [i * 2, i * 2 + 1]} for i, v in enumerate(values)]


class PanelScaffoldTests(unittest.TestCase):
    def test_quotes_are_mapped_to_original_runs_without_bridging_gaps(self):
        text = '96 "40" X96 OTHER 2006'
        scope = {'body_text': text, 'paragraph_runs': [{'unit': 0, 'body_span': [0, 11], 'text': text[:11]},
                                                     {'unit': 1, 'body_span': [18, 22], 'text': text[18:22]}]}
        rep = representation(scope)
        self.assertTrue(rep['available']); self.assertEqual(rep['quote_masks'], [[3, 7]])
        self.assertEqual([r['value'] for r in rep['inventory']['anchors']], ['96', '2006'])

    def test_unsupported_quote_retains_units_and_makes_page_unavailable(self):
        text = '96 “unsupported'
        rep = representation({'body_text': text, 'paragraph_runs': [{'unit': 0, 'body_span': [0, len(text)], 'text': text}]})
        self.assertFalse(rep['available']); self.assertEqual(rep['unsupported_quote_units'], [0])
        self.assertIsNone(rep['inventory']); self.assertEqual(len(rep['units']), 1)

    def test_capped_scan_uses_all_windows_and_retains_all_maximizers(self):
        scan = capped_scan(rows(['1', '2']), rows(['1', '2', '1', '2']), 2)
        self.assertEqual(scan['window_count'], 3); self.assertEqual(scan['maximum_lcs'], 2)
        self.assertEqual(scan['maximizing_starts'], [0, 2])

    def test_short_and_zero_numeric_sources_are_not_missing_pages(self):
        self.assertEqual(capped_scan(rows(['1']), rows(['1']), 11)['window_count'], 1)
        scan = capped_scan(rows(['1']), [], 11)
        self.assertEqual((scan['window_count'], scan['capped_width'], scan['maximum_lcs']), (1, 0, 0))
        with self.assertRaises(ValueError): capped_scan([], [], 0)

    def test_duplicate_controls_sparse_null_and_zero_anchor_units_retained(self):
        rep = {'inventory': {'anchors': rows(['1', '1'])}, 'quote_masks': [], 'units': [{'unit': 0}, {'unit': 1}, {'unit': 2}]}
        cfg = {'numeric_budget': 11, 'seed': 'fixture', 'draws_per_shuffle_family': 16,
               'minimum_shared_numeric_types': 3, 'control_families': ['reverse', 'within_paragraph_reverse', 'anchor_shuffle', 'paragraph_shuffle']}
        result = assessment(rows(['1', '1']), rep, cfg)
        self.assertEqual(len(result['controls']), 34); self.assertEqual(result['control_ties'], 34)
        self.assertIsNone(result['within_page_order_separated']); self.assertTrue(result['functional_checks_passed'])
        self.assertTrue(all(sorted(c['unit_order']) == [0, 1, 2] for c in result['controls'] if c['unit_order'] is not None))

    def test_panel_ties_fail_missing_pages_are_null_and_whole_score_is_separate(self):
        def case(cap, whole): return {'functional_checks_passed': True, 'observed': {'whole': {'shared_distinct': 3, 'ordered_lcs': whole}, 'capped_scan': {'maximum_lcs': cap}}}
        reference = case(6, 6)
        self.assertFalse(panel_decision(reference, [case(6, 6)], 3)['registered_capped_specificity_gate'])
        self.assertIsNone(panel_decision(reference, [None], 3)['registered_capped_specificity_gate'])
        r = panel_decision(reference, [case(5, 7)], 3)
        self.assertTrue(r['registered_capped_specificity_gate']); self.assertFalse(r['whole_page_specificity_diagnostic'])


if __name__ == '__main__': unittest.main()
