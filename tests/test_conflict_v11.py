"""Development-only fixtures for occurrence-preserving conflicts and threat controls."""
import json
from pathlib import Path
import unittest

from fl_decipher.content_v10 import CONTENT_FORMS, evidence, mode_quality
from fl_decipher.register_v5 import predictions
from fl_decipher.synthetic_v11 import generate, CONDITIONS, SETTINGS
from fl_decipher.text import sentences

ROOT = Path(__file__).resolve().parents[1]
CFG = json.loads((ROOT/'experiments/kamri_content_v10.json').read_text())
LEX = json.loads((ROOT/CFG['lexicon_path']).read_text())
FIXTURE = 119001


def packet(corruption='clean', extent='full', family='prediction_lure', density=3):
    return generate(FIXTURE, density, corruption, extent, family, LEX)


def quality(p, role):
    fa = sentences(p['fl_text']); sa = sentences(p['candidate_texts'][p['candidate_roles'].index(role)])
    ps, _ = predictions(fa, LEX, CFG['lexicon_rules'], CFG['prediction_variant'])
    a = {'blocks': [{'fl_atoms': [i], 'source_atoms': [i]} for i in range(len(sa))]}
    return evidence(a, fa, sa, ps, CFG)


class ConflictTests(unittest.TestCase):
    def test_dimensions_density_aliases_and_no_duplicate_replacement(self):
        answers = set()
        for c in CONDITIONS:
            p = generate(FIXTURE, **c, lexicon=LEX)
            answers.add(p['answer_index'])
            self.assertEqual(len(set(p['candidate_texts'])), 4)
            ps, gate = predictions(sentences(p['fl_text']), LEX, CFG['lexicon_rules'], CFG['prediction_variant'])
            known = 6*c['density'] - (6 if c['corruption'] == 'omit_one' else 18 if c['corruption'] == 'omit_all' else 0)
            self.assertEqual(sum(x['prediction'] in CONTENT_FORMS for row in ps for x in row), known)
            self.assertEqual(sum(x['prediction'] is not None for row in ps for x in row), 12+known)
            self.assertFalse(gate['active'])
        self.assertEqual(len(CONDITIONS), 24)
        self.assertEqual(len(answers), 1)

    def test_changed_occurrences_keep_their_truth_identities(self):
        for corruption in ['conflict_one', 'conflict_all', 'omit_one', 'omit_all']:
            for extent in ['full', 'half']:
                p = packet(corruption, extent)
                changed = [x for x in p['content_truth'] if x['changed']]
                self.assertEqual(len(changed), 6 if corruption.endswith('one') else 18)
                available = {x['uid'] for x in p['token_pairs']}
                unavailable = set(p['unavailable_query_uids'])
                self.assertEqual(available | unavailable, {x['uid'] for x in p['fl_token_ids']})
                self.assertFalse(available & unavailable)
                for x in changed:
                    self.assertIn(x['uid'], available | unavailable)
                    self.assertEqual(x['uid'] in available, extent == 'full' or x['atom_index'] < 3)

    def test_truth_and_renamed_pool_are_constant_across_corruptions(self):
        for extent in ['full', 'half']:
            clean = packet('clean', extent, 'content_renamed')
            for setting in SETTINGS[1:]:
                p = packet(setting['corruption'], extent, 'content_renamed')
                for k in ['candidate_texts', 'candidate_roles', 'source_token_ids', 'unavailable_query_uids', 'content_query_uids']:
                    self.assertEqual(p[k], clean[k])
                self.assertEqual([x['uid'] for x in p['fl_token_ids']], [x['uid'] for x in clean['fl_token_ids']])

    def test_clean_lure_is_observationally_tied_for_content(self):
        p = packet()
        true, lure = quality(p, 'correct'), quality(p, 'prediction_lure_1')
        self.assertNotEqual(p['candidate_texts'][p['answer_index']], p['candidate_texts'][p['candidate_roles'].index('prediction_lure_1')])
        for mode in ['content_bag', 'content_order']:
            self.assertEqual(mode_quality(true, mode), 1.)
            self.assertEqual(mode_quality(lure, mode), 1.)

    def test_conflict_all_is_invisible_to_bag_but_favors_ordered_lure(self):
        p = packet('conflict_all')
        true, lure = quality(p, 'correct'), quality(p, 'prediction_lure_1')
        self.assertEqual(mode_quality(true, 'content_bag'), 1.)
        self.assertEqual(mode_quality(lure, 'content_bag'), 1.)
        self.assertEqual(mode_quality(true, 'content_order'), 2/3)
        self.assertEqual(mode_quality(lure, 'content_order'), 1.)

    def test_one_conflict_alters_both_bag_and_order_objectives(self):
        p = packet('conflict_one')
        true, lure = quality(p, 'correct'), quality(p, 'prediction_lure_1')
        for mode in ['content_bag', 'content_order']:
            self.assertEqual(mode_quality(true, mode), 2/3)
            self.assertEqual(mode_quality(lure, mode), 1.)

    def test_omission_reduces_evidence_but_not_truth_denominator(self):
        clean, one, all_missing = packet(), packet('omit_one'), packet('omit_all')
        self.assertEqual(len(clean['token_pairs']), len(one['token_pairs']))
        self.assertEqual(len(clean['token_pairs']), len(all_missing['token_pairs']))
        e = quality(one, 'correct')
        self.assertEqual(e['content']['covered_content_predictions'], 12)
        self.assertEqual(mode_quality(e, 'content_order'), 1.)
        self.assertEqual(mode_quality(quality(all_missing, 'correct'), 'content_order'), 0.)

    def test_half_source_uses_only_available_evidence(self):
        p = packet('conflict_one', 'half')
        e = quality(p, 'prediction_lure_1')
        self.assertEqual(e['content']['total_query_content_predictions'], 18)
        self.assertEqual(e['content']['covered_content_predictions'], 9)
        self.assertEqual(mode_quality(e, 'content_order'), 1.)
        self.assertEqual(len(p['edges']), 3)

    def test_zero_content_control_gives_zero_for_every_candidate(self):
        p = packet(density=0)
        self.assertEqual(p['content_truth'], [])
        for role in p['candidate_roles']:
            e = quality(p, role)
            self.assertEqual(mode_quality(e, 'content_bag'), 0.)
            self.assertEqual(mode_quality(e, 'content_order'), 0.)


if __name__ == '__main__':
    unittest.main()
