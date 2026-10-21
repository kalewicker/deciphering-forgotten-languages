import math, unittest
from fl_decipher.context_guard_v79 import fit,predict,check_model
from fl_decipher.word_order_v77 import UNK,vocabulary

class ContextGuardTests(unittest.TestCase):
 def model(self):
  sequences=[('A',['h','a','h','a','h','a']),('B',['h','b','h','b','h','b'])]
  return fit(sequences,['h','a','b','z'])
 def test_mass_and_unknown_neutrality(self):
  m=self.model();check_model(m)
  self.assertIn('h',m[4]);self.assertEqual(predict(m,'h',UNK),m[0][UNK])
  self.assertAlmostEqual(sum(predict(m,'h',w) for w in m[0]),1)
 def test_unknown_and_ineligible_backoff(self):
  m=self.model()
  for h in [UNK,'a','missing']:
   for w in m[0]:self.assertEqual(predict(m,h,w),m[0][w])
 def test_group_requirement(self):
  seq=[('A',['h','a']*10),('B',['b','b'])]
  m=fit(seq,['h','a','b']);self.assertNotIn('h',m[4])
 def test_minimum_count(self):
  m=fit([('A',['h','a','h','a']),('B',['h','b','h','b'])],['h','a','b'])
  self.assertEqual(m[2]['h'],4);self.assertNotIn('h',m[4])
 def test_penalty_bound(self):
  m=self.model();ratio=predict(m,'h','z')/m[0]['z']
  self.assertAlmostEqual(ratio,.5+5/(m[2]['h']+10))
  self.assertGreater(math.log2(ratio),-1)
 def test_training_vocabulary_and_unknown_transitions(self):
  seq=[('A',['h','a','rare']),('B',['h','a','other'])]
  v=vocabulary([s for _,s in seq]);m=fit(seq,v)
  self.assertEqual(v,['a','h']);self.assertNotIn('rare',m[0])
  self.assertEqual(m[2]['a'],0);self.assertNotIn('evaluation_word',m[0])
if __name__=='__main__':unittest.main()
