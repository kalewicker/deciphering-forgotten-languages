import unittest
from fl_decipher.browser_listing_v85 import assess,origin_metadata
from fl_decipher.reserved_intake_v80 import LABEL,HOST
PREFIX=f'<!-- saved from url=(0070){LABEL} --><title>Forgotten Languages Full: Kamri</title>'
def anchor(i):return f'<h3 class="post-title"><a href="https://{HOST}/2026/01/post-{i}.html">Title {i}</a></h3>'
class BrowserListingTests(unittest.TestCase):
 def test_positive_comment_or_native_origin(self):
  self.assertTrue(origin_metadata(PREFIX.encode())['metadata_use_allowed'])
  raw=f'<title>Kamri</title><link rel="canonical" href="{LABEL}">'.encode()
  self.assertTrue(origin_metadata(raw)['metadata_use_allowed'])
  self.assertFalse(origin_metadata(b'<title>Kamri</title>')['metadata_use_allowed'])
 def test_conflicting_origin(self):
  raw=(PREFIX+'<meta property="og:url" content="https://evil.test">').encode()
  self.assertFalse(origin_metadata(raw)['metadata_use_allowed'])
 def test_base_and_title_ambiguity(self):
  for suffix in ['<base href="https://evil.test">','<title>Kamri</title>']:
   self.assertFalse(origin_metadata((PREFIX+suffix).encode())['metadata_use_allowed'])
 def test_first_four_and_complete_reasons(self):
  raw=(PREFIX+anchor(0)+anchor(0)+''.join(anchor(i) for i in range(1,7))).encode()
  known={f'https://{HOST}/2026/01/post-0.html'};r=assess(raw,known)
  self.assertTrue(r['nomination_capacity'])
  self.assertEqual([s['nominee']['index'] for s in r['slots']],[2,3,4,5])
  self.assertEqual([r['candidate_inventory']['candidates'][i]['reason'] for i in [0,1,6]],['previously_recorded','duplicate','over_cap'])
 def test_strict_hrefs_not_repaired(self):
  raw=(PREFIX+''.join(f'<h3 class="post-title"><a href="{u}">T</a></h3>' for u in ['/2026/01/a.html',f'http://{HOST}/2026/01/a.html',f'https://{HOST}/2026/01/a.html?m=0'])).encode()
  r=assess(raw,set());self.assertFalse(r['nomination_capacity'])
  self.assertEqual([x['reason'] for x in r['candidate_inventory']['candidates']],['invalid_url']*3)
 def test_failed_gate_skips_inventory(self):
  r=assess((anchor(1)+'<title>Other</title>').encode(),set())
  self.assertIsNone(r['candidate_inventory']);self.assertEqual(len(r['slots']),4)
  self.assertTrue(all(not s['filled'] for s in r['slots']));self.assertFalse(r['new_predictions'])
if __name__=='__main__':unittest.main()
