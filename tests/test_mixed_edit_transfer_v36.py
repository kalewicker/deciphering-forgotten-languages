"""Small accounting checks; no registered v36 passage generation or scoring."""
import unittest
from copy import deepcopy

from fl_decipher.mixed_edit_transfer_v36 import query, model_variants, metrics, PROFILES
from fl_decipher.synthetic_transfer_v32 import alias, view


class MixedEditAccountingTests(unittest.TestCase):
    def setUp(self):
        # Handcrafted arithmetic fixture, unrelated to the registered hash generator.
        self.source = [f'symbol{i % 24}' for i in range(72)]
        for i, label in zip([17, 35, 53], range(3), strict=True):
            self.source[i] = f'copiedanchor{label}'

    def test_full_token_and_lineage_denominators(self):
        for profile, (deleted, unknown, swaps, inserted) in PROFILES.items():
            forms, edits = query(self.source, 11, 99, profile)
            self.assertEqual(len(forms), 72)
            self.assertEqual(len(view(forms)['tokens']), 72)
            self.assertEqual(sum(o is None for o in edits['origins']), len(inserted))
            self.assertEqual(set(o for o in edits['origins'] if o is not None), set(range(72))-set(deleted))
            self.assertEqual(len(set(o for o in edits['origins'] if o is not None)), 72-len(deleted))

    def test_insertions_are_not_assigned_origins(self):
        forms, edits = query(self.source, 11, 99, 'light')
        for i, origin in enumerate(edits['origins']):
            if origin is None:
                self.assertTrue(forms[i].startswith('v36insert'))
            elif origin in (10, 30):
                self.assertEqual(forms[i], alias(11, int(self.source[origin][6:]), 1))

    def test_swap_and_block_reversal_order(self):
        _, light = query(self.source, 11, 99, 'light')
        origins = [o for o in light['origins'] if o is not None]
        self.assertEqual(origins[origins.index(13)+1], 12)
        _, block = query(self.source, 11, 99, 'block_mismatch')
        originals = [o for o in block['origins'] if o is not None]
        self.assertEqual(originals[originals.index(45):originals.index(38)+1], [45, 44, 43, 42, 40, 41, 39, 38])

    def test_sparse_dense_interventions_do_not_change_original(self):
        original = {'entries': {alias(k, s): {'source_form': f'symbol{s}', 'support_units': ['fixture']}
                                for k in (11, 29, 47, 83) for s in range(24)}, 'ledger': {'fixture': 'original'}}
        before = deepcopy(original)
        variants, changes = model_variants(original, [11, 29, 47, 83])
        self.assertEqual(original, before)
        self.assertEqual(variants['clean'], original)
        self.assertEqual([len(changes[b]) for b in ('sparse', 'dense')], [8, 32])
        self.assertEqual(variants['dense']['entries'][alias(11, 7)]['source_form'], 'symbol0')
        self.assertEqual(variants['sparse']['ledger'], original['ledger'])

    def test_origin_and_symbol_truth_are_separate(self):
        got = metrics([[0, 1], [1, 0], [2, 2]], [0, 1, None], ['a', 'a', 'b'], [0, 1, 2, 3])
        self.assertEqual(got, {'denominator': 4, 'returned': 3, 'origin_exact': 0, 'origin_wrong': 3,
                              'true_symbol_compatible': 2, 'true_symbol_wrong': 1, 'unmatched': 1})

    def test_scope_denominator_retains_abstentions(self):
        self.assertEqual(metrics([], [0, 1, 2], ['a', 'b', 'c'], [0, 1, 2])['unmatched'], 3)


if __name__ == '__main__':
    unittest.main()
