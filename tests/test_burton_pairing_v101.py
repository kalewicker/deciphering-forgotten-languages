import unittest

from scripts.burton_pairing_v101 import features, fold_plan, score_fold, shuffled_right, tokens


class BurtonPairingTests(unittest.TestCase):
    def test_fold_withholds_both_sides_and_duplicate_representations(self):
        rows = [{"ordinal": i, "excerpt": group, "yid": left.split(),
                 "english": right.split(), "key": str(i)}
                for i, group, left, right in [
                    (2, 0, "a", "one"), (3, 0, "b", "two"),
                    (4, 1, "a", "other"), (5, 1, "c", "two"),
                    (6, 1, "d", "three"), (7, 1, "e", "four"),
                ]]
        plan = fold_plan(rows)[0]
        self.assertEqual(plan["candidates"], [2, 3])
        self.assertEqual(plan["training"], [6, 7])
        indexed = {row["ordinal"]: row for row in rows}
        result = score_fold(indexed, plan)
        self.assertIsNone(result["observed"])
        self.assertIsNone(result["length"])
        self.assertIsNone(result["shuffled"])

    def test_control_preserves_excerpt_marginals_and_input(self):
        training = [{"excerpt": i % 2} for i in range(8)]
        right = [{i} for i in range(8)]
        permutations = [shuffled_right(training, right, 2, i) for i in range(20)]
        self.assertTrue(any(p != right for p in permutations))
        for permuted in permutations:
            for excerpt in (0, 1):
                self.assertCountEqual(permuted[excerpt::2], right[excerpt::2])
        self.assertEqual(right, [{i} for i in range(8)])

    def test_mask_and_minimum_support(self):
        self.assertEqual(tokens("Naïve—123 ՄԵԿ"), ["naïve", "մեկ"])
        query, candidates = features(["մեկ", "name", "rare"], [["name", "a"], ["b"]],
                                     [{"մեկ", "rare"}, {"մեկ", "name"}],
                                     [{"name", "a"}, {"b"}])
        self.assertEqual(query, {"մեկ"})
        self.assertEqual(candidates, [{"a"}, {"b"}])
