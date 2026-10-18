import copy
import importlib.util
from itertools import product
from pathlib import Path
import unittest

from fl_decipher.positional_worlds_v34 import prepare, predict, assess, score, canonical
from fl_decipher.synthetic_transfer_v32 import view

SPEC = importlib.util.spec_from_file_location('positional_reference', Path(__file__).resolve().parents[1] / 'scripts/verify_positional_worlds_v34.py')
REF = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(REF)


def fixtures():
    sources = [['symbol0', 'symbol0', 'symbol1', 'copiedanchor0', 'symbol2', 'symbol1'],
               ['symbol0', 'symbol1', 'symbol0', 'symbol2', 'symbol2', 'symbol0']]
    model = {'entries': {f'a{i}': {'source_form': f'symbol{i}'} for i in range(3)}, 'ledger': {}}
    public = {'views': {}}; gold = {'bases': [], 'queries': []}
    for passage, source in enumerate(sources):
        sid, qid, bid = f's{passage}', f'q{passage}', f'b{passage}'
        query = [s if s.startswith('copiedanchor') else 'a' + s[6:] for s in source]
        public['views'][sid] = view(source); public['views'][qid] = view(query)
        gold['bases'].append({'base_id': bid, 'view_ids': {'parent': sid}})
        gold['queries'].append({'query_view_id': qid, 'base_id': bid, 'key': 11, 'group': 'seen', 'mechanism': 'bijective', 'passage': passage})
    cfg = {'key': 11, 'group': 'seen', 'query_mechanism': 'bijective', 'passages': [0, 1], 'source_length': 6, 'site_denominator': 10}
    return public, gold, model, cfg


class PositionalWorldTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.old_public, cls.old_gold, cls.model, cls.cfg = fixtures()
        cls.public, cls.oracle = prepare(cls.old_public, cls.old_gold, cls.model, cls.cfg)
        cls.predictions = predict(cls.public, cls.model)
        cls.assessment = assess(cls.public, cls.oracle, cls.predictions)

    def test_independent_full_fixture_reconstruction(self):
        self.assertEqual((self.public, self.oracle), REF.reference_prepare(self.old_public, self.old_gold, self.model, self.cfg))
        self.assertEqual(len(self.oracle['sites']), 10)

    def test_invisible_equal_swap_has_same_input_and_different_origins(self):
        s = next(s for s in self.oracle['sites'] if s['symbol_relation'] == 'equal')
        a, b = s['worlds']
        self.assertEqual(a['observation_id'], b['observation_id'])
        self.assertNotEqual(a['origins'], b['origins'])
        self.assertEqual(self.predictions['predictions'][a['observation_id']], self.predictions['predictions'][b['observation_id']])

    def test_unequal_swap_changes_public_query_bytes(self):
        for s in self.oracle['sites']:
            if s['symbol_relation'] != 'unequal': continue
            a, b = [self.public['observations'][w['observation_id']] for w in s['worlds']]
            self.assertEqual(a['source'], b['source'])
            self.assertNotEqual(canonical(a), canonical(b))
            indices = [i for i in range(6) if a['query']['tokens'][i]['form'] != b['query']['tokens'][i]['form']]
            self.assertEqual(indices, [s['left_index'], s['left_index']+1])

    def test_balanced_bound_for_every_deterministic_point_answer_with_abstention(self):
        s = next(s for s in self.oracle['sites'] if s['symbol_relation'] == 'equal')
        positions = [s['left_index'], s['left_index']+1]
        for returns in product([None] + list(range(6)), repeat=2):
            emitted = 2 * sum(j is not None for j in returns)
            exact = sum(j is not None and w['origins'][i] == j for w in s['worlds'] for i, j in zip(positions, returns))
            self.assertLessEqual(2 * exact, emitted)
        c = next(c for c in self.assessment['certificates'] if c['site_id'] == s['site_id'])['balanced_point_bound']
        self.assertEqual((c['maximum_exact_calls'], c['fully_answered_calls']), (2, 4))

    def test_union_is_set_coverage_not_a_point_prediction(self):
        c = next(c for c in self.assessment['certificates'] if c['symbol_relation'] == 'equal')['balanced_point_bound']
        self.assertFalse(c['oracle_union_is_predictor_output'])
        self.assertEqual(c['oracle_union_set_coverage'], [4, 4])
        self.assertTrue(all(len(p['set_valued_origin_union']) == 2 for p in c['positions']))
        self.assertTrue(all(all(o in p['set_valued_origin_union'] for o in p['origins_by_world']) for p in c['positions']))

    def test_barrier_and_unmapped_sites_stay_in_inventory(self):
        excluded = [s for s in self.oracle['sites'] if not s['eligible']]
        self.assertEqual(len(excluded), 2)
        self.assertTrue(all(s['worlds'] == [] and 'blocked_endpoint' in s['exclusion_reasons'] for s in excluded))
        model = copy.deepcopy(self.model); del model['entries']['a2']
        public, gold = prepare(self.old_public, self.old_gold, model, self.cfg)
        self.assertEqual((public, gold), REF.reference_prepare(self.old_public, self.old_gold, model, self.cfg))
        self.assertEqual(len(gold['sites']), 10)
        self.assertGreater(sum(not s['eligible'] for s in gold['sites']), 2)

    def test_content_reuse_preserves_every_world_denominator(self):
        inventory = self.assessment['site_inventory']
        self.assertEqual(inventory['worlds'], 2*inventory['eligible_sites'])
        self.assertLess(inventory['unique_public_observations'], inventory['worlds'])
        self.assertEqual(self.assessment['all_worlds']['forced']['affected']['tokens'], 2*inventory['worlds'])
        self.assertEqual({w['observation_id'] for s in self.oracle['sites'] for w in s['worlds']}, set(self.public['observations']))

    def test_wrong_origin_can_still_be_symbol_compatible(self):
        s = score([[0, 0], [1, 1]], [1, 0], view(['symbol0', 'symbol0']), [0, 1])
        self.assertEqual(s['strict_precision'], [0, 2])
        self.assertEqual(s['symbol_compatibility'], [2, 2])

    def test_complete_independent_predictor_and_score_replay(self):
        self.assertEqual(self.predictions, REF.reference_predict(self.public, self.model))
        self.assertEqual(self.assessment, REF.reference_assess(self.public, self.oracle, self.predictions))
        self.assertTrue(self.assessment['identifiability_demonstration']['passed'])

    def test_no_mutation_or_oracle_metadata_in_predictor(self):
        public, model = copy.deepcopy(self.public), copy.deepcopy(self.model)
        before = copy.deepcopy((public, model))
        predict(public, model)
        self.assertEqual((public, model), before)
        for obs in public['observations'].values(): self.assertEqual(set(obs), {'source', 'query'})
        next(iter(public['observations'].values()))['world'] = 'swap'
        with self.assertRaises(AssertionError): predict(public, model)

    def test_observation_order_does_not_supply_a_hidden_world_label(self):
        reverse = {'observations': dict(reversed(list(self.public['observations'].items())))}
        self.assertEqual(predict(reverse, self.model), self.predictions)

    def test_no_eligible_sites_keeps_zero_denominators_and_fails_nonvacuity(self):
        model = {'entries': {}, 'ledger': {}}
        public, oracle = prepare(self.old_public, self.old_gold, model, self.cfg)
        a = assess(public, oracle, predict(public, model))
        self.assertEqual(a, REF.reference_assess(public, oracle, REF.reference_predict(public, model)))
        self.assertEqual(a['site_inventory']['sites'], 10)
        self.assertFalse(a['identifiability_demonstration']['passed'])
        self.assertFalse(a['unequal_swap_forced_safety_hypothesis']['passed'])
        self.assertEqual(a['all_worlds']['forced']['affected']['strict_precision'], [0, 0])


if __name__ == '__main__': unittest.main()
