import unittest
from collections import Counter
from fl_decipher.word_order_v77 import *

class WordOrderTests(unittest.TestCase):
 def test_barriers_and_singletons(self):
  row={'tokens':[{'blocked':False,'pair_from_previous':False},{'blocked':False,'pair_from_previous':True},
    {'blocked':True,'pair_from_previous':False},{'blocked':False,'pair_from_previous':False}]}
  self.assertEqual(segments(row),[[0,1],[3]])
 def test_vocabulary_and_unknown(self):
  seq=[['a','a','rare'],['b','b']];v=vocabulary(seq)
  self.assertEqual(v,['a','b'])
  m=fit(seq,v);self.assertAlmostEqual(m[0][UNK],1.5/6.5)
  self.assertNotIn('evaluation_only',m[0])
 def test_probabilities_normalize_and_backoff(self):
  m=fit([['a','b','a'],['b','a']],['a','b'])
  self.assertAlmostEqual(sum(m[0].values()),1)
  for h in ['a','b',UNK]:self.assertAlmostEqual(sum(predict(m,h,w) for w in m[0]),1)
  self.assertEqual(predict(m,UNK,'a'),m[0]['a'])
  self.assertAlmostEqual(predict(m,'a','b'),(1+10*m[0]['b'])/11)
 def test_shuffles_preserve_histograms(self):
  s=[2,3,4,5];self.assertEqual(order(4,'x',s),order(4,'x',s))
  self.assertEqual(Counter(order(4,'x',s)),Counter(s))
  seq=['a','a','b','c'];v=vocabulary([seq]);m=fit([seq],v)
  self.assertEqual(fit([[seq[i-2] for i in order(4,'x',s)]],v)[0],m[0])
 def test_known_metrics_retain_unknown_denominator(self):
  m=metrics([.5,.5],[.25,1],[True,False])
  self.assertAlmostEqual(m['gain'],0)
  self.assertEqual(m['known_gain'],-1)
  self.assertIsNone(metrics([.5],[.25],[False])['known_gain'])
 def test_macro_weighting_and_ties(self):
  folds=[{'pairs':n,'observed':{'gain':g,'known_gain':g,'known_targets':20},
    'controls':[{'gain':g} for _ in range(99)]} for n,g in [(10,1),(90,-1)]]
  s=summarize(folds)
  self.assertEqual(s['macro_gain'],0);self.assertAlmostEqual(s['token_weighted_gain'],-.8)
  self.assertEqual(s['conditional_rank'],1);self.assertFalse(s['development_gate'])
if __name__=='__main__':unittest.main()
