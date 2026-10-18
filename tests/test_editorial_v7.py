from collections import Counter
import json
from pathlib import Path
import unittest

from fl_decipher.editorial_v7 import EditorialScoreCache, VARIANTS, relative_pairs
from fl_decipher.experiment_v7 import aggregate, comparisons
from fl_decipher.passage_v3 import PreparedSource, ScoreCache, make_block
from fl_decipher.precision_v4 import align
from fl_decipher.register_v5 import predictions
from fl_decipher.synthetic_v7 import generate
from fl_decipher.text import sentences

ROOT = Path(__file__).resolve().parents[1]
CFG = json.loads((ROOT/'experiments/kamri_register_v5.json').read_text())
LEXICON = json.loads((ROOT/CFG['lexicon_path']).read_text())


class EditorialTests(unittest.TestCase):
    def test_legacy_is_exact_alignment_regression(self):
        packet = generate(97001, 15, LEXICON)
        fa = sentences(packet['fl_text']); sa = sentences(packet['candidate_texts'][packet['answer_index']])
        fu, su = [(i,) for i in range(6)], [(i,) for i in range(6)]
        ps, _ = predictions(fa, LEXICON, CFG['lexicon_rules'], 'gated_aliases')
        prep = PreparedSource(sa, su)
        old = ScoreCache(fa, prep, CFG, ps)
        new = EditorialScoreCache(fa, prep, CFG, ps, VARIANTS[0])
        self.assertEqual(align(fu, prep, old, CFG, 'tokens'), align(fu, prep, new, CFG, 'tokens'))

    def test_all_conditions_keep_world_identities_and_candidate_position(self):
        packets = [generate(97001, m, LEXICON) for m in range(16)]
        self.assertEqual(len({p['answer_index'] for p in packets}), 1)
        self.assertEqual(len({tuple(x['uid'] for x in p['fl_token_ids']) for p in packets}), 1)
        for p in packets:
            self.assertEqual(len(p['edges']), 6)
            self.assertEqual(len(set(p['candidate_texts'])), 4)
            extra = sum(x['uid'] is None for x in p['source_token_ids'])
            self.assertEqual(extra, (24 if p['mask'] & 2 else 0)+(12 if p['mask'] & 4 else 0))
            self.assertEqual(len(p['conflicted_fl_spans']), 6 if p['mask'] & 8 else 0)

    def test_source_rotations_preserve_atom_word_bags_and_punctuation(self):
        p = generate(97001, 7, LEXICON)
        arrays = [sentences(t) for t in p['candidate_texts']]
        for i in range(6):
            bags = [Counter(t.normalized for t in a[i].tokens) for a in arrays]
            self.assertTrue(all(b == bags[0] for b in bags))
            punctuation = [make_block(a, (i,)).features['punctuation'] for a in arrays]
            self.assertTrue(all(x == punctuation[0] for x in punctuation))

    def test_conflicts_change_predictions_without_relabeling_gold(self):
        p = generate(97001, 8, LEXICON)
        fa = sentences(p['fl_text'])
        ps, _ = predictions(fa, LEXICON, CFG['lexicon_rules'], 'gated_aliases')
        self.assertTrue(all(row[0]['prediction'] == 'and' for row in ps))
        source = sentences(p['candidate_texts'][p['answer_index']])
        self.assertTrue(all(a.tokens[0].normalized == 'the' for a in source))
        self.assertTrue(all(fa[e['fl_index']].tokens[0].normalized == 'aš' for e in p['edges']))

    def test_relative_pairs_scale_and_preserve_multiplicity(self):
        a = {'length': 8, 'repetitions': {(1, 3), (2, 6)}}
        b = {'length': 16, 'repetitions': {(2, 6), (4, 12)}}
        self.assertEqual(relative_pairs(a), relative_pairs(b))
        c = {'length': 32, 'repetitions': {(0, 8), (1, 9)}}
        self.assertEqual(relative_pairs(c), Counter({(0, 2): 2}))

    def test_neutral_lexical_credit_and_punctuation_are_separate(self):
        fa, sa = sentences('şu aš unknown,'), sentences('the something extra.')
        ps, _ = predictions(fa, LEXICON, CFG['lexicon_rules'], 'gated_aliases')
        prep = PreparedSource(sa, [(0,)])
        scores = {v['id']: EditorialScoreCache(fa, prep, CFG, ps, v).row((0,), 1, 'lexical')[0] for v in VARIANTS}
        self.assertAlmostEqual(scores['p0_r0_l1']-scores['p0_r0_l0'], .1)
        self.assertAlmostEqual(scores['p1_r0_l0']-scores['p0_r0_l0'], .06)
        self.assertAlmostEqual(scores['p1_r0_l1']-scores['p0_r0_l0'], .16)

    def test_unadmitted_metrics_remain_in_fixed_denominator(self):
        count = {'correct': 2, 'proposed': 3, 'reference': 6, 'extra': 1}
        row = {'dataset': 'synthetic', 'seed': 97001, 'unique_correct_top1': False,
               'admitted': False, 'top_work_correct': True, 'source_absent': {'false_admission': False},
               **{k: count for k in ('retrieved_edges', 'conditional_edges', 'retrieved_tokens', 'conditional_tokens')}}
        result = aggregate([row, row], 'fixture', 'legacy')
        self.assertEqual(result['selected_conditions'], 2)
        self.assertEqual(result['independent_worlds'], 1)
        self.assertEqual(result['unique_correct_top1'], 0)
        self.assertEqual(result['retrieved_edges']['reference'], 12)
        self.assertEqual(result['retrieved_edges']['recall'], 4/12)

    def test_factor_contrasts_change_one_factor_and_keep_paired_world(self):
        rows = [{'split': 'fresh', 'seed': 97001, 'mask': m, 'variant': v['id'],
                 'unique_correct_top1': v['lexical_neutral'], 'admitted': False, 'top_work_correct': True,
                 'source_absent': {'false_admission': False}, 'conditional_edges': {'correct': 6-m},
                 'conditional_tokens': {'correct': 30-m}} for m in range(2) for v in VARIANTS]
        result = comparisons(rows)
        self.assertEqual(result['independent_worlds'], 1)
        self.assertEqual(len(result['matched_scoring_factors']), 24)
        self.assertEqual(len(result['condition_vs_pristine']), 8)
        for c in result['matched_scoring_factors']:
            low = next(v for v in VARIANTS if v['id'] == c['low'])
            high = next(v for v in VARIANTS if v['id'] == c['high'])
            self.assertEqual([k for k in ('punctuation_neutral', 'relative_repetition', 'lexical_neutral') if low[k] != high[k]], [c['factor']])
            self.assertEqual(c['difference']['unique_correct_top1'], int(c['factor'] == 'lexical_neutral'))


if __name__ == '__main__':
    unittest.main()
