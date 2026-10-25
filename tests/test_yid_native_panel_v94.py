import unittest
from fl_decipher.yid_native_panel_v94 import panel
class PanelTests(unittest.TestCase):
 def fixture(self):
  docs=[{'number':n,'requested_url':f'https://example.org/{n}','denominator':1,'targets':[{'text':'abc'}]} for n in [43,86]]
  slots=[{'number':d['number'],'status':'supplied','main_path':str(d['number']),'requested_url':d['requested_url'],'final_url':d['requested_url']} for d in docs]
  def raw(p):return f'<link rel="canonical" href="https://example.org/{p}"><div class="post-body">abc</div>'.encode()
  return docs,slots,raw
 def test_both_posts_preserved(self):
  d,s,r=self.fixture();out=panel(d,s,r)['report'];self.assertEqual(out['compared_targets'],2);self.assertEqual(len(out['posts']),2)
 def test_unavailable_not_zero(self):
  d,s,r=self.fixture();s[1]['status']='unavailable';out=panel(d,s,r)['report'];self.assertEqual(out['unavailable_targets'],1);self.assertIsNone(out['posts'][1]['counts'])
 def test_pending_refuses_before_read(self):
  d,s,r=self.fixture();s[1]['status']='pending'
  with self.assertRaises(AssertionError):panel(d,s,lambda p:self.fail('read before readiness'))
 def test_identity_failure_keeps_denominator(self):
  d,s,r=self.fixture();s[1]['final_url']='wrong';out=panel(d,s,r)['report'];self.assertEqual(out['fixed_targets'],2);self.assertEqual(out['compared_targets'],1)
 def test_literal_miss_is_observed_zero(self):
  d,s,r=self.fixture();d[1]['targets'][0]['text']='absent';out=panel(d,s,r)['report'];self.assertEqual(out['compared_targets'],2);self.assertEqual(out['posts'][1]['counts']['literal']['matched'],0)
