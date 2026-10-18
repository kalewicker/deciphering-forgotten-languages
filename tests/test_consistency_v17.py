from fractions import Fraction
from collections import Counter
import unittest
from fl_decipher.consistency_v17 import measure,form_ledger,summary,apply_orders,control_orders,permutation_orders,primary_fraction

def rows(spec):
    result=[];indices={}
    for unit,component,fl,en in spec:
        i=indices.get(unit,0);indices[unit]=i+1
        result.append({'uid':unit+f':t{i}','unit_uid':unit,'component':component,'index':i,'fl_form':fl,'english_form':en,'english_surface':en,'english_span':[i,i+1]})
    return result

class ConsistencyTests(unittest.TestCase):
    def test_single_unit_repetition_is_not_cross_unit_support(self):
        r=rows([('u1','a','f','x'),('u1','a','f','x')]);s=summary(r)
        self.assertEqual(s['cross_unit_repeated_types'],0);self.assertIsNone(s['global']['macro_form_cross_unit_agreement'])
        self.assertTrue(form_ledger(r)[0]['within_unit_repetition_only'])
    def test_unit_frequency_agreement_and_equal_form_weighting(self):
        r=rows([('u1','a','a','x'),('u1','a','a','y'),('u2','b','a','x'),('u2','b','a','x'),('u1','a','b','z'),('u2','b','b','z')]);s=summary(r)
        self.assertEqual(primary_fraction(s),Fraction(3,4));self.assertEqual(s['global']['equal_occurrence_pairs'],3)
        self.assertEqual(s['global']['occurrence_weighted_agreement']['value'],3/5)
        self.assertEqual(s['global']['distinct_unit_pairs'],2)
    def test_strict_consistency_retains_conflicts(self):
        r=rows([('u1','a','f','x'),('u2','a','f','y'),('u1','a','g','z'),('u2','a','g','z')]);s=summary(r)
        self.assertEqual(s['strict_global_types'],1);self.assertEqual(s['conflicting_repeated_types'],1)
        self.assertEqual(len(form_ledger(r)),2)
    def test_cross_component_lead_needs_two_units_in_each_component(self):
        r=rows([('u1','a','f','x'),('u2','a','f','x'),('u3','b','f','x')]);self.assertFalse(form_ledger(r)[0]['cross_component_review_lead'])
        r+=rows([('u4','b','f','x')]);self.assertTrue(form_ledger(r)[0]['cross_component_review_lead'])
        r+=rows([('u5','b','f','y')]);self.assertFalse(form_ledger(r)[0]['cross_component_review_lead'])
    def test_scope_uses_distinct_units_and_preserves_exact_ties(self):
        r=rows([('u1','a','f','x'),('u2','a','f','x'),('u3','b','f','y')])
        self.assertEqual(measure(r,'within_component')['macro_form_cross_unit_agreement']['value'],1)
        self.assertEqual(measure(r,'between_components')['macro_form_cross_unit_agreement']['value'],0)
        self.assertEqual(primary_fraction(summary(r)),Fraction(1,3))
    def test_fixed_rotation_directions(self):
        r=rows([('u','a','a','x'),('u','a','b','y'),('u','a','c','z')])
        p,_=control_orders(r,'rotate_+1',[]);m,_=control_orders(r,'rotate_-1',[])
        self.assertEqual(p['u'],[2,0,1]);self.assertEqual(m['u'],[1,2,0])
    def test_swap_rejects_nonmatching_or_nonunique_length_pair(self):
        r=rows([('u1','a','f','x'),('u2','b','g','y'),('u3','c','h','z')])
        with self.assertRaises(AssertionError):control_orders(r,'length_matched_swap',['u1','u2'])
    def test_permutations_keep_every_occurrence_and_multiset(self):
        r=rows([('u1','a','f','x'),('u1','a','g','y'),('u2','b','f','y'),('u2','b','g','z')]);orders=list(permutation_orders(r,12345,25))
        self.assertEqual(len(orders),25);self.assertEqual(orders,list(permutation_orders(r,12345,25)))
        for number,o in orders:
            changed=apply_orders(r,o);self.assertEqual([x['uid'] for x in changed],[x['uid'] for x in r])
            for u in ('u1','u2'):self.assertEqual(Counter(x['english_form'] for x in changed if x['unit_uid']==u),Counter(x['english_form'] for x in r if x['unit_uid']==u))
    def test_invalid_order_is_rejected(self):
        r=rows([('u','a','f','x'),('u','a','g','y')])
        with self.assertRaises(AssertionError):apply_orders(r,{'u':[0,0]})
if __name__=='__main__':unittest.main()
