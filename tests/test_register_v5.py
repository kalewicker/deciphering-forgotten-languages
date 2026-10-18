import json
from pathlib import Path
import random
import unittest

from fl_decipher.experiment_v5 import nonidentity_orders, summarize
from fl_decipher.lexicon import predict
from fl_decipher.register_v5 import audit_aliases, gate, label_anchor_origins, predictions
from fl_decipher.text import sentences

ROOT = Path(__file__).resolve().parents[1]
CFG = json.loads((ROOT/'experiments/kamri_precision_v4.json').read_text())


class RegisterTests(unittest.TestCase):
    def test_gate_needs_distinct_forms_and_total_count(self):
        self.assertFalse(gate(sentences('ńańi ńańi ńańi.'))['active'])
        self.assertFalse(gate(sentences('ńańi tawwdan.'))['active'])
        self.assertTrue(gate(sentences('ńańi tawwdan ńańi.'))['active'])
        self.assertFalse(gate(sentences('xńańi xtawwdan xńańi.'))['active'])

    def test_baseline_eligibility_and_offsets_unchanged(self):
        lexicon = json.loads((ROOT/CFG['lexicon_path']).read_text())
        atoms = sentences('Şu ńańi şi. Aš tawwdan ńańi.')
        baseline, _ = predictions(atoms, lexicon, CFG['lexicon_rules'], 'baseline')
        for atom, row in zip(atoms, baseline, strict=True):
            old = predict(atom, lexicon, CFG['lexicon_rules'])
            self.assertEqual(old, [{k: v for k, v in p.items() if k != 'origin'} for p in row])
            self.assertEqual([p['span'] for p in row], [[t.start, t.end] for t in atom.tokens])

    def test_scope_prevents_single_marker_override(self):
        atoms = sentences('ńańi ńańi other.')
        universal, _ = predictions(atoms, {}, CFG['lexicon_rules'], 'universal_aliases')
        gated, _ = predictions(atoms, {}, CFG['lexicon_rules'], 'gated_aliases')
        self.assertEqual([p['prediction'] for p in universal[0]], ['of', 'of', None])
        self.assertEqual([p['prediction'] for p in gated[0]], [None, None, None])
        self.assertEqual(universal[0][0]['state'], 'experimental_single_work_register_hypothesis')

    def test_overrides_preserve_baseline_and_other_forms(self):
        atoms = sentences('ńańi tawwdan ńańi unknown.')
        gated, detector = predictions(atoms, {}, CFG['lexicon_rules'], 'gated_aliases')
        self.assertTrue(detector['active'])
        self.assertEqual([p['prediction'] for p in gated[0]], ['of', 'that', 'of', None])
        self.assertTrue(all(p['baseline_prediction'] is None for p in gated[0][:3]))
        self.assertEqual(gated[0][-1]['origin'], 'abstained')

    def test_presence_is_not_positional_confirmation(self):
        reference = [{'fl_index': 0, 'source_index': 0}]
        audit = audit_aliases('ńańi unknown.', 'something of extra.', reference)
        self.assertEqual(audit[0]['state'], 'source_span_presence_only')
        self.assertIsNone(audit[0]['projected_word'])
        self.assertFalse(audit[0]['semantic_gold'])
        conflict = audit_aliases('tawwdan unknown.', 'something else.', reference)
        self.assertEqual(conflict[0]['state'], 'equal_length_positional_conflict')
        absent = audit_aliases('tawwdan unknown.', 'something else extra.', reference)
        self.assertEqual(absent[0]['state'], 'absent_in_reviewed_source_span')

    def test_nonidentity_controls_are_deterministic_and_keep_repetitions(self):
        orders = nonidentity_orders(2, 20, random.Random(5731))
        self.assertEqual(orders, [[1, 0]]*20)
        self.assertEqual(nonidentity_orders(1, 20, random.Random(5731)), [])
        orders = nonidentity_orders(6, 20, random.Random(5731))
        self.assertEqual(orders, nonidentity_orders(6, 20, random.Random(5731)))
        self.assertTrue(all(o != list(range(6)) and sorted(o) == list(range(6)) for o in orders))

    def test_missing_reference_never_becomes_zero_recall(self):
        missing = {'group': 'missing', 'split': 'fresh', 'variant': 'baseline', 'status': 'source_unavailable'}
        summary = summarize([missing, dict(missing, group='also_missing')], 'fresh', 'baseline')
        self.assertEqual((summary['selected'], summary['available'], summary['missing']), (2, 0, 2))
        self.assertIsNone(summary['selected_sample_alignment_recall'])
        self.assertIsNone(summary['retrieved_edges']['recall_on_available'])
        self.assertEqual(summary['source_absent_evaluated'], 0)
        self.assertFalse(summary['reference_coverage_complete'])

    def test_alias_match_is_never_labeled_frozen_evidence(self):
        a = {'token_pairs': [{'basis': 'frozen_anchor', 'fl_index': 0, 'fl_span': [0, 4]},
                              {'basis': 'frozen_anchor', 'fl_index': 0, 'fl_span': [5, 8]},
                              {'basis': 'positional'}], 'edges': [{'fl_index': 0, 'source_index': 0}]}
        result = label_anchor_origins(a, [[{'span': [0, 4], 'origin': 'registered_alias'}, {'span': [5, 8], 'origin': 'frozen_v1'}]])
        self.assertEqual([p['basis'] for p in result['token_pairs']], ['experimental_alias', 'frozen_anchor', 'positional'])
        self.assertEqual(result['edges'], [{'fl_index': 0, 'source_index': 0}])


if __name__ == '__main__':
    unittest.main()
