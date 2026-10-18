import json
from pathlib import Path
import unittest

from fl_decipher.correspondence_v6 import alias_capacity, audit, components, unit_count
from fl_decipher.passage_v3 import make_block, PreparedSource, ScoreCache, protected_groups
from fl_decipher.register_v5 import predictions
from fl_decipher.text import sentences

ROOT = Path(__file__).resolve().parents[1]
CFG = json.loads((ROOT/'experiments/kamri_register_v5.json').read_text())


class CorrespondenceTests(unittest.TestCase):
    def test_protected_partial_block_not_feasible(self):
        groups = [(0,), (1, 2), (3,)]
        self.assertIsNone(unit_count((1,), groups))
        self.assertIsNone(unit_count((0, 2), groups))
        self.assertEqual(unit_count((1, 2, 3), groups), 2)
        self.assertEqual(unit_count((0, 1, 2, 3), groups), 3)

    def test_alias_presence_can_have_insufficient_capacity(self):
        fa, sa = sentences('ńańi ńańi ńańi.'), sentences('One of many.')
        row = alias_capacity(fa, sa, [{'fl_index': 0, 'source_index': 0}])[0]
        self.assertEqual((row['fl_count'], row['source_count'], row['minimum_unrealized']), (3, 1, 2))
        self.assertEqual(row['status'], 'insufficient_one_to_one_capacity')
        self.assertFalse(row['semantic_gold'])
        enough = alias_capacity(sentences('ńańi.'), sa, [{'fl_index': 0, 'source_index': 0}])[0]
        self.assertEqual(enough['status'], 'capacity_only_not_confirmation')

    def test_diagnostic_blend_matches_actual_cache(self):
        fa, sa = sentences('ńańi tawwdan ńańi, foo.'), sentences('of that other, word. Next.')
        ps, _ = predictions(fa, {}, CFG['lexicon_rules'], 'gated_aliases')
        prep = PreparedSource(sa, [(0,), (1,)])
        d = components(make_block(fa, (0,)), make_block(sa, (0,)), CFG, ps, (0,))
        self.assertAlmostEqual(d['similarity'], ScoreCache(fa, prep, CFG, ps).row((0,), 1, 'lexical')[0])
        self.assertEqual((d['predictions'], d['multiset_overlap']), (3, 2))
        self.assertEqual(next(x for x in d['prediction_capacity'] if x['word'] == 'of')['unmatched'], 1)

    def test_reference_guided_paths_remain_hypotheses_and_aliases_marked(self):
        ft, st = 'ńańi tawwdan ńańi.', 'of that of.'
        fa, sa = sentences(ft), sentences(st)
        ps, _ = predictions(fa, {}, CFG['lexicon_rules'], 'gated_aliases')
        d = audit(fa, sa, ft, st, [{'fl_index': 0, 'source_index': 0}], [(0,)], [(0,)], ps, CFG)
        row = d['reference_proposals'][0]
        self.assertFalse(row['token_hypotheses_used_by_retrieval'])
        self.assertFalse(row['semantic_gold'])
        self.assertTrue(all(p['basis'] == 'experimental_alias' for p in row['reference_guided_token_hypotheses']))
        self.assertEqual(len({tuple(p['source_span']) for p in row['reference_guided_token_hypotheses']}), 3)

    def test_reference_block_respects_abbreviation_group(self):
        ft, st = 'unknown word.', 'A medium e.g. an organism.'
        fa, sa = sentences(ft), sentences(st)
        ps, _ = predictions(fa, {}, CFG['lexicon_rules'], 'baseline')
        su = protected_groups(sa, st, CFG['abbreviations'])
        self.assertEqual(su, [(0, 1)])
        ref = [{'fl_index': 0, 'source_index': i} for i in range(2)]
        row = audit(fa, sa, ft, st, ref, [(0,)], su, ps, CFG)['reference_proposals'][0]
        self.assertTrue(row['proposal_feasible'])
        self.assertEqual(row['source_effective_units'], 1)
        self.assertEqual(row['source_atoms'], [0, 1])


if __name__ == '__main__':
    unittest.main()
