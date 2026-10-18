import importlib.util
from pathlib import Path
import tempfile
import unittest
from fl_decipher.calibration_evidence_v21 import locate, audit, assemble


def doc(text, docid='d', kind='fl'):
    return {'id': docid, 'kind': kind, 'text': text, 'url': 'https://example.org/article', 'source_group': 'g'}


def fixture():
    spec = {'uid': '01:001', 'article': 1, 'connected_group': ['g'], 'article_url': 'https://example.org/article',
            'fl_locator': 'Fa so.', 'source_locator': 'One thing.', 'fl_documents': ['fl'], 'source_documents': ['en']}
    docs = {'fl': {'document': doc('Fa so.', 'fl'), 'provenance': {'eligible': True}},
            'en': {'document': doc('One thing.', 'en', 'source'), 'provenance': {'eligible': True}}}
    return spec, docs


class CalibrationEvidenceTests(unittest.TestCase):
    def test_complete_multi_statement_group_preserves_document_offsets(self):
        d = doc('Intro ends. Alpha goes. Beta stays. Tail ends.')
        r = locate('Alpha goes. Beta stays.', d)
        self.assertEqual(len(r), 1)
        self.assertTrue(r[0]['complete_group'])
        self.assertEqual(r[0]['text'], 'Alpha goes. Beta stays.')
        self.assertEqual(r[0]['statement_span'], [12, 35])
        self.assertEqual(r[0]['tokens'][0]['span'], [12, 17])
        self.assertEqual(len(r[0]['atoms']), 2)

    def test_substring_and_truncated_or_lowercase_atoms_are_not_complete(self):
        for text, locator in [('Before Alpha goes today.', 'Alpha goes'), ('of destiny.', 'of destiny'), ('Alpha goes:', 'Alpha goes')]:
            r = locate(locator, doc(text))
            self.assertEqual(len(r), 1)
            self.assertFalse(r[0]['complete_group'])
        self.assertEqual(locate('Alpha goes.', doc('Alpha goes. Alpha goes.'))[1]['tokens'][0]['index'], 0)

    def test_project_unicode_normalization_preserves_accent_and_original_offsets(self):
        r = locate('Alpha A\u0304gama.', doc('Alpha Āgama.'))[0]
        self.assertTrue(r['complete_group'])
        self.assertEqual(r['tokens'][1]['surface'], 'Āgama')
        self.assertEqual(r['tokens'][1]['span'], [6, 11])
        self.assertEqual(locate('Alpha Agama.', doc('Alpha Āgama.')), [])

    def test_duplicate_fl_support_views_count_as_one_unit_and_incompatible_views_fail(self):
        spec, docs = fixture()
        spec['fl_documents'].append('fl2')
        docs['fl2'] = {'document': doc('Fa so.', 'fl2'), 'provenance': {'eligible': True}}
        r = audit([spec], docs, '03:007')
        self.assertEqual(r['unit_denominator'], 1)
        self.assertTrue(r['rows'][0]['gate']['development_packet_eligible'])
        self.assertEqual(r['rows'][0]['fl_support_view_denominator'], 2)
        docs['fl2']['document']['text'] = 'Fa so!'
        r = audit([spec], docs, '03:007')
        self.assertIn('fl_support_views_compatible', r['rows'][0]['gate']['unmet'])

    def test_each_required_evidence_condition_fails_closed(self):
        spec, docs = fixture()
        self.assertTrue(audit([spec], docs, '03:007')['rows'][0]['gate']['development_packet_eligible'])
        for mutate, key in [(lambda s, d: d['en']['provenance'].update(eligible=False), 'source_provenance_reviewed'),
                              (lambda s, d: d['fl']['document'].update(url='https://example.org/wrong'), 'fl_historical_provenance_and_article_scope'),
                              (lambda s, d: d['en']['document'].update(text='One thing. One thing.'), 'unique_source_occurrence'),
                              (lambda s, d: d['fl']['document'].update(text='Fa so. Fa so.'), 'unique_fl_occurrence_per_support_view'),
                              (lambda s, d: s.update(source_locator='One'), 'source_complete_statement_group'),
                              (lambda s, d: s.update(uid='03:007'), 'target_excluded')]:
            s, d = fixture();mutate(s, d)
            self.assertIn(key, audit([s], d, '03:007')['rows'][0]['gate']['unmet'])

    def test_numbered_or_heading_token_is_retained_instead_of_repaired(self):
        r = locate('Alpha goes.', doc('1. Alpha goes.'))[0]
        self.assertFalse(r['complete_group'])
        self.assertEqual(r['tokens'][0]['document_token_index'], 1)
        self.assertFalse(locate('Alpha goes.', doc('Heading Alpha goes.'))[0]['complete_group'])

    def test_order_inversion_invalidates_both_units(self):
        s, d = fixture()
        d['fl']['document']['text'] = 'Fa so. Ba la.'
        d['en']['document']['text'] = 'Other item. One thing.'
        second = s | {'uid': '01:002', 'fl_locator': 'Ba la.', 'source_locator': 'Other item.'}
        r = audit([s, second], d, '03:007')
        self.assertTrue(any(not x['ordered_nonoverlapping'] for x in r['order_checks']))
        self.assertTrue(all('no_observed_order_conflicts' in x['gate']['unmet'] for x in r['rows']))

    def test_failed_route_cannot_be_replaced_by_successful_comparator_route(self):
        s, d = fixture();ok = audit([s], d, '03:007')
        d['en']['provenance']['eligible'] = False;bad = audit([s], d, '03:007')
        cfg = {'comparator_uids': ['01:001'], 'excluded_target_uid': '03:007',
               'broadening_gate': {'min_new_eligible_units': 6, 'min_additional_connected_groups': 2, 'min_total_connected_groups': 3}}
        panel = assemble(bad, ok, cfg)
        self.assertEqual(panel['unit_denominator'], 0)
        self.assertEqual(len(panel['route_failures_retained']), 1)
        self.assertFalse(panel['decision']['meaningfully_broader_panel_available'])
        self.assertEqual(panel['decision']['next_step'], 'prioritize_evidence_acquisition_and_independent_review')
        self.assertFalse(panel['decision']['orthographic_rule_executed'])

    def test_preparation_guards_all_paths_before_writing(self):
        path = Path(__file__).resolve().parents[1]/'scripts/prepare_calibration_evidence_v21.py'
        spec = importlib.util.spec_from_file_location('prepare_calibration_evidence_test', path)
        m = importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory);(root/'benchmarks').mkdir()
            old = root/'benchmarks/kamri_calibration_evidence_v21.json';old.write_text('preserve')
            with self.assertRaises(FileExistsError):m.freeze(root)
            self.assertEqual(old.read_text(), 'preserve')
            self.assertFalse((root/'data/v21/frozen_inputs.json').exists())

if __name__ == '__main__':
    unittest.main()
