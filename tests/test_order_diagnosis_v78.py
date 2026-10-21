import unittest,math
from fl_decipher.order_diagnosis_v78 import *
def row(cell,value,known=True):
 return {'cell':cell,'gain':value,'control_gains':[value-1]*99,
         'target_status':'known' if known else 'training_absent'}
class DiagnosisTests(unittest.TestCase):
 def test_status(self):
  self.assertEqual([status(n) for n in [0,1,2,10]],['training_absent','training_singleton','known','known'])
 def test_support(self):
  self.assertEqual([support(*p) for p in [(0,0),(3,0),(3,2)]],['unseen_context','unseen_pair','seen_pair'])
  with self.assertRaises(AssertionError):support(1,2)
 def test_backoff(self):self.assertEqual(gain(.2,.2),0)
 def test_unseen_pair(self):
  for u,n in [(.1,5),(.4,30)]:self.assertAlmostEqual(gain(u,10*u/(n+10)),math.log2(10/(n+10)))
 def test_partition_and_empty_cells(self):
  result=aggregate([row(CELLS[0],2),row(CELLS[-1],-1,False)])
  self.assertEqual(len(result['cells']),12);self.assertEqual(result['gain'],.5)
  self.assertEqual(result['known_gain'],2)
  self.assertEqual(sum(c['contribution'] for c in result['cells']),.5)
  self.assertIsNone(result['cells'][1]['mean_gain']);self.assertEqual(result['cells'][1]['contribution'],0)
 def test_unequal_group_weighting(self):
  a=aggregate([row(CELLS[0],1)]);b=aggregate([row(CELLS[0],-1)]*9)
  self.assertEqual(macro([a,b])[0]['contribution'],0)
if __name__=='__main__':unittest.main()
