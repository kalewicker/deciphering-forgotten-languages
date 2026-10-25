import unittest
from fl_decipher.browser_listing_v87 import origin_metadata,assess
from fl_decipher.reserved_intake_v80 import HOST,LABEL
TARGET=LABEL+'?updated-max=2022-11-30T07:37:00%2B01:00&max-results=20&start=1&by-date=false'
def fixture(url=TARGET):return f'<!-- saved from url=(0159){url} --><title>Kamri</title>'
class PaginationIntakeTests(unittest.TestCase):
 def test_exact_query_binds(self):
  self.assertTrue(origin_metadata(fixture().encode(),TARGET)['metadata_use_allowed'])
 def test_bare_label_not_equated(self):
  self.assertFalse(origin_metadata(fixture(LABEL).encode(),TARGET)['metadata_use_allowed'])
 def test_changed_cursor_rejected(self):
  self.assertFalse(origin_metadata(fixture(TARGET.replace('start=1','start=2')).encode(),TARGET)['metadata_use_allowed'])
 def test_native_origin_conflict(self):
  raw=(fixture()+f'<link rel="canonical" href="{LABEL}">').encode()
  self.assertFalse(origin_metadata(raw,TARGET)['metadata_use_allowed'])
 def test_first_four_order_and_exposure(self):
  raw=(fixture()+''.join(f'<h3 class="post-title"><a href="https://{HOST}/2022/01/p-{i}.html">T{i}</a></h3>' for i in range(6))).encode()
  r=assess(raw,{f'https://{HOST}/2022/01/p-0.html'},TARGET)
  self.assertEqual([s['nominee']['index'] for s in r['slots']],[1,2,3,4]);self.assertTrue(r['nomination_capacity'])
 def test_rejected_origin_skips(self):
  r=assess(fixture(LABEL).encode(),set(),TARGET)
  self.assertIsNone(r['candidate_inventory']);self.assertEqual(len(r['slots']),4);self.assertFalse(r['new_predictions'])
if __name__=='__main__':unittest.main()
