"""Meaningful gate/selection checks for missing-evidence natural acquisition."""
import copy
from itertools import product
import unittest
from fl_decipher.natural_v12 import NOMINATIONS, opening, reference_gate, validate_denominators


class NaturalAcquisitionTests(unittest.TestCase):
    def test_every_required_gate_is_fail_closed(self):
        keys=['source_prose','authority_verified','extraction_reviewed','passage_reviewed','component_novel']
        for values in product([False,True],repeat=5):
            result=reference_gate(**dict(zip(keys,values,strict=True)))
            self.assertEqual(result['eligible'],all(values))
            self.assertEqual(result['unmet'],[k for k,v in zip(keys,values,strict=True) if not v])
        with self.assertRaises(AssertionError):
            reference_gate(**dict.fromkeys(keys,1))

    def test_selection_stops_without_backfilling(self):
        self.assertEqual(opening('One two. Three four five six. Seven.',5),'One two.')
        self.assertEqual(opening('One two three four. Five.',3),'')

    def test_semicolon_clause_is_not_an_entire_sentence(self):
        self.assertEqual(opening('One two; three four. Five.',3),'')
        self.assertEqual(opening('One two; three four. Five.',4),'One two; three four.')
        self.assertEqual(opening('One two. Unfinished text',100),'One two.')

    def test_only_declared_number_prefixes_are_removed(self):
        self.assertEqual(opening('1. Azazel! Flame.\n2. Word is feared.',numbered=True),'Azazel! Flame. Word is feared.')
        self.assertIn('1.',opening('1. First.',numbered=False))

    def test_missing_references_remain_null_with_selected_denominator(self):
        gate=reference_gate(source_prose=False,authority_verified=False,extraction_reviewed=False,passage_reviewed=False,component_novel=True)
        ledger={'selected_works':2,'selected_queries':2,'selected_components':2,'reference_eligible_queries':0,'evaluated_queries':0,'metrics':None,'model_executed':False,
                'records':[dict(n,gate=gate,references=None,lexical_accuracy=None) for n in NOMINATIONS]}
        self.assertTrue(validate_denominators(ledger))
        for field,value in [('metrics',{'accuracy':0}),('evaluated_queries',2),('model_executed',True),('selected_works',0)]:
            bad=copy.deepcopy(ledger);bad[field]=value
            with self.assertRaises(AssertionError):validate_denominators(bad)

    def test_ineligible_work_cannot_receive_nominal_reference_accuracy(self):
        gate=reference_gate(source_prose=False,authority_verified=False,extraction_reviewed=False,passage_reviewed=False,component_novel=True)
        ledger={'selected_works':2,'selected_queries':2,'selected_components':2,'reference_eligible_queries':0,'evaluated_queries':0,'metrics':None,'model_executed':False,
                'records':[dict(n,gate=gate,references=None,lexical_accuracy=None) for n in NOMINATIONS]}
        ledger['records'][0]['lexical_accuracy']=1.
        with self.assertRaises(AssertionError):validate_denominators(ledger)


if __name__=='__main__':
    unittest.main()
