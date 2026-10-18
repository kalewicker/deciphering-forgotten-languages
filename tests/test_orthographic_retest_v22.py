import importlib.util
from pathlib import Path
import tempfile
import unittest
from fl_decipher.orthographic_v20 import calibrate
from fl_decipher.orthographic_retest_v22 import adapt_panel, group_accounting, group_removal_support


def rows(words, uid):
    return [{'unit_uid': uid, 'document': 'doc', 'index': i, 'surface': s, 'form': s.casefold(),
             'span': [100+i*20, 100+i*20+len(s)], 'view_surface': s} for i, s in enumerate(words)]


def panel():
    return [{'uid': str(i), 'connected_group': ['g1', 'linked'] if i < 2 else ['g2'],
             'fl_tokens': rows(['Dadah', fl], str(i)), 'source_tokens': rows(['When', en], str(i))}
            for i, (fl, en) in enumerate([('Brahma', 'Brahmā'), ('Shakra', 'Shakra'), ('Indra', 'Indra')])]


def config():
    return {'unit_denominator': 3, 'lure_surface': 'xqframe',
            'calibration_gate': {'min_proposals': 3, 'min_units': 3, 'min_keys': 3, 'min_diacritic_dependent': 1,
                                 'max_positional_conflicts': 0, 'max_wrong_name_proposals': 0, 'max_cross_component_proposals': 0}}


class OrthographicRetestTests(unittest.TestCase):
    def test_adapter_preserves_composite_groups_and_every_original_token(self):
        original = panel();adapted = adapt_panel(original, 'target')
        self.assertEqual(adapted[0]['component'], '["g1","linked"]')
        self.assertEqual(adapted[0]['fl_tokens'], original[0]['fl_tokens'])
        self.assertEqual(adapted[0]['source_tokens'], original[0]['source_tokens'])
        self.assertNotIn('component', original[0])

    def test_adapter_rejects_duplicate_uid_target_and_unequal_packet(self):
        for units in [panel()+[panel()[0]], [panel()[0] | {'uid': 'target'}], [panel()[0] | {'source_tokens': []}]]:
            with self.assertRaises(ValueError):adapt_panel(units, 'target')

    def test_group_accounting_conserves_positive_and_negative_denominators(self):
        ps = adapt_panel(panel(), 'target');c = calibrate(ps, config());g = group_accounting(c, ps)
        self.assertEqual([x['unit_denominator'] for x in g], [2, 1])
        self.assertEqual(sum(x['token_pair_denominator'] for x in g), 6)
        for name in ['primary', 'baseline']:
            total = c['rules'][name]['summary']
            self.assertEqual(sum(x['rules'][name]['proposals'] for x in g), total['proposals'])
            self.assertEqual(sum(x['rules'][name]['cross_group_comparisons'] for x in g), 4)
            self.assertEqual(sum(x['rules'][name]['wrong_name_views'] for x in g), 3)
            self.assertEqual(sum(x['rules'][name]['frame_lure_views'] for x in g), 3)
        self.assertEqual(g[1]['rules']['primary']['support_units'], ['2'])

    def test_removal_is_whole_group_and_never_changes_full_panel_gate(self):
        ps = adapt_panel(panel(), 'target');cfg = config();c = calibrate(ps, cfg)
        self.assertTrue(c['rules']['primary']['gate']['conditional_anchor_calibration_eligible'])
        r = group_removal_support(c, ps, cfg['calibration_gate'])
        self.assertEqual(r[0]['removed_uids'], ['0', '1'])
        self.assertEqual(r[0]['remaining_unit_denominator'], 1)
        self.assertEqual(r[0]['rules']['primary']['keys'], ['indra'])
        self.assertFalse(r[0]['rules']['primary']['positive_conditions_met'])
        self.assertTrue(all(not x['used_for_primary_decision'] and not x['full_calibration_gate_recomputed'] and not x['fresh_holdout'] for x in r))
        self.assertTrue(c['rules']['primary']['gate']['conditional_anchor_calibration_eligible'])

    def test_preparation_guards_existing_target_before_writing_panel(self):
        path = Path(__file__).resolve().parents[1]/'scripts/prepare_orthographic_retest_v22.py'
        spec = importlib.util.spec_from_file_location('prepare_retest_test', path)
        m = importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory);(root/'data/v22').mkdir(parents=True)
            old = root/'data/v22/frozen_target.json';old.write_text('preserve')
            with self.assertRaises(FileExistsError):m.freeze(root)
            self.assertEqual(old.read_text(), 'preserve')
            self.assertFalse((root/'data/v22/frozen_panel.json').exists())

if __name__ == '__main__':
    unittest.main()
