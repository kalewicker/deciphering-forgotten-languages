import importlib.util
from pathlib import Path
import tempfile
import unittest
from fl_decipher.gap_v19 import alignment, search, gap_gate, control_order, tail, EVIDENCE_REQUIREMENTS
from fl_decipher.transfer_v18 import predict


def fixture(fl='Fa so fa.', english=('a', 'x', 'a', 'z')):
    p = predict({'uid': 'u', 'component': 'g', 'fl': fl},
                {'primary': {'fa': {'paired_english_form': 'a'}},
                 'secondary': {'fa': {'paired_english_form': 'a'}},
                 'conflicted_forms': [{'fl_form': 'so'}]})
    r = {'source_tokens': [{'index': i, 'form': w, 'surface': w, 'span': [100+i*3, 101+i*3]} for i, w in enumerate(english)]}
    return p, r


class GapTests(unittest.TestCase):
    def test_first_last_and_internal_gaps_preserve_all_original_identities(self):
        p, r = fixture()
        for gap, expected in [(0, [1, 2, 3]), (1, [0, 2, 3]), (3, [0, 1, 2])]:
            a = alignment(p, r, gap)
            indices = [row['source_token']['index'] for row in a['rows']]
            self.assertEqual(indices, expected)
            self.assertEqual(sorted(indices + [a['unpaired_source_token']['index']]), list(range(4)))
            self.assertEqual(a['unpaired_source_token'], r['source_tokens'][gap])
            self.assertEqual(a['aligned_pairs'], 3)

    def test_historical_fl_document_offsets_preserved_separately_from_target_offsets(self):
        p, r = fixture()
        r['historical_fl_statement_matches'] = [{'text': 'Fa so fa.', 'span': [832, 841]}]
        a = alignment(p, r, 1)
        self.assertEqual(a['rows'][0]['fl_document_span'], [832, 834])
        self.assertEqual(a['rows'][0]['fl_token']['fl_span'], [0, 2])
        self.assertEqual(a['rows'][2]['fl_document_span'], [838, 840])

    def test_permuted_unpaired_token_keeps_original_source_span(self):
        p, r = fixture()
        a = alignment(p, r, 1, [3, 2, 1, 0])
        self.assertEqual(a['unpaired_source_token'], r['source_tokens'][2])
        self.assertEqual([row['source_token']['index'] for row in a['rows']], [3, 1, 0])

    def test_illegal_lengths_gap_or_nonbijective_order_fail(self):
        p, r = fixture()
        for gap, order in [(-1, None), (4, None), (1, [0, 1, 1, 3]), (1, [False, 1, 2, 3])]:
            with self.assertRaises(ValueError):
                alignment(p, r, gap, order)
        with self.assertRaises(ValueError):
            alignment(p, {'source_tokens': r['source_tokens'][:3]}, 1)

    def test_every_maximizer_is_retained_including_no_prediction_case(self):
        p, r = fixture('So la.', ('x', 'y', 'z'))
        s = search(p, r)
        self.assertEqual(s['maxima']['primary']['gaps'], [0, 1, 2])
        self.assertFalse(s['maxima']['primary']['unique'])
        self.assertIsNone(s['maxima']['primary']['agreement'])

    def test_abstention_reason_and_denominators_stay_fixed_for_every_gap(self):
        p, r = fixture('Fa so la.', ('a', 'x', 'y', 'z'))
        s = search(p, r, include_alignments=True)
        for a in s['alignments']:
            self.assertEqual(a['stats']['primary']['predictions'], 1)
            self.assertEqual(a['stats']['primary']['abstentions'], 2)
            self.assertEqual(a['rows'][1]['primary']['abstention_reason'], 'conflicted_training_form')
            self.assertEqual(a['rows'][2]['primary']['abstention_reason'], 'outside_frozen_candidate_set')

    def test_each_control_searches_new_gap_maxima_not_observed_winner(self):
        p, r = fixture('Fa.', ('a', 'z'))
        observed = search(p, r)
        reversed_result = search(p, r, control_order('reverse', 2))
        self.assertEqual(observed['maxima']['primary']['gaps'], [1])
        self.assertEqual(reversed_result['maxima']['primary']['gaps'], [0])
        self.assertEqual(reversed_result['maxima']['primary']['matches'], 1)
        self.assertEqual(len(reversed_result['curve']), 2)
        self.assertEqual(control_order('rotate_+1', 4), [3, 0, 1, 2])
        self.assertEqual(control_order('rotate_-1', 4), [1, 2, 3, 0])

    def test_gap_gate_requires_all_evidence_and_exact_registered_lengths(self):
        r = {'gate': {'requirements': {key: True for key in EVIDENCE_REQUIREMENTS} | {'equal_token_counts': False}}}
        self.assertTrue(gap_gate(r, 21, 22)['development_gap_score_eligible'])
        for key in EVIDENCE_REQUIREMENTS:
            bad = {'gate': {'requirements': r['gate']['requirements'] | {key: False}}}
            self.assertFalse(gap_gate(bad, 21, 22)['development_gap_score_eligible'])
        self.assertFalse(gap_gate({'gate': {'requirements': {}}}, 21, 22)['development_gap_score_eligible'])
        self.assertFalse(gap_gate(r, 20, 21)['development_gap_score_eligible'])
        self.assertFalse(gap_gate(r, 21, 21)['development_gap_score_eligible'])
        self.assertFalse(r['gate']['requirements']['equal_token_counts'])
        self.assertFalse(gap_gate(r, 21, 22)['semantic_training_eligible'])

    def test_tail_counts_exact_integer_ties_and_pseudocount(self):
        t = tail(2, [0, 1, 2, 2, 3])
        self.assertEqual(t['greater_or_equal'], 3)
        self.assertEqual(t['exact_ties'], 2)
        self.assertEqual(t['p_one_sided']['value'], 4/6)
        self.assertEqual(tail(2, [0, 1])['p_one_sided']['value'], 1/3)

    def test_preparation_refuses_partial_existing_output_before_any_write(self):
        script = Path(__file__).resolve().parents[1]/'scripts/prepare_gap_v19.py'
        spec = importlib.util.spec_from_file_location('prepare_gap_test', script)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root/'benchmarks').mkdir()
            old = root/'benchmarks/kamri_gap_v19.json'
            old.write_text('preserve')
            with self.assertRaises(FileExistsError):
                module.prepare(root)
            self.assertEqual(old.read_text(), 'preserve')
            self.assertFalse((root/'data/v19/frozen_evidence.json').exists())

if __name__ == '__main__':
    unittest.main()
