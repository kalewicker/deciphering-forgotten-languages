import json
from pathlib import Path
import unittest

from fl_decipher.experiment_v4 import aggregate, metrics
from fl_decipher.lexicon import predict
from fl_decipher.passage_v3 import PreparedSource, ScoreCache, align as v3_align, protected_groups
from fl_decipher.precision_v4 import admission, align, block_reward, decode, gap_cost, token_path
from fl_decipher.synthetic_v4 import FAMILIES, FUNCTION_FORMS, generate
from fl_decipher.text import sentences, tokens

ROOT = Path(__file__).resolve().parents[1]
CFG = json.loads((ROOT/'experiments/kamri_passage_v3a.json').read_text()) | {
    'reference_tokens': 20, 'token_gap': -.75, 'token_exact': 2., 'token_mismatch': -2.,
    'token_unknown': .5, 'edge_minimum_pairs': 2}


class PrecisionTests(unittest.TestCase):
    def test_identical_span_reward_invariance(self):
        self.assertNotEqual(block_reward(.85, 1, 2, 12, 12, CFG, 'effective'),
                            block_reward(.85, 1, 1, 12, 12, CFG, 'effective'))
        for f, s in [(12, 12), (41, 53), (1, 2)]:
            self.assertEqual(block_reward(.85, 1, 2, f, s, CFG, 'tokens'),
                             block_reward(.85, 1, 1, f, s, CFG, 'tokens'))
        self.assertAlmostEqual(gap_cost(12, CFG, 'tokens'), gap_cost(5, CFG, 'tokens')+gap_cost(7, CFG, 'tokens'))

    def test_effective_reproduces_v3(self):
        fa, sa = sentences('şa xa şa. xa xa.'), sentences('the apple the. apple apple.')
        units = [(0,), (1,)]
        ps = [[{'prediction': 'the' if t.normalized == 'şa' else None} for t in s.tokens] for s in fa]
        source = PreparedSource(sa, units)
        cache = ScoreCache(fa, source, CFG, ps)
        self.assertEqual(align(units, source, cache, CFG, 'effective'),
                         v3_align(units, source, cache, CFG, max_block=2, scoring='lexical'))

    def test_merged_block_excludes_cross_edges(self):
        fa, sa = sentences('xa xb. xc xd.'), sentences('one two. three four.')
        ps = [[{'prediction': None} for t in s.tokens] for s in fa]
        block = {'fl_atoms': [0, 1], 'source_atoms': [0, 1]}
        a = {'blocks': [block], 'edges': [{'fl_index': f, 'source_index': s} for f in range(2) for s in range(2)],
             'strength': .1, 'linked_fl_atoms': 2, 'minimum_links_met': False}
        decoded = decode(a, fa, sa, ps, CFG, 'ordered')
        self.assertEqual(decoded['edges'], [{'fl_index': 0, 'source_index': 0}, {'fl_index': 1, 'source_index': 1}])
        self.assertEqual(len(decoded['token_pairs']), 4)
        self.assertEqual(len(a['edges']), 4)
        self.assertIsNone(decode(a, fa, sa, ps, CFG, 'cartesian')['token_pairs'])

    def test_known_insertion_and_deletion(self):
        fa = tokens('xa xb xc')
        items = [(0, t, meaning) for t, meaning in zip(fa, ['one', 'two', 'three'], strict=True)]
        for source in ['one inserted two three', 'one three']:
            pairs = token_path(items, [(0, t) for t in tokens(source)], CFG)
            self.assertTrue(all(p['basis'] == 'frozen_anchor' for p in pairs))
            for pair in pairs:
                f = next(t for t in fa if [t.start, t.end] == pair['fl_span'])
                meaning = dict(zip([t.surface for t in fa], ['one', 'two', 'three']))[f.surface]
                self.assertEqual(source[slice(*pair['source_span'])], meaning)
            self.assertEqual(len(pairs), 3 if 'inserted' in source else 2)

    def test_mismatch_abstains_and_single_unknown_does_not_emit(self):
        f, s = tokens('xa'), tokens('other')
        self.assertEqual(token_path([(0, f[0], 'one')], [(0, s[0])], CFG), [])
        a = {'blocks': [{'fl_atoms': [0], 'source_atoms': [0]}], 'strength': 1., 'edges': []}
        result = decode(a, sentences('xa.'), sentences('other.'), [[{'prediction': None}]], CFG, 'ordered')
        self.assertEqual(result['edges'], [])
        self.assertEqual(len(result['token_pairs']), 1)
        self.assertFalse(result['minimum_links_met'])

    def test_unique_margin_and_denominator_metrics(self):
        top = {'strength': .8, 'minimum_links_met': True}
        self.assertFalse(admission(top, 0., .7))
        self.assertTrue(admission(top, .1, .7))
        top['minimum_links_met'] = False
        self.assertFalse(admission(top, .1, .7))
        counts = metrics([{'fl_index': 0, 'source_index': 0}],
                         [{'fl_index': 0, 'source_index': 0}, {'fl_index': 1, 'source_index': 1}], False)
        self.assertEqual((counts['correct'], counts['proposed'], counts['reference']), (0, 1, 2))

    def test_generator_truth_and_function_eligibility(self):
        lexicon = json.loads((ROOT/CFG['lexicon_path']).read_text())
        for meaning, form in FUNCTION_FORMS.items():
            self.assertEqual(predict(sentences(form+'.')[0], lexicon, CFG['lexicon_rules'])[0]['prediction'], meaning)
        for index, family in enumerate(FAMILIES):
            # Development-only seeds, outside both registered panels.
            packet = generate(1001+index, family, lexicon)
            self.assertEqual(packet, generate(1001+index, family, lexicon))
            fa = sentences(packet['fl_text'])
            sa = sentences(packet['candidate_texts'][packet['answer_index']])
            pairs = packet['token_pairs']
            self.assertEqual(len(pairs), 29 if family == 'deletion' else 30)
            self.assertEqual({(p['fl_index'], p['source_index']) for p in pairs},
                             {(e['fl_index'], e['source_index']) for e in packet['edges']})
            for p in pairs:
                self.assertTrue(any([t.start, t.end] == p['fl_span'] for t in fa[p['fl_index']].tokens))
                self.assertTrue(any([t.start, t.end] == p['source_span'] for t in sa[p['source_index']].tokens))
            if family == 'abbreviation':
                self.assertLess(len(protected_groups(sa, packet['candidate_texts'][packet['answer_index']], CFG['abbreviations'])), len(sa))
            if family == 'sparse_anchors':
                self.assertTrue(all(p['prediction'] is None for s in fa for p in predict(s, lexicon, CFG['lexicon_rules'])))
            self.assertTrue(all(form not in lexicon for word, form in packet['substitution_key'].items() if word not in FUNCTION_FORMS))


if __name__ == '__main__':
    unittest.main()
