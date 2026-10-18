from itertools import product
import unittest
from fl_decipher.transfer_v18 import predict,reference_gate,evaluate,ratio

def candidates():return {'primary':{'fa':{'paired_english_form':'a'}},'secondary':{'fa':{'paired_english_form':'a'}},'conflicted_forms':[{'fl_form':'so'}]}
def ref(uid,english,eligible):return {'uid':uid,'source_tokens':[{'form':x} for x in english],'gate':{'development_positional_score_eligible':eligible}}
class TransferTests(unittest.TestCase):
 def test_target_english_does_not_affect_frozen_lookup(self):
  a={'uid':'u','component':'g','fl':'Fa so la.','english':'Anything'};b=a|{'english':'Different'}
  self.assertEqual(predict(a,candidates()),predict(b,candidates()))
 def test_conflicts_and_unseen_forms_abstain_without_majority_repair(self):
  p=predict({'uid':'u','component':'g','fl':'Fa so la.'},candidates())
  self.assertEqual(p['tokens'][1]['primary']['abstention_reason'],'conflicted_training_form')
  self.assertEqual(p['tokens'][2]['primary']['abstention_reason'],'outside_frozen_candidate_set')
 def test_gate_is_fail_closed_on_all_requirements(self):
  keys=['source_authority','source_statement_complete','source_continuation_orderly','historical_fl_unique_complete','equal_token_counts']
  for vs in product((False,True),repeat=5):
   g=reference_gate(**dict(zip(keys,vs,strict=True)));self.assertEqual(g['development_positional_score_eligible'],all(vs))
   self.assertEqual(g['unmet'],[k for k,v in zip(keys,vs,strict=True) if not v]);self.assertFalse(g['semantic_training_eligible'])
 def test_unscoreable_predictions_stay_in_full_primary_denominator(self):
  ps=[predict({'uid':'u1','component':'g','fl':'Fa.'},candidates()),predict({'uid':'u2','component':'h','fl':'Fa fa.'},candidates())]
  result=evaluate(ps,[ref('u1',['a'],True),ref('u2',['x'],False)])['stats']['primary']
  self.assertEqual(result['predictions'],3);self.assertEqual(result['verified_positional_matches'],1);self.assertEqual(result['positional_conflicts'],0)
  self.assertEqual(result['unscoreable_predictions'],2);self.assertEqual(result['supported_agreement_all_predictions'],ratio(1,3))
  self.assertEqual(result['conditional_agreement_scoreable_predictions'],ratio(1,1))
 def test_unscoreable_tokens_have_no_fabricated_reference_form(self):
  p=predict({'uid':'u','component':'g','fl':'Fa.'},candidates());row=evaluate([p],[ref('u',['a'],False)])['tokens'][0]
  self.assertIsNone(row['reference_form']);self.assertEqual(row['primary']['status'],'unscoreable')
 def test_scoring_never_truncates_unequal_length_pairs(self):
  p=predict({'uid':'u','component':'g','fl':'Fa fa.'},candidates())
  with self.assertRaises(AssertionError):evaluate([p],[ref('u',['a'],True)])
 def test_permuted_controls_preserve_prediction_and_abstention_counts(self):
  p=predict({'uid':'u','component':'g','fl':'Fa la.'},candidates());rs=[ref('u',['a','x'],True)]
  first=evaluate([p],rs);rotated=evaluate([p],rs,{'u':[1,0]})
  self.assertEqual(first['stats']['primary']['predictions'],rotated['stats']['primary']['predictions'])
  self.assertEqual(first['stats']['primary']['abstentions'],rotated['stats']['primary']['abstentions'])
  self.assertEqual(first['stats']['primary']['verified_positional_matches'],1);self.assertEqual(rotated['stats']['primary']['positional_conflicts'],1)
 def test_zero_denominators_are_unavailable(self):
  p=predict({'uid':'u','component':'g','fl':'La.'},candidates());s=evaluate([p],[ref('u',['x'],True)])['stats']['primary']
  self.assertIsNone(s['supported_agreement_all_predictions']);self.assertIsNone(s['conditional_agreement_scoreable_predictions'])
if __name__=='__main__':unittest.main()
