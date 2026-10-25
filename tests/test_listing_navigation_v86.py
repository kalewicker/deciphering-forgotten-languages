import unittest
from fl_decipher.listing_navigation_v86 import inventory,route_reason
BASE='https://forgottenlanguages-full.forgottenlanguages.org/search/label/Kamri'
URL=BASE+'?updated-max=2022-11-01T00%3A00%3A00Z&max-results=1&start=1&by-date=false'
def older(url=URL):return f'<a class="blog-pager-older-link" href="{url}">Older Posts</a>'
class NavigationTests(unittest.TestCase):
 def test_explicit_one_route_and_duplicate_agreement(self):
  r=inventory(('<div id="blog-pager">'+older()+older()+'</div>').encode())
  self.assertEqual(r['next_capture_url'],URL);self.assertEqual(r['explicit_older_signals'],2)
  self.assertEqual(r['distinct_eligible_older_urls'],1);self.assertEqual(len(r['inventory']),2)
 def test_missing_and_ambiguous(self):
  self.assertIsNone(inventory(b'<a rel="next" href="https://example.com">X</a>')['next_capture_url'])
  r=inventory((older()+older(BASE+'?start=2')).encode());self.assertEqual(r['selection_reason'],'ambiguous_older_routes')
 def test_shape_and_query_rejections(self):
  for u in [URL.replace('https:','http:'),URL+'#x',BASE+'?start=0',BASE+'?start=1&start=2',BASE+'?max-results=1',BASE+'?start=1&max-results=101',BASE+'?start=1&callback=x',BASE+'?updated-max=2022-11-01T00:00:00']:
   self.assertIsNotNone(route_reason(u),u)
  self.assertIsNone(route_reason(BASE+'?start=1'))
 def test_next_conflict(self):
  raw=(older()+f'<link rel="next" href="{BASE}?start=2">').encode()
  self.assertEqual(inventory(raw)['selection_reason'],'conflicting_rel_next')
 def test_base_rejects_but_keeps_inventory(self):
  r=inventory(('<base href="https://evil.test">'+older()).encode())
  self.assertEqual(r['selection_reason'],'base_href');self.assertEqual(len(r['inventory']),1)
 def test_scope_and_indices(self):
  raw=('<html><head><title>X</title></head><body><a href="https://evil.test">Ignore</a>'+older()+'</body></html>').encode()
  r=inventory(raw);self.assertEqual(len(r['inventory']),1);self.assertEqual(r['inventory'][0]['tag_index'],5)
  self.assertFalse(r['new_predictions']);self.assertEqual(r['network_requests'],0)
if __name__=='__main__':unittest.main()
