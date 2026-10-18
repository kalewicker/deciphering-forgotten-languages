import importlib.util
from pathlib import Path
import tempfile
import unittest
from fl_decipher.orthographic_v20 import folded, exact, eligible, proposal, name_pool, wrong_name_view, frame_lure, calibrate, compare_target


def rows(surfaces, uid='u', document='doc'):
    return [{'unit_uid': uid, 'document': document, 'index': i, 'surface': s, 'form': s.casefold(),
             'span': [100+i*20, 100+i*20+len(s)], 'view_surface': s} for i, s in enumerate(surfaces)]


def config(count=3):
    return {'unit_denominator': count, 'lure_surface': 'xqframe',
            'calibration_gate': {'min_proposals': 3, 'min_units': 3, 'min_keys': 3, 'min_diacritic_dependent': 1,
                                 'max_positional_conflicts': 0, 'max_wrong_name_proposals': 0, 'max_cross_component_proposals': 0}}


def panel():
    return [{'uid': str(i), 'component': 'a' if i < 2 else 'b',
             'fl_tokens': rows(['Dadah', fl], str(i), 'fl'), 'source_tokens': rows(['When', en], str(i), 'source')}
            for i, (fl, en) in enumerate([('Brahma', 'Brahmā'), ('Shakra', 'Shakra'), ('Indra', 'Indra')])]


class OrthographicTests(unittest.TestCase):
    def test_folding_is_fixed_mark_removal_not_transliteration_or_edit_distance(self):
        self.assertEqual(folded('Āgama'), 'agama')
        self.assertEqual(folded('Brahma\u0304'), 'brahma')
        self.assertNotEqual(exact('Āgama'), exact('Agama'))
        self.assertNotEqual(folded('Shakra'), folded('Shakira'))
        self.assertNotEqual(folded('ø'), 'o')

    def test_capitalized_noninitial_latin_length_rule_and_sentence_initial_abstention(self):
        ts = rows(['Shakra', 'Shakra', 'One', 'agama', 'Āgama', 'Κάλυμμα', 'Name42'])
        self.assertEqual([eligible(t) for t in ts], [False, True, False, False, True, False, False])

    def test_folded_proposal_preserves_original_forms_and_offsets(self):
        fl, en = rows(['Dadah', 'Agama'], document='fl'), rows(['When', 'Āgama'], document='source')
        r = proposal(fl, en, 'primary')
        a = r['proposals'][0]
        self.assertTrue(a['diacritic_dependent'])
        self.assertEqual(a['source_token']['surface'], 'Āgama')
        self.assertEqual(a['source_token']['span'], en[1]['span'])
        self.assertEqual(proposal(fl, en, 'baseline')['proposals'], [])
        self.assertEqual(en[1]['surface'], en[1]['view_surface'])

    def test_lowercase_or_initial_duplicate_blocks_reciprocal_uniqueness(self):
        fl = rows(['Dadah', 'Shakra'])
        for en in [rows(['When', 'Shakra', 'shakra']), rows(['Shakra', 'Shakra'])]:
            result = proposal(fl, en, 'primary')
            self.assertEqual(result['proposal_denominator'], 0)
            self.assertEqual(result['fl_ledger'][1]['status'], 'ambiguous_key_occurrence')
        self.assertEqual(proposal(rows(['Shakra', 'Shakra']), rows(['When', 'Shakra']), 'primary')['proposal_denominator'], 0)

    def test_lowercase_english_match_does_not_make_capitalized_anchor(self):
        r = proposal(rows(['Dadah', 'Shakra']), rows(['When', 'shakra']), 'primary')
        self.assertEqual(r['proposal_denominator'], 0)
        self.assertEqual(r['fl_ledger'][1]['status'], 'english_candidate_ineligible')

    def test_name_derangement_changes_view_only_and_keeps_replacement_origins(self):
        ps = panel()
        pool = name_pool(ps)
        view, replacements = wrong_name_view(ps[0], pool)
        self.assertNotEqual(folded(view[1]['view_surface']), folded(view[1]['surface']))
        self.assertEqual(view[1]['surface'], 'Brahmā')
        self.assertEqual(view[1]['span'], ps[0]['source_tokens'][1]['span'])
        self.assertTrue(replacements[0]['replacement_origins'])
        self.assertEqual(ps[0]['source_tokens'][1]['view_surface'], 'Brahmā')

    def test_name_preserving_lure_still_proposes_anchor_and_cannot_establish_source_identity(self):
        u = panel()[0]
        view = frame_lure(u, 'xqframe')
        self.assertEqual(view[0]['view_surface'], 'xqframe')
        self.assertEqual(view[1]['view_surface'], 'Brahmā')
        self.assertEqual(proposal(u['fl_tokens'], view, 'primary')['proposal_denominator'], 1)
        r = calibrate(panel(), config())['rules']['primary']
        self.assertEqual(r['summary']['frame_lure_proposals'], 3)
        self.assertTrue(r['gate']['conditional_anchor_calibration_eligible'])
        self.assertTrue(all(not v['source_identity_accepted'] for v in r['frame_lures']))

    def test_full_cross_component_denominator_and_fixed_coverage_gate(self):
        ps = panel()
        r = calibrate(ps, config())['rules']['primary']
        self.assertEqual(r['summary']['cross_component_comparisons'], 4)
        self.assertTrue(r['gate']['conditional_anchor_calibration_eligible'])
        short = calibrate(ps[:2], config(2))['rules']['primary']
        self.assertFalse(short['gate']['conditional_anchor_calibration_eligible'])
        self.assertIn('minimum_distinct_keys', short['gate']['unmet'])
        self.assertEqual(short['summary']['proposals'], 2)

    def test_positional_conflict_fails_gate_without_changing_anchor(self):
        ps = panel()
        ps[0]['source_tokens'] = rows(['When', 'the', 'Brahmā'], '0', 'source')
        r = calibrate(ps, config())['rules']['primary']
        self.assertEqual(r['summary']['positional_conflicts'], 1)
        self.assertFalse(r['gate']['conditional_anchor_calibration_eligible'])

    def test_failed_calibration_blocks_mechanical_target_winner_and_preserves_both_gaps(self):
        ps = panel()
        c = calibrate(ps[:2], config(2))
        target = {'uid': 'target', 'fl_tokens': rows(['Dadah', 'Agama']),
                  'source_tokens': rows(['When', 'an', 'Āgama']), 'gap_gate': {'development_gap_score_eligible': True}}
        alignments = [{'gap': gap, 'unpaired_source_token': target['source_tokens'][gap],
                       'rows': [{'fl_token': {'index': i}, 'source_token': {'index': j}} for i, j in enumerate([0, 2] if gap == 1 else [0, 1])]}
                      for gap in [1, 2]]
        r = compare_target(target, alignments, c)
        self.assertEqual(r['rules']['primary']['descriptive_maximizers'], [1])
        self.assertIsNone(r['primary_gap_lead'])
        self.assertFalse(r['rules']['primary']['conditional_comparison_available'])
        self.assertEqual(r['original_v19_gaps'], [1, 2])
        self.assertFalse(r['original_hypotheses_modified'])
        self.assertEqual(r['rules']['baseline']['descriptive_maximizers'], [1, 2])
        self.assertIsNone(compare_target(target, alignments, calibrate(ps, config()))['rules']['baseline']['eligible_gap_lead'])
        target['gap_gate']['development_gap_score_eligible'] = False
        self.assertIsNone(compare_target(target, alignments, calibrate(ps, config()))['primary_gap_lead'])

    def test_preparation_guards_every_output_before_any_write(self):
        script = Path(__file__).resolve().parents[1]/'scripts/prepare_orthographic_v20.py'
        spec = importlib.util.spec_from_file_location('prepare_orthographic_test', script)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root/'data/v20').mkdir(parents=True)
            old = root/'data/v20/frozen_target.json'
            old.write_text('preserve')
            with self.assertRaises(FileExistsError):
                module.freeze(root)
            self.assertEqual(old.read_text(), 'preserve')
            self.assertFalse((root/'data/v20/frozen_panel.json').exists())

if __name__ == '__main__':
    unittest.main()
