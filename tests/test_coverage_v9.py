import json
from pathlib import Path
import unittest

from fl_decipher.coverage_v9 import components, factor_quality, apply_factors
from fl_decipher.synthetic_v9 import generate
from fl_decipher.register_v5 import predictions
from fl_decipher.text import sentences

ROOT = Path(__file__).resolve().parents[1]
CFG = json.loads((ROOT/'experiments/kamri_order_v8.json').read_text())
LEXICON = json.loads((ROOT/CFG['lexicon_path']).read_text())


class CoverageTests(unittest.TestCase):
    def test_full_agreement_partial_coverage_isolated(self):
        fa, sa = sentences('x x. x x.'), sentences('a b.')
        ps = [[{'prediction': None} for _ in a.tokens] for a in fa]
        a = {'blocks': [{'fl_atoms': [0], 'source_atoms': [0]}], 'strength': .2}
        q = components(a, fa, sa, ps, CFG)
        self.assertEqual(q['covered_upper_bound'], 1.)
        self.assertEqual(q['upper_bound'], 2.)
        self.assertEqual(factor_quality(q, True, False)['quality'], 1.)
        self.assertEqual(factor_quality(q, False, True)['quality'], 0.)
        self.assertEqual(factor_quality(q, True, True)['quality'], q['quality'])
        self.assertEqual(factor_quality(q, False, False)['quality'], 1.)

    def test_all_combinations_and_v8_equivalence_with_conflict(self):
        fa, sa = sentences('x y. z z.'), sentences('the wrong.')
        ps = [[{'prediction': p} for p in ['the', 'and']], [{'prediction': None}, {'prediction': None}]]
        a = {'blocks': [{'fl_atoms': [0], 'source_atoms': [0]}], 'strength': .3, 'edges': []}
        q = components(a, fa, sa, ps, CFG)
        self.assertEqual(q['covered_upper_bound'], 4.)
        self.assertEqual(q['upper_bound'], 5.)
        self.assertAlmostEqual(factor_quality(q, True, False)['quality'], .5/4)
        self.assertAlmostEqual(factor_quality(q, False, True)['quality'], 2.5/5)
        self.assertEqual(factor_quality(q, True, True)['quality'], q['quality'])
        for o in (False, True):
            for c in (False, True):
                result = apply_factors(a, q, {'order': o, 'coverage': c})
                self.assertLessEqual(result['strength'], a['strength'])
                self.assertEqual(result['blocks'], a['blocks'])
                self.assertEqual(result['edges'], a['edges'])

    def test_empty_path_baseline_and_fail_closed_active_factors(self):
        fa = sentences('x x.')
        q = components({'blocks': []}, fa, [], [[{'prediction': None}]*2], CFG)
        self.assertEqual(factor_quality(q, False, False)['quality'], 1.)
        for o, c in [(True, False), (False, True), (True, True)]:
            self.assertEqual(factor_quality(q, o, c)['quality'], 0.)

    def test_density_changes_only_fl_anchor_forms(self):
        rich = generate(99001, 'normal', 'full', 'rotation', LEXICON)
        zero = generate(99001, 'zero', 'full', 'rotation', LEXICON)
        self.assertEqual(rich['candidate_texts'], zero['candidate_texts'])
        self.assertEqual([x['uid'] for x in rich['fl_token_ids']], [x['uid'] for x in zero['fl_token_ids']])
        for packet, n in [(rich, 12), (zero, 0)]:
            ps, gate = predictions(sentences(packet['fl_text']), LEXICON, CFG['lexicon_rules'], CFG['prediction_variant'])
            self.assertEqual(sum(p['prediction'] is not None for row in ps for p in row), n)
            self.assertFalse(gate['active'])

    def test_half_references_only_available_occurrences(self):
        full = generate(99001, 'normal', 'full', 'rotation', LEXICON)
        half = generate(99001, 'normal', 'half', 'rotation', LEXICON)
        self.assertEqual(full['fl_text'], half['fl_text'])
        self.assertEqual(len(full['edges']), 6)
        self.assertEqual(len(half['edges']), 3)
        available = {p['uid'] for p in half['token_pairs']}
        missing = set(half['unavailable_query_uids'])
        self.assertFalse(available & missing)
        self.assertEqual(available | missing, {t['uid'] for t in half['fl_token_ids']})

    def test_renamed_unknown_content_has_same_observable_objective(self):
        p = generate(99001, 'normal', 'full', 'renamed', LEXICON)
        fa = sentences(p['fl_text']); ps, _ = predictions(fa, LEXICON, CFG['lexicon_rules'], CFG['prediction_variant'])
        a = {'blocks': [{'fl_atoms': [i], 'source_atoms': [i]} for i in range(6)]}
        qualities = [components(a, fa, sentences(t), ps, CFG)['quality'] for t in p['candidate_texts']]
        self.assertEqual(qualities, [1.]*4)
        self.assertEqual(len(set(p['candidate_texts'])), 4)

    def test_content_order_retains_function_positions_and_content_bags(self):
        p = generate(99001, 'normal', 'full', 'content_order', LEXICON)
        correct = sentences(p['candidate_texts'][p['answer_index']])
        for text in p['candidate_texts']:
            for true, other in zip(correct, sentences(text), strict=True):
                tw = [t.normalized for t in true.tokens]; ow = [t.normalized for t in other.tokens]
                self.assertEqual(sorted(tw), sorted(ow))
                self.assertEqual([(i, w) for i, w in enumerate(tw) if w in ('the', 'and')],
                                 [(i, w) for i, w in enumerate(ow) if w in ('the', 'and')])

    def test_candidate_positions_shared_across_all_twelve_conditions(self):
        answers = {generate(99001, d, e, f, LEXICON)['answer_index'] for d in ('normal', 'zero') for e in ('full', 'half')
                   for f in ('rotation', 'renamed', 'content_order')}
        self.assertEqual(len(answers), 1)


if __name__ == '__main__':
    unittest.main()
