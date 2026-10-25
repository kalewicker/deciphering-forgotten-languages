import unittest
from fl_decipher.sequence_overlap_v88 import segments, matches, coverage, aggregate, macro


def unit(uid, forms, blocked=(), breaks=()):
    return {'uid': uid, 'tokens': [
        {'form': w, 'blocked': i in blocked,
         'pair_from_previous': i > 0 and i not in blocked and i-1 not in blocked and i not in breaks}
        for i, w in enumerate(forms)]}


def row(gain, lengths):
    return {'gain': gain, 'changed': gain != 0, 'covered_lengths': lengths,
            'max_covered_length': max(lengths, default=0)}


class OverlapTests(unittest.TestCase):
    def test_barriers_and_explicit_breaks(self):
        r = unit('a', list('abcdef'), blocked=(2,), breaks=(5,))
        self.assertEqual(segments(r), [[0, 1], [3, 4], [5]])
        self.assertEqual([m['evaluation_indices'] for m in matches([r], [unit('b', list('bcde'))])], [[3, 4]])

    def test_pair_must_be_wholly_inside_window(self):
        c = coverage(matches([unit('a', list('xabcy'))], [unit('b', list('abc'))]))
        self.assertEqual(c['a', 1, 2], {2, 3})
        self.assertEqual(c['a', 2, 3], {2, 3})
        self.assertNotIn(('a', 0, 1), c)
        self.assertNotIn(('a', 3, 4), c)

    def test_all_occurrences_and_eight_token_cap(self):
        m = matches([unit('a', ['x']*10)], [unit('b', ['x']*10), unit('c', ['x']*10)])
        self.assertEqual(len(m), 2*sum((11-k)**2 for k in range(2, 9)))
        self.assertEqual(max(x['length'] for x in m), 8)

    def test_forms_are_exact_not_unknown_categories(self):
        self.assertFalse(matches([unit('a', ['new1', 'new2'])], [unit('b', ['new3', 'new4'])]))
        self.assertFalse(matches([unit('a', ['X', 'y'])], [unit('b', ['x', 'y'])]))

    def test_partitions_preserve_negative_and_zero_gains(self):
        a = aggregate([row(2, [2, 3]), row(-1, [2]), row(0, [])])
        self.assertAlmostEqual(a['total']['contribution'], 1/3)
        self.assertEqual(a['lengths']['3']['covered']['positive_gain_sum'], 2)
        self.assertEqual(a['lengths']['3']['uncovered']['negative_gain_sum'], -1)
        self.assertIsNone(a['max_bins']['8']['mean_gain'])
        self.assertAlmostEqual(sum(x['contribution'] for x in a['max_bins'].values()), 1/3)

    def test_macro_uses_all_original_group_denominators(self):
        m = macro([aggregate([row(2, [2])]), aggregate([row(-1, [])]*9)])
        self.assertEqual(m['total']['contribution'], .5)
        self.assertEqual(m['lengths']['2']['covered']['contribution'], 1)
        self.assertEqual(m['lengths']['2']['uncovered']['contribution'], -.5)
        self.assertEqual(m['lengths']['2']['positive_mass_fraction_covered'], 1)
        self.assertIsNone(macro([aggregate([row(0, [])])])['lengths']['2']['positive_mass_fraction_covered'])


if __name__ == '__main__':
    unittest.main()
