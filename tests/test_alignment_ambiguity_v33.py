import copy
import importlib.util
from itertools import product
from math import comb
from pathlib import Path
import unittest

from fl_decipher.alignment_ambiguity_v33 import audit_pair, assess, summarize
from fl_decipher.synthetic_transfer_v32 import align

SPEC = importlib.util.spec_from_file_location('ambiguity_reference', Path(__file__).resolve().parents[1] / 'scripts/verify_alignment_ambiguity_v33.py')
REF = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(REF)


def fixture(left, right):
    decoded = [{'source_form': f} for f in left]
    q = {'tokens': [{} for _ in left]}
    c = {'tokens': [{'form': f or 'barrier', 'blocked': f is None} for f in right]}
    original = align(q, c, decoded)
    return decoded, c['tokens'], original


def brute_paths(left, right, forbidden=None):
    """Enumerate all legal operation sequences, without DP or path counting."""
    paths = []
    def visit(i, j, cost, matches):
        if i == len(left) and j == len(right):
            paths.append((cost, frozenset(matches))); return
        if i < len(left): visit(i+1, j, cost+1, matches)
        if j < len(right): visit(i, j+1, cost+1, matches)
        if i < len(left) and j < len(right) and left[i] is not None and left[i] == right[j] and (i, j) != forbidden:
            visit(i+1, j+1, cost, matches + [(i, j)])
    visit(0, 0, 0, [])
    best = min(c for c, _ in paths)
    return best, [s for c, s in paths if c == best]


class AlignmentAmbiguityTests(unittest.TestCase):
    def check_pair(self, left, right):
        d, c, p = fixture(left, right)
        actual = audit_pair(d, c, p)
        self.assertEqual(actual, REF.reference_pair(left, right, p))
        return actual

    def test_exhaustive_optimal_paths_and_token_ledgers(self):
        sequences = [list(s) for n in range(4) for s in product(['a', 'b', None], repeat=n)]
        for left in sequences:
            for right in sequences:
                a = self.check_pair(left, right); cost, paths = brute_paths(left, right)
                possible = set().union(*paths); forced = set(paths[0]).intersection(*paths)
                self.assertEqual(a['edit_cost'], cost)
                self.assertEqual(a['optimal_operation_paths'], len(paths))
                self.assertEqual(set(map(tuple, a['forced_matches'])), forced)
                self.assertEqual({(e['query_index'], e['candidate_index']) for e in a['possible_matches']}, possible)
                for e in a['possible_matches']:
                    self.assertEqual(e['through_paths'], sum((e['query_index'], e['candidate_index']) in s for s in paths))
                for side, tokens in enumerate((a['query_tokens'], a['candidate_tokens'])):
                    for t in tokens:
                        self.assertEqual(t['gap_on_some_optimum'], any(all(e[side] != t['token_index'] for e in s) for s in paths))

    def test_deleting_a_forced_edge_reduces_the_optimum(self):
        left, right = ['a', 'b', 'a'], ['a', 'b', 'b', 'a']
        a = self.check_pair(left, right)
        for e in a['possible_matches']:
            changed, _ = brute_paths(left, right, (e['query_index'], e['candidate_index']))
            self.assertEqual(changed > a['edit_cost'], e['forced'])

    def test_gap_multiplicity_without_matched_pair_ambiguity(self):
        a = self.check_pair(['a', None], ['a', None])
        self.assertEqual(a['optimal_operation_paths'], 2)
        self.assertTrue(a['gap_order_only_multiplicity'])
        self.assertFalse(a['matched_pair_ambiguity'])
        self.assertEqual(a['forced_matches'], [[0, 0]])

    def test_all_gap_counts_and_no_vacuous_position_matches(self):
        a = self.check_pair([None] * 3, ['a'] * 4)
        self.assertEqual(a['optimal_operation_paths'], comb(7, 3))
        self.assertEqual(a['forced_matches'], [])
        self.assertTrue(all(t['status'] == 'always_gap' for t in a['query_tokens'] + a['candidate_tokens']))

    def test_always_matched_token_can_have_ambiguous_partner(self):
        a = self.check_pair(['a'], ['a', 'a'])
        self.assertEqual(a['query_tokens'][0]['status'], 'ambiguous_partner')
        self.assertEqual(a['query_tokens'][0]['possible_partners'], [0, 1])
        self.assertFalse(a['query_tokens'][0]['gap_on_some_optimum'])
        self.assertEqual(a['forced_matches'], [])

    def test_optional_match_or_gap_is_explicit(self):
        a = self.check_pair(['a', 'a'], ['a'])
        self.assertEqual([t['status'] for t in a['query_tokens']], ['optional_match_or_gap'] * 2)

    def test_empty_sequences_are_retained(self):
        for left, right in [([], []), ([], ['a']), (['a'], [])]:
            a = self.check_pair(left, right)
            self.assertEqual(a['forced_matches'], [])
            self.assertEqual(len(a['query_tokens']), len(left))
            self.assertEqual(len(a['candidate_tokens']), len(right))

    def test_blocked_candidate_does_not_match_even_equal_surface(self):
        d, c, p = fixture(['a'], [None])
        c[0]['form'] = 'a'
        a = audit_pair(d, c, p)
        self.assertEqual(a['possible_matches'], [])

    def test_frozen_optimum_corruption_is_rejected(self):
        d, c, p = fixture(['a'], ['a'])
        for field in ['edit_cost', 'optimal_operation_paths', 'matched_tokens']:
            bad = copy.deepcopy(p); bad[field] += 1
            with self.assertRaises(AssertionError): audit_pair(d, c, bad)

    def test_frozen_trace_corruption_is_rejected(self):
        d, c, p = fixture(['a', 'b'], ['a', 'b'])
        p['trace'] = [[0, 1], [1, 0]]
        with self.assertRaises(AssertionError): audit_pair(d, c, p)

    def test_forced_matches_can_have_wrong_origins(self):
        a = self.check_pair(['a', 'a', 'b'], ['a', 'a', 'b']); a['original_qualifies'] = True
        result = {'pairs': {'q::p': a}}
        oracle = {'bases': [{'base_id': 'b', 'view_ids': {'parent': 'p'}}],
                  'queries': [{'query_view_id': 'q', 'base_id': 'b', 'group': 'seen', 'mechanism': 'reordering', 'origins': [1, 0, 2]}]}
        assessed = assess(result, oracle)
        self.assertEqual(assessed, REF.reference_assessment(result['pairs'], oracle))
        self.assertEqual(assessed['primary_summary']['forced_precision'], [1, 3])
        self.assertFalse(assessed['synthetic_hypothesis']['passed'])
        self.assertEqual(assessed['primary_summary']['wrong_retained'], 2)
        self.assertTrue(all(not d['origin_edge_possible'] for d in assessed['origin_disagreements']))

    def test_empty_primary_set_fails_nonvacuity_requirement(self):
        a = self.check_pair(['a'], ['a']); a['original_qualifies'] = False
        oracle = {'bases': [{'base_id': 'b', 'view_ids': {'parent': 'p'}}],
                  'queries': [{'query_view_id': 'q', 'base_id': 'b', 'group': 'seen', 'mechanism': 'bijective', 'origins': [0]}]}
        assessed = assess({'pairs': {'q::p': a}}, oracle)
        self.assertFalse(assessed['synthetic_hypothesis']['passed'])
        self.assertEqual(assessed['primary_summary']['forced_precision'], [0, 0])

    def test_zero_denominators_are_explicit(self):
        empty = summarize([])
        self.assertEqual(empty, REF.aggregate([]))
        self.assertEqual(empty['forced_precision'], [0, 0])
        self.assertEqual(empty['retained_fraction_of_query_tokens'], [0, 0])


if __name__ == '__main__': unittest.main()
