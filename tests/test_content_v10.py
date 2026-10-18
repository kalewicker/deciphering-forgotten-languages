import json
from itertools import combinations, product
from pathlib import Path
import unittest

from fl_decipher.content_v10 import CONTENT_FORMS, evidence, lcs_length, mode_quality, apply_mode
from fl_decipher.register_v5 import predictions
from fl_decipher.synthetic_v10 import generate, CONDITIONS
from fl_decipher.text import sentences

ROOT = Path(__file__).resolve().parents[1]
CFG = json.loads((ROOT/'experiments/kamri_coverage_v9.json').read_text())
LEX = json.loads((ROOT/CFG['lexicon_path']).read_text())


class ContentTests(unittest.TestCase):
    def test_lcs_matches_exhaustive_subsequences(self):
        def subsequences(a):
            return {tuple(a[i] for i in ids) for n in range(len(a)+1) for ids in combinations(range(len(a)), n)}
        for a in product(['world', 'lord'], repeat=3):
            for b in product(['world', 'lord'], repeat=3):
                self.assertEqual(lcs_length(a, b), max(map(len, subsequences(a) & subsequences(b))))
        self.assertEqual(lcs_length([], ['world']), 0)

    def test_roster_is_eligible_without_dictionary_changes(self):
        fa = sentences(' '.join(CONTENT_FORMS.values())+'.')
        ps, gate = predictions(fa, LEX, CFG['lexicon_rules'], CFG['prediction_variant'])
        self.assertEqual([p['prediction'] for p in ps[0]], list(CONTENT_FORMS))
        self.assertTrue(all(p['origin'] == 'frozen_v1' for p in ps[0]))
        self.assertFalse(gate['active'])

    def test_no_content_evidence_gives_zero_despite_positional_agreement(self):
        fa, sa = sentences('şu z aš y.'), sentences('the unrelated and words.')
        ps, _ = predictions(fa, LEX, CFG['lexicon_rules'], CFG['prediction_variant'])
        a = {'blocks': [{'fl_atoms': [0], 'source_atoms': [0]}], 'strength': .3}
        e = evidence(a, fa, sa, ps, CFG)
        self.assertEqual(mode_quality(e, 'positional'), 1.)
        self.assertEqual(mode_quality(e, 'content_bag'), 0.)
        self.assertEqual(mode_quality(e, 'content_order'), 0.)

    def test_content_sequence_order_is_separate_from_bag(self):
        fa = sentences('warċa mirnaķ misndin.')
        ps, _ = predictions(fa, LEX, CFG['lexicon_rules'], CFG['prediction_variant'])
        a = {'blocks': [{'fl_atoms': [0], 'source_atoms': [0]}], 'strength': .3, 'edges': []}
        e = evidence(a, fa, sentences('lord made world.'), ps, CFG)
        self.assertEqual(mode_quality(e, 'content_bag'), 1.)
        self.assertEqual(mode_quality(e, 'content_order'), 2/3)
        out = apply_mode(a, e, 'content_order')
        self.assertAlmostEqual(out['strength'], .2)
        self.assertEqual(out['edges'], a['edges'])
        self.assertEqual(out['blocks'], a['blocks'])

    def test_single_content_word_cannot_locate_itself_among_unknowns(self):
        fa = sentences('z warċa y.')
        ps, _ = predictions(fa, LEX, CFG['lexicon_rules'], CFG['prediction_variant'])
        a = {'blocks': [{'fl_atoms': [0], 'source_atoms': [0]}]}
        for text in ['world other words.', 'other words world.']:
            e = evidence(a, fa, sentences(text), ps, CFG)
            self.assertEqual(mode_quality(e, 'content_order'), 1.)

    def test_partial_scoring_uses_covered_roster_predictions_only(self):
        fa = sentences('warċa. mirnaķ.')
        ps, _ = predictions(fa, LEX, CFG['lexicon_rules'], CFG['prediction_variant'])
        e = evidence({'blocks': [{'fl_atoms': [0], 'source_atoms': [0]}]}, fa, sentences('world.'), ps, CFG)
        self.assertEqual(e['content']['covered_content_predictions'], 1)
        self.assertEqual(e['content']['total_query_content_predictions'], 2)
        self.assertEqual(mode_quality(e, 'content_order'), 1.)

    def test_content_matches_do_not_cross_selected_block_boundaries(self):
        fa, sa = sentences('warċa. mirnaķ.'), sentences('lord. world.')
        ps, _ = predictions(fa, LEX, CFG['lexicon_rules'], CFG['prediction_variant'])
        e = evidence({'blocks': [{'fl_atoms': [i], 'source_atoms': [i]} for i in range(2)]}, fa, sa, ps, CFG)
        self.assertEqual(e['content']['bag_matches'], 0)
        self.assertEqual(e['content']['ordered_matches'], 0)

    def test_all_conditions_have_fixed_density_and_shared_candidate_position(self):
        answers = set()
        for c in CONDITIONS:
            p = generate(109001, **c, lexicon=LEX); answers.add(p['answer_index'])
            self.assertEqual(len(set(p['candidate_texts'])), 4)
            ps, gate = predictions(sentences(p['fl_text']), LEX, CFG['lexicon_rules'], CFG['prediction_variant'])
            self.assertEqual(sum(x['prediction'] in CONTENT_FORMS for row in ps for x in row), 6*c['density'])
            self.assertEqual(sum(x['prediction'] is not None for row in ps for x in row), 12+6*c['density'])
            self.assertFalse(gate['active'])
            self.assertEqual(len(p['edges']), 6 if c['extent'] == 'full' else 3)
            self.assertEqual({x['uid'] for x in p['fl_token_ids']}, {x['uid'] for x in p['token_pairs']} | set(p['unavailable_query_uids']))
        self.assertEqual(len(answers), 1)

    def test_unknown_renaming_preserves_content_evidence(self):
        p = generate(109001, 3, 'full', 'unknown_renamed', LEX)
        fa = sentences(p['fl_text']); ps, _ = predictions(fa, LEX, CFG['lexicon_rules'], CFG['prediction_variant'])
        a = {'blocks': [{'fl_atoms': [i], 'source_atoms': [i]} for i in range(6)]}
        for text in p['candidate_texts']:
            e = evidence(a, fa, sentences(text), ps, CFG)
            self.assertEqual(mode_quality(e, 'content_bag'), 1.)
            self.assertEqual(mode_quality(e, 'content_order'), 1.)

    def test_content_renaming_removes_roster_matches(self):
        p = generate(109001, 3, 'full', 'content_renamed', LEX)
        for i, text in enumerate(p['candidate_texts']):
            words = [t.normalized for a in sentences(text) for t in a.tokens]
            self.assertEqual(sum(w in CONTENT_FORMS for w in words), 18 if i == p['answer_index'] else 0)


if __name__ == '__main__':
    unittest.main()
