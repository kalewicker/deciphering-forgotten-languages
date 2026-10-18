import copy
import hashlib
import importlib.util
from itertools import product
from pathlib import Path
import unittest

from fl_decipher.adjacent_transposition_v35 import align_forms, prepare, predict, assess
from fl_decipher.positional_worlds_v34 import canonical, prepare as old_prepare, predict as old_predict, assess as old_assess
from fl_decipher.synthetic_transfer_v32 import view
from test_positional_worlds_v34 import fixtures

SPEC = importlib.util.spec_from_file_location('crossing_reference', Path(__file__).resolve().parents[1]/'scripts/verify_adjacent_transposition_v35.py')
REF = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(REF)


def brute(q, c):
    paths = []
    def visit(i, j, cost, pairs, ops):
        if i == len(q) and j == len(c):
            paths.append(((cost, -len(pairs)), frozenset(pairs), frozenset(ops))); return
        if i < len(q): visit(i+1, j, cost+1, pairs, ops+[(i, j, 'query_gap')])
        if j < len(c): visit(i, j+1, cost+1, pairs, ops+[(i, j, 'candidate_gap')])
        if i < len(q) and j < len(c) and q[i] is not None and q[i] == c[j]:
            visit(i+1, j+1, cost, pairs+[(i, j)], ops+[(i, j, 'match')])
        if i+1 < len(q) and j+1 < len(c) and q[i] is not None and q[i+1] is not None and q[i] != q[i+1] and q[i] == c[j+1] and q[i+1] == c[j]:
            visit(i+2, j+2, cost+1, pairs+[(i, j+1), (i+1, j)], ops+[(i, j, 'swap')])
    visit(0, 0, 0, [], [])
    best = min(p[0] for p in paths)
    return best, [p for p in paths if p[0] == best]


class AdjacentTranspositionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        public, oracle, cls.model, cfg = fixtures()
        # Every registered base has barriers; give the second tiny base one too.
        for vid in ('s1', 'q1'):
            forms = [t['form'] for t in public['views'][vid]['tokens']]
            forms[-1] = 'copiedanchor0'; public['views'][vid] = view(forms)
        cls.old_public, cls.old_gold = old_prepare(public, oracle, cls.model, cfg)
        cls.baseline = old_assess(cls.old_public, cls.old_gold, old_predict(cls.old_public, cls.model))
        cls.public, cls.oracle = prepare(cls.old_public, cls.old_gold, cls.model)
        cls.predictions = predict(cls.public, cls.model)
        cls.assessment = assess(cls.public, cls.oracle, cls.predictions, cls.baseline)

    def test_exhaustive_paths_costs_pairs_operation_supports_and_dominators(self):
        seq = [list(x) for n in range(4) for x in product(['a', 'b', None], repeat=n)]
        for q in seq:
            for c in seq:
                r = align_forms(q, c); best, paths = brute(q, c)
                self.assertEqual(r, REF.reference_align(q, c))
                self.assertEqual((r['edit_cost'], -r['matched_tokens']), best)
                self.assertEqual(r['optimal_operation_paths'], len(paths))
                union = set().union(*(p[1] for p in paths)); common = set(paths[0][1]).intersection(*(p[1] for p in paths))
                self.assertEqual({(e['query_index'], e['candidate_index']) for e in r['possible_matches']}, union)
                self.assertEqual(set(map(tuple, r['forced_matches'])), common)
                for e in r['possible_matches']:
                    self.assertEqual(e['through_paths'], sum((e['query_index'], e['candidate_index']) in p[1] for p in paths))
                for op in r['possible_operations']:
                    key = (*op['from'], op['kind'])
                    self.assertEqual(op['through_paths'], sum(key in p[2] for p in paths))

    def test_adjacent_crossing_recovers_both_distinct_origins(self):
        r = align_forms(['b', 'a'], ['a', 'b'])
        self.assertEqual(r['forced_matches'], [[0, 1], [1, 0]])
        self.assertEqual((r['edit_cost'], r['matched_tokens'], r['cross_operations']), (1, 2, 1))
        self.assertEqual(r['optimal_operation_paths'], 1)

    def test_collectively_forced_pair_without_forced_supporting_operation(self):
        q, c = ['a', 'b', 'a'], ['b', 'a', 'a', 'b']
        r = align_forms(q, c); best, paths = brute(q, c)
        self.assertEqual(r, REF.reference_align(q, c))
        edge = next(e for e in r['possible_matches'] if (e['query_index'], e['candidate_index']) == (0, 1))
        self.assertTrue(edge['forced']); self.assertEqual(edge['through_paths'], 2)
        self.assertEqual(len(edge['supporting_operations']), 2)
        self.assertTrue(all(not r['possible_operations'][k]['forced'] for k in edge['supporting_operations']))
        self.assertTrue(all((0, 1) in p[1] for p in paths))

    def test_secondary_objective_prefers_more_matches_at_same_cost(self):
        r = align_forms(['b', 'a', 'b', 'a'], ['a', 'b', 'a', 'b'])
        self.assertEqual((r['edit_cost'], r['matched_tokens'], r['cross_operations']), (2, 4, 2))
        self.assertEqual(r, REF.reference_align(['b', 'a', 'b', 'a'], ['a', 'b', 'a', 'b']))

    def test_equal_symbols_do_not_create_an_invisible_cross_operation(self):
        r = align_forms(['a', 'a'], ['a', 'a'])
        self.assertEqual((r['edit_cost'], r['cross_operations']), (0, 0))
        self.assertEqual(r['forced_matches'], [[0, 0], [1, 1]])
        self.assertFalse(any(op['kind'] == 'swap' for op in r['possible_operations']))

    def test_unknown_and_blocked_forms_never_participate(self):
        for q, c in [([None, 'a'], ['a', None]), (['a', 'b'], [None, 'a']), ([None]*3, ['a', 'b'])]:
            r = align_forms(q, c)
            for e in r['possible_matches']:
                self.assertIsNotNone(q[e['query_index']]); self.assertIsNotNone(c[e['candidate_index']])
            self.assertFalse(any(op['kind'] == 'swap' for op in r['possible_operations']))

    def test_empty_sequences_and_all_gap_accounting(self):
        for q, c in [([], []), (['a'], []), ([], ['a']), ([None]*2, ['a']*3)]:
            r = align_forms(q, c)
            self.assertEqual(r, REF.reference_align(q, c)); self.assertEqual(r['forced_matches'], [])
            self.assertEqual((len(r['query_tokens']), len(r['candidate_tokens'])), (len(q), len(c)))

    def test_coverage_thresholds_keep_unknown_tokens_in_denominator(self):
        symbols = [f's{i}' for i in range(24)]
        self.assertTrue(align_forms(symbols+[None]*6, symbols+['x']*6)['qualifies'])
        self.assertFalse(align_forms(symbols+[None]*7, symbols+['x']*6)['qualifies'])
        self.assertFalse(align_forms(symbols[:23], symbols[:23])['qualifies'])

    def test_independent_controls_and_panels_reconstructed(self):
        self.assertEqual((self.public, self.oracle), REF.reference_prepare(self.old_public, self.old_gold, self.model))
        self.assertEqual(len(self.oracle['controls']), 14); self.assertEqual(len(self.public['panels']), 6)
        self.assertEqual(self.oracle['v34_sites'], self.old_gold['sites'])
        for k, v in self.old_public['observations'].items(): self.assertEqual(self.public['observations'][k], v)

    def test_full_independent_prediction_and_metric_replay(self):
        self.assertEqual(self.predictions, REF.reference_predict(self.public, self.model))
        self.assertEqual(self.assessment, REF.reference_assess(self.public, self.oracle, self.predictions, self.baseline))

    def test_tiny_worlds_recover_visible_swaps_and_preserve_equal_origin_errors(self):
        w = self.assessment['world_assessment']; affected = w['by_relation_world']['unequal']['swap']['forced']['affected']
        self.assertGreater(affected['tokens'], 0)
        self.assertEqual(affected['tokens'], affected['emitted']); self.assertEqual(affected['emitted'], affected['strict_exact'])
        equal = w['by_relation_world']['equal']['swap']['forced']['affected']
        self.assertGreater(equal['emitted'], 0); self.assertEqual(equal['strict_exact'], 0)

    def test_source_negative_controls_have_no_fabricated_origin_scores(self):
        for c in self.assessment['controls']:
            if c['role'] in ('impostor', 'blocked_source', 'frame_source'): self.assertIsNone(c['origin_scores'])
            if c['role'] in ('unknown_all', 'blocked_source', 'frame_source'): self.assertEqual(c['matched_tokens'], 0)

    def test_qualified_duplicate_slots_still_abstain(self):
        forms = [f'symbol{i%24}' for i in range(32)]; aliases = [f'a{i%24}' for i in range(32)]
        model = {'entries': {f'a{i}': {'source_form': f'symbol{i}'} for i in range(24)}, 'ledger': {}}
        obs = {'source': view(forms), 'query': view(aliases)}; oid = 'observation'+hashlib.sha256(canonical(obs)).hexdigest()
        public = {'observations': {oid: obs}, 'panels': [{'panel_id': 'anonymous', 'candidates': [{'slot_id': 'slot0', 'observation_id': oid}, {'slot_id': 'slot1', 'observation_id': oid}]}]}
        p = predict(public, model)
        self.assertTrue(p['predictions'][oid]['alignment']['qualifies'])
        self.assertEqual(p['panels'][0]['decision']['reason'], 'top_tie'); self.assertIsNone(p['panels'][0]['decision']['nominated'])

    def test_input_schema_and_model_immutability(self):
        public, model = copy.deepcopy(self.public), copy.deepcopy(self.model); before = copy.deepcopy((public, model))
        predict(public, model); self.assertEqual((public, model), before)
        next(iter(public['observations'].values()))['origin'] = []
        with self.assertRaises(AssertionError): predict(public, model)


if __name__ == '__main__': unittest.main()
