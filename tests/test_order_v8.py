import json
from pathlib import Path
import unittest
from itertools import product

from fl_decipher.order_v8 import apply_order, order_quality, token_objective
from fl_decipher.experiment_v8 import counterfactual
from fl_decipher.text import sentences

ROOT = Path(__file__).resolve().parents[1]
CFG = json.loads((ROOT/'experiments/kamri_editorial_v7.json').read_text())


class OrderTests(unittest.TestCase):
    def test_full_objective_retains_costs_not_just_positive_pairs(self):
        self.assertEqual(token_objective(['the'], ['and'], CFG), -1.5)
        self.assertEqual(token_objective([], ['a', 'b'], CFG), -1.5)
        self.assertEqual(token_objective(['the', None], [], CFG), -1.5)
        self.assertEqual(token_objective(['the', None], ['the', 'x'], CFG), 2.5)

    def test_known_anchor_rotation_reduces_objective(self):
        ps = ['the', None, 'and', None]
        original = token_objective(ps, ['the', 'x', 'and', 'y'], CFG)
        rotated = token_objective(ps, ['y', 'the', 'x', 'and'], CFG)
        self.assertEqual(original, 5.)
        self.assertLess(rotated, original)

    def test_perfect_quality_and_unknown_limit(self):
        fa, sa = sentences('şu x aš y.'), sentences('the x and y.')
        ps = [[{'prediction': p} for p in ['the', None, 'and', None]]]
        a = {'blocks': [{'fl_atoms': [0], 'source_atoms': [0]}], 'strength': .2}
        q = order_quality(a, fa, sa, ps, CFG)
        self.assertEqual(q['quality'], 1.)
        self.assertEqual(q['upper_bound'], 5.)
        unknown = [[{'prediction': None} for _ in fa[0].tokens]]
        other = sentences('unrelated words replace everything.')
        self.assertEqual(order_quality(a, fa, other, unknown, CFG)['quality'], 1.)

    def test_uncovered_tokens_are_charged_and_quality_clips(self):
        fa, sa = sentences('x x. x x. x x.'), sentences('y y.')
        ps = [[{'prediction': None} for _ in a.tokens] for a in fa]
        a = {'blocks': [{'fl_atoms': [0], 'source_atoms': [0]}], 'strength': .2}
        q = order_quality(a, fa, sa, ps, CFG)
        self.assertEqual(q['uncovered_query_tokens'], 4)
        self.assertEqual(q['uncovered_query_penalty'], -3.)
        self.assertLess(q['raw_quality'], 0.)
        self.assertEqual(q['quality'], 0.)
        self.assertEqual(apply_order(a, q, False)['strength'], .2)
        self.assertEqual(apply_order(a, q, True)['strength'], 0.)

    def test_order_does_not_reopen_search_or_change_edges(self):
        a = {'strength': .3, 'blocks': [], 'edges': [{'fl_index': 0, 'source_index': 0}]}
        q = {'quality': .4}
        result = apply_order(a, q, True)
        self.assertEqual(result['strength'], .12)
        self.assertEqual(result['blocks'], a['blocks'])
        self.assertEqual(result['edges'], a['edges'])
        self.assertEqual(a['strength'], .3)

    def test_objective_matches_exhaustive_small_alignment_paths(self):
        def exhaustive(ps, ss, i=0, j=0):
            if i == len(ps):
                return (len(ss)-j)*-.75
            if j == len(ss):
                return (len(ps)-i)*-.75
            score = (2. if ps[i] == ss[j] else -2.) if ps[i] is not None else .5-abs((i+.5)/len(ps)-(j+.5)/len(ss))
            return max(score+exhaustive(ps, ss, i+1, j+1), -.75+exhaustive(ps, ss, i+1, j), -.75+exhaustive(ps, ss, i, j+1))
        for ps in product([None, 'the'], repeat=2):
            for ss in product(['the', 'other'], repeat=3):
                self.assertAlmostEqual(token_objective(ps, ss, CFG), exhaustive(ps, ss))

    def test_old_threshold_counterfactual_is_unavailable_for_order_on(self):
        cfg = {'old_synthetic_thresholds': {'p0_r0_l0': .1}}
        candidate = {'strength': .2, 'minimum_links_met': True}
        row = {'split': 'fresh', 'order': False, 'background': 'p0_r0_l0',
               'rankings': [candidate], 'candidate_margin': .01,
               'source_absent': {'top': candidate, 'margin': .01}}
        self.assertTrue(counterfactual(row, cfg)['source_absent_false_admission'])
        self.assertIsNone(counterfactual({**row, 'order': True}, cfg))
        self.assertIsNone(counterfactual({**row, 'split': 'old_development'}, cfg))


if __name__ == '__main__':
    unittest.main()
